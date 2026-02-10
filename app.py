import streamlit as st
import pandas as pd
import random
import os
import time

# 페이지 설정
st.set_page_config(page_title="외관 퀴즈맞추기", layout="centered")

@st.cache_data
def load_data():
    # 실제 파일 경로에 맞춰 수정하세요
    df = pd.read_csv("answers.csv")
    return df

data = load_data()

# 세션 상태 초기화
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = random.randint(0, len(data) - 1)
if 'feedback' not in st.session_state:
    st.session_state.feedback = None

# 제출 로직 함수
def submit_logic():
    user_answer = st.session_state.input_field.strip()
    correct_answer = str(data.iloc[st.session_state.current_idx]['answer']).strip()
    
    if user_answer == correct_answer:
        st.session_state.feedback = ("success", "정답입니다! 🎉")
        st.session_state.score += 1
        # 정답일 때만 즉시 다음 문제 인덱스 준비
        st.session_state.current_idx = random.randint(0, len(data) - 1)
        time.sleep(0.7)
        st.rerun()
    else:
        hint = data.iloc[st.session_state.current_idx]['hint']
        st.session_state.feedback = ("error", f"틀렸습니다! 힌트: {hint}")
    
    # 입력창 초기화
    st.session_state.input_field = ""

# 화면 UI 구성
st.image("images/logo.png", width=100)
st.title("엔카 사진퀴즈")
st.subheader(f"현재 점수: {st.session_state.score}점")

# 문제 표시
current_quiz = data.iloc[st.session_state.current_idx]
img_path = os.path.join("images", current_quiz['filename'])

if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    st.error(f"이미지를 찾을 수 없습니다: {img_path}")

# 입력창 및 제출 버튼
# 엔터를 쳐도 submit_logic이 실행되도록 on_change 연결
st.text_input("정답을 입력하세요", key="input_field", on_change=submit_logic)
st.button("제출하기", on_click=submit_logic)

# 결과 메시지 출력 (제출 후에만 표시됨)
if st.session_state.feedback:
    type, message = st.session_state.feedback
    if type == "success":
        st.success(message)
    else:
        st.error(message)
    # 메시지를 한 번 보여준 후 다음 입력을 위해 상태 초기화 (선택 사항)
    st.session_state.feedback = None