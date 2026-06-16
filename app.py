import streamlit as st
import pandas as pd
import random
import os
import time
import difflib

# 1. 페이지 설정 및 CSS
st.set_page_config(page_title="엔카 사진퀴즈 - 시험 모드", layout="centered", page_icon="🚗")

st.markdown("""
    <style>
    .block-container { max-width: 700px; padding-top: 4rem !important; padding-bottom: 5rem !important; }
    .main-title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #E01010; }
    .sub-title { font-size: 1.1rem; text-align: center; color: #555; margin-bottom: 2rem; }
    .stButton > button { height: 3rem; font-size: 1.05rem !important; font-weight: 600; border-radius: 12px; }
    
    /* 오답 노트 스타일링 */
    .wrong-box {
        padding: 15px;
        background-color: #fff5f5;
        border-left: 5px solid #e01010;
        border-radius: 6px;
        margin-bottom: 15px;
    }
    
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

# 3. 세션 상태 초기화
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'is_finished' not in st.session_state: st.session_state.is_finished = False
if 'user_answers' not in st.session_state: st.session_state.user_answers = {} # {step_index: 유저가 고른 보기}

# --- [CASE 1] 시작 화면 ---
if not st.session_state.game_started:
    if os.path.exists("images/logo.png"): st.image("images/logo.png", use_container_width=True)
    st.markdown('<p class="main-title">🚗 엔카 사진 퀴즈</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">전면 후면의 사진을 보고 정답을 맞춰보세요! (시험 모드)</p>', unsafe_allow_html=True)

    st.write("---")
    quiz_count = st.select_slider("출제할 문제 수", options=[10, 20, 30, 50, "전체"], value=20)
    if st.button("🚀 시험 시작하기", use_container_width=True, type="primary"):
        all_indices = list(range(len(data)))
        random.shuffle(all_indices)
        limit = len(all_indices) if quiz_count == "전체" else min(int(quiz_count), len(all_indices))
        
        st.session_state.quiz_indices = all_indices[:limit]
        st.session_state.current_step = 0
        st.session_state.user_answers = {}  # 답안지 초기화
        st.session_state.game_started = True
        st.session_state.is_finished = False
        
        # 이전 게임 보기 캐시 삭제
        for k in list(st.session_state.keys()):
            if k.startswith("opts_"): del st.session_state[k]
        st.rerun()
    st.markdown('<div class="made-by-footer">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# --- [CASE 2] 최종 결과 화면 ---
elif st.session_state.is_finished:
    st.markdown("<h2 style='text-align:center;'>🏁 테스트 결과 확인</h2>", unsafe_allow_html=True)
    
    # 채점 진행
    total_q = len(st.session_state.quiz_indices)
    score = 0
    wrong_notes = [] # 틀린 문제 기록용 리스트
    
    for step, idx in enumerate(st.session_state.quiz_indices):
        current_quiz = data.iloc[idx]
        correct_ans = str(current_quiz['answer']).strip()
        user_ans = st.session_state.user_answers.get(step, "미선택").strip()
        
        if user_ans == correct_ans:
            score += 1
        else:
            wrong_notes.append({
                "step": step + 1,
                "front": current_quiz['filename'],
                "correct": correct_ans,
                "user": user_ans,
                "hint": current_quiz.get('hint', '힌트가 없습니다.')
            })
            
    # 최종 결과 안내
    st.markdown(f"""
        <div style='background-color:#f0f2f6; padding:30px; border-radius:15px; text-align:center; margin-bottom: 25px;'>
            <h3>최종 점수: <b>{score}</b> / {total_q}</h3>
            <h4>정답률: <b>{int((score/total_q)*100)}%</b></h4>
        </div>
    """, unsafe_allow_html=True)
    
    if score == total_q:
        st.balloons()
        st.success("👑 대단합니다! 모든 문제를 맞추셨습니다!")
    
    # 오답 노트 출력
    if wrong_notes:
        st.subheader("❌ 오답 노트")
        st.write("틀린 문제를 다시 확인해 보세요.")
        
        for note in wrong_notes:
            with st.container():
                st.markdown(f"#### 📝 {note['step']}번 문제")
                
                # 이미지 표시
                name, ext = os.path.splitext(note['front'])
                f_path, b_path = os.path.join("images", note['front']), os.path.join("images", f"{name}후{ext}")
                c1, c2 = st.columns(2)
                with c1:
                    if os.path.exists(f_path): st.image(f_path, caption="앞면", use_container_width=True)
                with c2:
                    if os.path.exists(b_path): st.image(b_path, caption="뒷면", use_container_width=True)
                
                # 정답 / 오답 / 힌트 정보 표시
                st.markdown(f"""
                    <div class="wrong-box">
                        <b>내가 고른 답:</b> <span style="color:#e01010;">{note['user']}</span><br>
                        <b>정답 등급명:</b> <span style="color:#10b981;">{note['correct']}</span><br>
                        <small style="color:#666;">💡 <b>힌트:</b> {note['hint']}</small>
                    </div>
                """, unsafe_allow_html=True)
                st.write("---")

    if st.button("🔄 처음으로 돌아가기", use_container_width=True, type="primary"):
        st.session_state.game_started = False
        st.session_state.is_finished = False
        st.session_state.current_step = 0
        st.session_state.user_answers = {}
        for k in list(st.session_state.keys()):
            if k.startswith("opts_"): del st.session_state[k]
        st.rerun()

    st.markdown('<div class="made-by-footer">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# --- [CASE 3] 시험 진행 화면 ---
else:
    total_q = len(st.session_state.quiz_indices)
    step = st.session_state.current_step
    current_idx = st.session_state.quiz_indices[step]
    current_quiz = data.iloc[current_idx]
    correct_answer = str(current_quiz['answer']).strip()

    # 상단 헤더 및 홈 버튼
    col_l, col_r = st.columns([5, 1])
    with col_l: st.markdown(f"#### 📝 문제 {step + 1} / {total_q}")
    with col_r: 
        if st.button("🏠"): 
            st.session_state.game_started = False
            st.rerun()
    st.progress((step + 1) / total_q)

    # 차량 앞/뒤 이미지 로드
    base_file = current_quiz['filename']
    name, ext = os.path.splitext(base_file)
    front_p, back_p = os.path.join("images", base_file), os.path.join("images", f"{name}후{ext}")
    c1, c2 = st.columns(2)
    with c1: 
        if os.path.exists(front_p): st.image(front_p, caption="앞면", use_container_width=True)
    with c2: 
        if os.path.exists(back_p): st.image(back_p, caption="뒷면", use_container_width=True)

    st.write("---")

    # 보기(옵션) 생성 및 캐싱
    option_key = f"opts_{current_idx}"
    if option_key not in st.session_state:
        st.session_state[option_key] = get_intelligent_options(correct_answer, data['answer'])
    options = st.session_state[option_key]
    
    st.markdown("**이 차량의 정확한 등급명은 무엇일까요?**")
    
    # 사용자가 기존에 이 문제를 풀었었는지 확인하여 이전 기록 유지
    previous_choice = st.session_state.user_answers.get(step, None)
    if previous_choice in options:
        default_index = options.index(previous_choice)
    else:
        default_index = 0 # 기본적으로 첫 번째 항목 선택 (or 아무것도 선택 안되게 하려면 데이터 설계 필요)
        st.session_state.user_answers[step] = options[0] # 초기값 할당

    # 라디오 버튼으로 보기 출력
    user_choice = st.radio(
        "보기를 선택하세요", 
        options, 
        index=default_index, 
        label_visibility="collapsed",
        key=f"radio_{step}_{current_idx}"
    )
    
    # 사용자가 보기를 바꿀 때마다 실시간으로 답안지에 기록
    st.session_state.user_answers[step] = user_choice

    st.write("")
    
    # 하단 네비게이션 버튼 배치 (이전 문제 / 다음 문제 / 최종 제출)
    nav_cols = st.columns([1, 2, 1])
    
    with nav_cols[0]:
        if step > 0:
            if st.button("⬅️ 이전", use_container_width=True):
                st.session_state.current_step -= 1
                st.rerun()
                
    with nav_cols[1]:
        st.markdown(f"<p style='text-align: center; line-height: 3rem; color: #666;'><b>{step + 1} / {total_q} 문항</b></p>", unsafe_allow_html=True)
        
    with nav_cols[2]:
        if step < total_q - 1:
            if st.button("다음 ➡️", use_container_width=True):
                st.session_state.current_step += 1
                st.rerun()
        else:
            if st.button("🏁 제출", use_container_width=True, type="primary"):
                st.session_state.is_finished = True
                st.rerun()