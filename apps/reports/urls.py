from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('submit/', views.submit_report, name='submit'),
]
