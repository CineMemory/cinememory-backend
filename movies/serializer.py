from rest_framework import serializers
from .models import Movie, Actor, Director, Series, Genre

class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = '__all__'

class DirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director
        fields = '__all__'

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
