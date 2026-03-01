import streamlit as st
import pandas as pd
import random
import os
import time
import difflib

# 1. 페이지 설정
st.set_page_config(page_title="엔카 사진퀴즈 (객관식)", layout="centered", page_icon="🚗")

# --- CSS 스타일 ---
st.markdown("""
    <style>
    .main-title { font-size: 2.8rem; font-weight: 800; text-align: center; margin-bottom: 0.5rem; }
    .sub-title { font-size: 1.2rem; text-align: center; color: #666; margin-bottom: 2rem; }
    .block-container { max-width: 800px; padding-top: 2rem; }
    .made-by-center { text-align: center; font-size: 0.8rem; color: #bbbbbb; margin-top: 50px; }
    /* 버튼 간격 조절 */
    div.stButton > button { margin-bottom: 10px; height: 3.5rem; font-size: 1.1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 및 유사 보기 생성 함수
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("answers.csv")
        # '후.' 포함 파일 제외
        if 'filename' in df.columns:
            df = df[~df['filename'].str.contains('후\\.', na=False)]
        if 'hint' not in df.columns:
            df['hint'] = "힌트가 제공되지 않는 문제입니다."
        return df.fillna("")
    except FileNotFoundError:
        st.error("데이터 파일(answers.csv)을 찾을 수 없습니다.")
        return pd.DataFrame(columns=['filename', 'answer', 'hint'])

def get_similar_options(current_answer, all_answers):
    """현재 정답과 텍스트가 유사한 오답 3개를 포함하여 총 4개의 보기를 생성합니다."""
    current_answer = str(current_answer).strip()
    # 자기 자신 제외한 유니크 목록
    others = list(set([str(ans).strip() for ans in all_answers if str(ans).strip() != current_answer]))
    
    # 텍스트 유사도가 높은 상위 10개 추출 (cutoff를 낮게 잡아 후보를 넉넉히 확보)
    similar_candidates = difflib.get_close_matches(current_answer, others, n=10, cutoff=0.1)
    
    # 유사 후보가 부족하면 나머지에서 랜덤 채움
    if len(similar_candidates) < 3:
        remaining = [a for a in others if a not in similar_candidates]
        similar_candidates += random.sample(remaining, min(len(remaining), 3 - len(similar_candidates)))
    
    # 최종 3개 선택 + 정답 1개
    final_options = random.sample(similar_candidates, 3) + [current_answer]
    random.shuffle(final_options)
    return final_options

data = load_data()

# 3. 세션 상태 초기화
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'is_finished' not in st.session_state:
    st.session_state.is_finished = False

# --- 화면 구성 ---

# [CASE 1] 시작 화면
if not st.session_state.game_started:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("images/logo.png"):
        st.image("images/logo.png", use_container_width=True)
    
    st.markdown('<p class="main-title">🚗 외관 사진 퀴즈</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">비슷한 등급 중에서 정답을 찾아보세요!</p>', unsafe_allow_html=True)
    
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
        st.session_state.game_started = True
        st.session_state.is_finished = False
        # 보기 미리 생성 방지를 위해 세션 정리
        for key in list(st.session_state.keys()):
            if key.startswith("opts_"): del st.session_state[key]
        st.rerun()

    st.markdown('<div class="made-by-center">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# [CASE 2] 결과 화면
elif st.session_state.is_finished:
    st.balloons()
    st.markdown(f"<h2 style='text-align:center;'>🏁 종료!</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center;'>최종 점수: {st.session_state.score} / {len(st.session_state.quiz_indices)}</h3>", unsafe_allow_html=True)
    
    if st.button("처음으로 돌아가기", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    st.markdown('<div class="made-by-center">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# [CASE 3] 게임 진행 중
else:
    total_q = len(st.session_state.quiz_indices)
    current_idx = st.session_state.quiz_indices[st.session_state.current_step]
    current_quiz = data.iloc[current_idx]
    correct_answer = str(current_quiz['answer']).strip()

    # 사이드바 진행도
    with st.sidebar:
        st.markdown(f"### 📊 진행 상황 ({st.session_state.current_step + 1}/{total_q})")
        st.write(f"현재 점수: {st.session_state.score}")
        if st.button("🏠 중단하고 홈으로"):
            st.session_state.game_started = False
            st.rerun()

    # 상단 정보
    st.progress((st.session_state.current_step + 1) / total_q)
    st.markdown(f"#### 📝 문제 {st.session_state.current_step + 1}")
    st.write("---")

    # 이미지 출력
    base_file = current_quiz['filename']
    name, ext = os.path.splitext(base_file)
    front_path = os.path.join("images", base_file)
    back_path = os.path.join("images", f"{name}후{ext}")

    img_col1, img_col2 = st.columns(2)
    with img_col1:
        if os.path.exists(front_path):
            st.image(front_path, caption="앞면", use_container_width=True)
    with img_col2:
        if os.path.exists(back_path):
            st.image(back_path, caption="뒷면", use_container_width=True)

    st.write("---")

    # --- 객관식 보기 로직 ---
    option_key = f"opts_{current_idx}"
    if option_key not in st.session_state:
        st.session_state[option_key] = get_similar_options(correct_answer, data['answer'])
    
    options = st.session_state[option_key]

    st.markdown("**차량의 등급을 선택하세요:**")
    
    # 피드백 영역
    feedback_placeholder = st.empty()

    # 2x2 버튼 레이아웃
    cols = st.columns(2)
    selected_option = None

    for i, option in enumerate(options):
        with cols[i % 2]:
            if st.button(option, use_container_width=True, key=f"opt_{i}"):
                selected_option = option

    # 정답 체크 로직
    if selected_option:
        if selected_option == correct_answer:
            feedback_placeholder.success(f"정답입니다! 🎉")
            st.session_state.score += 1
            time.sleep(1)
        else:
            feedback_placeholder.error(f"틀렸습니다! ❌ 정답: {correct_answer}")
            st.info(f"💡 힌트: {current_quiz['hint']}")
            time.sleep(2.5) # 오답 시에는 정답과 힌트를 볼 시간을 더 줌

        # 다음 문제 이동
        st.session_state.current_step += 1
        if st.session_state.current_step >= total_q:
            st.session_state.is_finished = True
        st.rerun()