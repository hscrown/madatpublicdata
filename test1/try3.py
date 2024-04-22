# Datasets 라이브러리로 데이터 프레임 로드해서 스트림릿으로 띄우기
# 잘되면 배포도 ㅇㅇ

import streamlit as st
from datasets import load_dataset
import pandas as pd

# Streamlit 앱 제목 설정
st.title('Global Copper Demand Forecasting Dataset')

# 데이터셋 로드
@st.cache_resource  # Streamlit 캐싱을 사용하여 데이터셋 로드 속도 향상
def load_data():
    dataset = load_dataset("CanariaView/GlobalCopperDemandForecastingDataset")
    # 데이터셋의 첫 번째 테이블을 DataFrame으로 변환
    df = pd.DataFrame(dataset['train'])
    return df

df = load_data()

# 데이터셋 표시
st.write("Dataset Preview:")
st.dataframe(df.head())  # 데이터셋의 상위 5개 행을 표시
