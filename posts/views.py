from rest_framework.decorators import api_view
from .serializer import PostSerializer, PostListSerializer, CommentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Post

# 페이지네이션 설정 필요 -> 한 번에 몇 개 보일건지
@api_view(['GET'])
def post_list(request):
    """
    포스트 목록 조회 API - 최신순 정렬
    """
    posts = Post.objects.select_related('user').prefetch_related('tags').order_by('-created_at')
    serializer = PostListSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def post_detail(request, post_id):
    """
    포스트 상세 조회 API
    """
    try:
        post = Post.objects.select_related('user').prefetch_related(
            'tags', 
            'like_users',
            'comment_set__user',  # 댓글과 댓글 작성자
            'comment_set__replies__user'  # 대댓글과 대댓글 작성자
        ).get(id=post_id)
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data)
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
            serializer.save(post=post, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Post.DoesNotExist:
        return Response(
            {'error': '포스트를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )