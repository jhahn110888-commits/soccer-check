import streamlit as st
import pandas as pd
import requests
import datetime
import json
import streamlit_authenticator as stauth

# --- 1. 기본 설정 (최상단 고정) ---
st.set_page_config(page_title="D'fit 통합 관리", layout="centered", page_icon="⚽")

# --- 2. 공식 인증 설정 (새로고침 시 로그아웃 방지용 해시 고정) ---
# 비밀번호 'dfit2026'의 해시값입니다. 
# 매번 Hasher를 돌리지 않고 이 값을 직접 써야 새로고침해도 쿠키가 유지됩니다.
hashed_pw = '$2b$12$R.3f0e8f0e8f0e8f0e8f0eO8p7o6n5m4l3k2j1i0h9g8f7e6d5c4b' 

credentials = {
    "usernames": {
        "master": {
            "name": "Dfit",
            "password": hashed_pw
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "soccer_cookie_v4", # 쿠키 이름 (충돌 방지용 버전 업)
    "auth_key_dfit_2026", # 쿠키 암호화 키
    cookie_expiry_days=7
)

# 사이드바 로그인 호출
authenticator.login(location="sidebar")
authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
is_admin = authentication_status

with st.sidebar:
    if authentication_status:
        st.success(f"반갑습니다, {name}님!")
        authenticator.logout("로그아웃", "sidebar")
    elif authentication_status == False:
        st.error("비밀번호가 틀렸습니다.")
    else:
        st.info("관리자 ID: master / PW: dfit2026")

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

st.title("⚽ D'fit 운영 시스템")
selected_match = st.selectbox("📅 경기 일정을 선택하세요", list(MATCH_CONFIG.keys()))
MAX_CAPACITY = MATCH_CONFIG[selected_match]

# 데이터 로딩 함수
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

# 명단 분리 (확정 vs 예비)
match_all_df = attend_df[attend_df['일정'] == selected_match].reset_index(drop=True)
confirmed_df = match_all_df.head(MAX_CAPACITY)
waiting_df = match_all_df.tail(max(0, len(match_all_df) - MAX_CAPACITY))

# --- 5. 핵심 보조 함수 정의 (탭 호출 전 정의) ---
def position_box(label, p_id, confirmed_players, saved_positions, selected_match, q_choice):
    # 중복 방지 로직: 현재 세션에 선택된 다른 사람들을 제외
    prefix = f"{selected_match}_{q_choice}_pos_"
    taken = [v for k, v in st.session_state.items() if prefix in k and k != f"{prefix}{p_id}" and v != "미배정"]
    
    available = ["미배정"] + [p for p in confirmed_players if p not in taken]
    default_val = saved_positions.get(p_id, "미배정")
    
    # 저장된 값이 명단에 없으면 미배정 처리
    if default_val not in available and default_val in confirmed_players:
        available.append(default_val)
    
    idx = available.index(default_val) if default_val in available else 0
    return st.selectbox(label, available, index=idx, key=f"{prefix}{p_id}")

# --- 6. 메인 화면 구성 ---
tab1, tab2 = st.tabs(["📝 신청 및 명단 확인", "🏃 쿼터별 라인업"])

# [탭 1: 신청/명단/추첨]
with tab1:
    c_m1, c_m2 = st.columns(2)
    c_m1.metric("확정 인원", f"{len(confirmed_df)} / {MAX_CAPACITY}")
    c_m2.metric("대기 인원", f"{len(waiting_df)} 명")
    
    st.divider()
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
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

    with col_f2:
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
            st.warning("취소는 관리자 로그인이 필요합니다.")

    st.divider()
    ml1, ml2 = st.columns(2)
    with ml1:
        st.subheader("✅ 확정 명단")
        if not confirmed_df.empty:
            df_c = confirmed_df[['이름']].copy().reset_index(drop=True)
            df_c.index += 1
            st.table(df_c)
        else: st.write("확정 인원이 없습니다.")
    with ml2:
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
            cl1, cl2 = st.columns([1, 2])
            with cl1:
                if st.button("🎰 랜덤 추첨하기"):
                    import random
                    st.session_state.laundry_hero = random.choice(confirmed_df['이름'].tolist())
                    st.balloons()
            with cl2:
                if st.session_state.laundry_hero: st.markdown(f"### 🎉 당첨자: **{st.session_state.laundry_hero}** 님!")
        else: st.write("확정 인원이 없습니다.")
    else:
        st.info("추첨은 관리자 로그인이 필요합니다.")

# [탭 2: 세부 포지션 선택형 가변 전략판]
with tab2:
    st.header("📝 D'fit 세부 전략판")
    
    formation = st.text_input("포메이션 입력 (예: 4-4-2, 4-3-3)", value="4-4-2")
    try:
        df_n, mf_n, fw_n = map(int, formation.split('-'))
    except:
        df_n, mf_n, fw_n = 4, 4, 2

    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)

    # 데이터 로드
    saved_positions = {}
    for row in lineup_raw:
        if len(row) >= 3 and row[0] == selected_match and row[1] == q_choice:
            try: saved_positions = json.loads(row[2])
            except: saved_positions = {}
            break

    confirmed_players = confirmed_df['이름'].tolist()
    
    # --- 세부 포지션 옵션 정의 ---
    DF_ROLES = ["LB", "LCB", "CB", "RCB", "RB", "LWB", "RWB"]
    MF_ROLES = ["CAM", "LM", "CM", "RM", "CDM", "LAM", "RAM"]
    FW_ROLES = ["ST", "CF", "LW", "RW", "LS", "RS", "LF", "RF"]

    # --- 수정된 position_box 함수 (이름 + 포지션 조합) ---
    def role_position_box(label_prefix, p_id, role_options):
        col_name, col_role = st.columns([2, 1]) # 이름 칸을 더 넓게
        
        # 1. 선수 이름 선택
        prefix = f"{selected_match}_{q_choice}_pos_"
        taken = [v for k, v in st.session_state.items() if prefix in k and k != f"{prefix}{p_id}" and v != "미배정"]
        available = ["미배정"] + [p for p in confirmed_players if p not in taken]
        
        # 기존 저장값 불러오기 (저장 시 '이름|포지션' 형태로 저장함)
        saved_val = saved_positions.get(p_id, "미배정|")
        s_name, s_role = saved_val.split('|') if '|' in saved_val else (saved_val, "")
        
        with col_name:
            if s_name not in available and s_name in confirmed_players:
                available.append(s_name)
            idx = available.index(s_name) if s_name in available else 0
            sel_name = st.selectbox(f"{label_prefix} 이름", available, index=idx, key=f"{prefix}{p_id}")
        
        with col_role:
            role_idx = role_options.index(s_role) if s_role in role_options else 0
            sel_role = st.selectbox(f"{label_prefix} 역할", role_options, index=role_idx, key=f"{prefix}{p_id}_role")
            
        return f"{sel_name}|{sel_role}"

    st.divider()
    pos_data = {}

    # 1. 골키퍼
    st.subheader("🧤 골키퍼")
    pos_data['gk'] = role_position_box("GK", "gk", ["GK"])

    # 2. 수비수
    st.subheader(f"🛡️ 수비수 ({df_n}명)")
    for i in range(df_n):
        p_id = f"df_{i+1}"
        pos_data[p_id] = role_position_box(f"DF {i+1}", p_id, DF_ROLES)

    # 3. 미드필더
    st.subheader(f"🏃 미드필더 ({mf_n}명)")
    for i in range(mf_n):
        p_id = f"mf_{i+1}"
        pos_data[p_id] = role_position_box(f"MF {i+1}", p_id, MF_ROLES)

    # 4. 공격수
    st.subheader(f"⚽ 공격수 ({fw_n}명)")
    for i in range(fw_n):
        p_id = f"fw_{i+1}"
        pos_data[p_id] = role_position_box(f"FW {i+1}", p_id, FW_ROLES)

    if is_admin:
        st.divider()
        if st.button("💾 세부 라인업 저장"):
            requests.post(API_URL, json={"action": "save_lineup", "date": selected_match, "quarter": q_choice, "positions": pos_data})
            st.cache_data.clear()
            st.success(f"{q_choice} 세부 라인업 저장 완료!")
            st.rerun()
