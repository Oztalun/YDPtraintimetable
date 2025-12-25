from django.db import models
from django.contrib.auth import get_user_model

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

User = get_user_model()


TRAIN_TYPES = [
    ('KTX', 'KTX'),
    ('MUGUNGHWA', '무궁화'),
    ('ITX-maeum', 'ITX-마음'),
    ('I-Saemaeul', 'I-새마을'),
]

TRAIN_ARRIVE_AT = [
    ('Seoul', '서울'),
    ('Yongsan', '용산'),
]

TRAIN_PLATFORM =[
    ('6', 6),
    ('7', 7),
    ('8', 8),
    ('9', 9),
]
    
class Train(models.Model):
    train_number = models.CharField(max_length=20)       # 열차번호
    train_type = models.CharField(max_length=50)         # 열차종별 (KTX, 무궁화 등)
    destination = models.CharField(max_length=100)       # 종착역
    departure_time = models.TimeField(null=True, blank=True)  # 출발 시간
    platform = models.CharField(max_length=10)           # 홈 (플랫폼)
    note = models.CharField(max_length=200, blank=True)  # 비고 (옵션)

    def __str__(self):
        return f"{self.train_number} ({self.train_type})"