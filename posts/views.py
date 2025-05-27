from rest_framework.decorators import api_view
from .serializer import PostSerializer, PostListSerializer, CommentSerializer
from .models import Tag
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Post, Comment
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

# 페이지네이션 설정 필요 -> 한 번에 몇 개 보일건지
@api_view(['GET'])
@permission_classes([])  # 인증 불필요 명시
def post_list(request):
    """
    포스트 목록 조회 API - 최신순 정렬
    """
    # 정렬 파라미터 가져오기
    sort_by = request.GET.get('sort', 'latest')
    
    # 기본 쿼리셋
    posts = Post.objects.select_related('user').prefetch_related('tags')
    
    # 정렬 적용
    if sort_by == 'latest':
        posts = posts.order_by('-created_at')
    elif sort_by == 'popular':
        posts = posts.annotate(
            like_count_field=Count('like_users')
        ).order_by('-like_count_field', '-created_at')
    elif sort_by == 'comments':
        posts = posts.annotate(
            comment_count_field=Count('comment')
        ).order_by('-comment_count_field', '-created_at')
    else:
        # 기본값은 최신순
        posts = posts.order_by('-created_at')
    
    serializer = PostListSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['GET', 'PUT', 'DELETE'])
def post_detail(request, post_id):
    """
    포스트 상세 조회 API
    """
    try:
        if request.method == 'GET':
            post = Post.objects.select_related('user').prefetch_related(
                'tags', 
                'like_users',
                'comment_set__user',  # 댓글과 댓글 작성자
                'comment_set__replies__user'  # 대댓글과 대댓글 작성자
            ).get(id=post_id)
            serializer = PostSerializer(post, context={'request': request})
            return Response(serializer.data)
        elif request.method == 'PUT':
            # 인증 확인
            if not request.user.is_authenticated:
                return Response(
                    {'error': '인증이 필요합니다.'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            post = Post.objects.get(id=post_id)
            
            # 작성자만 수정 가능
            if post.user != request.user:
                return Response(
                    {'error': '게시글 수정 권한이 없습니다.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = PostSerializer(post, data=request.data, context={'request': request}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            # 인증 확인
            if not request.user.is_authenticated:
                return Response(
                    {'error': '인증이 필요합니다.'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            post = Post.objects.get(id=post_id)
            
            # 작성자만 삭제 가능
            if post.user != request.user:
                return Response(
                    {'error': '게시글 삭제 권한이 없습니다.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            post.delete()
            return Response(
                {'message': '게시글이 삭제되었습니다.'}, 
                status=status.HTTP_200_OK
            )
    except Post.DoesNotExist:
        return Response(
            {'error': '포스트를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    if request.method == 'POST':
        serializer = PostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save(post=post, user=request.user)
            
            # 작성자 정보를 포함한 응답 생성
            response_data = {
                'message': '댓글이 성공적으로 작성되었습니다.',
                'comment_id': comment.id,
                'content': comment.content,
                'author': request.user.username,
                'user_id': request.user.id,
                'created_at': comment.created_at.isoformat(),
                'updated_at': comment.updated_at.isoformat(),
                'replies': []
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Post.DoesNotExist:
        return Response(
            {'error': '포스트를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def comment_detail(request, post_id, comment_id):
    """
    댓글 개별 조회, 수정, 삭제 API
    """
    try:
        post = Post.objects.get(id=post_id)
        comment = Comment.objects.select_related('user').prefetch_related('replies__user').get(
            id=comment_id, 
            post=post
        )
        
        if request.method == 'GET':
            # 댓글 조회
            serializer = CommentSerializer(comment)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            # 댓글 수정 (작성자만 가능)
            if comment.user != request.user:
                return Response(
                    {'error': '댓글 수정 권한이 없습니다.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = CommentSerializer(comment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # 댓글 삭제 (작성자만 가능)            
            if comment.user != request.user:
                return Response(
                    {'error': '댓글 삭제 권한이 없습니다.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 대댓글이 있는지 확인
            replies_count = comment.replies.count()
            
            comment_id_to_delete = comment.id
            comment.delete()
            
            return Response(
                {'message': '댓글이 삭제되었습니다.'}, 
                status=status.HTTP_200_OK
            )
            
    except Post.DoesNotExist:
        return Response(
            {'error': '포스트를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Comment.DoesNotExist:
        return Response(
            {'error': '댓글을 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_comment_like(request, post_id, comment_id):
    """
    댓글 좋아요 토글 API
    """
    try:
        post = Post.objects.get(id=post_id)
        comment = Comment.objects.get(id=comment_id, post=post)
        
        # 좋아요 상태 확인
        is_liked_before = comment.like_users.filter(id=request.user.id).exists()
        
        if is_liked_before:
            # 좋아요 취소
            comment.like_users.remove(request.user)
            is_liked_after = False
            message = '댓글 좋아요가 취소되었습니다.'
        else:
            # 좋아요 추가
            comment.like_users.add(request.user)
            is_liked_after = True
            message = '댓글 좋아요가 추가되었습니다.'
        
        # 최신 좋아요 수 계산
        like_count = comment.like_users.count()
        
        return Response({
            'message': message,
            'is_liked': is_liked_after,
            'like_count': like_count,
            'comment_id': comment.id
        }, status=status.HTTP_200_OK)
        
    except Post.DoesNotExist:
        return Response(
            {'error': '포스트를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Comment.DoesNotExist:
        return Response(
            {'error': '댓글을 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reply(request, post_id, comment_id):
    try:
        post = Post.objects.get(id=post_id)
        parent_comment = Comment.objects.get(id=comment_id, post=post)
        
        if parent_comment.parent is not None:
            return Response(
                {'error': '대댓글에는 답글을 달 수 없습니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            reply = serializer.save(post=post, user=request.user, parent=parent_comment)
            
            # 작성자 정보를 포함한 응답 생성
            response_data = {
                'message': '답글이 성공적으로 작성되었습니다.',
                'comment_id': reply.id,
                'content': reply.content,
                'author': request.user.username,
                'user_id': request.user.id,
                'created_at': reply.created_at.isoformat(),
                'updated_at': reply.updated_at.isoformat(),
                'parent_id': parent_comment.id
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Post.DoesNotExist:
        return Response(
            {'error': '포스트를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Comment.DoesNotExist:
        return Response(
            {'error': '댓글을 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
        
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def reply_detail(request, post_id, comment_id, reply_id):
    """
    대댓글 개별 조회, 수정, 삭제 API
    """
    try:
        post = Post.objects.get(id=post_id)
        comment = Comment.objects.get(id=comment_id, post=post)
        reply = Comment.objects.get(id=reply_id, post=post, parent=comment)
        
        if request.method == 'GET':
            serializer = CommentSerializer(reply)
            return Response(serializer.data)
            
        elif request.method == 'PUT':
            if reply.user != request.user:
                return Response(
                    {'error': '대댓글 수정 권한이 없습니다.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = CommentSerializer(reply, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            if reply.user != request.user:
                return Response(
                    {'error': '대댓글 삭제 권한이 없습니다.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            reply.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    except Post.DoesNotExist:
        return Response(
            {'error': '포스트를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Comment.DoesNotExist:
        return Response(
            {'error': '댓글을 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_like(request, post_id):
    """
    포스트 좋아요 토글 API
    """

    
    try:
        post = Post.objects.get(id=post_id)
        
        # 좋아요 상태 확인
        is_liked_before = post.like_users.filter(id=request.user.id).exists()
        
        if is_liked_before:
            # 좋아요 취소
            post.like_users.remove(request.user)
            is_liked_after = False
            message = '좋아요가 취소되었습니다.'
        else:
            # 좋아요 추가
            post.like_users.add(request.user)
            is_liked_after = True
            message = '좋아요가 추가되었습니다.'
        
        # 최신 좋아요 수 계산
        like_count = post.like_users.count()
        
        # 일관된 응답 구조 반환
        return Response({
            'message': message,
            'is_liked': is_liked_after,
            'like_count': like_count,
            'post_id': post.id
        }, status=status.HTTP_200_OK)
        
    except Post.DoesNotExist:
        return Response(
            {'error': '포스트를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
        
@api_view(['GET'])
@permission_classes([])
def tag_list(request):
    try:
        tags = Tag.objects.annotate(
            post_count=Count('post')
        ).filter(
            post_count__gt=0
        ).order_by('-post_count', 'name')
        
        # 태그 데이터 직렬화
        tag_data = []
        for tag in tags:
            tag_data.append({
                'id': tag.id,
                'name': tag.name,
                'post_count': tag.post_count
            })
        
        return Response(tag_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': '태그 목록을 불러오는 중 오류가 발생했습니다.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# 특정 태그의 게시글 조회
@api_view(['GET'])
@permission_classes([])  # 인증 불필요
def posts_by_tag(request, tag_name):
    """
    특정 태그가 포함된 게시글 목록 조회 API
    """
    try:
        # 태그 이름으로 태그 찾기
        try:
            tag = Tag.objects.get(name=tag_name)
        except Tag.DoesNotExist:
            return Response(
                {'error': f'"{tag_name}" 태그를 찾을 수 없습니다.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 해당 태그가 포함된 게시글들 조회 (최신순)
        posts = Post.objects.filter(
            tags=tag
        ).select_related('user').prefetch_related('tags', 'like_users').order_by('-created_at')
        
        # PostListSerializer 사용해서 직렬화
        serializer = PostListSerializer(posts, many=True)
        
        # 응답 데이터 구성
        response_data = {
            'tag': {
                'name': tag.name,
                'post_count': posts.count()
            },
            'posts': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': '태그별 게시글을 불러오는 중 오류가 발생했습니다.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

User = get_user_model()

@api_view(['GET'])
@permission_classes([])
def community_stats(request):
    """
    커뮤니티 통계 API
    """
    try:
        # 가입 회원 수
        total_users = User.objects.count()
        
        # 오늘 가입한 회원 수
        today = datetime.now().date()
        today_users = User.objects.filter(date_joined__date=today).count()
        
        # 전체 게시글 수
        total_posts = Post.objects.count()
        
        # 오늘 작성된 게시글 수
        today_posts = Post.objects.filter(created_at__date=today).count()
        
        # 전체 댓글 수
        total_comments = Comment.objects.count()
        
        # 오늘 작성된 댓글 수
        today_comments = Comment.objects.filter(created_at__date=today).count()
        
        # 최신 게시글 5개
        recent_posts = Post.objects.select_related('user').order_by('-created_at')[:5]
        recent_posts_data = []
        for post in recent_posts:
            recent_posts_data.append({
                'id': post.id,
                'title': post.title[:30] + '...' if len(post.title) > 30 else post.title,
                'author': post.user.username,
                'created_at': post.created_at.isoformat(),
                'comment_count': post.comment_set.count(),
                'like_count': post.like_users.count()
            })
        
        # 최신 댓글 5개
        recent_comments = Comment.objects.select_related('user', 'post').order_by('-created_at')[:5]
        recent_comments_data = []
        for comment in recent_comments:
            recent_comments_data.append({
                'id': comment.id,
                'content': comment.content[:50] + '...' if len(comment.content) > 50 else comment.content,
                'author': comment.user.username,
                'post_title': comment.post.title[:20] + '...' if len(comment.post.title) > 20 else comment.post.title,
                'post_id': comment.post.id,
                'created_at': comment.created_at.isoformat()
            })
        
        # 인기 태그 10개 (게시글 수 기준)
        popular_tags = Tag.objects.annotate(
            post_count=Count('post')
        ).filter(post_count__gt=0).order_by('-post_count')[:10]
        
        popular_tags_data = []
        for tag in popular_tags:
            popular_tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'post_count': tag.post_count
            })
        
        # 응답 데이터 구성
        stats_data = {
            'users': {
                'total': total_users,
                'today': today_users
            },
            'posts': {
                'total': total_posts,
                'today': today_posts
            },
            'comments': {
                'total': total_comments,
                'today': today_comments
            },
            'recent_posts': recent_posts_data,
            'recent_comments': recent_comments_data,
            'popular_tags': popular_tags_data,
            'last_updated': datetime.now().isoformat()
        }
        
        return Response({
            'status': 'success',
            'data': stats_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
      return Response(
        { 'error': f'통계 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_posts(request):
    """사용자가 작성한 게시글 목록"""
    try:
        user_posts = Post.objects.filter(user=request.user).select_related('user').prefetch_related('tags', 'like_users').order_by('-created_at')
        serializer = PostListSerializer(user_posts, many=True)
        return Response({
            'posts': serializer.data,
            'count': user_posts.count()
        })
    except Exception as e:
        return Response({'error': '데이터를 불러올 수 없습니다.'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_comments(request):
    """사용자가 작성한 댓글 목록"""
    try:
        user_comments = Comment.objects.filter(user=request.user).select_related('user', 'post').order_by('-created_at')
        
        comments_data = []
        for comment in user_comments:
            comments_data.append({
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at,
                'updated_at': comment.updated_at,
                'like_count': comment.like_users.count(),
                'post': {
                    'id': comment.post.id,
                    'title': comment.post.title,
                    'created_at': comment.post.created_at
                },
                'parent_id': comment.parent.id if comment.parent else None
            })
            
        return Response({
            'comments': comments_data,
            'count': len(comments_data)
        })
    except Exception as e:
        return Response({'error': '데이터를 불러올 수 없습니다.'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_liked_posts(request):
    """사용자가 좋아요한 게시글 목록"""
    try:
        liked_posts = request.user.liked_posts.all().select_related('user').prefetch_related('tags', 'like_users').order_by('-created_at')
        serializer = PostListSerializer(liked_posts, many=True)
        return Response({
            'liked_posts': serializer.data,
            'count': liked_posts.count()
        })
    except Exception as e:
        return Response({'error': '데이터를 불러올 수 없습니다.'}, status=500)  