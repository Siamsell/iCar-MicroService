from rest_framework import serializers
from .models import Notification, UserFollowPost, UserFollowUser,UserModel,VehiculeModel

class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = '__all__'
        
class VehiculeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehiculeModel
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.user:
            data['user'] = clean_user_data(UserModelSerializer(instance.user).data)
        else:
            data['user'] = None

        return data

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = ['id', 'user', 'subject', 'message', 'is_read', 'post', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserFollowPostSerializer(serializers.ModelSerializer):

    class Meta:
        model  = UserFollowPost
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.post:
            data['post'] = VehiculeModelSerializer(instance.post).data
        else:
            data['post'] = None

        return data


def clean_user_data(data):
    data.pop('role', None)
    data.pop('date_joined', None)
    data.pop('email', None)
    data.pop('number', None)
    return data

class UserFollowUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFollowUser
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['follower'] = clean_user_data(UserModelSerializer(instance.follower).data)
        data['following'] = clean_user_data(UserModelSerializer(instance.following).data)

        return data

