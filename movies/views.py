from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import ActorReview, DirectorReview, Movie, Actor, Director, MovieReview
from .serializer import DirectorBasicSerializer, MovieReviewSerializer, MovieSerializer, ActorSerializer, DirectorSerializer, MovieListSerializer, ActorBasicSerializer, ActorReviewSerializer, DirectorReviewSerializer
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
        
        return Response({
            'review': MovieReviewSerializer(review).data,
            'message': '리뷰가 등록되었습니다.',
        })
        
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
        
        return Response({
            'review': ActorReviewSerializer(review).data if Actor.objects.filter(actor_id=person_id).exists() else DirectorReviewSerializer(review).data,
            'message': '사람 리뷰가 등록되었습니다.',
        })
        
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
        