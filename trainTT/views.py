from django.shortcuts import render, redirect, get_object_or_404
from trainTT.models import Train
from django.views.decorators.http import require_http_methods, require_POST
import pandas as pd
from django.core.files.storage import FileSystemStorage
from datetime import datetime, time
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField
from django.http import JsonResponse
import os
from dotenv import load_dotenv
from django.http import JsonResponse

load_dotenv()

host_url = os.getenv("SERVER_URL")

def train_api(request):
    now = timezone.localtime().time()
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
    trains_list = list(trains.values(
        'train_number',
        'train_type',
        'destination',
        'departure_time',
        'platform',
        'note'
    ))

    return JsonResponse(trains_list, safe=False)


def TrainTTView(request):
    if request.method == "GET":
        # context = {"trains": TrainTimeTable.objects.all().order_by("pk")}
        context = {"TrainList": [
            {"trainNum": 1320, "traintype": "무궁화", "arriveAt": "서울",
                "arriveTime": "7:27", "platform": 7},
            {"trainNum": 1322, "traintype": "무궁화", "arriveAt": "서울",
                "arriveTime": "8:03", "platform": 6},
            {"trainNum": 1324, "traintype": "무궁화", "arriveAt": "서울",
                "arriveTime": "8:31", "platform": 7},
            {"trainNum": 1442, "traintype": "무궁화", "arriveAt": "용산",
                "arriveTime": "8:41", "platform": 6},
        ]}
        return render(request, "front.html", context)
    # else:
    #     return redirect("articles:articles")

    return render(request, "front.html", context)


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
