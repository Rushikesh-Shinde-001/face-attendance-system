from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Department, Student, Attendance
from datetime import date, datetime
from django.http import HttpResponse, JsonResponse
import csv
import os
import cv2
import numpy as np
import time

# ==================== STUDENT PORTAL ====================

def student_login(request):
    """Student login - फक्त student ID आणि email ने"""
    # Clear previous student session
    if 'student_id' in request.session:
        del request.session['student_id']
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        email = request.POST.get('email')
        
        print(f"Student Login Attempt - ID: {student_id}, Email: {email}")
        
        try:
            # Student शोधा
            student = Student.objects.get(student_id=student_id, email=email)
            
            # Session मध्ये store करा
            request.session['student_id'] = student.id
            request.session['student_name'] = student.name
            
            messages.success(request, f'Welcome {student.name}!')
            return redirect('student_dashboard')
            
        except Student.DoesNotExist:
            messages.error(request, 'Invalid Student ID or Email')
    
    return render(request, 'attendance/student_login.html')


def student_dashboard(request):
    """Student Dashboard - फक्त स्वतःची माहिती"""
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    try:
        student = Student.objects.get(id=request.session['student_id'])
    except Student.DoesNotExist:
        return redirect('student_login')
    
    today = date.today()
    
    # Today's attendance check
    today_attendance = Attendance.objects.filter(
        student=student,
        date=today
    ).first()
    
    # Total attendance
    total_attendance = Attendance.objects.filter(student=student).count()
    
    # Recent attendance
    recent_attendance = Attendance.objects.filter(
        student=student
    ).order_by('-date')[:10]
    
    context = {
        'student': student,
        'today_attendance': today_attendance,
        'total_attendance': total_attendance,
        'recent_attendance': recent_attendance,
        'can_mark': student.can_mark_attendance,
        'today': today,
    }
    return render(request, 'attendance/student_dashboard.html', context)


def mark_attendance(request):
    """Student manual attendance mark करतो"""
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    try:
        student = Student.objects.get(id=request.session['student_id'])
    except Student.DoesNotExist:
        return redirect('student_login')
    
    # Check permission
    if not student.can_mark_attendance:
        messages.error(request, '⛔ Attendance permission is OFF. Please contact admin.')
        return redirect('student_dashboard')
    
    today = date.today()
    
    # Check if already marked today
    already_marked = Attendance.objects.filter(
        student=student,
        date=today
    ).exists()
    
    if request.method == 'POST':
        if not already_marked:
            # Mark attendance
            Attendance.objects.create(
                student=student,
                date=today,
                time=datetime.now().time()
            )
            messages.success(request, '✅ Attendance marked successfully!')
        else:
            messages.warning(request, '⚠️ You have already marked attendance today')
        
        return redirect('student_dashboard')
    
    context = {
        'student': student,
        'already_marked': already_marked,
    }
    return render(request, 'attendance/mark_attendance.html', context)


def student_face_attendance(request):
    """Student face ने attendance - 5 second auto capture"""
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    try:
        student = Student.objects.get(id=request.session['student_id'])
    except Student.DoesNotExist:
        return redirect('student_login')
    
    # Check permission
    if not student.can_mark_attendance:
        messages.error(request, '⛔ Attendance permission is OFF')
        return redirect('student_dashboard')
    
    # Check if already marked today
    if Attendance.objects.filter(student=student, date=date.today()).exists():
        messages.warning(request, '⚠️ Already marked today')
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        try:
            # Load face detector
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Start webcam
            video = cv2.VideoCapture(0)
            
            if not video.isOpened():
                messages.error(request, '❌ Camera not accessible')
                return redirect('mark_attendance')
            
            # 5 second timer
            start_time = time.time()
            duration = 5  # फक्त 5 सेकंद
            recognized = False
            
            messages.info(request, '📸 Camera will run for 5 seconds... Look at camera!')
            
            while time.time() - start_time < duration:
                ret, frame = video.read()
                if not ret:
                    continue
                
                # Face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                # Calculate remaining time
                remaining = int(duration - (time.time() - start_time))
                if remaining < 0:
                    remaining = 0
                
                # Draw rectangle on faces
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, "✅ FACE DETECTED", (x, y-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # जर face दिसला तर लगेच attendance mark करा
                    if len(faces) > 0:
                        Attendance.objects.create(
                            student=student,
                            date=date.today(),
                            time=datetime.now().time()
                        )
                        recognized = True
                        
                        # Show success message on frame
                        cv2.putText(frame, "✅ ATTENDANCE MARKED!", (100, 200),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                        cv2.imshow('Face Attendance', frame)
                        cv2.waitKey(2000)  # 2 second pause
                        break
                
                # Display timer and instructions
                cv2.putText(frame, f"⏱️ Time: {remaining}s", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, "👤 Look at camera...", (10, 60),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                if len(faces) > 0:
                    cv2.putText(frame, f"✅ Face Detected!", (10, 90),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                cv2.imshow('Face Attendance', frame)
                
                if recognized:
                    break
                    
                if cv2.waitKey(1) & 0xFF == 27:  # ESC to cancel
                    break
            
            video.release()
            cv2.destroyAllWindows()
            
            if recognized:
                messages.success(request, '✅ Face detected! Attendance marked successfully!')
            else:
                messages.error(request, '❌ No face detected. Please try again.')
            
        except Exception as e:
            messages.error(request, f'❌ Camera error: {str(e)}')
        
        return redirect('student_dashboard')
    
    return render(request, 'attendance/student_face_attendance.html', {'student': student})


def my_attendance(request):
    """Student आपली attendance history बघतो"""
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    try:
        student = Student.objects.get(id=request.session['student_id'])
    except Student.DoesNotExist:
        return redirect('student_login')
    
    attendance = Attendance.objects.filter(student=student).order_by('-date')
    
    context = {
        'student': student,
        'attendance': attendance,
        'total': attendance.count(),
    }
    return render(request, 'attendance/my_attendance.html', context)


def my_profile(request):
    """Student आपला profile बघतो"""
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    try:
        student = Student.objects.get(id=request.session['student_id'])
    except Student.DoesNotExist:
        return redirect('student_login')
    
    total_attendance = Attendance.objects.filter(student=student).count()
    
    context = {
        'student': student,
        'total_attendance': total_attendance,
    }
    return render(request, 'attendance/my_profile.html', context)


def student_logout(request):
    """Student logout"""
    if 'student_id' in request.session:
        del request.session['student_id']
        del request.session['student_name']
        messages.success(request, 'Logged out successfully')
    
    return redirect('student_login')


# ==================== ADMIN PORTAL ====================

def admin_login(request):
    """Admin login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username == 'admin' and password == 'admin@123':
            request.session['is_admin'] = True
            messages.success(request, 'Welcome Admin!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')
    
    return render(request, 'attendance/admin_login.html')


def admin_dashboard(request):
    """Admin Dashboard"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    students = Student.objects.all().order_by('-created_at')
    total_students = students.count()
    today_attendance = Attendance.objects.filter(date=date.today()).count()
    
    context = {
        'students': students,
        'total_students': total_students,
        'today_attendance': today_attendance,
    }
    return render(request, 'attendance/admin_dashboard.html', context)


def students_list(request):
    """Admin सगळे students बघतो"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    students = Student.objects.all().order_by('-created_at')
    
    context = {
        'students': students,
    }
    return render(request, 'attendance/students_list.html', context)


def register_face(request):
    """Admin नवीन student add करतो - फक्त CS साठी"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        department_id = request.POST.get('department_id')
        year = request.POST.get('year')
        face_image = request.FILES.get('face_image')
        
        # Validation
        if Student.objects.filter(student_id=student_id).exists():
            messages.error(request, 'Student ID already exists')
            return redirect('register_face')
        
        if Student.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('register_face')
        
        # Get department
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            messages.error(request, 'Department not found')
            return redirect('register_face')
        
        # Create student
        Student.objects.create(
            student_id=student_id,
            name=name,
            email=email,
            department=department,
            year=year,
            face_image=face_image,
            can_mark_attendance=False
        )
        
        messages.success(request, f'Student {name} added successfully!')
        return redirect('students_list')
    
    # GET request - फक्त CS department दाखवा
    departments = Department.objects.filter(code='CS')
    years = ['FY', 'SY', 'TY']
    
    context = {
        'departments': departments,
        'years': years,
    }
    return render(request, 'attendance/register_face.html', context)


def student_detail(request, student_id):
    """View individual student details"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    student = get_object_or_404(Student, id=student_id)
    attendance = Attendance.objects.filter(student=student).order_by('-date')
    
    context = {
        'student': student,
        'attendance': attendance,
        'total_days': attendance.count(),
    }
    return render(request, 'attendance/student_detail.html', context)


def student_delete(request, student_id):
    """Delete a student"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        student.delete()
        messages.success(request, f'Student {student.name} deleted')
        return redirect('students_list')
    
    context = {'student': student}
    return render(request, 'attendance/student_confirm_delete.html', context)


def toggle_permission(request, student_id):
    """Individual student permission toggle"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    student = get_object_or_404(Student, id=student_id)
    student.can_mark_attendance = not student.can_mark_attendance
    student.save()
    
    status = 'ON' if student.can_mark_attendance else 'OFF'
    messages.success(request, f'✅ Permission for {student.name} is now {status}')
    
    return redirect('students_list')


# ==================== ADMIN FACE ATTENDANCE ====================

def admin_face_attendance(request):
    """Admin face ने student ची attendance घेतो - 5 second auto capture"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        
        try:
            student = Student.objects.get(id=student_id)
            
            # Check if already marked today
            if Attendance.objects.filter(student=student, date=date.today()).exists():
                messages.warning(request, f'{student.name} already marked today')
                return redirect('take_attendance')
            
            # Load face detector
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Start webcam
            video = cv2.VideoCapture(0)
            
            if not video.isOpened():
                messages.error(request, '❌ Camera not accessible')
                return redirect('take_attendance')
            
            # 5 second timer
            start_time = time.time()
            duration = 5
            recognized = False
            
            messages.info(request, f'📸 Camera will run for 5 seconds. Ask {student.name} to look at camera...')
            
            while time.time() - start_time < duration:
                ret, frame = video.read()
                if not ret:
                    continue
                
                # Face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                # Calculate remaining time
                remaining = int(duration - (time.time() - start_time))
                
                # Draw rectangle on faces
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"{student.name}", (x, y-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    if len(faces) > 0:
                        Attendance.objects.create(
                            student=student,
                            date=date.today(),
                            time=datetime.now().time()
                        )
                        recognized = True
                        
                        cv2.putText(frame, f"✅ ATTENDANCE MARKED!", (100, 200),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                        cv2.imshow('Admin Face Attendance', frame)
                        cv2.waitKey(2000)
                        break
                
                # Display timer
                cv2.putText(frame, f"⏱️ Time: {remaining}s", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f"👤 Student: {student.name}", (10, 60),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow('Admin Face Attendance', frame)
                
                if recognized:
                    break
                    
                if cv2.waitKey(1) & 0xFF == 27:
                    break
            
            video.release()
            cv2.destroyAllWindows()
            
            if recognized:
                messages.success(request, f'✅ Face detected! Attendance marked for {student.name}')
            else:
                messages.error(request, '❌ No face detected. Please try again.')
            
        except Student.DoesNotExist:
            messages.error(request, 'Student not found')
        except Exception as e:
            messages.error(request, f'❌ Camera error: {str(e)}')
        
        return redirect('take_attendance')
    
    # GET request - show student selection
    students = Student.objects.all().order_by('name')
    today_marked = Attendance.objects.filter(date=date.today()).values_list('student_id', flat=True)
    
    context = {
        'students': students,
        'today_marked': today_marked,
    }
    return render(request, 'attendance/admin_face_attendance.html', context)


# ==================== BULK PERMISSION FUNCTIONS ====================

def bulk_permission_on(request):
    """All students ची permission ON करा"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    count = Student.objects.all().update(can_mark_attendance=True)
    messages.success(request, f'✅ {count} students की permission ON केली!')
    return redirect('students_list')


def bulk_permission_off(request):
    """All students ची permission OFF करा"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    count = Student.objects.all().update(can_mark_attendance=False)
    messages.success(request, f'❌ {count} students की permission OFF केली!')
    return redirect('students_list')


def bulk_permission_toggle(request):
    """All students ची permission टॉगल करा"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    any_on = Student.objects.filter(can_mark_attendance=True).exists()
    
    if any_on:
        count = Student.objects.all().update(can_mark_attendance=False)
        messages.success(request, f'❌ {count} students की permission OFF केली!')
    else:
        count = Student.objects.all().update(can_mark_attendance=True)
        messages.success(request, f'✅ {count} students की permission ON केली!')
    
    return redirect('students_list')


# ==================== ATTENDANCE FUNCTIONS ====================

def take_attendance(request):
    """Take attendance (admin) - Manual + Face options"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        try:
            student = Student.objects.get(id=student_id)
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                date=date.today()
            )
            
            if created:
                messages.success(request, f'✅ Marked {student.name} present')
            else:
                messages.info(request, f'⚠️ {student.name} already marked')
        except Student.DoesNotExist:
            messages.error(request, 'Student not found')
        
        return redirect('take_attendance')
    
    students = Student.objects.all().order_by('name')
    today_marked = Attendance.objects.filter(
        date=date.today()
    ).values_list('student_id', flat=True)
    
    context = {
        'students': students,
        'today_marked': today_marked,
    }
    return render(request, 'attendance/take_attendance.html', context)


def view_attendance(request):
    """View attendance records"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    selected_date = request.GET.get('date', str(date.today()))
    
    try:
        filter_date = date.fromisoformat(selected_date)
    except:
        filter_date = date.today()
    
    attendance = Attendance.objects.filter(
        date=filter_date
    ).select_related('student').order_by('student__name')
    
    context = {
        'attendance': attendance,
        'selected_date': filter_date,
        'total': attendance.count(),
    }
    return render(request, 'attendance/view_attendance.html', context)


def export_attendance(request):
    """Export attendance to CSV"""
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    date_from = request.GET.get('from', str(date.today()))
    date_to = request.GET.get('to', str(date.today()))
    
    try:
        from_date = date.fromisoformat(date_from)
        to_date = date.fromisoformat(date_to)
    except:
        from_date = date.today()
        to_date = date.today()
    
    attendance = Attendance.objects.filter(
        date__range=[from_date, to_date]
    ).select_related('student').order_by('-date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{from_date}_to_{to_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Student ID', 'Name', 'Year', 'Time'])
    
    for record in attendance:
        writer.writerow([
            record.date,
            record.student.student_id,
            record.student.name,
            record.student.get_year_display(),
            record.time.strftime('%H:%M:%S')
        ])
    
    return response


# ==================== LOGOUT ====================

def admin_logout(request):
    """Admin logout"""
    if 'is_admin' in request.session:
        del request.session['is_admin']
        messages.success(request, 'Admin logged out')
    
    return redirect('admin_login')


# ==================== UTILITY FUNCTIONS ====================

def train_model(request):
    """Train face model - Coming soon"""
    messages.info(request, 'Model training feature coming soon')
    return redirect('admin_dashboard')


def test_camera(request):
    """Test camera - Coming soon"""
    messages.info(request, 'Camera test feature coming soon')
    return redirect('admin_dashboard')