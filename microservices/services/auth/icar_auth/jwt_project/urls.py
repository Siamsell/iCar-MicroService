from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


def health_check(request):
    return HttpResponse("Auth Server 2 Working ✅")
urlpatterns = [
    path('', health_check),
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
]
