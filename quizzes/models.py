import uuid
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

    is_active = models.BooleanField(default=True,verbose_name="آزمون فعال باشد؟")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "آزمون"  # نام مفرد فارسی
        verbose_name_plural = "آزمون‌ها" # نام جمع فارسی

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
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "سوال"  # نام مفرد فارسی
        verbose_name_plural = "سوالات" # نام جمع فارسی

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
        verbose_name = "گزینه"  # نام مفرد فارسی
        verbose_name_plural = "گزینه‌ها" # نام جمع فارسی

    def __str__(self):
        return self.choice_text

# -----------------------------
# مدل تلاش کاربر
# -----------------------------
class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر") # اضافه شده
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, verbose_name="آزمون") # اضافه شده
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع") # اضافه شده
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان پایان") # اضافه شده
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده؟") # اضافه شده
    score = models.FloatField(default=0, verbose_name="امتیاز") # اضافه شده

    class Meta:
        verbose_name = "تلاش کاربر"  # نام مفرد فارسی
        verbose_name_plural = "تلاش‌های کاربر" # نام جمع فارسی

    def __str__(self):
        return f"{self.user} - {self.quiz} - {self.started_at.strftime('%Y-%m-%d %H:%M')}" # فرمت تاریخ برای خوانایی بهتر

class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers', verbose_name="تلاش") # اضافه شده
    question = models.ForeignKey('Question', on_delete=models.CASCADE, verbose_name="سوال") # اضافه شده
    selected_choice = models.ForeignKey('Choice', on_delete=models.CASCADE, verbose_name="گزینه انتخاب شده") # اضافه شده

    class Meta:
        verbose_name = "پاسخ کاربر"  # نام مفرد فارسی
        verbose_name_plural = "پاسخ‌های کاربر" # نام جمع فارسی

    def __str__(self):
        return f"{self.attempt} - {self.question}"
    
class HomeSlider(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان")
    image = models.FileField(upload_to='sliders/', verbose_name="تصویر", blank=True)  # ✅ FileField
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
    

# آمارگیری
class Visitor(models.Model):

    visitor_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,      
        unique=True,        
        db_index=True,       
        verbose_name="شناسه بازدیدکننده" 
    )


    visit_time = models.DateTimeField(
        verbose_name="زمان بازدید",
        default=timezone.now 
    )

    def __str__(self):
        return f"Visitor: {self.visitor_id} on {self.visit_time.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "بازدیدکننده" 
        verbose_name_plural = "بازدیدکنندگان" 
        ordering = ['-visit_time']
