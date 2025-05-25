from rest_framework import serializers
from .models import Movie, Actor, Director, Series, Genre

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = '__all__'

class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = '__all__'

class DirectorSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'

class SeriesSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'