import streamlit as st
import pandas as pd
import requests
import datetime
import json
import plotly.graph_objects as go

# --- 1. 기본 설정 및 보안 (순서 중요!) ---
st.set_page_config(page_title="D'fit 통합 관리", layout="centered", page_icon="⚽")

# [보안] is_admin 정의를 최상단으로 올렸습니다.
try:
    ADMIN_PW = st.secrets["admin_password"]
except:
    ADMIN_PW = "test1234"

# URL 파라미터에서 비번 확인 (?pw=dfit2026 형태)
user_pw = st.query_params.get("pw", "")
is_admin = (user_pw == ADMIN_PW)

with st.sidebar:
    if is_admin:
        st.success("✅ 관리자 모드 활성")
        if st.button("로그아웃"):
            st.query_params.clear()
            st.rerun()
    else:
        st.warning("일반 사용자 모드")

# --- 2. API 및 데이터 로드 ---
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

# --- 3. 전술판 시각화 함수 ---
def draw_pitch(positions_data):
    fig = go.Figure()
    
    # 1. 축구장 배경 및 라인 (세로형 0~100)
    # 전체 필드
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="seagreen", line_color="white", line_width=2)
    
    # 중앙선 및 센터서클
    fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line_color="white", line_width=2)
    fig.add_shape(type="circle", x0=35, y0=40, x1=65, y1=60, line_color="white", line_width=2)

    # --- [골대 및 박스 추가] ---
    # 하단 페널티 박스 (우리 편)
    fig.add_shape(type="rect", x0=20, y0=0, x1=80, y1=15, line_color="white", line_width=2) # 큰 박스
    fig.add_shape(type="rect", x0=35, y0=0, x1=65, y1=5, line_color="white", line_width=2)  # 소박스
    # 하단 골대 라인
    fig.add_shape(type="line", x0=40, y0=-2, x1=60, y1=-2, line_color="white", line_width=4)

    # 상단 페널티 박스 (상대 편)
    fig.add_shape(type="rect", x0=20, y0=85, x1=80, y1=100, line_color="white", line_width=2) # 큰 박스
    fig.add_shape(type="rect", x0=35, y0=95, x1=65, y1=100, line_color="white", line_width=2) # 소박스
    # 상단 골대 라인
    fig.add_shape(type="line", x0=40, y0=102, x1=60, y1=102, line_color="white", line_width=4)

    # 2. 포지션별 좌표 설정 (세로 배치 최적화)
    coords = {}
    
    # 골키퍼 (우리 편 골대 앞)
    coords['gk'] = [50, 7]
    
    # 수비수 (우리 편 진영)
    df_list = [k for k in positions_data.keys() if 'df_' in k]
    for i, k in enumerate(df_list):
        coords[k] = [(100 / (len(df_list) + 1)) * (i + 1), 25]
        
    # 미드필더 (중앙 지역)
    mf_list = [k for k in positions_data.keys() if 'mf_' in k]
    for i, k in enumerate(mf_list):
        coords[k] = [(100 / (len(mf_list) + 1)) * (i + 1), 50]
        
    # 공격수 (상대 편 진영)
    fw_list = [k for k in positions_data.keys() if 'fw_' in k]
    for i, k in enumerate(fw_list):
        coords[k] = [(100 / (len(fw_list) + 1)) * (i + 1), 75]

    # 3. 선수 데이터 시각화
    if positions_data:
        x_coords, y_coords, names = [], [], []
        for p_id, info in positions_data.items():
            if "|" in info:
                name, role = info.split("|")
                if name != "미배정" and p_id in coords:
                    x, y = coords[p_id]
                    x_coords.append(x)
                    y_coords.append(y)
                    names.append(f"<b>{name}</b><br>{role}")

        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords,
            mode="markers+text",
            marker=dict(size=20, color="white", line=dict(width=3, color="navy")),
            text=names,
            textposition="top center",
            textfont=dict(color="white", size=13),
            hoverinfo='none',
            showlegend=False
        ))

    # 레이아웃 설정 (세로 길게)
    fig.update_layout(
        width=450, height=650,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 110]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 110]),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

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
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)
    
    saved_positions = {}
    saved_formation = "4-4-2"
    
    for row in lineup_raw:
        if len(row) >= 2 and str(row[0]).strip() == selected_match.strip() and str(row[1]).strip() == q_choice.strip():
            try:
                saved_positions = json.loads(row[2])
                if len(row) >= 4: saved_formation = str(row[3]).replace("'", "").strip()
            except: pass
            break 

    # [일반 모드 최적화] 관리자만 포메이션 수정 가능
    if is_admin:
        formation = st.text_input(f"{q_choice} 포메이션 설정", value=saved_formation, key=f"form_input_{q_choice}")
    else:
        st.subheader(f"🏟️ {q_choice} 포메이션: {saved_formation}")
        formation = saved_formation

    try:
        df_n, mf_n, fw_n = map(int, formation.split('-'))
    except:
        df_n, mf_n, fw_n = 4, 4, 2

    # 관리자 모드일 때만 선수 선택창 표시
    pos_data = {}
    if is_admin:
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
            with c1: sel_n = st.selectbox(label, display_list, key=name_key)
            with c2: sel_r = st.selectbox(label, options, key=f"{prefix}_{p_id}_role", index=options.index(s_role) if s_role in options else 0)
            return f"{sel_n}|{sel_r}"

        st.subheader("GK")
        pos_data['gk'] = q_role_box("GK", "gk", ["GK"])
        st.subheader("DF")
        for i in range(df_n): pos_data[f'df_{i+1}'] = q_role_box(f"DF {i+1}", f"df_{i+1}", ["LB", "LCB", "CB", "RCB", "RB"])
        st.subheader("MF")
        for i in range(mf_n): pos_data[f'mf_{i+1}'] = q_role_box(f"MF {i+1}", f"mf_{i+1}", ["CAM", "LM", "CM", "RM", "CDM"])
        st.subheader("FW")
        for i in range(fw_n): pos_data[f'fw_{i+1}'] = q_role_box(f"FW {i+1}", f"fw_{i+1}", ["ST", "CF", "LW", "RW"])

        if st.button(f"💾 {q_choice} 저장"):
            requests.post(API_URL, json={"action": "save_lineup", "date": selected_match, "quarter": q_choice, "positions": pos_data, "formation": formation})
            st.cache_data.clear()
            st.rerun()
    else:
        # 일반 사용자는 선택창 대신 저장된 데이터를 시각화용 데이터로 사용
        pos_data = saved_positions

    # 시각화 전술판 출력
    if pos_data:
        st.divider()
        st.plotly_chart(draw_pitch(pos_data), use_container_width=True)
