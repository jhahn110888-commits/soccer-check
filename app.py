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
API_URL = "https://script.google.com/macros/s/AKfycbwyAWhVK4KGk0GJcNz1GJt1RzudRmRgf0SK_pADPZ3NrmLiree0p9WRZb5ZhHf0aema/exec"

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
        # 현재 경기_쿼터 정보를 포함한 고유 키 접두사
        prefix = f"{selected_match}_{q_choice}"
        
        # 1. 현재 쿼터 내에서 이미 선택된 모든 이름 수집 (자기 자신은 제외)
        # 세션 상태에 저장된 값들 중 '이름|역할' 형태인 것들을 찾아 이름만 추출합니다.
        current_selections = []
        for k, v in st.session_state.items():
            if prefix in k and "_name" in k and k != f"{prefix}_{p_id}_name":
                if v != "미배정":
                    current_selections.append(v)
        
        # 2. 전체 확정 명단에서 이미 선택된 사람 제외
        available = ["미배정"] + [p for p in confirmed_players if p not in current_selections]
        
        # 3. 기존 저장된 데이터 불러오기
        saved_val = saved_positions.get(p_id, "미배정|")
        s_name, s_role = saved_val.split('|') if '|' in saved_val else (saved_val, "")
        
        with c1:
            # 저장된 이름이 현재 선택 가능한 목록에 없더라도(중복 방지 로직 때문), 
            # 화면에 표시하기 위해 목록에 강제로 추가해줍니다.
            display_available = available.copy()
            if s_name != "미배정" and s_name not in display_available:
                display_available.append(s_name)
            
            idx = display_available.index(s_name) if s_name in display_available else 0
            sel_n = st.selectbox(f"{label} 이름", display_available, index=idx, key=f"{prefix}_{p_id}_name")
            
        with c2:
            r_idx = options.index(s_role) if s_role in options else 0
            sel_r = st.selectbox(f"{label} 역할", options, index=r_idx, key=f"{prefix}_{p_id}_role")
            
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
    st.header("📝 D'fit 쿼터별 세부 전략판")
    
    # --- [함수 정의: 호출보다 위에 있어야 에러가 안 납니다] ---
    def handle_change():
        # 선택 시 화면을 다시 그려 목록을 실시간 업데이트합니다.
        pass 

    def q_role_box(label, p_id, options, confirmed_players, saved_positions, q_choice, selected_match):
        c1, c2 = st.columns([2, 1])
        prefix = f"{selected_match}_{q_choice}"
        
        # 1. 현재 쿼터 내에서 이미 선택된 이름들 수집 (자기 자신 제외)
        current_selections = []
        for k, v in st.session_state.items():
            if prefix in k and "_name" in k and k != f"{prefix}_{p_id}_name":
                if v != "미배정":
                    current_selections.append(v)
        
        # 2. 전체 명단에서 선택된 사람 제외
        available = ["미배정"] + [p for p in confirmed_players if p not in current_selections]
        
        # 3. 저장된 값 불러오기
        saved_val = saved_positions.get(p_id, "미배정|")
        s_name, s_role = saved_val.split('|') if '|' in saved_val else (saved_val, "")
        
        with c1:
            # 현재 선택된 이름은 목록에 유지 (에러 방지)
            display_list = available.copy()
            if s_name != "미배정" and s_name not in display_list:
                display_list.append(s_name)
            
            idx = display_list.index(s_name) if s_name in display_list else 0
            sel_n = st.selectbox(
                f"{label} 이름", 
                display_list, 
                index=idx, 
                key=f"{prefix}_{p_id}_name",
                on_change=handle_change # 상태 변경 시 즉시 반영
            )
        with c2:
            r_idx = options.index(s_role) if s_role in options else 0
            sel_r = st.selectbox(
                f"{label} 역할", 
                options, 
                index=r_idx, 
                key=f"{prefix}_{p_id}_role"
            )
        return f"{sel_n}|{sel_r}"
    # --- [함수 정의 끝] ---

    # 1. 쿼터 및 포메이션 설정
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)
    
    # 데이터 로드
    saved_positions = {}
    saved_formation = "4-4-2"
    for row in lineup_raw:
        if len(row) >= 4 and row[0] == selected_match and row[1] == q_choice:
            try: 
                saved_positions = json.loads(row[2])
                saved_formation = row[3] if row[3] else "4-4-2"
            except: pass
            break

    if is_admin:
        formation = st.text_input(f"{q_choice} 포메이션 설정", value=saved_formation)
    else:
        st.info(f"현재 포메이션: **{saved_formation}**")
        formation = saved_formation

    try:
        df_n, mf_n, fw_n = map(int, formation.split('-'))
    except:
        df_n, mf_n, fw_n = 4, 4, 2

    confirmed_players = confirmed_df['이름'].tolist()
    DF_ROLES = ["LB", "LCB", "CB", "RCB", "RB"]
    MF_ROLES = ["CAM", "LM", "CM", "RM", "CDM"]
    FW_ROLES = ["ST", "CF", "LW", "RW"]

    # 2. 라인업 배치 UI 호출
    pos_data = {}
    st.subheader(f"🧤 {q_choice} 골키퍼")
    pos_data['gk'] = q_role_box("GK", "gk", ["GK"], confirmed_players, saved_positions, q_choice, selected_match)

    st.subheader(f"🛡️ {q_choice} 수비수")
    for i in range(df_n): 
        p_id = f'df_{i+1}'
        pos_data[p_id] = q_role_box(f"DF {i+1}", p_id, DF_ROLES, confirmed_players, saved_positions, q_choice, selected_match)

    st.subheader(f"🏃 {q_choice} 미드필더")
    for i in range(mf_n): 
        p_id = f'mf_{i+1}'
        pos_data[p_id] = q_role_box(f"MF {i+1}", p_id, MF_ROLES, confirmed_players, saved_positions, q_choice, selected_match)

    st.subheader(f"⚽ {q_choice} 공격수")
    for i in range(fw_n): 
        p_id = f'fw_{i+1}'
        pos_data[p_id] = q_role_box(f"FW {i+1}", p_id, FW_ROLES, confirmed_players, saved_positions, q_choice, selected_match)

    # 3. 저장 버튼
    if is_admin:
        st.divider()
        if st.button(f"💾 {q_choice} 설정 저장"):
            requests.post(API_URL, json={
                "action": "save_lineup", 
                "date": selected_match, 
                "quarter": q_choice, 
                "positions": pos_data,
                "formation": formation
            })
            st.cache_data.clear()
            st.success("저장되었습니다!")
            st.rerun()
