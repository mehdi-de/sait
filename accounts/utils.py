from django.db.models import Sum, Count

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
    'اسفند'
]


def get_user_rank(user):

    leaderboard_data = (
        QuizAttempt.objects.filter(
            is_completed=True,
            quiz__is_premium=True,
            quiz__is_active=True,
        )
        .values('user_id')
        .annotate(
            total_score=Sum('score'),
            quizzes_taken=Count('id')
        )
        .order_by('-total_score')
    )

    rank = 0
    last_score = None

    for index, entry in enumerate(leaderboard_data, start=1):

        current_score = entry['total_score']

        if current_score != last_score:
            rank = index

        if entry['user_id'] == user.id:

            quizzes_taken = entry['quizzes_taken'] or 1

            avg_score = (
                entry['total_score'] / quizzes_taken
            )

            return {
                'rank': rank,
                'total_score': round(entry['total_score'], 2),
                'average': round(avg_score, 2),
                'quizzes_taken': quizzes_taken
            }

        last_score = current_score

    return {
        'rank': '-',
        'total_score': 0,
        'average': 0,
        'quizzes_taken': 0
    }


def persian_date(dt):

    if not dt:
        return '-'

    jdate = jdatetime.datetime.fromgregorian(
        datetime=dt
    )

    return jdate.strftime('%Y/%m/%d')


def persian_full_date(dt):

    if not dt:
        return '-'

    jdate = jdatetime.datetime.fromgregorian(
        datetime=dt
    )

    return (
        f"{jdate.strftime('%Y/%m/%d')} "
        f"- {dt.strftime('%H:%M')}"
    )


def persian_short_date(dt):

    if not dt:
        return '-'

    jdate = jdatetime.datetime.fromgregorian(
        datetime=dt
    )

    return (
        f"{jdate.day} "
        f"{PERSIAN_MONTHS[jdate.month - 1]}"
    )