from django.urls import path
from .views import register, login, get_current_user, logout

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('me/', get_current_user, name='current-user'),
    path('logout/', logout, name='logout'),
]

