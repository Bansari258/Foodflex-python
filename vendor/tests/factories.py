import factory
from django.contrib.auth.models import User
from vendor.models import Vendor, MenuItem, Order, Review
from django.utils import timezone
from datetime import time

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"vendor{n}@example.com")
    username = factory.LazyAttribute(lambda obj: obj.email)
    password = factory.PostGenerationMethodCall('set_password', 'B@ns@ri258')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

class VendorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vendor

    user = factory.SubFactory(UserFactory)
    restaurant_name = factory.Faker('company')
    shop_no = "101"
    floor = "1st Floor"
    area = "Downtown"
    city = "Test City"
    landmark = "Near Central Park"
    restaurant_phone = "1234567890"
    restaurant_email = factory.LazyAttribute(lambda obj: obj.user.email)
    profile_image = factory.django.ImageField(filename='profile.jpg')
    description = factory.Faker('paragraph')
    takeaway = True
    delivery = True
    open_time = time(9, 0)  # 9:00 AM
    close_time = time(21, 0)  # 9:00 PM
    category = 'restaurant'
    fssai_number = "12345678901234"
    full_name = factory.Faker('name')
    owner_email = factory.LazyAttribute(lambda obj: f"owner_{obj.user.email}")
    owner_phone = "0987654321"

class MenuItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MenuItem

    vendor = factory.SubFactory(VendorFactory)
    name = factory.Faker('word')
    price = 10.99
    description = factory.Faker('sentence')
    image = factory.django.ImageField(filename='menu_item.jpg')
    is_available = True
    category = 'main'

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    vendor = factory.SubFactory(VendorFactory)
    user = factory.SubFactory(UserFactory)
    user_address = "123 Test Street"
    user_city = "Test City"
    user_postal_code = "12345"
    order_items = {"items": [{"name": "Test Item", "price": 10.99, "quantity": 1}]}
    total_amount = 10.99
    status = 'ongoing'
    created_at = factory.LazyFunction(timezone.now)

class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    user = factory.SubFactory(UserFactory)
    vendor = factory.SubFactory(VendorFactory)
    overall_rating = 4.5
    comment = factory.Faker('paragraph')