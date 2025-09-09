from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:session_id>/', views.dummy_payment_page, name='chat_dummy_pay'),
]