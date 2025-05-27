from rest_framework import serializers
from .models import ActorReview, DirectorReview, Movie, Actor, Director, MovieReview, Series, Genre, WatchProvider, MovieWatchProvider, PersonalizedTimeline

class MovieBasicSerializer(serializers.ModelSerializer):    # 영화 기본 정보
    class Meta:
        model = Movie
        fields = ('movie_id', 'title', 'release_date', 'poster_path', 'vote_average', 
                 'runtime', 'popularity', 'status', 'tagline', 'overview')

class ActorBasicSerializer(serializers.ModelSerializer):    # 배우 기본 정보    
    class Meta:
        model = Actor
        fields = ('actor_id', 'name', 'profile_path', 'role')

class DirectorBasicSerializer(serializers.ModelSerializer):    # 감독 기본 정보
    class Meta:
        model = Director
        fields = ('director_id', 'name', 'profile_path', 'role')

class ActorSerializer(serializers.ModelSerializer): # 배우 상세 페이지 들어갔을 때 정보
    movies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Actor
        fields = ('actor_id', 'name', 'birth', 'death', 'profile_path', 'bio', 
                 'instagram_id', 'role', 'movies', 'like_users', 'review_users', 'like_count', 'is_liked', 'review_count', 'reviews')
    
    def get_movies(self, obj):  # 배우의 출연작 목록
        movies = obj.movies.all()
        return MovieBasicSerializer(movies, many=True).data
    
    def get_like_count(self, obj):  # 배우의 좋아요 수
        return obj.like_users.count()
    
    def get_is_liked(self, obj):  # 배우의 좋아요 여부
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.like_users.filter(id=request.user.id).exists()
        return False
    
    def get_review_count(self, obj):  # 배우의 리뷰 수
        return obj.review_users.count()
    
    def get_reviews(self, obj):
        from .models import MovieReview, Movie  # 순환 import 방지
    
        # obj 타입 확인 및 디버깅
        if not isinstance(obj, Movie):
            print(f"❌ get_reviews: Expected Movie, got {type(obj)}: {obj}")
            return []
    
        try:
            reviews = MovieReview.objects.filter(movie=obj).select_related('user').order_by('-created_at')[:5]
            return MovieReviewSerializer(reviews, many=True).data
        except Exception as e:
            print(f"❌ get_reviews error: {e}")
            return []
    
class DirectorSerializer(serializers.ModelSerializer): # 감독 상세 페이지 들어갔을 때 정보
    movies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Director
        fields = ('director_id', 'name', 'birth', 'death', 'profile_path', 'bio', 
                 'instagram_id', 'role', 'movies', 'like_users', 'review_users', 'like_count', 'is_liked', 'review_count', 'reviews')
    
    def get_movies(self, obj):  # 감독의 연출작 목록
        movies = obj.movies.all()   
        return MovieBasicSerializer(movies, many=True).data
    
    def get_like_count(self, obj):  # 감독의 좋아요 수
        return obj.like_users.count()
    
    def get_is_liked(self, obj):  # 감독의 좋아요 여부
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.like_users.filter(id=request.user.id).exists()
        return False
    
    def get_review_count(self, obj):  # 감독의 리뷰 수
        return obj.review_users.count()
    
    def get_reviews(self, obj):  # 감독의 리뷰 목록
        return obj.review_users.all()
    
    
class SeriesSerializer(serializers.ModelSerializer): # 시리즈 기본 정보
    class Meta:
        model = Series
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'

class WatchProviderSerializer(serializers.ModelSerializer): # 영화 상세 페이지 들어갔을 때 정보 - 시청 가능한 플랫폼 정보
    class Meta:
        model = WatchProvider
        fields = '__all__'

class MovieWatchProviderSerializer(serializers.ModelSerializer):    # 영화 상세 페이지 들어갔을 때 정보 - 시청 가능한 플랫폼 정보
    watch_provider = WatchProviderSerializer(read_only=True)
    
    class Meta:
        model = MovieWatchProvider
        fields = ('watch_provider', 'provider_type', 'display_priority', 'price', 'country_code')

class MovieListSerializer(serializers.ModelSerializer): # 영화 목록 페이지 들어갔을 때 정보 - 검색 결과 등
    actors = ActorBasicSerializer(many=True, read_only=True)
    directors = DirectorBasicSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    series = SeriesSerializer(read_only=True)
    
    class Meta:
        model = Movie
        fields = ('movie_id', 'title', 'release_date', 'poster_path', 'vote_average', 
                 'runtime', 'popularity', 'status', 'tagline', 'overview', 'adult_flag',
                 'actors', 'directors', 'genres', 'series')


class MovieSerializer(serializers.ModelSerializer): # 영화 상세 페이지 들어갔을 때 정보
    actors = ActorSerializer(many=True, read_only=True)
    directors = DirectorSerializer(many=True, read_only=True)
    series = SeriesSerializer(read_only=True)  # ForeignKey이므로 many=True 제거
    genres = GenreSerializer(many=True, read_only=True)
    watch_provider_details = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = '__all__'
    
    def get_like_count(self, obj):  # 영화의 좋아요 수
        return obj.like_users.count()
    
    def get_is_liked(self, obj):  # 영화의 좋아요 여부
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.like_users.filter(id=request.user.id).exists()
        return False    
    
    def get_review_count(self, obj):  # 영화의 리뷰 수
        return obj.review_users.count()
    
    def get_reviews(self, obj):
        from .models import MovieReview  # 순환 import 방지
        reviews = MovieReview.objects.filter(movie=obj).order_by('-created_at')[:5]
        return [{
            'id': review.id,
            'user': review.user.username,
            'content': review.content,
            'created_at': review.created_at
        } for review in reviews]
    
    def get_watch_provider_details(self, obj):  # 영화의 시청 가능한 플랫폼 정보
        movie_watch_providers = MovieWatchProvider.objects.filter(movie=obj).order_by('display_priority')
        return MovieWatchProviderSerializer(movie_watch_providers, many=True).data

    def get_average_rating(self, obj):
        """영화의 평균 별점 계산"""
        from django.db.models import Avg
        from .models import MovieReview
        avg = MovieReview.objects.filter(movie=obj).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0


class MovieReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_profile = serializers.SerializerMethodField()  # 사용자 프로필 정보 추가
    
    class Meta:
        model = MovieReview
        fields = ['id', 'user', 'user_profile', 'content', 'rating', 'created_at', 'updated_at']  # rating 추가
        
    def get_user_profile(self, obj):
        """사용자 프로필 정보 (아바타 등)"""
        return {
            'username': obj.user.username,
            'profile_image_url': obj.user.profile_image_url,
        }
        
class ActorReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ActorReview
        fields = '__all__'
        
class DirectorReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = DirectorReview
        fields = '__all__'
        
class OnboardingMovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    poster_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Movie
        fields = (
            'movie_id', 
            'title', 
            'release_date', 
            'poster_url', 
            'vote_average', 
            'runtime', 
            'popularity', 
            'tagline', 
            'adult_flag', 
            'genres', 
            'onboarding_priority', 
            'onboarding_category'
        )
        
    def get_poster_url(self, obj):
        return obj.poster_url

class MovieSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ('movie_id', 'title', 'release_date', 'poster_path', 'vote_average', 'runtime', 'popularity', 'status', 'tagline', 'overview', 'adult_flag')

    def get_poster_url(self, obj):
        return obj.poster_url
    
class UserPreferenceSerializer(serializers.ModelSerializer):
    selected_movies = MovieSimpleSerializer(many=True, read_only=True)
    selected_movie_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="선택한 영화 ID 리스트"
    )
    
    class Meta:
        model = UserPreference
        fields = (
            'selected_movies',
            'selected_movie_ids',
            'analysis_result',
            'preferred_genres',
            'preferred_decades',
            'storytelling_preference',
            'tone_preference',
            'recommendation_keywords',
            'is_analyzed',
            'analyzed_at',
            'created_at',
            'updated_at'
        )
        read_only_fields = (
            'analysis_result',
            'is_analyzed',
            'analyzed_at',
            'created_at',
            'updated_at'
        )
        
    def update(self, instance, validated_data):
        selected_movie_ids = validated_data.pop('selected_movie_ids', None)
        if selected_movie_ids:
            instance.selected_movies.set(Movie.objects.filter(movie_id__in=selected_movie_ids))
        return super().update(instance, validated_data)
    
class PersonalizedTimelineSerializer(serializers.ModelSerializer):
    movie = MovieSimpleSerializer(read_only=True)
    
    class Meta:
        model = PersonalizedTimeline
        fields = (
            'id',
            'movie',
            'user_age',
            'year',
            'recommendation_reason',
            'preference_score',
            'display_order',
            'created_at'
        )