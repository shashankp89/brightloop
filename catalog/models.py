import calendar
from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Tax(models.Model):
    name = models.CharField(max_length=80, unique=True)
    percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "taxes"

    def __str__(self):
        return f"{self.name} ({self.percent:.2f}%)"


class Product(models.Model):
    class Type(models.TextChoices):
        SERVICE = "service", "Service"
        SOFTWARE = "software", "Software"
        ADDON = "addon", "Add-on"
        PHYSICAL = "physical", "Physical"

    name = models.CharField(max_length=150)
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.SERVICE)
    sales_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    tax = models.ForeignKey(
        Tax, null=True, blank=True, on_delete=models.PROTECT, related_name="products"
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    attribute = models.CharField(max_length=80)
    value = models.CharField(max_length=80)
    extra_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["attribute", "value"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "attribute", "value"], name="unique_variant_per_product"
            )
        ]

    def __str__(self):
        return f"{self.attribute}: {self.value}"

    @property
    def price(self):
        return self.product.sales_price + self.extra_price


class Plan(models.Model):
    class Period(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    name = models.CharField(max_length=120)
    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    billing_period = models.CharField(
        max_length=10, choices=Period.choices, default=Period.MONTHLY
    )
    min_quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    available_from = models.DateField(default=timezone.localdate)
    available_to = models.DateField(null=True, blank=True)
    auto_close = models.BooleanField(
        default=False, help_text="Close subscriptions automatically when they expire."
    )
    closable = models.BooleanField(
        default=False, help_text="Allow subscriptions to be closed before they expire."
    )
    pausable = models.BooleanField(
        default=False, help_text="Allow subscriptions to be paused and resumed."
    )
    renewable = models.BooleanField(
        default=False, help_text="Allow subscriptions to be renewed."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def is_available(self, on=None):
        on = on or timezone.localdate()
        if not self.is_active or on < self.available_from:
            return False
        return self.available_to is None or on <= self.available_to

    @property
    def availability(self):
        today = timezone.localdate()
        if not self.is_active:
            return "Inactive"
        if today < self.available_from:
            return "Upcoming"
        if self.available_to and today > self.available_to:
            return "Ended"
        return "Available"

    def add_periods(self, start, count=1):
        """Date that is `count` billing periods after `start`."""
        if self.billing_period == self.Period.DAILY:
            return start + timedelta(days=count)
        if self.billing_period == self.Period.WEEKLY:
            return start + timedelta(weeks=count)
        months = count if self.billing_period == self.Period.MONTHLY else 12 * count
        years, month_index = divmod(start.month - 1 + months, 12)
        year, month = start.year + years, month_index + 1
        day = min(start.day, calendar.monthrange(year, month)[1])
        return start.replace(year=year, month=month, day=day)
