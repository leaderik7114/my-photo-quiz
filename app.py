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

# --- 세션 상태 초기화 ---
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'wrong_count' not in st.session_state:
    st.session_state.wrong_count = 0
if 'is_finished' not in st.session_state:
    st.session_state.is_finished = False
if 'quiz_indices' not in st.session_state:
    indices = list(range(len(data)))
    random.shuffle(indices)
    st.session_state.quiz_indices = indices
    st.session_state.current_step = 0

# --- 화면 UI 구성 ---
st.image("images/logo.png", width=100)
st.title("🚗 엔카 사진퀴즈")

# 모든 문제를 다 풀었는지 확인
if st.session_state.is_finished:
    st.balloons() # 축하 효과
    st.success("🎉 모든 문제를 다 풀었습니다!")
    st.write(f"최종 점수: **{st.session_state.score}** / {len(data)}")
    
    if st.button("처음부터 다시 시작하기"):
        # 모든 상태 초기화
        st.session_state.score = 0
        st.session_state.wrong_count = 0
        st.session_state.current_step = 0
        st.session_state.is_finished = False
        random.shuffle(st.session_state.quiz_indices) # 문제 순서 다시 섞기
        st.rerun()
    
    st.stop() # 아래 퀴즈 로직이 실행되지 않도록 중단

# --- 퀴즈 진행 로직 ---
current_idx = st.session_state.quiz_indices[st.session_state.current_step]
current_quiz = data.iloc[current_idx]

st.subheader("(띄어쓰기 없이 입력해 주세요!)")
col1, col2 = st.columns(2)
with col1:
    st.write(f"현재 점수: **{st.session_state.score}**점")
with col2:
    st.write(f"문제 진행: **{st.session_state.current_step + 1} / {len(data)}**")

img_path = os.path.join("images", current_quiz['filename'])

if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    st.warning("⚠️ 이미지를 불러올 수 없습니다.")

# --- 정답 처리 로직 ---
user_answer = st.chat_input("정답을 입력하고 엔터를 누르세요!")

if user_answer:
    processed_user_answer = user_answer.replace(" ", "").lower()
    correct_answer = str(current_quiz['answer']).replace(" ", "").lower()
    display_answer = str(current_quiz['answer']).strip()
    
    if processed_user_answer == correct_answer:
        st.success(f"정답입니다! 🎉")
        st.session_state.score += 1
        is_correct = True
    else:
        st.session_state.wrong_count += 1
        if st.session_state.wrong_count >= 5:
            st.error(f"❌ 5회 실패! 정답은 [{display_answer}] 였습니다.")
            is_correct = True # 실패해도 다음 문제로 넘어감
        else:
            st.error(f"틀렸습니다! (남은 기회: {5 - st.session_state.wrong_count}번)")
            st.info(f"💡 힌트: {current_quiz['hint']}")
            is_correct = False

    # 다음 문제로 넘어가기 위한 처리
    if is_correct:
        st.session_state.wrong_count = 0
        st.session_state.current_step += 1
        
        # 마지막 문제였는지 체크
        if st.session_state.current_step >= len(data):
            st.session_state.is_finished = True
        
        time.sleep(1.2)
        st.rerun()