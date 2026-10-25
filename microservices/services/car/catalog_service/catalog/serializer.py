from rest_framework import serializers
from .models import CategorieModel, SubCategorieModel, VehiculeModel, VehiculeImage,UserModel
from django.db import transaction




class VehiculeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehiculeImage
        fields = ['id', 'image','image_url', 'uploaded_at', 'is_primary']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('image', None)
        return representation
        
class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = '__all__'


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieModel
        fields = '__all__'

        
class SubCategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategorieModel
        fields = '__all__'


class VehiculeSerializer(serializers.ModelSerializer):
    images = VehiculeImageSerializer(many=True, read_only=True)
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = VehiculeModel
        fields = '__all__'
    
    def get_category(self, obj):
        return {
            'id': obj.category.id,
            'name': obj.category.name
        }
    def get_subcategory(self, obj):
        return {
            'id': obj.subcategory.id,
            'name': obj.subcategory.name
        }

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'name': obj.user.name
        }
        


class VehiculeCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False),
        write_only=True,
        required=True,
        min_length=1,
        max_length=15
    )
    primary_image_index = serializers.IntegerField(
        write_only=True, 
        required=False, 
        allow_null=True,
        min_value=0
    )
    
    class Meta:
        model = VehiculeModel
        fields = [
            'id', 'name', 'brand', 'subcategory', 'year', 'status',
            'description', 'phone', 'location', 'milage', 'coleur',
            'fuel', 'transmissionType', 'images', 'primary_image_index','user_id'
        ]
    
    @transaction.atomic
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        primary_index = validated_data.pop('primary_image_index', None)
        
        vehicle = VehiculeModel.objects.create(**validated_data)
        
        try:
            for index, image_data in enumerate(images_data):
                is_primary = (primary_index == index) if primary_index is not None else (index == 0)
                vehicule_image = VehiculeImage.objects.create(
                    vehicle=vehicle,
                    image=image_data,
                    is_primary=is_primary,
                )
                vehicule_image.image_url = "https://oussama-bjm-car.hf.space"+vehicule_image.image.url
                vehicule_image.save()
        except Exception as e:
            for img in vehicle.images.all():
                img.delete()
            raise serializers.ValidationError(f"Error uploading images: {str(e)}")
        
        return vehicle