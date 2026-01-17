
from django.urls import path
from django.views.generic import TemplateView
from trainTT import views

urlpatterns = [
    path('', views.TrainTTView, name='trainTimeTable'), #리스트,생성
    # path('upload/', views.upload_excel, name='upload_excel'),
    path('trains/', views.train_list, name='train_list'),                   #열차 시간표
    path('api/trains/', views.train_api, name='train_list_api'),            #열차 시간표 API
    
    path('subway/', views.subway_list, name='subway_list'),                 #실시간 도착 정보(정보는 없고 탬플릿만)
    path("arrival/", views.realtime_arrival, name="realtime_arrival"),      #실시간 도착 정보 1회성
    
    path('line1pos/', views.line1pos_list, name='line1pos_list'),           #실시간 위치
    path('api/line1pos/', views.line1pos_api, name='line1pos_api'),             #실시간 위치 API
    path("line1/", TemplateView.as_view(template_name="line1pos.html")),    #실시간 위치 템플릿 (안됨, 에러)
    
    path('inquiry/', views.train_inquiry, name='train_inquiry'),            #문의
]