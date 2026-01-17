# metro/services.py
import requests
from bs4 import BeautifulSoup

URL = "https://rail.blue/railroad/logis/metroarriveinfo.aspx"

def fetch_arrival_data():
    params = {
        "q": "7JiB65Ox7Y_s",
        "c": "Korail",
        "base": "1",
        "v": "d"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://rail.blue/"
    }

    res = requests.get(URL, params=params, headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    # 역 이름
    station_tag = soup.find("span", id="spStation")
    station = station_tag.text.strip() if station_tag else "알 수 없음"

    trains = {"up": [], "down": []}

    # 🔥 방향 기준 td 검색
    tables = soup.select("table.main_table")

    for table in tables:
        rows = table.find_all("tr")
        for tr in rows:
            train_td = tr.find("td", class_="tdTrainNo")
            dest_td = tr.find("td", class_="tdDest")

            if not train_td or not dest_td:
                continue

            train_no = (
                train_td.get_text(strip=True)
                .split()[0]
                .replace("#", "")
                .upper()
            )

            status_tag = train_td.find("span", class_="spMAStatus")
            status = status_tag.text.strip() if status_tag else ""

            destination = dest_td.find("span", class_="spMetroTrainDestination")
            destination = destination.get_text(" ", strip=True) if destination else ""

            arrive_time = dest_td.find("span", class_="spMetroArriveTime")
            arrive_time = arrive_time.text.strip() if arrive_time else ""

            delay = dest_td.find("span", class_="spMetroArriveDelayApply")
            delay = delay.text.strip() if delay else "정시"

            train_type = "일반"
            if dest_td.find("span", class_="tdResultRedRapid"):
                train_type = "급행"
            elif dest_td.find("span", class_="tdResultSpecialRapid"):
                train_type = "특급"

            # 상/하행 판별 (부모 테이블 기준)
            direction = "up" if "tblTrainListU" in str(table) else "down"

            trains[direction].append({
                "train_no": train_no,
                "destination": destination,
                "type": train_type,
                "status": status,
                "arrive_time": arrive_time,
                "delay": delay
            })

    return {
        "station": station,
        "up": trains["up"],
        "down": trains["down"]
    }
