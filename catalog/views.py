from functools import cached_property

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, ProtectedError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.models import User
from core.permissions import AdminRequiredMixin, TeamRequiredMixin, role_required

from .forms import PlanForm, ProductForm, TaxForm, VariantForm
from .models import Plan, Product, ProductVariant, Tax

FORM_TEMPLATE = "core/form_page.html"


class CatalogList(TeamRequiredMixin, ListView):
    paginate_by = settings.PAGE_SIZE


class TaxList(CatalogList):
    model = Tax
    template_name = "catalog/tax_list.html"


class TaxCreate(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Tax
    form_class = TaxForm
    template_name = FORM_TEMPLATE
    success_url = reverse_lazy("catalog:tax_list")
    success_message = "Tax saved."
    extra_context = {"title": "New tax", "cancel_url": success_url}


class TaxUpdate(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Tax
    form_class = TaxForm
    template_name = FORM_TEMPLATE
    success_url = reverse_lazy("catalog:tax_list")
    success_message = "Tax updated."
    extra_context = {"title": "Edit tax", "cancel_url": success_url}


class ProductList(CatalogList):
    model = Product
    template_name = "catalog/product_list.html"

    def get_queryset(self):
        products = (
            Product.objects.select_related("tax")
            .annotate(variant_count=Count("variants"))
            .order_by("name")
        )
        query = self.request.GET.get("q", "").strip()
        return products.filter(name__icontains=query) if query else products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class ProductDetail(TeamRequiredMixin, DetailView):
    queryset = Product.objects.select_related("tax").prefetch_related("variants")
    template_name = "catalog/product_detail.html"


class ProductCreate(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = FORM_TEMPLATE
    success_message = "Product created."
    extra_context = {"title": "New product", "cancel_url": reverse_lazy("catalog:product_list")}

    def get_success_url(self):
        return reverse("catalog:product_detail", args=[self.object.pk])


class ProductUpdate(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = FORM_TEMPLATE
    success_message = "Product updated."
    extra_context = {"title": "Edit product"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()
        return context

    def get_success_url(self):
        return reverse("catalog:product_detail", args=[self.object.pk])


class VariantCreate(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = VariantForm
    template_name = FORM_TEMPLATE
    success_message = "Variant added."

    @cached_property
    def product(self):
        return get_object_or_404(Product, pk=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = ProductVariant(product=self.product)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"New variant for {self.product.name}"
        context["cancel_url"] = self.get_success_url()
        return context

    def get_success_url(self):
        return reverse("catalog:product_detail", args=[self.product.pk])


class VariantUpdate(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    queryset = ProductVariant.objects.select_related("product")
    form_class = VariantForm
    template_name = FORM_TEMPLATE
    success_message = "Variant updated."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit variant of {self.object.product.name}"
        context["cancel_url"] = self.get_success_url()
        return context

    def get_success_url(self):
        return reverse("catalog:product_detail", args=[self.object.product_id])


@role_required(User.Role.ADMIN)
@require_POST
def variant_delete(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    product_id = variant.product_id
    try:
        variant.delete()
        messages.success(request, "Variant removed.")
    except ProtectedError:
        messages.error(request, "That variant is used on a subscription and can't be removed.")
    return redirect("catalog:product_detail", pk=product_id)


class PlanList(CatalogList):
    model = Plan
    template_name = "catalog/plan_list.html"


class PlanCreate(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Plan
    form_class = PlanForm
    template_name = FORM_TEMPLATE
    success_url = reverse_lazy("catalog:plan_list")
    success_message = "Plan created."
    extra_context = {"title": "New plan", "cancel_url": success_url}


class PlanUpdate(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Plan
    form_class = PlanForm
    template_name = FORM_TEMPLATE
    success_url = reverse_lazy("catalog:plan_list")
    success_message = "Plan updated."
    extra_context = {"title": "Edit plan", "cancel_url": success_url}
