import streamlit as st
import pandas as pd
import requests
import datetime
import json

# --- 1. 기본 설정 ---
st.set_page_config(page_title="D'fit 통합 관리", layout="centered", page_icon="⚽")

# --- 2. 초간단 로그인 시스템 (해시 미사용) ---
ADMIN_ID = "master"
ADMIN_PW = "dfit2026"

# 세션 상태 초기화 (로그인 정보 저장용)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

with st.sidebar:
    st.header("🔐 관리자 로그인")
    
    if not st.session_state["authenticated"]:
        input_id = st.text_input("아이디", key="login_id")
        input_pw = st.text_input("비밀번호", type="password", key="login_pw")
        
        if st.button("로그인"):
            if input_id == ADMIN_ID and input_pw == ADMIN_PW:
                st.session_state["authenticated"] = True
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")
    else:
        st.success(f"반갑습니다, {ADMIN_ID}님!")
        if st.button("로그아웃"):
            st.session_state["authenticated"] = False
            st.rerun()

is_admin = st.session_state["authenticated"]

# --- 3. 디자인 및 API 설정 ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    .stTable { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

API_URL = "https://script.google.com/macros/s/AKfycbzYMf0rfazFlzLrGuzq6o4QH37Dgpp3p_7M91yNykTjuEN9C7sbYwWIrKKWj6P9LB4A/exec"

# 4. 경기 일정 설정
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

# 데이터 로딩 함수 (캐시 적용)
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

# --- 5. 보조 함수 ---
def role_position_box(label_prefix, p_id, role_options, confirmed_players, saved_positions):
    col_name, col_role = st.columns([2, 1])
    prefix = f"{selected_match}_pos_"
    
    # 중복 체크
    taken = [v for k, v in st.session_state.items() if prefix in k and k != f"{prefix}{p_id}" and "|" in str(v)]
    taken_names = [t.split('|')[0] for t in taken]
    
    available = ["미배정"] + [p for p in confirmed_players if p not in taken_names]
    
    saved_val = saved_positions.get(p_id, "미배정|")
    s_name, s_role = saved_val.split('|') if '|' in saved_val else (saved_val, "")
    
    with col_name:
        if s_name not in available and s_name in confirmed_players: available.append(s_name)
        idx = available.index(s_name) if s_name in available else 0
        sel_name = st.selectbox(f"{label_prefix} 이름", available, index=idx, key=f"{prefix}{p_id}_name")
    
    with col_role:
        role_idx = role_options.index(s_role) if s_role in role_options else 0
        sel_role = st.selectbox(f"{label_prefix} 역할", role_options, index=role_idx, key=f"{prefix}{p_id}_role")
        
    return f"{sel_name}|{sel_role}"

# --- 6. 메인 화면 ---
tab1, tab2 = st.tabs(["📝 신청 및 명단 확인", "🏃 세부 전략판"])

with tab1:
    # (신청/취소/명단/조끼추첨 로직 - 기존과 동일하게 들어감)
    st.info("여기는 기존 신청 명단 페이지입니다.")
    # ... 중략 (재환님 기존 탭1 코드 그대로 유지 가능)

with tab2:
    st.header("📝 D'fit 가변 전략판")
    formation = st.text_input("포메이션 (예: 4-4-2)", value="4-4-2")
    try:
        df_n, mf_n, fw_n = map(int, formation.split('-'))
    except:
        df_n, mf_n, fw_n = 4, 4, 2

    # 데이터 로드
    saved_positions = {}
    for row in lineup_raw:
        if len(row) >= 3 and row[0] == selected_match: # 쿼터 구분 생략 시
            try: saved_positions = json.loads(row[2])
            except: saved_positions = {}
            break

    confirmed_players = confirmed_df['이름'].tolist()
    
    DF_ROLES = ["LB", "LCB", "CB", "RCB", "RB"]
    MF_ROLES = ["CAM", "LM", "CM", "RM", "CDM"]
    FW_ROLES = ["ST", "CF", "LW", "RW"]

    pos_data = {}
    st.subheader("🧤 골키퍼")
    pos_data['gk'] = role_position_box("GK", "gk", ["GK"], confirmed_players, saved_positions)

    st.subheader(f"🛡️ 수비수 ({df_n}명)")
    for i in range(df_n):
        pos_data[f'df_{i+1}'] = role_position_box(f"DF {i+1}", f"df_{i+1}", DF_ROLES, confirmed_players, saved_positions)

    st.subheader(f"🏃 미드필더 ({mf_n}명)")
    for i in range(mf_n):
        pos_data[f'mf_{i+1}'] = role_position_box(f"MF {i+1}", f"mf_{i+1}", MF_ROLES, confirmed_players, saved_positions)

    st.subheader(f"⚽ 공격수 ({fw_n}명)")
    for i in range(fw_n):
        pos_data[f'fw_{i+1}'] = role_position_box(f"FW {i+1}", f"fw_{i+1}", FW_ROLES, confirmed_players, saved_positions)

    if is_admin:
        if st.button("💾 라인업 저장"):
            requests.post(API_URL, json={"action": "save_lineup", "date": selected_match, "positions": pos_data})
            st.success("저장되었습니다!")
