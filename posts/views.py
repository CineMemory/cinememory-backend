from rest_framework.decorators import api_view
from .serializer import PostSerializer, PostListSerializer
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    if request.method == 'POST':
        serializer = PostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)