from datetime import timedelta
import random

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import Plan, Subscription

from .models import (
    AdBanner,
    Choice,
    HomeSlider,
    Question,
    Quiz,
    QuizAttempt,
    UserAnswer,
    VisitorStats,
)


# -----------------------------------
# صفحه اصلی
# -----------------------------------
def home(request):

    left_ad = AdBanner.objects.filter(
        position='left',
        is_active=True
    ).first()

    right_ad = AdBanner.objects.filter(
        position='right',
        is_active=True
    ).first()

    sliders = HomeSlider.objects.filter(
        is_active=True
    ).order_by('order')[:5]

    today = timezone.now().date()

    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    today_stats = VisitorStats.objects.filter(
        date=today
    ).first()

    week_unique = VisitorStats.objects.filter(
        date__gte=week_ago
    ).aggregate(
        total=Sum('unique_visitors_today')
    )['total'] or 0

    month_unique = VisitorStats.objects.filter(
        date__gte=month_ago
    ).aggregate(
        total=Sum('unique_visitors_today')
    )['total'] or 0

    total_unique = VisitorStats.objects.aggregate(
        total=Sum('unique_visitors_today')
    )['total'] or 0

    context = {
        'sliders': sliders,
        'today_unique': today_stats.unique_visitors_today if today_stats else 0,
        'week_unique': week_unique,
        'month_unique': month_unique,
        'total_unique': total_unique,
        'left_ad': left_ad,
        'right_ad': right_ad,
    }

    return render(
        request,
        'quizzes/home.html',
        context
    )


# -----------------------------------
# لیست آزمون‌ها
# -----------------------------------
@login_required(login_url='accounts:login')
def quiz_list_view(request):

    quizzes = Quiz.objects.filter(
        is_active=True
    ).prefetch_related('questions')

    # فقط آزمون‌های پریمیوم انجام‌شده
    completed_quiz_ids = QuizAttempt.objects.filter(
        user=request.user,
        is_completed=True,
        quiz__is_premium=True
    ).values_list(
        'quiz_id',
        flat=True
    )

    has_subscription = False

    try:

        subscription = request.user.subscription

        subscription.check_status()
        subscription.save()

        has_subscription = subscription.is_active

    except Subscription.DoesNotExist:

        has_subscription = False

    context = {
        'quizzes': quizzes,
        'completed_quiz_ids': completed_quiz_ids,
        'has_subscription': has_subscription,
        'page_title': 'لیست آزمون‌ها',
    }

    return redirect(
    reverse(
        'quizzes:quiz_question',
        kwargs={'pk': quiz.id}
    )
)

# -----------------------------------
# شروع آزمون
# -----------------------------------
@login_required
def start_quiz_view(request, pk):

    quiz = get_object_or_404(
        Quiz,
        pk=pk,
        is_active=True
    )

    # -----------------------------
    # فقط برای آزمون پریمیوم
    # -----------------------------
    if quiz.is_premium:

        try:
            subscription = request.user.subscription

            subscription.check_status()
            subscription.save()

            if not subscription.is_active:

                messages.warning(
                    request,
                    'برای شرکت در این آزمون باید اشتراک فعال داشته باشید.'
                )

                return redirect('quizzes:subscribe')

        except Subscription.DoesNotExist:

            messages.warning(
                request,
                'برای شرکت در این آزمون باید اشتراک تهیه کنید.'
            )

            return redirect('quizzes:subscribe')

        # فقط یک بار
        already_completed = QuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz,
            is_completed=True
        ).exists()

        if already_completed:

            messages.warning(
                request,
                'شما قبلاً در این آزمون شرکت کرده‌اید.'
            )

            return redirect('quizzes:quiz_list')

    # -----------------------------
    # حذف attempt ناقص قبلی
    # -----------------------------
    QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=False
    ).delete()

    # -----------------------------
    # ساخت attempt جدید
    # -----------------------------
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        is_completed=False
    )

    # -----------------------------
    # گرفتن سوالات
    # -----------------------------
    questions = list(
        quiz.questions.filter(
            is_active=True
        )
    )

    if not questions:

        messages.warning(
            request,
            'این آزمون سوال ندارد.'
        )

        return redirect('quizzes:quiz_list')

    random.shuffle(questions)

    # -----------------------------
    # پاک کردن session قبلی
    # -----------------------------
    request.session.pop('quiz_progress', None)
    request.session.pop('attempt_id', None)

    # -----------------------------
    # ذخیره session جدید
    # -----------------------------
    request.session['attempt_id'] = attempt.id

    request.session['quiz_progress'] = {
        'quiz_id': quiz.id,
        'question_ids': [q.id for q in questions],
        'current_index': 0,
        'start_time': timezone.now().isoformat(),
    }

    request.session.modified = True

    print("START QUIZ OK")
    print("QUIZ ID:", quiz.id)

    # -----------------------------
    # انتقال به سوالات
    # -----------------------------
    return redirect(
        'quizzes:quiz_question',
        pk=quiz.id
    )
# -----------------------------------
# سوالات آزمون
# -----------------------------------
@login_required
def quiz_question_view(request, pk):

    quiz = get_object_or_404(
        Quiz,
        pk=pk,
        is_active=True
    )

    progress = request.session.get('quiz_progress')
    attempt_id = request.session.get('attempt_id')

    if not progress or not attempt_id:

        messages.warning(
            request,
            'لطفاً آزمون را مجدد شروع کنید.'
        )

        return redirect('quizzes:quiz_list')

    if progress.get('quiz_id') != quiz.id:

        messages.warning(
            request,
            'خطا در اطلاعات آزمون.'
        )

        return redirect('quizzes:quiz_list')

    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        user=request.user,
        quiz=quiz
    )

    start_time = timezone.datetime.fromisoformat(
        progress['start_time']
    )

    end_time = start_time + timedelta(
        minutes=quiz.duration_minutes
    )

    if timezone.now() > end_time:

        total_questions = quiz.questions.count()

        correct_count = attempt.answers.filter(
            selected_choice__is_correct=True
        ).count()

        wrong_count = attempt.answers.filter(
            selected_choice__is_correct=False
        ).count()

        unit_score = 100 / total_questions if total_questions else 0

        positive_score = correct_count * unit_score

        negative_score = wrong_count * (unit_score / 3)

        final_score = max(
            0,
            positive_score - negative_score
        )

        attempt.score = round(final_score, 2)
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()

        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)

        messages.warning(
            request,
            'زمان آزمون به پایان رسید.'
        )

        return redirect(
            'quizzes:quiz_results',
            quiz_id=quiz.id
        )

    question_ids = progress['question_ids']
    current_index = progress['current_index']

    if current_index >= len(question_ids):

        total_questions = quiz.questions.count()

        correct_count = attempt.answers.filter(
            selected_choice__is_correct=True
        ).count()

        wrong_count = attempt.answers.filter(
            selected_choice__is_correct=False
        ).count()

        unit_score = 100 / total_questions if total_questions else 0

        positive_score = correct_count * unit_score

        negative_score = wrong_count * (unit_score / 3)

        final_score = max(
            0,
            positive_score - negative_score
        )

        attempt.score = round(final_score, 2)
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()

        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)

        return redirect(
            'quizzes:quiz_results',
            quiz_id=quiz.id
        )

    question = get_object_or_404(
        Question.objects.prefetch_related('choices'),
        id=question_ids[current_index],
        is_active=True
    )

    if request.method == 'POST':

        choice_id = request.POST.get('choice')

        if choice_id:

            try:

                selected_choice = Choice.objects.get(
                    id=choice_id,
                    question=question
                )

                UserAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        'selected_choice': selected_choice
                    }
                )

            except Choice.DoesNotExist:
                pass

        progress['current_index'] += 1

        request.session['quiz_progress'] = progress
        request.session.modified = True

        return redirect(
            'quizzes:quiz_question',
            pk=quiz.id
        )

    progress_percentage = int(
        ((current_index + 1) / len(question_ids)) * 100
    )

    remaining_seconds = int(
        (end_time - timezone.now()).total_seconds()
    )

    context = {
        'quiz': quiz,
        'question': question,
        'current_question_index': current_index + 1,
        'total_questions': len(question_ids),
        'progress_percentage': progress_percentage,
        'remaining_seconds': max(0, remaining_seconds),
        'duration_minutes': quiz.duration_minutes,
    }

    return render(
        request,
        'quizzes/question_detail.html',
        context
    )
# -----------------------------------
# نتایج آزمون
# -----------------------------------
@login_required
def quiz_results_view(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        pk=quiz_id
    )

    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=True
    ).order_by(
        '-completed_at'
    ).first()

    if not attempt:

        messages.warning(
            request,
            'نتیجه‌ای برای این آزمون یافت نشد.'
        )

        return redirect('quiz_list')

    total_questions = quiz.questions.count()

    correct_count = attempt.answers.filter(
        selected_choice__is_correct=True
    ).count()

    wrong_count = attempt.answers.filter(
        selected_choice__is_correct=False
    ).count()

    answered_questions = attempt.answers.count()

    unanswered_count = total_questions - answered_questions

    unit_score = 100 / total_questions if total_questions else 0

    positive_score = correct_count * unit_score

    negative_score = wrong_count * (unit_score / 3)

    final_score = max(
        0,
        positive_score - negative_score
    )

    attempt.score = round(final_score, 2)
    attempt.save()

    context = {
        'quiz': quiz,
        'attempt': attempt,
        'total_questions': total_questions,
        'correct_count': correct_count,
        'wrong_count': wrong_count,
        'unanswered_count': unanswered_count,
        'unit_score': round(unit_score, 2),
        'positive_score': round(positive_score, 2),
        'negative_score': round(negative_score, 2),
        'net_score': round(final_score, 2),
    }

    return render(
        request,
        'quizzes/results.html',
        context
    )


# -----------------------------------
# تحلیل آزمون
# -----------------------------------
@login_required
def quiz_analysis_view(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        pk=quiz_id
    )

    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=True
    ).order_by(
        '-completed_at'
    ).first()

    if not attempt:

        messages.warning(
            request,
            'تحلیل آزمون یافت نشد.'
        )

        return redirect('quiz_list')

    user_answers_data = []

    questions = quiz.questions.prefetch_related('choices')

    for question in questions:

        answer = attempt.answers.filter(
            question=question
        ).first()

        correct_choice = question.choices.filter(
            is_correct=True
        ).first()

        user_answers_data.append({
            'question': question,
            'selected_choice': answer.selected_choice if answer else None,
            'correct_choice': correct_choice,
            'is_correct': (
                answer.selected_choice.is_correct
                if answer and answer.selected_choice
                else False
            ),
        })

    context = {
        'quiz': quiz,
        'attempt': attempt,
        'user_answers': user_answers_data,
    }

    return render(
        request,
        'quizzes/analysis.html',
        context
    )


# -----------------------------------
# اشتراک
# -----------------------------------
@login_required
def subscribe_view(request):

    user_status = None

    try:

        subscription = request.user.subscription

        subscription.check_status()
        subscription.save()

        user_status = subscription

    except Subscription.DoesNotExist:
        pass

    available_plans = Plan.objects.filter(
        is_active=True
    ).order_by('price')

    context = {
        'user_status': user_status,
        'available_plans': available_plans,
    }

    return render(
        request,
        'quizzes/subscribe.html',
        context
    )


# -----------------------------------
# مدیریت اشتراک
# -----------------------------------
@login_required
def manage_subscription_view(request):

    try:

        subscription = request.user.subscription

        subscription.check_status()
        subscription.save()

        if subscription.is_active:

            messages.success(
                request,
                f'اشتراک شما تا تاریخ {subscription.end_date.strftime("%Y/%m/%d")} فعال است.'
            )

        else:

            messages.warning(
                request,
                'اشتراک شما منقضی شده است.'
            )

    except Subscription.DoesNotExist:

        messages.warning(
            request,
            'شما اشتراک فعالی ندارید.'
        )

    return redirect('subscribe')


# -----------------------------------
# درباره ما
# -----------------------------------
def about(request):

    return render(
        request,
        'quizzes/about.html'
    )

from datetime import timedelta
import random

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import Plan, Subscription

from .models import (
    AdBanner,
    Choice,
    HomeSlider,
    Question,
    Quiz,
    QuizAttempt,
    UserAnswer,
    VisitorStats,
)


# -----------------------------------
# صفحه اصلی
# -----------------------------------
def home(request):

    left_ad = AdBanner.objects.filter(
        position='left',
        is_active=True
    ).first()

    right_ad = AdBanner.objects.filter(
        position='right',
        is_active=True
    ).first()

    sliders = HomeSlider.objects.filter(
        is_active=True
    ).order_by('order')[:5]

    today = timezone.now().date()

    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    today_stats = VisitorStats.objects.filter(
        date=today
    ).first()

    week_unique = VisitorStats.objects.filter(
        date__gte=week_ago
    ).aggregate(
        total=Sum('unique_visitors_today')
    )['total'] or 0

    month_unique = VisitorStats.objects.filter(
        date__gte=month_ago
    ).aggregate(
        total=Sum('unique_visitors_today')
    )['total'] or 0

    total_unique = VisitorStats.objects.aggregate(
        total=Sum('unique_visitors_today')
    )['total'] or 0

    context = {
        'sliders': sliders,
        'today_unique': today_stats.unique_visitors_today if today_stats else 0,
        'week_unique': week_unique,
        'month_unique': month_unique,
        'total_unique': total_unique,
        'left_ad': left_ad,
        'right_ad': right_ad,
    }

    return render(
        request,
        'quizzes/home.html',
        context
    )


# -----------------------------------
# لیست آزمون‌ها
# -----------------------------------
@login_required(login_url='accounts:login')
def quiz_list_view(request):

    quizzes = Quiz.objects.filter(
        is_active=True
    ).prefetch_related('questions')

    completed_quiz_ids = QuizAttempt.objects.filter(
        user=request.user,
        is_completed=True
    ).values_list(
        'quiz_id',
        flat=True
    )

    has_subscription = False

    try:

        subscription = request.user.subscription

        if hasattr(subscription, 'check_status'):
            subscription.check_status()

        has_subscription = subscription.is_active

    except Subscription.DoesNotExist:
        has_subscription = False

    context = {
        'quizzes': quizzes,
        'completed_quiz_ids': completed_quiz_ids,
        'has_subscription': has_subscription,
        'page_title': 'لیست آزمون‌ها',
    }

    return render(
        request,
        'quizzes/quiz_list.html',
        context
    )


# -----------------------------------
# شروع آزمون
# -----------------------------------
@login_required
def start_quiz_view(request, pk):

    quiz = get_object_or_404(
        Quiz.objects.prefetch_related('questions__choices'),
        pk=pk,
        is_active=True
    )

    if quiz.is_premium:

        try:

            subscription = request.user.subscription

            if hasattr(subscription, 'check_status'):
                subscription.check_status()

            if not subscription.is_active:

                messages.warning(
                    request,
                    'برای شرکت در این آزمون باید اشتراک فعال داشته باشید.'
                )

                return redirect('quizzes:subscribe')

        except Subscription.DoesNotExist:

            messages.warning(
                request,
                'برای شرکت در این آزمون باید اشتراک تهیه کنید.'
            )

            return redirect('quizzes:subscribe')

    already_completed = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=True
    ).exists()

    if already_completed:

        messages.warning(
            request,
            'شما قبلاً در این آزمون شرکت کرده‌اید.'
        )

        return redirect('quizzes:quiz_list')

    existing_attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=False
    ).first()

    if existing_attempt:

        attempt = existing_attempt

    else:

        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz
        )

    questions = list(
        quiz.questions.filter(
            is_active=True
        )
    )

    if not questions:

        messages.warning(
            request,
            'این آزمون هنوز سوالی ندارد.'
        )

        return redirect('quizzes:quiz_list')

    random.shuffle(questions)

    request.session['attempt_id'] = attempt.id

    request.session['quiz_progress'] = {
        'quiz_id': quiz.id,
        'question_ids': [q.id for q in questions],
        'current_index': 0,
        'start_time': timezone.now().isoformat(),
    }

    messages.success(
        request,
        f'آزمون {quiz.title} شروع شد.'
    )

    return redirect(
        'quizzes:quiz_question',
        pk=quiz.id
    )


# -----------------------------------
# سوالات آزمون
# -----------------------------------
@login_required
def quiz_question_view(request, pk):

    quiz = get_object_or_404(
        Quiz,
        pk=pk,
        is_active=True
    )

    progress = request.session.get('quiz_progress')
    attempt_id = request.session.get('attempt_id')

    if not progress or not attempt_id:

        messages.warning(
            request,
            'لطفاً آزمون را مجدد شروع کنید.'
        )

        return redirect('quizzes:quiz_list')

    if progress.get('quiz_id') != quiz.id:

        messages.warning(
            request,
            'خطا در اطلاعات آزمون.'
        )

        return redirect('quizzes:quiz_list')

    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        user=request.user,
        quiz=quiz
    )

    start_time = timezone.datetime.fromisoformat(
        progress['start_time']
    )

    end_time = start_time + timedelta(
        minutes=quiz.duration_minutes
    )

    if timezone.now() > end_time:

        total_questions = quiz.questions.count()

        correct_count = attempt.answers.filter(
            selected_choice__is_correct=True
        ).count()

        wrong_count = attempt.answers.filter(
            selected_choice__is_correct=False
        ).count()

        unit_score = 100 / total_questions if total_questions else 0

        positive_score = correct_count * unit_score

        negative_score = wrong_count * (unit_score / 3)

        final_score = max(
            0,
            positive_score - negative_score
        )

        attempt.score = round(final_score, 2)
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()

        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)

        messages.warning(
            request,
            'زمان آزمون به پایان رسید.'
        )

        return redirect(
            'quizzes:quiz_results',
            quiz_id=quiz.id
        )

    question_ids = progress['question_ids']
    current_index = progress['current_index']

    if current_index >= len(question_ids):

        total_questions = quiz.questions.count()

        correct_count = attempt.answers.filter(
            selected_choice__is_correct=True
        ).count()

        wrong_count = attempt.answers.filter(
            selected_choice__is_correct=False
        ).count()

        unit_score = 100 / total_questions if total_questions else 0

        positive_score = correct_count * unit_score

        negative_score = wrong_count * (unit_score / 3)

        final_score = max(
            0,
            positive_score - negative_score
        )

        attempt.score = round(final_score, 2)
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()

        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)

        return redirect(
            'quizzes:quiz_results',
            quiz_id=quiz.id
        )

    question = get_object_or_404(
        Question.objects.prefetch_related('choices'),
        id=question_ids[current_index],
        is_active=True
    )

    if request.method == 'POST':

        choice_id = request.POST.get('choice')

        if choice_id:

            try:

                selected_choice = Choice.objects.get(
                    id=choice_id,
                    question=question
                )

                UserAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        'selected_choice': selected_choice
                    }
                )

            except Choice.DoesNotExist:
                pass

        progress['current_index'] += 1

        request.session['quiz_progress'] = progress
        request.session.modified = True

        return redirect(
            'quizzes:quiz_question',
            pk=quiz.id
        )

    progress_percentage = int(
        ((current_index + 1) / len(question_ids)) * 100
    )

    remaining_seconds = int(
        (end_time - timezone.now()).total_seconds()
    )

    context = {
        'quiz': quiz,
        'question': question,
        'current_question_index': current_index + 1,
        'total_questions': len(question_ids),
        'progress_percentage': progress_percentage,
        'remaining_seconds': max(0, remaining_seconds),
        'duration_minutes': quiz.duration_minutes,
    }

    return render(
        request,
        'quizzes/question_detail.html',
        context
    )


# -----------------------------------
# نتایج آزمون
# -----------------------------------
@login_required
def quiz_results_view(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        pk=quiz_id
    )

    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=True
    ).order_by(
        '-completed_at'
    ).first()

    if not attempt:

        messages.warning(
            request,
            'نتیجه‌ای برای این آزمون یافت نشد.'
        )

        return redirect('quizzes:quiz_list')

    total_questions = quiz.questions.count()

    correct_count = attempt.answers.filter(
        selected_choice__is_correct=True
    ).count()

    wrong_count = attempt.answers.filter(
        selected_choice__is_correct=False
    ).count()

    answered_questions = attempt.answers.count()

    unanswered_count = total_questions - answered_questions

    unit_score = 100 / total_questions if total_questions else 0

    positive_score = correct_count * unit_score

    negative_score = wrong_count * (unit_score / 3)

    final_score = max(
        0,
        positive_score - negative_score
    )

    attempt.score = round(final_score, 2)
    attempt.save()

    context = {
        'quiz': quiz,
        'attempt': attempt,
        'total_questions': total_questions,
        'correct_count': correct_count,
        'wrong_count': wrong_count,
        'unanswered_count': unanswered_count,
        'unit_score': round(unit_score, 2),
        'positive_score': round(positive_score, 2),
        'negative_score': round(negative_score, 2),
        'net_score': round(final_score, 2),
    }

    return render(
        request,
        'quizzes/results.html',
        context
    )


# -----------------------------------
# تحلیل آزمون
# -----------------------------------
@login_required
def quiz_analysis_view(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        pk=quiz_id
    )

    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=True
    ).order_by(
        '-completed_at'
    ).first()

    if not attempt:

        messages.warning(
            request,
            'تحلیل آزمون یافت نشد.'
        )

        return redirect('quizzes:quiz_list')

    user_answers_data = []

    questions = quiz.questions.prefetch_related('choices')

    for question in questions:

        answer = attempt.answers.filter(
            question=question
        ).first()

        correct_choice = question.choices.filter(
            is_correct=True
        ).first()

        user_answers_data.append({
            'question': question,
            'selected_choice': answer.selected_choice if answer else None,
            'correct_choice': correct_choice,
            'is_correct': (
                answer.selected_choice.is_correct
                if answer and answer.selected_choice
                else False
            ),
        })

    context = {
        'quiz': quiz,
        'attempt': attempt,
        'user_answers': user_answers_data,
    }

    return render(
        request,
        'quizzes/analysis.html',
        context
    )


# -----------------------------------
# اشتراک
# -----------------------------------
@login_required
def subscribe_view(request):

    user_status = None

    try:

        subscription = request.user.subscription

        if hasattr(subscription, 'check_status'):
            subscription.check_status()

        user_status = subscription

    except Subscription.DoesNotExist:
        pass

    available_plans = Plan.objects.filter(
        is_active=True
    ).order_by('price')

    context = {
        'user_status': user_status,
        'available_plans': available_plans,
    }

    return render(
        request,
        'quizzes/subscribe.html',
        context
    )


# -----------------------------------
# مدیریت اشتراک
# -----------------------------------
@login_required
def manage_subscription_view(request):

    try:

        subscription = request.user.subscription

        if hasattr(subscription, 'check_status'):
            subscription.check_status()

        if subscription.is_active:

            messages.success(
                request,
                f'اشتراک شما تا تاریخ {subscription.end_date.strftime("%Y/%m/%d")} فعال است.'
            )

        else:

            messages.warning(
                request,
                'اشتراک شما منقضی شده است.'
            )

    except Subscription.DoesNotExist:

        messages.warning(
            request,
            'شما اشتراک فعالی ندارید.'
        )

    return redirect('quizzes:subscribe')


# -----------------------------------
# درباره ما
# -----------------------------------
def about(request):

    return render(
        request,
        'quizzes/about.html'
    )


# -----------------------------------
# شروع پرداخت
# -----------------------------------
@login_required
def initiate_purchase_view(request, plan_id):

    if request.method != 'POST':
        return redirect('quizzes:subscribe')

    plan = get_object_or_404(
        Plan,
        pk=plan_id,
        is_active=True
    )

    merchant_id = settings.ZARINPAL_MERCHANT

    amount_rial = int(plan.price) * 10

    callback_url = request.build_absolute_uri(
        reverse('quizzes:verify_payment')
    )

    data = {
        "merchant_id": merchant_id,
        "amount": amount_rial,
        "currency": "IRR",
        "description": f"خرید اشتراک {plan.name}",
        "callback_url": callback_url,
    }

    request_url = 'https://payment.zarinpal.com/pg/v4/payment/request.json'

    start_pay_url = 'https://payment.zarinpal.com/pg/StartPay/'

    try:

        response = requests.post(
            request_url,
            json=data,
            timeout=10
        )

        response_data = response.json()

        code = response_data.get(
            'data',
            {}
        ).get('code')

        authority = response_data.get(
            'data',
            {}
        ).get('authority')

        if code == 100 and authority:

            request.session['plan_id'] = plan.id

            return redirect(
                f'{start_pay_url}{authority}'
            )

        messages.error(
            request,
            'خطا در اتصال به درگاه پرداخت.'
        )

    except Exception as e:

        messages.error(
            request,
            f'خطا: {str(e)}'
        )

    return redirect('quizzes:subscribe')

# -----------------------------------
# تایید پرداخت
# -----------------------------------
@login_required
def verify_payment_view(request):

    authority = request.GET.get('Authority')

    status = request.GET.get('Status')

    if not authority or status != 'OK':

        messages.error(
            request,
            'پرداخت لغو شد.'
        )

        return redirect('quizzes:subscribe')

    plan_id = request.session.get('plan_id')

    if not plan_id:

        messages.error(
            request,
            'پلن یافت نشد.'
        )

        return redirect('quizzes:subscribe')

    plan = get_object_or_404(
        Plan,
        id=plan_id
    )

    merchant_id = settings.ZARINPAL_MERCHANT

    amount_rial = int(plan.price) * 10

    data = {
        "merchant_id": merchant_id,
        "amount": amount_rial,
        "authority": authority,
    }

    verify_url = 'https://payment.zarinpal.com/pg/v4/payment/verify.json'

    try:

        response = requests.post(
            verify_url,
            json=data,
            timeout=10
        )

        result = response.json()

        verify_data = result.get('data', {})

        if verify_data.get('code') == 100:

            ref_id = verify_data.get('ref_id')

            subscription, created = Subscription.objects.get_or_create(
                user=request.user
            )

            now = timezone.now()

            if (
                subscription.end_date and
                subscription.end_date > now
            ):
                start_date = subscription.end_date
            else:
                start_date = now

            end_date = start_date + timedelta(
                days=plan.duration_days
            )

            subscription.plan = plan
            subscription.start_date = start_date
            subscription.end_date = end_date
            subscription.status = 'فعال'
            subscription.authority = authority
            subscription.ref_id = str(ref_id)

            subscription.save()

            messages.success(
                request,
                'اشتراک شما با موفقیت فعال شد.'
            )

            return redirect('quizzes:subscribe')

        messages.error(
            request,
            'پرداخت تایید نشد.'
        )

    except Exception as e:

        messages.error(
            request,
            f'خطا: {str(e)}'
        )

    return redirect('quizzes:subscribe')