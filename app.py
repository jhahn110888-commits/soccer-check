import streamlit as st
import pandas as pd
import requests
import datetime
import json
import 

# --- 1. 기본 설정 ---
st.set_page_config(page_title="D'fit 통합 관리", layout="centered", page_icon="⚽")

try:
    ADMIN_PW = st.secrets["admin_password"]
except:
    ADMIN_PW = "test1234"

with st.sidebar:
    if is_admin:
        st.success("✅ 관리자 모드 활성")
        if st.button("로그아웃"):
            st.query_params.clear()
            st.rerun()
    else:
        st.warning("일반 사용자 모드")

# --- 3. API 및 데이터 로드 ---
API_URL = "https://script.google.com/macros/s/AKfycbyaZjCt2UAxIvk3xaPKgF2LrS7Su23kaco26KG3AwdcZ2hX8bLHYfvG_1zIVP6S5fK6nA/exec"

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

selected_match = st.selectbox("📅 경기 선택", list(MATCH_CONFIG.keys()))
MAX_CAPACITY = MATCH_CONFIG[selected_match]

@st.cache_data(ttl=2)
def get_all_data(url):
    try:
        res = requests.get(url)
        full_data = res.json()
        attend_df = pd.DataFrame(full_data['attend'][1:], columns=full_data['attend'][0])
        lineup_raw = full_data.get('lineup', [])
        return attend_df, lineup_raw
    except:
        return pd.DataFrame(columns=['일정', '이름', '시간']), []

attend_df, lineup_raw = get_all_data(API_URL)
match_all_df = attend_df[attend_df['일정'] == selected_match].reset_index(drop=True)
confirmed_df = match_all_df.head(MAX_CAPACITY)
waiting_df = match_all_df.tail(max(0, len(match_all_df) - MAX_CAPACITY))

# --- 4. 탭 구성 ---
tab1, tab2 = st.tabs(["📝 신청 및 명단", "🏃 라인업"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🙋 신청")
        with st.form("add"):
            name = st.text_input("이름")
            if st.form_submit_button("참석"):
                now = datetime.datetime.now().strftime("%H:%M")
                requests.post(API_URL, json={"action": "add", "date": selected_match, "name": name, "time": now})
                st.cache_data.clear()
                st.rerun()
    with col2:
        st.subheader("🚫 취소")
        if is_admin:
            with st.form("del"):
                d_name = st.text_input("이름")
                if st.form_submit_button("취소"):
                    requests.post(API_URL, json={"action": "delete", "date": selected_match, "name": d_name})
                    st.cache_data.clear()
                    st.rerun()
        else: st.info("관리자 전용")

    st.divider()
    m1, m2 = st.columns(2)
    with m1:
        st.subheader("✅ 확정 명단")
        df_c = confirmed_df[['이름']].reset_index(drop=True)
        df_c.index += 1
        st.table(df_c)
    with m2:
        st.subheader("⏳ 예비 명단")
        df_w = waiting_df[['이름']].reset_index(drop=True)
        df_w.index += 1
        st.table(df_w)

with tab2:
    st.header("📝 라인업")
    
    # 1. 쿼터 선택
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)
    
    # --- [데이터 로드 로직 보강] ---
    saved_positions = {}
    saved_formation = "4-4-2"  # 기본값
    
    # lineup_raw에서 현재 선택된 경기와 '정확한 쿼터'가 일치하는 행을 끝까지 찾습니다.
    for row in lineup_raw:
        # row[0]: 날짜, row[1]: 쿼터, row[2]: 포지션JSON, row[3]: 포메이션
        if len(row) >= 2:
            # 공백이나 대소문자 차이로 안 읽힐 수 있으니 strip() 처리
            if str(row[0]).strip() == selected_match.strip() and str(row[1]).strip() == q_choice.strip():
                try:
                    saved_positions = json.loads(row[2])
                    # 포메이션 정보가 있다면 작은따옴표를 떼고 깨끗하게 가져옵니다.
                    if len(row) >= 4:
                        saved_formation = str(row[3]).replace("'", "").strip()
                except Exception as e:
                    pass
                # 일치하는 쿼터를 찾았으면 루프를 중단합니다.
                break 

    # 2. 관리자/일반 모드에 따른 포메이션 설정
    if is_admin:
        formation = st.text_input(f"{q_choice} 포메이션 설정", value=saved_formation, key=f"form_input_{q_choice}")
    else:
        st.info(f"현재 {q_choice} 포메이션: **{saved_formation}**")
        formation = saved_formation

    # 3. 포메이션 숫자 파싱
    try:
        df_n, mf_n, fw_n = map(int, formation.split('-'))
    except:
        df_n, mf_n, fw_n = 4, 4, 2

    # 중복 제거 로직 함수
    def q_role_box(label, p_id, options):
        c1, c2 = st.columns([2, 1])
        prefix = f"{selected_match}_{q_choice}"
        name_key = f"{prefix}_{p_id}_name"
        
        taken = [v for k, v in st.session_state.items() if prefix in k and "_name" in k and k != name_key and v != "미배정"]
        available = ["미배정"] + [p for p in confirmed_df['이름'].tolist() if p not in taken]
        
        saved_val = saved_positions.get(p_id, "미배정|")
        s_name, s_role = saved_val.split('|') if '|' in saved_val else (saved_val, "")
        
        if name_key not in st.session_state: st.session_state[name_key] = s_name
        
        display_list = available.copy()
        if st.session_state[name_key] not in display_list: display_list.append(st.session_state[name_key])
        
        with c1: sel_n = st.selectbox(f"{label}", display_list, key=name_key)
        with c2: sel_r = st.selectbox(f"{label}", options, key=f"{prefix}_{p_id}_role", index=options.index(s_role) if s_role in options else 0)
        return f"{sel_n}|{sel_r}"

    pos_data = {}
    st.subheader("GK")
    pos_data['gk'] = q_role_box("GK", "gk", ["GK"])
    
    st.subheader("DF")
    for i in range(df_n): pos_data[f'df_{i+1}'] = q_role_box(f"DF {i+1}", f"df_{i+1}", ["LB", "LCB", "CB", "RCB", "RB"])
    
    st.subheader("MF")
    for i in range(mf_n): pos_data[f'mf_{i+1}'] = q_role_box(f"MF {i+1}", f"mf_{i+1}", ["CAM", "LM", "CM", "RM", "CDM"])
    
    st.subheader("FW")
    for i in range(fw_n): pos_data[f'fw_{i+1}'] = q_role_box(f"FW {i+1}", f"fw_{i+1}", ["ST", "CF", "LW", "RW"])

    if is_admin and st.button(f"💾 {q_choice} 저장"):
        requests.post(API_URL, json={"action": "save_lineup", "date": selected_match, "quarter": q_choice, "positions": pos_data, "formation": formation})
        st.cache_data.clear()
        st.rerun()
