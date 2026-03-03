from django.urls import path
from . import views

urlpatterns = [
    # ========== STUDENT PORTAL ==========
    path('', views.student_login, name='student_login'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('student-face-attendance/', views.student_face_attendance, name='student_face_attendance'),
    path('my-attendance/', views.my_attendance, name='my_attendance'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('student-logout/', views.student_logout, name='student_logout'),
    
    # ========== ADMIN PORTAL ==========
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('students/', views.students_list, name='students_list'),
    path('register/', views.register_face, name='register_face'),
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('student/delete/<int:student_id>/', views.student_delete, name='student_delete'),
    path('toggle-permission/<int:student_id>/', views.toggle_permission, name='toggle_permission'),
    
    # ========== ADMIN FACE ATTENDANCE ==========
    path('admin-face-attendance/', views.admin_face_attendance, name='admin_face_attendance'),
    
    # ========== BULK PERMISSION ==========
    path('bulk-permission-on/', views.bulk_permission_on, name='bulk_permission_on'),
    path('bulk-permission-off/', views.bulk_permission_off, name='bulk_permission_off'),
    path('bulk-permission-toggle/', views.bulk_permission_toggle, name='bulk_permission_toggle'),
    
    # ========== ATTENDANCE ==========
    path('take-attendance/', views.take_attendance, name='take_attendance'),
    path('view-attendance/', views.view_attendance, name='view_attendance'),
    path('export-attendance/', views.export_attendance, name='export_attendance'),
    
    # ========== UTILITIES ==========
    path('train-model/', views.train_model, name='train_model'),
    path('test-camera/', views.test_camera, name='test_camera'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
]
