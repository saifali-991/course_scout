from django.urls import path

from . import views

urlpatterns = [
    path('google/', views.GoogleLoginView.as_view(), name='auth-google'),
    path('logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('me/', views.MeView.as_view(), name='auth-me'),
]