from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Movie, Actor, Director, Series, Genre
from .serializer import MovieSerializer, ActorSerializer, DirectorSerializer, SeriesSerializer, GenreSerializer


# Create your views here.
@api_view(['GET'])
def movie_detail(request, movie_id):
    try:
        # 관계 데이터를 효율적으로 가져오기 위한 최적화
        movie = Movie.objects.select_related('series').prefetch_related(
            'genres', 'directors', 'actors', 'like_users'
        ).get(movie_id=movie_id)
        
        serializer = MovieSerializer(movie)
        return Response(serializer.data)
    except Movie.DoesNotExist:
        return Response(
            {'error': '영화를 찾을 수 없습니다.'}, 
            status=404
        )