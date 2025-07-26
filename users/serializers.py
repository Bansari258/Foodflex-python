# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import re
import logging

logger = logging.getLogger(__name__)

class UserSignupSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(max_length=30, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password']

    def validate(self, data):
        logger.info("Validating user signup data: %s", data)
        password = data.get('password')
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
            raise serializers.ValidationError({
                "password": "Password must be at least 8 characters long, with 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character (@$!%*?&)."
            })
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})
        if not data['first_name']:
            raise serializers.ValidationError({"first_name": "First name is required."})
        if not data['last_name']:
            raise serializers.ValidationError({"last_name": "Last name is required."})
        return data

    def create(self, validated_data):
        logger.info("Creating user with data: %s", validated_data)
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        logger.info("Validating user login data: %s", dict(data))
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise serializers.ValidationError("Please provide both email and password.")
        user = authenticate(username=email, password=password)
        if user:
            if not user.is_active:
                raise serializers.ValidationError("This account is disabled.")
            refresh = RefreshToken.for_user(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user,  
                'user_details': {  
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }
        else:
            raise serializers.ValidationError("Invalid email or password.")