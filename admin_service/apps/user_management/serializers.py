from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserActivity


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'first_name', 'last_name',
            'permission_level', 'status', 'container_id', 'container_status',
            'cpu_limit', 'memory_limit', 'storage_limit',
            'created_at', 'updated_at', 'last_login_at',
            'password', 'confirm_password'
        ]
        read_only_fields = ['id', 'container_id', 'container_status', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        if 'password' in attrs and 'confirm_password' in attrs:
            if attrs['password'] != attrs['confirm_password']:
                raise serializers.ValidationError("密码确认不匹配")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """用户列表序列化器"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'permission_level', 'status',
            'container_status', 'created_at', 'last_login_at'
        ]


class UserActivitySerializer(serializers.ModelSerializer):
    """用户活动序列化器"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_username', 'action', 'description',
            'ip_address', 'user_agent', 'created_at'
        ]


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('用户名或密码错误')
            if not user.is_active:
                raise serializers.ValidationError('用户账户已被禁用')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('必须提供用户名和密码')
        
        return attrs
