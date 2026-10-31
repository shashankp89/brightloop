from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import CustomerProfile, User
from .validators import StrongPasswordValidator

GOOD_PASSWORD = "Sunrise#2026"


class PasswordRuleTests(TestCase):
    def test_accepts_strong_password(self):
        StrongPasswordValidator().validate(GOOD_PASSWORD)

    def test_rejects_weak_passwords(self):
        for weak in ["Short#1a", "alllowercase#1", "ALLUPPERCASE#1", "NoSpecialChar12"]:
            with self.subTest(password=weak):
                with self.assertRaises(ValidationError):
                    StrongPasswordValidator().validate(weak)

    def test_exactly_eight_characters_is_too_short(self):
        with self.assertRaises(ValidationError):
            StrongPasswordValidator().validate("Abcdef#1")


class SignupTests(TestCase):
    def signup(self, **overrides):
        data = {
            "name": "Asha Rao",
            "company": "Rao Stores",
            "phone": "",
            "email": "asha@example.com",
            "password1": GOOD_PASSWORD,
            "password2": GOOD_PASSWORD,
        }
        data.update(overrides)
        return self.client.post(reverse("accounts:signup"), data)

    def test_creates_customer_with_profile_and_signs_in(self):
        response = self.signup()
        self.assertRedirects(response, reverse("core:home"))
        user = User.objects.get(email="asha@example.com")
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertEqual(user.profile.company, "Rao Stores")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_email_is_unique_ignoring_case(self):
        self.signup()
        self.client.logout()
        response = self.signup(email="ASHA@Example.com")
        self.assertContains(response, "already exists")
        self.assertEqual(User.objects.count(), 1)

    def test_weak_password_is_rejected_with_message(self):
        response = self.signup(password1="weakpass", password2="weakpass")
        self.assertContains(response, "Password must")
        self.assertFalse(User.objects.exists())

    def test_mismatched_passwords(self):
        response = self.signup(password2="Different#2026")
        self.assertContains(response, "do not match")
        self.assertFalse(CustomerProfile.objects.exists())

    def test_invalid_email_shows_feedback(self):
        response = self.signup(email="not-an-email")
        self.assertContains(response, "Enter a valid email address")


class LoginTests(TestCase):
    def setUp(self):
        User.objects.create_user("mira@example.com", "Mira", GOOD_PASSWORD)

    def test_login_ignores_email_case(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "Mira@Example.com", "password": GOOD_PASSWORD},
        )
        self.assertRedirects(response, reverse("core:home"))

    def test_wrong_password(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "mira@example.com", "password": "nope"},
        )
        self.assertContains(response, "correct email and password")

    def test_home_requires_login(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])


class PasswordResetTests(TestCase):
    def test_reset_link_goes_to_registered_email(self):
        User.objects.create_user("mira@example.com", "Mira", GOOD_PASSWORD)
        self.client.post(reverse("accounts:password_reset"), {"email": "mira@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["mira@example.com"])
        self.assertIn("/accounts/reset/", mail.outbox[0].body)

    def test_unknown_email_sends_nothing(self):
        self.client.post(reverse("accounts:password_reset"), {"email": "ghost@example.com"})
        self.assertEqual(len(mail.outbox), 0)


class StaffAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            "admin@example.com", "Admin", GOOD_PASSWORD, role=User.Role.ADMIN
        )
        self.staff = User.objects.create_user(
            "staff@example.com", "Staff", GOOD_PASSWORD, role=User.Role.STAFF
        )
        self.customer = User.objects.create_user("c@example.com", "Cust", GOOD_PASSWORD)
        self.url = reverse("accounts:staff_create")

    def test_admin_can_add_staff(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url,
            {
                "name": "New Hire",
                "email": "hire@example.com",
                "password1": GOOD_PASSWORD,
                "password2": GOOD_PASSWORD,
            },
        )
        self.assertRedirects(response, reverse("accounts:staff_list"))
        self.assertEqual(User.objects.get(email="hire@example.com").role, User.Role.STAFF)

    def test_staff_and_customers_cannot_add_staff(self):
        for user in (self.staff, self.customer):
            with self.subTest(role=user.role):
                self.client.force_login(user)
                self.assertEqual(self.client.get(self.url).status_code, 403)
                self.assertEqual(self.client.post(self.url, {}).status_code, 403)

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])
