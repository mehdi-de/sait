from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm  # UserCreationForm اضافه شد
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt  # اضافه: برای @csrf_exempt
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Sum, Avg, F, Count
from accounts.models import Plan, Subscription 
from quizzes.models import Quiz, QuizAttempt
from accounts.utils import get_user_rank
from accounts.utils import persian_date, persian_full_date 



# Register view: مدیریت ثبت‌نام کاربر
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            new_message = 'ثبت‌نام با موفقیت انجام شد!'
            existing_messages = [m.message for m in messages.get_messages(request)]
            if new_message not in existing_messages:
                messages.success(request, new_message)

            return redirect('accounts:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

# Login view: مدیریت ورود کاربر
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('accounts:dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

# Dashboard view: نمایش داشبورد کاربر با
@login_required
def dashboard_view(request):
    # 🆕 پیغام خوش‌آمدگویی - فقط بار اول بعد از لاگین
    welcome_message = None
    if 'dashboard_welcome_shown' not in request.session:
        welcome_message = """
        دوست عزیز! 👋

        هر ماه، چهار تا آزمون رو توی سایت براتون بارگذاری می‌کنیم. 
        یادتون باشه که این آزمون‌ها فقط تا آخر ماه فعال هستن و بعدش دیگه از دسترس خارج می‌شن.

        پس حتماً حواستون به تقویمتون باشه که این فرصت‌های عالی رو از دست ندین! 😉

        یه رقابت دوستانه با بقیه کاربران در انتظارتونه. 
        خودتون رو نشون بدید و حسابی لذت ببرید!

        منتظر حضورتون هستیم! ✨
        """
        request.session['dashboard_welcome_shown'] = True  # فلگ برای بار بعدی

    # دریافت اطلاعات اشتراک کاربر
    subscription = getattr(request.user, 'subscription', None)
    subscription_status = "اشتراک ندارید"  
    subscription_end = None    

    if subscription:
        subscription.check_status()
        subscription_status = subscription.status if hasattr(subscription, 'status') else "-"
        if hasattr(subscription, 'end_date') and subscription.end_date:
            subscription_end = subscription.end_date
        else:
            subscription_end = None

    # رتبه کاربر
    user_rank_data = get_user_rank(request.user)

    # نتایج آزمون‌ها
    quizzes = Quiz.objects.prefetch_related('questions').select_related()
    attempts = {a.quiz_id: a for a in QuizAttempt.objects.filter(user=request.user, is_completed=True)}

    quiz_results = []
    for quiz in quizzes:
        attempt = attempts.get(quiz.id)
        total = quiz.questions.count()
        correct = attempt.answers.filter(selected_choice__is_correct=True).count() if attempt else 0
        percent = round((correct / total * 100), 2) if total else 0

        quiz_results.append({
            'quiz': quiz,
            'correct_answers': correct,
            'total_questions': total,
            'percentage': percent,
            'status': f"{'گذرانده شده' if attempt else 'آزمون داده نشده'}",
            'attempted': bool(attempt),
            'is_active': quiz.is_active
        })
    
    subscription_end_persian = persian_date(subscription_end)

    return render(request, 'accounts/dashboard.html', {
        'welcome_message': welcome_message,
        'subscription_status': subscription_status,
        'subscription_end': subscription_end,
        'quiz_results': quiz_results,
        'user_rank': user_rank_data,
        'subscription_end_persian': subscription_end_persian,
    })
    
# Logout view: خروج کاربر
@login_required
def logout_view(request):
    logout(request)
    return redirect('home')  # یا login

# Subscribe view: مدیریت صفحه subscribe و ایجاد اشتراک (تست محلی)
@login_required
def subscribe_view(request):
    plans = Plan.objects.filter(is_active=True)
    subscription = getattr(request.user, 'subscription', None)
    
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        if not plan_id:
            messages.error(request, 'لطفاً یک پلن انتخاب کنید.')
            return redirect('accounts:subscribe')
        
        plan = get_object_or_404(Plan, id=plan_id, is_active=True)
        
        if subscription and subscription.is_active:
            messages.warning(request, 'شما قبلاً اشتراک فعالی دارید! برای تغییر پلن، با ادمین تماس بگیرید.')
            return redirect('accounts:dashboard')
        
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'is_active': False,
                'start_date': timezone.now(),
                'status': 'ندارد'
            }
        )
        if not created:
            subscription.plan = plan
            subscription.start_date = timezone.now()
        
        subscription.end_date = timezone.now() + timedelta(days=plan.duration_days)
        subscription.save()
        
        # برای تست محلی
        subscription.is_active = True
        subscription.status = 'فعال'
        subscription.save()
        messages.success(request, f'اشتراک {plan.name} با موفقیت فعال شد! (تست محلی)')
        return redirect('accounts:dashboard')
    
    context = {
        'plans': plans,
        'current_subscription': subscription
    }
    return render(request, 'accounts/subscribe.html', context)

# Payment success view: پردازش موفقیت پرداخت (تست محلی)
@csrf_exempt
@login_required
def payment_success_view(request):
    subscription = getattr(request.user, 'subscription', None)
    if not subscription:
        messages.error(request, 'اشتراک یافت نشد. لطفاً دوباره تلاش کنید.')
        return redirect('accounts:dashboard')
    
    # برای تست محلی
    subscription.is_active = True
    subscription.status = 'فعال'
    subscription.start_date = timezone.now()
    if not subscription.end_date and subscription.plan:
        subscription.end_date = timezone.now() + timedelta(days=subscription.plan.duration_days)
    subscription.save()
    messages.success(request, f'پرداخت موفق! اشتراک {subscription.plan.name if subscription.plan else "نامشخص"} فعال شد.')
    return redirect('accounts:dashboard')


@login_required
def leaderboard_view(request):
    """
    جدول رتبه‌بندی کاربران بر اساس مجموع نمرات آزمون‌های **پریمیوم** تکمیل شده.
    """
    
    # 1. کوئری برای محاسبه مجموع امتیازات فقط برای QuizAttempt های مربوط به Quiz های پریمیوم
    leaderboard_data = QuizAttempt.objects.filter(
        is_completed=True,
        quiz__is_premium=True,  # <-- این شرط فقط آزمون های پرمیوم را فیلتر می کند
        quiz__is_active=True 
    ).select_related('user').values(
        'user_id', 
        'user__username'
    ).annotate(
        total_score=Sum('score'),  # مجموع امتیازات (از 0 تا 100)
        quizzes_taken=Count('id')  # تعداد آزمون های پریمیوم شرکت شده
    ).order_by('-total_score')

    # 2. آماده سازی لیست نهایی با محاسبه میانگین و رتبه
    leaderboard_list = []
    rank = 0
    last_score = None

    for entry in leaderboard_data:
        # محاسبه میانگین نمره
        average_score = entry['total_score'] / entry['quizzes_taken'] if entry['quizzes_taken'] else 0
        
        # منطق تعیین رتبه (برای امتیازات یکسان، رتبه یکسان)
        current_score = entry['total_score']
        if current_score != last_score:
            rank += 1
        
        leaderboard_list.append({
            'user': {'username': entry['user__username']}, # ساختار مشابه خروجی قبلی
            'total_score': round(entry['total_score'], 2),
            'average_score': round(average_score, 2),
            'quizzes_taken': entry['quizzes_taken'],
            'rank': rank
        })
        last_score = current_score
    
    return render(request, 'accounts/leaderboard.html', {'leaderboard': leaderboard_list})

def user_logout(request):
    logout(request)
    return redirect('/')


