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
        
@api_view(['GET'])
def person_detail(request, person_id):
    try:
        # 배우인지 확인
        if Actor.objects.filter(actor_id=person_id).exists():
            person = Actor.objects.prefetch_related('movies').get(actor_id=person_id)
            serializer = ActorSerializer(person)
            return Response(serializer.data)
        # 감독인지 확인
        elif Director.objects.filter(director_id=person_id).exists():
            person = Director.objects.prefetch_related('movies').get(director_id=person_id)
            serializer = DirectorSerializer(person)
            return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': '사람을 찾을 수 없습니다.'}, 
            status=404
        )

@api_view(['GET'])
def search_some(request):
    search_query = request.GET.get('search', '')
    
    if not search_query:
        return Response(status=204)
    
    try:
        if Movie.objects.filter(title__icontains=search_query).exists():
            movies = Movie.objects.filter(title__icontains=search_query)
            serializer = MovieSerializer(movies, many=True)
            return Response(serializer.data)
        elif Actor.objects.filter(name__icontains=search_query).exists():
            actors = Actor.objects.filter(name__icontains=search_query)
            serializer = ActorSerializer(actors, many=True)
            return Response(serializer.data)
        elif Director.objects.filter(name__icontains=search_query).exists():
            directors = Director.objects.filter(name__icontains=search_query)
            serializer = DirectorSerializer(directors, many=True)
            return Response(serializer.data)
        else:
            return Response(
                {'error': '검색 결과를 찾을 수 없습니다.'}, 
                status=404
            )
    except Exception as e:
        return Response(
            {'error': '검색 중 오류가 발생했습니다.'}, 
            status=500
        )