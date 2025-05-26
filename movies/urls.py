from django.urls import path, include
from django.conf import settings
from . import views

urlpatterns = [
    path('<int:movie_id>/', views.movie_detail, name='movieDetail'),
    path('person/<int:person_id>/', views.person_detail, name='personDetail'),
    path('search/', views.search_some, name='searchSome'),
    path('review/<int:movie_id>/', views.review_movie, name='reviewMovie'),
    path('person/review/<int:person_id>/', views.review_person, name='reviewPerson'),
    path('like/<int:movie_id>/', views.like_movie, name='likeMovie'),
    path('person/like/<int:person_id>/', views.like_person, name='likePerson'),
]

