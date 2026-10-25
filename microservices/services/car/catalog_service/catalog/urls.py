from django.urls import path,include
from rest_framework import routers
from .views import CategorieViewSet,SubCategorieViewSet,VehiculeViewSet,UserModelViewSet
router = routers.DefaultRouter()

router.register(r'categories',CategorieViewSet)
router.register(r'subcategories',SubCategorieViewSet)
router.register(r'vehicules',VehiculeViewSet)
router.register(r'users',UserModelViewSet)


urlpatterns = [
     path('',include(router.urls))
]
