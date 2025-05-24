from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('me/', views.get_my_info, name='get_my_info'),
    path('<int:user_id>/', views.get_user_profile, name='get_user_profile'),
    path('me/update/', views.update_user, name='update_user'),
    path('me/delete/', views.delete_user, name='delete_user'),
    # JWT 토큰 발급/갱신 (로그인/로그아웃 역할)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
