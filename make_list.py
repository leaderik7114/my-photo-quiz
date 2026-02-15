import os
import pandas as pd

img_dir = "images"
csv_file = "answers.csv"

# 1. 이미지 파일 목록 가져오기
current_files = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]

# 2. 기존 CSV 로드 또는 생성
if os.path.exists(csv_file):
    df_old = pd.read_csv(csv_file)
    existing_files = df_old['filename'].tolist()
else:
    df_old = pd.DataFrame(columns=['filename', 'answer', 'hint'])
    existing_files = []

# 3. 새로 추가된 파일만 작업
new_files = [f for f in current_files if f not in existing_files]

if new_files:
    # 새 파일들을 위한 데이터 생성
    new_data = []
    for f in new_files:
        # 파일명에서 확장자 제거 (예: "소나타.jpg" -> "소나타")
        auto_answer = os.path.splitext(f)[0]
        
        new_data.append({
            'filename': f,
            'answer': auto_answer, # 파일명을 정답으로 자동 입력!
            'hint': ''             # 힌트는 나중에 필요하면 기입
        })
    
    df_new = pd.DataFrame(new_data)
    
    # 4. 기존 데이터와 합치기 (기존 정답 보존)
    df_final = pd.concat([df_old, df_new], ignore_index=True)
    df_final.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"✅ 새 사진 {len(new_files)}개를 추가하고 정답을 자동으로 채웠습니다!")
else:
    print("✨ 새로 추가된 사진이 없습니다.")