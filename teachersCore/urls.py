from django.urls import path

from .views import *

urlpatterns = [
    path('login/',LoginView.as_view(),name='login'),
    path('refresh/',RefreshTokenView.as_view(),name='refresh-token'),
    path('logout/',logout_view,name='logout'),

    path("teachers/", ListTeachers, name="list_teachers"),
    path("teachers/create/", Create_teacher, name="create_teacher"),
    path("teachers/<int:pk>/", GetTeacher, name="get_teacher"),
    path("teachers/<int:pk>/update/", Update_teacher, name="update_teacher"),
    path("teachers/<int:pk>/delete/", Delete_teacher, name="delete_teacher"),

    path("attendance/check-in/", Check_in, name="check_in"),
    path("attendance/<int:pk>/check-out/", Check_out, name="check_out"),
    path("attendance/my/", My_attendance, name="my_attendance"),

    path("duties/periods/", List_duty_periods, name="list_duty_periods"),
    path("duties/periods/create/", Create_duty_period, name="create_duty_period"),

    path("duties/assign/<int:period_id>/", Assign_duty, name="assign_duty"),
    path("duties/assignments/", List_assignments, name="list_assignments"),
    path("duties/my/", My_duty, name="my_duty"),

    path("report/teacher/<int:teacher_id>/pdf/",WeeklyReport,name='report') # /api/reports/teacher/5/pdf/?start_date=2025-08-12&end_date=2025-08-18


]