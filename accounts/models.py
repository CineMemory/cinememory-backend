from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import os

# Create your models here.
def user_profile_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{instance.id}.{ext}'
    return os.path.join('profile_images', filename)

class User(AbstractUser):
    birth = models.DateField() 
    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        null=True,
        blank=True,
        default='profile_images/default.jpg'
    )
    
    # 취향 설정 완료 여부
    onboarding_completed = models.BooleanField(default=False)

    # GPT가 생성한 사용자 취향 분석 텍스트
    taste_analysis = models.TextField(null=True, blank=True)


    def user_profile_image_path(instance, filename):
        ext = filename.split('.')[-1]
        filename = f'{instance.id}.{ext}'
        return os.path.join('profile_images', filename)
    
    @property
    def profile_image_url(self):
        if self.profile_image:
            return self.profile_image.url
        else:
            return '/media/default.jpg'
    
    # 성인 여부 확인
    @property
    def is_adult(self):
        from datetime import date

        today = date.today()
        age = today.year - self.birth.year
        return age >= 19

class OnboardingStep(models.Model):
    # 설문 진행 상황 추적
    STEP_CHOICES = [
        ('favorite_movies', '재밌게 본 영화 선택'),
        ('interesting_movies', '재밌어 보이는 영화 선택'),
        ('exclude_genres', '제외할 장르 선택'),
        ('gpt_analysis', 'GPT 분석 중'),
        ('completed', '완료'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='onboarding_progress'
    )
    current_step = models.CharField(
        max_length=20, choices=STEP_CHOICES, default='favorite_movies'
    )
    step_data = models.JSONField(default=dict)  # 각 단계별 선택 데이터 저장
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_current_step_display()}"


class UserMoviePreference(models.Model):  # 사용자 영화 선호도
    PREFERENCE_TYPE_CHOICES = [
        ('favorite', '재밌게 본 영화'),
        ('interesting', '재밌어 보이는 영화'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='movie_preferences'
    )
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    preference_type = models.CharField(
        max_length=20, choices=PREFERENCE_TYPE_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'movie', 'preference_type']

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} ({self.get_preference_type_display()})"


class UserGenreExclusion(models.Model):  # 사용자가 제외한 장르
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='excluded_genres'
    )
    genre = models.ForeignKey('movies.Genre', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'genre']

    def __str__(self):
        return f"{self.user.username} - 제외: {self.genre.name}"


class GPTRecommendation(models.Model):  # GPT가 생성한 개인화 추천 결과
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='gpt_recommendation'
    )
    taste_summary = (
        models.TextField()
    )  # "설문을 보아하니 {username}는 {} 취향이다"

    # GPT 추천 영화들 (최대 6개)
    recommended_movies = models.ManyToManyField(
        'movies.Movie',
        through='GPTRecommendedMovie',
        related_name='gpt_recommendations',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}의 GPT 추천"


class GPTRecommendedMovie(models.Model):  # GPT 추천 영화 상세 정보
    recommendation = models.ForeignKey(
        GPTRecommendation, on_delete=models.CASCADE
    )
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    reason = models.TextField()  # 추천 근거
    recommendation_order = models.IntegerField()  # 추천 순서 (1-6)
    target_age = models.IntegerField()  # 사용자의 몇 살 때 추천영화인지

    class Meta:
        unique_together = ['recommendation', 'movie']
        ordering = ['recommendation_order']

    def __str__(self):
        return f"{self.recommendation.user.username} - {self.movie.title} (순서: {self.recommendation_order})"


class OnboardingMovie(models.Model):  # 온보딩에서 사용할 영화 풀 정보
    MOVIE_TYPE_CHOICES = [
        ('famous', '유명한 영화'),
        ('hidden', '안 유명한 영화'),
    ]

    movie = models.OneToOneField(
        'movies.Movie',
        on_delete=models.CASCADE,
        related_name='onboarding_info',
    )
    movie_type = models.CharField(max_length=10, choices=MOVIE_TYPE_CHOICES)
    display_order = models.IntegerField(default=0)  # 표시 순서
    is_active = models.BooleanField(default=True)  # 활성화 여부

    class Meta:
        ordering = ['display_order', 'movie__popularity']

    def __str__(self):
        return f"{self.movie.title} ({self.get_movie_type_display()})"


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"