from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
import random
from datetime import timedelta
from .models import (
    Quiz, Question, Choice, QuizAttempt, UserAnswer, HomeSlider, VisitorStats,AdBanner
)
from django.db.models import Sum, Count
from .models import IPVisit
import datetime
from django.urls import reverse
from django.contrib import messages
from accounts.models import Plan
from accounts.models import Subscription
import requests
from django.conf import settings
from django.db.models.functions import TruncDay
from django.views.decorators.cache import cache_page

# ------------------------
# لیست آزمون‌ها
# ------------------------
@login_required(login_url='accounts:login')
def quiz_list_view(request):
    quizzes = Quiz.objects.filter(is_active=True)
    
    user_attempts = QuizAttempt.objects.filter(user=request.user, is_completed=True)
    completed_quiz_ids = user_attempts.values_list('quiz_id', flat=True)

    # ✅ چک اشتراک کاربر
    has_subscription = False
    try:
        subscription = request.user.subscription
        subscription.check_status()
        has_subscription = subscription.is_active
    except Subscription.DoesNotExist:
        has_subscription = False

    return render(request, 'quizzes/quiz_list.html', {
        'quizzes': quizzes,
        'completed_quiz_ids': completed_quiz_ids,
        'has_subscription': has_subscription,  # ✅ ارسال به template
        'page_title': 'لیست آزمون‌ها'
    })
# ------------------------
# صفحه ورود رمز آزمون
# ------------------------
# @cache_page(60 * 5)
def home(request):

    left_ad = AdBanner.objects.filter(position='left', is_active=True).first()
    right_ad = AdBanner.objects.filter(position='right', is_active=True).first()

    sliders = HomeSlider.objects.filter(is_active=True).order_by('order')[:5]
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # فقط unique visitors
    today_stats = VisitorStats.objects.filter(date=today).first()
    week_unique = VisitorStats.objects.filter(date__gte=week_ago).aggregate(total=Sum('unique_visitors_today'))['total'] or 0
    month_unique = VisitorStats.objects.filter(date__gte=month_ago).aggregate(total=Sum('unique_visitors_today'))['total'] or 0
    total_unique = VisitorStats.objects.aggregate(total=Sum('unique_visitors_today'))['total'] or 0
    
    context = {
        "sliders": sliders,
        "today_unique": today_stats.unique_visitors_today if today_stats else 0,
        "week_unique": week_unique,
        "month_unique": month_unique,
        "total_unique": total_unique,
        "left_ad": left_ad,
        "right_ad": right_ad,
    }
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

    # ✅ تایمر بر اساس quiz.duration_minutes
    start_time = timezone.datetime.fromisoformat(progress['start_time'])
    end_time = start_time + timedelta(minutes=quiz.duration_minutes)  # ✅ هر آزمون جدا

    if timezone.now() > end_time:
        # محاسبه کنکوری (قدیمی)
        total_questions = quiz.questions.count()
        correct_count = attempt.answers.filter(selected_choice__is_correct=True).count()
        wrong_count = attempt.answers.exclude(selected_choice__is_correct__isnull=True).count()
        unit_score = 100 / total_questions if total_questions > 0 else 0
        positive_score = correct_count * unit_score
        negative_score = (unit_score / 3) * wrong_count
        net_score = max(0, positive_score - negative_score)
        
        attempt.score = net_score
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()
        
        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)
        return redirect('quiz_results', quiz_id=quiz.id)

    question_ids = progress['question_ids']
    current_index = progress['current_index']

    if current_index >= len(question_ids):
        # ✅ محاسبه جدید کنکوری
        total_questions = quiz.questions.count()
        unit_score = 100 / total_questions if total_questions > 0 else 0
        
        user_answers = attempt.answers.select_related('selected_choice')
        correct_count = sum(1 for a in user_answers if a.selected_choice and a.selected_choice.is_correct)
        wrong_count = sum(1 for a in user_answers if a.selected_choice and not a.selected_choice.is_correct)
        
        positive_score = correct_count * unit_score
        negative_score = (unit_score / 3) * wrong_count
        net_score = max(0, positive_score - negative_score)
        
        attempt.score = net_score
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()
        
        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)
        return redirect('quiz_results', quiz_id=quiz.id)

    question = get_object_or_404(Question.objects.prefetch_related('choices'), id=question_ids[current_index])

    if request.method == 'POST':
        choice_id = request.POST.get('choice')
    
        if choice_id:
            try:
                selected_choice = Choice.objects.get(id=choice_id)
                UserAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={'selected_choice': selected_choice}
                )
            except Choice.DoesNotExist:
                pass  # خالی رد کن
        
        progress['current_index'] += 1
        request.session.modified = True
        return redirect('quiz_question', pk=quiz.id)

    progress_percentage = int(((current_index + 1) / len(question_ids)) * 100)
    remaining_seconds = int((end_time - timezone.now()).total_seconds())

    return render(request, 'quizzes/question_detail.html', {
        'quiz': quiz,
        'question': question,
        'current_question_index': current_index + 1,
        'total_questions': len(question_ids),
        'progress_percentage': progress_percentage,
        'remaining_seconds': max(0, remaining_seconds),
        'duration_minutes': quiz.duration_minutes,  # ✅ پاس به template
    })

# ------------------------
# نتایج آزمون (ضد تقلب)
# ------------------------

@login_required
def quiz_results_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=True
    ).order_by('-completed_at').first()

    if not attempt:
        messages.warning(request, "شما هنوز این آزمون را کامل نکرده‌اید.")
        return redirect('quiz_list')

    total_questions = quiz.questions.count()
    unit_score = 100 / total_questions if total_questions > 0 else 0
    
    user_answers = attempt.answers.select_related('selected_choice')
    correct_count = 0
    wrong_count = 0
    unanswered_count = 0
    
    for answer in user_answers:
        if answer.selected_choice:
            if answer.selected_choice.is_correct:
                correct_count += 1
            else:
                wrong_count += 1
        else:
            unanswered_count += 1
    
    positive_score = correct_count * unit_score
    negative_score = (unit_score / 3) * wrong_count
    net_score = max(0, positive_score - negative_score)
    
    attempt.score = net_score
    attempt.save()

    context = {
        'quiz': quiz,
        'total_questions': total_questions,
        'correct_count': correct_count,
        'wrong_count': wrong_count,
        'unanswered_count': unanswered_count,
        'unit_score': round(unit_score, 2),
        'positive_score': round(positive_score, 2),
        'negative_score': round(negative_score, 2),
        'net_score': round(net_score, 2),
        'attempt_id': attempt.id,  # ✅ برای تحلیل
    }
    
    return render(request, 'quizzes/results.html', context)

# ✅ صفحه تحلیل جدا
@login_required
def quiz_analysis_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=True
    ).order_by('-completed_at').first()

    if not attempt:
        messages.warning(request, "آزمون پیدا نشد.")
        return redirect('quiz_list')

    total_questions = quiz.questions.count()
    user_answers_data = []
    
    # ✅ همه سوالات (داده شده + خالی)
    all_questions = list(quiz.questions.all())
    
    # پاسخ‌های داده شده
    answered_questions = attempt.answers.values_list('question_id', flat=True)
    
    # ✅ پاسخ‌های داده شده
    for answer in attempt.answers.select_related('selected_choice', 'question').prefetch_related('question__choices'):
        correct_choice = answer.question.choices.filter(is_correct=True).first()
        user_answers_data.append({
            'question_text': answer.question.text,
            'selected_choice_text': answer.selected_choice.choice_text if answer.selected_choice else 'پاسخ نداده',
            'correct_choice_text': correct_choice.choice_text if correct_choice else 'نامشخص',
            'is_correct': answer.selected_choice.is_correct if answer.selected_choice else False,
            'is_answered': bool(answer.selected_choice),
            'question_id': answer.question.id,  # ✅ فقط id
        })
    
    # ✅ سوالات خالی - با پاسخت صحیح!
    for question in all_questions:
        if question.id not in answered_questions:
            correct_choice = question.choices.filter(is_correct=True).first()
            user_answers_data.append({
                'question_text': question.text,
                'selected_choice_text': 'پاسخ نداده',
                'correct_choice_text': correct_choice.choice_text if correct_choice else 'نامشخص',
                'is_correct': False,
                'is_answered': False,
                'question_id': question.id,  # ✅ فقط id
            })

    # ✅ مرتب‌سازی بر اساس ID سوال
    user_answers_data.sort(key=lambda x: x['question_id'])

    context = {
        'quiz': quiz,
        'attempt': attempt,
        'user_answers': user_answers_data,
        'total_questions': total_questions,
    }
    
    return render(request, 'quizzes/analysis.html', context)

# ------------------------
# اشتراک
# ------------------------

@login_required
def subscribe_view(request):
    storage = messages.get_messages(request)
    storage.used = True 

    # 🔥 اطلاعات کامل subscription
    try:
        subscription = request.user.subscription
        subscription.check_status()
        user_status = {
            'status': subscription.status,
            'end_date': subscription.end_date,
            'plan': subscription.plan,
            'is_active': subscription.is_active
        }
    except Subscription.DoesNotExist:
        user_status = None

    available_plans = Plan.objects.filter(is_active=True).order_by('price')

    context = {
        'user_status': user_status,  # 🔥 کلید درست
        'available_plans': available_plans,
    }
    return render(request, 'quizzes/subscribe.html', context)   # accounts نه quizzes!

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

    import time
    time.sleep(3)  # صبر کن تا محدودیت رد بشه

    merchant_id = settings.ZARINPAL_MERCHANT
    amount_rial = int(plan.price) * 10

    callback_url = request.build_absolute_uri(reverse('verify_payment'))

    data = {
        "merchant_id": merchant_id,
        "amount": amount_rial,
        "currency": "IRR",
        "description": f"خرید اشتراک {plan.name}",
        "callback_url": callback_url,
    }

    # ✅ API اصلی (نه sandbox!)
    request_url = 'https://payment.zarinpal.com/pg/v4/payment/request.json'
    start_pay_url = 'https://payment.zarinpal.com/pg/StartPay/'

    try:
        response = requests.post(request_url, json=data, timeout=10)
        res_data = response.json()

        print("🔍 Response:", res_data)

        code = res_data.get('data', {}).get('code')
        authority = res_data.get('data', {}).get('authority')

        if code == 100 and authority:
            request.session['plan_id'] = plan_id
            return redirect(f"{start_pay_url}{authority}")
        else:
            messages.error(request, f"خطا: {res_data}")

    except Exception as e:
        messages.error(request, f"خطا: {str(e)}")

    return redirect('subscribe')

    
@login_required
def verify_payment_view(request):
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')
    plan_id = request.session.get('plan_id')

    if status != 'OK':
        messages.error(request, "❌ پرداخت لغو شد.")
        return redirect('subscribe')

    plan = get_object_or_404(Plan, pk=plan_id)

    data = {
        "merchant_id": '1344b5d4-0048-11e8-94db-005056a205be',
        "amount": int(plan.price) * 10,
        "authority": authority,
    }

    url = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'

    try:
        response = requests.post(url, json=data, timeout=10)
        res_data = response.json()

        print("🔍 Verify Response:", res_data)

        data_part = res_data.get('data', {})
        code = data_part.get('code')
        ref_id = data_part.get('ref_id')

        if code in [100, 101]:
            Subscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timedelta(days=plan.duration_days),
                    'is_active': True,
                    'status': 'فعال',
                }
            )
            messages.success(request, f"✅ پرداخت موفق! شماره تراکنش: {ref_id}")
            return redirect('accounts:dashboard')
        else:
            messages.error(request, f"❌ تایید نشد. کد: {code}")

    except Exception as e:
        messages.error(request, f"خطا: {str(e)}")

    return redirect('subscribe')


