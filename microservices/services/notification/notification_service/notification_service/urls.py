from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


def health_check(request):
    return HttpResponse("Notification Server 1 Working ✅")
urlpatterns = [
        path('', health_check),

    path('admin/', admin.site.urls),
    path('api/', include('notifications.urls')),
]
