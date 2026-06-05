from django.db.models import Sum, Count
from quizzes.models import QuizAttempt
from jdatetime import datetime as jdatetime  # 🔥 اضافه

def get_user_rank(user):
    """
    رتبه، مجموع و میانگین نمره کاربر را برمی‌گرداند.
    """
    leaderboard_data = QuizAttempt.objects.filter(
        is_completed=True,
        quiz__is_premium=True,
        quiz__is_active=True,
    ).values(
        'user_id'
    ).annotate(
        total_score=Sum('score'),
        quizzes_taken=Count('id')
    ).order_by('-total_score')

    rank = 0
    last_score = None

    for entry in leaderboard_data:
        score = entry['total_score']
        if score != last_score:
            rank += 1

        if entry['user_id'] == user.id:
            avg_score = entry['total_score'] / entry['quizzes_taken']
            return {
                'rank': rank,
                'total_score': entry['total_score'],
                'average': round(avg_score, 2),
                'quizzes_taken': entry['quizzes_taken']
            }
        last_score = score

    return None  # 🔥 بدون تغییر

# 🔥 توابع تاریخ ایرانی - جدید!
def persian_date(dt):
    """تبدیل به شمسی: 1405/02/14"""
    if not dt:
        return "-"
    jdate = jdatetime.fromgregorian(datetime=dt)
    return jdate.strftime("%Y/%m/%d")

def persian_full_date(dt):
    """کامل: 1405/02/14 - 15:56"""
    if not dt:
        return "-"
    jdate = jdatetime.fromgregorian(datetime=dt)
    return f"{jdate.strftime('%Y/%m/%d')} - {dt.strftime('%H:%M')}"

def persian_short_date(dt):
    """کوتاه: 14 اردیبهشت"""
    if not dt:
        return "-"
    jdate = jdatetime.fromgregorian(datetime=dt)
    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
              'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    return f"{jdate.day} {months[jdate.month-1]}"