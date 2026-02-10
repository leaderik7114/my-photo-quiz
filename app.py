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
if 'trigger_check' not in st.session_state:
    st.session_state.trigger_check = False
# [추가] 입력창 초기화를 위한 랜덤 키 번호
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# 화면 UI 구성
st.image("images/logo.png", width=100)
st.title("엔카 사진퀴즈")
st.subheader("(띄어쓰기는 하시면 안됩니다..)")
st.subheader(f"현재 점수: {st.session_state.score}점")

current_quiz = data.iloc[st.session_state.current_idx]
img_path = os.path.join("images", current_quiz['filename'])

if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)

# 콜백 함수
def on_input_submit():
    st.session_state.trigger_check = True

# [수정] key 값에 세션 변수를 넣어서 매번 바뀌게 설정
st.text_input("정답을 입력하세요", key=f"input_{st.session_state.input_key}", on_change=on_input_submit)
st.button("제출하기", on_click=on_input_submit)

# --- 실제 정답 체크 로직 ---
if st.session_state.trigger_check:
    # 현재 활성화된 키의 값을 가져옴
    user_answer = st.session_state[f"input_{st.session_state.input_key}"].strip()
    correct_answer = str(current_quiz['answer']).strip()
    
    if user_answer == correct_answer:
        st.success("정답입니다! 🎉")
        st.session_state.score += 1
        st.session_state.current_idx = random.randint(0, len(data) - 1)
        st.session_state.wrong_count = 0
        st.session_state.input_key += 1 # [핵심] 키 번호를 바꿔서 입력창 리셋
        st.session_state.trigger_check = False
        time.sleep(1)
        st.rerun()
    else:
        st.session_state.wrong_count += 1
        if st.session_state.wrong_count >= 5:
            st.warning(f"5회 실패! 정답은 [{correct_answer}] 였습니다.")
            st.session_state.current_idx = random.randint(0, len(data) - 1)
            st.session_state.wrong_count = 0
            st.session_state.input_key += 1 # [핵심] 키 번호를 바꿔서 입력창 리셋
            st.session_state.trigger_check = False
            time.sleep(2)
            st.rerun()
        else:
            st.error(f"틀렸습니다! (남은 기회: {5 - st.session_state.wrong_count}번) 힌트: {current_quiz['hint']}")
            st.session_state.input_key +=1
            st.session_state.trigger_check = False
            time.sleep(0.1)
            st.rerun()