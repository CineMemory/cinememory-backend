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

    class Meta:
        model = User
        fields = ['id', 'username', 'password1', 'password2', 'birth']
        read_only_fields = ['id']
        
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
        validate_password(value)
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
        password = validated_data.pop('password1')
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            password=password,
            birth=validated_data['birth']
        )
        return user
    
    def update(self, instance, validated_data):
        """
        사용자 정보 수정
        username, birth, password1, password2 모두 처리
        """
        # 비밀번호 변경 처리
        password1 = validated_data.pop('password1', None)
        password2 = validated_data.pop('password2', None)
        if password1 and password2:
            if password1 != password2:
                raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
            instance.set_password(password1)

        # username, birth 변경 처리
        instance.username = validated_data.get('username', instance.username)
        instance.birth = validated_data.get('birth', instance.birth)
        instance.save()
        return instance
    
    def delete(self, instance):
        """
        사용자 계정 삭제
        """
        instance.delete()
        return instance
    
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
        