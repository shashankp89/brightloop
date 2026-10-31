from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .forms import PlanForm, VariantForm
from .models import Plan, Product, ProductVariant, Tax

PASSWORD = "Sunrise#2026"


def make_user(role, email=None):
    return User.objects.create_user(email or f"{role}@example.com", role.title(), PASSWORD, role=role)


class VariantPriceTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Odoo ERP", sales_price=Decimal("1000"))

    def test_brand_variant_adds_to_price(self):
        variant = ProductVariant.objects.create(
            product=self.product, attribute="Brand", value="Odoo", extra_price=Decimal("560")
        )
        self.assertEqual(variant.price, Decimal("1560"))

    def test_duplicate_variant_is_rejected(self):
        ProductVariant.objects.create(product=self.product, attribute="Brand", value="Odoo")
        form = VariantForm(
            {"attribute": "brand", "value": "ODOO", "extra_price": "0"},
            instance=ProductVariant(product=self.product),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("value", form.errors)

    def test_variant_cannot_push_price_below_zero(self):
        form = VariantForm(
            {"attribute": "Tier", "value": "Free", "extra_price": "-1500"},
            instance=ProductVariant(product=self.product),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("extra_price", form.errors)


class PlanTests(TestCase):
    def plan(self, period, **extra):
        return Plan(name="P", price=10, billing_period=period, **extra)

    def test_monthly_periods_keep_the_original_day(self):
        plan = self.plan(Plan.Period.MONTHLY)
        self.assertEqual(plan.add_periods(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(plan.add_periods(date(2026, 1, 31), 2), date(2026, 3, 31))
        self.assertEqual(plan.add_periods(date(2026, 11, 15), 3), date(2027, 2, 15))

    def test_yearly_period_from_leap_day(self):
        plan = self.plan(Plan.Period.YEARLY)
        self.assertEqual(plan.add_periods(date(2024, 2, 29), 1), date(2025, 2, 28))

    def test_daily_and_weekly_periods(self):
        start = date(2026, 3, 1)
        self.assertEqual(self.plan(Plan.Period.DAILY).add_periods(start, 3), date(2026, 3, 4))
        self.assertEqual(self.plan(Plan.Period.WEEKLY).add_periods(start, 2), date(2026, 3, 15))

    def test_availability_window(self):
        today = timezone.localdate()
        plan = self.plan(
            Plan.Period.MONTHLY,
            available_from=today - timedelta(days=5),
            available_to=today + timedelta(days=5),
        )
        self.assertTrue(plan.is_available())
        self.assertFalse(plan.is_available(today - timedelta(days=6)))
        self.assertFalse(plan.is_available(today + timedelta(days=6)))
        plan.available_to = None
        self.assertTrue(plan.is_available(today + timedelta(days=400)))

    def test_inactive_plan_is_never_available(self):
        plan = self.plan(Plan.Period.MONTHLY, available_from=date(2020, 1, 1), is_active=False)
        self.assertFalse(plan.is_available())

    def test_end_date_before_start_is_rejected(self):
        form = PlanForm(
            {
                "name": "Gold",
                "price": "99",
                "billing_period": "monthly",
                "min_quantity": "1",
                "available_from": "2026-06-01",
                "available_to": "2026-05-01",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("available_to", form.errors)

    def test_minimum_quantity_must_be_positive(self):
        form = PlanForm(
            {
                "name": "Gold",
                "price": "99",
                "billing_period": "monthly",
                "min_quantity": "0",
                "available_from": "2026-06-01",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("min_quantity", form.errors)


class CatalogAccessTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin")
        self.staff = make_user("staff")
        self.customer = make_user("customer")
        self.product = Product.objects.create(name="Odoo ERP", sales_price=100)

    def test_team_can_read_catalog(self):
        for user in (self.admin, self.staff):
            self.client.force_login(user)
            for name in ("product_list", "plan_list", "tax_list"):
                with self.subTest(user=user.role, page=name):
                    self.assertEqual(self.client.get(reverse(f"catalog:{name}")).status_code, 200)

    def test_only_admin_can_write(self):
        urls = [
            reverse("catalog:product_create"),
            reverse("catalog:plan_create"),
            reverse("catalog:tax_create"),
            reverse("catalog:product_variant_create", args=[self.product.pk]),
        ]
        self.client.force_login(self.staff)
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        for url in urls:
            with self.subTest(url=url, user="admin"):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_customer_is_blocked_from_catalog(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("catalog:product_list")).status_code, 403)

    def test_admin_creates_plan_with_flags(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalog:plan_create"),
            {
                "name": "Pro Monthly",
                "price": "499.00",
                "billing_period": "monthly",
                "min_quantity": "2",
                "available_from": "2026-01-01",
                "pausable": "on",
                "renewable": "on",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("catalog:plan_list"))
        plan = Plan.objects.get(name="Pro Monthly")
        self.assertTrue(plan.pausable and plan.renewable)
        self.assertFalse(plan.auto_close or plan.closable)

    def test_variant_delete_needs_post(self):
        variant = ProductVariant.objects.create(product=self.product, attribute="Brand", value="Odoo")
        self.client.force_login(self.admin)
        url = reverse("catalog:product_variant_delete", args=[variant.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.assertFalse(ProductVariant.objects.filter(pk=variant.pk).exists())

    def test_product_search(self):
        Product.objects.create(name="Backup add-on", sales_price=5)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("catalog:product_list"), {"q": "backup"})
        self.assertContains(response, "Backup add-on")
        self.assertNotContains(response, "Odoo ERP")

    def test_tax_str_and_product_tax_choices_hide_inactive(self):
        active = Tax.objects.create(name="GST", percent=Decimal("18"))
        Tax.objects.create(name="Old", percent=Decimal("5"), is_active=False)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("catalog:product_create"))
        self.assertContains(response, str(active))
        self.assertNotContains(response, "Old (")
