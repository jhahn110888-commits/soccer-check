import streamlit as st
import pandas as pd
import requests
import datetime
import json
import plotly.graph_objects as go

# --- 1. 기본 설정 및 보안 ---
st.set_page_config(page_title="D'fit 통합 관리", layout="centered", page_icon="⚽")

try:
    ADMIN_PW = st.secrets["admin_password"]
except:
    ADMIN_PW = "dfit2026"

user_pw = st.query_params.get("pw", "")
is_admin = (user_pw == ADMIN_PW)

with st.sidebar:
    if is_admin:
        st.success("✅ 관리자 모드 활성")
        if st.button("로그아웃 (캐시 초기화)"):
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

# --- 3. 세로형 전술 보드 시각화 ---
def draw_pitch(positions_data):
    if isinstance(positions_data, str):
        try: positions_data = json.loads(positions_data)
        except: return go.Figure()

    fig = go.Figure()
    
    # 🚨 [해결책] layer="below"를 추가해서 잔디밭을 맨 밑으로 뺍니다!
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="seagreen", line_color="white", line_width=2, layer="below")
    fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line_color="white", line_width=2, layer="below")
    fig.add_shape(type="circle", x0=35, y0=40, x1=65, y1=60, line_color="white", line_width=2, layer="below")
    fig.add_shape(type="rect", x0=20, y0=0, x1=80, y1=12, line_color="white", layer="below")
    fig.add_shape(type="rect", x0=20, y0=88, x1=80, y1=100, line_color="white", layer="below")

    # 패턴 매칭으로 좌표 배분 (대소문자 무시)
    coords = {}
    gk_keys = [k for k in positions_data.keys() if 'gk' in str(k).lower()]
    df_keys = sorted([k for k in positions_data.keys() if 'df' in str(k).lower()])
    mf_keys = sorted([k for k in positions_data.keys() if 'mf' in str(k).lower()])
    fw_keys = sorted([k for k in positions_data.keys() if 'fw' in str(k).lower()])

    if gk_keys: coords[gk_keys[0]] = [50, 7]
    for i, k in enumerate(df_keys): coords[k] = [(100 / (len(df_keys) + 1)) * (i + 1), 28]
    for i, k in enumerate(mf_keys): coords[k] = [(100 / (len(mf_keys) + 1)) * (i + 1), 53]
    for i, k in enumerate(fw_keys): coords[k] = [(100 / (len(fw_keys) + 1)) * (i + 1), 78]

    x_c, y_c, labels = [], [], []
    for p_id, loc in coords.items():
        info = positions_data[p_id]
        if "|" in str(info):
            name, role = str(info).split("|")
            if name.strip() and name != "미배정":
                x_c.append(loc[0])
                y_c.append(loc[1])
                labels.append(f"<b>{name}</b><br>{role}")

    if x_c:
        fig.add_trace(go.Scatter(
            x=x_c, y=y_c, mode="markers+text",
            marker=dict(size=25, color="white", line=dict(width=3, color="navy")),
            text=labels, textposition="top center",
            textfont=dict(color="white", size=14), showlegend=False
        ))
    else:
        fig.add_annotation(x=50, y=50, text="데이터는 읽었으나 그릴 선수가 없습니다", showarrow=False, font=dict(color="white", size=16))

    fig.update_layout(width=450, height=650, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 110]),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 110]),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig
    
# --- 4. 탭 구성 ---
tab1, tab2 = st.tabs(["📝 신청 및 명단", "🏃 라인업"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🙋 신청")
        with st.form("add", clear_on_submit=True):
            name = st.text_input("이름")
            if st.form_submit_button("참석"):
                now = datetime.datetime.now().strftime("%H:%M")
                requests.post(API_URL, json={"action": "add", "date": selected_match, "name": name, "time": now})
                st.cache_data.clear()
                st.rerun()
    with col2:
        st.subheader("🚫 취소")
        if is_admin:
            with st.form("del", clear_on_submit=True):
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
    saved_formation = "4-3-3"
    
    for row in lineup_raw:
        if len(row) >= 3:
            if str(row[0]).strip() == selected_match.strip() and str(row[1]).strip() == q_choice.strip():
                try:
                    saved_positions = json.loads(str(row[2]))
                    if len(row) >= 4: saved_formation = str(row[3]).replace("'", "").strip()
                    break
                except: pass

    if is_admin:
        formation = st.text_input(f"{q_choice} 포메이션 설정", value=saved_formation, key=f"form_input_{q_choice}")
    else:
        st.subheader(f"🏟️ {q_choice} 포메이션: {saved_formation}")
        formation = saved_formation

    try: df_n, mf_n, fw_n = map(int, formation.split('-'))
    except: df_n, mf_n, fw_n = 4, 3, 3

    pos_data = {}
    if is_admin:
        # [핵심 수정] UI 잠김 방지를 위해 가장 심플하고 안전한 로직으로 교체
        def q_role_box(label, p_id, options):
            c1, c2 = st.columns([2, 1])
            
            # 서버에서 데이터 읽어오기
            saved_val = saved_positions.get(p_id, "미배정|")
            s_name, s_role = saved_val.split('|') if '|' in saved_val else (saved_val, "")
            
            players = ["미배정"] + confirmed_df['이름'].tolist()
            if s_name not in players: players.append(s_name)
                
            n_idx = players.index(s_name)
            r_idx = options.index(s_role) if s_role in options else 0
            
            with c1: sel_n = st.selectbox(label, players, index=n_idx, key=f"{selected_match}_{q_choice}_{p_id}_n")
            with c2: sel_r = st.selectbox("역할", options, index=r_idx, key=f"{selected_match}_{q_choice}_{p_id}_r")
            
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
        pos_data = saved_positions

    st.divider()
    
    # 🚨 진짜 안 나올 때 원인을 파악하기 위한 디버그 패널 
    with st.expander("🛠️ (확인용) 현재 그림판에 들어가는 데이터"):
        st.write("서버에서 받은 데이터:", saved_positions)
        st.write("그림으로 그릴 데이터:", pos_data)
        
    if pos_data:
        st.plotly_chart(draw_pitch(pos_data), use_container_width=False)
