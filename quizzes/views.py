
from datetime import timedelta
import random

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
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
        'today_unique': (
            today_stats.unique_visitors_today
            if today_stats else 0
        ),
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
# درباره ما
# -----------------------------------
def about(request):

    return render(
        request,
        'quizzes/about.html'
    )


# -----------------------------------
# لیست آزمون‌ها
# عمومی برای همه کاربران
# -----------------------------------
def quiz_list_view(request):

    quizzes = Quiz.objects.filter(
        is_active=True
    ).prefetch_related('questions')

    completed_quiz_ids = []
    has_subscription = False

    # اطلاعات تلاش‌های قبلی فقط برای کاربران واردشده
    if request.user.is_authenticated:

        completed_quiz_ids = QuizAttempt.objects.filter(
            user=request.user,
            is_completed=True,
            quiz__is_premium=True
        ).values_list(
            'quiz_id',
            flat=True
        )

        try:
            subscription = request.user.subscription
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
        Quiz,
        pk=pk,
        is_active=True
    )

    # بررسی اشتراک برای آزمون ویژه
    if quiz.is_premium:

        try:
            subscription = request.user.subscription
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

    # شرکت مجدد مجاز است.
    # اگر تلاش نیمه‌کاره وجود داشته باشد، همان تلاش ادامه پیدا می‌کند.
    existing_attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        is_completed=False
    ).order_by('-started_at').first()

    if existing_attempt:

        attempt = existing_attempt

    else:

        questions = list(
            quiz.questions.filter(is_active=True)
        )

        if not questions:
            messages.warning(
                request,
                'این آزمون هنوز سوالی ندارد.'
            )
            return redirect('quizzes:quiz_list')

        random.shuffle(questions)

        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz
        )

        request.session['attempt_id'] = attempt.id

        request.session['quiz_progress'] = {
            'quiz_id': quiz.id,
            'question_ids': [q.id for q in questions],
            'current_index': 0,
            'start_time': attempt.started_at.isoformat(),
        }

        request.session.modified = True

        messages.success(
            request,
            f'آزمون {quiz.title} شروع شد.'
        )

        return redirect(
            'quizzes:quiz_question',
            pk=quiz.id
        )

    # بازیابی اطلاعات تلاش نیمه‌کاره
    progress = request.session.get('quiz_progress')

    same_attempt = (
        request.session.get('attempt_id') == attempt.id
        and progress
        and progress.get('quiz_id') == quiz.id
    )

    if not same_attempt:

        answered_ids = set(
            attempt.answers.values_list(
                'question_id',
                flat=True
            )
        )

        remaining_questions = list(
            quiz.questions.filter(
                is_active=True
            ).exclude(
                id__in=answered_ids
            )
        )

        random.shuffle(remaining_questions)

        request.session['attempt_id'] = attempt.id

        request.session['quiz_progress'] = {
            'quiz_id': quiz.id,
            'question_ids': [
                q.id for q in remaining_questions
            ],
            'current_index': 0,
            'start_time': attempt.started_at.isoformat(),
        }

        request.session.modified = True

    return redirect(
        'quizzes:quiz_question',
        pk=quiz.id
    )


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
            'لطفاً آزمون را مجدداً شروع کنید.'
        )
        return redirect('quizzes:quiz_list')

    if progress.get('quiz_id') != quiz.id:
        messages.warning(
            request,
            'اطلاعات آزمون معتبر نیست.'
        )
        return redirect('quizzes:quiz_list')

    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        user=request.user,
        quiz=quiz
    )

    # اگر آزمون قبلاً تمام شده باشد
    if attempt.is_completed:

        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)

        return redirect(
            'quizzes:quiz_analysis',
            quiz_id=quiz.id
        )

    start_time = attempt.started_at

    end_time = start_time + timedelta(
        minutes=quiz.duration_minutes
    )

    total_questions = quiz.questions.filter(
        is_active=True
    ).count()

    # -----------------------------------
    # تابع پایان آزمون و ثبت نمره
    # -----------------------------------
    def finish_attempt():

        correct_count = attempt.answers.filter(
            question__quiz=quiz,
            question__is_active=True,
            selected_choice__is_correct=True
        ).count()

        wrong_count = attempt.answers.filter(
            question__quiz=quiz,
            question__is_active=True,
            selected_choice__is_correct=False
        ).count()

        unit_score = (
            100 / total_questions
            if total_questions > 0
            else 0
        )

        positive_score = correct_count * unit_score

        negative_score = wrong_count * (unit_score / 3)

        final_score = max(
            0,
            positive_score - negative_score
        )

        # ذخیره نتیجه آزمون
        attempt.score = round(final_score, 2)
        attempt.is_completed = True
        attempt.completed_at = timezone.now()

        attempt.save(
            update_fields=[
                'score',
                'is_completed',
                'completed_at'
            ]
        )

        # پاک کردن اطلاعات آزمون از Session
        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)

        request.session.modified = True

        messages.success(
            request,
            'آزمون شما با موفقیت به پایان رسید.'
        )

        # انتقال مستقیم به صفحه تحلیل آزمون
        return redirect(
            'quizzes:quiz_analysis',
            quiz_id=quiz.id
        )

    # -----------------------------------
    # بررسی تعداد سوالات
    # -----------------------------------
    if total_questions == 0:

        messages.warning(
            request,
            'این آزمون هنوز سؤال فعالی ندارد.'
        )

        return finish_attempt()

    # -----------------------------------
    # بررسی اتمام زمان آزمون
    # -----------------------------------
    if timezone.now() >= end_time:

        messages.warning(
            request,
            'زمان آزمون به پایان رسید.'
        )

        return finish_attempt()

    # -----------------------------------
    # دریافت اطلاعات پیشرفت آزمون
    # -----------------------------------
    question_ids = progress.get('question_ids', [])

    current_index = progress.get('current_index', 0)

    if (
        not isinstance(question_ids, list)
        or not isinstance(current_index, int)
        or isinstance(current_index, bool)
        or current_index < 0
    ):

        request.session.pop('quiz_progress', None)
        request.session.pop('attempt_id', None)

        messages.warning(
            request,
            'اطلاعات پیشرفت آزمون معتبر نیست. لطفاً دوباره شروع کنید.'
        )

        return redirect('quizzes:quiz_list')

    # -----------------------------------
    # بررسی پایان سوالات
    # -----------------------------------
    if current_index >= len(question_ids):

        return finish_attempt()

    # -----------------------------------
    # دریافت سوال فعلی
    # -----------------------------------
    question = get_object_or_404(
        Question.objects.prefetch_related('choices'),
        id=question_ids[current_index],
        quiz=quiz,
        is_active=True
    )

    # -----------------------------------
    # ثبت پاسخ کاربر
    # -----------------------------------
    if request.method == 'POST':

        choice_id = request.POST.get('choice')

        # اگر کاربر گزینه‌ای انتخاب کرده باشد
        if choice_id:

            try:

                selected_choice = Choice.objects.get(
                    id=choice_id,
                    question=question
                )

            except (
                Choice.DoesNotExist,
                ValueError,
                TypeError
            ):

                messages.warning(
                    request,
                    'گزینه انتخاب‌شده معتبر نیست.'
                )

                return redirect(
                    'quizzes:quiz_question',
                    pk=quiz.id
                )

            # ثبت یا بروزرسانی پاسخ
            UserAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'selected_choice': selected_choice
                }
            )

        # اگر گزینه‌ای انتخاب نشده باشد،
        # سوال بدون پاسخ رد می‌شود.

        progress['current_index'] += 1

        request.session['quiz_progress'] = progress
        request.session.modified = True

        return redirect(
            'quizzes:quiz_question',
            pk=quiz.id
        )

    # -----------------------------------
    # محاسبه درصد پیشرفت
    # -----------------------------------
    progress_percentage = int(
        ((current_index + 1) / len(question_ids)) * 100
    )

    # -----------------------------------
    # محاسبه زمان باقی‌مانده
    # -----------------------------------
    remaining_seconds = int(
        (end_time - timezone.now()).total_seconds()
    )

    # -----------------------------------
    # اطلاعات ارسالی به قالب
    # -----------------------------------
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

    # آخرین تلاش تکمیل‌شده کاربر
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

    total_questions = quiz.questions.filter(
        is_active=True
    ).count()

    correct_count = attempt.answers.filter(
        question__quiz=quiz,
        question__is_active=True,
        selected_choice__is_correct=True
    ).count()

    wrong_count = attempt.answers.filter(
        question__quiz=quiz,
        question__is_active=True,
        selected_choice__is_correct=False
    ).count()

    answered_questions = attempt.answers.filter(
        question__quiz=quiz,
        question__is_active=True,
        selected_choice__isnull=False
    ).count()

    unanswered_count = max(
        0,
        total_questions - answered_questions
    )

    unit_score = (
        100 / total_questions
        if total_questions > 0
        else 0
    )

    positive_score = correct_count * unit_score

    negative_score = wrong_count * (unit_score / 3)

    final_score = attempt.score

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

    # آخرین تلاش تکمیل‌شده کاربر
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

    # دریافت سوالات فعال
    questions = quiz.questions.filter(
        is_active=True
    ).prefetch_related('choices').order_by('id')

    # دریافت پاسخ‌های ثبت‌شده این تلاش
    answers = attempt.answers.filter(
        question__quiz=quiz
    ).select_related(
        'selected_choice'
    )

    # برای دسترسی سریع به پاسخ هر سوال
    answer_map = {
        answer.question_id: answer
        for answer in answers
    }

    user_answers_data = []

    correct_count = 0
    wrong_count = 0
    unanswered_count = 0

    for question in questions:

        answer = answer_map.get(question.id)

        selected_choice = (
            answer.selected_choice
            if answer else None
        )

        # پیدا کردن گزینه صحیح
        correct_choice = question.choices.filter(
            is_correct=True
        ).first()

        # بررسی پاسخ داده شده یا بدون پاسخ بودن
        is_answered = selected_choice is not None

        is_correct = (
            selected_choice.is_correct
            if is_answered else False
        )

        if is_correct:
            correct_count += 1

        elif is_answered:
            wrong_count += 1

        else:
            unanswered_count += 1

        # استخراج متن سوال و گزینه‌ها
        question_text = (
            getattr(question, 'text', None)
            or getattr(question, 'question_text', None)
            or str(question)
        )

        selected_choice_text = (
            getattr(selected_choice, 'text', None)
            or getattr(selected_choice, 'choice_text', None)
            or str(selected_choice)
            if is_answered else 'پاسخ نداده'
        )

        correct_choice_text = (
            getattr(correct_choice, 'text', None)
            or getattr(correct_choice, 'choice_text', None)
            or str(correct_choice)
            if correct_choice else 'نامشخص'
        )

        user_answers_data.append({

            # اطلاعات اصلی
            'question': question,
            'selected_choice': selected_choice,
            'correct_choice': correct_choice,

            # متن‌های مورد نیاز HTML
            'question_text': question_text,
            'selected_choice_text': selected_choice_text,
            'correct_choice_text': correct_choice_text,

            # وضعیت پاسخ
            'is_answered': is_answered,
            'is_correct': is_correct,

        })

    total_questions = len(user_answers_data)

    context = {
        'quiz': quiz,
        'attempt': attempt,

        'user_answers': user_answers_data,

        # آمار کلی
        'total_questions': total_questions,
        'correct_count': correct_count,
        'wrong_count': wrong_count,
        'unanswered_count': unanswered_count,
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

        if subscription.is_active and subscription.end_date:

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

    merchant_id = getattr(
        settings,
        'ZARINPAL_MERCHANT',
        None
    )

    if not merchant_id:
        messages.error(
            request,
            'تنظیمات درگاه پرداخت انجام نشده است.'
        )
        return redirect('quizzes:subscribe')

    # تبدیل مبلغ تومان به ریال
    amount_rial = int(plan.price * 10)

    if amount_rial <= 0:
        messages.error(
            request,
            'مبلغ پلن معتبر نیست.'
        )
        return redirect('quizzes:subscribe')

    callback_url = request.build_absolute_uri(
        reverse('quizzes:verify_payment')
    )

    data = {
        'merchant_id': merchant_id,
        'amount': amount_rial,
        'currency': 'IRR',
        'description': f'خرید اشتراک {plan.name}',
        'callback_url': callback_url,
    }

    request_url = settings.ZARINPAL_REQUEST_URL
    start_pay_url = settings.ZARINPAL_STARTPAY_URL

    try:
        response = requests.post(
            request_url,
            json=data,
            timeout=15
        )

        response.raise_for_status()

        response_data = response.json()
        payment_data = response_data.get('data') or {}

        code = payment_data.get('code')
        authority = payment_data.get('authority')

        if code == 100 and authority:

            request.session['pending_payment'] = {
                'plan_id': plan.id,
                'authority': authority,
            }

            request.session.modified = True

            return redirect(
                start_pay_url.format(
                    authority=authority
                )
            )

        messages.error(
            request,
            'درخواست پرداخت از طرف درگاه تأیید نشد.'
        )

    except requests.RequestException:
        messages.error(
            request,
            'ارتباط با درگاه پرداخت برقرار نشد. لطفاً دوباره تلاش کنید.'
        )

    except ValueError:
        messages.error(
            request,
            'پاسخ دریافتی از درگاه پرداخت معتبر نیست.'
        )

    except Exception:
        messages.error(
            request,
            'در فرایند پرداخت خطایی رخ داد.'
        )

    return redirect('quizzes:subscribe')


# -----------------------------------
# تایید پرداخت
# -----------------------------------
@login_required
def verify_payment_view(request):

    authority = request.GET.get('Authority')
    status = request.GET.get('Status')

    if not authority:

        messages.error(
            request,
            'اطلاعات پرداخت معتبر نیست.'
        )

        return redirect('quizzes:subscribe')

    # بررسی اینکه این پرداخت قبلاً ثبت شده است یا نه
    try:

        subscription = request.user.subscription

        if (
            subscription.authority == authority
            and subscription.ref_id
        ):

            messages.success(
                request,
                'این پرداخت قبلاً تأیید و اشتراک شما فعال شده است.'
            )

            return redirect('quizzes:subscribe')

    except Subscription.DoesNotExist:
        pass

    if status != 'OK':

        messages.error(
            request,
            'پرداخت لغو شد یا توسط درگاه تأیید نشد.'
        )

        return redirect('quizzes:subscribe')

    # دریافت اطلاعات پرداخت از Session
    pending_payment = request.session.get(
        'pending_payment'
    )

    if not pending_payment:

        messages.error(
            request,
            'اطلاعات سفارش پیدا نشد. لطفاً با پشتیبانی تماس بگیرید.'
        )

        return redirect('quizzes:subscribe')

    # کنترل تطبیق کد پرداخت
    if pending_payment.get('authority') != authority:

        messages.error(
            request,
            'اطلاعات پرداخت با سفارش شما مطابقت ندارد.'
        )

        return redirect('quizzes:subscribe')

    plan_id = pending_payment.get('plan_id')

    plan = get_object_or_404(
        Plan,
        pk=plan_id,
        is_active=True
    )

    merchant_id = getattr(
        settings,
        'ZARINPAL_MERCHANT',
        None
    )

    if not merchant_id:

        messages.error(
            request,
            'تنظیمات درگاه پرداخت انجام نشده است.'
        )

        return redirect('quizzes:subscribe')

    # فرض: قیمت پلن در دیتابیس به تومان ذخیره شده است.
    amount_rial = int(plan.price * 10)

    data = {
        'merchant_id': merchant_id,
        'amount': amount_rial,
        'authority': authority,
    }

    verify_url = settings.ZARINPAL_VERIFY_URL

    try:

        response = requests.post(
            verify_url,
            json=data,
            timeout=15
        )

        response.raise_for_status()

        result = response.json()

        verify_data = result.get('data', {})

        code = verify_data.get('code')

        # کد 100: پرداخت موفق
        # کد 101: پرداخت قبلاً تأیید شده است
        if code in (100, 101):

            ref_id = verify_data.get('ref_id')

            now = timezone.now()

            # ثبت و فعال‌سازی اشتراک در یک تراکنش
            with transaction.atomic():

                subscription, created = (
                    Subscription.objects.select_for_update().get_or_create(
                        user=request.user
                    )
                )

                # جلوگیری از تمدید دوباره همین پرداخت
                if subscription.authority == authority:

                    request.session.pop(
                        'pending_payment',
                        None
                    )

                    messages.success(
                        request,
                        'این پرداخت قبلاً ثبت شده است.'
                    )

                    return redirect('quizzes:subscribe')

                # اگر اشتراک قبلی هنوز فعال باشد،
                # اشتراک جدید از تاریخ پایان قبلی شروع می‌شود.
                if (
                    subscription.end_date
                    and subscription.end_date > now
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

                subscription.is_active = True
                subscription.status = 'فعال'

                subscription.authority = authority
                subscription.ref_id = (
                    str(ref_id) if ref_id else ''
                )

                subscription.save()

            request.session.pop(
                'pending_payment',
                None
            )

            request.session.modified = True

            messages.success(
                request,
                'پرداخت با موفقیت تأیید شد و اشتراک شما فعال گردید.'
            )

            return redirect('quizzes:subscribe')

        messages.error(
            request,
            'پرداخت توسط درگاه تأیید نشد.'
        )

    except (
        requests.RequestException,
        ValueError
    ):

        messages.error(
            request,
            'در بررسی پرداخت خطایی رخ داد. لطفاً دوباره تلاش کنید.'
        )

    return redirect('quizzes:subscribe')

# -----------------------------------
# مرور آزمون‌های تکمیل‌شده کاربر
# -----------------------------------
@login_required
def my_attempts_view(request):

    attempts = QuizAttempt.objects.filter(
        user=request.user,
        is_completed=True
    ).select_related(
        'quiz'
    ).order_by(
        '-completed_at'
    )

    context = {
        'attempts': attempts,
    }

    return render(
        request,
        'quizzes/my_attempts.html',
        context
    )