import streamlit as st
import pandas as pd
import random
import os
import time

# 페이지 설정
st.set_page_config(page_title="외관 퀴즈맞추기", layout="centered")

@st.cache_data
def load_data():
    df = pd.read_csv("answers.csv")
    return df

data = load_data()

# 세션 상태 초기화
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = random.randint(0, len(data) - 1)
if 'wrong_count' not in st.session_state:
    st.session_state.wrong_count = 0

# 화면 UI 구성
st.image("images/logo.png", width=100)
st.title("엔카 사진퀴즈")
st.subheader("(띄어쓰기는 하시면 안됩니다..)")
st.subheader(f"현재 점수: {st.session_state.score}점")

# 메시지가 표시될 빈 공간 확보 (메시지 잔상 방지용)
feedback_container = st.empty()

# 제출 로직 함수
def submit_logic():
    user_answer = st.session_state.input_field.strip()
    current_quiz = data.iloc[st.session_state.current_idx]
    correct_answer = str(current_quiz['answer']).strip()
    
    if user_answer == correct_answer:
        # 정답일 때
        feedback_container.success("정답입니다! 🎉")
        st.session_state.score += 1
        st.session_state.current_idx = random.randint(0, len(data) - 1)
        st.session_state.wrong_count = 0  # 틀린 횟수 초기화
        st.session_state.input_field = "" # 입력창 비우기
        time.sleep(2)                    # 2초 대기
        feedback_container.empty()       # 메시지 삭제
        st.rerun()                       # 다음 문제로 화면 갱신
        
    else:
        # 틀렸을 때
        st.session_state.wrong_count += 1
        st.session_state.input_field = "" # 틀려도 입력창은 비워줌
        
        if st.session_state.wrong_count >= 5:
            # 5번 틀렸을 때 정답 공개
            feedback_container.warning(f"5회 실패! 정답은 [{correct_answer}] 였습니다. 다음 문제로 이동합니다.")
            st.session_state.current_idx = random.randint(0, len(data) - 1)
            st.session_state.wrong_count = 0
            time.sleep(3) # 정답 볼 시간 3초
            feedback_container.empty()
            st.rerun()
        else:
            # 5번 미만일 때 힌트 표시
            hint = current_quiz['hint']
            left_chance = 5 - st.session_state.wrong_count
            feedback_container.error(f"틀렸습니다! (남은 기회: {left_chance}번) 힌트: {hint}")

# 문제 표시
current_quiz = data.iloc[st.session_state.current_idx]
img_path = os.path.join("images", current_quiz['filename'])

if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    st.error(f"이미지를 찾을 수 없습니다: {img_path}")

# 입력창 및 제출 버튼
st.text_input("정답을 입력하세요", key="input_field", on_change=submit_logic)
st.button("제출하기", on_click=submit_logic)