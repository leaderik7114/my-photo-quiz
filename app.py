import streamlit as st
import pandas as pd
import random
import os

# 페이지 설정
st.set_page_config(page_title="외관 퀴즈맞추기", layout="centered")

# 데이터 불러오기
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
if 'feedback' not in st.session_state:
    st.session_state.feedback = ""

# 제출 함수 정의 (입력창 초기화를 위해 콜백 활용)
def submit_answer():
    user_input = st.session_state.input_field.strip()
    current_quiz = data.iloc[st.session_state.current_idx]
    
    if user_input == str(current_quiz['answer']).strip():
        st.session_state.feedback = "correct"
        st.session_state.score += 1
        st.session_state.current_idx = random.randint(0, len(data) - 1)
    else:
        st.session_state.feedback = f"wrong_{current_quiz['hint']}"
    
    # [핵심] 정답/오답 상관없이 입력창 비우기
    st.session_state.input_field = ""

# 화면 구성
st.image("images/logo.png", width=100)
st.title("엔카 사진퀴즈")
st.write(f"현재 점수: **{st.session_state.score}**점")

# 문제 표시
current_quiz = data.iloc[st.session_state.current_idx]
img_path = os.path.join("images", current_quiz['filename'])

if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    st.error(f"이미지 파일을 찾을 수 없습니다: {img_path}")

# 정답 입력 (on_change 또는 엔터 키 대응)
st.text_input("정답은 무엇일까요?", key="input_field", on_change=submit_answer)
st.button("제출하기", on_click=submit_answer)

# 결과 메시지 표시
if st.session_state.feedback == "correct":
    st.success("정답입니다! 🎉")
    st.session_state.feedback = "" # 메시지 초기화
elif st.session_state.feedback.startswith("wrong"):
    hint = st.session_state.feedback.split("_")[1]
    st.error(f"틀렸습니다! 힌트: {hint}")
    st.session_state.feedback = "" # 메시지 초기화