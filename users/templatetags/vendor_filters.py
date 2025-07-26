from django import template
from vendor.models import Vendor  # Import the Vendor model

register = template.Library()

@register.filter
def get_category_display(vendor):
    # Access the CATEGORY_CHOICES from the Vendor model
    category_choices = dict(Vendor.CATEGORY_CHOICES)
    return category_choices.get(vendor.category, vendor.category.title())