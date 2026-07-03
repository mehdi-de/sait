from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Quiz(models.Model):

    title = models.CharField(
        max_length=200,
        verbose_name='عنوان آزمون'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='توضیحات آزمون'
    )

    is_premium = models.BooleanField(
        default=False,
        verbose_name='آزمون ویژه است؟'
    )

    duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name='زمان آزمون'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال باشد؟'
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='تاریخ ایجاد'
    )

    class Meta:
        verbose_name = 'آزمون'
        verbose_name_plural = 'آزمون‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Question(models.Model):

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='آزمون'
    )

    text = models.TextField(
        verbose_name='متن سوال'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )

    created_at = models.DateTimeField(
        default=timezone.now
    )

    class Meta:
        verbose_name = 'سوال'
        verbose_name_plural = 'سوالات'

    def __str__(self):
        return self.text[:50]


class Choice(models.Model):

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name='سوال'
    )

    choice_text = models.CharField(
        max_length=500,
        verbose_name='متن گزینه'
    )

    is_correct = models.BooleanField(
        default=False,
        verbose_name='پاسخ صحیح'
    )

    class Meta:
        verbose_name = 'گزینه'
        verbose_name_plural = 'گزینه‌ها'

    def __str__(self):
        return self.choice_text


class QuizAttempt(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    is_completed = models.BooleanField(
        default=False
    )

    score = models.FloatField(
        default=0
    )

    class Meta:
        verbose_name = 'تلاش آزمون'
        verbose_name_plural = 'تلاش‌های آزمون'

    def __str__(self):
        return f'{self.user} - {self.quiz}'


class UserAnswer(models.Model):

    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'پاسخ کاربر'
        verbose_name_plural = 'پاسخ‌های کاربران'


class HomeSlider(models.Model):

    title = models.CharField(
        max_length=100
    )

    image = models.ImageField(
        upload_to='sliders/'
    )

    is_active = models.BooleanField(
        default=True
    )

    order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'اسلایدر'
        verbose_name_plural = 'اسلایدرها'

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return ''


class VisitorStats(models.Model):

    date = models.DateField(unique=True)

    unique_visitors_today = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ['-date']
        verbose_name = 'آمار بازدید'
        verbose_name_plural = 'آمار بازدیدها'

    def __str__(self):
        return str(self.date)


class IPVisit(models.Model):

    ip_address = models.GenericIPAddressField()

    date = models.DateField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('ip_address', 'date')
        verbose_name = 'بازدید IP'
        verbose_name_plural = 'بازدیدهای IP'

    def __str__(self):
        return self.ip_address


class AdBanner(models.Model):

    POSITION_CHOICES = [
        ('left', 'سمت چپ'),
        ('right', 'سمت راست'),
    ]

    title = models.CharField(
        max_length=100
    )

    image = models.ImageField(
        upload_to='ads/'
    )

    link = models.URLField(
        blank=True
    )

    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = 'تبلیغ'
        verbose_name_plural = 'تبلیغات'

    def __str__(self):
        return self.title