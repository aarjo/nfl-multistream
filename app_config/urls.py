from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('nfldata', views.nfldata, name='nfldata'),
]