# vendor/urls.py
from django.urls import path
from . import views

app_name = 'vendor'

urlpatterns = [
    path('', views.vendor_landing, name='vendor_landing'),
    path('signup/', views.vendor_signup, name='vendor_signup'),
    path('profile/setup/', views.vendor_profile_setup, name='profile_setup'),
    path('menu/setup/', views.vendor_menu_setup, name='menu_setup'),
    path('home/', views.vendor_home, name='vendor_home'),
    path('profile/', views.vendor_profile, name='vendor_profile'),
    path('help/', views.help, name='vendor_help'),
    path('menu/', views.menu, name='menu'),
    path('orders/', views.orders, name='orders'),
    path('customers/', views.customers, name='customers'),
    path('earnings/', views.vendor_earnings, name='earnings'),
    path('logout/', views.vendor_logout, name='vendor_logout'),
    path('order/<int:order_id>/complete/', views.complete_order, name='complete_order'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    # API Endpoints
    path('api/signup/', views.VendorSignupAPIView.as_view(), name='api_vendor_signup'),
    path('api/profile/setup/', views.VendorProfileSetupAPIView.as_view(), name='api_profile_setup'),
    path('api/menu/setup/', views.VendorMenuSetupAPIView.as_view(), name='api_menu_setup'),
    path('api/login/', views.VendorLoginAPIView.as_view(), name='api_vendor_login'),
    path('api/dashboard/', views.VendorDashboardAPIView.as_view(), name='api_vendor_dashboard'),
    path('api/menu/', views.MenuItemListAPIView.as_view(), name='api_menu_list'),
    path('api/menu/create/', views.MenuItemCreateAPIView.as_view(), name='api_menu_create'),
    path('api/menu/<int:pk>/', views.MenuItemDetailAPIView.as_view(), name='api_menu_detail'),
    path('api/menu/<int:pk>/update/', views.MenuItemUpdateAPIView.as_view(), name='api_menu_update'),
    path('api/menu/<int:pk>/delete/', views.MenuItemDeleteAPIView.as_view(), name='api_menu_delete'),
]