from datetime import datetime, date
from django import forms
from django.shortcuts import render, redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    )
from .models import Timesheet, Profile, ClockPunch, Day
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from .forms import (
    UserRegisterForm,
    UserUpdateForm,
    ProfileUpdateForm,
    TimesheetForm,
    RawClockPunchForm,
    )
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse
import os
from decouple import config

import logging
logger = logging.getLogger(__name__)

def clock(request, **kwargs):
    """Clock button which creates ClockPunch object."""
    current_timesheet = Timesheet.objects.filter(user=request.user,
                                  pay_period_start__lte=date.
                                  today()).order_by('-pay_period_start')[0]
    current_day = Day.objects.filter(timesheet=current_timesheet,
                                     day__startswith=date.
                                     today()).order_by('-day')[0]
    try:
        '''If the last clock was in, create a clock out, else create
        clock in. If no clock(AttributeError, out of range) create a
        clock in also. This ones kinda wet too.'''
        last_clock = ClockPunch.objects.filter(date_time__lt=datetime.now(),
                                               user=request.user).first().clock
        if last_clock == True:
            ClockPunch.objects.create(clock=False, time=datetime.now().time(),
                                      date_time=timezone.now(),
                                      user=request.user,
                                      timesheet=current_timesheet,
                                      day=current_day)
            messages.success(request, f'Successfully Clocked Out!')
        else:
            ClockPunch.objects.create(clock=True, time=datetime.now().time(),
                                      date_time=timezone.now(),
                                      user=request.user,
                                      timesheet=current_timesheet,
                                      day=current_day)
            messages.success(request, f'Successfully Clocked In!')
    except AttributeError:
        ClockPunch.objects.create(clock=True, time=datetime.now().time(),
                                  date_time=timezone.now(),
                                  user=request.user,
                                  timesheet=current_timesheet,
                                  day=current_day)
        messages.success(request, f'Successfully Clocked In!')
    if kwargs:
        '''If the pk comes in from the timesheet detail, go back to that page.
        Else go home. Check out urlpatterns'''
        return redirect('timesheets:timesheet-detail', kwargs.get('pk', ''))
    else:
        return redirect('timesheets:timesheets-home')

def change_clock(request, **kwargs):
    '''Button on clockpunch detail page that changes clock from in to out and
    visa versa.'''
    clock_punch = ClockPunch.objects.get(pk=kwargs["pk"])
    timesheet_pk = clock_punch.timesheet.id
    if clock_punch.clock == True:
        clock_punch.clock = False
    elif clock_punch.clock == False:
        clock_punch.clock = True
    clock_punch.save()
    return redirect('timesheets:clockpunch-detail', timesheet_pk, kwargs.get('pk', ''))

class TimesheetListView(LoginRequiredMixin, ListView):
    model = Timesheet
    template_name = 'timesheets/home.html'
    paginate_by = 5

    # def get_queryset(self):
    #     return (Timesheet.objects.filter(user=self.request.user).
    #                               order_by('-pay_period_start'))

    def get_context_data(self, **kwargs):
        '''last_clock will return if the last clockpunch was in/out in order to
        display the correct button. timesheet_old True if there's no
        timesheet for the current day. Then create TM instead of clock button'''
        context = super().get_context_data(**kwargs)
        try:
            timesheet_list = (Timesheet.objects.filter(user=self.request.user).order_by('-pay_period_start'))
            paginator = Paginator(timesheet_list, 5)

            page_number = self.request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            context['count'] = paginator.count
            context['page_obj'] = page_obj
            current_timesheet = Timesheet.objects.filter(user=self.
                                request.user, pay_period_start__lte=date.
                                today()).order_by('-pay_period_start')[0]
            if current_timesheet.pay_period_end > date.today():
                context['timesheet_old'] = False
            else:
                context['timesheet_old'] = True

            context['timesheets'] = timesheet_list
            if ClockPunch.objects.filter(date_time__lt=datetime.now()).first():
                context['last_clock'] = (ClockPunch.objects.filter(date_time__lt=
                                         datetime.now()).first().clock)
            else:
                context['last_clock'] = False
        except IndexError:
            context['no_timesheet'] = True
        return context

class TimesheetDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Timesheet  # <app>/<model>_<viewtype>.html
    # context_object_name = 'days'
    #
    # def get_queryset(self):
    #     return (Timesheet.objects.filter(user=self.request.user).
    #                               order_by('-pay_period_start'))
    def test_func(self):
        timesheet = self.get_object()
        if self.request.user == timesheet.user:
            return True
        return False

    def get_context_data(self, **kwargs):
        #TODO When clockpunch is created before the last one, we get IndexError
        '''This is the more modular table created. Makes nested lists in
        context['punch_list']. These contain all the clock punches for
        that table row(first position) for the timesheet. All places in the
        table without punches get filled in with "No Punch". Min positions for
        the table is 4. Max is mac_punches. last_clock, pretty obvy. If last
        clockpunch exist make last_clock same as that. Else False. Used to
        determine if new clockpunch is in or out.'''
        context = super().get_context_data(**kwargs)

        # Add in a QuerySet
        day_set = self.object.day_set.all().order_by('day')
        context['punch_list'] = []  #List of list. Index = the clock punch of the day
                                    # Iterates through each day for that punch position (ex. 1(first punch): mon time, tues time etc.)
        max_punch_list = []
        for day in day_set:
            max_punch_list.append(len(list(day.clockpunch_set.all())))
        max_punches = max(max_punch_list)

        i = 1
        while i <= max_punches or i <= 4:
            punches = []
            for day in day_set:
                try:
                    punches.append(list(day.clockpunch_set.all())[-i])
                except IndexError:
                    punches.append("No Punch")
            i += 1
            context['punch_list'].append(punches)

        context['timesheet_days']    = day_set
        context['current_timesheet'] = Timesheet.objects.filter(user=self.
                                       request.user, pay_period_start__lt=date.
                                       today()).order_by('-pay_period_start')[0]
        context['today']             = date.today()

        if ClockPunch.objects.filter(date_time__lt=datetime.now()).first():
            context['last_clock'] = (ClockPunch.objects.filter(date_time__lt=
                                     datetime.now()).first().clock)
        else:
             context['last_clock'] = False
        if self.object.pay_period_start <= date.today() and self.object.pay_period_end >= date.today():
            context['today_in_timesheet'] = True
        else:
            context['today_in_timesheet'] = False

        return context

class TimesheetCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Timesheet  # in this case it's <app>/<model>_form.html
    form_class = TimesheetForm
    success_message = "Timesheet Created!"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class TimesheetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Timesheet
    form_class = TimesheetForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def test_func(self):
        timesheet = self.get_object()
        if self.request.user == timesheet.user:
            return True
        return False

class TimesheetDeleteView(
    LoginRequiredMixin,
    SuccessMessageMixin,
    UserPassesTestMixin,
    DeleteView
    ):
    model = Timesheet
    success_url = reverse_lazy('timesheets:timesheets-home')
    success_message = "Timesheet Deleted!"

    def test_func(self):
        timesheet = self.get_object()
        if self.request.user == timesheet.user:
            return True
        return False

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        logger.debug(obj)
        logger.debug(obj.__dict__)
        return super(TimesheetDeleteView, self).delete(request, *args, **kwargs)

class ClockPunchDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ClockPunch  # <app>/<model>_<viewtype>.html

    def test_func(self):
        clockpunch = self.get_object()
        if self.request.user == clockpunch.timesheet.user:
            return True
        return False

    # def get_context_data(self, **kwargs):
    #     '''Grabs the day_id from url. Comes through kwargs.'''
    #     context = super(ClockPunchDetailView, self).get_context_data(**kwargs)
    #     day_id = Day.objects.get(id=self.kwargs.get('day_id', ''))
    #     context['day_id'] = day_id
    #     return context

class ClockPunchCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    '''This ones not displaying the radio buttons for clock. Was using
    def clockpunch instead. Doesn't look as good but the buttons work.'''
    '''Ended up creating buttons for each day instead and automating the clock
    in/out. see below. Looks good and is easy.'''
    model = ClockPunch  # in this case it's <app>/<model>_form.html
    form_class = RawClockPunchForm
    success_message = "Clock Punch Created!"

    # New punch different color?

    def form_valid(self, form):
        '''If there's a clock-in for the last clock
        then it makes the instance clock-out(False). Else if no clock or last
        clock was clock-out then it makes instance clock-in(True).
        This one below was before the nightshift change. Can't rely on just
        the day, last clock may come from day or timesheet before current.
        Instead took time from the form, combined to make datetime, then found
        the clock of the punch prior.'''
        day = Day.objects.get(id=self.kwargs.get('day_id', ''))
        user = self.request.user
        # try:
        #     if day.clockpunch_set.all().first().clock == True: #first == most recent
        #         form.instance.clock = False
        #     else:
        #         form.instance.clock = True
        # except AttributeError:
        #     form.instance.clock = True
        date_time = timezone.make_aware(datetime.combine(day.day,
                                        form.cleaned_data['time']))
        form.instance.date_time = date_time
        form.instance.user      = user
        form.instance.day       = day
        form.instance.timesheet = Timesheet.objects.get(id=self.
                                                        kwargs.get('pk', ''))
        try:
            last_clock = ClockPunch.objects.filter(date_time__lt=date_time,
                                                   user=user).first().clock
            if last_clock == True:
                form.instance.clock = False
            else:
                form.instance.clock = True
        except AttributeError:
            form.instance.clock = True
        '''need to change future punches.clock'''
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        '''Grabs the day_id from url. Comes through kwargs.'''
        context = super(ClockPunchCreateView, self).get_context_data(**kwargs)
        timesheet = Timesheet.objects.get(id=self.kwargs.get('pk', ''))
        day = Day.objects.get(id=self.kwargs.get('day_id', ''))
        context['timesheet'] = timesheet
        context['day']       = day
        return context

    def get_success_url(self):
        return reverse('timesheets:timesheet-detail',
                        kwargs={'pk': self.kwargs.get('pk', '')})

class ClockPunchUpdateView(
    LoginRequiredMixin,
    SuccessMessageMixin,
    UserPassesTestMixin,
    UpdateView
    ):
    model = ClockPunch
    form_class = RawClockPunchForm
    success_message = "Clock Punch Updated!"

    def form_valid(self, form):
        '''Updates the datetime with the time. What about the clock?
        when we put the same try, except at above in create view, the last
        clock pulled this instance and gave the wrong clock. Do we really
        need to update the clock? Can we assume the update won't change the
        position of the clock? If so it would be better to delete then make
        again, similar to the time sheets. Something like, if this time is
        outside the one before or the one after, throw an error.'''
        day = form.instance.day
        user = self.request.user
        form.instance.timesheet.user = user
        date_time = timezone.make_aware(datetime.combine(day.day,
                                        form.cleaned_data['time']))
        form.instance.date_time = date_time
        return super().form_valid(form)

    def test_func(self):
        clockpunch = self.get_object()
        if self.request.user == clockpunch.timesheet.user:
            return True
        return False

    def get_success_url(self):
        '''Go back to current timesheet'''
        return reverse('timesheets:timesheet-detail',
                        kwargs={'pk': self.kwargs.get('tm_pk', '')})

class ClockPunchDeleteView(
    LoginRequiredMixin,
    SuccessMessageMixin,
    UserPassesTestMixin,
    DeleteView
    ):
    model = ClockPunch
    success_message = "Clock Punch Deleted!"

    # def form_valid(self, form):
    #     '''change future clocks'''
    #     pass

    def test_func(self):
        clockpunch = self.get_object()
        if self.request.user == clockpunch.timesheet.user:
            return True
        return False

    def delete(self, request, *args, **kwargs):
        '''Trying to get the obj to display in the success message'''
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        logger.debug(obj)
        logger.debug(obj.__dict__)
        return super(ClockPunchDeleteView, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        '''Go back to current timesheet'''
        return reverse('timesheets:timesheet-detail',
                        kwargs={'pk': self.kwargs.get('tm_pk', '')})

def about(request):
    return render(request, 'timesheets/about.html', {'title': 'About'})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request,
                        f'Account created for {username}. You can now log in!')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'timesheets/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'timesheets/profile.html', context)

# def timesheet_detail(request, user_id):
#     context = {
#         'timesheet': Timesheet.objects.filter(user_id=user_id)
#     }
#
#     return render(request, 'timesheets/timesheet_detail.html', context)

# def home(request):
#     context = {
#         'timesheets': Timesheet.objects.all()
#     }
#     return render(request, 'timesheets/home.html', context)

# def clockpunch(request, pk):
#     '''Used create view instead. Maybe take out later.'''
#     form = RawClockPunchForm()
#     current_timesheet = Timesheet.objects.filter(user=request.user, id=pk)
#     if request.method == 'POST':
#         form = RawClockPunchForm(data=request.POST)
#         if form.is_valid():
#             print(form.cleaned_data)
#             ClockPunch.objects.create(**form.cleaned_data,
#                                       timesheet=current_timesheet)
#         else: print(form.errors)
#     context = {
#         "form": form,
#         "timesheet": current_timesheet
#     }
#     return render(request, "timesheets/clockpunch.html", context)
