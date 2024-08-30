from django.urls import path
from .views import google_login, google_callback, get_user_details, logout

urlpatterns = [
    path('auth/login/', google_login, name='google-login'),
    path('auth/callback/', google_callback, name='google-callback'),
    path('user-details/', get_user_details, name='user-details'),
    path('logout/', logout, name='logout'),
]