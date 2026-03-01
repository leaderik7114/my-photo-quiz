import streamlit as st
import pandas as pd
import random
import os
import time
import difflib

# 1. 페이지 설정 및 스타일 정의
st.set_page_config(page_title="엔카 사진퀴즈 (고난도)", layout="centered", page_icon="🚗")

st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 800; text-align: center; margin-bottom: 0.5rem; color: #FF2E2E; }
    .sub-title { font-size: 1.1rem; text-align: center; color: #666; margin-bottom: 2rem; }
    .block-container { max-width: 700px; padding-top: 2rem; }
    .stButton > button { 
        height: 4rem; 
        font-size: 1.1rem !important; 
        font-weight: 600;
        border-radius: 10px;
        margin-bottom: 5px;
    }
    .made-by-center { text-align: center; font-size: 0.8rem; color: #bbbbbb; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 및 정교한 유사 보기 생성 로직
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("answers.csv")
        if 'filename' in df.columns:
            df = df[~df['filename'].str.contains('후\\.', na=False)]
        if 'hint' not in df.columns:
            df['hint'] = "힌트가 없습니다."
        return df.fillna("")
    except FileNotFoundError:
        st.error("데이터 파일(answers.csv)을 찾을 수 없습니다.")
        return pd.DataFrame(columns=['filename', 'answer', 'hint'])

def get_advanced_similar_options(current_answer, all_answers):
    """단어 포함 여부와 글자 일치도를 계산해 가장 유사한 오답 3개를 추출합니다."""
    current_answer = str(current_answer).strip()
    # 자기 자신 제외한 유니크 목록
    others = list(set([str(ans).strip() for ans in all_answers if str(ans).strip() != current_answer]))
    
    scored_candidates = []
    for candidate in others:
        score = 0
        # 점수 알고리즘 1: 핵심 단어 포함 여부 (가장 강력함)
        if current_answer in candidate or candidate in current_answer:
            score += 20
        
        # 점수 알고리즘 2: 공통 글자 집합 크기 (글자 구성의 유사성)
        common_chars = set(current_answer) & set(candidate)
        score += len(common_chars) * 2
        
        # 점수 알고리즘 3: 전체 문구 유사도 비율
        ratio = difflib.SequenceMatcher(None, current_answer, candidate).ratio()
        score += ratio * 10
        
        scored_candidates.append((candidate, score))
    
    # 점수 높은 순으로 정렬
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # 상위 10개 중 3개를 무작위로 뽑아 '너무 뻔하지 않은' 유사 보기 구성
    pool_size = min(len(scored_candidates), 10)
    top_pool = [c[0] for c in scored_candidates[:pool_size]]
    
    # 후보가 부족할 경우 대비
    if len(top_pool) < 3:
        top_pool += random.sample(others, min(len(others), 3 - len(top_pool)))
    
    final_options = random.sample(top_pool, 3) + [current_answer]
    random.shuffle(final_options)
    return final_options

data = load_data()

# 3. 세션 상태 관리
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'is_finished' not in st.session_state:
    st.session_state.is_finished = False

# --- [화면 1] 시작 페이지 ---
if not st.session_state.game_started:
    st.markdown("<br>", unsafe_allow_html=True)
    if os.path.exists("images/logo.png"):
        st.image("images/logo.png", use_container_width=True)
    
    st.markdown('<p class="main-title">🚗 외관 사진 퀴즈</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">사진을 보고 정확한 모델 등급을 선택하세요!</p>', unsafe_allow_html=True)
    
    st.write("---")
    quiz_count = st.select_slider("문제 수 선택", options=[5, 10, 20, "전체"], value=10)
    
    if st.button("🚀 게임 시작하기", use_container_width=True, type="primary"):
        all_indices = list(range(len(data)))
        random.shuffle(all_indices)
        limit = len(all_indices) if quiz_count == "전체" else min(int(quiz_count), len(all_indices))
        
        st.session_state.quiz_indices = all_indices[:limit]
        st.session_state.current_step = 0
        st.session_state.score = 0
        st.session_state.game_started = True
        st.session_state.is_finished = False
        # 이전 보기 기록 삭제
        for k in list(st.session_state.keys()):
            if k.startswith("opts_"): del st.session_state[k]
        st.rerun()

# --- [화면 2] 결과 페이지 ---
elif st.session_state.is_finished:
    st.balloons()
    st.markdown(f"<h2 style='text-align:center;'>🏁 수고하셨습니다!</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center;'>최종 점수: {st.session_state.score} / {len(st.session_state.quiz_indices)}</h3>", unsafe_allow_html=True)
    
    if st.button("다시 도전하기", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()

# --- [화면 3] 게임 진행 페이지 ---
else:
    total_q = len(st.session_state.quiz_indices)
    current_idx = st.session_state.quiz_indices[st.session_state.current_step]
    current_quiz = data.iloc[current_idx]
    correct_answer = str(current_quiz['answer']).strip()

    # 상단 헤더 및 진행도
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"#### 📝 문제 {st.session_state.current_step + 1} / {total_q}")
    with col2:
        if st.button("🏠 홈", key="home_btn"):
            st.session_state.game_started = False
            st.rerun()
            
    st.progress((st.session_state.current_step + 1) / total_q)

    # 이미지 영역
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

    # 보기 생성 및 고정
    option_key = f"opts_{current_idx}"
    if option_key not in st.session_state:
        st.session_state[option_key] = get_advanced_similar_options(correct_answer, data['answer'])
    
    options = st.session_state[option_key]

    # 객관식 버튼 UI
    st.markdown("**이 차량의 정확한 등급명은?**")
    feedback_area = st.empty()
    cols = st.columns(2)
    user_choice = None

    for i, opt in enumerate(options):
        with cols[i % 2]:
            if st.button(opt, use_container_width=True, key=f"btn_{current_idx}_{i}"):
                user_choice = opt

    # 정답 체크 로직
    if user_choice:
        if user_choice == correct_answer:
            feedback_area.success("정답입니다! 🎉")
            st.session_state.score += 1
            time.sleep(1)
        else:
            feedback_area.error(f"오답입니다! ❌ 정답은 [{correct_answer}]")
            st.info(f"💡 힌트: {current_quiz['hint']}")
            time.sleep(2.5)

        st.session_state.current_step += 1
        if st.session_state.current_step >= total_q:
            st.session_state.is_finished = True
        st.rerun()