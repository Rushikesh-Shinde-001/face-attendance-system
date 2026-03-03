from django.db import models
from datetime import date

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Student(models.Model):
    YEAR_CHOICES = [
        ('FY', 'First Year'),
        ('SY', 'Second Year'),
        ('TY', 'Third Year'),
    ]
    
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    year = models.CharField(max_length=10, choices=YEAR_CHOICES)
    face_image = models.ImageField(upload_to='faces/', blank=True, null=True)
    
    # Attendance Permission
    can_mark_attendance = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student_id} - {self.name}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'date']
    
    def __str__(self):
        return f"{self.student.name} - {self.date}"