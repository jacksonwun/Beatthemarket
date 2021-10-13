from django.urls import path
from django.conf.urls import include
from . import views

urlpatterns = [
    path('', views.Dash_board),

    path('dashboard/', views.Dash_board, name="dashboard"),
    path('realTimeInfo/', views.Real_Time_Info, name="realTimeInfo"),
    path('warrant/', views.Warrant, name="warrant"),
    path('settings/', views.Settings, name="settings"),
]