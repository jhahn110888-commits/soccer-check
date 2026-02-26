import streamlit as st
from audiorecorder import audiorecorder # 이건 무시하셔도 됩니다
import pandas as pd
from datetime import datetime

# 앱 제목 및 설정
st.set_page_config(page_title="축구부 참석 신청", layout="centered")
st.title("⚽ 축구부 주간 매치 신청")

# --- 설정값 (여기만 수정하면 됩니다) ---
MAX_CAPACITY = 20  # 선착순 인원 제한
MATCH_DATE = "2026년 3월 7일 (토)" # 이번 주 경기 날짜
# ----------------------------------

# 데이터 저장 (간편하게 시뮬레이션 - 실제 배포 시 구글 시트 연동 코드로 교체 가능)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['이름', '신청시간'])

db = st.session_state.db
current_count = len(db)

# 화면 구성
st.info(f"📅 경기 일정: **{MATCH_DATE}**")
st.metric("현재 신청 인원", f"{current_count} / {MAX_CAPACITY}명")

if current_count >= MAX_CAPACITY:
    st.error("❌ 선착순 마감되었습니다! 다음 기회에 신청해주세요.")
else:
    with st.form("signup_form", clear_on_submit=True):
        name = st.text_input("이름을 입력해주세요 (예: 홍길동)")
        submit = st.form_submit_id("참석 신청하기")
        
        if submit:
            if name.strip() == "":
                st.warning("이름을 입력해야 합니다.")
            else:
                new_data = pd.DataFrame({'이름': [name], '신청시간': [datetime.now().strftime("%H:%M:%S")]})
                st.session_state.db = pd.concat([db, new_data], ignore_index=True)
                st.success(f"✅ {name}님, 신청이 완료되었습니다!")
                st.rerun()

# 실시간 명단 노출
st.divider()
st.subheader("📋 현재 신청자 명단")
if not db.empty:
    # 순번 계산해서 보여주기
    display_db = db.copy()
    display_db.index = display_db.index + 1
    st.table(display_db)
else:
    st.write("아직 신청자가 없습니다. 1등으로 신청해보세요!")
