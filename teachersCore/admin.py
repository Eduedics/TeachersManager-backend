from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(Teacher)
admin.site.register(DutyPeriod)
admin.site.register(DutyAssignment)
admin.site.register(Attendance)
