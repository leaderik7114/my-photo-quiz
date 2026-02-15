import streamlit as st

import pandas as pd

import random

import os

import time

# 페이지 설정

st.set_page_config(page_title="외관 퀴즈맞추기", layout="centered")

@st.cache_data

def load_data():

    # 데이터 로드 및 전처리

    df = pd.read_csv("answers.csv")

    return df

data = load_data()

# --- 세션 상태 초기화 (개선: 셔플 방식 도입) ---

if 'score' not in st.session_state:

    st.session_state.score = 0

if 'wrong_count' not in st.session_state:

    st.session_state.wrong_count = 0

if 'quiz_indices' not in st.session_state:

    # 문제 순서를 섞어서 저장 (중복 방지)

    indices = list(range(len(data)))

    random.shuffle(indices)

    st.session_state.quiz_indices = indices

    st.session_state.current_step = 0

# 문제 출제 (큐가 비었으면 다시 셔플)

if st.session_state.current_step >= len(st.session_state.quiz_indices):

    random.shuffle(st.session_state.quiz_indices)

    st.session_state.current_step = 0

current_idx = st.session_state.quiz_indices[st.session_state.current_step]

current_quiz = data.iloc[current_idx]

# 화면 UI 구성

st.image("images/logo.png", width=100)

st.title("🚗 엔카 사진퀴즈")


# 점수 및 진행도 표시

col1, col2 = st.columns(2)

with col1:

    st.write(f"현재 점수: **{st.session_state.score}**점")

""" 
몇문제 진행중인지 확인하는 코드

with col2:

    st.write(f"문제 진행: **{st.session_state.current_step + 1} / {len(data)}**")

 """

# 문제 이미지 설정

img_path = os.path.join("images", current_quiz['filename'])

# 문제 표시 (개선: 예외 처리 강화)

if os.path.exists(img_path):

    st.image(img_path, use_container_width=True)

else:

    st.warning("⚠️ 이미지를 불러올 수 없어 다음 문제로 넘어갑니다.")

    st.session_state.current_step += 1

    st.rerun()

# --- 하단 고정 입력창 ---

user_answer = st.chat_input("정답을 입력하고 엔터를 누르세요!")

if user_answer:

    # 개선: 대소문자 및 공백 처리 강화

    processed_user_answer = user_answer.replace(" ", "").lower()

    correct_answer = str(current_quiz['answer']).replace(" ", "").lower()

    display_answer = str(current_quiz['answer']).strip() # 출력용 원본 정답

    

    if processed_user_answer == correct_answer:

        st.success(f"정답입니다! 🎉 (정답: {display_answer})")

        st.session_state.score += 1

        st.session_state.current_step += 1

        st.session_state.wrong_count = 0

        time.sleep(1.2)

        st.rerun()

    else:

        st.session_state.wrong_count += 1

        if st.session_state.wrong_count >= 5:

            st.error(f"❌ 5회 실패! 정답은 [{display_answer}] 였습니다.")

            st.session_state.current_step += 1

            st.session_state.wrong_count = 0

            time.sleep(2.0)

            st.rerun()

        else:

            remaining = 5 - st.session_state.wrong_count

            st.error(f"틀렸습니다! (남은 기회: {remaining}번)")

            # 힌트 제공 (3회 이상 틀렸을 때만 노출하는 식으로 조절 가능)

            st.info(f"💡 힌트: {current_quiz['hint']}")