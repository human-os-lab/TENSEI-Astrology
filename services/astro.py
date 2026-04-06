import swisseph as swe
from datetime import datetime

swe.set_ephe_path('/usr/share/ephe')

PLANETS = {
    '太陽': swe.SUN, '月': swe.MOON, '水星': swe.MERCURY,
    '金星': swe.VENUS, '火星': swe.MARS, '木星': swe.JUPITER,
    '土星': swe.SATURN, '天王星': swe.URANUS, '海王星': swe.NEPTUNE,
    '冥王星': swe.PLUTO
}

SIGNS = ['牡羊座','牡牛座','双子座','蟹座','獅子座','乙女座',
         '天秤座','蠍座','射手座','山羊座','水瓶座','魚座']

SIGNS_EN = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
            'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

ASPECTS = [
    {'name': 'コンジャンクション', 'angle': 0, 'orb': 8, 'symbol': '☌'},
    {'name': 'セクスタイル', 'angle': 60, 'orb': 6, 'symbol': '⚹'},
    {'name': 'スクエア', 'angle': 90, 'orb': 8, 'symbol': '□'},
    {'name': 'トライン', 'angle': 120, 'orb': 8, 'symbol': '△'},
    {'name': 'オポジション', 'angle': 180, 'orb': 8, 'symbol': '☍'},
]

def get_sign(lon):
    return SIGNS[int(lon / 30)]

def get_degree(lon):
    return lon % 30

def get_house(lon, houses):
    for i in range(11, -1, -1):
        if lon >= houses[i] % 360 or (i == 0 and lon < houses[11] % 360):
            return i + 1
    return 1

def get_sabian_degree(lon):
    """サビアン度数（1〜360）を返す"""
    deg = int(lon % 30) + 1
    sign_index = int(lon / 30)
    return sign_index * 30 + deg

def calc_aspect_angle(a, b):
    diff = abs(a - b) % 360
    if diff > 180:
        diff = 360 - diff
    return diff

def calculate_chart(birth_date, birth_time, lat, lng):
    dt = datetime.combine(birth_date, birth_time)
    # UTCに変換（簡易：日本時間 -9時間）
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour - 9 + dt.minute/60)

    houses, ascmc = swe.houses(jd, lat, lng, b'P')

    planets = []
    planet_positions = {}

    for name, planet_id in PLANETS.items():
        pos, _ = swe.calc_ut(jd, planet_id)
        lon = pos[0]
        sign = get_sign(lon)
        degree = get_degree(lon)
        house = get_house(lon, houses)
        sabian = get_sabian_degree(lon)

        planet_data = {
            'name': name,
            'sign': sign,
            'degree': round(degree, 1),
            'house': house,
            'longitude': round(lon, 2),
            'sabian_degree': sabian,
            'retrograde': pos[3] < 0
        }
        planets.append(planet_data)
        planet_positions[name] = lon

    # ASC・MC追加
    for name, lon in [('ASC', ascmc[0]), ('MC', ascmc[1])]:
        planets.append({
            'name': name,
            'sign': get_sign(lon),
            'degree': round(get_degree(lon), 1),
            'house': 1 if name == 'ASC' else 10,
            'longitude': round(lon, 2),
            'sabian_degree': get_sabian_degree(lon),
            'retrograde': False
        })
        planet_positions[name] = lon

    # アスペクト計算
    aspects = []
    planet_names = list(planet_positions.keys())
    for i in range(len(planet_names)):
        for j in range(i+1, len(planet_names)):
            p1, p2 = planet_names[i], planet_names[j]
            angle = calc_aspect_angle(planet_positions[p1], planet_positions[p2])
            for asp in ASPECTS:
                if abs(angle - asp['angle']) <= asp['orb']:
                    aspects.append({
                        'planet1': p1,
                        'planet2': p2,
                        'aspect': asp['name'],
                        'symbol': asp['symbol'],
                        'angle': round(angle, 1),
                        'orb': round(abs(angle - asp['angle']), 1)
                    })

    house_data = [{'number': i+1, 'sign': get_sign(h), 'degree': round(get_degree(h), 1)}
                  for i, h in enumerate(houses)]

    return {
        'planets': planets,
        'aspects': aspects,
        'houses': house_data,
        'asc': {'sign': get_sign(ascmc[0]), 'degree': round(get_degree(ascmc[0]), 1)},
        'mc': {'sign': get_sign(ascmc[1]), 'degree': round(get_degree(ascmc[1]), 1)},
    }
