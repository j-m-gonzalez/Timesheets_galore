from django.contrib import admin
from .models import Profile, Timesheet, ClockPunch, Day, Week

class DayAdmin(admin.ModelAdmin):
    list_display = ('day', 'timesheet', 'total_hours',)
    readonly_fields = ('total_hours',)

admin.site.register(Profile)
admin.site.register(Timesheet)
admin.site.register(Day, DayAdmin)
admin.site.register(Week)
admin.site.register(ClockPunch)
