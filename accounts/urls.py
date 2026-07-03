from django.urls import path

from . import views


app_name = 'accounts'


urlpatterns = [

    path(
        'register/',
        views.register_view,
        name='register'
    ),

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    path(
        'dashboard/',
        views.dashboard_view,
        name='dashboard'
    ),

    path(
        'leaderboard/',
        views.leaderboard_view,
        name='leaderboard'
    ),

    path(
        'subscribe/',
        views.subscribe_view,
        name='subscribe'
    ),

    path(
        'payment-success/',
        views.payment_success_view,
        name='payment_success'
    ),
]