import streamlit as st
import pandas as pd
import requests
import datetime
import json

# --- 설정 및 디자인 ---
st.set_page_config(page_title="D'fit 통합 관리", layout="centered", page_icon="⚽")

# 관리자 비밀번호 설정
ADMIN_PASSWORD = "dfit1234" 

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    .stTable { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 사이드바: 관리자 로그인 ---
with st.sidebar:
    st.header("🔐 관리자 전용")
    user_pw = st.text_input("관리자 비밀번호", type="password")
    is_admin = (user_pw == ADMIN_PASSWORD)
    
    if is_admin:
        st.success("인증되었습니다. (수정 가능)")
    elif user_pw:
        st.error("비밀번호가 틀렸습니다.")
    else:
        st.info("관리자 전용 기능을 위해 로그인하세요.")

# --- API 설정 ---
API_URL = "https://script.google.com/macros/s/AKfycbzYMf0rfazFlzLrGuzq6o4QH37Dgpp3p_7M91yNykTjuEN9C7sbYwWIrKKWj6P9LB4A/exec"

st.title("⚽ D'fit 운영 시스템")

MATCH_CONFIG = {
    "2026-02-27 (금) 달성 스포츠 파크": 21,    
    "2026-03-04 (수) 교내 풋살": 14,    
    "2026-03-07 (토) 달성 스포츠 파크": 21,
    "2026-03-11 (수) 교내 풋살": 14,
    "2026-03-12 (목) 달성 스포츠 파크": 40,
    "2026-03-18 (수) 교내 풋살": 14,
    "2026-03-19 (목) 달성 스포츠 파크": 20,
    "2026-03-25 (수) 교내 풋살": 22,
    "2026-03-26 (목) 달성 스포츠 파크": 20
}

selected_match = st.selectbox("📅 경기 일정을 선택하세요", list(MATCH_CONFIG.keys()))
MAX_CAPACITY = MATCH_CONFIG[selected_match]

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

match_all_df = attend_df[attend_df['일정'] == selected_match].reset_index(drop=True)
confirmed_df = match_all_df.head(MAX_CAPACITY)
waiting_df = match_all_df.tail(max(0, len(match_all_df) - MAX_CAPACITY))

tab1, tab2 = st.tabs(["📝 신청 및 명단 확인", "🏃 쿼터별 라인업"])

# [탭 1: 신청 및 명단]
with tab1:
    c1, c2 = st.columns(2)
    c1.metric("확정 인원", f"{len(confirmed_df)} / {MAX_CAPACITY} 명")
    c2.metric("대기 인원", f"{len(waiting_df)} 명")
    
    st.divider()
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        st.subheader("🙋 참석 신청")
        with st.form("add_form", clear_on_submit=True):
            name = st.text_input("이름", placeholder="이름을 입력하세요")
            if st.form_submit_button("참석 확정"):
                if name.strip() == "": st.warning("이름을 입력해주세요.")
                elif name in match_all_df['이름'].values: st.info("이미 등록된 이름입니다.")
                else:
                    now = datetime.datetime.now().strftime("%H:%M")
                    requests.post(API_URL, json={"action": "add", "date": selected_match, "name": name, "time": now})
                    st.cache_data.clear()
                    st.success(f"{name}님 신청 완료!")
                    st.rerun()

    with sub_col2:
        st.subheader("🚫 신청 취소")
        if is_admin:
            with st.form("del_form", clear_on_submit=True):
                del_name = st.text_input("취소할 이름")
                if st.form_submit_button("신청 취소"):
                    if del_name in match_all_df['이름'].values:
                        requests.post(API_URL, json={"action": "delete", "date": selected_match, "name": del_name})
                        st.cache_data.clear()
                        st.success(f"{del_name}님 취소 완료.")
                        st.rerun()
                    else: st.error("명단에 없습니다.")
        else:
            st.warning("관리자만 취소 가능합니다.")

    st.divider()
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.subheader("✅ 확정 명단")
        if not confirmed_df.empty:
            df_c = confirmed_df[['이름']].copy().reset_index(drop=True)
            df_c.index += 1
            st.table(df_c)
        else: st.write("확정 인원이 없습니다.")
    with m_col2:
        st.subheader("⏳ 예비 명단")
        if not waiting_df.empty:
            df_w = waiting_df[['이름']].copy().reset_index(drop=True)
            df_w.index += 1
            st.table(df_w)
        else: st.write("대기자가 없습니다.")

    st.divider()
    st.subheader("🧺 오늘 조끼 빨 사람?")
    if is_admin:
        if not confirmed_df.empty:
            if 'laundry_hero' not in st.session_state: st.session_state.laundry_hero = None
            col_l1, col_l2 = st.columns([1, 2])
            with col_l1:
                if st.button("🎰 랜덤 추첨하기"):
                    import random
                    st.session_state.laundry_hero = random.choice(confirmed_df['이름'].tolist())
                    st.balloons()
            with col_l2:
                if st.session_state.laundry_hero: st.markdown(f"### 🎉 당첨자: **{st.session_state.laundry_hero}** 님!")
        else: st.write("확정 인원이 없습니다.")
    else:
        st.info("추첨 권한은 관리자에게 있습니다.")

# [탭 2: 4-4-2 라인업]
with tab2:
    st.header("📝 4-4-2 라인업")
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)
    
    saved_positions = {}
    for row in lineup_raw:
        if len(row) >= 3 and row[0] == selected_match and row[1] == q_choice:
            try: saved_positions = json.loads(row[2])
            except: saved_positions = {}
            break

    confirmed_players = confirmed_df['이름'].tolist()
    pos_keys = ['fw1', 'fw2', 'mf1', 'mf2', 'mf3', 'mf4', 'df1', 'df2', 'df3', 'df4', 'gk']
    
    def get_currently_selected(exclude_key):
        return [st.session_state.get(f"{selected_match}_{q_choice}_{k}", "미배정") for k in pos_keys if k != exclude_key and st.session_state.get(f"{selected_match}_{q_choice}_{k}", "미배정") != "미배정"]

    def position_box(label, key):
        taken = get_currently_selected(key)
        available = ["미배정"] + [p for p in confirmed_players if p not in taken]
        default_val = saved_positions.get(key, "미배정")
        if default_val in confirmed_players and default_val not in available: available.append(default_val)
        idx = available.index(default_val) if default_val in available else 0
        return st.selectbox(label, available, index=idx, key=f"{selected_match}_{q_choice}_{key}")

    st.divider()
    pos_data = {}
    
    st.caption("공격수 (FW)")
    c1, c2 = st.columns(2)
    with c1: pos_data['fw1'] = position_box("ST(L)", 'fw1')
    with c2: pos_data['fw2'] = position_box("ST(R)", 'fw2')

    st.caption("미드필더 (MF)")
    c3, c4, c5, c6 = st.columns(4)
    with c3: pos_data['mf1'] = position_box("LM", 'mf1')
    with c4: pos_data['mf2'] = position_box("CM(L)", 'mf2')
    with c5: pos_data['mf3'] = position_box("CM(R)", 'mf3')
    with c6: pos_data['mf4'] = position_box("RM", 'mf4')

    st.caption("수비수 (DF)")
    c7, c8, c9, c10 = st.columns(4)
    with c7: pos_data['df1'] = position_box("LB", 'df1')
    with c8: pos_data['df2'] = position_box("CB(L)", 'df2')
    with c9: pos_data['df3'] = position_box("CB(R)", 'df3')
    with c10: pos_data['df4'] = position_box("RB", 'df4')

    st.caption("골키퍼 (GK)")
    pos_data['gk'] = position_box("GK", 'gk')

    st.divider()
    if is_admin:
        if st.button("💾 라인업 저장하기"):
            requests.post(API_URL, json={"action": "save_lineup", "date": selected_match, "quarter": q_choice, "positions": pos_data})
            st.cache_data.clear()
            st.success("저장되었습니다!")
            st.rerun()
    else:
        st.warning("라인업 수정 권한이 없습니다.")
