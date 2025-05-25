from rest_framework import serializers
from .models import Movie, Actor, Director, Series, Genre

class MovieBasicSerializer(serializers.ModelSerializer):
    """영화 기본 정보만 포함하는 Serializer (순환 참조 방지)"""
    class Meta:
        model = Movie
        fields = ('movie_id', 'title', 'release_date', 'poster_path', 'vote_average', 
                 'runtime', 'popularity', 'status')

class ActorSerializer(serializers.ModelSerializer):
    movies = serializers.SerializerMethodField()
    
    class Meta:
        model = Actor
        fields = ('actor_id', 'name', 'birth', 'death', 'profile_path', 'bio', 
                 'instagram_id', 'role', 'movies', 'like_users')
    
    def get_movies(self, obj):
        """배우의 출연작 목록"""
        movies = obj.movies.all()
        return MovieBasicSerializer(movies, many=True).data

class DirectorSerializer(serializers.ModelSerializer):
    movies = serializers.SerializerMethodField()
    
    class Meta:
        model = Director
        fields = ('director_id', 'name', 'birth', 'death', 'profile_path', 'bio', 
                 'instagram_id', 'role', 'movies', 'like_users')
    
    def get_movies(self, obj):
        """감독의 연출작 목록"""
        movies = obj.movies.all()
        return MovieBasicSerializer(movies, many=True).data

class SeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Series
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class MovieSerializer(serializers.ModelSerializer):
    actors = ActorSerializer(many=True, read_only=True)
    directors = DirectorSerializer(many=True, read_only=True)
    series = SeriesSerializer(read_only=True)  # ForeignKey이므로 many=True 제거
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = '__all__'
