# vendor/views.py
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from rest_framework import status
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth, TruncDay
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib import messages
from rest_framework_simplejwt.exceptions import TokenError
import logging
from users.views import add_cart_context
from .serializers import VendorSignupSerializer, VendorProfileSetupSerializer, MenuItemSerializer, VendorLoginSerializer
from .models import Vendor, MenuItem, Order
logger = logging.getLogger(__name__)

# Function: vendor_landing
def vendor_landing(request):
    return render(request, 'vendor/vendor_landing.html')

# Function: vendor_signup
def vendor_signup(request):
    return render(request, 'vendor/vendor_signup.html')

# Function: vendor_profile_setup
def vendor_profile_setup(request):
    if not request.user.is_authenticated:
         return redirect('vendor:vendor_signup')
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    context = {
        'days_of_week': days_of_week,
    }
    return render(request, 'vendor/vendor_profile_setup.html', context)

# Function: vendor_menu_setup
def vendor_menu_setup(request):
    if not request.user.is_authenticated:
        return redirect('vendor:vendor_signup')
    return render(request, 'vendor/vendor_menu_setup.html')

# Function: customers
def customers(request):
    if not request.user.is_authenticated:
        return redirect('vendor:vendor_signup')
    return render(request, 'vendor/customers.html')

# Function: vendor_profile
def vendor_profile(request):
    if not request.user.is_authenticated:
        return redirect('vendor:vendor_signup')
    return render(request, 'vendor/vendor_profile.html')

# Function: help
def help(request):
    return render(request, 'vendor/vendor_help.html')

# Function: vendor_logout
def vendor_logout(request):
    try:
        if 'refresh_token' in request.session:
            refresh_token = request.session.get('refresh_token')
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info("Refresh token blacklisted for user: %s", request.user)
            except TokenError as e:
                logger.warning("Failed to blacklist refresh token: %s", str(e))
            finally:
                del request.session['refresh_token']
        logout(request)
        logger.info("User logged out successfully: %s", request.user if request.user.is_authenticated else "Anonymous")
    except Exception as e:
        logger.error("Error during logout: %s", str(e), exc_info=True)
    return redirect('vendor:vendor_landing')

# Function: vendor_home
@login_required
def vendor_home(request):
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect('vendor:vendor_login')
    total_earnings = Order.objects.filter(vendor=vendor).aggregate(total=Sum('total_amount'))['total'] or 0.0
    new_orders = Order.objects.filter(vendor=vendor, status='ongoing').count()
    total_customers = Order.objects.filter(vendor=vendor).values('user').distinct().count()
    try:
        from .models import Review
        average_rating = Review.objects.filter(vendor=vendor).aggregate(avg_rating=Avg('overall_rating'))['avg_rating'] or 0.0
        average_rating = round(average_rating, 1)
    except ImportError:
        average_rating = 0.0
    recent_orders = Order.objects.filter(vendor=vendor).order_by('-created_at')[:5]
    try:
        from .models import OrderItem
        top_menu_items = OrderItem.objects.filter(
            order__vendor=vendor
        ).values(
            'menu_item__name',
            'menu_item__category',
            'menu_item__price'
        ).annotate(
            order_count=Count('id')
        ).order_by('-order_count')[:5]
    except ImportError:
        top_menu_items = MenuItem.objects.filter(vendor=vendor).order_by('-id')[:5].values(
            'name', 'category', 'price'
        )
        top_menu_items = [
            {
                'menu_item__name': item['name'],
                'menu_item__category': item['category'],
                'menu_item__price': item['price'],
                'order_count': 0
            } for item in top_menu_items
        ]
    today = timezone.now()
    six_months_ago = today - timedelta(days=180)
    monthly_earnings = Order.objects.filter(
        vendor=vendor,
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')
    chart_labels = []
    chart_data = []
    current_month = six_months_ago
    while current_month <= today:
        chart_labels.append(current_month.strftime('%b %Y'))
        earnings_for_month = next(
            (entry['total'] for entry in monthly_earnings if entry['month'].strftime('%Y-%m') == current_month.strftime('%Y-%m')),
            0.0
        )
        chart_data.append(float(earnings_for_month))
        current_month = (current_month + timedelta(days=31)).replace(day=1)
    context = {
        'total_earnings': total_earnings,
        'new_orders': new_orders,
        'total_customers': total_customers,
        'average_rating': average_rating,
        'recent_orders': recent_orders,
        'top_menu_items': top_menu_items,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'vendor/vendor_home.html', context)

# Class: VendorSignupAPIView
class VendorSignupAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        logger.info("Signup request received: %s", dict(request.data))
        try:
            serializer = VendorSignupSerializer(data=request.data)
            if serializer.is_valid():
                vendor = serializer.save()
                user = vendor.user
                login(request, user)
                refresh = RefreshToken.for_user(user)
                redirect_url = reverse('vendor:profile_setup')
                logger.info("User signed up: %s, Redirect URL: %s", user.email, redirect_url)
                return Response({
                    'success': True,
                    'message': 'Signup successful',
                    'redirect_url': redirect_url,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_200_OK)
            logger.warning("Validation failed: %s", serializer.errors)
            return Response({
                'success': False,
                'message': 'Signup failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Signup error: %s", str(e), exc_info=True)
            return Response({
                'success': False,
                'message': 'An internal error occurred',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Class: VendorProfileSetupAPIView
class VendorProfileSetupAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        logger.info("Fetching profile for user: %s, Token: %s", request.user, request.auth)
        try:
            vendor = get_object_or_404(Vendor, user=request.user)
            serializer = VendorProfileSetupSerializer(vendor)
            return Response({
                'success': True,
                'restaurant_name': serializer.data.get('restaurant_name', ''),
                'shop_no': serializer.data.get('shop_no', ''),
                'floor': serializer.data.get('floor', ''),
                'area': serializer.data.get('area', ''),
                'city': serializer.data.get('city', ''),
                'landmark': serializer.data.get('landmark', ''),
                'restaurant_phone': serializer.data.get('restaurant_phone', ''),
                'restaurant_email': serializer.data.get('restaurant_email', ''),
                'profile_image': serializer.data.get('profile_image', '') if serializer.data.get('profile_image') else '',
                'description': serializer.data.get('description', ''),
                'takeaway': serializer.data.get('takeaway', False),
                'delivery': serializer.data.get('delivery', False),
                'category': serializer.data.get('category', 'restaurant'),
                'open_time': serializer.data.get('open_time', ''),
                'close_time': serializer.data.get('close_time', ''),
            }, status=status.HTTP_200_OK)
        except Vendor.DoesNotExist:
            logger.error("Vendor not found for user: %s", request.user)
            return Response({'success': False, 'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Profile fetch error: %s", str(e), exc_info=True)
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request):
        logger.info("Processing POST request for profile update for user: %s, Token: %s, Data: %s", request.user, request.auth, dict(request.data))
        try:
            vendor = get_object_or_404(Vendor, user=request.user)
            serializer = VendorProfileSetupSerializer(vendor, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info("Profile updated for: %s", vendor.user.email)
                profile_image_url = ''
                if vendor.profile_image:
                    try:
                        profile_image_url = vendor.profile_image.url if default_storage.exists(vendor.profile_image.name) else ''
                    except Exception as e:
                        logger.error("Error generating profile_image URL: %s", str(e), exc_info=True)
                        profile_image_url = ''
                return Response({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'restaurant_name': vendor.restaurant_name,
                    'shop_no': vendor.shop_no,
                    'floor': vendor.floor,
                    'area': vendor.area,
                    'city': vendor.city,
                    'landmark': vendor.landmark,
                    'restaurant_phone': vendor.restaurant_phone,
                    'restaurant_email': vendor.restaurant_email,
                    'profile_image': profile_image_url,
                    'description': vendor.description,
                    'takeaway': vendor.takeaway,
                    'delivery': vendor.delivery,
                    'category': vendor.category,
                    'open_time': str(vendor.open_time) if vendor.open_time else '',
                    'close_time': str(vendor.close_time) if vendor.close_time else '',
                    'redirect_url': reverse('vendor:menu')
                }, status=status.HTTP_200_OK)
            logger.warning("Validation failed: %s", serializer.errors)
            return Response({
                'success': False,
                'message': 'Profile update failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Profile update error: %s", str(e), exc_info=True)
            return Response({
                'success': False,
                'message': 'An internal error occurred',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Class: VendorMenuSetupAPIView
class VendorMenuSetupAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = [JWTAuthentication]
    def post(self, request):
        logger.info("Menu setup request received: %s", dict(request.data))
        logger.info("User authenticated: %s, User: %s", request.user.is_authenticated, request.user)
        try:
            vendor = Vendor.objects.get(user=request.user)
            menu_items_data = []
            for key in request.data.keys():
                if key.startswith('menu_items['):
                    index = key.split('[')[1].split(']')[0]
                    field = key.split(']')[1][1:]
                    if not any(item['index'] == index for item in menu_items_data):
                        menu_items_data.append({'index': index})
                    for item in menu_items_data:
                        if item['index'] == index:
                            item[field] = request.data[key] if field != 'image' else request.FILES.get(key)
            errors = {}
            saved_items = 0
            for item_data in menu_items_data:
                serializer = MenuItemSerializer(data=item_data)
                if serializer.is_valid():
                    serializer.save(vendor=vendor)
                    saved_items += 1
                else:
                    errors[f"menu_item_{item_data['index']}"] = serializer.errors
            if errors:
                logger.warning("Validation failed for some items: %s", errors)
                return Response({
                    'success': False,
                    'message': f'Saved {saved_items} items, but some failed.',
                    'errors': errors
                }, status=status.HTTP_400_BAD_REQUEST)
            logger.info("Menu setup completed for: %s", vendor.user.email)
            return Response({
                'success': True,
                'message': 'Menu setup completed successfully',
                'redirect_url': reverse('vendor:vendor_home')
            }, status=status.HTTP_200_OK)
        except Vendor.DoesNotExist:
            logger.error("No Vendor profile found for user: %s", request.user.email)
            return Response({
                'success': False,
                'message': 'Vendor profile not found for this user',
                'error': 'Vendor not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Menu setup error: %s", str(e), exc_info=True)
            return Response({
                'success': False,
                'message': 'An internal error occurred',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Class: VendorLoginAPIView
class VendorLoginAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            logger.warning("Missing email or password in login request.")
            return Response({
                'success': False,
                'message': 'Email and password are required.',
                'errors': {
                    'email': 'This field is required.' if not email else None,
                    'password': 'This field is required.' if not password else None,
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            logger.info("User authenticated: %s", email)
            try:
                vendor = Vendor.objects.get(user=user)
                refresh = RefreshToken.for_user(user)
                return Response({
                    'success': True,
                    'message': 'Login successful.',
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'redirect_url': reverse('vendor:vendor_home')
                }, status=status.HTTP_200_OK)
            except Vendor.DoesNotExist:
                logger.error("Vendor profile not found for user: %s", email)
                return Response({
                    'success': False,
                    'message': 'This user does not have a vendor profile.',
                    'errors': {'non_field_errors': ['Vendor profile not found.']}
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning("Invalid credentials for email: %s", email)
            return Response({
                'success': False,
                'message': 'Invalid email or password.',
                'errors': {
                    'non_field_errors': ['Invalid email or password.']
                }
            }, status=status.HTTP_400_BAD_REQUEST)

# Class: VendorDashboardAPIView
class VendorDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, *args, **kwargs):
        logger.info("Fetching dashboard data for user: %s", request.user)
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vendor profile not found.',
            }, status=status.HTTP_400_BAD_REQUEST)
        total_earnings = Order.objects.filter(vendor=vendor).aggregate(total=Sum('total_amount'))['total'] or 0.0
        new_orders = Order.objects.filter(vendor=vendor, status='ongoing').count()
        total_customers = Order.objects.filter(vendor=vendor).values('user').distinct().count()
        try:
            from .models import Review
            average_rating = Review.objects.filter(vendor=vendor).aggregate(avg_rating=Avg('overall_rating'))['avg_rating'] or 0.0
            average_rating = round(average_rating, 1)
        except ImportError:
            average_rating = 0.0
        recent_orders = Order.objects.filter(vendor=vendor).order_by('-created_at')[:5]
        recent_orders_data = [
            {
                'id': order.id,
                'user_email': order.user.email,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'status': order.status,
                'total_amount': float(order.total_amount),
            } for order in recent_orders
        ]
        try:
            from .models import OrderItem
            top_menu_items = OrderItem.objects.filter(
                order__vendor=vendor
            ).values('menu_item__name', 'menu_item__category', 'menu_item__price').annotate(
                order_count=Count('id')
            ).order_by('-order_count')[:5]
            top_menu_items_data = [
                {
                    'menu_item__name': item['menu_item__name'],
                    'menu_item__category': item['menu_item__category'],
                    'menu_item__price': float(item['menu_item__price']),
                    'order_count': item['order_count'],
                } for item in top_menu_items
            ]
        except ImportError:
            top_menu_items = MenuItem.objects.filter(vendor=vendor).order_by('-id')[:5]
            top_menu_items_data = [
                {
                    'menu_item__name': item.name,
                    'menu_item__category': item.category,
                    'menu_item__price': float(item.price),
                    'order_count': 0,
                } for item in top_menu_items
            ]
        today = timezone.now()
        six_months_ago = today - timedelta(days=180)
        monthly_earnings = Order.objects.filter(
            vendor=vendor,
            created_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('total_amount')
        ).order_by('month')
        chart_labels = []
        chart_data = []
        current_month = six_months_ago
        while current_month <= today:
            chart_labels.append(current_month.strftime('%b %Y'))
            earnings_for_month = next(
                (entry['total'] for entry in monthly_earnings if entry['month'].strftime('%Y-%m') == current_month.strftime('%Y-%m')),
                0.0
            )
            chart_data.append(float(earnings_for_month))
            current_month = (current_month + timedelta(days=31)).replace(day=1)
        return Response({
            'success': True,
            'message': 'Dashboard data retrieved successfully.',
            'data': {
                'total_earnings': float(total_earnings),
                'new_orders': new_orders,
                'total_customers': total_customers,
                'average_rating': average_rating,
                'recent_orders': recent_orders_data,
                'top_menu_items': top_menu_items_data,
                'chart_labels': chart_labels,
                'chart_data': chart_data,
            }
        }, status=status.HTTP_200_OK)

# Class: MenuManagementView
@method_decorator(login_required, name='dispatch')
class MenuManagementView(APIView):
    def get(self, request, *args, **kwargs):
        logger.info("Fetching menu management page for user: %s", request.user)
        if not request.user.is_authenticated:
            return redirect('vendor:vendor_login')
        vendor = get_object_or_404(Vendor, user=request.user)
        return render(request, 'vendor/menu.html', {'vendor': vendor})

# Class: MenuItemListAPIView
@method_decorator(login_required, name='dispatch')
class MenuItemListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        logger.info("Fetching menu items for user: %s", request.user)
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': 'Authentication required.',
            }, status=status.HTTP_401_UNAUTHORIZED)
        vendor = get_object_or_404(Vendor, user=request.user)
        menu_items = MenuItem.objects.filter(vendor=vendor)
        serializer = MenuItemSerializer(menu_items, many=True)
        return Response({
            'success': True,
            'message': 'Menu items retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

# Class: MenuItemCreateAPIView
@method_decorator(login_required, name='dispatch')
class MenuItemCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        logger.info("Creating menu item for user: %s", request.user)
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': 'Authentication required.',
            }, status=status.HTTP_401_UNAUTHORIZED)
        vendor = get_object_or_404(Vendor, user=request.user)
        serializer = MenuItemSerializer(data=request.data, context={'vendor': vendor})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Menu item created successfully.',
                'redirect_url': reverse('vendor:menu')
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Validation errors.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# Class: MenuItemUpdateAPIView
@method_decorator(login_required, name='dispatch')
class MenuItemUpdateAPIView(APIView):
    def put(self, request, pk, *args, **kwargs):
        logger.info("Updating menu item %s for user: %s", pk, request.user)
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': 'Authentication required.',
            }, status=status.HTTP_401_UNAUTHORIZED)
        vendor = get_object_or_404(Vendor, user=request.user)
        menu_item = get_object_or_404(MenuItem, pk=pk, vendor=vendor)
        serializer = MenuItemSerializer(menu_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Menu item updated successfully.',
                'redirect_url': reverse('vendor:menu')
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'message': 'Validation errors.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# Class: MenuItemDeleteAPIView
@method_decorator(login_required, name='dispatch')
class MenuItemDeleteAPIView(APIView):
    def delete(self, request, pk, *args, **kwargs):
        logger.info("Deleting menu item %s for user: %s", pk, request.user)
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': 'Authentication required.',
            }, status=status.HTTP_401_UNAUTHORIZED)
        vendor = get_object_or_404(Vendor, user=request.user)
        menu_item = get_object_or_404(MenuItem, pk=pk, vendor=vendor)
        menu_item.delete()
        return Response({
            'success': True,
            'message': 'Menu item deleted successfully.',
            'redirect_url': reverse('vendor:menu')
        }, status=status.HTTP_200_OK)

# Class: MenuItemDetailAPIView
@method_decorator(login_required, name='dispatch')
class MenuItemDetailAPIView(APIView):
    def get(self, request, pk, *args, **kwargs):
        logger.info("Fetching menu item %s for user: %s", pk, request.user)
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': 'Authentication required.',
            }, status=status.HTTP_401_UNAUTHORIZED)
        vendor = get_object_or_404(Vendor, user=request.user)
        menu_item = get_object_or_404(MenuItem, pk=pk, vendor=vendor)
        serializer = MenuItemSerializer(menu_item)
        return Response({
            'success': True,
            'message': 'Menu item retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

# Function: menu
def menu(request):
    if not request.user.is_authenticated:
        return redirect('vendor:vendor_login')
    return render(request, 'vendor/menu.html')

# Function: orders
@login_required
def orders(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    ongoing_orders = Order.objects.filter(vendor=vendor, status='ongoing').order_by('-created_at')
    completed_orders = Order.objects.filter(vendor=vendor, status='completed').order_by('-created_at')
    cancelled_orders = Order.objects.filter(vendor=vendor, status='cancelled').order_by('-created_at')
    context = {
        'ongoing_orders': ongoing_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
    }
    return render(request, 'vendor/vendor_orders.html', context)

# Function: complete_order
@login_required
def complete_order(request, order_id):
    vendor = get_object_or_404(Vendor, user=request.user)
    order = get_object_or_404(Order, id=order_id, vendor=vendor)
    if order.status == 'ongoing':
        order.status = 'completed'
        order.save()
    return redirect('vendor:orders')

# Function: cancel_order
@login_required
def cancel_order(request, order_id):
    vendor = get_object_or_404(Vendor, user=request.user)
    order = get_object_or_404(Order, id=order_id, vendor=vendor)
    if order.status == 'ongoing':
        order.status = 'cancelled'
        order.save()
    return redirect('vendor:orders')

# Function: vendor_earnings
@login_required
def vendor_earnings(request):
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        messages.error(request, "You do not have a vendor profile.")
        return redirect('vendor:vendor_login')
    orders = Order.objects.filter(vendor=vendor).order_by('-created_at')
    total_earnings = orders.aggregate(total=Sum('total_amount'))['total'] or 0.0
    daily_earnings = orders.annotate(day=TruncDay('created_at')).values('day').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('-day')
    monthly_earnings = orders.annotate(month=TruncMonth('created_at')).values('month').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('-month')
    chart_labels = [entry['month'].strftime('%B %Y') for entry in monthly_earnings]
    chart_data = [float(entry['total']) for entry in monthly_earnings]
    context = {
        'orders': orders,
        'total_earnings': total_earnings,
        'daily_earnings': daily_earnings,
        'monthly_earnings': monthly_earnings,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'vendor/earnings.html', context)