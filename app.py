import streamlit as st
import pandas as pd
import requests
import datetime
import json

# --- 설정 및 디자인 ---
st.set_page_config(page_title="FC DGIST 통합 관리", layout="centered", page_icon="⚽")

# CSS로 디자인 강화
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    .stTable { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- API 설정 (본인의 구글 앱 스크립트 URL을 입력하세요) ---
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

# 데이터 로딩 함수 (참석 명단 + 라인업)
@st.cache_data(ttl=2)
def get_all_data(url):
    try:
        res = requests.get(url)
        full_data = res.json()
        attend_df = pd.DataFrame(full_data['attend'][1:], columns=full_data['attend'][0]) if len(full_data['attend']) > 1 else pd.DataFrame(columns=['일정', '이름', '시간'])
        lineup_raw = full_data.get('lineup', [])
        return attend_df, lineup_raw
    except:
        return pd.DataFrame(columns=['일정', '이름', '시간']), []

with st.spinner('데이터 동기화 중...'):
    attend_df, lineup_raw = get_all_data(API_URL)

# 현재 일정에 맞는 명단 필터링
current_match_df = attend_df[attend_df['일정'] == selected_match].reset_index(drop=True)
current_count = len(current_match_df)

# --- 메인 탭 구성 (2개로 통합) ---
tab1, tab2 = st.tabs(["📝 신청 및 명단 확인", "🏃 쿼터별 라인업"])

# [탭 1: 신청/취소 + 전체 명단 통합]
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

    # 신청/취소 바로 아래에 명단 배치
    st.divider()
    st.subheader(f"📋 {selected_match} 확정 명단")
    if not current_match_df.empty:
        display_df = current_match_df[['이름']].copy()
        display_df.index = display_df.index + 1
        display_df.columns = ['참석자 명단']
        st.table(display_df)
    else:
        st.write("아직 신청자가 없습니다.")

# [탭 2: 쿼터별 라인업 (날짜/쿼터 연동 저장)]
with tab2:
    st.header("📝 쿼터별 전략판")
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)
    
    # 해당 날짜 & 쿼터의 저장된 라인업 찾기
    saved_positions = {}
    for row in lineup_raw:
        if len(row) >= 3 and row[0] == selected_match and row[1] == q_choice:
            try:
                saved_positions = json.loads(row[2])
            except:
                saved_positions = {}
            break

    player_list = ["미배정"] + current_match_df['이름'].tolist()
    
    st.divider()
    st.subheader(f"🏟️ {selected_match} - {q_choice}")

    pos_data = {}
    # 포지션 선택 UI (저장된 값이 있으면 불러오고, 없으면 미배정)
    def get_index(pos_key):
        val = saved_positions.get(pos_key, "미배정")
        return player_list.index(val) if val in player_list else 0

    st.caption("공격수 (FW)")
    f1, f2 = st.columns(2)
    pos_data['fw1'] = f1.selectbox("ST(L)", player_list, index=get_index('fw1'), key=f"fw1_{selected_match}_{q_choice}")
    pos_data['fw2'] = f2.selectbox("ST(R)", player_list, index=get_index('fw2'), key=f"fw2_{selected_match}_{q_choice}")

    st.caption("미드필더 (MF)")
    m1, m2, m3, m4 = st.columns(4)
    pos_data['mf1'] = m1.selectbox("LM", player_list, index=get_index('mf1'), key=f"mf1_{selected_match}_{q_choice}")
    pos_data['mf2'] = m2.selectbox("CM(L)", player_list, index=get_index('mf2'), key=f"mf2_{selected_match}_{q_choice}")
    pos_data['mf3'] = m3.selectbox("CM(R)", player_list, index=get_index('mf3'), key=f"mf3_{selected_match}_{q_choice}")
    pos_data['mf4'] = m4.selectbox("RM", player_list, index=get_index('mf4'), key=f"mf4_{selected_match}_{q_choice}")

    st.caption("수비수 (DF)")
    d1, d2, d3, d4 = st.columns(4)
    pos_data['df1'] = d1.selectbox("LB", player_list, index=get_index('df1'), key=f"df1_{selected_match}_{q_choice}")
    pos_data['df2'] = d2.selectbox("CB(L)", player_list, index=get_index('df2'), key=f"df2_{selected_match}_{q_choice}")
    pos_data['df3'] = d3.selectbox("CB(R)", player_list, index=get_index('df3'), key=f"df3_{selected_match}_{q_choice}")
    pos_data['df4'] = d4.selectbox("RB", player_list, index=get_index('df4'), key=f"df4_{selected_match}_{q_choice}")

    st.caption("골키퍼 (GK)")
    pos_data['gk'] = st.selectbox("GK", player_list, index=get_index('gk'), key=f"gk_{selected_match}_{q_choice}")

    if st.button("💾 현재 라인업 저장하기"):
        with st.spinner("구글 시트에 저장 중..."):
            requests.post(API_URL, json={
                "action": "save_lineup",
                "date": selected_match,
                "quarter": q_choice,
                "positions": pos_data
            })
            st.cache_data.clear()
            st.success("라인업이 저장되었습니다! 부원들도 이제 이 화면을 볼 수 있습니다.")
            st.rerun()
