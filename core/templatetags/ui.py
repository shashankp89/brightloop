from decimal import Decimal

from django import template
from django.conf import settings

register = template.Library()


@register.filter
def money(value):
    if value in (None, ""):
        return ""
    return f"{settings.CURRENCY_SYMBOL}{Decimal(value):,.2f}"
