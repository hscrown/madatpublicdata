
# 패키지 임포트

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from lxml import etree
from haversine import haversine
from datasets import load_dataset


# 오늘 날짜와 시간 불러오기
what_date = datetime.now().strftime("%Y%m%d")
what_time = datetime.now().strftime("%H%M")

# 기상청 좌표 데이터 로드
dataset = load_dataset("hscrown/weather_api_info")
kor_loc = pd.DataFrame(dataset['train'])
kor_loc = kor_loc.iloc[:,:15]
kor_loc = kor_loc.dropna()

# 내 좌표 설정
my_loc = (37.566, 126.9784)

# 가장 가까운 기상청 x, y 좌표 찾기
grid, min_distance, nx, ny = None, float('inf'), None, None
for index, row in kor_loc.iterrows():
    grid_point = (row['위도(초/100)'], row['경도(초/100)'])
    distance = haversine(my_loc, grid_point)
    if distance < min_distance:
        min_distance = distance
        grid = row
        nx, ny = grid['격자 X'], grid['격자 Y']

# 기상 정보 가져오기
url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
params = {
    'serviceKey': 'sX3JWddMWHJxC43fx9mqgcqSsbmAlTpoFTUPbnrE1Db5uVnEAs7gJIL4Z3tzW1u2S6UC+8/go3xYCnG2wDctAQ==',
    'pageNo': '1',
    'numOfRows': '1000',
    'dataType': 'XML',
    'base_date': what_date,
    'base_time': what_time,
    'nx': nx,
    'ny': ny
}
response = requests.get(url, params=params)
root = etree.fromstring(response.content)
rain = root.xpath('//obsrValue/text()')[0]
temp = root.xpath('//obsrValue/text()')[3]
rain_mapping = {
    '0': "비가 오고 있지 않습니다.",
    '1': "비 소식이 있습니다.",
    '2': "비 또는 눈이 내립니다.",
    '3': "눈이 오고 있습니다.",
    '4': "소나기가 옵니다.",
    '5': "빗방울이 떨어집니다.",
    '6': "빗방울과 눈날림이 있습니다.",
    '7': "눈날림이 있습니다."
}
rain = rain_mapping.get(rain, "기상 정보 없음")

  # 초단기예보데이터
url2 = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst'


response2 = requests.get(url2, params=params)
root2 = etree.fromstring(response2.content)

# 엘리먼트 선택
items = root2.xpath('//item')

# 딕셔너리로 만들기
data = [{
    "baseDate": item.findtext("baseDate"),
    "baseTime": item.findtext("baseTime"),
    "category": item.findtext("category"),
    "fcstDate": item.findtext("fcstDate"),
    "fcstTime": item.findtext("fcstTime"),
    "fcstValue": item.findtext("fcstValue"),
    "nx": item.findtext("nx"),
    "ny": item.findtext("ny")
} for item in items]

# 데이터프레임으로 만들기
df = pd.DataFrame(data)
df = df[df['fcstDate'] == df['baseDate']] # 오늘 예측 값만
# df = df[df['fcstTime'] == df['baseTime']]
df

sky_dict = {
    '1': "맑음",
    '2': "구름조금",
    '3': "구름많음",
    '4': "흐림"
}

# 30분뒤 하늘상태는
df = df[df['category'] == 'SKY']['fcstValue'].map(sky_dict)
sky = df.values[0]

# 날씨 정보에 따른 장소 추천 로직
if rain != '비가 오고 있지 않습니다.' or float(temp) >= 30:
    # 박물관 정보 불러오기
    muse = load_dataset("hscrown/seoul_museums")
    muse = pd.DataFrame(muse['train'])
    muse.rename(columns={'시설명':"NAME",'주소':"ADRES",'위도':'LATITUDE','경도':'LONGITUDE'}, inplace=True)
    muse['LATITUDE'].replace('', np.nan, inplace=True)
    muse['LONGITUDE'].replace('', np.nan, inplace=True)
    muse = muse.dropna()
    muse['LATITUDE'] = muse['LATITUDE'].astype(float)
    muse['LONGITUDE'] = muse['LONGITUDE'].astype(float)

    # 도서관 정보 불러오기
    api_key = '57524f76506d656e3732636a52457a'
    start_point = 1
    end_point = 1000
    url = f'http://openAPI.seoul.go.kr:8088/{api_key}/json/SeoulLibraryTimeInfo/{start_point}/{end_point}/'
    url2 = f'http://openAPI.seoul.go.kr:8088/{api_key}/json/SeoulLibraryTimeInfo/1001/2000/'

    data = requests.get(url).json()
    data2 = requests.get(url2).json()

    data = pd.DataFrame(data['SeoulLibraryTimeInfo']['row'])
    data2 = pd.DataFrame(data2['SeoulLibraryTimeInfo']['row'])

    lib = pd.concat([data, data2])
    lib.rename(columns={'LBRRY_NAME':"NAME",'ADRES':"ADRES",'XCNTS':'LATITUDE','YDNTS':"LONGITUDE"}, inplace=True)
    lib['LATITUDE'] = lib['LATITUDE'].astype(float)
    lib['LONGITUDE'] = lib['LONGITUDE'].astype(float)

    # 결합
    places = pd.concat([muse, lib])

    # 가장 가까운 위치 찾기
    min_distance, place_name, place_lat, place_long, place_adres = float('inf'), None, None, None, None
    for index, row in places.iterrows():
        point = (row['LATITUDE'], row['LONGITUDE'])
        distance = haversine(my_loc, point)
        if distance < min_distance:
            min_distance = distance
            place_name, place_lat, place_long, place_adres = row['NAME'], row['LATITUDE'], row['LONGITUDE'], row['ADRES']
    result = {"sky":sky, "rain": rain, "temp": temp, "place": "cultural","name": place_name, "latitude": place_lat, "longitude": place_long, "address": place_adres}
else:
    park_url = 'http://openAPI.seoul.go.kr:8088/57524f76506d656e3732636a52457a/json/SearchParkInfoService/1/1000/'
    park_data = requests.get(park_url).json()['SearchParkInfoService']['row']
    park = pd.DataFrame(park_data)
    park.rename(columns={'P_PARK':"NAME",'P_ADDR':"ADRES",'XCNTS':'LATITUDE','YDNTS':"LONGITUDE"}, inplace=True)
    park['LATITUDE'].replace('', np.nan, inplace=True)
    park['LONGITUDE'].replace('', np.nan, inplace=True)
    park = park.dropna()
    park['LATITUDE'] = park['LATITUDE'].astype(float)
    park['LONGITUDE'] = park['LONGITUDE'].astype(float)
    min_distance, park_name, park_lat, park_long, park_adres = float('inf'), None, None, None, None
    for index, row in park.iterrows():
        point = (row['LATITUDE'], row['LONGITUDE'])
        distance = haversine(my_loc, point)
        if distance < min_distance:
            min_distance = distance
            park_name, park_lat, park_long, park_adres = row['NAME'], row['LATITUDE'], row['LONGITUDE'], row['ADRES']
    result = {"sky":sky, "rain": rain, "temp": temp, "place": "park","name": park_name, "latitude": park_lat, "longitude": park_long, "address": park_adres}

# 결과 출력
print(result)
