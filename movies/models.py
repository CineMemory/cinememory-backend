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