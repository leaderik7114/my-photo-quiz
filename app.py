import streamlit as st
import pandas as pd
import random
import os
import time

# 1. 페이지 설정 및 레이아웃 최적화
st.set_page_config(page_title="엔카 사진퀴즈", layout="centered", page_icon="🚗")

# --- CSS 스타일 정의 ---
st.markdown("""
    <style>
    /* 제목 및 레이아웃 스타일 */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        white-space: nowrap;
        word-break: keep-all;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.2rem;
        text-align: center;
        white-space: nowrap;
        color: #666;
        margin-bottom: 2rem;
    }
    /* 데스크톱 모니터에서 너무 퍼지지 않게 너비 제한 */
    .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }
    .made-by-center {
        text-align: center;
        font-size: 0.8rem;
        color: #bbbbbb;
        margin-top: 50px;
        padding-bottom: 20px;
        font-family: sans-serif;
    }
    /* 폼 내부 여백 조절 */
    div[data-testid="stForm"] {
        border: none;
        padding: 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 함수 (중복 제거 포함)
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("answers.csv")
        
        # 파일명에 '후.'(예: A후.png)가 포함된 행은 퀴즈 대상에서 제외 (중복 출제 방지)
        if 'filename' in df.columns:
            df = df[~df['filename'].str.contains('후\\.', na=False)]
            
        if 'hint' not in df.columns:
            df['hint'] = "힌트가 제공되지 않는 문제입니다."
        return df.fillna("")
    except FileNotFoundError:
        st.error("데이터 파일(answers.csv)을 찾을 수 없습니다.")
        return pd.DataFrame(columns=['filename', 'answer', 'hint'])

data = load_data()

# 3. 세션 상태 초기화
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'is_finished' not in st.session_state:
    st.session_state.is_finished = False
if 'wrong_count' not in st.session_state:
    st.session_state.wrong_count = 0

# --- 화면 구성 ---

# [CASE 1] 시작 화면
if not st.session_state.game_started:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("images/logo.png"):
        st.image("images/logo.png", use_container_width=True)
    
    st.markdown('<p class="main-title">🚗 외관 사진 퀴즈</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">앞/뒤 사진을 동시에 보고 등급을 맞춰보세요!</p>', unsafe_allow_html=True)
    
    st.write("---")
    quiz_count_options = [10, 30, 50, "전체"]
    selected_count = st.select_slider("출제할 문제 수 선택", options=quiz_count_options, value=10)
    
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

    st.markdown('<div class="made-by-center">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# [CASE 2] 결과 화면
elif st.session_state.is_finished:
    st.balloons()
    st.title("🏁 모든 문제를 풀었습니다!")
    st.markdown(f"### 최종 점수: **{st.session_state.score}** / {len(st.session_state.quiz_indices)}")
    
    if st.button("처음으로 돌아가기", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    st.markdown('<div class="made-by-center">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# [CASE 3] 게임 진행 중
else:
    with st.sidebar:
        st.markdown("### 📊 현재 진행 상황")
        st.write(f"맞힌 개수: {st.session_state.score}")
        if st.button("🏠 그만하기", use_container_width=True):
            st.session_state.game_started = False
            st.rerun()

    # 현재 문제 데이터 추출
    total_q = len(st.session_state.quiz_indices)
    current_idx = st.session_state.quiz_indices[st.session_state.current_step]
    current_quiz = data.iloc[current_idx]

    # --- 상단 레이아웃 여백 확보 ---
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True) # 상단 여백 추가
    
    # 정보 표시 (한눈에 들어오게 디자인 변경)
    col_status1, col_status2 = st.columns([2, 1])
    with col_status1:
        st.markdown(f"#### 📝 문제 **{st.session_state.current_step + 1}** / {total_q}")
    with col_status2:
        st.markdown(f"#### ⭐ 점수: **{st.session_state.score}**")
    
    st.progress((st.session_state.current_step + 1) / total_q)
    st.markdown("---") # 구분선 추가로 가독성 확보

    # 이미지 경로 처리
    base_file = current_quiz['filename']
    name, ext = os.path.splitext(base_file)
    front_path = os.path.join("images", base_file)
    back_path = os.path.join("images", f"{name}후{ext}")

    # 이미지 출력 (여백 및 캡션 강조)
    img_col1, img_col2 = st.columns(2)
    with img_col1:
        if os.path.exists(front_path):
            st.image(front_path, caption="[ 차량 앞면 ]", use_container_width=True)
        else:
            st.error("앞면 사진을 찾을 수 없습니다.")
    with img_col2:
        if os.path.exists(back_path):
            st.image(back_path, caption="[ 차량 뒷면 ]", use_container_width=True)
        else:
            st.warning("뒷면 사진('후')이 없습니다.")

    st.write("") # 간격

    # 정답 입력 폼 (카드 형태 유지)
    with st.form(key="quiz_form", clear_on_submit=True):
        st.markdown("**이 차량의 정확한 등급을 입력하세요**")
        user_answer = st.text_input("입력창", label_visibility="collapsed", placeholder="여기에 정답 입력...")
        submit_btn = st.form_submit_button("정답 확인하기", use_container_width=True)

        if submit_btn:
            if user_answer:
                processed_user = user_answer.replace(" ", "").lower()
                correct_answer = str(current_quiz['answer']).replace(" ", "").lower()
                display_answer = str(current_quiz['answer']).strip()

                if processed_user == correct_answer:
                    st.success(f"정답입니다! 🎉 정답: {display_answer}")
                    st.session_state.score += 1
                    st.session_state.wrong_count = 0
                    st.session_state.current_step += 1
                    
                    if st.session_state.current_step >= total_q:
                        st.session_state.is_finished = True
                    
                    time.sleep(1.0)
                    st.rerun()
                else:
                    st.session_state.wrong_count += 1
                    if st.session_state.wrong_count >= 5:
                        st.error(f"❌ 5회 실패! 정답은 [{display_answer}] 였습니다.")
                        time.sleep(2.0)
                        st.session_state.wrong_count = 0
                        st.session_state.current_step += 1
                        if st.session_state.current_step >= total_q:
                            st.session_state.is_finished = True
                        st.rerun()
                    else:
                        st.warning(f"틀렸습니다! (남은 기회: {5 - st.session_state.wrong_count}번)")
                        st.info(f"💡 힌트: {current_quiz['hint']}")
            else:
                st.warning("정답을 입력한 후 버튼을 눌러주세요.")
