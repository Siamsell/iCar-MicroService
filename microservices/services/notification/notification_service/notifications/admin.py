from django.contrib import admin
from .models import (
    UserModel,
    VehiculeModel,
    Notification,
    UserFollowPost,
    UserFollowUser
)

admin.site.register(UserModel)
admin.site.register(VehiculeModel)
admin.site.register(Notification)
admin.site.register(UserFollowPost)
admin.site.register(UserFollowUser)