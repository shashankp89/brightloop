from django import forms
from django.db.models import Q

from core.forms import BootstrapMixin, DateInput

from .models import Plan, Product, ProductVariant, Tax


class TaxForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Tax
        fields = ["name", "percent", "is_active"]


class ProductForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "type", "sales_price", "cost_price", "tax", "notes", "is_active"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        keep_current = Q(pk=self.instance.tax_id) if self.instance.tax_id else Q()
        self.fields["tax"].queryset = Tax.objects.filter(Q(is_active=True) | keep_current)
        self.fields["tax"].empty_label = "No tax"


class VariantForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["attribute", "value", "extra_price"]
        help_texts = {
            "attribute": "What the variant varies by, for example Brand.",
            "extra_price": "Added to the product's sales price.",
        }

    def clean(self):
        data = super().clean()
        product = self.instance.product
        attribute, value = data.get("attribute"), data.get("value")
        extra = data.get("extra_price")
        if attribute and value:
            clash = ProductVariant.objects.filter(
                product=product, attribute__iexact=attribute, value__iexact=value
            ).exclude(pk=self.instance.pk)
            if clash.exists():
                self.add_error("value", "This product already has that variant.")
        if extra is not None and product.sales_price + extra < 0:
            self.add_error("extra_price", "The variant price can't be below zero.")
        return data


class PlanForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Plan
        fields = [
            "name",
            "price",
            "billing_period",
            "min_quantity",
            "available_from",
            "available_to",
            "auto_close",
            "closable",
            "pausable",
            "renewable",
            "is_active",
        ]
        widgets = {"available_from": DateInput(), "available_to": DateInput()}
        help_texts = {"available_to": "Leave empty if the plan has no end date."}

    def clean(self):
        data = super().clean()
        start, end = data.get("available_from"), data.get("available_to")
        if start and end and end < start:
            self.add_error("available_to", "The end date can't be before the start date.")
        return data
