# vendor/models.py
from datetime import datetime, timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Vendor(models.Model):
    CATEGORY_CHOICES = [
        ('restaurant', 'Restaurant & Cafe'),
        ('cloud_kitchen', 'Cloud Kitchen'),
        ('tiffin', 'Tiffin Service  '),
        ('stall', 'Stall'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    restaurant_name = models.CharField(max_length=255, blank=True, null=True)
    shop_no = models.CharField(max_length=50, blank=True, null=True)
    floor = models.CharField(max_length=50, blank=True, null=True)
    area = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    restaurant_phone = models.CharField(max_length=15, blank=True, null=True)
    restaurant_email = models.EmailField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='vendor_profiles/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    takeaway = models.BooleanField(default=False, blank=True, null=True)
    delivery = models.BooleanField(default=False, blank=True, null=True)
    open_time = models.TimeField(blank=True, null=True)
    close_time = models.TimeField(blank=True, null=True)
    rating = models.FloatField(default=0.0, blank=True, null=True)  # For rating display
    discount = models.IntegerField(default=0, blank=True, null=True)  # Optional discount
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='restaurant')

    # Vendor documentation fields
    fssai_number = models.CharField(max_length=50, blank=True, null=True)
    fssai_document = models.FileField(upload_to='vendor/documents/', blank=True, null=True)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    gst_document = models.FileField(upload_to='vendor/documents/', blank=True, null=True)
    shop_establishment_number = models.CharField(max_length=50, blank=True, null=True)
    shop_establishment_document = models.FileField(upload_to='vendor/documents/', blank=True, null=True)
    health_trade_license_number = models.CharField(max_length=50, blank=True, null=True)
    health_trade_license_document = models.FileField(upload_to='vendor/documents/', blank=True, null=True)
    company_incorporation_number = models.CharField(max_length=50, blank=True, null=True)
    company_incorporation_document = models.FileField(upload_to='vendor/documents/', blank=True, null=True)
    bank_account_number = models.CharField(max_length=20, blank=True, null=True)
    bank_statement = models.FileField(upload_to='vendor/documents/', blank=True, null=True)
    partnership_deed = models.FileField(upload_to='vendor/documents/', blank=True, null=True)
    fire_safety_certificate = models.FileField(upload_to='vendor/documents/', blank=True, null=True)

    # Owner information
    full_name = models.CharField(max_length=100, blank=True, null=True)
    owner_email = models.EmailField(blank=True, null=True)
    owner_phone = models.CharField(max_length=15, blank=True, null=True)

    # Add created_at field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.restaurant_name} - {self.user.email}"

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            avg = sum(review.overall_rating for review in reviews) / reviews.count()
            return round(avg * 2, 1)  
        return 0.0

    class Meta:
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('starters', 'Starters'),
        ('main', 'Main Courses'),
        ('desserts', 'Desserts'),
        ('drinks', 'Drinks'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='main')

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = (
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='orders')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_address = models.TextField(default='134, ABC Street')
    user_city = models.CharField(max_length=100, default='City')
    user_postal_code = models.CharField(max_length=10, default='123456')
    order_items = models.JSONField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.vendor.restaurant_name}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='reviews')
    overall_rating = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        blank=True,
        null=True
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.vendor.restaurant_name}"

    class Meta:
        unique_together = ('user', 'vendor')