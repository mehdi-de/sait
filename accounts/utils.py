
from django.db.models import Sum, Count
from django.utils import timezone

from quizzes.models import QuizAttempt

import jdatetime


PERSIAN_MONTHS = [
    'فروردین',
    'اردیبهشت',
    'خرداد',
    'تیر',
    'مرداد',
    'شهریور',
    'مهر',
    'آبان',
    'آذر',
    'دی',
    'بهمن',
    'اسفند',
]



def get_user_rank(user):
    """
    محاسبه رتبه کاربر بر اساس مجموع امتیاز آزمون‌های
    ویژه، فعال و تکمیل‌شده.
    """

    leaderboard_data = (
        QuizAttempt.objects
        .filter(
            is_completed=True,
            quiz__is_premium=True,
            quiz__is_active=True,
        )
        .values('user_id')
        .annotate(
            total_score=Sum('score', default=0),
            quizzes_taken=Count('id'),
        )
    )

    # دریافت اطلاعات کاربر
    user_data = leaderboard_data.filter(
        user_id=user.id
    ).order_by('user_id').first()

    if not user_data:
        return {
            'rank': '-',
            'total_score': 0,
            'average': 0,
            'quizzes_taken': 0,
        }

    total_score = user_data['total_score'] or 0
    quizzes_taken = user_data['quizzes_taken'] or 0

    average_score = (
        total_score / quizzes_taken
        if quizzes_taken
        else 0
    )

    # تعداد کاربرانی که امتیاز بیشتری دارند
    users_above = leaderboard_data.filter(
        total_score__gt=total_score
    ).count()

    rank = users_above + 1

    return {
        'rank': rank,
        'total_score': round(total_score, 2),
        'average': round(average_score, 2),
        'quizzes_taken': quizzes_taken,
    }



def _get_local_datetime(dt):
    """
    تبدیل datetime دارای timezone به زمان محلی پروژه.
    """

    if not dt:
        return None

    if timezone.is_aware(dt):
        return timezone.localtime(dt)

    return dt


def persian_date(dt):
    """
    تبدیل تاریخ میلادی به تاریخ شمسی با فرمت:
    1405/08/21
    """

    if not dt:
        return '-'

    dt = _get_local_datetime(dt)

    jdate = jdatetime.datetime.fromgregorian(
        datetime=dt
    )

    return jdate.strftime('%Y/%m/%d')


def persian_full_date(dt):
    """
    تبدیل تاریخ و ساعت میلادی به شمسی با فرمت:
    1405/08/21 - 14:30
    """

    if not dt:
        return '-'

    dt = _get_local_datetime(dt)

    jdate = jdatetime.datetime.fromgregorian(
        datetime=dt
    )

    return (
        f"{jdate.strftime('%Y/%m/%d')} "
        f"- {dt.strftime('%H:%M')}"
    )


def persian_short_date(dt):
    """
    نمایش تاریخ کوتاه شمسی با نام ماه:
    21 آبان
    """

    if not dt:
        return '-'

    dt = _get_local_datetime(dt)

    jdate = jdatetime.datetime.fromgregorian(
        datetime=dt
    )

    month_name = PERSIAN_MONTHS[jdate.month - 1]

    return f"{jdate.day} {month_name}"
