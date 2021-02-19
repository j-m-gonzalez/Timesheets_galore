from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.admin import widgets
from .models import Profile, Timesheet, ClockPunch, Day

class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        kwargs["format"] = "%Y-%m-%dT%H:%M"
        super().__init__(**kwargs)

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=250)
    last_name = forms.CharField(max_length=250)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model  = Profile
        fields = ['image', 'position']

class TimesheetForm(forms.ModelForm):
    pay_period_start = forms.DateField(widget=forms.widgets.
                                       DateInput(attrs={'type': 'date'}))
    pay_period_end   = forms.DateField(widget=forms.widgets.
                                       DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Timesheet
        fields = ['pay_period_start', 'pay_period_end']

class RawClockPunchForm(forms.ModelForm):
    time = forms.TimeField(widget=forms.widgets.
                                       TimeInput(attrs={'type': 'time',
                                                        'value': '12:00'}))
    #day = forms.ChoiceField(widget=forms.Select, choices=(Day.objects.all()))
    # date_time = forms.DateTimeField(widget=forms.widgets.
    #                                    DateTimeInput(attrs={'type': 'datetime-local'}))

    # clock = forms.BooleanField()
    # clock = forms.BooleanField(widget=forms.RadioSelect(choices=
    #                           [(True, 'Clock in'), (False, 'Clock out')]))
    # day = forms.ModelChoiceField(queryset = Day.objects.all() )
    # How to only show days for this timesheet?

    class Meta:
        model = ClockPunch
        fields = ['time']
