from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegisterForm
from .models import Plan, Subscription, SubscriptionStatus
from .utils import get_user_rank, persian_date

from quizzes.models import Quiz, QuizAttempt


def register_view(request):

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

    if request.method == 'POST':

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            next_url = request.GET.get('next')

            return redirect(
                next_url or 'accounts:dashboard'
            )

    else:
        form = AuthenticationForm()

    return render(
        request,
        'accounts/login.html',
        {'form': form}
    )


@login_required
def dashboard_view(request):

    welcome_message = None

    if 'dashboard_welcome_shown' not in request.session:

        welcome_message = """
دوست عزیز 👋

هر ماه چهار آزمون جدید داخل سایت قرار می‌گیرد.

این آزمون‌ها فقط تا پایان همان ماه فعال هستند؛
پس حتماً قبل از پایان ماه در آن‌ها شرکت کنید.

موفق باشید 🌱
"""

        request.session[
            'dashboard_welcome_shown'
        ] = True

    subscription = getattr(
        request.user,
        'subscription',
        None
    )

    subscription_status = 'اشتراک ندارید'

    subscription_end = None

    if subscription:

        subscription.update_status()

        subscription_status = (
            subscription.get_status_display()
        )

        subscription_end = subscription.end_date

    user_rank_data = get_user_rank(
        request.user
    )

    quizzes = (
        Quiz.objects
        .filter(is_active=True)
        .prefetch_related('questions')
    )

    attempts_queryset = (
        QuizAttempt.objects.filter(
            user=request.user,
            is_completed=True
        )
        .prefetch_related(
            'answers__selected_choice'
        )
    )

    attempts = {
        attempt.quiz_id: attempt
        for attempt in attempts_queryset
    }

    quiz_results = []

    for quiz in quizzes:

        attempt = attempts.get(quiz.id)

        total_questions = (
            quiz.questions.count()
        )

        correct_answers = 0

        if attempt:

            correct_answers = (
                attempt.answers.filter(
                    selected_choice__is_correct=True
                ).count()
            )

        percentage = 0

        if total_questions > 0:

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

        'subscription_end_persian': (
            persian_date(subscription_end)
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

    plans = Plan.objects.filter(
        is_active=True
    )

    subscription = getattr(
        request.user,
        'subscription',
        None
    )

    if request.method == 'POST':

        plan_id = request.POST.get('plan_id')

        if not plan_id:

            messages.error(
                request,
                'لطفاً یک پلن انتخاب کنید.'
            )

            return redirect(
                'accounts:subscribe'
            )

        plan = get_object_or_404(
            Plan,
            id=plan_id,
            is_active=True
        )

        if subscription and subscription.is_active:

            messages.warning(
                request,
                'شما اشتراک فعال دارید.'
            )

            return redirect(
                'accounts:dashboard'
            )

        subscription, created = (
            Subscription.objects.get_or_create(
                user=request.user
            )
        )

        subscription.plan = plan

        subscription.start_date = (
            timezone.now()
        )

        subscription.end_date = (
            timezone.now()
            + timedelta(
                days=plan.duration_days
            )
        )

        subscription.status = (
            SubscriptionStatus.ACTIVE
        )

        subscription.save()

        messages.success(
            request,
            f'اشتراک {plan.name} فعال شد.'
        )

        return redirect(
            'accounts:dashboard'
        )

    context = {
        'plans': plans,
        'current_subscription': subscription
    }

    return render(
        request,
        'accounts/subscribe.html',
        context
    )


@login_required
def payment_success_view(request):

    subscription = getattr(
        request.user,
        'subscription',
        None
    )

    if not subscription:

        messages.error(
            request,
            'اشتراک یافت نشد.'
        )

        return redirect(
            'accounts:dashboard'
        )

    subscription.status = (
        SubscriptionStatus.ACTIVE
    )

    subscription.start_date = (
        timezone.now()
    )

    if (
        not subscription.end_date
        and subscription.plan
    ):

        subscription.end_date = (
            timezone.now()
            + timedelta(
                days=subscription.plan.duration_days
            )
        )

    subscription.save()

    messages.success(
        request,
        'پرداخت با موفقیت انجام شد.'
    )

    return redirect(
        'accounts:dashboard'
    )


@login_required
def leaderboard_view(request):

    leaderboard_data = (

        QuizAttempt.objects.filter(
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

        .order_by('-total_score')
    )

    leaderboard_list = []

    rank = 0

    last_score = None

    for index, entry in enumerate(
        leaderboard_data,
        start=1
    ):

        current_score = (
            entry['total_score']
        )

        if current_score != last_score:
            rank = index

        quizzes_taken = (
            entry['quizzes_taken'] or 1
        )

        average_score = (
            current_score / quizzes_taken
        )

        leaderboard_list.append({

            'user': {
                'username': (
                    entry['user__username']
                )
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

            'rank': rank
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

    return redirect('accounts:login')