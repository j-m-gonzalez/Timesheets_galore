from django.urls import path
from .views import (
    TimesheetListView,
    TimesheetDetailView,
    TimesheetCreateView,
    TimesheetUpdateView,
    TimesheetDeleteView,
    ClockPunchDetailView,
    ClockPunchCreateView,
    ClockPunchUpdateView,
    ClockPunchDeleteView,
    )
from . import views

app_name = 'timesheets'

urlpatterns = [
    path('', TimesheetListView.as_view(), name='timesheets-home'),
    path('<int:pk>/', TimesheetDetailView.as_view(), name='timesheet-detail'),
    path('new/', TimesheetCreateView.as_view(), name='timesheet-create'),
    path('clock/', views.clock, name='timesheet-clock'),
    path('clock/<int:pk>/', views.clock, name='timesheet-detail-clock'),
    path('change_clock/<int:pk>/', views.change_clock, name='clockpunch-detail-change_clock'),
    # path('clock_out/', views.clock_out, name='timesheet-clock_out'),
    #path('raw_clock/', views.clockpunch, name='timesheet-raw_clockpunch'),
    path('<int:pk>/update/', TimesheetUpdateView.as_view(), name='timesheet-update'),
    path('<int:pk>/delete/', TimesheetDeleteView.as_view(), name='timesheet-delete'),
    path('about/', views.about, name='timesheets-about'),
    path('<int:tm_pk>/<int:pk>/', ClockPunchDetailView.as_view(), name='clockpunch-detail'),
    path('<int:pk>/<int:day_id>/clock/', ClockPunchCreateView.as_view(), name='clockpunch-create'),
    path('<int:tm_pk>/<int:pk>/update/', ClockPunchUpdateView.as_view(), name='clockpunch-update'),
    path('<int:tm_pk>/<int:pk>/delete/', ClockPunchDeleteView.as_view(), name='clockpunch-delete'),
    #path('<int:user_id>/timesheets/', views.home, name='timesheets-timesheets'),
    #path('<int:user_id>/timesheets/<int:timesheet_id>', views.timesheet_detail, name='timesheets-timesheet_detail'),
    #path('<int:user_id>/', views.profile, name='timesheets_profile'),
]
