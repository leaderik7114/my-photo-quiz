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
    .block-container { max-width: 700px; padding-top: 4rem !important; padding-bottom: 5rem !important; }
    .main-title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #E01010; }
    .sub-title { font-size: 1.1rem; text-align: center; color: #555; margin-bottom: 2rem; }
    .stButton > button { height: 3rem; font-size: 1.05rem !important; font-weight: 600; border-radius: 12px; }
    
    /* 힌트 및 오답 박스 스타일링 */
    .hint-spacer { margin-top: 100px; }
    .hint-box {
        padding: 20px;
        background-color: #fdfdfe;
        border: 1px dashed #cccccc;
        border-radius: 10px;
        text-align: center;
        color: #666666;
    }
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
    # 전체 정답 리스트에서 현재 정답을 제외하고 중복 제거
    others = list(set([str(ans).strip() for ans in all_answers if str(ans).strip() != current_answer]))
    
    # 1. 유사도 점수 계산 로직 (기존 로직 유지)
    scored_candidates = []
    for candidate in others:
        score = 0
        if current_answer in candidate or candidate in current_answer: score += 20
        common_chars = set(current_answer) & set(candidate)
        score += len(common_chars) * 2
        ratio = difflib.SequenceMatcher(None, current_answer, candidate).ratio()
        score += ratio * 10
        scored_candidates.append((candidate, score))
        
    # 점수가 높은 순(가장 비슷한 순)으로 정렬
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # 점수 기준(8점 초과)을 만족하는 '진짜 유사한' 후보들만 필터링
    similar_pool = [c[0] for c in scored_candidates if c[1] > 8]
    
    # 오답 후보를 저장할 리스트
    top_pool = []
    
    # 우선 데이터셋에 존재하는 진짜 유사한 이름들로 먼저 채우기 (최대 3개)
    for cand in similar_pool:
        if cand not in top_pool:
            top_pool.append(cand)
        if len(top_pool) == 3:
            break
            
    # 2. [핵심 수정] 만약 실제 데이터셋에 유사한 명칭이 부족해서 3개가 안 채워졌다면?
    # 다른 뚱딴지같은 차종을 가져오는 게 아니라, 현재 정답 명칭에 수식어를 조합해서 무조건 유사 명칭을 만들어냅니다.
    if len(top_pool) < 3:
        prefixes = ["더 뉴 ", "올 뉴 ", "뉴 ", "페이스리프트 "]
        suffixes = [" 2세대", " 3세대", " 4세대", " PE", " 하이브리드", " 시그니처", " 인스퍼레이션"]
        
        # 앞 글자(예: '그랜저', '쏘렌토')를 기준으로 삼음
        base_word = current_answer.split(' ')[0]
        
        # 중복을 피하기 위해 시도 횟수를 넉넉히(최대 100번) 잡고 조합 실행
        for _ in range(100):
            if len(top_pool) == 3:
                break
                
            # 무작위로 앞수식어 또는 뒷수식어 붙이기
            if random.random() > 0.5:
                fake = random.choice(prefixes) + current_answer
            else:
                fake = current_answer + random.choice(suffixes)
                
            # 띄어쓰기 서식을 깔끔하게 정리하고, 기존 보기나 정답과 중복되지 않는지 검증
            fake = " ".join(fake.split()) 
            if fake != current_answer and fake not in top_pool:
                top_pool.append(fake)

    # 3. 만약 위 단계에서도 아주 드물게 베이스 단어 추출 등이 꼬여 3개가 안 채워졌을 때를 위한 마지막 보루
    # 철저하게 '유사도 점수'가 가장 높았던 상위권 후보들 중에서 강제로 매꿉니다.
    if len(top_pool) < 3:
        for cand, score in scored_candidates:
            if cand not in top_pool and cand != current_answer:
                top_pool.append(cand)
            if len(top_pool) == 3:
                break

    # 오답 후보 3개 + 정답 1개 = 총 4개 결합
    final_options = top_pool[:3] + [current_answer]
    
    # 마지막으로 셔플하여 순서 섞기
    random.shuffle(final_options)
    return final_options
data = load_data()

# 3. 세션 상태 초기화
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'is_finished' not in st.session_state: st.session_state.is_finished = False
if 'retry_chance' not in st.session_state: st.session_state.retry_chance = True 
if 'game_mode' not in st.session_state: st.session_state.game_mode = "기본 모드" # 기본 모드 vs 시험 모드
if 'user_answers' not in st.session_state: st.session_state.user_answers = {} 

# --- [CASE 1] 시작 화면 ---
if not st.session_state.game_started:
    if os.path.exists("images/logo.png"): st.image("images/logo.png", use_container_width=True)
    st.markdown('<p class="main-title">🚗 엔카 사진 퀴즈</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">전면 후면의 사진을 보고 정답을 맞춰보세요!</p>', unsafe_allow_html=True)

    st.write("---")
    
    # 🌟 모드 선택 라디오 버튼 추가
    selected_mode = st.radio("🎮 플레이 모드 선택", ["기본 연습 모드 (정답 즉시 확인)", "시험 모드 (20문항 후 결과 확인)"], index=0)
    
    # 모드에 따른 문제 수 설정
    if "시험 모드" in selected_mode:
        st.info("📝 시험 모드는 총 20문제가 출제되며, 진행 중 정/오답이 공개되지 않습니다.")
        quiz_count = 20
    else:
        quiz_count = st.select_slider("문제 수", options=[10, 20, 30, 50, "전체"], value=10)
        
    if st.button("🚀 게임 시작하기", use_container_width=True, type="primary"):
        all_indices = list(range(len(data)))
        random.shuffle(all_indices)
        
        limit = len(all_indices) if quiz_count == "전체" else min(int(quiz_count), len(all_indices))
        
        st.session_state.quiz_indices = all_indices[:limit]
        st.session_state.current_step = 0
        st.session_state.score = 0
        st.session_state.retry_chance = True
        st.session_state.game_mode = "시험 모드" if "시험 모드" in selected_mode else "기본 모드"
        st.session_state.user_answers = {}
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
    
    total_q = len(st.session_state.quiz_indices)
    
    # [시험 모드 결과]
    if st.session_state.game_mode == "시험 모드":
        score = 0
        wrong_notes = []
        for step, idx in enumerate(st.session_state.quiz_indices):
            current_quiz = data.iloc[idx]
            correct_ans = str(current_quiz['answer']).strip()
            user_ans = st.session_state.user_answers.get(step, "미선택").strip()
            
            if user_ans == correct_ans: score += 1
            else:
                wrong_notes.append({
                    "step": step + 1, "front": current_quiz['filename'],
                    "correct": correct_ans, "user": user_ans, "hint": current_quiz.get('hint', '힌트가 없습니다.')
                })
        
        st.markdown(f"""
            <div style='background-color:#f0f2f6; padding:30px; border-radius:15px; text-align:center; margin-bottom:25px;'>
                <h3>[시험 모드] 최종 점수: <b>{score}</b> / {total_q}</h3>
                <h4>정답률: <b>{int((score/total_q)*100)}%</b></h4>
            </div>
        """, unsafe_allow_html=True)
        
        if wrong_notes:
            st.subheader("❌ 오답 노트")
            for note in wrong_notes:
                st.markdown(f"#### 📝 {note['step']}번 문제")
                name, ext = os.path.splitext(note['front'])
                f_path, b_path = os.path.join("images", note['front']), os.path.join("images", f"{name}후{ext}")
                c1, c2 = st.columns(2)
                with c1: 
                    if os.path.exists(f_path): st.image(f_path, use_container_width=True)
                with c2: 
                    if os.path.exists(b_path): st.image(b_path, use_container_width=True)
                st.markdown(f"""
                    <div class="wrong-box">
                        <b>내가 고른 답:</b> <span style="color:#e01010;">{note['user']}</span><br>
                        <b>정답 등급명:</b> <span style="color:#10b981;">{note['correct']}</span><br>
                        <small style="color:#666;">💡 <b>힌트:</b> {note['hint']}</small>
                    </div>
                """, unsafe_allow_html=True)
                st.write("---")
                
    # [기본 모드 결과]
    else:
        st.markdown(f"<div style='background-color:#f0f2f6; padding:30px; border-radius:15px; text-align:center; margin-bottom:25px;'><h3>최종 점수: <b>{st.session_state.score}</b> / {total_q}</h3></div>", unsafe_allow_html=True)
    
    if st.button("처음으로 돌아가기", use_container_width=True, type="primary"):
        st.session_state.game_started = False
        st.session_state.is_finished = False
        st.session_state.current_step = 0
        st.session_state.score = 0
        st.session_state.retry_chance = True
        st.session_state.user_answers = {}
        for k in list(st.session_state.keys()):
            if k.startswith("opts_"): del st.session_state[k]
        st.rerun()

    st.markdown('<div class="made-by-footer">made by 진단광고제작팀 최인규</div>', unsafe_allow_html=True)

# --- [CASE 3] 게임 진행 ---
else:
    total_q = len(st.session_state.quiz_indices)
    step = st.session_state.current_step
    current_idx = st.session_state.quiz_indices[step]
    current_quiz = data.iloc[current_idx]
    correct_answer = str(current_quiz['answer']).strip()

    col_l, col_r = st.columns([5, 1])
    with col_l: st.markdown(f"#### 📝 문제 {step + 1} / {total_q} ({st.session_state.game_mode})")
    with col_r: 
        if st.button("🏠홈으로"): 
            st.session_state.game_started = False
            st.rerun()
    st.progress((step + 1) / total_q)

    # 이미지 로드
    base_file = current_quiz['filename']
    name, ext = os.path.splitext(base_file)
    front_p, back_p = os.path.join("images", base_file), os.path.join("images", f"{name}후{ext}")
    c1, c2 = st.columns(2)
    with c1: 
        if os.path.exists(front_p): st.image(front_p, caption="앞면", use_container_width=True)
    with c2: 
        if os.path.exists(back_p): st.image(back_p, caption="뒷면", use_container_width=True)

    st.write("---")

    # 보기 생성 및 캐싱
    option_key = f"opts_{current_idx}"
    if option_key not in st.session_state:
        st.session_state[option_key] = get_intelligent_options(correct_answer, data['answer'])
    options = st.session_state[option_key]
    
    # ----------------------------------------------------
    #  [분기점 1] 시험 모드 레이아웃 (라디오 버튼 + 네비게이션)
    # ----------------------------------------------------
    if st.session_state.game_mode == "시험 모드":
        st.markdown("**이 차량의 정확한 등급명은 무엇일까요?**")
        previous_choice = st.session_state.user_answers.get(step, options[0])
        default_index = options.index(previous_choice) if previous_choice in options else 0
        
        user_choice = st.radio("보기 선택", options, index=default_index, label_visibility="collapsed", key=f"radio_{step}_{current_idx}")
        st.session_state.user_answers[step] = user_choice # 실시간 저장

        st.write("")
        nav_cols = st.columns([1.2, 1.6, 1.2], gap="small")
    
        with nav_cols[0]:
        # '이전' 대신 '⬅️ 뒤로' 처럼 글자수를 줄여서 폰 깨짐 방지
            if step > 0:
                if st.button("⬅️ 이전", use_container_width=True):
                   st.session_state.current_step -= 1
                   st.rerun()
            else:
                st.write("") # 빈칸 유지
                
        with nav_cols[1]:
            st.markdown(f"<p style='text-align: center; line-height: 3rem; color: #666; font-size: 0.95rem; font-weight: bold;'>{step + 1} / {total_q}</p>", unsafe_allow_html=True)
        
        with nav_cols[2]:
            if step < total_q - 1:
                if st.button("다음 ➡️", use_container_width=True):
                    st.session_state.current_step += 1
                    st.rerun()
            else:
                if st.button("🏁 제출", use_container_width=True, type="primary"):
                    st.session_state.is_finished = True
                    st.rerun()

    # ----------------------------------------------------
    #  [분기점 2] 기본 연습 모드 레이아웃 (기존 사각형 버튼 방식)
    # ----------------------------------------------------
    else:
        feedback_area = st.empty()
        hint_area = st.empty()  # 🌟 틀렸을 때 힌트를 즉시 띄워줄 공간 마련
        
        if not st.session_state.retry_chance:
            feedback_area.error("❌ 틀렸습니다!")
            # 🌟 [수정] '틀렸습니다' 문구 바로 아래에 힌트 박스 배치
            hint_text = current_quiz.get('hint', '힌트가 없습니다.')
            hint_area.markdown(f"""
                <div class="hint-box" style="margin-top: 10px; margin-bottom: 20px;">
                    <small style="color:#999;">💡 HINT</small><br>
                    <b>{hint_text}</b>
                </div>
            """, unsafe_allow_html=True)
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
                hint_area.empty() # 정답일 때는 힌트 공간 비우기
                st.session_state.score += 1
                st.session_state.retry_chance = True
                st.session_state.current_step += 1
                time.sleep(1)
            else:
                if st.session_state.retry_chance:
                    st.session_state.retry_chance = False
                else:
                    feedback_area.error(f"아쉬워요! 정답은 **[{correct_answer}]** 입니다.")
                    hint_area.empty()
                    time.sleep(2.5)
                    st.session_state.retry_chance = True
                    st.session_state.current_step += 1

            if st.session_state.current_step >= total_q: st.session_state.is_finished = True
            st.rerun()