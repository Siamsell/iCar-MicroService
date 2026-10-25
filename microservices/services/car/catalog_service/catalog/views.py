from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db import transaction
import os
from .rabbitmq import publish_content_event,publish_vehicle_deleted
from django.conf import settings
from rest_framework.exceptions import PermissionDenied


from .serializer import (
    CategorieSerializer, 
    SubCategorieSerializer, 
    VehiculeSerializer,
    VehiculeCreateSerializer,
    VehiculeImageSerializer,
    UserModelSerializer
)
from .models import CategorieModel, SubCategorieModel, VehiculeModel, VehiculeImage,UserModel
from catalog_service.authentication import IsAuthenticatedStateless


class CategorieViewSet(viewsets.ModelViewSet):
    queryset = CategorieModel.objects.all()
    serializer_class = CategorieSerializer
 
 
class UserModelViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserModelSerializer   
    
class SubCategorieViewSet(viewsets.ModelViewSet):
    queryset = SubCategorieModel.objects.all()
    serializer_class = SubCategorieSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        categorie_id = self.request.query_params.get('categorie_id')

        if categorie_id:
            queryset = queryset.filter(categorie_id=categorie_id)

        return queryset
    


class VehiculeViewSet(viewsets.ModelViewSet):
    queryset = VehiculeModel.objects.all()
    serializer_class = VehiculeSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VehiculeCreateSerializer
        return VehiculeSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy', 'add_image', 'remove_image','post']:
            return [IsAuthenticatedStateless()]
        return []
    
    
    def get_queryset(self):
        if self.action == 'list':
            queryset = VehiculeModel.objects.filter(status=VehiculeModel.Status.ACTIVE)

            # Get all filter parameters from request
            params = self.request.query_params

            # String fields (exact match)
            name = params.get('name')
            brand = params.get('brand')
            subcategory = params.get('subcategory')
            user_id = params.get('user_id')
            category_id = params.get('category')
            coleur = params.get('coleur')
            fuel = params.get('fuel')
            transmissionType = params.get('transmissionType')
            location = params.get('location')

            # Numeric fields with min/max
            year_min = params.get('year_min')
            year_max = params.get('year_max')
            milage_min = params.get('milage_min')
            milage_max = params.get('milage_max')

            # Apply filters
            if name and name.strip():
                queryset = queryset.filter(name__icontains=name)

            if brand and brand.strip():
                queryset = queryset.filter(brand__icontains=brand)

            if subcategory and subcategory.strip():
                queryset = queryset.filter(subcategory_id=subcategory)

            if user_id and user_id.strip():
                queryset = queryset.filter(user_id=user_id)

            if category_id and category_id.strip():
                queryset = queryset.filter(subcategory__categorie_id=category_id)

            if coleur and coleur.strip():
                queryset = queryset.filter(coleur__icontains=coleur)

            if fuel and fuel.strip():
                queryset = queryset.filter(fuel=fuel)

            if transmissionType and transmissionType.strip():
                queryset = queryset.filter(transmissionType=transmissionType)

            if location and location.strip():
                queryset = queryset.filter(location__icontains=location)

            # Year filters
            if year_min and year_min.strip():
                queryset = queryset.filter(year__gte=year_min)

            if year_max and year_max.strip():
                queryset = queryset.filter(year__lte=year_max)

            # Milage filters
            if milage_min and milage_min.strip():
                queryset = queryset.filter(milage__gte=milage_min)

            if milage_max and milage_max.strip():
                queryset = queryset.filter(milage__lte=milage_max)

            return queryset.select_related(
            'subcategory',
            'subcategory__categorie'
            ).prefetch_related('images')

        return VehiculeModel.objects.all().select_related(
        'subcategory',
        'subcategory__categorie'
        ).prefetch_related('images')  
    
    def perform_create(self, serializer):
        if not self.request.user or not self.request.user.id:
                raise PermissionDenied("Authentication required")

        """Save vehicle and send notification if status is not DRAFT"""
        vehicle = serializer.save(user_id=self.request.user.id)
        
        print("notification will be send ...")
        
        if vehicle.status == VehiculeModel.Status.ACTIVE:
            
            vehicule_data = {
            'id': vehicle.id,
            'name': vehicle.name,
            'brand': vehicle.brand,
            'user': vehicle.user_id,
            'status': vehicle.status,
            'created_at': str(vehicle.created_at)
                }
            
            publish_content_event (
                vehicule_data=vehicule_data,
                event_type= "new_post",
                title = f"{self.request.user.name} has added a new post: {vehicle.brand} {vehicle.name}"            
            )
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if str(instance.user_id) != str(request.user.id):
            return Response({
                'error': 'You don\'t have permission to update this vehicle'
            }, status=status.HTTP_403_FORBIDDEN)
            
        result = super().update(request, *args, **kwargs)
        
        instance.refresh_from_db()
        
        if instance.status == VehiculeModel.Status.ACTIVE:
            
            vehicule_data = {
            'id': instance.id,
            'name': instance.name,
            'brand': instance.brand,
            'user': instance.user_id,
            'status': instance.status,
            'created_at': str(instance.created_at)
          }
            
            publish_content_event(
                vehicule_data=vehicule_data,
                event_type='update_car',
                title = f"{self.request.user.name} has update the post of: {instance.brand} {instance.name}"            
            )
        return result
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if str(instance.user_id) != str(request.user.id):
            return Response({
                'error': 'You don\'t have permission to update this vehicle'
            }, status=status.HTTP_403_FORBIDDEN)
            
        old_status = instance.status
        result = super().partial_update(request, *args, **kwargs)
        
        instance.refresh_from_db()
        
        vehicule_data = {
            'id': instance.id,
            'name': instance.name,
            'brand': instance.brand,
            'user': instance.user_id,
            'status': instance.status,
            'created_at': str(instance.created_at)
        }
        
        publish_content_event(
                vehicule_data=vehicule_data,
                event_type='update_car',
                title = f"{self.request.user.name} has update the post of: {instance.brand} {instance.name}"            

        )
        
        return result
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if str(instance.user_id) != str(request.user.id):
            return Response({
                'error': 'You don\'t have permission to delete this vehicle'
            }, status=status.HTTP_403_FORBIDDEN)
            
        vehicle_id = instance.id
        owner_user_id = instance.user_id
        vehicle_name = instance.name
            
        publish_vehicle_deleted(vehicle_id=vehicle_id,vehicle_name=vehicle_name,owner_user_id=owner_user_id)
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedStateless])
    def my_cars(self, request):
        user_id = request.user.id
        cars = VehiculeModel.objects.filter(user_id=user_id).prefetch_related('images')
        serializer = self.get_serializer(cars, many=True)
        return Response({
            'count': cars.count(),
            'cars': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedStateless], 
            parser_classes=[MultiPartParser, FormParser])
    def add_image(self, request, pk=None):
        """
        Add single image to existing vehicle.
        POST /api/vehicles/{id}/add_image/
        Form-data: image=<file>, is_primary=<boolean>
        """
        vehicle = self.get_object()
        
        # Check ownership
        if str(vehicle.user_id) != str(request.user.id):
            return Response({
                'error': 'You don\'t have permission to modify this vehicle'
            }, status=status.HTTP_403_FORBIDDEN)
        
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({
                'error': 'No image file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        is_primary = request.data.get('is_primary', 'false').lower() == 'true'
        
        try:
            # If setting as primary, unset others
            if is_primary:
                vehicle.images.filter(is_primary=True).update(is_primary=False)
            
            image_obj = VehiculeImage.objects.create(
                vehicle=vehicle,
                image=image_file,
                is_primary=is_primary
            )
            
            serializer = VehiculeImageSerializer(image_obj)
            return Response({
                'message': 'Image uploaded successfully',
                'image': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Clean up uploaded file if creation failed
            if 'image_obj' in locals() and image_obj.image:
                if os.path.isfile(image_obj.image.path):
                    os.remove(image_obj.image.path)
            return Response({
                'error': f'Failed to upload image: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticatedStateless], 
            url_path='remove-image/(?P<image_id>[^/.]+)')
    def remove_image(self, request, pk=None, image_id=None):
        """
        Remove specific image from vehicle.
        DELETE /api/vehicles/{id}/remove-image/{image_id}/
        """
        vehicle = self.get_object()
        
        # Check ownership
        if str(vehicle.user_id) != str(request.user.id):
            return Response({
                'error': 'You don\'t have permission to modify this vehicle'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            image = vehicle.images.get(id=image_id)
            image.delete()  # This also deletes the physical file
            return Response({
                'message': 'Image deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except VehiculeImage.DoesNotExist:
            return Response({
                'error': 'Image not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Failed to delete image: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticatedStateless])
    def set_primary_image(self, request, pk=None):
        """
        Set specific image as primary.
        PATCH /api/vehicles/{id}/set_primary_image/
        Body: {"image_id": 123}
        """
        vehicle = self.get_object()
        
        if str(vehicle.user_id) != str(request.user.id):
            return Response({
                'error': 'You don\'t have permission to modify this vehicle'
            }, status=status.HTTP_403_FORBIDDEN)
        
        image_id = request.data.get('image_id')
        if not image_id:
            return Response({
                'error': 'image_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Unset current primary
            vehicle.images.filter(is_primary=True).update(is_primary=False)
            
            # Set new primary
            image = vehicle.images.get(id=image_id)
            image.is_primary = True
            image.save()
            
            return Response({
                'message': 'Primary image updated successfully',
                'image': VehiculeImageSerializer(image).data
            })
            
        except VehiculeImage.DoesNotExist:
            return Response({
                'error': 'Image not found'
            }, status=status.HTTP_404_NOT_FOUND)