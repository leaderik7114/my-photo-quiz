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
st.write(f"현재 점수: **{st.session_state.score}**점")

# 문제 데이터 설정
current_quiz = data.iloc[st.session_state.current_idx]
img_path = os.path.join("images", current_quiz['filename'])

# 문제 표시
if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    st.error(f"이미지를 찾을 수 없습니다: {img_path}")

# --- 하단 고정 입력창 (st.chat_input) ---
# 이 위젯은 제출 후에도 커서가 자동으로 유지됩니다.
user_answer = st.chat_input("정답을 입력하고 엔터를 누르세요!")

if user_answer:
    user_answer = user_answer.strip()
    correct_answer = str(current_quiz['answer']).strip()
    
    if user_answer == correct_answer:
        st.success("정답입니다! 🎉")
        st.session_state.score += 1
        st.session_state.current_idx = random.randint(0, len(data) - 1)
        st.session_state.wrong_count = 0
        time.sleep(1.5) # 정답 확인 시간 (취향에 따라 조절)
        st.rerun()
    else:
        st.session_state.wrong_count += 1
        if st.session_state.wrong_count >= 5:
            st.warning(f"5회 실패! 정답은 [{correct_answer}] 였습니다.")
            st.session_state.current_idx = random.randint(0, len(data) - 1)
            st.session_state.wrong_count = 0
            time.sleep(2.5)
            st.rerun()
        else:
            st.error(f"틀렸습니다! (남은 기회: {5 - st.session_state.wrong_count}번) 힌트: {current_quiz['hint']}")
            # chat_input은 rerun을 하지 않아도 입력칸이 자동으로 비워집니다.