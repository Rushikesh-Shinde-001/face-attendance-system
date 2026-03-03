from django.contrib import admin
from .models import Department, Student, Attendance

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code']
    search_fields = ['name', 'code']
    list_filter = ['name']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'name', 'email', 'department', 'year', 'can_mark_attendance']
    search_fields = ['student_id', 'name', 'email']
    list_filter = ['department', 'year', 'can_mark_attendance']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'time']
    search_fields = ['student__name', 'student__student_id']
    list_filter = ['date']