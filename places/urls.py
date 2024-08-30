from django.urls import path
from .views import search_businesses

urlpatterns = [
    path('search/', search_businesses, name='search_businesses'),
]
