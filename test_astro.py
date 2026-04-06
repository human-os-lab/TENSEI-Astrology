import swisseph as swe
from datetime import datetime

swe.set_ephe_path('/usr/share/ephe')

PLANETS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
    'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO
}

SIGNS = ['牡羊座','牡牛座','双子座','蟹座','獅子座','乙女座',
         '天秤座','蠍座','射手座','山羊座','水瓶座','魚座']

def get_sign(lon):
    return SIGNS[int(lon / 30)]

def get_degree(lon):
    return lon % 30

# 東京・1990年1月1日12:00でテスト
dt = datetime(1990, 1, 1, 12, 0)
jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60)

print("=== テスト計算：東京 1990/1/1 12:00 ===")
for name, planet_id in PLANETS.items():
    pos, _ = swe.calc_ut(jd, planet_id)
    lon = pos[0]
    print(f"{name}: {get_sign(lon)} {get_degree(lon):.1f}度 (経度:{lon:.2f})")

# ASC・MC計算（東京: 35.68N, 139.69E）
houses, ascmc = swe.houses(jd, 35.68, 139.69, b'P')
print(f"\nASC: {get_sign(ascmc[0])} {get_degree(ascmc[0]):.1f}度")
print(f"MC:  {get_sign(ascmc[1])} {get_degree(ascmc[1]):.1f}度")
print("\nハウスカスプ:")
for i, h in enumerate(houses, 1):
    print(f"  第{i}ハウス: {get_sign(h)} {get_degree(h):.1f}度")
