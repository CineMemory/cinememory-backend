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
    is_onboarding_movie = models.BooleanField(default=False)
    onboarding_priority = models.IntegerField(default=0)
    onboarding_category = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.title
    
    @property
    def poster_url(self):
        if self.poster_path:
            return f'https://image.tmdb.org/t/p/w500{self.poster_path}'
        return None

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    analysis_result = models.JSONField(default=list, blank=True, help_text='분석 결과를 저장하는 필드')
    preferred_genres = models.JSONField(default=list, help_text="선호 장르 리스트")
    preferred_decades = models.JSONField(default=list, help_text="선호 연대 리스트") 
    storytelling_preference = models.CharField(max_length=100, blank=True, help_text="스토리텔링 선호도")
    tone_preference = models.CharField(max_length=100, blank=True, help_text="톤앤매너 선호도")
    recommendation_keywords = models.JSONField(default=list, help_text="추천 키워드 리스트")
    
    # 분석 상태
    is_analyzed = models.BooleanField(default=False)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}의 취향"


# ✨ 새 모델: 개인화된 타임라인
class PersonalizedTimeline(models.Model):
    """사용자별 개인화된 영화 타임라인"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personalized_movies')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    
    # 타임라인 정보
    user_age = models.IntegerField(help_text="사용자의 몇 살 때 추천 영화인지")
    year = models.IntegerField(help_text="실제 연도")
    
    # 추천 정보
    recommendation_reason = models.TextField(blank=True, help_text="추천 이유")
    preference_score = models.FloatField(default=0.0, help_text="취향 매칭 점수 (0-1)")
    display_order = models.IntegerField(default=0, help_text="같은 나이 내에서의 정렬 순서")
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'user_age', 'movie']
        ordering = ['user_age', 'display_order']
    
    def __str__(self):
        return f"{self.user.username} {self.user_age}세 - {self.movie.title}"


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"