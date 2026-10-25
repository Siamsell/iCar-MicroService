from django.contrib import admin
from django.urls import path, include
import catalog.urls
from django.http import HttpResponse
from django.conf.urls.static import static
from django.conf import settings

def health_check(request):
    return HttpResponse("Car Server 1 Working ✅")


urlpatterns = [
        path('', health_check),
    path('admin/', admin.site.urls),
    path('api/', include(catalog.urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)