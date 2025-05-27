from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializer import UserSerializer
from .models import Follow, OnboardingStep, OnboardingMovie, UserMoviePreference, UserGenreExclusion, GPTRecommendation, GPTRecommendedMovie
from movies.models import Movie, Genre
from .gpt_service import GPTRecommendationService
from django.db import transaction

User = get_user_model()

# Create your views here.
"""
필수 항목
username -> 중복 확인
password -> 조건 확인 (조건 미정)
birth -> 생년월일 전부
"""

# 회원가입
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # 회원가입 성공 시 토큰 생성
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'birth': user.birth
            },
            'token': token.key,
            'message': '회원가입이 완료되었습니다.'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 닉네임(username) 중복 확인
@api_view(['POST'])
@permission_classes([AllowAny])
def username_check(request):
    """
    사용자명 중복 확인 API
    
    요청 데이터:
    - username: 확인할 사용자 아이디
    
    응답:
    - 사용 가능: 200 OK
    - 중복: 400 Bad Request
    """
    username = request.data.get('username')
    if not username:
        return Response({'error': '사용자명을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': '이미 사용 중인 아이디입니다.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'message': '사용 가능한 아이디입니다.'}, status=status.HTTP_200_OK)

# 내 정보 조회
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_info(request):
    """
    로그인한 사용자 정보 조회 API
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 다른 사용자 프로필 조회
@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_profile(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': '사용자를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

# 사용자 정보 수정
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user(request):
    """
    사용자 정보 수정 API
    
    수정 가능 항목:
    - username: 사용자 아이디
    - password1, password2: 비밀번호 변경
    - birth: 생년월일
    - profile_image: 프로필 이미지
    """
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'user': serializer.data,
            'message': '사용자 정보가 수정되었습니다.'
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 계정 삭제
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request):
    """
    계정 삭제 API
    """
    user = request.user
    # 관련 토큰도 함께 삭제
    try:
        token = Token.objects.get(user=user)
        token.delete()
    except Token.DoesNotExist:
        pass
    
    user.delete()
    return Response({'message': '계정이 삭제되었습니다.'}, status=status.HTTP_200_OK)

# 로그인
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    로그인 API
    
    요청 데이터:
    - username: 사용자 아이디
    - password: 비밀번호
    
    응답:
    - 성공: 200 OK, 사용자 정보 및 토큰
    - 실패: 400 Bad Request, 오류 메시지
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': '사용자명과 비밀번호를 모두 입력해주세요.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'birth': user.birth
            },
            'token': token.key,
            'message': '로그인되었습니다.'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': '사용자명 또는 비밀번호가 올바르지 않습니다.'
        }, status=status.HTTP_400_BAD_REQUEST)

# 로그아웃
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    로그아웃 API - 토큰 삭제
    """
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({'message': '로그아웃되었습니다.'}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({'message': '이미 로그아웃되었습니다.'}, status=status.HTTP_200_OK)

# 프로필 이미지 업데이트
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_image(request):
    """
    프로필 이미지 업데이트 API
    
    요청 데이터:
    - profile_image: 업로드할 이미지 파일
    """
    if 'profile_image' not in request.FILES:
        return Response({'error': '프로필 이미지를 선택해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    user.profile_image = request.FILES['profile_image']
    user.save()
    
    serializer = UserSerializer(user)
    return Response({
        'user': serializer.data,
        'message': '프로필 이미지가 업데이트되었습니다.'
    }, status=status.HTTP_200_OK)


# 팔로우/언팔로우 토글
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    try:
        target_user = User.objects.get(id=user_id)
        if target_user == request.user:
            return Response({'error': '자기 자신을 팔로우할 수 없습니다.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        follow_relation = Follow.objects.filter(
            follower=request.user, 
            following=target_user
        ).first()
        
        if follow_relation:
            # 언팔로우
            follow_relation.delete()
            return Response({'message': '언팔로우했습니다.', 'is_following': False}, 
                          status=status.HTTP_200_OK)
        else:
            # 팔로우
            Follow.objects.create(follower=request.user, following=target_user)
            return Response({'message': '팔로우했습니다.', 'is_following': True}, 
                          status=status.HTTP_200_OK)
            
    except User.DoesNotExist:
        return Response({'error': '사용자를 찾을 수 없습니다.'}, 
                      status=status.HTTP_404_NOT_FOUND)

# 팔로워 목록 조회
@api_view(['GET'])
@permission_classes([AllowAny])
def get_followers(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        followers = User.objects.filter(following__following=user)
        serializer = UserSerializer(followers, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': '사용자를 찾을 수 없습니다.'}, 
                      status=status.HTTP_404_NOT_FOUND)

# 팔로잉 목록 조회
@api_view(['GET'])
@permission_classes([AllowAny])
def get_following(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        following = User.objects.filter(followers__follower=user)
        serializer = UserSerializer(following, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': '사용자를 찾을 수 없습니다.'}, 
                      status=status.HTTP_404_NOT_FOUND)

# username으로 회원 프로필 페이지 추적
@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_by_username(request, username):
    try:
        user = User.objects.get(username=username)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': '사용자를 찾을 수 없습니다.'}, 
                      status=status.HTTP_404_NOT_FOUND)
        
# 온보딩
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def onboarding_status(request):
    """현재 온보딩 진행 상황 조회"""
    try:
        step = OnboardingStep.objects.get(user=request.user)
        return Response(
            {
                'current_step': step.current_step,
                'step_data': step.step_data,
                'completed': request.user.onboarding_completed,
            }
        )
    except OnboardingStep.DoesNotExist:
        # 첫 온보딩 시작
        step = OnboardingStep.objects.create(user=request.user)
        return Response(
            {
                'current_step': step.current_step,
                'step_data': step.step_data,
                'completed': False,
            }
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_famous_movies(request):
    """1단계: 유명한 영화들 제공"""
    famous_movies = OnboardingMovie.objects.filter(
        movie_type='famous', is_active=True
    ).select_related('movie')[:20]

    movies_data = []
    for onboarding_movie in famous_movies:
        movie = onboarding_movie.movie
        movies_data.append(
            {
                'movie_id': movie.id,
                'title': movie.title,
                'poster_path': movie.poster_path,
                'release_date': movie.release_date,
                'overview': (
                    movie.overview[:100] + '...' if movie.overview else ''
                ),
            }
        )

    return Response({'movies': movies_data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_favorite_movies(request):
    """1단계: 재밌게 본 영화들 저장"""
    movie_ids = request.data.get('movie_ids', [])

    if len(movie_ids) < 1 or len(movie_ids) > 10:
        return Response(
            {'error': '1개 이상 10개 이하로 선택해주세요.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        # 기존 선호도 삭제
        UserMoviePreference.objects.filter(
            user=request.user, preference_type='favorite'
        ).delete()

        # 새로운 선호도 저장
        for movie_id in movie_ids:
            try:
                movie = Movie.objects.get(id=movie_id)
                UserMoviePreference.objects.create(
                    user=request.user, movie=movie, preference_type='favorite'
                )
            except Movie.DoesNotExist:
                continue

        # 진행 상황 업데이트
        step, created = OnboardingStep.objects.get_or_create(user=request.user)
        step.current_step = 'interesting_movies'
        step.step_data['favorite_movies'] = movie_ids
        step.save()

    return Response({'message': '재밌게 본 영화가 저장되었습니다.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_hidden_movies(request):
    """2단계: 숨겨진 영화들 제공"""
    hidden_movies = OnboardingMovie.objects.filter(
        movie_type='hidden', is_active=True
    ).select_related('movie')[:20]

    movies_data = []
    for onboarding_movie in hidden_movies:
        movie = onboarding_movie.movie
        movies_data.append(
            {
                'movie_id': movie.id,
                'title': movie.title,
                'poster_path': movie.poster_path,
                'release_date': movie.release_date,
                'overview': (
                    movie.overview[:100] + '...' if movie.overview else ''
                ),
            }
        )

    return Response({'movies': movies_data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_interesting_movies(request):
    """2단계: 관심있는 영화들 저장"""
    movie_ids = request.data.get('movie_ids', [])

    if len(movie_ids) < 1 or len(movie_ids) > 10:
        return Response(
            {'error': '1개 이상 10개 이하로 선택해주세요.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        # 기존 선호도 삭제
        UserMoviePreference.objects.filter(
            user=request.user, preference_type='interesting'
        ).delete()

        # 새로운 선호도 저장
        for movie_id in movie_ids:
            try:
                movie = Movie.objects.get(id=movie_id)
                UserMoviePreference.objects.create(
                    user=request.user,
                    movie=movie,
                    preference_type='interesting',
                )
            except Movie.DoesNotExist:
                continue

        # 진행 상황 업데이트
        step, created = OnboardingStep.objects.get_or_create(user=request.user)
        step.current_step = 'exclude_genres'
        step.step_data['interesting_movies'] = movie_ids
        step.save()

    return Response({'message': '관심있는 영화가 저장되었습니다.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_genres(request):
    """3단계: 전체 장르 목록 제공"""
    genres = Genre.objects.all()
    genres_data = [
        {'genre_id': genre.id, 'genre_name': genre.name} for genre in genres
    ]
    return Response({'genres': genres_data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_excluded_genres(request):
    """3단계: 제외할 장르 저장"""
    genre_ids = request.data.get('genre_ids', [])

    with transaction.atomic():
        # 기존 제외 장르 삭제
        UserGenreExclusion.objects.filter(user=request.user).delete()

        # 새로운 제외 장르 저장
        for genre_id in genre_ids:
            try:
                genre = Genre.objects.get(id=genre_id)
                UserGenreExclusion.objects.create(
                    user=request.user, genre=genre
                )
            except Genre.DoesNotExist:
                continue

        # 진행 상황 업데이트
        step = OnboardingStep.objects.get(user=request.user)
        step.current_step = 'gpt_analysis'
        step.step_data['excluded_genres'] = genre_ids
        step.save()

    return Response({'message': '제외할 장르가 저장되었습니다.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_random_movie_during_analysis(request):  # GPT 분석 중 보여줄 랜덤 영화
    random_movie = Movie.objects.order_by('?').first()

    if random_movie:
        return Response(
            {
                'movie_id': random_movie.id,
                'title': random_movie.title,
                'poster_path': random_movie.poster_path,
                'backdrop_path': random_movie.backdrop_path,
            }
        )
    return Response({'movie': None})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_gpt_recommendations(request):
   """4단계: GPT를 통한 개인화 추천 생성"""
   user = request.user

   # 사용자 선호 데이터 수집
   favorite_movies = UserMoviePreference.objects.filter(
       user=user, preference_type='favorite'
   ).select_related('movie')

   interesting_movies = UserMoviePreference.objects.filter(
       user=user, preference_type='interesting'
   ).select_related('movie')

   excluded_genres = UserGenreExclusion.objects.filter(
       user=user
   ).select_related('genre')

   try:
       # GPT 서비스 초기화 및 추천 생성
       gpt_service = GPTRecommendationService()
       gpt_response = gpt_service.generate_recommendations(
           user, favorite_movies, interesting_movies, excluded_genres
       )

       # GPT 추천 결과 저장 (기존 것이 있으면 업데이트)
       with transaction.atomic():
           # get_or_create 대신 명시적으로 처리
           try:
               recommendation = GPTRecommendation.objects.get(user=user)
               # 기존 추천이 있으면 업데이트
               recommendation.taste_summary = gpt_response['taste_summary']
               recommendation.save()
               
               # 기존 추천 영화들 삭제
               GPTRecommendedMovie.objects.filter(
                   recommendation=recommendation
               ).delete()
               
           except GPTRecommendation.DoesNotExist:
               # 새로 생성
               recommendation = GPTRecommendation.objects.create(
                   user=user,
                   taste_summary=gpt_response['taste_summary']
               )

           # 새로운 추천 영화들 저장 - 중복 체크 추가
           saved_movie_ids = set()  # 중복 방지를 위한 set
           for i, movie_rec in enumerate(gpt_response['movies'], 1):
               try:
                   movie = Movie.objects.get(id=movie_rec['movie_id'])
                   
                   # 이미 저장된 영화인지 확인
                   if movie.id in saved_movie_ids:
                       print(f"⚠️ 중복된 영화 스킵: {movie.title} (ID: {movie.id})")
                       continue
                       
                   # 혹시나 DB에 이미 존재하는지도 체크
                   if GPTRecommendedMovie.objects.filter(
                       recommendation=recommendation, 
                       movie=movie
                   ).exists():
                       print(f"⚠️ DB에 이미 존재하는 영화 스킵: {movie.title}")
                       continue
                   
                   GPTRecommendedMovie.objects.create(
                       recommendation=recommendation,
                       movie=movie,
                       reason=movie_rec['reason'],
                       recommendation_order=i,
                       target_age=movie_rec['target_age'],
                   )
                   saved_movie_ids.add(movie.id)
                   
               except Movie.DoesNotExist:
                   print(f"⚠️ 존재하지 않는 영화 ID: {movie_rec['movie_id']}")
                   continue

           # 온보딩 완료 처리
           step = OnboardingStep.objects.get(user=user)
           step.current_step = 'completed'
           step.save()

           user.onboarding_completed = True
           user.taste_analysis = gpt_response['taste_summary']
           user.save()

       return Response(
           {
               'message': '개인화 추천이 완료되었습니다.',
               'taste_summary': gpt_response['taste_summary'],
               'recommended_movies': gpt_response['movies'],
           }
       )

   except Exception as e:
       print(f"❌ GPT 추천 생성 오류: {str(e)}")  # 디버깅용
       return Response(
           {'error': f'추천 생성 중 오류가 발생했습니다: {str(e)}'},
           status=status.HTTP_500_INTERNAL_SERVER_ERROR,
       )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_recommendations(request):
   """추천 결과 재생성"""
   user = request.user

   # 기존 추천이 있는지 확인
   if not GPTRecommendation.objects.filter(user=user).exists():
       return Response(
           {
               'error': '이전 추천 결과가 없습니다. 먼저 온보딩을 완료해주세요.'
           },
           status=status.HTTP_400_BAD_REQUEST,
       )

   # 사용자 선호 데이터 수집
   favorite_movies = UserMoviePreference.objects.filter(
       user=user, preference_type='favorite'
   ).select_related('movie')

   interesting_movies = UserMoviePreference.objects.filter(
       user=user, preference_type='interesting'
   ).select_related('movie')

   excluded_genres = UserGenreExclusion.objects.filter(
       user=user
   ).select_related('genre')

   try:
       # GPT 서비스 초기화 및 추천 재생성
       gpt_service = GPTRecommendationService()
       gpt_response = gpt_service.generate_recommendations(
           user, favorite_movies, interesting_movies, excluded_genres
       )

       # 기존 추천 결과 업데이트
       with transaction.atomic():
           recommendation = GPTRecommendation.objects.get(user=user)
           recommendation.taste_summary = gpt_response['taste_summary']
           recommendation.save()

           # 기존 추천 영화들 삭제
           GPTRecommendedMovie.objects.filter(
               recommendation=recommendation
           ).delete()

           # 새로운 추천 영화들 저장 - 중복 체크 추가
           saved_movie_ids = set()  # 중복 방지를 위한 set
           for i, movie_rec in enumerate(gpt_response['movies'], 1):
               try:
                   movie = Movie.objects.get(id=movie_rec['movie_id'])
                   
                   # 이미 저장된 영화인지 확인
                   if movie.id in saved_movie_ids:
                       print(f"⚠️ 중복된 영화 스킵: {movie.title} (ID: {movie.id})")
                       continue
                       
                   # 혹시나 DB에 이미 존재하는지도 체크
                   if GPTRecommendedMovie.objects.filter(
                       recommendation=recommendation, 
                       movie=movie
                   ).exists():
                       print(f"⚠️ DB에 이미 존재하는 영화 스킵: {movie.title}")
                       continue
                   
                   GPTRecommendedMovie.objects.create(
                       recommendation=recommendation,
                       movie=movie,
                       reason=movie_rec['reason'],
                       recommendation_order=i,
                       target_age=movie_rec['target_age'],
                   )
                   saved_movie_ids.add(movie.id)
                   
               except Movie.DoesNotExist:
                   print(f"⚠️ 존재하지 않는 영화 ID: {movie_rec['movie_id']}")
                   continue

           # 사용자 취향 분석 업데이트
           user.taste_analysis = gpt_response['taste_summary']
           user.save()

       return Response(
           {
               'message': '추천이 재생성되었습니다.',
               'taste_summary': gpt_response['taste_summary'],
               'recommended_movies': gpt_response['movies'],
           }
       )

   except Exception as e:
       return Response(
           {'error': f'추천 재생성 중 오류가 발생했습니다: {str(e)}'},
           status=status.HTTP_500_INTERNAL_SERVER_ERROR,
       )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_recommendations(request):
    """사용자의 GPT 추천 결과 조회"""
    try:
        recommendation = GPTRecommendation.objects.get(user=request.user)

        # 추천 영화들 가져오기
        recommended_movies = (
            GPTRecommendedMovie.objects.filter(recommendation=recommendation)
            .select_related('movie')
            .order_by('recommendation_order')
        )

        movies_data = []
        for rec_movie in recommended_movies:
            movie = rec_movie.movie
            movies_data.append(
                {
                    'movie_id': movie.id,
                    'title': movie.title,
                    'poster_path': movie.poster_path,
                    'release_date': movie.release_date,
                    'overview': movie.overview,
                    'reason': rec_movie.reason,
                    'target_age': rec_movie.target_age,
                    'recommendation_order': rec_movie.recommendation_order,
                }
            )

        return Response(
            {
                'taste_summary': recommendation.taste_summary,
                'recommended_movies': movies_data,
                'created_at': recommendation.created_at,
                'updated_at': recommendation.updated_at,
            }
        )

    except GPTRecommendation.DoesNotExist:
        return Response(
            {'error': '아직 추천 결과가 없습니다. 온보딩을 완료해주세요.'},
            status=status.HTTP_404_NOT_FOUND,
        )
