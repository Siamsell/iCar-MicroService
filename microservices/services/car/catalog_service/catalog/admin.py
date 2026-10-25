from django.contrib import admin
from .models import (
    UserModel,
    CategorieModel,
    SubCategorieModel,
    VehiculeModel,
    VehiculeImage
)

admin.site.register(UserModel)
admin.site.register(CategorieModel)
admin.site.register(SubCategorieModel)
admin.site.register(VehiculeModel)
admin.site.register(VehiculeImage)