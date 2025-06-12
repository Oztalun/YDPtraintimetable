from django.shortcuts import render, redirect, get_object_or_404
from trainTT.models import TrainTimeTable, Train
from django.views.decorators.http import require_http_methods, require_POST
import pandas as pd
from django.core.files.storage import FileSystemStorage
from datetime import datetime, time
from django.utils import timezone
# 처음
# @require_http_methods(["GET", "POST"])


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
        return render(request, "trainTT/front.html", context)
    # else:
    #     return redirect("articles:articles")

    return render(request, "trainTT/front.html", context)

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
            print(f"원본: {row['도착(출발 시간)']} -> 변환: {departure_time}, 타입: {type(row['도착(출발 시간)'])}")
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

        return render(request, 'trainTT/upload_success.html')

    return render(request, 'trainTT/upload_form.html')


def train_list(request):
    now = datetime.now().time()
    trains = Train.objects.all().order_by('id') # 기본 정렬 

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

    return render(request, 'trainTT/train_list.html', {'trains': trains, 'request': request})
