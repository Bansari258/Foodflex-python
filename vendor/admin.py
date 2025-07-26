from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from vendor.models import Vendor, MenuItem, Order, Review
from django.db.models import Sum, Avg, Count

# Inline for Vendor to show in User admin
class VendorInline(admin.StackedInline):
    model = Vendor
    can_delete = False
    verbose_name_plural = 'Vendor Profile'
    fields = ('restaurant_name', 'category', 'restaurant_phone', 'restaurant_email', 'full_name', 'owner_email', 'owner_phone')

# Customize the User admin to include Vendor inline
class UserAdmin(BaseUserAdmin):
    inlines = (VendorInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

# Register the customized UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Admin for Vendor model
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'restaurant_name',
        'category',
        'restaurant_phone',
        'restaurant_email',
        'full_name',
        'total_orders',
        'total_earnings',
        'average_rating',
        'created_at',  # Added back
    )
    list_filter = ('category', 'takeaway', 'delivery', 'created_at')  # Added back
    search_fields = ('user__username', 'restaurant_name', 'restaurant_email', 'full_name', 'owner_email', 'owner_phone')
    date_hierarchy = 'created_at'  # Added back
    ordering = ('-created_at',)  # Added back

    # Fieldsets to organize the form for adding/editing a vendor
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'restaurant_name', 'category', 'profile_image', 'description', 'rating', 'discount')
        }),
        ('Contact Information', {
            'fields': ('restaurant_phone', 'restaurant_email')
        }),
        ('Address', {
            'fields': ('shop_no', 'floor', 'area', 'city', 'landmark')
        }),
        ('Operating Details', {
            'fields': ('takeaway', 'delivery', 'open_time', 'close_time')
        }),
        ('Owner Information', {
            'fields': ('full_name', 'owner_email', 'owner_phone')
        }),
        ('Documentation', {
            'fields': (
                'fssai_number', 'fssai_document',
                'gst_number', 'gst_document',
                'shop_establishment_number', 'shop_establishment_document',
                'health_trade_license_number', 'health_trade_license_document',
                'company_incorporation_number', 'company_incorporation_document',
                'bank_account_number', 'bank_statement',
                'partnership_deed', 'fire_safety_certificate'
            )
        }),
    )

    # Custom methods to display vendor activities
    def total_orders(self, obj):
        return obj.orders.count()
    total_orders.short_description = 'Total Orders'

    def total_earnings(self, obj):
        earnings = obj.orders.aggregate(total=Sum('total_amount'))['total'] or 0.0
        return f"₹{earnings:.2f}"
    total_earnings.short_description = 'Total Earnings'

    def average_rating(self, obj):
        return obj.average_rating
    average_rating.short_description = 'Average Rating (1-10)'

# Admin for MenuItem model
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'category', 'price', 'is_available', 'created_at')
    list_filter = ('vendor', 'category', 'is_available', 'created_at')
    search_fields = ('name', 'vendor__restaurant_name', 'category')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

# Admin for Order model
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'user', 'total_amount', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'vendor')
    search_fields = ('vendor__restaurant_name', 'user__username', 'status')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def order_items_display(self, obj):
        items = obj.order_items.get('items', [])
        return ", ".join([f"{item['name']} (x{item['quantity']})" for item in items])
    order_items_display.short_description = 'Order Items'

