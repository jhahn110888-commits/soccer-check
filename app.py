import streamlit as st
import pandas as pd
import requests
import datetime

# --- 설정 및 디자인 테마 ---
st.set_page_config(page_title="D'fit 신청 시스템", layout="centered", page_icon="⚽")

# CSS 주입으로 버튼 디자인 변경
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007BFF;
        color: white;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- API 설정 ---
API_URL = "https://script.google.com/macros/s/AKfycbzyMz75oWHac-WiRPhuJFmFgQqRuKiqERx3PJ7JBPh5mZKKPIuI566lM8rBEjAXvJyOHw/exec"

st.title("⚽ D'fit 일정 및 참석 관리")
st.caption("실시간 선착순 매치 신청 시스템")

MATCH_CONFIG = {
    "2026-03-07 (토) 대운동장": 22,
    "2026-03-14 (토) 풋살장": 12
}

selected_match = st.selectbox("📅 경기 일정을 선택하세요", list(MATCH_CONFIG.keys()))
MAX_CAPACITY = MATCH_CONFIG[selected_match]

# 데이터 로딩 시 스피너 표시 (체감 속도 개선)
@st.cache_data(ttl=10) # 10초 동안은 캐시 사용해 속도 향상
def get_data(url):
    try:
        res = requests.get(url)
        data = res.json()
        return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame(columns=['일정', '이름', '시간'])
    except:
        return pd.DataFrame(columns=['일정', '이름', '시간'])

with st.spinner('데이터를 불러오는 중...'):
    df = get_data(API_URL)

current_match_df = df[df['일정'] == selected_match].reset_index(drop=True)
current_count = len(current_match_df)

# 현황판 디자인 개선
c1, c2 = st.columns(2)
with c1:
    st.metric("현재 신청", f"{current_count} 명")
with c2:
    st.metric("남은 자리", f"{MAX_CAPACITY - current_count} 명")

st.divider()

# 신청/취소 폼을 탭으로 나누어 깔끔하게 정리
tab1, tab2 = st.tabs(["✅ 참석 신청", "❌ 신청 취소"])

with tab1:
    if current_count >= MAX_CAPACITY:
        st.error("🚨 본 경기는 선착순 마감되었습니다.")
    else:
        with st.form("add_form", clear_on_submit=True):
            name = st.text_input("이름 입력", placeholder="성함을 입력해주세요")
            if st.form_submit_button("지금 바로 신청하기"):
                if name.strip() == "":
                    st.warning("이름을 입력해주세요.")
                elif name in current_match_df['이름'].values:
                    st.info("이미 명단에 등록된 이름입니다.")
                else:
                    with st.status("구글 시트에 기록 중..."): # 진행 상태 표시
                        now = datetime.datetime.now().strftime("%H:%M")
                        requests.post(API_URL, json={"action": "add", "date": selected_match, "name": name, "time": now})
                        st.cache_data.clear() # 데이터 갱신을 위해 캐시 삭제
                    st.success(f"축하합니다! {name}님 신청 완료.")
                    st.rerun()

with tab2:
    with st.form("del_form", clear_on_submit=True):
        del_name = st.text_input("취소할 이름 입력")
        if st.form_submit_button("참석 취소하기"):
            if del_name in current_match_df['이름'].values:
                with st.status("명단에서 삭제 중..."):
                    requests.post(API_URL, json={"action": "delete", "date": selected_match, "name": del_name})
                    st.cache_data.clear()
                st.toast(f"{del_name}님 취소가 완료되었습니다.")
                st.rerun()
            else:
                st.error("명단에서 이름을 찾을 수 없습니다.")

# 명단 디자인 개선 (표 대신 리스트 느낌으로)
st.subheader("📋 현재 확정 명단")
if not current_match_df.empty:
    display_df = current_match_df[['이름']].copy()
    display_df.index = display_df.index + 1
    display_df.columns = ['참석자 명단']
    st.dataframe(display_df, use_container_width=True) # 꽉 찬 화면으로 보기
else:
    st.write("아직 신청자가 없습니다.")
