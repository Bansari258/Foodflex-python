# users/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.db.models import Avg
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse
import json
import logging
from vendor.models import Vendor, MenuItem, Order, Review
from .serializers import UserSignupSerializer, UserLoginSerializer
from .models import Profile

logger = logging.getLogger(__name__)

# Helper function to get tokens for a user
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# Add cart context helper function
def add_cart_context(request):
    vendor_id = request.session.get('vendor_id', 1)  # Default to 1 if not set
    order_dict = request.session.get('order', {})
    order_json = json.dumps(order_dict, cls=DjangoJSONEncoder)
    return {
        'vendor_id': vendor_id,
        'order_json': order_json,
    }

# Landing page (publicly accessible)
def landing(request):
    context = add_cart_context(request)
    return render(request, 'landing.html', context)

# User Signup Page (publicly accessible)
def signup(request):
    return render(request, 'users/signup.html')

# Help Page (publicly accessible)
def help(request):
    if request.method == 'POST':
        name = request.POST.get('name_contact')
        subject = request.POST.get('subject_contact')
        email = request.POST.get('email_contact')
        message = request.POST.get('message_contact')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            messages.success(request, 'Thank you! We’ll reach out to you soon.')
            return redirect('users:help')

    context = add_cart_context(request)
    return render(request, 'users/help.html', context)

# User Signup API
class UserSignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create the Profile object for the user
            Profile.objects.get_or_create(user=user)
            tokens = get_tokens_for_user(user)
            logger.info(f"User {user.email} signed up successfully.")
            return Response({
                'success': True,
                'message': 'User created successfully',
                'data': {
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    },
                    'tokens': tokens,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Signup failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# User Login API
class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            user = data['user']  # This is now the User object
            user_details = data['user_details']  # Dictionary for the response
            # Log the user in for session-based authentication
            login(request, user)
            logger.info(f"User {user.email} logged in successfully.")
            return Response({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'refresh': data['refresh'],
                    'access': data['access'],
                    'user': user_details  # Use the dictionary for the response
                },
                'redirect_url': reverse('users:home'),
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'message': 'Invalid email or password',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# User Session API
class UserSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_authenticated:
            logger.warning("Unauthenticated user attempted to access user session data.")
            return Response({
                'success': False,
                'detail': 'Authentication credentials were not provided.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user
        logger.info(f"User session data accessed for {user.email}.")
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_200_OK)

# User Logout API
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class UserLogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required.',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            # Log the user out of the session
            logout(request)
            logger.info(f"User {request.user.email} logged out successfully, refresh token blacklisted.")
            return Response({
                'success': True,
                'message': 'Logout successful.',
                'redirect_url': reverse('users:landing')
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error during logout.',
                'error': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

# User Home Page (protected by JWTMiddleware)
def home(request):
    top_vendors = Vendor.objects.all().order_by('-rating')[:5]
    category_choices = dict(Vendor.CATEGORY_CHOICES)
    top_vendors_with_display = []
    for vendor in top_vendors:
        vendor_data = {
            'vendor': vendor,
            'category_display': category_choices.get(vendor.category, vendor.category.title()),
            'takeaway': vendor.takeaway if vendor.takeaway is not None else False,
            'delivery': vendor.delivery if vendor.delivery is not None else False,
        }
        top_vendors_with_display.append(vendor_data)

    context = {
        'top_vendors': top_vendors_with_display,
        'user': request.user,
    }
    context.update(add_cart_context(request))
    return render(request, 'users/home.html', context)

# Browse Shops (protected by JWTMiddleware)
def browse_shops(request):
    vendors = Vendor.objects.all()

    query = request.GET.get('q', '')
    if query:
        vendors = vendors.filter(restaurant_name__icontains=query) | vendors.filter(area__icontains=query) | vendors.filter(city__icontains=query)

    vendors = vendors.annotate(avg_rating=Avg('reviews__overall_rating')).order_by('-avg_rating')

    paginator = Paginator(vendors, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = [
        {'name': 'Restaurant & Cafe', 'count': Vendor.objects.filter(category='restaurant').count()},
        {'name': 'Cloud Kitchen', 'count': Vendor.objects.filter(category='cloud_kitchen').count()},
        {'name': 'Tiffin Service', 'count': Vendor.objects.filter(category='tiffin').count()},
        {'name': 'Stall', 'count': Vendor.objects.filter(category='stall').count()},
    ]

    top_categories = [
        {'name': 'Pizza', 'image': '/static/img/cat_listing_1.jpg'},
        {'name': 'Sushi', 'image': '/static/img/cat_listing_2.jpg'},
        {'name': 'Dessert', 'image': '/static/img/cat_listing_3.jpg'},
        {'name': 'Hamburger', 'image': '/static/img/cat_listing_4.jpg'},
        {'name': 'Ice Cream', 'image': '/static/img/cat_listing_5.jpg'},
        {'name': 'Kebab', 'image': '/static/img/cat_listing_6.jpg'},
        {'name': 'Italian', 'image': '/static/img/cat_listing_7.jpg'},
        {'name': 'Chinese', 'image': '/static/img/cat_listing_8.jpg'},
    ]

    rating_counts = {
        '9': Vendor.objects.filter(reviews__overall_rating__gte=4.5).distinct().count(),
        '8': Vendor.objects.filter(reviews__overall_rating__gte=4.0).distinct().count(),
        '7': Vendor.objects.filter(reviews__overall_rating__gte=3.5).distinct().count(),
        '6': Vendor.objects.filter(reviews__overall_rating__gte=3.0).distinct().count(),
    }

    context = {
        'vendors': page_obj,
        'vendor_count': vendors.count(),
        'location': 'Convent Street 2983',
        'categories': categories,
        'top_categories': top_categories,
        'rating_counts': rating_counts,
    }
    context.update(add_cart_context(request))
    return render(request, 'users/browseshop.html', context)

# Vendor Detail Page (protected by JWTMiddleware)
def vendor_detail(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    reviews = Review.objects.filter(vendor=vendor).order_by('-created_at')
    score = vendor.average_rating
    score_on_5 = score / 2

    vendor.rating = score
    vendor.save()

    if request.method == 'POST':
        if Review.objects.filter(user=request.user, vendor=vendor).exists():
            messages.error(request, 'You have already reviewed this vendor.')
            return redirect('users:vendor_detail', vendor_id=vendor_id)

        try:
            overall_rating = float(request.POST.get('overall_rating'))
            if not (1 <= overall_rating <= 5):
                messages.error(request, 'Rating must be between 1 and 5.')
                return redirect('users:vendor_detail', vendor_id=vendor_id)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid rating value.')
            return redirect('users:vendor_detail', vendor_id=vendor_id)

        comment = request.POST.get('comment')

        Review.objects.create(
            user=request.user,
            vendor=vendor,
            overall_rating=overall_rating,
            comment=comment
        )
        messages.success(request, 'Your review has been submitted successfully.')
        return redirect('users:vendor_detail', vendor_id=vendor_id)

    menu_items = vendor.menu_items.all()
    menu_items_by_section = {}
    for item in menu_items:
        category = item.category or "General"
        if category not in menu_items_by_section:
            menu_items_by_section[category] = []
        menu_items_by_section[category].append(item)

    menu_items_json = json.dumps([{
        'id': item.id,
        'name': item.name,
        'price': float(item.price),
        'description': item.description,
        'image': item.image.url if item.image else None
    } for item in menu_items])

    context = {
        'vendor': vendor,
        'menu_items_by_section': menu_items_by_section,
        'menu_items_json': menu_items_json,
        'score': round(score, 1),
        'score_on_5': round(score_on_5, 1),
        'review_count': reviews.count(),
        'reviews': reviews,
        'vendor_id': vendor_id,
        'order_json': request.GET.get('order', '{}'),
    }
    return render(request, 'users/detail-restaurant.html', context)

# Leave Review (protected by JWTMiddleware)
def leave_review(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        if Review.objects.filter(user=request.user, vendor=vendor).exists():
            messages.error(request, 'You have already reviewed this vendor.')
            return redirect('users:vendor_detail', vendor_id=vendor_id)

        food_quality = int(request.POST.get('food_quality'))
        service = int(request.POST.get('service'))
        punctuality = int(request.POST.get('punctuality'))
        price = int(request.POST.get('price'))
        comment = request.POST.get('comment')

        if not all(1 <= rating <= 5 for rating in [food_quality, service, punctuality, price]):
            messages.error(request, 'Ratings must be between 1 and 5.')
            return redirect('users:vendor_detail', vendor_id=vendor_id)

        Review.objects.create(
            user=request.user,
            vendor=vendor,
            food_quality=food_quality,
            service=service,
            punctuality=punctuality,
            price=price,
            comment=comment
        )
        messages.success(request, 'Your review has been submitted successfully.')
        return redirect('users:vendor_detail', vendor_id=vendor_id)

    return redirect('users:vendor_detail', vendor_id=vendor_id)

# Order View (protected by JWTMiddleware)
def order_view(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)

    order_data = request.GET.get('order', '{}')
    order_dict = json.loads(order_data) if order_data else {}

    request.session['order'] = order_dict
    request.session['vendor_id'] = vendor_id

    menu_items = MenuItem.objects.filter(vendor=vendor, is_available=True).order_by('id')
    
    menu_items_list = [
        {
            'id': item.id,
            'name': item.name,
            'price': str(item.price),
            'description': item.description,
            'category': item.category,
        }
        for item in menu_items
    ]
    
    menu_items_json = json.dumps(menu_items_list, cls=DjangoJSONEncoder)

    context = {
        'vendor': vendor,
        'order': order_dict,
        'order_json': json.dumps(order_dict, cls=DjangoJSONEncoder),
        'menu_items_json': menu_items_json,
        'menu_items': menu_items_list,
        'current_date': timezone.now(),
        'current_time': timezone.now(),
    }
    context.update(add_cart_context(request))
    return render(request, 'users/order.html', context)

# Confirm View (protected by JWTMiddleware)
def confirm_view(request):
    order_items = request.session.get('order', {})
    vendor_id = request.session.get('vendor_id')

    if not vendor_id or not order_items:
        messages.error(request, "No order data found. Please place an order first.")
        return redirect('users:home')

    vendor = get_object_or_404(Vendor, id=vendor_id)

    initial_data = {
        'first_name': request.session.get('first_name', ''),
        'last_name': request.session.get('last_name', ''),
        'phone': request.session.get('phone', ''),
        'address': '',
        'city': '',
        'postal_code': '',
    }

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')
        payment_method = request.POST.get('payment_method')
        order_data = request.POST.get('order', '{}')

        if not all([first_name, last_name, phone, address, city, postal_code, vendor_id]):
            messages.error(request, "All fields are required.")
            return redirect('users:order', vendor_id=vendor_id)

        try:
            order_items = json.loads(order_data) if order_data else order_items
        except json.JSONDecodeError as e:
            messages.error(request, "Invalid order data. Please try again.")
            logger.error(f"JSONDecodeError: {e} - Order Data: {order_data}")
            return redirect('users:order', vendor_id=vendor_id)

        request.session['first_name'] = first_name
        request.session['last_name'] = last_name
        request.session['phone'] = phone
        request.session['email'] = request.POST.get('email', '')

        subtotal = sum(details['total'] for details in order_items.values())
        delivery_fee = 10.00 if subtotal > 0 and vendor.delivery else 0.00
        total_amount = subtotal + delivery_fee

        order = Order.objects.create(
            vendor=vendor,
            user=request.user,  # Associate the order with the authenticated user
            user_address=address,
            user_city=city,
            user_postal_code=postal_code,
            order_items=order_items,
            total_amount=total_amount,
            status='ongoing',
        )

        context = {
            'name': f"{first_name} {last_name}",
            'email': request.session.get('email', 'Not provided'),
            'phone': phone,
            'address': address,
            'city': city,
            'postal_code': postal_code,
            'payment_method': payment_method,
            'vendor': vendor,
            'order': order_items,
        }
        context.update(add_cart_context(request))
        request.session.pop('order', None)
        request.session.pop('vendor_id', None)
        return render(request, 'users/confirm.html', context)
    
    context = {
        'initial_data': initial_data,
        'vendor_id': vendor_id,
        'order': order_items,
        'order_json': json.dumps(order_items, cls=DjangoJSONEncoder),
    }
    context.update(add_cart_context(request))
    return render(request, 'users/order.html', context)

# My Orders View (protected by JWTMiddleware)
def my_orders(request):
    ongoing_orders = Order.objects.filter(user=request.user, status='ongoing').order_by('-created_at')
    past_orders = Order.objects.filter(user=request.user).exclude(status='ongoing').order_by('-created_at')

    context = {
        'ongoing_orders': ongoing_orders,
        'past_orders': past_orders,
        'current_time': timezone.now(),
    }
    context.update(add_cart_context(request))
    return render(request, 'users/order-details.html', context)

# Profile View (protected by JWTMiddleware)
from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    if not request.user.is_authenticated:
        logger.warning("Unauthenticated user attempted to access profile page.")
        return redirect('users:landing')

    # Get or create the profile for the user
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Handle both traditional POST and AJAX requests
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        phone = data.get('phone')

        # Server-side validation
        errors = {}
        if not first_name:
            errors['first_name'] = ['This field may not be blank.']
        if not last_name:
            errors['last_name'] = ['This field may not be blank.']
        if not email:
            errors['email'] = ['This field may not be blank.']
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors['email'] = ['Please enter a valid email address.']
            if email != request.user.email and User.objects.filter(email=email).exclude(id=request.user.id).exists():
                errors['email'] = ['This email is already in use.']
        if not phone:
            errors['phone'] = ['This field may not be blank.']

        if errors:
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'Profile update failed',
                    'errors': errors
                }, status=400)
            else:
                for field, error_list in errors.items():
                    for error in error_list:
                        messages.error(request, f"{field.capitalize()}: {error}")
                return redirect('users:profile')

        try:
            # Update the user object
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            if email != user.email:
                user.email = email
            user.save()

            # Update the profile object
            profile.phone = phone
            profile.save()

            logger.info(f"User {user.email} updated their profile successfully.")
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': 'Profile updated successfully!'
                }, status=200)
            else:
                messages.success(request, "Profile updated successfully.")
                return redirect('users:profile')
        except Exception as e:
            logger.error(f"Error updating profile for user {user.email}: {str(e)}", exc_info=True)
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'Error updating profile. Please try again.'
                }, status=500)
            else:
                messages.error(request, "Error updating profile. Please try again.")
                return redirect('users:profile')

    # For GET requests, pass the user and profile to the template
    context = {
        'user': request.user,
        'profile': profile
    }
    return render(request, 'users/profile.html', context)

# User Profile API (protected by JWT)
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Get or create the profile
        profile, created = Profile.objects.get_or_create(user=user)
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': profile.phone
            }
        }, status=status.HTTP_200_OK)