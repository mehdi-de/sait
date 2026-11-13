
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        label='ایمیل',
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'ایمیل خود را وارد کنید',
                'autocomplete': 'email',
            }
        )
    )

    class Meta:
        model = User

        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                'این ایمیل قبلاً ثبت شده است.'
            )

        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip().lower()

        if not username:
            raise forms.ValidationError(
                'لطفاً نام کاربری را وارد کنید.'
            )

        if User.objects.filter(
            username__iexact=username
        ).exists():
            raise forms.ValidationError(
                'این نام کاربری قبلاً ثبت شده است.'
            )

        return username

    def save(self, commit=True):
        user = super().save(commit=False)

        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            self.save_m2m()

        return user
