import streamlit as st
import pandas as pd
import requests
import datetime

# --- 설정 및 디자인 (생략된 상단 코드는 이전과 동일) ---
st.set_page_config(page_title="FC DGIST 전략판", layout="centered", page_icon="⚽")
API_URL = "https://script.google.com/macros/s/AKfycbzyMz75oWHac-WiRPhuJFmFgQqRuKiqERx3PJ7JBPh5mZKKPIuI566lM8rBEjAXvJyOHw/exec"

# 데이터 불러오기 함수 (캐싱 포함)
@st.cache_data(ttl=5)
def get_data(url):
    try:
        res = requests.get(url)
        data = res.json()
        return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame(columns=['일정', '이름', '시간'])
    except:
        return pd.DataFrame(columns=['일정', '이름', '시간'])

df = get_data(API_URL)
# (중략: 일정 선택 및 신청/취소 로직은 기존 유지)

# --- 탭 구성 ---
tab1, tab2, tab3 = st.tabs(["✅ 신청/취소", "📋 전체 명단", "🏃 쿼터별 라인업"])

with tab1:
    # (기존 신청/취소 폼 코드 위치)
    st.write("신청 및 취소는 여기서 진행하세요.")

with tab2:
    st.subheader("📊 현재 참석 확정자")
    current_match_df = df[df['일정'] == st.session_state.get('selected_match', list(df['일정'].unique())[0] if not df.empty else "")]
    st.table(current_match_df[['이름']].reset_index(drop=True).rename(index=lambda x: x+1))

with tab3:
    st.header("📝 쿼터별 라인업 전략판")
    
    # 신청자 명단을 리스트로 추출 (선택 상자에 넣기 위함)
    player_list = ["미배정"] + current_match_df['이름'].tolist()
    
    # 쿼터 선택
    q_col = st.columns(4)
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)
    
    st.divider()
    st.subheader(f"🏟️ {q_choice} 포메이션 설정")

    # 포메이션 배치 (예: 4-4-2 기준)
    # 공격수
    st.write("**[FW]**")
    f1, f2 = st.columns(2)
    fw1 = f1.selectbox("ST (좌)", player_list, key=f"{q_choice}_fw1")
    fw2 = f2.selectbox("ST (우)", player_list, key=f"{q_choice}_fw2")

    # 미드필더
    st.write("**[MF]**")
    m1, m2, m3, m4 = st.columns(4)
    mf1 = m1.selectbox("LM", player_list, key=f"{q_choice}_mf1")
    mf2 = m2.selectbox("CM (좌)", player_list, key=f"{q_choice}_mf2")
    mf3 = m3.selectbox("CM (우)", player_list, key=f"{q_choice}_mf3")
    mf4 = m4.selectbox("RM", player_list, key=f"{q_choice}_mf4")

    # 수비수
    st.write("**[DF]**")
    d1, d2, d3, d4 = st.columns(4)
    df1 = d1.selectbox("LB", player_list, key=f"{q_choice}_df1")
    df2 = d2.selectbox("CB (좌)", player_list, key=f"{q_choice}_df2")
    df3 = d3.selectbox("CB (우)", player_list, key=f"{q_choice}_df3")
    df4 = d4.selectbox("RB", player_list, key=f"{q_choice}_df4")

    # 골키퍼
    st.write("**[GK]**")
    gk = st.selectbox("GK", player_list, key=f"{q_choice}_gk")

    # 저장 버튼 (현재는 화면 확인용이며, 필요 시 구글 시트에 별도 저장 가능)
    if st.button(f"{q_choice} 라인업 확정 (캡처용)"):
        st.success(f"{q_choice} 라인업이 화면에 고정되었습니다. 스크린샷으로 공유하세요!")
