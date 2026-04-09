from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
import random
from datetime import timedelta
from .models import Quiz, Question, Choice, QuizAttempt,UserAnswer
import datetime
from django.urls import reverse
from django.contrib import messages
from accounts.models import Plan
from django.http import HttpResponse
from accounts.models import Subscription

# ------------------------
# لیست آزمون‌ها
# ------------------------
@login_required(login_url='accounts:login')
def quiz_list_view(request):
    quizzes = Quiz.objects.all()
    user_attempts = QuizAttempt.objects.filter(user=request.user, is_completed=True)
    # یک دیکشنری بسازیم که id آزمون‌های تکمیل شده را نگه دارد
    completed_quiz_ids = user_attempts.values_list('quiz_id', flat=True)

    return render(request, 'quizzes/quiz_list.html', {
        'quizzes': quizzes,
        'completed_quiz_ids': completed_quiz_ids,
        'page_title': 'لیست آزمون‌ها'
    })
# ------------------------
# صفحه ورود رمز آزمون
# ------------------------
def home(request):
    context = {"error": None}

    if request.method == "POST":
        password = request.POST.get("password")

        try:
            quiz = Quiz.objects.get(password=password)
            request.session["allowed_quiz"] = quiz.id
            messages.success(request, f"دسترسی به '{quiz.title}' فعال شد.")
            return redirect('quiz_detail', pk=quiz.id)
        except Quiz.DoesNotExist:
            context["error"] = "رمز اشتباه است."
            messages.error(request, "رمز عبور اشتباه است.")

    return render(request, 'quizzes/home.html', context)


# ------------------------
# شروع آزمون
# ------------------------
@login_required
def start_quiz_view(request, pk):
    quiz = get_object_or_404(
        Quiz.objects.prefetch_related('questions__choices'),
        pk=pk
    )

    # ------------------------
    # چک پریمیوم و محدودیت یک بار شرکت
    # ------------------------
    if quiz.is_premium:
        subscription = getattr(request.user, 'subscription', None)
        if not subscription or not subscription.is_active:
            messages.warning(
                request,
                "این آزمون پرمیوم است. برای شرکت در آن باید اشتراک فعال داشته باشید."
            )
            return redirect('subscribe')

        # بررسی اینکه کاربر قبلاً این آزمون را کامل نکرده باشد
        previous_attempt = QuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz,
            is_completed=True
        ).exists()

        if previous_attempt:
            messages.info(
                request,
                "شما قبلاً این آزمون پرمیوم را گذرانده‌اید و نمی‌توانید دوباره شرکت کنید."
            )
            return redirect('quiz_list')

    # ------------------------
    # ساخت یا ادامه attempt جاری
    # ------------------------
    existing_attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=False
    ).first()

    if existing_attempt:
        request.session['attempt_id'] = existing_attempt.id
    else:
        new_attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz
        )
        request.session['attempt_id'] = new_attempt.id

    # ------------------------
    # گرفتن سوالات و تنظیم session
    # ------------------------
    questions = list(quiz.questions.all())
    if not questions:
        messages.warning(request, "این آزمون هنوز سوال ندارد.")
        return redirect('quiz_list')

    random.shuffle(questions)
    question_ids = [q.id for q in questions]

    request.session['quiz_progress'] = {
        'quiz_id': quiz.id,
        'question_ids': question_ids,
        'current_index': 0,
        'start_time': timezone.now().isoformat(),
    }

    messages.info(request, f"آزمون '{quiz.title}' شروع شد.")
    return redirect('quiz_question', pk=quiz.id)

# ------------------------
# نمایش سوال
# ------------------------
@login_required
def quiz_question_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    progress = request.session.get('quiz_progress')
    attempt_id = request.session.get('attempt_id')

    if not progress or progress.get('quiz_id') != quiz.id or not attempt_id:
        messages.warning(request, "لطفاً آزمون را از ابتدا شروع کنید.")
        return redirect('quiz_list')

    attempt = get_object_or_404(QuizAttempt, id=attempt_id)

    # چک تایمر
    start_time = timezone.datetime.fromisoformat(progress['start_time'])
    end_time = start_time + timedelta(minutes=quiz.duration_minutes)

    if timezone.now() > end_time:
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        # محاسبه نمره
        total_questions = quiz.questions.count()
        correct_answers = attempt.answers.filter(selected_choice__is_correct=True).count()
        attempt.score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        attempt.save()

        messages.info(request, "زمان آزمون به پایان رسید.")
        return redirect('quiz_results', quiz_id=quiz.id)

    question_ids = progress['question_ids']
    current_index = progress['current_index']

    if current_index >= len(question_ids):
        # آزمون کامل شد
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        total_questions = quiz.questions.count()
        correct_answers = attempt.answers.filter(selected_choice__is_correct=True).count()
        attempt.score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        attempt.save()

        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)
        return redirect('quiz_results', quiz_id=quiz.id)

    question = get_object_or_404(
        Question.objects.prefetch_related('choices'),
        id=question_ids[current_index]
    )

    if request.method == 'POST':
        choice_id = request.POST.get('choice')

        if not choice_id:
            messages.warning(request, "لطفاً یک گزینه انتخاب کنید.")
        else:
            selected_choice = get_object_or_404(Choice, id=choice_id)

            # ذخیره پاسخ در UserAnswer
            UserAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={'selected_choice': selected_choice}
            )

            progress['current_index'] += 1
            request.session.modified = True

            return redirect('quiz_question', pk=quiz.id)

    remaining_seconds = int((end_time - timezone.now()).total_seconds())

    return render(request, 'quizzes/question_detail.html', {
        'quiz': quiz,
        'question': question,
        'choices': question.choices.all(),
        'current_step': current_index + 1,
        'total_steps': len(question_ids),
        'remaining_seconds': remaining_seconds
    })

# ------------------------
# نتایج آزمون (ضد تقلب)
# ------------------------
@login_required
def quiz_results_view(request, quiz_id):
    # گرفتن آزمون
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    # پیدا کردن آخرین attempt کامل کاربر
    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=True
    ).last()

    if not attempt:
        messages.warning(request, "شما هنوز این آزمون را شروع نکرده‌اید.")
        return redirect('quiz_list')

    # جمع‌آوری پاسخ‌ها با select_related صحیح
    user_answers = []
    for ans in attempt.answers.all().select_related('selected_choice', 'question'):
        # پاسخ درست هر سوال
        correct_choice = ans.question.choices.filter(is_correct=True).first()

        user_answers.append({
            'question_text': ans.question.text,  # متن سوال
            'selected_choice_text': ans.selected_choice.choice_text if ans.selected_choice else 'گزینه‌ای انتخاب نشده',
            'correct_choice_text': correct_choice.choice_text if correct_choice else 'نامشخص',
            'is_correct': ans.selected_choice.is_correct if ans.selected_choice else False,
        })

    total_questions = quiz.questions.count()
    correct_answers = sum(1 for a in user_answers if a['is_correct'])
    percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

    return render(request, 'quizzes/results.html', {
        'quiz': quiz,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'percentage': round(percentage, 0),  # رند شده به عدد صحیح
        'user_answers': user_answers,
    })
# ------------------------
# اشتراک
# ------------------------

@login_required
def subscribe_view(request):
    # پاکسازی پیام‌های موجود در سشن قبل از نمایش صفحه اشتراک
    storage = messages.get_messages(request)
    storage.used = True 

    try:
        subscription = request.user.subscription
        is_currently_active = subscription.check_status()
    except Subscription.DoesNotExist:
        subscription = None
        is_currently_active = False

    available_plans = Plan.objects.filter(is_active=True).order_by('price')

    context = {
        'subscription': subscription,
        'is_currently_active': is_currently_active,
        'available_plans': available_plans,
    }
    return render(request, 'quizzes/subscribe.html', context)

@login_required
def manage_subscription_view(request):
    try:
        subscription = request.user.subscription
        subscription.check_status()

        if subscription.is_active:
            messages.success(
                request,
                f"اشتراک شما فعال است و تا تاریخ {subscription.end_date.strftime('%Y/%m/%d')} اعتبار دارد."
            )
        else:
            messages.warning(request, "اشتراک شما منقضی شده است.")
    except Subscription.DoesNotExist:
        messages.info(request, "شما اشتراک فعالی ندارید.")

    return redirect('subscribe')

def about(request):
    return render(request, 'quizzes/about.html')


@login_required
def initiate_purchase_view(request, plan_id):
    if request.method != 'POST':
        return redirect('subscribe')

    plan = get_object_or_404(Plan, pk=plan_id, is_active=True)

    subscription, created = Subscription.objects.update_or_create(
        user=request.user,
        defaults={
            'plan': plan,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=plan.duration_days),
            'is_active': True,
            'status': 'فعال',
        }
    )

    messages.success(request, f"پلن '{plan.name}' برای شما فعال شد تا {subscription.end_date.strftime('%Y/%m/%d')}.")
    return redirect('accounts:dashboard')