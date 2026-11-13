
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import RegisterForm
from .models import Plan, Subscription
from .utils import get_user_rank, persian_date

from quizzes.models import Quiz, QuizAttempt


def get_user_subscription(user):
    """
    دریافت اشتراک کاربر.
    اگر کاربر هنوز اشتراکی نداشته باشد، None برمی‌گرداند.
    """
    try:
        return user.subscription
    except Subscription.DoesNotExist:
        return None


def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                'ثبت‌نام با موفقیت انجام شد.'
            )

            return redirect('accounts:dashboard')
    else:
        form = RegisterForm()

    return render(
        request,
        'accounts/register.html',
        {'form': form}
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    next_url = (
        request.POST.get('next')
        or request.GET.get('next')
    )

    if request.method == 'POST':
        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # جلوگیری از هدایت کاربر به آدرس خارجی
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect('accounts:dashboard')
    else:
        form = AuthenticationForm()

    return render(
        request,
        'accounts/login.html',
        {
            'form': form,
            'next': next_url,
        }
    )


@login_required
def dashboard_view(request):
    welcome_message = None

    if not request.session.get('dashboard_welcome_shown'):
        welcome_message = """
دوست عزیز 👋

هر ماه چهار آزمون جدید داخل سایت قرار می‌گیرد.

این آزمون‌ها فقط تا پایان همان ماه فعال هستند؛
پس حتماً قبل از پایان ماه در آن‌ها شرکت کنید.

موفق باشید 🌱
"""

        request.session['dashboard_welcome_shown'] = True

    # دریافت و بررسی وضعیت اشتراک
    subscription = get_user_subscription(request.user)

    subscription_status = 'اشتراک ندارید'
    subscription_end = None

    if subscription:
        subscription.check_status()

        subscription_status = subscription.get_status_display()
        subscription_end = subscription.end_date

    # رتبه کاربر
    user_rank_data = get_user_rank(request.user)

    # آزمون‌های فعال
    quizzes = (
        Quiz.objects
        .filter(is_active=True)
        .prefetch_related('questions')
    )

    # تلاش‌های تکمیل‌شده کاربر
    # مرتب‌سازی نزولی بر اساس شناسه برای انتخاب آخرین رکورد ثبت‌شده
    attempts_queryset = (
        QuizAttempt.objects
        .filter(
            user=request.user,
            is_completed=True
        )
        .order_by('-pk')
        .prefetch_related(
            'answers__selected_choice'
        )
    )

    # برای هر آزمون فقط جدیدترین تلاش نگهداری می‌شود
    attempts = {}

    for attempt in attempts_queryset:
        if attempt.quiz_id not in attempts:
            attempts[attempt.quiz_id] = attempt

    quiz_results = []

    for quiz in quizzes:
        attempt = attempts.get(quiz.id)

        # استفاده از داده‌های prefetch شده
        total_questions = len(quiz.questions.all())

        correct_answers = 0

        if attempt:
            correct_answers = (
                attempt.answers
                .filter(
                    selected_choice__is_correct=True
                )
                .count()
            )

        percentage = 0

        if total_questions:
            percentage = round(
                (correct_answers / total_questions) * 100,
                2
            )

        quiz_results.append({
            'quiz': quiz,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'percentage': percentage,
            'status': (
                'گذرانده شده'
                if attempt
                else 'آزمون داده نشده'
            ),
            'attempted': bool(attempt),
            'is_active': quiz.is_active,
        })

    context = {
        'welcome_message': welcome_message,
        'subscription_status': subscription_status,
        'subscription_end': subscription_end,
        'subscription_end_persian': persian_date(
            subscription_end
        ),
        'quiz_results': quiz_results,
        'user_rank': user_rank_data,
    }

    return render(
        request,
        'accounts/dashboard.html',
        context
    )


@login_required
def subscribe_view(request):
    plans = Plan.objects.filter(is_active=True)

    subscription = get_user_subscription(request.user)

    # به‌روزرسانی وضعیت اشتراک پیش از بررسی آن
    if subscription:
        subscription.check_status()

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')

        if not plan_id:
            messages.error(
                request,
                'لطفاً یک پلن انتخاب کنید.'
            )

            return redirect('accounts:subscribe')

        plan = get_object_or_404(
            Plan,
            id=plan_id,
            is_active=True
        )

        if subscription and subscription.is_active:
            messages.warning(
                request,
                'شما در حال حاضر اشتراک فعال دارید.'
            )

            return redirect('accounts:dashboard')

        # فعال‌سازی اشتراک در این View انجام نمی‌شود.
        # تأیید پرداخت و فعال‌سازی فقط در فرایند پرداخت
        # اپ quizzes انجام می‌شود.
        messages.info(
            request,
            f'پلن {plan.name} انتخاب شد. '
            'برای پرداخت و فعال‌سازی اشتراک، '
            'از بخش خرید اشتراک اقدام کنید.'
        )

        return redirect('quizzes:subscribe')

    context = {
        'plans': plans,
        'current_subscription': subscription,
    }

    return render(
        request,
        'accounts/subscribe.html',
        context
    )


@login_required
def payment_success_view(request):
    """
    این View به‌تنهایی اجازه فعال‌سازی اشتراک ندارد.
    فعال‌سازی اشتراک باید پس از تأیید واقعی درگاه پرداخت
    در فرایند پرداخت اپ quizzes انجام شود.
    """

    subscription = get_user_subscription(request.user)

    if subscription:
        subscription.check_status()

        if subscription.is_active:
            messages.success(
                request,
                'اشتراک شما فعال است.'
            )
        else:
            messages.warning(
                request,
                'وضعیت پرداخت یا اشتراک شما هنوز تأیید نشده است.'
            )
    else:
        messages.warning(
            request,
            'برای حساب شما اشتراکی ثبت نشده است.'
        )

    return redirect('accounts:dashboard')


def leaderboard_view(request):
    leaderboard_data = (
        QuizAttempt.objects
        .filter(
            is_completed=True,
            quiz__is_premium=True,
            quiz__is_active=True
        )
        .values(
            'user_id',
            'user__username'
        )
        .annotate(
            total_score=Sum('score'),
            quizzes_taken=Count('id')
        )
        .order_by('-total_score', 'user_id')
    )

    leaderboard_list = []

    rank = 0
    last_score = None

    for index, entry in enumerate(
        leaderboard_data,
        start=1
    ):
        current_score = entry['total_score']

        # مدیریت امتیاز خالی
        if current_score is None:
            current_score = 0

        if index == 1 or current_score != last_score:
            rank = index

        quizzes_taken = entry['quizzes_taken'] or 0

        average_score = (
            current_score / quizzes_taken
            if quizzes_taken
            else 0
        )

        leaderboard_list.append({
            'user': {
                'username': entry['user__username']
            },
            'total_score': round(
                current_score,
                2
            ),
            'average_score': round(
                average_score,
                2
            ),
            'quizzes_taken': quizzes_taken,
            'rank': rank,
        })

        last_score = current_score

    return render(
        request,
        'accounts/leaderboard.html',
        {
            'leaderboard': leaderboard_list
        }
    )


@require_POST
@login_required
def logout_view(request):
    logout(request)

    messages.success(
        request,
        'با موفقیت از حساب کاربری خارج شدید.'
    )

    return redirect('accounts:login')
