from rest_framework.decorators import api_view
from .serializer import PostSerializer, PostListSerializer, CommentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Post, Comment

# 페이지네이션 설정 필요 -> 한 번에 몇 개 보일건지
@api_view(['GET'])
@permission_classes([])  # 인증 불필요 명시
def post_list(request):
    """
    포스트 목록 조회 API - 최신순 정렬
    """
    posts = Post.objects.select_related('user').prefetch_related('tags').order_by('-created_at')
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
            serializer.save(post=post, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
def create_reply(request, post_id, comment_id):
    """
    대댓글 생성 API
    /api/v1/cinememory/community/post/{post_id}/comments/{comment_id}/replies
    """
    try:
        # 포스트 존재 확인
        post = Post.objects.get(id=post_id)
        
        # 부모 댓글 존재 확인 (해당 포스트의 댓글인지도 확인)
        parent_comment = Comment.objects.get(id=comment_id, post=post)
        
        # 대댓글은 최상위 댓글에만 달 수 있도록 제한 (선택사항)
        if parent_comment.parent is not None:
            return Response(
                {'error': '대댓글에는 답글을 달 수 없습니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(post=post, user=request.user, parent=parent_comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
    # try:
    #     post = Post.objects.get(id=post_id)
    #     if post.like_users.filter(id=request.user.id).exists():
    #         post.like_users.remove(request.user)
    #         return Response(
    #             {'message': '좋아요가 취소되었습니다.'}, 
    #             status=status.HTTP_204_NO_CONTENT
    #         )
    #     else:
    #         post.like_users.add(request.user)
    #         return Response(
    #             {'message': '좋아요가 추가되었습니다.'}, 
    #             status=status.HTTP_201_CREATED
    #         )
    # except Post.DoesNotExist:
    #     return Response(
    #         {'error': '포스트를 찾을 수 없습니다.'}, 
    #         status=status.HTTP_404_NOT_FOUND
    #     )
    
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