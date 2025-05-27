from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializer import MyPageSerializer, UserSerializer

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
    """
    특정 사용자 프로필 조회 API
    """
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_page(request):
    user = request.user
    serializer = MyPageSerializer(user)
    return Response(serializer.data)    