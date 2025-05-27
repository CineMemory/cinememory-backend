from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Movie, Actor, Director, MovieReview, MovieProvider, Provider
from .serializer import DirectorBasicSerializer, MovieReviewSerializer, MovieSerializer, ActorSerializer, DirectorSerializer, MovieListSerializer, ActorBasicSerializer, MovieProviderSerializer
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


# Create your views here.
@api_view(['GET'])
def movie_detail(request, id):
    print(f'요청된 movie_id: {id}')
    try:
        movie = Movie.objects.get(id=id)
        print(f'영화 찾음: {movie.title}')

        # 관계 데이터를 효율적으로 가져오기 위한 최적화
        movie = Movie.objects.select_related('series').prefetch_related(
            'genres', 'directors', 'actors', 'liked_by'
        ).get(id=id)
        
        serializer = MovieSerializer(movie)
        return Response(serializer.data)
    except Exception as e:
        print(f'에러 발생: {e}')
        raise
    
        
@api_view(['GET'])
def person_detail(request, person_id):
    try:
        # 배우인지 확인
        if Actor.objects.filter(id=person_id).exists():
            person = Actor.objects.prefetch_related('movies').get(id=person_id)
            serializer = ActorSerializer(person)
            return Response(serializer.data)
        # 감독인지 확인
        elif Director.objects.filter(id=person_id).exists():
            person = Director.objects.prefetch_related('movies').get(id=person_id)
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
            return Response({'error': '검색 결과를 찾을 수 없습니다.'}, status=204)
        
        return Response(results)
        
    except Exception as e:
        return Response({'error': '검색 중 오류가 발생했습니다.'}, status=500)
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_movie(request, movie_id):
    try:
        movie = Movie.objects.get(id=movie_id)
        content = request.data.get('content', '')
        rating = request.data.get('rating', 0)
        
        if not content:
            return Response({'error': '리뷰 내용을 입력해주세요.'}, status=400)

        if not (0 <= float(rating) <=5):
            return Response({'error': '별점은 0~5점 사이여야 합니다.'}, status=400) 
        
        # MovieReview 모델 사용
        review, created = MovieReview.objects.get_or_create(
            user=request.user,
            movie=movie,
            defaults={'content': content, 'rating': rating}
        )
        
        if not created:
            review.content = content
            review.rating = rating
            review.save()
        
        # 리뷰 사용자 목록에 추가
        movie.reviewed_by.add(request.user)
        
        return Response({
            'review': MovieReviewSerializer(review).data,
        })
        
    except Movie.DoesNotExist:
        return Response({'error': '영화를 찾을 수 없습니다.'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_movie(request, movie_id):
    try:
        movie = Movie.objects.get(id=movie_id)
        is_liked_before = movie.liked_by.filter(id=request.user.id).exists()
        
        if is_liked_before:
            movie.liked_by.remove(request.user)
            is_liked_after = False
            message = '좋아요가 취소되었습니다.'
        else:
            movie.liked_by.add(request.user)
            is_liked_after = True
            message = '좋아요가 추가되었습니다.'
            
        like_count = movie.liked_by.count()
        
        return Response({
            'message': message,
            'is_liked': is_liked_after,
            'like_count': like_count,
            'movie_id': movie.id
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
        if Actor.objects.filter(id=person_id).exists():
            person = Actor.objects.get(id=person_id)
            is_liked_before = person.liked_by.filter(id=request.user.id).exists()
        elif Director.objects.filter(id=person_id).exists():
            person = Director.objects.get(id=person_id)
            is_liked_before = person.liked_by.filter(id=request.user.id).exists()
        else:
            return Response(
                {'error': '사람을 찾을 수 없습니다.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        if is_liked_before:
            person.liked_by.remove(request.user)
            is_liked_after = False
            message = '좋아요가 취소되었습니다.'
        else:
            person.liked_by.add(request.user)
            is_liked_after = True
            message = '좋아요가 추가되었습니다.'
            
        like_count = person.liked_by.count()
        
        return Response({
            'message': message,
            'is_liked': is_liked_after,
            'like_count': like_count,
            'person_id': person.id
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
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_liked_movies(request):
    """사용자가 좋아요한 영화 목록"""
    try:
        liked_movies = request.user.liked_movies.all()
        serializer = MovieListSerializer(liked_movies, many=True)
        return Response({
            'liked_movies': serializer.data,
            'count': liked_movies.count()
        })
    except Exception as e:
        return Response({'error': '데이터를 불러올 수 없습니다.'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_reviews(request):
    """사용자가 작성한 리뷰 목록"""
    try:
        movie_reviews = MovieReview.objects.filter(user=request.user).select_related('movie').order_by('-created_at')
        serializer = MovieReviewSerializer(movie_reviews, many=True)
        return Response({
            'reviews': serializer.data,
            'count': movie_reviews.count()
        })
    except Exception as e:
        return Response({'error': '데이터를 불러올 수 없습니다.'}, status=500)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_liked_actors(request):
    """사용자가 좋아요한 배우 목록"""
    try:
        liked_actors = request.user.liked_actors.all()
        serializer = ActorBasicSerializer(liked_actors, many=True)
        return Response({
            'liked_actors': serializer.data,
            'count': liked_actors.count()
        })
    except Exception as e:
        return Response({'error': '데이터를 불러올 수 없습니다.'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_liked_directors(request):
    """사용자가 좋아요한 감독 목록"""
    try:
        liked_directors = request.user.liked_directors.all()
        serializer = DirectorBasicSerializer(liked_directors, many=True)
        return Response({
            'liked_directors': serializer.data,
            'count': liked_directors.count()
        })
    except Exception as e:
        return Response({'error': '데이터를 불러올 수 없습니다.'}, status=500)