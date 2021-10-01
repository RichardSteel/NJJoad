'''Defines URL patterns for JOAD application'''

from django.urls import path
from . import views

app_name='waxobejoad'
urlpatterns = [
    #Home page
    path('', views.index, name='index'),
    path('students/', views.students, name='students'),
    path('student/<int:student_id>/', views.student, name='student'),
    path('new_student/', views.new_student, name='new_student'),
    path('edit_student/<int:student_id>/', views.edit_student, name='edit_student'),
    path('enter_score/<int:student_id>/', views.enter_score, name='enter_score'),
    path('save_student_score/', views.save_student_score, name='save_student_score'),
    path('new_event/', views.new_event, name='new_event'),
    path('new_session/', views.new_session, name='new_session'),
    path('assign_student/', views.assign_student, name='assign_student'),
    path('sessions/', views.sessions, name='sessions'),
    path('pay_invoice/', views.pay_invoice, name='pay_invoice'),
    path('session_mgnt/', views.session_mgnt, name='session_mgnt'),
    path('list_students/', views.list_students, name='list_students'),
]