from .models import ClockPunch, Timesheet
from datetime import datetime, date

def sidebar_to_context(request):
    '''Sends context to base.html to display the last clock and
    current_timesheet. If no timesheet or not logged in, display none.
    if no clock, display none for clock.'''
    if (request.user.is_authenticated and  #Below only evaled if 1st is true
            Timesheet.objects.filter(user=request.user)):
        current_timesheet = Timesheet.objects.filter(user=request.user,
                                      pay_period_start__lte=date.
                                      today()).order_by('-pay_period_start')[0]
        if ClockPunch.objects.filter(user=request.user):
            last_clockpunch = ClockPunch.objects.filter(user=request.user,
                                         date_time__lt=datetime.now()).first()
            if last_clockpunch.clock:
                clock_in_out = "Clock in"
            else:
                clock_in_out = "Clock out"
            return {
                'current_timesheet': current_timesheet,
                'clock_in_out': clock_in_out,
                'last_clockpunch': last_clockpunch.date_time,
            }
        else:
            return {
                'current_timesheet': current_timesheet,
                'clock_in_out': 'None',
                'last_clockpunch': 'None',
            }
    else:
        return {
            'current_timesheet': 'None',
            'clock_in_out': 'None',
            'last_clockpunch': 'None',
        }




# Ya know what's wierd, put last_clock accidently in base.html and it showed up
# with the correct boolean. How'd it get there?
