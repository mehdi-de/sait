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

    def __str__(self):
        return f'{self.name} ({self.duration_days} روز)'

    class Meta:
        verbose_name = 'پلن اشتراک'
        verbose_name_plural = 'پلن‌های اشتراک'


class SubscriptionStatus(models.TextChoices):
    NONE = 'ندارد', 'ندارد'
    ACTIVE = 'فعال', 'فعال'
    EXPIRED = 'منقضی', 'منقضی'


class Subscription(models.Model):

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
        null=True,
        db_index=True
    )

    ref_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True
    )

    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.NONE
    )

    def __str__(self):
        return f'{self.user.username} - {self.status}'

    @property
    def is_active(self):
        return self.status == SubscriptionStatus.ACTIVE

    def update_status(self):

        now = timezone.now()

        if self.start_date and self.end_date:

            if self.start_date <= now <= self.end_date:
                self.status = SubscriptionStatus.ACTIVE

            elif now > self.end_date:
                self.status = SubscriptionStatus.EXPIRED

            else:
                self.status = SubscriptionStatus.NONE

        else:
            self.status = SubscriptionStatus.NONE

    def save(self, *args, **kwargs):
        self.update_status()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'اشتراک'
        verbose_name_plural = 'اشتراک‌ها'