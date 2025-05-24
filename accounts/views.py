from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework import status
from accounts.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializer import UserSerializer

# Create your views here.
"""
필수 항목
username -> 중복 확인
password -> 조건 확인 (조건 미정)
birth -> 생년월일 전부
"""

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """
    회원가입 API
    - username: 사용자 아이디 (중복 불가)
    - password: 비밀번호 (Django 기본 비밀번호 유효성 검사 적용)
    - password_confirm: 비밀번호 확인
    - birth: 생년월일
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': '회원가입이 완료되었습니다.',
            'user': {
                'id': user.id,
                'username': user.username
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 유저네임 중복 확인
def is_duplicate_username(username):
    return User.objects.filter(username=username).exists()

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def login(request):
#     """
#     로그인 API
#     - username: 사용자 아이디
#     - password: 비밀번호
#     """
#     username = request.data.get('username')
#     password = request.data.get('password')

#     if not username or not password:
#         return Response({
#             'error': '아이디와 비밀번호를 모두 입력해주세요.'
#         }, status=status.HTTP_400_BAD_REQUEST)

#     user = authenticate(request, username=username, password=password)
#     if user is not None:
#         auth_login(request, user)
#         return Response({
#             'message': '로그인되었습니다.',
#             'user': {
#                 'id': user.id,
#                 'username': user.username
#             }
#         })
#     return Response({
#         'error': '아이디 또는 비밀번호가 일치하지 않습니다.'
#     }, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def logout(request):
#     """
#     로그아웃 API
#     """
#     auth_logout(request)
#     return Response({'message': '로그아웃되었습니다.'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_info(request):
    """
    현재 로그인한 사용자 정보 조회 API
    """
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request, user_id):
    """
    특정 사용자의 프로필 정보 조회 API
    """
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({'error': '사용자를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request):
    """
    사용자 정보 수정 API
    - username: 변경할 아이디 (선택)
    - birth: 변경할 생년월일 (선택)
    """
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': '정보가 수정되었습니다.',
            'user': serializer.data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request):
    """
    회원 탈퇴 API
    """
    user = request.user
    user.delete()
    return Response({'message': '회원 탈퇴가 완료되었습니다.'})