from rest_framework import serializers
from .models import Post, Comment, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')

class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Comment
        fields = ('id', 'user', 'username', 'content', 'replies', 'created_at', 'updated_at')
        read_only_fields = ('user',)
    
    def get_replies(self, obj):
        # 대댓글들을 가져옴 (parent가 현재 댓글인 것들)
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True).data

class PostListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    like_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ('id', 'title', 'content', 'tags', 'like_count', 'created_at', 'updated_at')
    
    def get_like_count(self, obj):
        return obj.like_users.count()

class PostSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
        help_text="새로운 태그를 생성하거나 기존 태그를 이름으로 연결"
    )
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ('id', 'user', 'title', 'content', 'tags', 'tag_ids', 'tag_names', 'like_count', 'is_liked', 'comments', 'created_at', 'updated_at')
        read_only_fields = ('user', 'like_count', 'is_liked', 'comments')
    
    def get_like_count(self, obj):
        return obj.like_users.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.like_users.filter(id=request.user.id).exists()
        return False
    
    def get_comments(self, obj):
        # 최상위 댓글들만 가져옴 (parent가 None인 것들)
        top_level_comments = obj.comment_set.filter(parent=None).order_by('created_at')
        return CommentSerializer(top_level_comments, many=True).data
    
    def create(self, validated_data):
        from .models import Tag  # Tag 모델 import 추가 필요
        
        # validated_data.pop()은 딕셔너리에서 해당 키의 값을 가져오고 삭제하는 메서드입니다.
        # 두 번째 인자 []는 키가 없을 경우의 기본값입니다.
        # tag_ids와 tag_names는 Post 모델의 직접적인 필드가 아니므로 
        # create() 메서드에서 사용 후 제거해야 합니다.
        tag_ids = validated_data.pop('tag_ids', [])
        tag_names = validated_data.pop('tag_names', [])
        
        post = Post.objects.create(**validated_data)
        
        # 기존 태그 ID로 연결
        if tag_ids:
            post.tags.add(*tag_ids)
        
        # 태그 이름으로 생성/연결
        if tag_names:
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name.strip(),
                    defaults={'name': tag_name.strip()}
                )
                post.tags.add(tag)
        
        return post
    
