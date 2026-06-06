from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    # صفحه اصلی
    path('', views.home, name='home'),

    # لیست آزمون‌ها
    path('quizzes/', views.quiz_list_view, name='quiz_list'),

    # شروع آزمون
    path('quiz/<int:pk>/start/', views.start_quiz_view, name='start_quiz'),

    # نمایش سوال
    path('quiz/<int:pk>/question/', views.quiz_question_view, name='quiz_question'),

    # نتایج آزمون
    path('quiz/<int:quiz_id>/results/', views.quiz_results_view, name='quiz_results'),
    path('quiz/<int:quiz_id>/analysis/', views.quiz_analysis_view, name='quiz_analysis'),

    # اشتراک و پرداخت
    path('subscribe/', views.subscribe_view, name='subscribe'),
    path('subscription/manage/', views.manage_subscription_view, name='manage_subscription'),
    
    # مسیر شروع پرداخت (فقط یک بار تعریف شد)
    path('purchase/<int:plan_id>/', views.initiate_purchase_view, name='initiate_purchase'),
    
    # مسیر بازگشت از زرین‌پال (Callback)
    path('payment/verify/', views.verify_payment_view, name='verify_payment'),

    # سایر
    path('about/', views.about, name='about'),
    path('admin/', admin.site.urls),
]
