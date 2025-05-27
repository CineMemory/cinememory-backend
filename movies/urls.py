from django.urls import path, include
from django.conf import settings
from . import views

urlpatterns = [
    path('<int:id>/', views.movie_detail, name='movieDetail'),
    path('person/<int:person_id>/', views.person_detail, name='personDetail'),
    path('search/', views.search_some, name='searchSome'),
    path('review/<int:movie_id>/', views.review_movie, name='reviewMovie'),
    path('review/<int:movie_id>/<int:review_id>/', views.review_movie_detail, name='reviewMovieDetail'),
    path('person/review/<int:person_id>/', views.review_person, name='reviewPerson'),
    path('person/review/<int:person_id>/<int:review_id>/', views.review_person_detail, name='reviewPersonDetail'),
    path('like/<int:movie_id>/', views.like_movie, name='likeMovie'),
    path('person/like/<int:person_id>/', views.like_person, name='likePerson'),
    path('user/liked/', views.user_liked_movies, name='userLikedMovies'),
    path('user/reviews/', views.user_reviews, name='userReviews'),
]
