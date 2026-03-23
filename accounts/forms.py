from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="ایمیل",
        help_text="ایمیل خود را وارد کنید.",
        error_messages={
            "required": "وارد کردن ایمیل الزامی است.",
            "invalid": "ایمیل وارد شده معتبر نیست."
        }
    )

    password1 = forms.CharField(
        label="رمز عبور",
        strip=False,
        widget=forms.PasswordInput,
        help_text="رمز عبور باید حداقل ۸ کاراکتر داشته باشد و با اطلاعات شخصی شما مشابه نباشد.",
        error_messages={
            "required": "وارد کردن رمز عبور الزامی است."
        }
    )

    password2 = forms.CharField(
        label="تایید رمز عبور",
        strip=False,
        widget=forms.PasswordInput,
        help_text="رمز عبور را دوباره وارد کنید.",
        error_messages={
            "required": "وارد کردن تایید رمز عبور الزامی است.",
            "password_mismatch": "رمز عبور با تایید آن مطابقت ندارد."
        }
    )

    username = forms.CharField(
        label="نام کاربری",
        help_text="فقط حروف، اعداد و @/./+/-/_ مجاز است.",
        error_messages={
            "required": "وارد کردن نام کاربری الزامی است.",
            "max_length": "نام کاربری نمی‌تواند بیشتر از ۱۵۰ کاراکتر باشد."
        }
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "نام کاربری",
            "email": "ایمیل",
            "password1": "رمز عبور",
            "password2": "تایید رمز عبور"
        }
        help_texts = {
            "username": "فقط حروف، اعداد و @/./+/-/_ مجاز است.",
        }
