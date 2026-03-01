import streamlit as st
import pandas as pd
import random
import os
import time
import difflib

# 1. 페이지 설정 및 커스텀 CSS (상단 여백 및 하단 스타일 보강)
st.set_page_config(page_title="엔카 사진퀴즈", layout="centered", page_icon="🚗")

st.markdown("""
    <style>
    /* 상단 잘림 방지를 위한 안전 여백 */
    .block-container { 
        max-width: 700px; 
        padding-top: 6rem !important; 
        padding-bottom: 5rem !important;
    }
    
    /* 제목 및 부제목 스타일 */
    .main-title { 
        font-size: 2.5rem; 
        font-weight: 800; 
        text-align: center; 
        margin-bottom: 0.5rem; 
        color: #E01010; 
    }
    
    .sub-title { 
        font-size: 1.1rem; 
        text-align: center; 
        color: #555; 
        margin-bottom: 2rem; 
    }

    /* 버튼 공통 스타일 */
    .stButton > button { 
        height: 3.8rem; 
        font-size: 1.05rem !important; 
        font-weight: 600;
        border-radius: 12px;
    }

    /* 제작자 정보 스타일 (하단 고정 느낌) */
    .made-by-footer { 
        text-align: center; 
        font-size: 0.85rem; 
        color: #aaaaaa; 
        margin-top: 60px; 
        padding-top: 20px;
        border-top: 1px solid #eeeeee;
        font-family: sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 및 로직 함수
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("answers.csv")
        if 'filename' in df.columns:
            df = df[~df['filename'].str.contains('후\\.', na=False)]
        if 'hint' not in df.columns:
            df['hint'] = "힌트가 제공되지 않는 문제입니다."
        return df.fillna("")
    except FileNotFoundError:
        st.error("데이터 파일(answers.csv)을 찾을 수 없습니다.")
        return pd.DataFrame(columns=['filename', 'answer', 'hint'])

def get_intelligent_options(current_answer, all_answers):
    current_answer = str(current_answer).strip()
    others = list(set([str(ans).strip() for ans in all_answers if str(ans).strip() != current_answer]))
    
    scored_candidates = []
    for candidate in others:
        score = 0
        if current_answer in candidate or candidate in current_answer: score += 20
        common_chars = set(current_answer) & set(candidate)
        score += len(common_chars) * 2
        ratio = difflib.SequenceMatcher(None, current_answer, candidate).ratio()
        score += ratio * 10
        scored_candidates.append((candidate, score))
    
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    top_pool = [c[0] for c in scored_candidates if c[1] > 8][:3]

    if len(top_pool) < 3:
        prefixes = ["더 뉴 ", "올 뉴 ", "뉴 ", "그랜드 "]
        suffixes = [" 2세대", " 3세대", " 4세대", " PE", " 하이브리드", " 마스터"]
        base_word = current_answer.split(' ')[0]
        generated = set()
        while len(top_pool) + len(generated) < 3:
            mode = random.choice(["pre", "suf", "mix"])
            if mode == "pre": fake = random.choice(prefixes) + current_answer.replace("더 뉴 ", "").replace("올 뉴 ", "")
            elif mode == "suf": fake = base_word + random.choice(suffixes)
            else: fake = random.choice(prefixes) + base_word + random.choice(suffixes)
            if fake != current_answer and fake not in top_pool: generated.add(fake)
        top_pool += list(generated)

    final_options = top_pool[:3] + [current_answer]
    random.shuffle(final_options)
    return final_options

data = load_data()

# 3. 세션 상태 관리
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'is_finished' not in st.session_state: st.session_state.is_finished = False

# --- [CASE 1] 시작 화면 ---
if not st.session_state.game_started:
    
    if os.path.exists("images/logo.png"):
        st.image("images/logo.png", use_container_width=True)

    st.markdown('<p class="main-title">🚗 엔카 사진 퀴즈</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">앞/뒤 사진을 보고 정확한 등급을 맞혀보세요!</p>', unsafe_allow_html=True)
    
    
    st.write("---")
    quiz_count = st.select_slider("풀어볼 문제 수 선택", options=[10, 20, 30, 50, "전체"], value=10)
    
    if st.button("🚀 게임 시작하기", use_container_width=True, type="primary"):
        all_indices = list(range(len(data)))
        random.shuffle(all_indices)
        limit = len(all_indices) if quiz_count == "전체" else min(int(quiz_count), len(all_indices))
        st.session_state.quiz_indices = all_indices[:limit]
        st.session_state.current_step = 0
        st.session_state.score = 0
        st.session_state.game_started = True
        st.session_state.is_finished = False
        for k in list(st.session_state.keys()):
            if k.startswith("opts_"): del st.session_state[k]
        st.rerun()

    st.markdown('<div class="made-by-footer">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# --- [CASE 2] 결과 화면 ---
elif st.session_state.is_finished:
    st.balloons()
    st.markdown("<h2 style='text-align:center;'>🏁 결과 확인</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='background-color:#f0f2f6; padding:30px; border-radius:15px; text-align:center;'><h3>최종 점수: <b>{st.session_state.score}</b> / {len(st.session_state.quiz_indices)}</h3></div>", unsafe_allow_html=True)
    
    if st.button("처음으로 돌아가기", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    
    st.markdown('<div class="made-by-footer">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# --- [CASE 3] 게임 진행 중 ---
else:
    total_q = len(st.session_state.quiz_indices)
    current_idx = st.session_state.quiz_indices[st.session_state.current_step]
    current_quiz = data.iloc[current_idx]
    correct_answer = str(current_quiz['answer']).strip()

    # 상단 정보 레이아웃
    col_status_l, col_status_r = st.columns([5, 1])
    with col_status_l: 
        st.markdown(f"#### 📝 문제 {st.session_state.current_step + 1} / {total_q}")
    with col_status_r: 
        if st.button("🏠"): 
            st.session_state.game_started = False
            st.rerun()
    st.progress((st.session_state.current_step + 1) / total_q)

    # 사진 출력 영역
    base_file = current_quiz['filename']
    name, ext = os.path.splitext(base_file)
    front_path, back_path = os.path.join("images", base_file), os.path.join("images", f"{name}후{ext}")

    img_col1, img_col2 = st.columns(2)
    with img_col1:
        if os.path.exists(front_path): st.image(front_path, caption="앞면", use_container_width=True)
    with img_col2:
        if os.path.exists(back_path): st.image(back_path, caption="뒷면", use_container_width=True)

    st.write("---")

    # 객관식 보기 영역
    option_key = f"opts_{current_idx}"
    if option_key not in st.session_state:
        st.session_state[option_key] = get_intelligent_options(correct_answer, data['answer'])
    
    options = st.session_state[option_key]
    st.markdown("**이 차량의 정확한 등급명은?**")
    
    feedback_area = st.empty()
    btn_cols = st.columns(2)
    user_choice = None

    for i, opt in enumerate(options):
        with btn_cols[i % 2]:
            if st.button(opt, use_container_width=True, key=f"btn_{current_idx}_{i}"):
                user_choice = opt

    # 결과 판정 및 이동
    if user_choice:
        if user_choice == correct_answer:
            feedback_area.success("정답입니다! 🎉")
            st.session_state.score += 1
            time.sleep(1)
        else:
            feedback_area.error(f"오답! 정답은 [{correct_answer}] 입니다.")
            st.info(f"💡 힌트: {current_quiz['hint']}")
            time.sleep(2.5)
            
        st.session_state.current_step += 1
        if st.session_state.current_step >= total_q: st.session_state.is_finished = True
        st.rerun()