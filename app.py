import streamlit as st
import pandas as pd
import random
import os

# 페이지 설정
st.set_page_config(page_title="1000장 사진 퀴즈", layout="centered")

# 데이터 불러오기 (캐싱 처리로 속도 최적화)
@st.cache_data
def load_data():
    df = pd.read_csv("answers.csv")
    return df

data = load_data()

# 게임 상태 유지용 변수 설정
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = random.randint(0, len(data) - 1)

# 화면 상단
st.title("🏆 무한 사진 퀴즈")
st.write(f"현재 점수: {st.session_state.score}점")

# 문제 표시
current_quiz = data.iloc[st.session_state.current_idx]
img_path = os.path.join("images", current_quiz['filename'])

if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    st.error(f"이미지 파일을 찾을 수 없습니다: {img_path}")

# 정답 입력
user_input = st.text_input("정답은 무엇일까요?", key="input_field").strip()

if st.button("제출하기"):
    if user_input == str(current_quiz['answer']).strip():
        st.success("정답입니다! 🎉")
        st.session_state.score += 1
        # 다음 문제로 넘어가기 위한 인덱스 변경
        st.session_state.current_idx = random.randint(0, len(data) - 1)
        st.button("다음 문제로")
    else:
        st.error(f"틀렸습니다! 힌트: {current_quiz['hint']}")