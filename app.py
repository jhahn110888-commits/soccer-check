import streamlit as st
import pandas as pd
import requests

# --- 설정 (아까 복사한 웹 앱 URL을 여기에 넣으세요) ---
API_URL = "https://script.google.com/macros/s/AKfycbzyMz75oWHac-WiRPhuJFmFgQqRuKiqERx3PJ7JBPh5mZKKPIuI566lM8rBEjAXvJyOHw/exec"
# -----------------------------------------------

st.set_page_config(page_title="D'fit 일정 관리", layout="centered")
st.title("⚽ D'fit 일정 및 참석 관리")

# 1. 일정별 인원 제한 설정 (딕셔너리 형태)
# "일정 이름": 인원제한 숫자 형태로 적어주시면 됩니다.
MATCH_CONFIG = {
    "2026-03-07 (토) 대운동장": 22,
    "2026-03-07 (토) 개강 총회": 100,
    "2026-03-21 (토) 특별 매치": 30
}

# 일정 선택
selected_match = st.selectbox("📅 일정을 선택하세요", list(MATCH_CONFIG.keys()))
MAX_CAPACITY = MATCH_CONFIG[selected_match]

# 데이터 불러오기 함수
def get_data():
    try:
        res = requests.get(API_URL)
        data = res.json()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        else:
            return pd.DataFrame(columns=['일정', '이름', '시간'])
    except:
        return pd.DataFrame(columns=['일정', '이름', '시간'])

df = get_data()
# 선택된 일정의 명단만 필터링
current_match_df = df[df['일정'] == selected_match].reset_index(drop=True)
current_count = len(current_match_df)

# 상단 현황판
st.info(f"📍 {selected_match} (정원: {MAX_CAPACITY}명)")
st.metric("현재 신청 인원", f"{current_count} / {MAX_CAPACITY}명")

# 신청 및 취소 섹션
col1, col2 = st.columns(2)

with col1:
    st.subheader("🙋 신청")
    if current_count >= MAX_CAPACITY:
        st.error("❌ 정원이 마감되었습니다.")
    else:
        with st.form("add_form", clear_on_submit=True):
            name = st.text_input("이름")
            if st.form_submit_button("참석 확정") and name:
                if name in current_match_df['이름'].values:
                    st.warning("이미 신청된 이름입니다.")
                else:
                    # '시간'은 저장만 하고 나중에 표에서는 안 보여줄 예정입니다.
                    import datetime
                    now_time = datetime.datetime.now().strftime("%H:%M")
                    requests.post(API_URL, json={"action": "add", "date": selected_match, "name": name, "time": now_time})
                    st.success(f"{name}님 완료!")
                    st.rerun()

with col2:
    st.subheader("🚫 취소")
    with st.form("del_form", clear_on_submit=True):
        del_name = st.text_input("취소할 이름")
        if st.form_submit_button("신청 취소") and del_name:
            if del_name in current_match_df['이름'].values:
                requests.post(API_URL, json={"action": "delete", "date": selected_match, "name": del_name})
                st.success("취소되었습니다.")
                st.rerun()
            else:
                st.error("명단에 없습니다.")

# 📋 실시간 명단 (순번 표시)
st.divider()
st.subheader("📋 실시간 선착순 명단")

if not current_match_df.empty:
    # 1. '시간' 열을 아예 빼버리고 이름만 남깁니다.
    display_df = current_match_df[['이름']].copy()
    # 2. 인덱스를 1부터 시작하게 만들어서 '순번'으로 활용합니다.
    display_df.index = display_df.index + 1
    display_df.index.name = "순번"
    # 3. 표 출력
    st.table(display_df)
else:
    st.write("아직 신청자가 없습니다.")
