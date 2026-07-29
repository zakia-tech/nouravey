from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.map_view, name='map'),
    path('api/map-data/', views.map_data, name='map-data'),
    path('api/subcounty-boundaries/', views.subcounty_boundaries, name='subcounty-boundaries'),
    path('api/ward-boundary/<str:ward_key>/', views.ward_boundary, name='ward-boundary'),
]
