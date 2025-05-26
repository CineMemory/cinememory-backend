from django.urls import path, include
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.post_list, name='PosstList'),
    path('post/', views.create_post, name='createPost'),
    path('post/<int:post_id>/', views.post_detail, name='postDetail'),
    path('post/<int:post_id>/comments/', views.create_comment, name='createComment'),
    path('post/<int:post_id>/comments/<int:comment_id>/', views.comment_detail, name='commentDetail'),
    path('post/<int:post_id>/comments/<int:comment_id>/replies/', views.create_reply, name='createReply'),
    path('post/<int:post_id>/comments/<int:comment_id>/replies/<int:reply_id>/', views.reply_detail, name='replyDetail'),
    path('post/<int:post_id>/likes/', views.toggle_like, name='toggleLike'),
    path('tags/', views.tag_list, name='tagList'),                    # 모든 태그 조회
    path('tags/<str:tag_name>/posts/', views.posts_by_tag, name='postsByTag'),  # 특정 태그의 게시글 조회
]

