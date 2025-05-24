from django.db import models
from django.conf import settings

class Genre(models.Model):
    genre_id = models.IntegerField(primary_key=True)
    genre_name = models.CharField(max_length=255)

    def __str__(self):
        return self.genre_name

class Series(models.Model):
    series_id = models.IntegerField(primary_key=True)
    series_title = models.CharField(max_length=255)
    series_overview = models.TextField()
    series_poster_path = models.URLField()
    series_backdrop_path = models.URLField()
    popularity = models.FloatField(default=0)

    def __str__(self):
        return self.series_title

class Director(models.Model):
    director_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10)
    birth = models.DateField()
    death = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_path = models.URLField()
    instagram_id = models.CharField(max_length=100, null=True)
    like_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_directors', blank=True)
    
    def __str__(self):
        return self.name

class Actor(models.Model):
    actor_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10)
    birth = models.DateField()
    death = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_path = models.URLField()
    instagram_id = models.CharField(max_length=100, null=True, blank=True)
    like_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_actors', blank=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    movie_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    poster_path = models.URLField()
    popularity = models.FloatField(default=0)
    tagline = models.TextField(null=True, blank=True)
    overview = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50)
    runtime = models.IntegerField(null=True, blank=True)
    vote_average = models.FloatField(default=0)
    adult_flag = models.BooleanField(default=False)
    video_flag = models.BooleanField(default=False)
    series = models.ForeignKey(Series, on_delete=models.CASCADE, null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name='movies')
    directors = models.ManyToManyField(Director, related_name='movies')
    actors = models.ManyToManyField(Actor, related_name='movies')
    like_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_movies', blank=True)

    def __str__(self):
        return self.title