import streamlit as st
import pandas as pd
import requests
import datetime

# --- 설정 및 디자인 ---
st.set_page_config(page_title="FC DGIST 통합 관리", layout="centered", page_icon="⚽")

# CSS로 버튼 및 레이아웃 예쁘게
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    [data-testid="stExpander"] { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- API 설정 (본인의 구글 앱 스크립트 URL을 꼭 넣어주세요) ---
API_URL = "https://script.google.com/macros/s/AKfycbzyMz75oWHac-WiRPhuJFmFgQqRuKiqERx3PJ7JBPh5mZKKPIuI566lM8rBEjAXvJyOHw/exec"

st.title("⚽ FC DGIST 운영 시스템")

# 1. 일정 및 인원 제한 설정
MATCH_CONFIG = {
    "2026-03-07 (토) 대운동장": 22,
    "2026-03-14 (토) 풋살장": 12,
    "2026-03-21 (토) 연습 매치": 20
}

selected_match = st.selectbox("📅 경기 일정을 선택하세요", list(MATCH_CONFIG.keys()))
MAX_CAPACITY = MATCH_CONFIG[selected_match]

# 데이터 로딩 함수
@st.cache_data(ttl=5)
def get_data(url):
    try:
        res = requests.get(url)
        data = res.json()
        return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame(columns=['일정', '이름', '시간'])
    except:
        return pd.DataFrame(columns=['일정', '이름', '시간'])

with st.spinner('최신 명단 불러오는 중...'):
    df = get_data(API_URL)

# 현재 일정에 맞는 명단 필터링
current_match_df = df[df['일정'] == selected_match].reset_index(drop=True)
current_count = len(current_match_df)

# --- 메인 탭 구성 ---
tab1, tab2, tab3 = st.tabs(["✅ 신청/취소", "📋 전체 명단", "🏃 쿼터별 라인업"])

# [탭 1: 신청 및 취소]
with tab1:
    c1, c2 = st.columns(2)
    c1.metric("현재 신청", f"{current_count} 명")
    c2.metric("남은 자리", f"{MAX_CAPACITY - current_count} 명")
    
    st.divider()
    
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        st.subheader("🙋 참석 신청")
        if current_count >= MAX_CAPACITY:
            st.error("정원이 마감되었습니다.")
        else:
            with st.form("add_form", clear_on_submit=True):
                name = st.text_input("이름", placeholder="실명을 입력하세요")
                if st.form_submit_button("참석 확정"):
                    if name.strip() == "":
                        st.warning("이름을 입력해주세요.")
                    elif name in current_match_df['이름'].values:
                        st.info("이미 등록된 이름입니다.")
                    else:
                        now = datetime.datetime.now().strftime("%H:%M")
                        requests.post(API_URL, json={"action": "add", "date": selected_match, "name": name, "time": now})
                        st.cache_data.clear()
                        st.success(f"{name}님 신청 완료!")
                        st.rerun()

    with sub_col2:
        st.subheader("🚫 신청 취소")
        with st.form("del_form", clear_on_submit=True):
            del_name = st.text_input("취소할 이름")
            if st.form_submit_button("신청 취소"):
                if del_name in current_match_df['이름'].values:
                    requests.post(API_URL, json={"action": "delete", "date": selected_match, "name": del_name})
                    st.cache_data.clear()
                    st.success(f"{del_name}님 취소 완료.")
                    st.rerun()
                else:
                    st.error("명단에 없습니다.")

# [탭 2: 전체 명단 확인]
with tab2:
    st.subheader(f"📊 {selected_match} 확정 명단")
    if not current_match_df.empty:
        display_df = current_match_df[['이름']].copy()
        display_df.index = display_df.index + 1
        display_df.columns = ['참석자 성함']
        st.table(display_df)
    else:
        st.write("아직 신청자가 없습니다.")

# [탭 3: 쿼터별 라인업 전략판]
with tab3:
    st.header("📝 쿼터별 전략판")
    player_list = ["미배정"] + current_match_df['이름'].tolist()
    
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)
    st.divider()
    
    # 포지션 배치 UI
    st.write(f"🏟️ **{q_choice} 포메이션 (4-4-2)**")
    
    # FW
    st.caption("공격수 (FW)")
    f1, f2 = st.columns(2)
    fw1 = f1.selectbox("ST (좌)", player_list, key=f"{q_choice}_fw1")
    fw2 = f2.selectbox("ST (우)", player_list, key=f"{q_choice}_fw2")

    # MF
    st.caption("미드필더 (MF)")
    m1, m2, m3, m4 = st.columns(4)
    mf1 = m1.selectbox("LM", player_list, key=f"{q_choice}_mf1")
    mf2 = m2.selectbox("CM(L)", player_list, key=f"{q_choice}_mf2")
    mf3 = m3.selectbox("CM(R)", player_list, key=f"{q_choice}_mf3")
    mf4 = m4.selectbox("RM", player_list, key=f"{q_choice}_mf4")

    # DF
    st.caption("수비수 (DF)")
    d1, d2, d3, d4 = st.columns(4)
    df1 = d1.selectbox("LB", player_list, key=f"{q_choice}_df1")
    df2 = d2.selectbox("CB(L)", player_list, key=f"{q_choice}_df2")
    df3 = d3.selectbox("CB(R)", player_list, key=f"{q_choice}_df3")
