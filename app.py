import streamlit as st
import pandas as pd
import random
import os
import time
import difflib

# 1. 페이지 설정 및 CSS
st.set_page_config(page_title="엔카 사진퀴즈", layout="centered", page_icon="🚗")

st.markdown("""
    <style>
    .block-container { max-width: 700px; padding-top: 6rem !important; padding-bottom: 5rem !important; }
    .main-title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #E01010; }
    .sub-title { font-size: 1.1rem; text-align: center; color: #555; margin-bottom: 2rem; }
    .stButton > button { height: 3.8rem; font-size: 1.05rem !important; font-weight: 600; border-radius: 12px; }
    .made-by-footer { text-align: center; font-size: 0.85rem; color: #aaaaaa; margin-top: 60px; padding-top: 20px; border-top: 1px solid #eeeeee; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 및 로직
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("answers.csv")
        if 'filename' in df.columns:
            df = df[~df['filename'].str.contains('후\\.', na=False)]
        return df.fillna("")
    except FileNotFoundError:
        st.error("answers.csv 파일을 찾을 수 없습니다.")
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
        prefixes, suffixes = ["더 뉴 ", "올 뉴 ", "뉴 "], [" 2세대", " 3세대", " 4세대", " PE", " 하이브리드"]
        base_word = current_answer.split(' ')[0]
        generated = set()
        while len(top_pool) + len(generated) < 3:
            fake = random.choice(prefixes) + base_word if random.random() > 0.5 else base_word + random.choice(suffixes)
            if fake != current_answer: generated.add(fake)
        top_pool += list(generated)
    final_options = top_pool[:3] + [current_answer]
    random.shuffle(final_options)
    return final_options

data = load_data()

# 3. 세션 상태
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'is_finished' not in st.session_state: st.session_state.is_finished = False
if 'retry_chance' not in st.session_state: st.session_state.retry_chance = True 

# --- [CASE 1] 시작 화면 ---
if not st.session_state.game_started:
    if os.path.exists("images/logo.png"): st.image("images/logo.png", use_container_width=True)
    st.markdown('<p class="main-title">🚗 엔카 사진 퀴즈</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">전면 후면의 사진을 보고 정답을 맞춰보세요!</p>', unsafe_allow_html=True)

    st.write("---")
    quiz_count = st.select_slider("문제 수", options=[10, 20, 30, 50, "전체"], value=10)
    if st.button("🚀 게임 시작하기", use_container_width=True, type="primary"):
        all_indices = list(range(len(data)))
        random.shuffle(all_indices)
        limit = len(all_indices) if quiz_count == "전체" else min(int(quiz_count), len(all_indices))
        st.session_state.quiz_indices = all_indices[:limit]
        st.session_state.current_step, st.session_state.score = 0, 0
        st.session_state.game_started, st.session_state.retry_chance = True, True
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

# --- [CASE 3] 게임 진행 ---
else:
    total_q = len(st.session_state.quiz_indices)
    current_idx = st.session_state.quiz_indices[st.session_state.current_step]
    current_quiz = data.iloc[current_idx]
    correct_answer = str(current_quiz['answer']).strip()

    col_l, col_r = st.columns([5, 1])
    with col_l: st.markdown(f"#### 📝 문제 {st.session_state.current_step + 1} / {total_q}")
    with col_r: 
        if st.button("🏠"): 
            st.session_state.game_started = False
            st.rerun()
    st.progress((st.session_state.current_step + 1) / total_q)

    # 이미지
    base_file = current_quiz['filename']
    name, ext = os.path.splitext(base_file)
    front_p, back_p = os.path.join("images", base_file), os.path.join("images", f"{name}후{ext}")
    c1, c2 = st.columns(2)
    with c1: 
        if os.path.exists(front_p): st.image(front_p, caption="앞면", use_container_width=True)
    with c2: 
        if os.path.exists(back_p): st.image(back_p, caption="뒷면", use_container_width=True)

    st.write("---")

    # 보기 생성
    option_key = f"opts_{current_idx}"
    if option_key not in st.session_state:
        st.session_state[option_key] = get_intelligent_options(correct_answer, data['answer'])
    options = st.session_state[option_key]
    
    # UI 피드백 영역
    feedback_area = st.empty()
    
    if not st.session_state.retry_chance:
        # 첫 번째 틀렸을 때 나타나는 힌트 영역
        hint_text = current_quiz.get('hint', '힌트가 없습니다.')
        feedback_area.warning(f"❌ 틀렸습니다!")
        feedback_area.warning(f"**힌트:** {hint_text}")
    else:
        st.markdown("**이 차량의 정확한 등급명은?**")
    
    btn_cols = st.columns(2)
    user_choice = None
    for i, opt in enumerate(options):
        with btn_cols[i % 2]:
            if st.button(opt, use_container_width=True, key=f"btn_{current_idx}_{i}_{st.session_state.retry_chance}"):
                user_choice = opt

    if user_choice:
        if user_choice == correct_answer:
            feedback_area.success("정답입니다! 🎉")
            st.session_state.score += 1
            st.session_state.retry_chance = True
            st.session_state.current_step += 1
            time.sleep(1)
        else:
            if st.session_state.retry_chance:
                # 첫 번째 오답: 힌트 보여주기 위해 상태만 변경
                st.session_state.retry_chance = False
            else:
                # 두 번째 오답: 정답 공개 후 다음 문제로
                feedback_area.error(f"아쉬워요! 정답은 **[{correct_answer}]** 입니다.")
                time.sleep(2.5)
                st.session_state.retry_chance = True
                st.session_state.current_step += 1

        if st.session_state.current_step >= total_q: st.session_state.is_finished = True
        st.rerun()