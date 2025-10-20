from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('trainTT.urls')),
    path('admin/', admin.site.urls),
]
