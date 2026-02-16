import streamlit as st
import pandas as pd
import random
import os
import time

# 페이지 설정
st.set_page_config(page_title="엔카 사진퀴즈", layout="centered")

@st.cache_data
def load_data():
    # 데이터 로드 (브랜드, 차종 컬럼이 나중에 추가되어도 문제없이 작동함)
    df = pd.read_csv("answers.csv")
    return df

data = load_data()

# --- 사이드바 설정 ---
st.sidebar.title("🎮 퀴즈 설정")
quiz_count = st.sidebar.radio("출제 문제 수", [10, 30, 50, "전체"], index=0)

# [게임 시작/리셋] 버튼 - 이 버튼을 누르면 설정된 개수대로 문제를 새로 뽑습니다.
if st.sidebar.button("🔄 게임 시작 / 리셋"):
    all_indices = list(range(len(data)))
    random.shuffle(all_indices)
    
    # 선택한 개수만큼 슬라이싱 (보유한 문제보다 선택한 수가 크면 전체 문제 출제)
    if quiz_count != "전체":
        limit = min(int(quiz_count), len(all_indices))
        selected_indices = all_indices[:limit]
    else:
        selected_indices = all_indices
    
    # 세션 상태 초기화
    st.session_state.quiz_indices = selected_indices
    st.session_state.current_step = 0
    st.session_state.score = 0
    st.session_state.wrong_count = 0
    st.session_state.is_finished = False
    st.rerun()

# --- 세션 상태 최초 초기화 (앱 처음 실행 시) ---
if 'quiz_indices' not in st.session_state:
    st.info("왼쪽 사이드바에서 문제 수를 선택하고 [게임 시작] 버튼을 눌러주세요!")
    st.stop()

# --- 화면 UI 구성 ---
st.image("images/logo.png", width=100)
st.title("🚗 엔카 사진퀴즈")

# 모든 문제를 다 풀었을 때
if st.session_state.is_finished:
    st.balloons()
    st.success("🎉 준비된 문제를 모두 완료했습니다!")
    st.write(f"최종 점수: **{st.session_state.score}** / {len(st.session_state.quiz_indices)}")
    if st.button("다시 도전하기"):
        st.session_state.is_finished = False # 리셋 로직은 위쪽 사이드바 버튼과 공유하도록 유도
        st.info("사이드바의 리셋 버튼을 눌러주세요.")
    st.stop()

# 문제 진행도 및 데이터 설정
total_q = len(st.session_state.quiz_indices)
current_idx = st.session_state.quiz_indices[st.session_state.current_step]
current_quiz = data.iloc[current_idx]

st.subheader("외관사진만으로 등급을 맞춰보세요!")
col1, col2 = st.columns(2)
with col1:
    st.write(f"현재 점수: **{st.session_state.score}**점")
with col2:
    st.write(f"문제 진행: **{st.session_state.current_step + 1} / {total_q}**")

# 이미지 표시
img_path = os.path.join("images", current_quiz['filename'])
if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    st.error(f"이미지를 찾을 수 없습니다: {current_quiz['filename']}")

# --- 정답 입력 창 ---
user_answer = st.chat_input("정답을 입력하고 엔터를 누르세요!")

if user_answer:
    processed_user_answer = user_answer.replace(" ", "").lower()
    correct_answer = str(current_quiz['answer']).replace(" ", "").lower()
    display_answer = str(current_quiz['answer']).strip()
    
    if processed_user_answer == correct_answer:
        st.success("정답입니다! 🎉")
        st.session_state.score += 1
        is_correct = True
    else:
        st.session_state.wrong_count += 1
        if st.session_state.wrong_count >= 5:
            st.error(f"❌ 5회 실패! 정답은 [{display_answer}] 였습니다.")
            is_correct = True # 실패해도 다음으로 넘김
        else:
            st.error(f"틀렸습니다! (남은 기회: {5 - st.session_state.wrong_count}번)")
            st.info(f"💡 힌트: {current_quiz['hint']}")
            is_correct = False

    if is_correct:
        st.session_state.wrong_count = 0
        st.session_state.current_step += 1
        
        # 종료 체크
        if st.session_state.current_step >= total_q:
            st.session_state.is_finished = True
        
        time.sleep(1.2)
        st.rerun()