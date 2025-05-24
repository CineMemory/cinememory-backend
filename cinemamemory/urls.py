"""
URL configuration for cinemamemory project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/cinememory/movies/', include('movies.urls')),
    path('api/v1/cinememory/community/', include('posts.urls')),
    # 커스텀 accounts 뷰 (회원가입, 사용자 관리)
    path('api/v1/cinememory/accounts/', include('accounts.urls')),
    # dj-rest-auth 뷰 (로그인, 로그아웃 등 기본 인증)
    path('api/v1/cinememory/auth/', include('dj_rest_auth.urls')),
    path('api/v1/cinememory/auth/registration/', include('dj_rest_auth.registration.urls')),
    # API 문서화
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
