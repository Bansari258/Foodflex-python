from django import template

register = template.Library()

@register.filter
def dict_to_list(value):
    if isinstance(value, dict):
        return list(value.values())
    elif isinstance(value, list):
        return value  # If it's already a list, return it as-is
    return []

@register.filter
def dict_get(list, key):
    return next((item for item in list if item.get('id') == int(key)), None)    