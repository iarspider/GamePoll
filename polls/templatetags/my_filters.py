from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@stringfilter
def is_number(value):
    try:
        int(value)
    except ValueError:
        return False
    else:
        return True


register.filter("is_number", is_number)
