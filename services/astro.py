import ephem
import math
from datetime import datetime

SIGNS = ['牡羊座','牡牛座','双子座','蟹座','獅子座','乙女座',
         '天秤座','蠍座','射手座','山羊座','水瓶座','魚座']

ASPECTS = [
    {'name': 'コンジャンクション', 'angle': 0,   'orb': 8, 'symbol': '☌'},
    {'name': 'セクスタイル',       'angle': 60,  'orb': 6, 'symbol': '⚹'},
    {'name': 'スクエア',           'angle': 90,  'orb': 8, 'symbol': '□'},
    {'name': 'トライン',           'angle': 120, 'orb': 8, 'symbol': '△'},
    {'name': 'オポジション',       'angle': 180, 'orb': 8, 'symbol': '☍'},
]

def get_sign(lon): return SIGNS[int(lon / 30) % 12]
def get_degree(lon): return lon % 30
def get_sabian_degree(lon):
    return int(lon / 30) % 12 * 30 + int(lon % 30) + 1

def to_ecl_lon(body):
    ra = float(body.a_ra)
    dec = float(body.a_dec)
    epsilon = math.radians(23.4393)
    x = math.cos(dec) * math.cos(ra)
    y = math.cos(dec) * math.sin(ra)
    z = math.sin(dec)
    ye = y * math.cos(epsilon) + z * math.sin(epsilon)
    return math.degrees(math.atan2(ye, x)) % 360

def calc_houses(jd, lat, lng):
    theta0 = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360
    LST = (theta0 + lng) % 360
    epsilon = math.radians(23.4393)
    LST_rad = math.radians(LST)
    lat_rad = math.radians(lat)
    asc = math.degrees(math.atan2(
        math.cos(LST_rad),
        -(math.sin(LST_rad) * math.cos(epsilon) + math.tan(lat_rad) * math.sin(epsilon))
    )) % 360
    mc_y = math.sin(LST_rad) * math.cos(epsilon) - math.tan(lat_rad) * math.sin(epsilon)
    mc = math.degrees(math.atan2(mc_y, -math.cos(LST_rad))) % 360
    if math.sin(LST_rad) > 0:
        mc = (mc + 180) % 360
    cusps = [(asc + i * 30) % 360 for i in range(12)]
    return cusps, asc, mc

def get_house(lon, cusps):
    lon = lon % 360
    for i in range(12):
        next_i = (i + 1) % 12
        start = cusps[i] % 360
        end = cusps[next_i] % 360
        if start <= end:
            if start <= lon < end:
                return i + 1
        else:
            if lon >= start or lon < end:
                return i + 1
    return 1

def calc_aspect_angle(a, b):
    diff = abs(a - b) % 360
    return 360 - diff if diff > 180 else diff

def calculate_chart(birth_date, birth_time, lat, lng):
    dt = datetime.combine(birth_date, birth_time)
    utc_h = dt.hour - 9 + dt.minute / 60.0
    ephem_date = f"{dt.year}/{dt.month}/{dt.day} {int(utc_h % 24):02d}:{dt.minute:02d}:00"

    obs = ephem.Observer()
    obs.lat = str(lat); obs.lon = str(lng)
    obs.date = ephem_date; obs.epoch = ephem.J2000; obs.pressure = 0

    jd = float(ephem.julian_date(obs.date))
    cusps, asc_lon, mc_lon = calc_houses(jd, lat, lng)

    bodies = {'太陽': ephem.Sun(), '月': ephem.Moon(), '水星': ephem.Mercury(),
              '金星': ephem.Venus(), '火星': ephem.Mars(), '木星': ephem.Jupiter(),
              '土星': ephem.Saturn(), '天王星': ephem.Uranus(),
              '海王星': ephem.Neptune(), '冥王星': ephem.Pluto()}

    planets_data = []
    positions = {}

    for name, body in bodies.items():
        body.compute(obs)
        lon = to_ecl_lon(body)
        planets_data.append({
            'name': name, 'sign': get_sign(lon),
            'degree': round(get_degree(lon), 1),
            'house': get_house(lon, cusps),
            'longitude': round(lon, 2),
            'sabian_degree': get_sabian_degree(lon),
            'retrograde': False
        })
        positions[name] = lon

    for name, lon in [('ASC', asc_lon), ('MC', mc_lon)]:
        planets_data.append({
            'name': name, 'sign': get_sign(lon),
            'degree': round(get_degree(lon), 1),
            'house': 1 if name == 'ASC' else 10,
            'longitude': round(lon, 2),
            'sabian_degree': get_sabian_degree(lon),
            'retrograde': False
        })
        positions[name] = lon

    aspects = []
    names = list(positions.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            p1, p2 = names[i], names[j]
            angle = calc_aspect_angle(positions[p1], positions[p2])
            for asp in ASPECTS:
                if abs(angle - asp['angle']) <= asp['orb']:
                    aspects.append({
                        'planet1': p1, 'planet2': p2,
                        'aspect': asp['name'], 'symbol': asp['symbol'],
                        'angle': round(angle, 1),
                        'orb': round(abs(angle - asp['angle']), 1)
                    })

    return {
        'planets': planets_data, 'aspects': aspects,
        'houses': [{'number': i+1, 'sign': get_sign(c), 'degree': round(get_degree(c), 1)}
                   for i, c in enumerate(cusps)],
        'asc': {'sign': get_sign(asc_lon), 'degree': round(get_degree(asc_lon), 1)},
        'mc': {'sign': get_sign(mc_lon), 'degree': round(get_degree(mc_lon), 1)},
    }
