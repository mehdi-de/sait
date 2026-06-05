from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from datetime import timedelta

# -----------------------------
# مدل آزمون
# -----------------------------
class Quiz(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان آزمون")
    description = models.TextField(verbose_name="توضیحات آزمون", blank=True, null=True)
    is_premium = models.BooleanField(default=False, verbose_name="آزمون ویژه است؟")
    duration_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True, verbose_name="آزمون فعال باشد؟")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "آزمون"
        verbose_name_plural = "آزمون‌ها"

    def __str__(self):
        return self.title

# -----------------------------
# مدل سوال
# -----------------------------
class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name="آزمون مرتبط")
    text = models.TextField(verbose_name="متن سوال")
    is_active = models.BooleanField(_('فعال باشد؟'), default=True, help_text=_('تعیین می‌کند که این سوال فعال باشد یا خیر.'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "سوال"
        verbose_name_plural = "سوالات"

    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text

# -----------------------------
# مدل گزینه‌ها
# -----------------------------
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices', verbose_name="سوال مرتبط")
    choice_text = models.CharField(max_length=500, verbose_name="متن گزینه")
    is_correct = models.BooleanField(default=False, verbose_name="آیا این گزینه صحیح است؟")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "گزینه"
        verbose_name_plural = "گزینه‌ها"

    def __str__(self):
        return self.choice_text

# -----------------------------
# مدل تلاش کاربر
# -----------------------------
class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر")
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, verbose_name="آزمون")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان پایان")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده؟")
    score = models.FloatField(default=0, verbose_name="امتیاز")

    class Meta:
        verbose_name = "تلاش کاربر"
        verbose_name_plural = "تلاش‌های کاربر"

    def __str__(self):
        return f"{self.user} - {self.quiz} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"

class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers', verbose_name="تلاش")
    question = models.ForeignKey('Question', on_delete=models.CASCADE, verbose_name="سوال")
    selected_choice = models.ForeignKey('Choice', on_delete=models.CASCADE, verbose_name="گزینه انتخاب شده")

    class Meta:
        verbose_name = "پاسخ کاربر"
        verbose_name_plural = "پاسخ‌های کاربر"

    def __str__(self):
        return f"{self.attempt} - {self.question}"

class HomeSlider(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان")
    image = models.FileField(upload_to='sliders/', verbose_name="تصویر", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = "اسلاید"
        verbose_name_plural = "اسلایدها"

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return "/static/image/slide1.jpg"

# -----------------------------
# مدل آمار بازدید ✅ جدید
# -----------------------------
class VisitorStats(models.Model):
    date = models.DateField(unique=True)
    unique_visitors_today = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "آمار بازدید"
        verbose_name_plural = "آمار بازدیدها"
    
    def __str__(self):
        return f"{self.date}: {self.unique_visitors_today} بازدیدکننده"


class IPVisit(models.Model):
    ip_address = models.GenericIPAddressField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['ip_address', 'date']
        verbose_name = "بازدید IP"
        verbose_name_plural = "بازدیدهای IP"
    
    def __str__(self):
        return f"{self.ip_address} - {self.date}"

class AdBanner(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان")
    image = models.ImageField(upload_to='ads/', verbose_name="عکس/گیف")
    link = models.URLField(verbose_name="لینک", blank=True)
    position = models.CharField(max_length=20, choices=[('left', ' تبلیغ اولی'), ('right', 'تبلیغ دومی ')], verbose_name="موقعیت")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "بنر تبلیغ"
        verbose_name_plural = "بنرهای تبلیغ"