from django.shortcuts import render, redirect, get_object_or_404
from trainTT.models import Train
from django.views.decorators.http import require_http_methods, require_POST
import pandas as pd
from django.core.files.storage import FileSystemStorage
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField
from django.http import JsonResponse
import os
from dotenv import load_dotenv
from .services import fetch_arrival_data
from django.http import HttpResponse
import requests
import xml.etree.ElementTree as ET

from django.urls import reverse
from django.test import Client  # 내부 호출용

load_dotenv()

host_url = os.getenv("SERVER_URL")

SEOUL_API_KEY = os.getenv("SEOUL_API_KEY")   # 🔥 여기에 실제 인증키
line1pos_API_KEY = os.getenv("LINE1POS_API_KEY")


def api_response(request, *, title, method, endpoint, description, data):
    """
    모든 API에서 공통으로 사용하는 응답 처리기
    """
    # print("🔥 api_response CALLED 🔥")
    # print("TITLE:", title)
    # print("ACCEPT:", request.headers.get("Accept"))
    accept = request.headers.get("Accept", "")

    if "text/html" in accept:                       #브라우저는 text/html 타입의 응답을 원함
        return render(request, "api.html", {
            "title": title,
            "method": method,
            "endpoint": endpoint,
            "description": description,
            "api_data": data,
            'host_url':host_url,
        })

    return JsonResponse(                            #브라우저가 아니면 json 응답
        data,
        safe=False,
        json_dumps_params={"ensure_ascii": False}
    )


def line1pos_api(request):
    url = (
        "http://swopenapi.seoul.go.kr/api/subway/"
        f"{line1pos_API_KEY}/xml/realtimePosition/0/75/1호선"
    )

    res = requests.get(url, timeout=10)
    root = ET.fromstring(res.text)

    rows = root.findall("row")

    data = []
    for r in rows:
        row_data = {}

        # 🔥 row 안의 모든 태그를 그대로 dict로 변환
        for child in r:
            row_data[child.tag] = child.text

        data.append(row_data)
    # data = []
    # for r in root.findall("row"):
    #     data.append({
    #         "train_no": r.findtext("trainNo"),
    #         "station": r.findtext("statnNm"),
    #         "destination": r.findtext("statnTnm"),
    #         "updn": r.findtext("updnLine"),
    #         "status": r.findtext("trainSttus"),
    #         "is_express": r.findtext("directAt"),
    #         "is_last": r.findtext("lstcarAt"),
    #     })
    

    # 🔥 무조건 api_response로 보냄
    return api_response(
        request,
        title="🚆 1호선 실시간 열차 위치 정보",
        method="GET",
        endpoint="/api/line1pos/",
        description="서울 지하철 1호선 전체 열차의 실시간 위치 정보",
        data=data,
    )


def line1pos_list(request):
    """
    1호선 실시간 열차 위치를 표로 보여주는 페이지
    """
    # url = (
    #     "http://swopenapi.seoul.go.kr/api/subway/"
    #     f"{line1pos_API_KEY}/xml/realtimePosition/0/75/1호선"
    # )

    # res = requests.get(url, timeout=10)
    # root = ET.fromstring(res.text)

    # rows = root.findall("row")

    # trains = []
    # for r in rows:
    #     row_data = {}
    #     for child in r:
    #         row_data[child.tag] = child.text
    #     trains.append(row_data)

    # return render(request, "line1pos_list.html", {
    #     "trains": trains
    # })
    """
    1호선 실시간 열차 위치를 표로 보여주는 페이지.
    line1pos_api를 내부 호출하여 데이터를 가져옵니다.
    """
    # 내부 요청을 만들어서 API 호출
    client = Client()
    response = client.get(reverse("line1pos_api"))  # urls.py에 path("api/line1pos/", views.line1pos_api, name="line1pos_api") 있어야 함

    # JSON 데이터 파싱
    if response.status_code == 200:
        trains = response.json()
    else:
        trains = []

    return render(request, "line1pos_list.html", {
        "trains": trains,
        'host_url':host_url,
    })


def realtime_arrival_api(request):
    """
    서울 지하철 실시간 도착 API
    """
    station_name = request.GET.get("station", "영등포")
    url = (
        f"http://swopenapi.seoul.go.kr/api/subway/"
        f"{SEOUL_API_KEY}/xml/realtimeStationArrival/0/10/{station_name}"
    )

    res = requests.get(url, timeout=10)
    root = ET.fromstring(res.text)

    # 결과 코드 확인
    result = root.find("RESULT")
    if result is not None:
        code = result.findtext("code")
        if code != "INFO-000":
            return JsonResponse({"error": "API 오류", "code": code})

    rows = root.findall("row")
    data = []

    for row in rows:
        item = {child.tag: child.text for child in row}
        data.append(item)

    return api_response(
        request,
        title=f"🚆 {station_name} 실시간 도착 정보",
        method="GET",
        endpoint=f"/api/realtime_arrival/?station={station_name}",
        description=f"{station_name}역의 서울 지하철 실시간 도착 정보",
        data=data
    )


def realtime_arrival(request):
    station_name = request.GET.get("station", "영등포")

    url = (
        f"http://swopenapi.seoul.go.kr/api/subway/"
        f"{SEOUL_API_KEY}/xml/realtimeStationArrival/0/10/{station_name}"
    )

    res = requests.get(url, timeout=10)
    root = ET.fromstring(res.text)

    # 결과 코드 확인
    result = root.find("RESULT")
    if result is not None:
        code = result.findtext("code")
        if code != "INFO-000":
            return JsonResponse({"error": "API 오류", "code": code})

    rows = root.findall("row")
    data = []

    for row in rows:
        item = {
            "subway_id": row.findtext("subwayId"),
            "line": row.findtext("updnLine"),
            "train_line": row.findtext("trainLineNm"),
            "station": row.findtext("statnNm"),
            "train_type": row.findtext("btrainSttus"),
            "train_no": row.findtext("btrainNo"),
            "destination": row.findtext("bstatnNm"),
            "arrival_sec": row.findtext("barvlDt"),
            "msg1": row.findtext("arvlMsg2"),
            "msg2": row.findtext("arvlMsg3"),
            "arrival_code": row.findtext("arvlCd"),
            "is_last": row.findtext("lstcarAt") == "1",
            "received_at": row.findtext("recptnDt"),
        }
        data.append(item)

    # 👉 JSON으로 보고 싶으면 이 줄만 사용
    # return JsonResponse(data, safe=False, json_dumps_params={"ensure_ascii": False})

    # 👉 화면으로 보고 싶으면 template 사용
    return render(request, "realtime_arrival.html", {
        "station": station_name,
        "trains": data,
        'host_url':host_url,
    })




#열차-----------------------------------------------
def train_api(request):
    now = timezone.localtime().time()
    before30 = (timezone.localtime() - timedelta(minutes=30)).time()
    trains = Train.objects.all().order_by('id')

    # 검색 필터
    type_filter = request.GET.get('type')
    dest_filter = request.GET.get('destination')
    number_filter = request.GET.get('number')
    time_filter = request.GET.get('time')
    waypoint_filter = request.GET.get('waypoint')

    if type_filter:
        trains = trains.filter(train_type__icontains=type_filter)
    if dest_filter:
        trains = trains.filter(destination__icontains=dest_filter)
    if number_filter:
        trains = trains.filter(train_number__icontains=number_filter)
    if time_filter:
        trains = trains.filter(departure_time__icontains=time_filter)
    if waypoint_filter == 'up':
        trains = trains.filter(platform__in=[6, 7])
    elif waypoint_filter == 'down':
        trains = trains.filter(platform__in=[8, 9])
        
    trains = trains.annotate(
    is_after=Case(
        When(departure_time__gte=now, then=Value(0)),
        default=Value(1),
        output_field=IntegerField(),
    )
    ).order_by('is_after', 'departure_time')

    # QuerySet -> 리스트 of dict
    trains_list = {"trains":list(trains.values(
        'train_number',
        'train_type',
        'destination',
        'departure_time',
        'platform',
        'note'
    ))}
    return api_response(
        request,
        title=f"🚆 영등포 열차 시간표",
        method="GET",
        endpoint=f"/api/trains",
        description=f"영등포 열차 시간표",
        data=trains_list
    )



def TrainTTView(request):
    return render(request, "front.html", {'host_url':host_url})


def train_inquiry(request):
    return render(request, 'train_inquiry.html', {'host_url':host_url})


def subway_list(request):
    data = fetch_arrival_data()
    data['host_url'] = host_url
    return render(request, 'subway_list.html', data)


def convert_to_time(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        try:
            dt = pd.to_datetime(value.strip())
            return dt.time()
        except Exception as e:
            print(f"시간 변환 에러: {e} / 값: {value}")
            return None
    if isinstance(value, time):  # time 타입 체크
        return value
    if hasattr(value, 'time'):
        return value.time()
    return None


# def convert_to_time(value):
#     if pd.isna(value):
#         return None
#     dt = pd.to_datetime(value, errors='coerce')
#     if pd.isna(dt):
#         return None
#     # dt가 Timestamp면 time()으로 변환
#     return dt.time() if hasattr(dt, 'time') else None


def upload_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        fs = FileSystemStorage()
        filename = fs.save(excel_file.name, excel_file)
        filepath = fs.path(filename)

        df = pd.read_excel(filepath, engine='openpyxl', header=1)
        print(df.head())

        for _, row in df.iterrows():
            departure_time = convert_to_time(row['도착(출발 시간)'])
            print(
                f"원본: {row['도착(출발 시간)']} -> 변환: {departure_time}, 타입: {type(row['도착(출발 시간)'])}")
            Train.objects.create(
                train_number=str(row['열차번호']),
                train_type=row['열차종별'],
                destination=row['종착역'],
                departure_time=departure_time,
                platform=str(row['홈']),
                note=row.get('비고', '')
            )

        # for _, row in df.iterrows():
        #     print(row['도착(출발 시간)'], type(row['도착(출발 시간)']))
        #     Train.objects.create(
        #         train_number=str(row['열차번호']),
        #         train_type=row['열차종별'],
        #         destination=row['종착역'],
        #         # arrival_time = pd.to_datetime(row['도착시간']).time(),
        #         departure_time=convert_to_time(row['도착(출발 시간)']),
        #         platform=str(row['홈']),
        #         note=row.get('비고', '')
        #     )

        return render(request, 'upload_success.html')
    return render(request, 'upload_form.html')


def train_list(request):
    return render(request, 'train_list.html', {'host_url':host_url})#, {'trains': trains, 'now': now, 'request': request}


def downtrain_list(request):
    now = timezone.localtime().time()
    print(now)
    trains = Train.objects.all().order_by('id')  # 기본 정렬

    # 검색 필터
    type_filter = request.GET.get('type')
    dest_filter = request.GET.get('destination')
    number_filter = request.GET.get('number')
    time_filter = request.GET.get('time')

    if type_filter:
        trains = trains.filter(train_type__icontains=type_filter)

    if dest_filter:
        trains = trains.filter(destination__icontains=dest_filter)

    if number_filter:
        trains = trains.filter(train_number__icontains=number_filter)

    if time_filter:
        trains = trains.filter(departure_time__icontains=time_filter)

    # --------------------------------------------------------------------------------------
    # 필터를 사용하려면 리스트화 하기 전이여야 하므로 마지막에 진행
    # 시간 기준으로 리스트를 나눔
    trains = trains.annotate(
        is_after=Case(
            When(departure_time__gte=now, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('is_after', 'departure_time')
    # 하행 열차
    downtrains = trains.filter(platform__in=[8, 9])

    return render(request, 'train_list.html', {'downtrains': downtrains, 'now': now, 'request': request})


def uptrain_list(request):
    now = timezone.localtime().time()
    print(now)
    trains = Train.objects.all().order_by('id')  # 기본 정렬

    # 검색 필터
    type_filter = request.GET.get('type')
    dest_filter = request.GET.get('destination')
    number_filter = request.GET.get('number')
    time_filter = request.GET.get('time')

    if type_filter:
        trains = trains.filter(train_type__icontains=type_filter)

    if dest_filter:
        trains = trains.filter(destination__icontains=dest_filter)

    if number_filter:
        trains = trains.filter(train_number__icontains=number_filter)

    if time_filter:
        trains = trains.filter(departure_time__icontains=time_filter)

    trains = trains.annotate(
        is_after=Case(
            When(departure_time__gte=now, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('is_after', 'departure_time')

    # 상행 열차
    uptrains = trains.filter(platform__in=[6, 7])

    return render(request, 'train_list.html', {'uptrains': uptrains, 'now': now, 'request': request})


def origintrain_list(request):
    SetTime = time(3, 0)  # 15:00 (오후 3시)
    now = timezone.localtime().time()
    print(now)
    trains = Train.objects.all().order_by('id')  # 기본 정렬

    # 오리지날 시간표
    OriginalTrains = trains.annotate(
        is_after=Case(
            When(departure_time__gte=SetTime, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('is_after', 'departure_time')

    # 검색 필터
    type_filter = request.GET.get('type')
    dest_filter = request.GET.get('destination')
    number_filter = request.GET.get('number')
    time_filter = request.GET.get('time')

    if type_filter:
        trains = trains.filter(train_type__icontains=type_filter)

    if dest_filter:
        trains = trains.filter(destination__icontains=dest_filter)

    if number_filter:
        trains = trains.filter(train_number__icontains=number_filter)

    if time_filter:
        trains = trains.filter(departure_time__icontains=time_filter)
    
    return render(request, 'train_list.html', {'trains': OriginalTrains, 'now': now, 'request': request})
