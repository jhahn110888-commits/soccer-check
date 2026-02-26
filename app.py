import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 설정 (아까 복사한 웹 앱 URL을 여기에 넣으세요) ---
API_URL = "https://script.google.com/macros/s/AKfycbzyMz75oWHac-WiRPhuJFmFgQqRuKiqERx3PJ7JBPh5mZKKPIuI566lM8rBEjAXvJyOHw/exec"
# -----------------------------------------------

st.set_page_config(page_title="축구부 관리 시스템", layout="centered")
st.title("⚽ 축구부 일정 및 참석 관리")

SCHEDULES = ["2026-03-07 (토) 대운동장", "2026-03-14 (토) 풋살장"]
selected_match = st.selectbox("📅 경기를 선택하세요", SCHEDULES)

# 데이터 불러오기
def get_data():
    res = requests.get(API_URL)
    data = res.json()
    return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame(columns=['일정', '이름', '시간'])

df = get_data()
current_match_df = df[df['일정'] == selected_match].reset_index(drop=True)

st.metric("현재 신청 인원", f"{len(current_match_df)} / 20명")

col1, col2 = st.columns(2)
with col1:
    with st.form("add"):
        name = st.text_input("이름")
        if st.form_submit_button("참석 신청") and name:
            requests.post(API_URL, json={"action": "add", "date": selected_match, "name": name, "time": datetime.now().strftime("%H:%M")})
            st.rerun()

with col2:
    with st.form("del"):
        del_name = st.text_input("취소할 이름")
        if st.form_submit_button("신청 취소") and del_name:
            requests.post(API_URL, json={"action": "delete", "date": selected_match, "name": del_name})
            st.rerun()

st.divider()
st.subheader("📋 참석 명단")
if not current_match_df.empty:
    current_match_df.index = current_match_df.index + 1
    st.table(current_match_df[['이름', '시간']])
