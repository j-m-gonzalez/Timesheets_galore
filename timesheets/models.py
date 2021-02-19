from datetime import date, datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.urls import reverse
# import other model for foriegn keys
import django.utils.timezone
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

# TODO
# -CreateView for clockpunch
# -When clockpunch created, try to match it up with a timesheet and day
#   -Alt: specify timesheet and day...nah, make user friendy.
#   -Let them just pick the day and time and match it up in the back


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    position = models.CharField(max_length=250)
    date_created = models.DateTimeField(default=django.utils.timezone.now)

    def __str__(self):
        return '{} {}'.format(self.user.first_name, self.user.last_name)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

class Timesheet(models.Model):
    pay_period_start = models.DateField(null=True)
    pay_period_end = models.DateField(null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
      # Create dict(or maybe list) of each day for the timesheets: <---DONE with signal
        # How to update days when timesheet is updated? Just delete and create new one?
        # Why would you need to update? Keep the punches without making new timesheet? Maybe

    class Meta:
        ordering = ['-pay_period_end']

    @property
    def total_hours(self):
        day_hours = []
        for day in self.day_set.all():
            day_hours.append(day.total_hours)
        total_hours = sum(day_hours)
        return round(total_hours, 2)

    @property
    def normal_hours(self):
        day_hours = []
        for day in self.day_set.all():
            day_hours.append(day.normal_hours)
        total_hours = sum(day_hours)
        return round(total_hours, 2)

    @property
    def overtime_hours(self):
        week_hours = []
        for week in self.week_set.all():
            week_hours.append(week.overtime_hours)
        total_hours = sum(week_hours)
        return round(total_hours, 2)

    @property
    def double_overtime_hours(self):
        week_hours = []
        for week in self.week_set.all():
            week_hours.append(week.double_overtime_hours)
        total_hours = sum(week_hours)
        return round(total_hours, 2)


    def __str__(self):
        return f'''{self.user.first_name} {self.user.last_name} |
                   {self.pay_period_start} to {self.pay_period_end}
                   '''

    def get_absolute_url(self):
        return reverse('timesheets:timesheet-detail', kwargs={'pk': self.pk})

class Week(models.Model):
    """Made for overtime calculations. Belongs to pay period which week ends."""
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-start_date']

    def get_hours(self, attr):
        '''Get each type of hours(attr) for each day in the week then sum.'''
        day_hours = []
        for day in self.day_set.all():
            day_hours.append(getattr(day, attr))
        total_hours = sum(day_hours)
        return round(total_hours, 2)

    @property
    def total_hours(self):
        return self.get_hours("total_hours")

    @property
    def normal_hours(self):
        return self.get_hours("normal_hours")

    @property
    def overtime_hours(self):
        return self.get_hours("overtime_hours")

    @property
    def double_overtime_hours(self):
        return self.get_hours("double_overtime_hours")

    def __str__(self):
        return f'''{self.user.first_name} {self.user.last_name} |
                   {self.start_date} to {self.end_date}
                   '''
        # {str(self.end_date.strftime("%a\n%b, %d")})

class Day(models.Model):
    """Created through signals when timesheet is created."""
    day = models.DateField(null=True)
    week = models.ForeignKey(Week, null=True, on_delete=models.CASCADE)
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-day']

    @property
    def total_hours(self):
        # Doesnt update when you update the clockpunch
        # Also displays 0 when there's a clock in but no out even when there's
        # a pair before
        '''Got 4 scenarios. first, last: in/out, in/in, out/in and out/out.
        -in/out: is the normal daytime shift where you clock in then out. Here
                we just subtract the first from the second then add 2 to get
                the next set then repeat.
        Last 3 have to do with overnight shifts.
        -If first_punch = "out": first_punch - start of day,
                                 then same as above but -1 punch[0] in list
        If last_punch = "in":
            If no punch after last: ignore last_punch
            elif next_punch: end of day - last_punch
        ex. 8 am(in), 4 pm(out), 5 pm(in) = 8 hrs until next_punch is clocked.
            then = 8 + 7(5 pm to midnight) = 15 hrs.
        Maybe put this in a readme. Getting long.
        Also, maybe refactor. The if and while's are kinda wet. Functions?'''
        min = datetime.combine(self.day, datetime.min.time())
        max = datetime.combine(self.day, datetime.max.time())
        start = timezone.make_aware(min)
        end = timezone.make_aware(max)
        clockpunch_set = self.clockpunch_set.all().order_by('date_time')
        total_hour_list = []
        def next_punch(i):
            return ClockPunch.objects.filter(user=self.timesheet.user,
                              date_time__gt=clockpunch_set[i].date_time).first()
        try:
            first = clockpunch_set[0].clock
            last = clockpunch_set.last().clock
            i = 0
            if first == True and last == False:
                while i < len(clockpunch_set):
                    total_hour_list.append(clockpunch_set[i+1].date_time -
                                           clockpunch_set[i].date_time)
                    i += 2

            elif first == True and last == True:
                while i < (len(clockpunch_set) - 1):
                    total_hour_list.append(clockpunch_set[i+1].date_time -
                                        clockpunch_set[i].date_time)
                    i += 2
                if next_punch(i):
                    total_hour_list.append(end - clockpunch_set[i].date_time)

            elif first == False and last == True:
                total_hour_list.append(clockpunch_set[i].date_time - start)
                i += 1
                while i < (len(clockpunch_set) - 1):
                    total_hour_list.append(clockpunch_set[i+1].date_time -
                                        clockpunch_set[i].date_time)
                    i += 2
                if next_punch(i):
                    total_hour_list.append(end - clockpunch_set[i].date_time)

            elif first == False and last == False:
                total_hour_list.append(clockpunch_set[i].date_time - start)
                i += 1
                while i < len(clockpunch_set):
                    total_hour_list.append(clockpunch_set[i+1].date_time -
                                        clockpunch_set[i].date_time)
                    i += 2
        except IndexError:
            total_hour_list.append(timedelta(0))
        total_hours = sum(total_hour_list, timedelta())
        hours = total_hours.seconds / 3600
        return round(hours, 2)

    @property
    def normal_hours(self):
        if self.day.weekday() == 6:
            return 0.0
        elif self.total_hours > 8:
            return 8.0
        else:
            return self.total_hours

    @property
    def overtime_hours(self):
        o_time = 0.0
        if self.day.weekday() == 6:
            if self.total_hours > 8:
                o_time = 8
            else:
                o_time = self.total_hours
        elif self.total_hours > 8:
            if self.total_hours > 12:
                o_time = 4.0
            else:
                o_time = self.total_hours - 8
        return round(o_time, 2)

    @property
    def double_overtime_hours(self):
        double_o_time = 0
        if self.day.weekday() == 6:
            if self.total_hours > 8:
                double_o_time = self.total_hours - 8
        elif self.total_hours > 12:
            double_o_time = self.total_hours - 12
        return round(double_o_time, 2)

    # Double overtime for > 12 hours or for > 8 on sunday

    def __str__(self):
        return str(self.day.strftime("%a\n%b, %d"))

class ClockPunch(models.Model):
    # Assert that current clock punch was opposite of last. In/Out.
    # Maybe a comment attribute too?
    clock = models.BooleanField()
    time = models.TimeField(auto_now_add=False, null=True, blank=True)
    date_time = models.DateTimeField(auto_now_add=False, blank=False)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE)
    day = models.ForeignKey(Day, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date_time']
        verbose_name_plural = 'clockpunches'

    def __str__(self):
        if self.clock == True:
            clock = 'Clock in'
        elif self.clock == False:
            clock = 'Clock out'
        return "{} \n{}: {} {}".format(str(self.timesheet),
                                clock, self.day, self.time.strftime('%H:%M:%S'))

    def clocked_recently(self):
        return self.time >= (django.utils.timezone.now() -
                             datetime.timedelta(days=1))
