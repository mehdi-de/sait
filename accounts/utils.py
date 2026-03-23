from django.db.models import Sum, Count
from quizzes.models import QuizAttempt

def get_user_rank(user):
    """
    رتبه، مجموع و میانگین نمره کاربر را برمی‌گرداند.
    اگر کاربر هیچ آزمون پریمیومی نداده باشد، None برمی‌گردد.
    """

    leaderboard_data = QuizAttempt.objects.filter(
        is_completed=True,
        quiz__is_premium=True
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

    return None
