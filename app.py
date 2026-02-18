import streamlit as st
import pandas as pd
import random
import os
import time

# 1. 페이지 설정
st.set_page_config(page_title="엔카 사진퀴즈", layout="centered", page_icon="🚗")

# 2. 데이터 로드
@st.cache_data
def load_data():
    if not os.path.exists("answers.csv"):
        return pd.DataFrame(columns=['filename', 'answer', 'hint'])
    df = pd.read_csv("answers.csv")
    return df.fillna("")

data = load_data()
max_questions = len(data)

# 3. 세션 상태 관리
if 'game_started' not in st.session_state:
    st.session_state.game_started = False

# --- [CASE 1] 게임 시작 전 (메인 화면) ---
if not st.session_state.game_started:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if os.path.exists("images/logo.png"):
        st.image("images/logo.png", width=150)
    
    st.title("🚗 엔카 사진퀴즈")
    st.write(f"현재 총 **{max_questions}개**의 문제가 준비되어 있습니다.")
    st.write("---")
    
    # --- 슬라이더 설정 ---
    # 1부터 전체 개수까지, 10단위로 조절 가능하도록 설정
    selected_count = st.slider(
        "출제할 문제 수를 선택하세요",
        min_value=1,
        max_value=max_questions,
        value=min(10, max_questions), # 기본값 10
        step=10 if max_questions >= 10 else 1 # 10개 이상일 때만 10단위 스텝 적용
    )
    
    # 만약 슬라이더 값이 최대치에 근접하면 '전체'라고 표시해줌
    count_display = f"**{selected_count}개**" if selected_count < max_questions else "**전체**"
    st.write(f"선택된 문제 수: {count_display}")

    if st.button("🚀 게임 시작하기", use_container_width=True, type="primary"):
        all_indices = list(range(max_questions))
        random.shuffle(all_indices)
        
        # 슬라이더에서 선택한 만큼 자르기
        st.session_state.quiz_indices = all_indices[:selected_count]
            
        st.session_state.current_step = 0
        st.session_state.score = 0
        st.session_state.wrong_count = 0
        st.session_state.game_started = True 
        st.session_state.is_finished = False
        st.rerun()
    st.stop() # 시작 전에는 아래 코드를 실행하지 않음

# --- [CASE 2] 게임 종료 및 진행 로직 (기존과 동일) ---
elif st.session_state.get('is_finished', False):
    st.balloons()
    st.title("🏁 퀴즈 결과")
    st.metric("최종 점수", f"{st.session_state.score} / {len(st.session_state.quiz_indices)}")
    if st.button("처음으로 돌아가기", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    st.stop()

# --- 게임 진행 중 UI ---
header_col, btn_col = st.columns([7, 3])
with header_col:
    st.subheader("외관사진으로 등급맞추기!")
with btn_col:
    if st.button("🏠 처음으로", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()

total_q = len(st.session_state.quiz_indices)
current_step = st.session_state.current_step
current_quiz = data.iloc[st.session_state.quiz_indices[current_step]]

st.progress((current_step) / total_q)
st.write(f"문제 {current_step + 1} / {total_q} | 점수: {st.session_state.score}")

img_path = os.path.join("images", current_quiz['filename'])
if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)

user_answer = st.chat_input("정답을 입력하세요!")
if user_answer:
    ans_clean = user_answer.replace(" ", "").lower()
    correct_clean = str(current_quiz['answer']).replace(" ", "").lower()

    if ans_clean == correct_clean:
        st.success("정답입니다! 🎉")
        st.session_state.score += 1
        time.sleep(1)
        st.session_state.current_step += 1
    else:
        st.session_state.wrong_count += 1
        if st.session_state.wrong_count >= 5:
            st.error(f"❌ 정답은 [{current_quiz['answer']}]")
            time.sleep(2)
            st.session_state.current_step += 1
            st.session_state.wrong_count = 0
        else:
            st.warning(f"틀렸습니다! (남은 기회: {5 - st.session_state.wrong_count}번)")
    
    if st.session_state.current_step >= total_q:
        st.session_state.is_finished = True
    st.rerun()