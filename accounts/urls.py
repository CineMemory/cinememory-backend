from django.urls import path
from . import views

urlpatterns = [
    # 회원가입 및 사용자 관리
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('check-username/', views.username_check, name='username_check'),  # 사용자명 중복 검사
    
    # 사용자 정보 조회 및 관리
    path('me/', views.get_my_info, name='get_my_info'),
    path('<int:user_id>/', views.get_user_profile, name='get_user_profile'),
    path('me/update/', views.update_user, name='update_user'),
    path('me/profile-image/', views.update_profile_image, name='update_profile_image'),
    path('me/delete/', views.delete_user, name='delete_user'),
    path('me/my-page/', views.my_page, name='my_page'),
]
