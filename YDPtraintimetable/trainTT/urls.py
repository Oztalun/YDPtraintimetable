
from django.urls import path
from trainTT import views

urlpatterns = [
    path('', views.ArticleAPIView.as_view(), name='articles'), #리스트,생성
]
