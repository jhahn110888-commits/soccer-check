import streamlit as st
import pandas as pd
import requests
import datetime
import json

# --- 1. 기본 설정 ---
st.set_page_config(page_title="D'fit 통합 관리", layout="centered", page_icon="⚽")

# --- 2. URL 파라미터 기반 로그인 시스템 (새로고침 방어) ---
ADMIN_PW = "dfit2026"

# URL에서 'pw' 파라미터를 읽어옵니다.
# 예: https://your-app.streamlit.app/?pw=dfit2026
query_params = st.query_params
user_pw = query_params.get("pw", "")

# 관리자 여부 판별
is_admin = (user_pw == ADMIN_PW)

with st.sidebar:
    st.header("🔐 관리자 모드")
    if is_admin:
        if st.button("로그아웃 (일반 모드로)"):
            st.query_params.clear()
            st.rerun()
    else:
        st.warning("일반 사용자 모드")

# --- 3. 디자인 및 API 설정 ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    .stTable { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 재환님의 구글 앱스 스크립트 API URL
API_URL = "https://script.google.com/macros/s/AKfycbzYMf0rfazFlzLrGuzq6o4QH37Dgpp3p_7M91yNykTjuEN9C7sbYwWIrKKWj6P9LB4A/exec"

# 경기 일정 설정
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

# --- 4. 보조 함수 (전략판용) ---
def role_box(label, p_id, options):
    c1, c2 = st.columns([2, 1])
    prefix = f"{selected_match}_pos_"
    
    # 중복 체크 (세션 내에서 이름 중복 방지)
    taken_names = [v.split('|')[0] for k, v in st.session_state.items() if prefix in k and "|" in str(v) and k != f"{prefix}{p_id}_name"]
    available = ["미배정"] + [p for p in confirmed_players if p not in taken_names]
    
    saved_val = saved_positions.get(p_id, "미배정|")
    s_name, s_role = saved_val.split('|') if '|' in saved_val else (saved_val, "")
    
    with c1:
        if s_name not in available and s_name in confirmed_players: available.append(s_name)
        idx = available.index(s_name) if s_name in available else 0
        sel_n = st.selectbox(f"{label} 이름", available, index=idx, key=f"{prefix}{p_id}_name")
    with c2:
        r_idx = options.index(s_role) if s_role in options else 0
        sel_r = st.selectbox(f"{label}", options, index=r_idx, key=f"{prefix}{p_id}_role")
    return f"{sel_n}|{sel_r}"

# --- 5. 메인 화면 ---
tab1, tab2 = st.tabs(["📝 신청 및 명단 확인", "🏃 세부 전략판"])

with tab1:
    c_m1, c_m2 = st.columns(2)
    c_m1.metric("확정 인원", f"{len(confirmed_df)} / {MAX_CAPACITY}")
    c_m2.metric("대기 인원", f"{len(waiting_df)} 명")
    
    st.divider()
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.subheader("🙋 참석 신청")
        with st.form("add_form", clear_on_submit=True):
            u_name = st.text_input("이름", placeholder="실명을 입력하세요")
            if st.form_submit_button("참석 확정"):
                if u_name.strip() == "": st.warning("이름을 입력해주세요.")
                elif u_name in match_all_df['이름'].values: st.info("이미 등록된 이름입니다.")
                else:
                    now = datetime.datetime.now().strftime("%H:%M")
                    requests.post(API_URL, json={"action": "add", "date": selected_match, "name": u_name, "time": now})
                    st.cache_data.clear()
                    st.success(f"{u_name}님 신청 완료!")
                    st.rerun()

    with col_f2:
        st.subheader("🚫 신청 취소")
        if is_admin:
            with st.form("del_form", clear_on_submit=True):
                del_name = st.text_input("취소할 이름")
                if st.form_submit_button("신청 취소"):
                    requests.post(API_URL, json={"action": "delete", "date": selected_match, "name": del_name})
                    st.cache_data.clear()
                    st.success(f"{del_name}님 취소 완료.")
                    st.rerun()
        else:
            st.info("취소는 관리자 모드에서 가능합니다.")

    m_c1, m_c2 = st.columns(2)
    with m_c1:
        st.subheader("✅ 확정 명단")
        df_c = confirmed_df[['이름']].reset_index(drop=True)
        df_c.index += 1 
        st.table(df_c)
        
    with m_c2:
        st.subheader("⏳ 예비 명단")
        df_w = waiting_df[['이름']].reset_index(drop=True)
        df_w.index += 1
        st.table(df_w)

    if is_admin:
        st.divider()
        st.subheader("🎰 조끼 추첨")
        if st.button("랜덤 추첨 시작"):
            import random
            winner = random.choice(confirmed_df['이름'].tolist())
            st.balloons()
            st.success(f"오늘의 조끼 당번은 **{winner}** 님입니다!")

with tab2:
    st.header("📝 라인업")
    
    # 1. 포메이션 및 쿼터 선택
    formation = st.text_input("포메이션 (예: 4-4-2, 4-3-3)", value="4-4-2")
    try:
        df_n, mf_n, fw_n = map(int, formation.split('-'))
    except:
        df_n, mf_n, fw_n = 4, 4, 2

    # [중요] 쿼터 선택 - 이 값에 따라 데이터가 완전히 분리됩니다.
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)

    # 2. 해당 경기 & 해당 쿼터 데이터 로드
    saved_positions = {}
    for row in lineup_raw:
        # 조건에 '쿼터(row[1])' 정보를 추가하여 해당 쿼터 데이터만 가져옵니다.
        if len(row) >= 3 and row[0] == selected_match and row[1] == q_choice:
            try: 
                saved_positions = json.loads(row[2])
            except: 
                saved_positions = {}
            break

    confirmed_players = confirmed_df['이름'].tolist()
    
    DF_ROLES = ["LB", "LCB", "CB", "RCB", "RB"]
    MF_ROLES = ["CAM", "LM", "CM", "RM", "CDM"]
    FW_ROLES = ["ST", "CF", "LW", "RW"]

    # [중요] 키값에 q_choice를 포함시켜서 쿼터별로 입력창이 꼬이지 않게 합니다.
    def q_role_box(label, p_id, options):
        c1, c2 = st.columns([2, 1])
        # 쿼터별로 독립된 key 생성
        key_prefix = f"{selected_match}_{q_choice}_{p_id}"
        
        # 쿼터 내 중복 체크
        taken_names = [v.split('|')[0] for k, v in st.session_state.items() 
                       if f"{selected_match}_{q_choice}" in k and "|" in str(v) and k != f"{key_prefix}_name"]
        available = ["미배정"] + [p for p in confirmed_players if p not in taken_names]
        
        saved_val = saved_positions.get(p_id, "미배정|")
        s_name, s_role = saved_val.split('|') if '|' in saved_val else (saved_val, "")
        
        with c1:
            if s_name not in available and s_name in confirmed_players: available.append(s_name)
            idx = available.index(s_name) if s_name in available else 0
            sel_n = st.selectbox(f"{label} 이름", available, index=idx, key=f"{key_prefix}_name")
        with c2:
            r_idx = options.index(s_role) if s_role in options else 0
            sel_r = st.selectbox(f"{label}", options, index=r_idx, key=f"{key_prefix}_role")
        return f"{sel_n}|{sel_r}"

    # 포지션 배치 UI
    pos_data = {}
    st.subheader(f"GK")
    pos_data['gk'] = q_role_box("GK", "gk", ["GK"])

    st.subheader(f"DF")
    for i in range(df_n): 
        pos_data[f'df_{i+1}'] = q_role_box(f"DF {i+1}", f"df_{i+1}", DF_ROLES)

    st.subheader(f"MF")
    for i in range(mf_n): 
        pos_data[f'mf_{i+1}'] = q_role_box(f"MF {i+1}", f"mf_{i+1}", MF_ROLES)

    st.subheader(f"FW")
    for i in range(fw_n): 
        pos_data[f'fw_{i+1}'] = q_role_box(f"FW {i+1}", f"fw_{i+1}", FW_ROLES)

    # 3. 저장 버튼 (관리자 전용)
    if is_admin:
        st.divider()
        if st.button(f"💾 {q_choice} 라인업 저장"):
            # 구글 시트에 action: "save_lineup", date, quarter, positions 정보를 보냅니다.
            requests.post(API_URL, json={
                "action": "save_lineup", 
                "date": selected_match, 
                "quarter": q_choice, 
                "positions": pos_data
            })
            st.cache_data.clear()
            st.success(f"{q_choice} 라인업이 성공적으로 저장되었습니다!")
            st.rerun()
    else:
        st.warning("라인업 수정 권한이 없습니다. 관리자 모드로 접속하세요.")
