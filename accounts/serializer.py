from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from dj_rest_auth.registration.serializers import RegisterSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    주요 기능:
    1. 회원가입 시 사용자 정보 검증
    2. 사용자 정보 수정
    3. 사용자 정보 조회
    4. 회원 탈퇴
    """
    # 필수 입력 필드 정의
    username = serializers.CharField(required=True)  # 사용자 아이디
    password1 = serializers.CharField(write_only=True, required=True)  # 비밀번호 (읽기 전용)
    password2 = serializers.CharField(write_only=True, required=True)  # 비밀번호 확인 (읽기 전용)
    birth = serializers.DateField(required=True)  # 생년월일
    profile_image = serializers.ImageField(required=False)  # 프로필 이미지 
    profile_image_url = serializers.SerializerMethodField()  # 프로필 이미지 URL
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'password1', 'password2', 'birth', 'profile_image', 'profile_image_url', 'followers_count', 'following_count', 'is_following']
        read_only_fields = ['id']
        
    def get_profile_image_url(self, obj):
        """
        프로필 이미지 URL 반환
        """
        if obj.profile_image:
            return obj.profile_image.url
        return '/media/profile_images/default.jpg'
    
    def to_representation(self, instance):
        """
        사용자 정보 조회 시 비밀번호 필드 제외
        """
        ret = super().to_representation(instance)
        # password1, password2는 write_only이므로 조회 시 자동으로 제외됨
        return ret

    def validate_username(self, value):
        """
        username 중복 검사
        이미 존재하는 username인 경우 ValidationError 발생
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 사용 중인 아이디입니다.")
        return value
    
    def validate_password1(self, value):  # validate_password → validate_password1
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def validate(self, data):
        # password1, password2가 둘 다 있을 때만 검증
        password1 = data.get('password1')
        password2 = data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        elif password1 or password2:  # 둘 중 하나만 있으면 에러
            raise serializers.ValidationError("비밀번호를 변경하려면 password1과 password2를 모두 입력해주세요.")
        
        return data

    def create(self, validated_data):
        try:
            password = validated_data.pop('password1')
            validated_data.pop('password2')
            user = User.objects.create_user(
                username=validated_data['username'],
                password=password,
                birth=validated_data['birth']
            )
            return user
        except Exception as e:
            raise serializers.ValidationError("사용자 생성 중 오류가 발생했습니다.")
    
    def update(self, instance, validated_data):
        """
        사용자 정보 수정
        username, birth, password1, password2, profile_image 모두 처리
        """
        try:
            # 비밀번호 변경 처리
            password1 = validated_data.pop('password1', None)
            password2 = validated_data.pop('password2', None)
            if password1 and password2:
                if password1 != password2:
                    raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
                instance.set_password(password1)

            # username, birth, profile_image 변경 처리
            instance.username = validated_data.get('username', instance.username)
            instance.birth = validated_data.get('birth', instance.birth)
            
            # 프로필 이미지 처리
            profile_image = validated_data.get('profile_image', None)
            if profile_image is not None:
                instance.profile_image = profile_image
            
            instance.save()
            return instance
        except Exception as e:
            raise serializers.ValidationError("사용자 정보 수정 중 오류가 발생했습니다.")
    
    def delete(self, instance):
        """
        사용자 계정 삭제
        """
        try:
            instance.delete()
            return instance
        except Exception as e:
            raise serializers.ValidationError("사용자 삭제 중 오류가 발생했습니다.")
    
    def get_user_info(self, instance):
        """
        사용자 정보 조회
        민감한 정보를 제외한 기본 정보만 반환
        """
        return {
            'id': instance.id,
            'username': instance.username,
            'birth': instance.birth
        }
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(follower=request.user).exists()
        return False


class CustomRegisterSerializer(RegisterSerializer):
    """
    dj-rest-auth 회원가입을 위한 커스텀 시리얼라이저
    birth 필드를 추가하여 회원가입 시 생년월일도 함께 받음
    """
    birth = serializers.DateField(required=True)
    
    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['birth'] = self.validated_data.get('birth', '')
        return data
    
    def save(self, request):
        user = super().save(request)
        user.birth = self.cleaned_data.get('birth')
        user.save()
        return user
        