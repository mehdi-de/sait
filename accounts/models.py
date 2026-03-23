from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# --- مدل جدید: تعریف پلن‌های مختلف (بدون تغییر عمده، فقط import timedelta برای استفاده بعدی) ---
class Plan(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام پلن")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="قیمت به تومان")
    duration_days = models.PositiveIntegerField(verbose_name="مدت زمان اشتراک (روز)")  # تغییر: PositiveIntegerField برای مثبت بودن اجباری
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات (اختیاری)")  # اضافه: فیلد توضیحات برای کامل‌تر کردن

    def __str__(self):
        return f"{self.name} ({self.duration_days} روز)"

    class Meta:
        verbose_name = "پلن اشتراک"
        verbose_name_plural = "پلن‌های اشتراک"



class Subscription(models.Model):
    STATUS_CHOICES = [  # اضافه: choices برای status
        ('ندارد', 'ندارد'),
        ('فعال', 'فعال'),
        ('منقضی', 'منقضی'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')  # تغییر کوچک: related_name اضافه برای دسترسی آسان (user.subscription)
    
    # اتصال به مدل Plan
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="پلن خریداری شده")
    
    is_active = models.BooleanField(default=False, verbose_name="فعال است؟")
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انقضا")
    
    # اضافه: فیلدهای زرین‌پال (برای ذخیره Authority و Ref ID در پرداخت)
    authority = models.CharField(max_length=100, blank=True, null=True, verbose_name="شناسه Authority زرین‌پال")
    ref_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="شناسه پیگیری زرین‌پال (Ref ID)")
    
    # اضافه: status field برای نمایش بهتر (با choices)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ندارد', verbose_name="وضعیت اشتراک")

    def __str__(self):
        status = "فعال" if self.is_active else "غیرفعال"
        return f"اشتراک {self.user.username} - وضعیت: {status}"

    # بهبود: check_status (status رو هم آپدیت می‌کنه)
    def check_status(self):
        now = timezone.now()

        if self.end_date and now > self.end_date:
            self.is_active = False
            self.status = 'منقضی'
        elif self.end_date and now <= self.end_date:
            self.is_active = True
            self.status = 'فعال'
        else:
            self.is_active = False
            self.status = 'ندارد'
        # ذخیره فقط فیلدهای تغییرکرده برای بهینه‌سازی
        super().save(update_fields=['is_active', 'status'])

    # اضافه: property برای نمایش status در template (سازگار با get_status_display قبلی)
    @property
    def get_status_display(self):
        self.check_status()  # مطمئن شو status به‌روز باشه
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    # تغییر: در save()، check_status رو فراخوانی کن برای آپدیت خودکار
   

    class Meta:
        verbose_name = "اشتراک کاربر"
        verbose_name_plural = "اشتراک‌های کاربران"