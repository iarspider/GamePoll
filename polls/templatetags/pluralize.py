from django import template
from pytils import numeral

register = template.Library()


@register.filter
def ru_plural(value, variants):
    variants = variants.split(",")
    value = abs(int(value))

    result = numeral.get_plural(value, variants)

    return result
