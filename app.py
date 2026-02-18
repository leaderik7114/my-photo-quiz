import streamlit as st
import pandas as pd
import random
import os
import time

# 1. 페이지 설정
st.set_page_config(page_title="엔카 사진퀴즈", layout="centered", page_icon="🚗")

# 2. 데이터 로드 함수
@st.cache_data
def load_data():
    try:
        # answers.csv 로드 (브랜드, 차종 등 추가 컬럼이 있어도 유연하게 대응)
        df = pd.read_csv("answers.csv")
        # 힌트 컬럼이 없을 경우를 대비해 기본값 설정
        if 'hint' not in df.columns:
            df['hint'] = "힌트가 제공되지 않는 문제입니다."
        return df.fillna("")
    except FileNotFoundError:
        st.error("데이터 파일(answers.csv)을 찾을 수 없습니다. 경로를 확인해주세요.")
        return pd.DataFrame(columns=['filename', 'answer', 'hint'])

data = load_data()

# 3. 세션 상태 초기화 (게임 시작 여부 플래그 추가)
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'is_finished' not in st.session_state:
    st.session_state.is_finished = False

# --- 화면 구성 ---

# [CASE 1] 게임이 아직 시작되지 않았을 때 (첫 화면)
if not st.session_state.game_started:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 로고 표시 (경로에 파일이 있을 경우)
        if os.path.exists("images/logo.png"):
            st.image("images/logo.png", use_container_width=True)
        
        st.title("🚗 외관사진퀴즈 ")
        st.write("외관 사진만 보고 차량의 등급을 맞춰보세요!")
        st.write("---")
        
        # 문제 수 선택
        quiz_count_options = [10, 30, 50, "전체"]
        selected_count = st.select_slider(
            "출제할 문제 수를 선택하세요",
            options=quiz_count_options,
            value=10
        )
        
        st.write("<br>", unsafe_allow_html=True)
        
        # 시작 버튼
        if st.button("🚀 게임 시작하기", use_container_width=True, type="primary"):
            # 문제 섞기 및 선택
            all_indices = list(range(len(data)))
            random.shuffle(all_indices)
            
            if selected_count != "전체":
                limit = min(int(selected_count), len(all_indices))
                selected_indices = all_indices[:limit]
            else:
                selected_indices = all_indices
            
            # 게임 데이터 세션에 저장
            st.session_state.quiz_indices = selected_indices
            st.session_state.current_step = 0
            st.session_state.score = 0
            st.session_state.wrong_count = 0
            st.session_state.game_started = True
            st.session_state.is_finished = False
            st.rerun()

# [CASE 2] 모든 문제를 풀었을 때 (결과 화면)
elif st.session_state.is_finished:
    st.balloons()
    st.title("🏁 퀴즈 종료!")
    st.markdown(f"### 최종 점수: **{st.session_state.score}** / {len(st.session_state.quiz_indices)}")
    
    if st.button("처음으로 돌아가기", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()

# [CASE 3] 게임 진행 중
else:
    # 사이드바에는 간단한 조작 버튼만 배치
    if st.sidebar.button("🏠 처음으로 (그만하기)"):
        st.session_state.game_started = False
        st.rerun()

    # 현재 문제 정보 가져오기
    total_q = len(st.session_state.quiz_indices)
    current_idx = st.session_state.quiz_indices[st.session_state.current_step]
    current_quiz = data.iloc[current_idx]

    # 상단 정보 표시
    st.subheader("외관사진으로 등급맞추기!")
    progress_val = (st.session_state.current_step) / total_q
    st.progress(progress_val)
    
    c1, c2 = st.columns(2)
    with c1: st.write(f"현재 점수: **{st.session_state.score}**점")
    with c2: st.write(f"문제 진행: **{st.session_state.current_step + 1} / {total_q}**")

    # 이미지 로드
    img_path = os.path.join("images", current_quiz['filename'])
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
    else:
        st.error(f"이미지를 찾을 수 없습니다: {current_quiz['filename']}")

    # 입력창 (채팅 입력 방식 혹은 텍스트 입력 방식 선택 가능)
    user_answer = st.chat_input("정답을 입력하고 엔터를 누르세요!")

    if user_answer:
        # 공백 제거 및 소문자 변환 비교
        processed_user = user_answer.replace(" ", "").lower()
        correct_answer = str(current_quiz['answer']).replace(" ", "").lower()
        display_answer = str(current_quiz['answer']).strip()
        
        if processed_user == correct_answer:
            st.success("정답입니다! 🎉")
            st.session_state.score += 1
            is_correct = True
        else:
            st.session_state.wrong_count += 1
            if st.session_state.wrong_count >= 5:
                st.error(f"❌ 5회 실패! 정답은 [{display_answer}] 였습니다.")
                is_correct = True # 5번 틀리면 정답 공개 후 다음 문제로
            else:
                st.warning(f"틀렸습니다! (남은 기회: {5 - st.session_state.wrong_count}번)")
                st.info(f"💡 힌트: {current_quiz['hint']}")
                is_correct = False

        if is_correct:
            st.session_state.wrong_count = 0
            st.session_state.current_step += 1
            
            # 모든 문제를 다 풀었는지 확인
            if st.session_state.current_step >= total_q:
                st.session_state.is_finished = True
            
            time.sleep(1.0)
            st.rerun()