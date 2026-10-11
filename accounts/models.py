from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Plan(models.Model):

    name = models.CharField(
        max_length=100,
        verbose_name='نام پلن'
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت'
    )

    duration_days = models.PositiveIntegerField(
        verbose_name='مدت اشتراک'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال است؟'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='توضیحات'
    )

    class Meta:
        verbose_name = 'پلن اشتراک'
        verbose_name_plural = 'پلن‌های اشتراک'

    def __str__(self):
        return f'{self.name} ({self.duration_days} روز)'


class Subscription(models.Model):

    STATUS_CHOICES = [
        ('ندارد', 'ندارد'),
        ('فعال', 'فعال'),
        ('منقضی', 'منقضی'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription'
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='پلن'
    )

    is_active = models.BooleanField(
        default=False,
        verbose_name='فعال'
    )

    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ شروع'
    )

    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ پایان'
    )

    authority = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    ref_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ندارد'
    )

    class Meta:
        verbose_name = 'اشتراک'
        verbose_name_plural = 'اشتراک‌ها'

    def __str__(self):
        return f"{self.user.username} - {self.status}"

    def check_status(self):

        now = timezone.now()

        if self.end_date:

            if now > self.end_date:
                self.is_active = False
                self.status = 'منقضی'

            else:
                self.is_active = True
                self.status = 'فعال'

        else:
            self.is_active = False
            self.status = 'ندارد'

        self.save(update_fields=['is_active', 'status'])

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(
            self.status,
            self.status
        )