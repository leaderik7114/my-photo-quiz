import streamlit as st
import pandas as pd
import random
import os
import time

# 1. 페이지 설정
st.set_page_config(page_title="엔카 사진퀴즈", layout="centered", page_icon="🚗")

# --- CSS 스타일 정의 (줄바꿈 방지 및 디자인 고정) ---
st.markdown("""
    <style>
    /* 제목 스타일: 줄바꿈 절대 방지 */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        white-space: nowrap;      /* 한 줄 고정 */
        word-break: keep-all;     /* 단어 단위 끊김 방지 */
        margin-bottom: 0.5rem;
    }
    /* 설명 문구 스타일: 가독성 유지 */
    .sub-title {
        font-size: 1.2rem;
        text-align: center;
        white-space: nowrap;
        color: #666;
        margin-bottom: 2rem;
    }
    /* 메인 컨테이너 너비 제한 (너무 퍼지지 않게) */
    .block-container {
        max-width: 600px;
        padding-top: 5rem;
    }
    /* 중앙 하단 소소한 문구 스타일 */
    .made-by-center {
        text-align: center;
        font-size: 0.8rem;
        color: #bbbbbb;
        margin-top: 50px; /* 위쪽 콘텐츠와 간격 조절 */
        padding-bottom: 20px;
        font-family: sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)
# 2. 데이터 로드 함수
@st.cache_data
def load_data():
    try:
        # answers.csv 로드 (브랜드, 차종 등 추가 컬럼이 있어도 유연하게 대응)
        df = pd.read_csv("answers.csv")

        if 'filename' in df.columns:
            # '후.'이 포함되지 않은 행만 필터링하여 다시 df에 저장
            df = df[~df['filename'].str.contains('후\\.', na=False)]


        
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
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 로고 표시
    if os.path.exists("images/logo.png"):
        st.image("images/logo.png", use_container_width=True)
    
    # CSS 클래스가 적용된 제목과 설명
    st.markdown('<p class="main-title">🚗 외관 사진 퀴즈</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">사진만 보고 차량의 등급을 맞춰보세요!</p>', unsafe_allow_html=True)
    
    st.write("---")
    
    # 문제 수 선택
    quiz_count_options = [10, 30, 50, "전체"]
    selected_count = st.select_slider(
        "출제할 문제 수를 선택하세요",
        options=quiz_count_options,
        value=10
    )
    
    st.write("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 게임 시작하기", use_container_width=True, type="primary"):
        all_indices = list(range(len(data)))
        random.shuffle(all_indices)
        
        if selected_count != "전체":
            limit = min(int(selected_count), len(all_indices))
            selected_indices = all_indices[:limit]
        else:
            selected_indices = all_indices
        
        st.session_state.quiz_indices = selected_indices
        st.session_state.current_step = 0
        st.session_state.score = 0
        st.session_state.wrong_count = 0
        st.session_state.game_started = True
        st.session_state.is_finished = False
        st.rerun()

        # --- 시작 화면 하단에 중앙 배치 ---
    st.markdown('<div class="made-by-center">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# [CASE 2] 모든 문제를 풀었을 때 (결과 화면)
elif st.session_state.is_finished:
    st.balloons()
    st.title("🏁 퀴즈 종료!")
    st.markdown(f"### 최종 점수: **{st.session_state.score}** / {len(st.session_state.quiz_indices)}")
    
    if st.button("처음으로 돌아가기", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
# 종료 화면 하단에도 워터마크 표시
    st.markdown('<div class="made-by-center">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)


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

   # --- 레이아웃 구성 ---
    # 중앙 정렬을 위한 컨테이너
    main_container = st.container()

    with main_container:
        # 진행도 표시
        st.caption(f"문제 {st.session_state.current_step + 1} / {total_q}  |  현재 점수: {st.session_state.score}점")
        st.progress((st.session_state.current_step + 1) / total_q)
        
        st.subheader("🚗 이 차량의 등급은 무엇일까요?")

        # 이미지 경로 설정
        base_file = current_quiz['filename']
        name, ext = os.path.splitext(base_file)
        front_path = os.path.join("images", base_file)
        back_path = os.path.join("images", f"{name}후{ext}")

        # 사진 출력 (좌우 배치)
        img_col1, img_col2 = st.columns(2)
        with img_col1:
            if os.path.exists(front_path):
                st.image(front_path, caption="앞면", use_container_width=True)
        with img_col2:
            if os.path.exists(back_path):
                st.image(back_path, caption="뒷면", use_container_width=True)

        st.write("") # 간격 조절
        
        # --- 입력 폼 (사진 바로 아래 배치) ---
        # st.form을 사용하면 엔터키로 제출이 가능하며 시선이 분산되지 않습니다.
        with st.form(key="answer_form", clear_on_submit=True):
            user_answer = st.text_input("정답을 입력하세요 (엔터 키 가능)", placeholder="예: 그랜저 IG 프리미엄")
            submit_button = st.form_submit_button("정답 확인", use_container_width=True)

            if submit_button and user_answer:
                processed_user = user_answer.replace(" ", "").lower()
                correct_answer = str(current_quiz['answer']).replace(" ", "").lower()
                display_answer = str(current_quiz['answer']).strip()
                
                if processed_user == correct_answer:
                    st.success("정답입니다! 🎉")
                    st.session_state.score += 1
                    st.session_state.wrong_count = 0
                    st.session_state.current_step += 1
                    
                    if st.session_state.current_step >= total_q:
                        st.session_state.is_finished = True
                    
                    time.sleep(1.2)
                    st.rerun()
                else:
                    st.session_state.wrong_count += 1
                    if st.session_state.wrong_count >= 5:
                        st.error(f"❌ 정답은 [{display_answer}] 였습니다.")
                        time.sleep(2.0)
                        st.session_state.wrong_count = 0
                        st.session_state.current_step += 1
                        if st.session_state.current_step >= total_q:
                            st.session_state.is_finished = True
                        st.rerun()
                    else:
                        st.warning(f"틀렸습니다! (남은 기회: {5 - st.session_state.wrong_count}번)")
                        st.info(f"💡 힌트: {current_quiz['hint']}")

        if is_correct:
            st.session_state.wrong_count = 0
            st.session_state.current_step += 1
            
            # 모든 문제를 다 풀었는지 확인
            if st.session_state.current_step >= total_q:
                st.session_state.is_finished = True
            
            time.sleep(1.0)
            st.rerun()