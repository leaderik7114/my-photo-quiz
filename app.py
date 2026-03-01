import streamlit as st
import pandas as pd
import random
import os
import time
import difflib

# 1. 페이지 설정 및 커스텀 CSS
st.set_page_config(page_title="엔카 사진퀴즈 (지능형 오답)", layout="centered", page_icon="🚗")

st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 800; text-align: center; margin-bottom: 0.5rem; color: #E01010; }
    .sub-title { font-size: 1.1rem; text-align: center; color: #555; margin-bottom: 2rem; }
    .block-container { max-width: 700px; padding-top: 2rem; }
    .stButton > button { 
        height: 3.8rem; 
        font-size: 1.05rem !important; 
        font-weight: 600;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .made-by-center { text-align: center; font-size: 0.8rem; color: #bbbbbb; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 및 지능형 오답 생성 함수
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
    """실제 유사 데이터와 가짜 오답을 섞어 최적의 4지선다를 구성합니다."""
    current_answer = str(current_answer).strip()
    # 자기 자신 제외한 유니크 목록
    others = list(set([str(ans).strip() for ans in all_answers if str(ans).strip() != current_answer]))
    
    # [Step 1] 실제 데이터에서 유사도 점수 계산
    scored_candidates = []
    for candidate in others:
        score = 0
        if current_answer in candidate or candidate in current_answer:
            score += 20
        common_chars = set(current_answer) & set(candidate)
        score += len(common_chars) * 2
        ratio = difflib.SequenceMatcher(None, current_answer, candidate).ratio()
        score += ratio * 10
        scored_candidates.append((candidate, score))
    
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # 점수가 높은 실제 데이터 최대 3개 확보
    top_pool = [c[0] for c in scored_candidates if c[1] > 8][:3]

    # [Step 2] 데이터가 부족하거나 난이도를 높이기 위해 가짜 오답 생성
    if len(top_pool) < 3:
        prefixes = ["더 뉴 ", "올 뉴 ", "뉴 ", "그랜드 "]
        suffixes = [" 2세대", " 3세대", " 4세대", " PE", " 하이브리드", " 마스터", " 프레스티지", " 노블레스"]
        
        # 정답에서 핵심 단어 추출 (앞 2글자 혹은 공백 기준 첫 단어)
        base_word = current_answer.split(' ')[0]
        
        generated = set()
        attempts = 0
        while len(top_pool) + len(generated) < 3 and attempts < 20:
            attempts += 1
            mode = random.choice(["pre", "suf", "mix"])
            
            if mode == "pre":
                # 수식어 + 본래이름 (중복수식어 제거)
                clean_name = current_answer.replace("더 뉴 ", "").replace("올 뉴 ", "")
                fake = random.choice(prefixes) + clean_name
            elif mode == "suf":
                fake = base_word + random.choice(suffixes)
            else:
                # 랜덤 조합
                fake = random.choice(prefixes) + base_word + random.choice(suffixes)
            
            if fake != current_answer and fake not in top_pool:
                generated.add(fake)
        
        top_pool += list(generated)

    # 최종 4개 (만약 데이터가 아예 없으면 기본 랜덤이라도 추가)
    while len(top_pool) < 3:
        r_opt = random.choice(others)
        if r_opt not in top_pool: top_pool.append(r_opt)

    final_options = top_pool[:3] + [current_answer]
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
    
    st.markdown('<p class="main-title">🚗 엔카 사진 퀴즈</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">실제 데이터와 가짜 오답이 섞여있습니다. 주의하세요!</p>', unsafe_allow_html=True)
    
    st.write("---")
    quiz_count = st.select_slider("풀어볼 문제 수", options=[5, 10, 20, "전체"], value=10)
    
    if st.button("🚀 게임 시작하기", use_container_width=True, type="primary"):
        all_indices = list(range(len(data)))
        random.shuffle(all_indices)
        limit = len(all_indices) if quiz_count == "전체" else min(int(quiz_count), len(all_indices))
        
        st.session_state.quiz_indices = all_indices[:limit]
        st.session_state.current_step = 0
        st.session_state.score = 0
        st.session_state.game_started = True
        st.session_state.is_finished = False
        # 이전 캐시 삭제
        for k in list(st.session_state.keys()):
            if k.startswith("opts_"): del st.session_state[k]
        st.rerun()

    st.markdown('<div class="made-by-center">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# --- [화면 2] 결과 페이지 ---
elif st.session_state.is_finished:
    st.balloons()
    st.markdown(f"<h2 style='text-align:center;'>🏁 테스트 결과</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='background-color:#f0f2f6; padding:20px; border-radius:15px; text-align:center;'><h3>최종 점수: <b>{st.session_state.score}</b> / {len(st.session_state.quiz_indices)}</h3></div>", unsafe_allow_html=True)
    
    if st.button("처음으로 돌아가기", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()

# --- [화면 3] 게임 진행 페이지 ---
else:
    total_q = len(st.session_state.quiz_indices)
    current_idx = st.session_state.quiz_indices[st.session_state.current_step]
    current_quiz = data.iloc[current_idx]
    correct_answer = str(current_quiz['answer']).strip()

    # 상단 레이아웃
    col_l, col_r = st.columns([5, 1])
    with col_l:
        st.markdown(f"#### 📝 문제 {st.session_state.current_step + 1} / {total_q}")
    with col_r:
        if st.button("🏠"):
            st.session_state.game_started = False
            st.rerun()
            
    st.progress((st.session_state.current_step + 1) / total_q)

    # 사진 출력
    base_file = current_quiz['filename']
    name, ext = os.path.splitext(base_file)
    front_path = os.path.join("images", base_file)
    back_path = os.path.join("images", f"{name}후{ext}")

    img_col1, img_col2 = st.columns(2)
    with img_col1:
        if os.path.exists(front_path):
            st.image(front_path, caption="앞면 (Front)", use_container_width=True)
    with img_col2:
        if os.path.exists(back_path):
            st.image(back_path, caption="뒷면 (Rear)", use_container_width=True)

    st.write("---")

    # 보기 로직 (세션 저장)
    option_key = f"opts_{current_idx}"
    if option_key not in st.session_state:
        st.session_state[option_key] = get_intelligent_options(correct_answer, data['answer'])
    
    options = st.session_state[option_key]

    # 객관식 버튼 UI
    st.markdown("**이 차량의 정확한 명칭을 고르세요:**")
    feedback_placeholder = st.empty()
    
    # 2x2 배치
    btn_cols = st.columns(2)
    user_choice = None

    for i, opt in enumerate(options):
        with btn_cols[i % 2]:
            if st.button(opt, use_container_width=True, key=f"btn_{current_idx}_{i}"):
                user_choice = opt

    # 결과 판정
    if user_choice:
        if user_choice == correct_answer:
            feedback_placeholder.success("정답입니다! 탁월한 눈썰미시네요! 🎉")
            st.session_state.score += 1
            time.sleep(1.2)
        else:
            feedback_placeholder.error(f"오답입니다! ❌ 정답은 [{correct_answer}]")
            st.info(f"💡 힌트: {current_quiz['hint']}")
            time.sleep(3.0)

        st.session_state.current_step += 1
        if st.session_state.current_step >= total_q:
            st.session_state.is_finished = True
        st.rerun()