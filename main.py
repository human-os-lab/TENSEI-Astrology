from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import date, time
from geopy.geocoders import Nominatim
from services.astro import calculate_chart

app = FastAPI()
templates = Jinja2Templates(directory="templates")


geolocator = Nominatim(user_agent="etsuko-astro-app")

# 主要都市フォールバック（geopyが使えない環境用）
CITY_COORDS = {
    "東京": (35.6895, 139.6917), "大阪": (34.6937, 135.5023),
    "名古屋": (35.1815, 136.9066), "札幌": (43.0642, 141.3469),
    "福岡": (33.5904, 130.4017), "京都": (35.0116, 135.7681),
    "横浜": (35.4437, 139.6380), "神戸": (34.6901, 135.1956),
    "仙台": (38.2682, 140.8694), "広島": (34.3853, 132.4553),
    "那覇": (26.2124, 127.6809), "金沢": (36.5944, 136.6256),
}

def geocode_place(place: str):
    # フォールバック：主要都市名で検索
    for city, coords in CITY_COORDS.items():
        if city in place:
            return coords[0], coords[1], place
    # geopyで試みる
    try:
        loc = geolocator.geocode(place, language="ja", timeout=5)
        if loc:
            return loc.latitude, loc.longitude, loc.address
    except Exception:
        pass
    return None, None, None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/calculate", response_class=HTMLResponse)
async def calculate(
    request: Request,
    birth_date: date = Form(...),
    birth_time: time = Form(...),
    birth_place: str = Form(...),
):
    lat, lng, location_name = geocode_place(birth_place)
    if lat is None:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"「{birth_place}」の場所が見つかりませんでした。都道府県・市区町村名で入力してください。"
        })
    location_name = location_name or birth_place

    chart = calculate_chart(birth_date, birth_time, lat, lng)

    return templates.TemplateResponse("result_free.html", {
        "request": request,
        "birth_date": birth_date,
        "birth_time": birth_time,
        "birth_place": birth_place,
        "location_name": location_name,
        "lat": round(lat, 4),
        "lng": round(lng, 4),
        "chart": chart,
    })
