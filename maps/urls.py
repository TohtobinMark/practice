from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('add/', views.add_location, name='add_location'),
    path('edit/<int:pk>/', views.edit_location, name='edit_location'),
    path('delete/<int:pk>/', views.delete_location, name='delete_location'),
    path('add-request/', views.add_request, name='add_request'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('cancel-request/<int:pk>/', views.cancel_request, name='cancel_request'),
]