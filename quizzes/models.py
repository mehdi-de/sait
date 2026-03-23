
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# -----------------------------
# مدل آزمون
# -----------------------------
class Quiz(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان آزمون")
    description = models.TextField(verbose_name="توضیحات آزمون", blank=True, null=True)
    is_premium = models.BooleanField(default=False, verbose_name="آزمون ویژه است؟")
    duration_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")  # اضافه شد
    
    def __str__(self):
        return self.title
    
# -----------------------------
# مدل سوال
# -----------------------------
class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name="آزمون مرتبط")
    text = models.TextField(verbose_name="متن سوال")
    is_active = models.BooleanField(
        _('فعال باشد؟'),
        default=True,
        help_text=_('تعیین می‌کند که این سوال فعال باشد یا خیر.')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")  # اضافه شد

    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text

# -----------------------------
# مدل گزینه‌ها
# -----------------------------
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices', verbose_name="سوال مرتبط")
    choice_text = models.CharField(max_length=500, verbose_name="متن گزینه")
    is_correct = models.BooleanField(default=False, verbose_name="آیا این گزینه صحیح است؟")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")  # اضافه شد

    def __str__(self):
        return self.choice_text

# -----------------------------
# مدل تلاش کاربر
# -----------------------------
class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    score = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user} - {self.quiz} - {self.started_at}"


class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    selected_choice = models.ForeignKey('Choice', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.attempt} - {self.question}"
