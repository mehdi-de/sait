from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('', views.home, name='home'),

    path('about/', views.about, name='about'),

    path('quizzes/', views.quiz_list_view, name='quiz_list'),

    path('quiz/<int:pk>/start/', views.start_quiz_view, name='start_quiz'),

    path('quiz/<int:pk>/question/', views.quiz_question_view, name='quiz_question'),

    path('quiz/<int:quiz_id>/results/', views.quiz_results_view, name='quiz_results'),

    path('quiz/<int:quiz_id>/analysis/', views.quiz_analysis_view, name='quiz_analysis'),

    path('subscribe/', views.subscribe_view, name='subscribe'),

    path(
        'subscription/manage/',
        views.manage_subscription_view,
        name='manage_subscription'
    ),

    path(
        'purchase/<int:plan_id>/',
        views.initiate_purchase_view,
        name='initiate_purchase'
    ),

    path(
        'payment/verify/',
        views.verify_payment_view,
        name='verify_payment'
    ),
]