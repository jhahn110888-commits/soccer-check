import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 앱 설정 및 제목
st.set_page_config(page_title="축구부 통합 관리 시스템", layout="centered")
st.title("⚽ 축구부 일정 및 참석 관리")

# --- 구글 시트 연결 (영구 저장용) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 설정값 (여기서 일정을 추가/수정하세요) ---
SCHEDULES = ["2026-03-07 (토) 대운동장", "2026-03-14 (토) 풋살장"]
MAX_CAPACITY = 20

# 1. 일정 선택 (여러 일정 관리)
selected_match = st.selectbox("📅 참여하실 경기를 선택하세요", SCHEDULES)

# 2. 기존 데이터 불러오기
try:
    df = conn.read(ttl="0s") # 실시간 데이터를 위해 캐시 끔
except:
    df = pd.DataFrame(columns=['일정', '이름', '시간'])

# 현재 선택된 일정의 명단만 필터링
current_match_df = df[df['일정'] == selected_match].reset_index(drop=True)
current_count = len(current_match_df)

# 상단 현황판
st.info(f"📍 선택된 일정: **{selected_match}**")
st.metric("현재 신청 인원", f"{current_count} / {MAX_CAPACITY}명")

# 3. 신청 및 취소 로직
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("🙋 신청하기")
    if current_count >= MAX_CAPACITY:
        st.error("정원이 초과되었습니다.")
    else:
        with st.form("signup", clear_on_submit=True):
            name = st.text_input("이름")
            submit = st.form_submit_button("참석 확정")
            if submit and name:
                if name in current_match_df['이름'].values:
                    st.warning("이미 신청하셨습니다.")
                else:
                    new_row = pd.DataFrame([{"일정": selected_match, "이름": name, "시간": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success(f"{name}님 신청 완료!")
                    st.rerun()

with col2:
    st.subheader("🚫 취소하기")
    with st.form("cancel", clear_on_submit=True):
        cancel_name = st.text_input("취소할 이름")
        cancel_submit = st.form_submit_button("신청 취소")
        if cancel_submit and cancel_name:
            if cancel_name in current_match_df['이름'].values:
                # 해당 일정의 해당 이름만 삭제
                updated_df = df[~((df['일정'] == selected_match) & (df['이름'] == cancel_name))]
                conn.update(data=updated_df)
                st.success("취소되었습니다.")
                st.rerun()
            else:
                st.error("명단에 없는 이름입니다.")

# 4. 실시간 명단 (순번 표시)
st.divider()
st.subheader("📋 실시간 참석 명단")
if not current_match_df.empty:
    # 순번 만들기 (1번부터 시작)
    current_match_df.index = current_match_df.index + 1
    current_match_df.index.name = "순번"
    st.table(current_match_df[['이름', '시간']])
else:
    st.write("아직 신청자가 없습니다.")
