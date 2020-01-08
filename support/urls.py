from django.urls import path
from support import views

app_name = 'support'

urlpatterns = [
    path('', views.dummy, name='dummy'),
]
