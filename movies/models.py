from django.db import models

# Create your models here.
class Movie(models.Model):
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    poster_url = models.URLField()
    directors = models.ManyToManyField('Director', through='MovieDirector')
    actors = models.ManyToManyField('Actor', through='MovieActor')

class Director(models.Model):
    name = models.CharField(max_length=255)

class Actor(models.Model):
    name = models.CharField(max_length=255)

class MovieDirector(models.Model):  # 영화-감독 중개테이블
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    director = models.ForeignKey(Director, on_delete=models.CASCADE)

class MovieActor(models.Model):  # 영화-배우 중개테이블
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)