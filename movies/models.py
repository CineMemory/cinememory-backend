from django.db import models

class Movie(models.Model):
    pk = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    poster_path = models.URLField()
    popularity = models.FloatField(default=0)
    directors = models.ManyToManyField('Director', related_name='movies')
    actors = models.ManyToManyField('Actor', related_name='movies')

    def __str__(self):
        return self.title

class Director(models.Model):
    pk = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10)
    birth = models.DateField()
    death = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_path = models.URLField()
    instagram_id = models.CharField(max_length=100, null=True)
    
    def __str__(self):
        return self.name

class Actor(models.Model):
    pk = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10)
    birth = models.DateField()
    death = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_path = models.URLField()
    instagram_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name
