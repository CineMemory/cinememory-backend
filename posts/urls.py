from django.urls import path, include
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.post_list, name='PosstList'),
    path('post/', views.create_post, name='createPost'),
]

