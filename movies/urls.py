from django.urls import path, include
from django.conf import settings
from . import views

urlpatterns = [
    path('<int:movie_id>/', views.movie_detail, name='movieDetail'),
]

