from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Vendor, MenuItem
import logging

logger = logging.getLogger(__name__)

class VendorSignupSerializer(serializers.ModelSerializer):
    vendor_email = serializers.EmailField(required=True)
    password_register = serializers.CharField(write_only=True, required=True)
    confirm_password_register = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Vendor
        fields = [
            'vendor_email', 'password_register', 'confirm_password_register', 
            'fssai_number', 'fssai_document', 'gst_number', 'gst_document',
            'shop_establishment_number', 'shop_establishment_document',
            'health_trade_license_number', 'health_trade_license_document',
            'company_incorporation_number', 'company_incorporation_document',
            'bank_account_number', 'bank_statement', 'partnership_deed', 'fire_safety_certificate',
            'full_name', 'owner_email', 'owner_phone'
        ]
        extra_kwargs = {
            'fssai_number': {'required': False},
            'fssai_document': {'required': False},
            'gst_number': {'required': False},
            'gst_document': {'required': False},
            'shop_establishment_number': {'required': False},
            'shop_establishment_document': {'required': False},
            'health_trade_license_number': {'required': False},
            'health_trade_license_document': {'required': False},
            'company_incorporation_number': {'required': False},
            'company_incorporation_document': {'required': False},
            'bank_account_number': {'required': False},
            'bank_statement': {'required': False},
            'partnership_deed': {'required': False},
            'fire_safety_certificate': {'required': False},
            'full_name': {'required': False},
            'owner_email': {'required': False},
            'owner_phone': {'required': False},
        }

    def validate(self, data):
        logger.info("Validating signup data: %s", data)
        if data['password_register'] != data['confirm_password_register']:
            raise serializers.ValidationError({'confirm_password_register': 'Passwords do not match.'})
        if User.objects.filter(email=data['vendor_email']).exists():
            raise serializers.ValidationError({'vendor_email': 'This email is already registered.'})
       
        return data

    def create(self, validated_data):
        logger.info("Creating vendor with data: %s", validated_data)
        user_data = {'email': validated_data.pop('vendor_email')}
        password = validated_data.pop('password_register')
        validated_data.pop('confirm_password_register')
        user = User.objects.create_user(
            username=user_data['email'],
            email=user_data['email'],
            password=password
        )
        vendor = Vendor.objects.create(user=user, **validated_data)
        return vendor


class VendorProfileSetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'restaurant_name', 'shop_no', 'floor', 'area', 'city', 'landmark', 'restaurant_phone',
            'restaurant_email', 'profile_image', 'description', 'takeaway', 'delivery','category',
            'open_time', 'close_time'
        ]
        extra_kwargs = {
            'profile_image': {'required': False},
            'description': {'required': False},
            'category': {'required': True},
            'open_time': {'required': False},
            'close_time': {'required': False},
        }

    def to_internal_value(self, data):
        mutable_data = data.copy()  # Create a mutable copy
        return super().to_internal_value(mutable_data)
    
    def validate(self, data):
        logger.info("Validating profile setup data: %s", data)
        if not data.get('area'):
            raise serializers.ValidationError({'area': 'Area is required.'})
        if not data.get('city'):
            raise serializers.ValidationError({'city': 'City is required.'})
        if not data.get('restaurant_name'):
            raise serializers.ValidationError({'restaurant_name': 'Restaurant name is required.'})
        if not data.get('restaurant_phone'):
            raise serializers.ValidationError({'restaurant_phone': 'Phone number is required.'})
        if not data.get('restaurant_email'):
            raise serializers.ValidationError({'restaurant_email': 'Email is required.'})
        if not data.get('profile_image'):
            raise serializers.ValidationError({'profile_image': 'Profile image is required.'})
        if not data.get('open_time'):
            raise serializers.ValidationError({'open_time': 'Open time is required.'})
        if not data.get('close_time'):
            raise serializers.ValidationError({'close_time': 'Close time is required.'})
        if not data.get('category'):
            raise serializers.ValidationError({'category': 'Category is required.'})
        return data
class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price', 'description', 'image', 'is_available', 'category']

    def validate(self, data):
        if not data.get('name') or not data.get('price'):
            raise serializers.ValidationError({'name': 'Name and price are required.'})
        return data

class VendorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        logger.info("Validating login data: %s", dict(data))
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise serializers.ValidationError("Please provide both email and password.")
        
        user = authenticate(username=email, password=password)
        if not user or not user.is_active or not Vendor.objects.filter(user=user).exists():
            raise serializers.ValidationError("Invalid credentials or not a vendor.")
        
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'vendor': {
                'id': user.id,
                'email': user.email,
                'restaurant_name': user.vendor_profile.restaurant_name
            }
        }


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price', 'description', 'image', 'is_available']
        extra_kwargs = {
            'image': {'required': False},
            'description': {'required': False},
        }

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def create(self, validated_data):
        vendor = self.context.get('vendor')
        return MenuItem.objects.create(vendor=vendor, **validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.price = validated_data.get('price', instance.price)
        instance.description = validated_data.get('description', instance.description)
        instance.image = validated_data.get('image', instance.image)
        instance.is_available = validated_data.get('is_available', instance.is_available)
        instance.save()
        return instance