from django.urls import path
from . import views
from .views import start_quiz_view
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

urlpatterns = [

    # صفحه اصلی (ورود رمز آزمون)
    path('', views.home, name='home'),

    # لیست آزمون‌ها
    path('quizzes/', views.quiz_list_view, name='quiz_list'),

    # شروع آزمون
    path('quiz/<int:pk>/start/', views.start_quiz_view, name='start_quiz'),

    # نمایش سوال
    path('quiz/<int:pk>/question/', views.quiz_question_view, name='quiz_question'),

    # نتایج آزمون
    path('quiz/<int:quiz_id>/results/', views.quiz_results_view, name='quiz_results'),

    # اشتراک
    path('subscribe/', views.subscribe_view, name='subscribe'),
    path('subscription/manage/', views.manage_subscription_view, name='manage_subscription'),

    path('about/', views.about, name='about'),

    path('purchase/<int:plan_id>/', views.initiate_purchase_view, name='initiate_purchase'),

    path('admin/', admin.site.urls),


        # مسیر شروع پرداخت (همان initiate_purchase که دارید)
    path('purchase/<int:plan_id>/', views.initiate_purchase_view, name='initiate_purchase'),
    
    # مسیر بازگشت از زرین‌پال (Callback)
    path('payment/verify/', views.verify_payment_view, name='verify_payment'),
]
