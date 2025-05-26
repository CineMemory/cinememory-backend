from django.conf import settings
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import ActorReview, DirectorReview, Movie, Actor, Director, MovieReview, PersonalizedTimeline
from .serializer import DirectorBasicSerializer, MovieReviewSerializer, MovieSerializer, ActorSerializer, DirectorSerializer, MovieListSerializer, ActorBasicSerializer, ActorReviewSerializer, DirectorReviewSerializer, PersonalizedTimelineSerializer
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


# Create your views here.
@api_view(['GET'])
def movie_detail(request, movie_id):
    try:
        # 관계 데이터를 효율적으로 가져오기 위한 최적화
        movie = Movie.objects.select_related('series').prefetch_related(
            'genres', 'directors', 'actors', 'like_users'
        ).get(movie_id=movie_id)
        
        serializer = MovieSerializer(movie)
        return Response(serializer.data)
    except Movie.DoesNotExist:
        return Response(
            {'error': '영화를 찾을 수 없습니다.'}, 
            status=404
        )
        
@api_view(['GET'])
def person_detail(request, person_id):
    try:
        # 배우인지 확인
        if Actor.objects.filter(actor_id=person_id).exists():
            person = Actor.objects.prefetch_related('movies').get(actor_id=person_id)
            serializer = ActorSerializer(person)
            return Response(serializer.data)
        # 감독인지 확인
        elif Director.objects.filter(director_id=person_id).exists():
            person = Director.objects.prefetch_related('movies').get(director_id=person_id)
            serializer = DirectorSerializer(person)
            return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': '사람을 찾을 수 없습니다.'}, 
            status=404
        )

@api_view(['GET'])
def search_some(request):
    search_query = request.GET.get('search', '')
    
    if not search_query:
        return Response({'message': '검색어를 입력해주세요.'}, status=400)
    
    try:
        results = {
            'movies': [],
            'actors': [],
            'directors': []
        }
        
        # 모든 카테고리에서 검색
        movies = Movie.objects.filter(title__icontains=search_query)[:10]
        actors = Actor.objects.filter(name__icontains=search_query)[:10]
        directors = Director.objects.filter(name__icontains=search_query)[:10]
        
        if movies:
            results['movies'] = MovieListSerializer(movies, many=True).data
        if actors:
            results['actors'] = ActorBasicSerializer(actors, many=True).data
        if directors:
            results['directors'] = DirectorBasicSerializer(directors, many=True).data
        
        # 결과가 하나도 없을 때만 404
        if not any([movies, actors, directors]):
            return Response({'error': '검색 결과를 찾을 수 없습니다.'}, status=404)
        
        return Response(results)
        
    except Exception as e:
        return Response({'error': '검색 중 오류가 발생했습니다.'}, status=500)
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_movie(request, movie_id):
    try:
        movie = Movie.objects.get(movie_id=movie_id)
        content = request.data.get('content', '')
        
        if not content:
            return Response({'error': '리뷰 내용을 입력해주세요.'}, status=400)
        
        # MovieReview 모델 사용
        review, created = MovieReview.objects.get_or_create(
            user=request.user,
            movie=movie,
            defaults={'content': content}
        )
        
        if not created:
            review.content = content
            review.save()
        
        # 리뷰 사용자 목록에 추가
        movie.review_users.add(request.user)
        
        return Response(MovieReviewSerializer(review).data,)
        
    except Movie.DoesNotExist:
        return Response({'error': '영화를 찾을 수 없습니다.'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_person(request, person_id):
    try:
        if Actor.objects.filter(actor_id=person_id).exists():
            person = Actor.objects.get(actor_id=person_id)
            content = request.data.get('content', '')
            review, created = ActorReview.objects.get_or_create(
                user=request.user,
                actor=person,
                defaults={'content': content}
            )
        elif Director.objects.filter(director_id=person_id).exists():
            person = Director.objects.get(director_id=person_id)
            content = request.data.get('content', '')
            review, created = DirectorReview.objects.get_or_create(
                user=request.user,
                director=person,
                defaults={'content': content}
            )
        else:
            return Response({'error': '사람을 찾을 수 없습니다.'}, status=404)
        
        if not created:
            review.content = content
            review.save()
        
        # 리뷰 사용자 목록에 추가
        person.review_users.add(request.user)
        
        return Response(ActorReviewSerializer(review).data if Actor.objects.filter(actor_id=person_id).exists() else DirectorReviewSerializer(review).data)
        
    except (Actor.DoesNotExist, Director.DoesNotExist):
        return Response({'error': '사람을 찾을 수 없습니다.'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_movie(request, movie_id):
    try:
        movie = Movie.objects.get(movie_id=movie_id)
        is_liked_before = movie.like_users.filter(id=request.user.id).exists()
        
        if is_liked_before:
            movie.like_users.remove(request.user)
            is_liked_after = False
            message = '좋아요가 취소되었습니다.'
        else:
            movie.like_users.add(request.user)
            is_liked_after = True
            message = '좋아요가 추가되었습니다.'
            
        like_count = movie.like_users.count()
        
        return Response({
            'message': message,
            'is_liked': is_liked_after,
            'like_count': like_count,
            'movie_id': movie.movie_id
        }, status=status.HTTP_200_OK)
    
    except Movie.DoesNotExist:
        return Response(
            {'error': '영화를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
       

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_person(request, person_id):
    try:
        if Actor.objects.filter(actor_id=person_id).exists():
            person = Actor.objects.get(actor_id=person_id)
            is_liked_before = person.like_users.filter(id=request.user.id).exists()
        elif Director.objects.filter(director_id=person_id).exists():
            person = Director.objects.get(director_id=person_id)
            is_liked_before = person.like_users.filter(id=request.user.id).exists()
        else:
            return Response(
                {'error': '사람을 찾을 수 없습니다.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        if is_liked_before:
            person.like_users.remove(request.user)
            is_liked_after = False
            message = '좋아요가 취소되었습니다.'
        else:
            person.like_users.add(request.user)
            is_liked_after = True
            message = '좋아요가 추가되었습니다.'
            
        like_count = person.like_users.count()
        
        return Response({
            'message': message,
            'is_liked': is_liked_after,
            'like_count': like_count,
            'person_id': person.actor_id if Actor.objects.filter(actor_id=person_id).exists() else person.director_id
        }, status=status.HTTP_200_OK)
    
    except (Actor.DoesNotExist, Director.DoesNotExist):
        return Response(
            {'error': '사람을 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_movie_detail(request, movie_id, review_id):
    try:    
        review = MovieReview.objects.get(id=review_id)
        if review.user != request.user:
            return Response({'error': '리뷰 수정 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            serializer = MovieReviewSerializer(review)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = MovieReviewSerializer(review, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()  # user는 이미 설정되어 있으므로 따로 전달할 필요 없음
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            review.delete()
            return Response({'message': '리뷰가 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT) 
    except MovieReview.DoesNotExist:
        return Response({'error': '리뷰를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_person_detail(request, person_id, review_id):
    try:
        # Actor 리뷰인지 Director 리뷰인지 확인
        if Actor.objects.filter(actor_id=person_id).exists():
            review = ActorReview.objects.get(id=review_id)
            if review.user != request.user:
                return Response({'error': '리뷰 수정 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            
            if request.method == 'GET':
                serializer = ActorReviewSerializer(review)
                return Response(serializer.data)
            elif request.method == 'PUT':
                serializer = ActorReviewSerializer(review, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()  # user는 이미 설정되어 있으므로 따로 전달할 필요 없음
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            elif request.method == 'DELETE':
                review.delete()
                return Response({'message': '리뷰가 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT)
                
        elif Director.objects.filter(director_id=person_id).exists():
            review = DirectorReview.objects.get(id=review_id)
            if review.user != request.user:
                return Response({'error': '리뷰 수정 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            
            if request.method == 'GET':
                serializer = DirectorReviewSerializer(review)
                return Response(serializer.data)
            elif request.method == 'PUT':
                serializer = DirectorReviewSerializer(review, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()  # user는 이미 설정되어 있으므로 따로 전달할 필요 없음
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            elif request.method == 'DELETE':
                review.delete()
                return Response({'message': '리뷰가 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': '사람을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
            
    except (ActorReview.DoesNotExist, DirectorReview.DoesNotExist):
        return Response({'error': '리뷰를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_onboarding_movies(request):
    movies = Movie.objects.filter(
        is_onboarding_movie=True
    ).order_by('onboarding_priority')[:30]
    
    serializer = OnboardingMovieSerializer(movies, many=True)
    return Response(
        {
        'movies': serializer.data,
        'count': movies.count()
    }, status=status.HTTP_200_OK)
    
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_preference(request):
    """사용자 취향 조회/수정"""
    # 사용자 취향 객체 가져오기 또는 생성
    preference, created = UserPreference.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'GET':
        serializer = UserPreferenceSerializer(preference)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = UserPreferenceSerializer(
            preference, 
            data=request.data, 
            partial=(request.method == 'PATCH')
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'preference': serializer.data,
                'message': '취향 정보가 저장되었습니다.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_preferences(request):
    """GPT를 이용한 취향 분석"""
    try:
        user = request.user
        preference = UserPreference.objects.get(user=user)
        
        # 최소 5개 영화 선택 확인
        if preference.selected_movies.count() < 5:
            return Response({
                'error': '최소 5개의 영화를 선택해주세요.',
                'selected_count': preference.selected_movies.count()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 이미 분석된 경우 재분석 여부 확인
        if preference.is_analyzed:
            force_reanalyze = request.data.get('force_reanalyze', False)
            if not force_reanalyze:
                return Response({
                    'message': '이미 분석이 완료되었습니다.',
                    'analysis_result': preference.analysis_result
                }, status=status.HTTP_200_OK)
        
        # 선택된 영화 정보 수집
        selected_movies = preference.selected_movies.all()
        movie_data = []
        
        for movie in selected_movies:
            movie_genres = [genre.genre_name for genre in movie.genres.all()]
            movie_data.append({
                'title': movie.title,
                'release_date': movie.release_date.strftime('%Y-%m-%d'),
                'genres': movie_genres,
                'overview': movie.overview or '',
                'vote_average': movie.vote_average,
                'year': movie.release_date.year
            })
        
        # GPT 분석 요청
        analysis_result = request_gpt_analysis(movie_data, user.birth)
        
        # 분석 결과 저장
        preference.analysis_result = analysis_result
        preference.preferred_genres = analysis_result.get('preferred_genres', [])
        preference.preferred_decades = analysis_result.get('preferred_decades', [])
        preference.storytelling_preference = analysis_result.get('storytelling_preference', '')
        preference.tone_preference = analysis_result.get('tone_preference', '')
        preference.recommendation_keywords = analysis_result.get('recommendation_keywords', [])
        preference.is_analyzed = True
        preference.analyzed_at = timezone.now()
        preference.save()
        
        # 개인화 타임라인 생성
        timeline_created = create_personalized_timeline(user, analysis_result)
        
        return Response({
            'message': '취향 분석이 완료되었습니다.',
            'analysis_result': analysis_result,
            'timeline_created': timeline_created
        }, status=status.HTTP_200_OK)
        
    except UserPreference.DoesNotExist:
        return Response({
            'error': '취향 정보를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'분석 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def request_gpt_analysis(movie_data, user_birth_date):
    """GPT API를 이용한 영화 취향 분석"""
    
    # 영화 정보를 텍스트로 변환
    movies_text = "\n".join([
        f"- {movie['title']} ({movie['year']}) | 장르: {', '.join(movie['genres'])} | 평점: {movie['vote_average']}"
        for movie in movie_data
    ])
    
    # 사용자 현재 나이 계산
    today = date.today()
    age = today.year - user_birth_date.year - ((today.month, today.day) < (user_birth_date.month, user_birth_date.day))
    
    prompt = f"""
사용자가 선택한 영화들을 분석하여 취향을 파악해주세요:

사용자 정보:
- 생년월일: {user_birth_date}
- 현재 나이: {age}세

선택된 영화들:
{movies_text}

다음 JSON 형식으로 정확히 분석 결과를 제공해주세요:
{{
    "preferred_genres": ["장르1", "장르2", "장르3"],
    "preferred_decades": ["1990s", "2000s", "2010s"],
    "storytelling_preference": "액션 중심적 스토리텔링",
    "tone_preference": "진지하고 현실적인 톤",
    "recommendation_keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
    "analysis_summary": "이 사용자는... (100자 이내 요약)"
}}

분석 기준:
1. 장르는 한국어로 표기 (액션, 드라마, 코미디, SF, 로맨스, 스릴러, 호러, 애니메이션 등)
2. 연대는 영어로 표기 (1980s, 1990s, 2000s, 2010s, 2020s)
3. 사용자의 나이를 고려한 맞춤형 분석
4. 선택한 영화들의 공통점과 패턴 파악
"""

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 비용 효율적인 모델 사용
            messages=[
                {
                    "role": "system", 
                    "content": "당신은 영화 전문가이며, 사용자의 영화 취향을 정확히 분석하는 전문가입니다. 반드시 유효한 JSON 형식으로 응답해주세요."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        result_text = response.choices[0].message.content.strip()
        # JSON 파싱 시도
        result = json.loads(result_text)
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        # 기본값 반환
        return create_default_analysis()
    except Exception as e:
        print(f"GPT API 오류: {e}")
        return create_default_analysis()

def create_default_analysis():
    """GPT 분석 실패 시 기본값 반환"""
    return {
        "preferred_genres": ["드라마", "액션", "코미디"],
        "preferred_decades": ["2000s", "2010s"],
        "storytelling_preference": "균형잡힌 스토리텔링",
        "tone_preference": "다양한 톤",
        "recommendation_keywords": ["가족", "우정", "성장", "모험", "사랑"],
        "analysis_summary": "다양한 장르를 선호하는 균형잡힌 취향의 사용자입니다."
    }

def create_personalized_timeline(user, analysis_result):
    """분석 결과를 바탕으로 개인화 타임라인 생성"""
    from datetime import datetime
    
    # 기존 타임라인 삭제
    PersonalizedTimeline.objects.filter(user=user).delete()
    
    # 사용자 생년 및 현재 나이 계산
    birth_year = user.birth.year
    current_year = datetime.now().year
    current_age = current_year - birth_year
    
    preferred_genres = analysis_result.get('preferred_genres', [])
    keywords = analysis_result.get('recommendation_keywords', [])
    
    created_count = 0
    
    # 0세부터 현재 나이까지 각 나이별로 영화 추천
    for age in range(0, current_age + 1):
        year = birth_year + age
        
        # 해당 연도 전후로 개봉한 영화 검색 (±2년 범위)
        year_range_start = year - 2
        year_range_end = year + 2
        
        # 선호 장르와 매칭되는 영화 찾기
        candidate_movies = Movie.objects.filter(
            release_date__year__gte=year_range_start,
            release_date__year__lte=year_range_end,
            genres__genre_name__in=preferred_genres,
            vote_average__gte=6.0  # 최소 평점 6.0 이상
        ).distinct().order_by('-vote_average', '-popularity')[:6]
        
        # 타임라인 생성
        for idx, movie in enumerate(candidate_movies):
            # 취향 매칭 점수 계산
            score = calculate_preference_score(movie, analysis_result)
            
            PersonalizedTimeline.objects.create(
                user=user,
                movie=movie,
                user_age=age,
                year=year,
                recommendation_reason=f"{age}세 때 추천하는 영화입니다.",
                preference_score=score,
                display_order=idx
            )
            created_count += 1
    
    return created_count


def calculate_preference_score(movie, analysis_result):
    """영화와 사용자 취향 간의 매칭 점수 계산 (0-1)"""
    score = 0.0
    
    # 장르 매칭 점수 (50%)
    movie_genres = [genre.genre_name for genre in movie.genres.all()]
    preferred_genres = analysis_result.get('preferred_genres', [])
    
    if preferred_genres:
        genre_matches = len(set(movie_genres) & set(preferred_genres))
        genre_score = genre_matches / len(preferred_genres)
        score += genre_score * 0.5
    
    # 평점 점수 (30%)
    rating_score = movie.vote_average / 10.0
    score += rating_score * 0.3
    
    # 인기도 점수 (20%)
    # 인기도를 0-1 범위로 정규화 (100을 최대값으로 가정)
    popularity_score = min(movie.popularity / 100.0, 1.0)
    score += popularity_score * 0.2
    
    return min(score, 1.0)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_personalized_timeline(request):
    """개인화된 영화 타임라인 조회"""
    timeline = PersonalizedTimeline.objects.filter(
        user=request.user
    ).order_by('user_age', 'display_order')
    
    # 나이별로 그룹화
    timeline_by_age = {}
    for item in timeline:
        age = item.user_age
        if age not in timeline_by_age:
            timeline_by_age[age] = []
        timeline_by_age[age].append(item)
    
    # 시리얼라이저 적용
    result = {}
    for age, movies in timeline_by_age.items():
        serializer = PersonalizedTimelineSerializer(movies, many=True)
        result[str(age)] = serializer.data
    
    return Response({
        'timeline': result,
        'total_ages': len(timeline_by_age),
        'total_movies': timeline.count()
    }, status=status.HTTP_200_OK)
