from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("taxes/", views.TaxList.as_view(), name="tax_list"),
    path("taxes/new/", views.TaxCreate.as_view(), name="tax_create"),
    path("taxes/<int:pk>/edit/", views.TaxUpdate.as_view(), name="tax_update"),
    path("products/", views.ProductList.as_view(), name="product_list"),
    path("products/new/", views.ProductCreate.as_view(), name="product_create"),
    path("products/<int:pk>/", views.ProductDetail.as_view(), name="product_detail"),
    path("products/<int:pk>/edit/", views.ProductUpdate.as_view(), name="product_update"),
    path(
        "products/<int:pk>/variants/new/",
        views.VariantCreate.as_view(),
        name="product_variant_create",
    ),
    path(
        "variants/<int:pk>/edit/",
        views.VariantUpdate.as_view(),
        name="product_variant_update",
    ),
    path("variants/<int:pk>/delete/", views.variant_delete, name="product_variant_delete"),
    path("plans/", views.PlanList.as_view(), name="plan_list"),
    path("plans/new/", views.PlanCreate.as_view(), name="plan_create"),
    path("plans/<int:pk>/edit/", views.PlanUpdate.as_view(), name="plan_update"),
]
