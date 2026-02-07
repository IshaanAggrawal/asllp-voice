from django.urls import path
from .views import register, get_current_user

urlpatterns = [
    path('register/', register, name='register'),
    path('me/', get_current_user, name='current-user'),
]
