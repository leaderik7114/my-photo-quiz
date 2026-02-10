import streamlit as st
import pandas as pd
import random
import os
import time

# 1. 페이지 설정 및 데이터 로드 (가장 상단)
st.set_page_config(page_title="외관 퀴즈맞추기", layout="centered")

@st.cache_data
def load_data():
    return pd.read_csv("answers.csv")

data = load_data()

# 2. 세션 상태 초기화
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = random.randint(0, len(data) - 1)

# 3. [중요] 메시지 박스를 함수 정의보다 '위'에 만들거나, 
# 함수 내부에서 전역적으로 접근 가능하게 정의해야 합니다.
# 화면 구성을 위해 제목 아래에 배치하겠습니다.

st.title("엔카 사진퀴즈")
st.write(f"현재 점수: {st.session_state.score}점")

# 메시지가 나타날 공간을 미리 확보 (함수 밖, 메인 영역)
feedback_container = st.empty() 

# 4. 제출 로직 함수 (feedback_container가 위에 있으므로 이제 인식 가능)
def submit_logic():
    user_answer = st.session_state.input_field.strip()
    current_quiz = data.iloc[st.session_state.current_idx]
    
    if user_answer == str(current_quiz['answer']).strip():
        feedback_container.success("정답입니다! 🎉")
        st.session_state.score += 1
        st.session_state.current_idx = random.randint(0, len(data) - 1)
        st.session_state.input_field = ""
        time.sleep(1)
        feedback_container.empty()
        st.rerun()
    else:
        feedback_container.error(f"틀렸습니다! 힌트: {current_quiz['hint']}")
        st.session_state.input_field = ""

# 5. 문제 이미지 표시
current_quiz = data.iloc[st.session_state.current_idx]
img_path = os.path.join("images", current_quiz['filename'])
if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)

# 6. 입력창 (on_change에 함수 연결)
st.text_input("정답을 입력하세요", key="input_field", on_change=submit_logic)
st.button("제출하기", on_click=submit_logic)