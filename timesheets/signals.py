import datetime
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, Timesheet, Day, Week

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=Timesheet)
def create_weeks(sender, instance, created, **kwargs):
    """Creates day and week objects for timesheet. Week belongs to timesheet in
    which week ends. Usually has overlap into previous timesheet.
    First we create the week, then if that week overlaps with the previous
    timesheet we go back to the days from that timesheet and assign them to
    the week we just created. Then create additional weeks inside this timesheet
    along with days assigned to those weeks until the end of the week falls
    outside of the timesheet. After this, if there are days left over which fall
    outside of the last week but prior to the end of the timesheet, we create
    those days without a week assigned to them. Those days will = previous_days
    for the next timesheet and we'll assign those days to the first week of
    that timesheet."""
    if created:
        start = instance.pay_period_start - datetime.timedelta(days=
                                            instance.pay_period_start.weekday())
        end = start + datetime.timedelta(days=6)
        current_day = instance.pay_period_start
        previous_days = Day.objects.filter(day__range=(start, current_day), 
                                           user=instance.user)
        while end <= instance.pay_period_end:
            week = Week.objects.create(start_date=start, end_date=end,
                                timesheet=instance, user=instance.user)
            if start < instance.pay_period_start:
                for day in previous_days:
                    day.week = week
                    day.save()
            while current_day <= end:
                Day.objects.create(day=current_day, week=week,
                                   timesheet=instance, user=instance.user)
                current_day += datetime.timedelta(days=1)
            start += datetime.timedelta(days=7)
            end += datetime.timedelta(days=7)
        while current_day <= instance.pay_period_end:
            Day.objects.create(day=current_day, timesheet=instance,
                               user=instance.user)
            current_day += datetime.timedelta(days=1)

# @receiver(post_save, sender=Timesheet)
# def create_days(sender, instance, created, **kwargs):
#     """Creates day objects for each day of the timesheet."""
#     if created:
#         day = instance.pay_period_start
#         while day <= instance.pay_period_end:
#             #self.clockpunches.update({self.pay_period_start: []})
#             Day.objects.create(day=day, timesheet=instance, user=instance.user)
#             day += datetime.timedelta(days=1)

''' Do we need a save signal too?
This signal below creates a second set of day objects when
timesheet is created. We don't want that. What about when it's updated?
Will that ever really happen?
 '''

# @receiver(post_save, sender=Timesheet)
# def save_days(sender, instance, **kwargs):
#     day = instance.pay_period_start
#     while day <= instance.pay_period_end:
#         #self.clockpunches.update({self.pay_period_start: []})
#         current_day = Day(day=day, timesheet=instance)
#         current_day.save()
#         day += datetime.timedelta(days=1)
