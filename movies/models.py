# movies/model.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Genre(models.Model):
    id = models.IntegerField(primary_key=True)  # TMDB에서 제공하는 장르 ID
    name = models.CharField(max_length=255)     # 장르 이름 (예: 액션, 코미디, 드라마)

    def __str__(self):
        return self.name

class Series(models.Model):
    id = models.IntegerField(primary_key=True)      # TMDB에서 제공하는 시리즈 ID
    title = models.CharField(max_length=255)         # 시리즈 제목
    overview = models.TextField()                    # 시리즈 설명
    poster_path = models.URLField()                  # 포스터 이미지 URL
    backdrop_path = models.URLField()                # 배경 이미지 URL
    popularity = models.FloatField(default=0)        # TMDB 인기도 점수

    def __str__(self):
        return self.title

class Director(models.Model):
    id = models.IntegerField(primary_key=True)       # TMDB에서 제공하는 감독 ID
    name = models.CharField(max_length=255)          # 감독 이름
    role = models.CharField(max_length=10)           # 역할 (감독, 각본 등)
    birth_date = models.DateField(null=True, blank=True)  # 생년월일
    death_date = models.DateField(null=True, blank=True)  # 사망일
    biography = models.TextField(null=True, blank=True)    # 약력
    profile_path = models.URLField()                 # 프로필 이미지 URL
    instagram_username = models.CharField(max_length=100, null=True)  # 인스타그램 아이디
    liked_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_directors', blank=True)  # 좋아요한 사용자들
    reviewed_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='reviewed_directors', blank=True)  # 임시 복구

    
    def __str__(self):
        return self.name

class Actor(models.Model):
    id = models.IntegerField(primary_key=True)       # TMDB에서 제공하는 배우 ID
    name = models.CharField(max_length=255)          # 배우 이름
    role = models.CharField(max_length=10)           # 역할 (배우, 성우 등)
    birth_date = models.DateField(null=True, blank=True)  # 생년월일
    death_date = models.DateField(null=True, blank=True)  # 사망일
    biography = models.TextField(null=True, blank=True)    # 약력
    profile_path = models.URLField()                 # 프로필 이미지 URL
    instagram_username = models.CharField(max_length=100, null=True, blank=True)  # 인스타그램 아이디
    liked_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_actors', blank=True)
    reviewed_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='reviewed_actors', blank=True)  # 임시 복구



    def __str__(self):
        return self.name
    
class Provider(models.Model):
    id = models.IntegerField(primary_key=True)       # TMDB에서 제공하는 스트리밍 서비스 ID
    name = models.CharField(max_length=100)          # 스트리밍 서비스 이름 (예: Netflix, Disney+)
    logo_path = models.URLField()                    # 서비스 로고 이미지 URL
    
    def __str__(self):
        return self.name


class Movie(models.Model):
    id = models.IntegerField(primary_key=True)       # TMDB에서 제공하는 영화 ID
    title = models.CharField(max_length=255)         # 영화 제목
    release_date = models.DateField()                # 개봉일
    poster_path = models.URLField()                  # 포스터 이미지 URL
    backdrop_path = models.URLField(null=True, blank=True)  # 배경 이미지 URL
    popularity = models.FloatField(default=0)        # TMDB 인기도 점수
    tagline = models.TextField(null=True, blank=True)  # 영화 태그라인
    overview = models.TextField(null=True, blank=True)  # 영화 줄거리
    status = models.CharField(max_length=50)         # 영화 상태 (개봉예정, 개봉, 종료 등)
    runtime = models.IntegerField(null=True, blank=True)  # 상영시간 (분)
    vote_average = models.FloatField(default=0)      # 평균 평점
    is_adult = models.BooleanField(default=False)    # 성인물 여부
    is_video = models.BooleanField(default=False)    # 비디오 여부
    series = models.ForeignKey(Series, on_delete=models.CASCADE, null=True, blank=True)  # 시리즈 연결
    genres = models.ManyToManyField(Genre, related_name='movies')  # 장르들
    directors = models.ManyToManyField(Director, related_name='movies')  # 감독들
    actors = models.ManyToManyField(Actor, through='MovieActor', related_name='movies')  # 배우들
    liked_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_movies', blank=True)  # 좋아요한 사용자들
    reviewed_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='reviewed_movies', blank=True)  # 리뷰 작성한 사용자들
    
    providers = models.ManyToManyField(        # 스트리밍 서비스들
        Provider, 
        through='MovieProvider',   
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


class MovieActor(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)  # 영화
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)  # 배우
    character_name = models.CharField(max_length=255, null=True, blank=True)  # 배우가 맡은 캐릭터 이름
    cast_order = models.IntegerField(default=0)      # 출연 순서 (낮을수록 더 중요한 역할)
    
    class Meta:
        # 같은 영화에서 같은 배우가 같은 캐릭터를 중복으로 맡는 것만 방지
        # 다른 캐릭터라면 같은 배우가 여러 역할 가능 (1인 2역, 성우 등)
        unique_together = ['movie', 'actor', 'character_name']
        ordering = ['cast_order']                    # 출연 순서대로 정렬
    
    def __str__(self):
        if self.character_name:
            return f"{self.movie.title} - {self.actor.name} as {self.character_name}"
        return f"{self.movie.title} - {self.actor.name}"

class MovieProvider(models.Model):
    PROVIDER_TYPE_CHOICES = [
        ('flatrate', 'Streaming'),  # 구독형 스트리밍
        ('rent', 'Rent'),          # 대여
        ('buy', 'Buy'),            # 구매
    ]
    
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)  # 영화
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)  # 스트리밍 서비스
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPE_CHOICES)  # 서비스 유형
    display_priority = models.IntegerField(default=0, null=True, blank=True)  # 표시 우선순위
    price = models.CharField(max_length=50, null=True, blank=True)  # 가격 (예: "3,500원")
    country_code = models.CharField(max_length=2, default='KR', null=True, blank=True)  # 국가 코드
    
    class Meta:
        unique_together = ['movie', 'provider', 'provider_type']  # 같은 영화, 같은 서비스, 같은 유형은 중복 불가
        ordering = ['display_priority']              # 우선순위대로 정렬
    
    def __str__(self):
        return f"{self.movie.title} - {self.provider.name} ({self.get_provider_type_display()})"
    
class MovieReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 리뷰 작성자
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)  # 리뷰 대상 영화
    content = models.TextField()                    # 리뷰 내용
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])  # 평점 (0-5)
    created_at = models.DateTimeField(auto_now_add=True)  # 작성일
    updated_at = models.DateTimeField(auto_now=True)  # 수정일

    class Meta:
        unique_together = ['user', 'movie']         # 한 사용자는 한 영화에 대해 하나의 리뷰만 작성 가능
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title} ({self.rating}⭐)"