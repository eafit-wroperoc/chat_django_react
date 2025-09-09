from django.urls import path
from . import views

urlpatterns = [
    path('session/', views.create_session, name='create_session'),
    path('message/', views.process_message, name='process_message'),
    path('heartbeat/', views.heartbeat, name='heartbeat'),
]