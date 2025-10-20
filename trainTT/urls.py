
from django.urls import path
from trainTT import views

urlpatterns = [
    path('', views.TrainTTView, name='trainTimeTable'), #리스트,생성
    # path('upload/', views.upload_excel, name='upload_excel'),
    path('trains/', views.train_list, name='train_list'),
    path('api/trains/', views.train_api, name='train_list_api'),
]
