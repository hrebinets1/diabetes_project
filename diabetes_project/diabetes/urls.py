from django.urls import path
from . import views

urlpatterns = [
    path('auth_patient/', views.auth_patient, name='auth_patient'),
    path('auth_medic/', views.auth_medic, name='auth_medic'),
    path('', views.main_page, name='main_page'),
    path('register_medic/', views.register_medic, name='register_medic'),
    path('register_patient/', views.register_patient, name='register_patient'),
    path('main_medic_page/', views.main_medic_page, name='main_medic_page'),
    path('main_patient_page/', views.main_patient_page, name='main_patient_page'),
    path('logout', views.logout_view, name='logout')
]