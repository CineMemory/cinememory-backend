from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


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
    # 사람들 리뷰
    review_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='reviewed_directors', blank=True)
    
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
    # 사람들 리뷰
    review_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='reviewed_actors', blank=True)

    def __str__(self):
        return self.name
    
class WatchProvider(models.Model):
    provider_id = models.IntegerField(primary_key=True)
    provider_name = models.CharField(max_length=100)
    logo_path = models.URLField()
    
    def __str__(self):
        return self.provider_name

class Movie(models.Model):
    movie_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    poster_path = models.URLField()
    backdrop_path = models.URLField(null=True, blank=True)
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
    review_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='reviewed_movies', blank=True)
    
    watch_providers = models.ManyToManyField(
        WatchProvider, 
        through='MovieWatchProvider',
        related_name='movies',
        blank=True
    )

    def __str__(self):
        return self.title

class MovieWatchProvider(models.Model):
    PROVIDER_TYPE_CHOICES = [
        ('flatrate', 'Streaming'),  # 구독형 스트리밍
        ('rent', 'Rent'),          # 대여
        ('buy', 'Buy'),            # 구매
    ]
    
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watch_provider = models.ForeignKey(WatchProvider, on_delete=models.CASCADE, db_column='watchprovider_id')
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPE_CHOICES)  # fixture 호환성을 위해
    display_priority = models.IntegerField(default=0, null=True, blank=True)
    price = models.CharField(max_length=50, null=True, blank=True)  # "3,500원" 형태로 저장
    country_code = models.CharField(max_length=2, default='KR', null=True, blank=True)  # 한국만 사용하지만 확장성을 위해
    
    # 호환성을 위한 property
    @property
    def monetization_type(self):
        return self.provider_type
    
    @monetization_type.setter
    def monetization_type(self, value):
        self.provider_type = value
    
    class Meta:
        # 같은 영화, 같은 제공업체, 같은 결제 타입은 중복 불가
        unique_together = ['movie', 'watch_provider', 'provider_type']
        # display_priority 순으로 정렬
        ordering = ['display_priority']
    
    def __str__(self):
        return f"{self.movie.title} - {self.watch_provider.provider_name} ({self.get_provider_type_display()})"
    
    
class ActorReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title} - {self.actor.name}"
    
class DirectorReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    director = models.ForeignKey(Director, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title} - {self.director.name}"
    
class MovieReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])  # ⭐ 추가
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
      unique_together = ['user', 'movie']
    
    def __str__(self):
      return f"{self.user.username} - {self.movie.title} ({self.rating}⭐)"