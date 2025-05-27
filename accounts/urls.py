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
    
    # 팔로우, 팔로잉
    path('<int:user_id>/follow/', views.follow_user, name='follow_user'),
    path('<int:user_id>/followers/', views.get_followers, name='get_followers'),
    path('<int:user_id>/following/', views.get_following, name='get_following'),

    path('username/<str:username>/', views.get_user_by_username, name='get_user_by_username'),
    
    # 온보딩
    path('onboarding/status/', views.onboarding_status, name='onboarding_status'),
    path('onboarding/movies/famous/', views.get_famous_movies, name='get_famous_movies'),
    path('onboarding/movies/hidden/', views.get_hidden_movies, name='get_hidden_movies'),
    path('onboarding/movies/random/', views.get_random_movie_during_analysis, name='get_random_movie'),
    path('onboarding/genres/', views.get_genres, name='get_genres'),
    path('onboarding/step1/save/', views.save_favorite_movies, name='save_favorite_movies'),
    path('onboarding/step2/save/', views.save_interesting_movies, name='save_interesting_movies'),
    path('onboarding/step3/save/', views.save_excluded_genres, name='save_excluded_genres'),
    path('onboarding/step4/generate/', views.generate_gpt_recommendations, name='generate_gpt_recommendations'),
    # 추천 결과 조회 및 관리
    path('recommendations/', views.get_user_recommendations, name='get_user_recommendations'),
    path('recommendations/regenerate/', views.regenerate_recommendations, name='regenerate_recommendations'),
]
