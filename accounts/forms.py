from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import transaction

from core.forms import BootstrapMixin

from .models import CustomerProfile, User


class NewAccountForm(BootstrapMixin, forms.Form):
    name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        data = super().clean()
        password1, password2 = data.get("password1"), data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two passwords do not match.")
        elif password1:
            try:
                password_validation.validate_password(password1)
            except ValidationError as error:
                self.add_error("password1", error)
        return data


class SignupForm(NewAccountForm):
    company = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=30, required=False)

    field_order = ["name", "company", "phone", "email", "password1", "password2"]

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(data["email"], data["name"], data["password1"])
        CustomerProfile.objects.create(
            user=user, company=data["company"], phone=data["phone"]
        )
        return user


class StaffCreateForm(NewAccountForm):
    def save(self):
        data = self.cleaned_data
        return User.objects.create_user(
            data["email"], data["name"], data["password1"], role=User.Role.STAFF
        )


class LoginForm(BootstrapMixin, AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()
