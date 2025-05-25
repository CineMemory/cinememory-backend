from django.urls import path, include
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.post_list, name='PosstList'),
    path('post/', views.create_post, name='createPost'),
    path('post/<int:post_id>/', views.post_detail, name='postDetail'),
    path('post/<int:post_id>/comments/', views.create_comment, name='createComment'),
    path('post/<int:post_id>/comments/<int:comment_id>/', views.comment_detail, name='commentDetail'),
]

