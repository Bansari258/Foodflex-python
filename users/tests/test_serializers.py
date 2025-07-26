from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)

class UserSignupSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'This email is already registered.'})
        return data

    def create(self, validated_data):
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
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        logger.info(f"Validating login for email: {email}")

        # Check if the user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.error(f"User with email {email} does not exist")
            raise serializers.ValidationError({'non_field_errors': ['Invalid email or password.']})

        logger.info(f"User found: {user.username}, is_active: {user.is_active}")

        # Check if the user is inactive
        if not user.is_active:
            logger.info(f"User {email} is inactive")
            raise serializers.ValidationError({'non_field_errors': ['This account is disabled.']})

        # Manually verify the password
        if not user.check_password(password):
            logger.error(f"Password verification failed for user {email}")
            raise serializers.ValidationError({'non_field_errors': ['Invalid email or password.']})

        logger.info(f"User {email} authenticated successfully")

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['user'] = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        return data