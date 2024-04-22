# NLP 모델 웹에 배포하기 연습 ## 실패
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from huggingface_hub.hf_api import HfFolder

import requests

API_URL = "https://api-inference.huggingface.co/models/hscrown/oliveKobart"
headers = {"Authorization": "Bearer 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"}

token = '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'
# 모델 및 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained("hscrown/oliveKobart")
model = AutoModelForSeq2SeqLM.from_pretrained("hscrown/oliveKobart")

def generate_summary(text):
    # 입력 텍스트를 토큰화
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)

    # 요약 생성
    summary_ids = model.generate(inputs["input_ids"], max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)

    # 토큰을 텍스트로 디코딩하여 요약 반환
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# Streamlit 애플리케이션 정의
def main():
    st.title("한국어 텍스트 요약기")

    # 텍스트 입력 받기
    input_text = st.text_area("요약할 텍스트를 입력하세요.", height=200)

    # 요약 버튼
    if st.button("요약 생성"):
        if input_text:
            # 요약 생성
            summary = generate_summary(input_text)
            # 결과 출력
            st.subheader("요약 결과")
            st.write(summary)
        else:
            st.warning("텍스트를 입력해주세요.")

if __name__ == "__main__":
    main()
