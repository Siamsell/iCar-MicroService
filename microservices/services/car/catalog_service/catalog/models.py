from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
import os
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import pre_delete
from django.dispatch import receiver

        
class UserModel(models.Model):
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, default='user')
    date_joined = models.DateTimeField()
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def is_admin(self):
        return self.role == 'admin'
    

class CategorieModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(unique=True)
    image = models.ImageField(upload_to='category_images/')
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        ordering = ['name']

class SubCategorieModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(unique=True)
    image = models.ImageField(upload_to='subcategory_images/')
    categorie = models.ForeignKey(
        CategorieModel, 
        on_delete=models.CASCADE,
        related_name='subcategories',
        db_column='categorie_id'
    )
    
    def __str__(self):
        return f"{self.name} ({self.categorie.name})"
    
    class Meta:
        ordering = ['name']
        
        
class VehiculeModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    brand = models.TextField()
    subcategory = models.ForeignKey(SubCategorieModel, on_delete=models.CASCADE)
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE, 
        related_name='vehicles',
        db_column='user_id',
        help_text="ID of the user who owns this vehicle (from auth service)"
    )
    year = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1800),
            MaxValueValidator(2027)
        ]
    )
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT','draft'
        ACTIVE = 'ACTIVE','active'
        INACTIVE = 'INACTIVE','inactive'
        
    status = models.CharField(choices=Status.choices, default=Status.ACTIVE, max_length=20)
    description = models.TextField(max_length=400)
    phone = models.CharField(max_length=10)
    location = models.CharField(max_length=255)
    milage = models.PositiveBigIntegerField()
    coleur = models.CharField(max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    
    class FuelType(models.TextChoices):
        GASOIL = 'gasoil', 'Gasoil'
        DIESEL = 'diesel', 'Diesel'
        HYBRID = 'hybrid', 'Hybrid'
        ELECTRIC = 'electric', 'Electric'
    
    fuel = models.CharField(
        max_length=20,
        choices=FuelType.choices,
        default=FuelType.GASOIL
    )
    
    class TransmissionType(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual'          
        AUTOMATIC = 'AUTOMATIC', 'Automatic'  
        SEMI_AUTOMATIC = 'SEMI_AUTOMATIC', 'Semi-Automatic'
        CVT = 'CVT', 'CVT'
        
    transmissionType = models.CharField(
        max_length=30,
        choices=TransmissionType.choices,
        default=TransmissionType.MANUAL
    )
    
    def __str__(self):
        return self.name
    
    @property
    def category(self):
        return self.subcategory.categorie
    
    class Meta:
        ordering = ['-created_at']


class VehiculeImage(models.Model):
    vehicle = models.ForeignKey(
        VehiculeModel, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='vehicle_images/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False, help_text="Main display image")
    image_url = models.TextField(max_length=500, help_text="Full URL of the image",default="")

    class Meta:
        ordering = ['-is_primary', '-uploaded_at']
    
    def __str__(self):
        return f"Image {self.id} for {self.vehicle.name}"

    
    def get_image(self, obj):
        request = self.context.get('request')

        if obj.image:
            url = obj.image.url

            return request.build_absolute_uri(url) if request else url

        return None
    
    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)
        


@receiver(pre_delete, sender=VehiculeImage)
def delete_vehicle_image_file(sender, instance, **kwargs):
    """Delete image file when VehiculeImage is deleted (including CASCADE)"""
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
            print(f"Deleted file: {instance.image.path}")