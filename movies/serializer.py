from rest_framework import serializers

from .models import Movie, Actor, Director, MovieReview, Series, Genre, Provider, MovieProvider, MovieActor


class MovieBasicSerializer(serializers.ModelSerializer):    # 영화 기본 정보
    class Meta:
        model = Movie
        fields = ('id', 'title', 'release_date', 'poster_path', 'vote_average', 
                 'runtime', 'popularity', 'status', 'tagline', 'overview')

class ActorBasicSerializer(serializers.ModelSerializer):    # 배우 기본 정보    
    class Meta:
        model = Actor
        fields = ('id', 'name', 'profile_path', 'role')

class DirectorBasicSerializer(serializers.ModelSerializer):    # 감독 기본 정보
    class Meta:
        model = Director
        fields = ('id', 'name', 'profile_path', 'role')

class MovieActorSerializer(serializers.ModelSerializer):    # 영화-배우 관계 (캐릭터 정보 포함)
    actor = ActorBasicSerializer(read_only=True)
    
    class Meta:
        model = MovieActor
        fields = ('actor', 'character_name', 'cast_order')

class ActorMovieSerializer(serializers.ModelSerializer):    # 배우-영화 관계 (캐릭터 정보 포함)
    movie = MovieBasicSerializer(read_only=True)
    
    class Meta:
        model = MovieActor
        fields = ('movie', 'character_name', 'cast_order')

class ActorSerializer(serializers.ModelSerializer): # 배우 상세 페이지 들어갔을 때 정보
    movies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Actor
        fields = ('id', 'name', 'birth_date', 'death_date', 'profile_path', 'biography', 
                 'instagram_username', 'role', 'movies', 'liked_by', 'like_count', 'is_liked')
    
    def get_movies(self, obj):  # 배우의 출연작 목록 (캐릭터 정보 포함)
        movie_actors = MovieActor.objects.filter(actor=obj).select_related('movie').order_by('cast_order')
        return ActorMovieSerializer(movie_actors, many=True).data
    
    def get_like_count(self, obj):  # 배우의 좋아요 수
        return obj.liked_by.count()
    
    def get_is_liked(self, obj):  # 배우의 좋아요 여부
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.liked_by.filter(id=request.user.id).exists()
        return False
    
class DirectorSerializer(serializers.ModelSerializer): # 감독 상세 페이지 들어갔을 때 정보
    movies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Director
        fields = ('id', 'name', 'birth_date', 'death_date', 'profile_path', 'biography', 
                 'instagram_username', 'role', 'movies', 'liked_by', 'like_count', 'is_liked')
    
    def get_movies(self, obj):  # 감독의 연출작 목록
        movies = obj.movies.all()   
        return MovieBasicSerializer(movies, many=True).data
    
    def get_like_count(self, obj):  # 감독의 좋아요 수
        return obj.liked_by.count()
    
    def get_is_liked(self, obj):  # 감독의 좋아요 여부
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.liked_by.filter(id=request.user.id).exists()
        return False
    
        
class SeriesSerializer(serializers.ModelSerializer): # 시리즈 기본 정보
    class Meta:
        model = Series
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'

class ProviderSerializer(serializers.ModelSerializer): # 영화 상세 페이지 들어갔을 때 정보 - 시청 가능한 플랫폼 정보
    class Meta:
        model = Provider
        fields = '__all__'

class MovieProviderSerializer(serializers.ModelSerializer):    # 영화 상세 페이지 들어갔을 때 정보 - 시청 가능한 플랫폼 정보
    provider = ProviderSerializer(read_only=True)
    
    class Meta:
        model = MovieProvider
        fields = ('provider', 'provider_type', 'display_priority', 'price', 'country_code')

class MovieListSerializer(serializers.ModelSerializer): # 영화 목록 페이지 들어갔을 때 정보 - 검색 결과 등
    actors = serializers.SerializerMethodField()  # 캐릭터 정보 포함하도록 변경
    directors = DirectorBasicSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    series = SeriesSerializer(read_only=True)
    
    class Meta:
        model = Movie
        fields = ('id', 'title', 'release_date', 'poster_path', 'vote_average', 
                 'runtime', 'popularity', 'status', 'tagline', 'overview', 'is_adult',
                 'actors', 'directors', 'genres', 'series')
    
    def get_actors(self, obj):  # 영화의 출연 배우들 (캐릭터 정보 포함)
        movie_actors = MovieActor.objects.filter(movie=obj).select_related('actor').order_by('cast_order')[:5]  # 상위 5명만
        return MovieActorSerializer(movie_actors, many=True).data


class MovieSerializer(serializers.ModelSerializer): # 영화 상세 페이지 들어갔을 때 정보
    movie_id = serializers.IntegerField(source='id', read_only=True)  # id를 movie_id로도 제공
    movieId = serializers.IntegerField(source='id', read_only=True)   # camelCase로도 제공
    actors = serializers.SerializerMethodField()  # 캐릭터 정보 포함하도록 변경
    directors = DirectorBasicSerializer(many=True, read_only=True)
    series = SeriesSerializer(read_only=True)  # ForeignKey이므로 many=True 제거
    genres = GenreSerializer(many=True, read_only=True)
    providers = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = (
            'id', 'movie_id', 'movieId', 
            'title', 'release_date', 
            'poster_path', 'backdrop_path', 
            'vote_average', 'runtime', 'popularity', 
            'status', 'tagline', 'overview', 
            'is_adult', 'is_video',
            'actors', 'directors', 'genres', 'series', 
            'providers', 
            'like_count', 'is_liked', 'review_count', 'reviews', 'average_rating')
    
    def get_actors(self, obj):  # 영화의 출연 배우들 (캐릭터 정보 포함)
        movie_actors = MovieActor.objects.filter(movie=obj).select_related('actor').order_by('cast_order')
        return MovieActorSerializer(movie_actors, many=True).data
    
    def get_like_count(self, obj):  # 영화의 좋아요 수
        try:
            return obj.liked_by.count()
        except Exception:
            return 0
    
    def get_is_liked(self, obj):  # 영화의 좋아요 여부
        try:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                return obj.liked_by.filter(id=request.user.id).exists()
            return False
        except Exception:
            return False    
    
    def get_review_count(self, obj):  # 영화의 리뷰 수
        try:
            return obj.reviewed_by.count()
        except Exception:
            return 0
    
    def get_reviews(self, obj):
        from .models import MovieReview
        try:
            reviews = MovieReview.objects.filter(movie=obj).select_related('user').order_by('-created_at')[:5]
            return [{
                'id': review.id,
                'user': review.user.username,
                'user_profile': {  # 새로 추가
                    'id': review.user.id,
                    'username': review.user.username
                },
                'content': review.content,
                'rating': review.rating,
                'created_at': review.created_at
            } for review in reviews]
        except Exception as e:
            print(f"❌ get_reviews error: {e}")
            return []
    
    def get_providers(self, obj):  # 영화의 시청 가능한 플랫폼 정보
        try:
            movie_providers = MovieProvider.objects.filter(movie=obj).select_related('provider').order_by('display_priority')
            return MovieProviderSerializer(movie_providers, many=True).data
        except Exception as e:
            print(f"❌ get_providers error: {e}")
            return []

    def get_average_rating(self, obj):
        """영화의 평균 별점 계산"""
        try:
            from django.db.models import Avg
            from .models import MovieReview
            avg = MovieReview.objects.filter(movie=obj).aggregate(Avg('rating'))['rating__avg']
            return round(avg, 1) if avg else 0.0
        except Exception as e:
            print(f"❌ get_average_rating error: {e}")
            return 0.0

class MovieReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_profile = serializers.SerializerMethodField()  # 사용자 프로필 정보 추가
    movie_info = serializers.SerializerMethodField()
    
    class Meta:
        model = MovieReview
        fields = ['id', 'user', 'user_profile', 'movie_info', 'content', 'rating', 'created_at', 'updated_at']  # rating 추가
        
    def get_user_profile(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
        }

    def get_movie_info(self, obj):
        return {
            'id': obj.movie.id,
            'title': obj.movie.title,
            'poster_path': obj.movie.poster_path
        }
    