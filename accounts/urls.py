from django.urls import path
from .views import register_view, dashboard_view,leaderboard_view
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'accounts'



urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),  # 👈 اصلاح اینجا
    path('dashboard/', dashboard_view, name='dashboard'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('logout/', views.user_logout, name='logout'),
]
