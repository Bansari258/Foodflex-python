# users/urls.py
from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'users'

urlpatterns = [
    # Public routes
    path('', views.landing, name='landing'),
    path('signup/', views.signup, name='signup'),
    path('help/', views.help, name='help'),
    path('api/signup/', views.UserSignupAPIView.as_view(), name='api_signup'),
    path('api/login/', views.UserLoginAPIView.as_view(), name='api_login'),
    # Protected routes (require JWT authentication)
    path('api/logout/', views.UserLogoutAPIView.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('browseshops/', views.browse_shops, name='browse_shops'),
    path('vendor/detail/<int:vendor_id>/', views.vendor_detail, name='vendor_detail'),
    path('vendor/<int:vendor_id>/leave-review/', views.leave_review, name='leave_review'),
    path('order/<int:vendor_id>/', views.order_view, name='order'),
    path('confirm/', views.confirm_view, name='confirm'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('profile/', views.profile, name='profile'),
    path('api/user/', views.UserProfileAPIView.as_view(), name='api_user'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user/session/', views.UserSessionAPIView.as_view(), name='api_user_session'),
]