import streamlit as st
import pandas as pd
import requests
import datetime
import json
import plotly.graph_objects as go

# --- 1. 기본 설정 및 보안 (URL 파라미터 인증) ---
st.set_page_config(page_title="D'fit 통합 관리", layout="centered", page_icon="⚽")

# [보안] GitHub 노출 방지를 위해 Streamlit Secrets 사용
try:
    ADMIN_PW = st.secrets["admin_password"]
except:
    ADMIN_PW = "dfit2026"  # Secrets 미설정 시 기본 비번

# URL 파라미터 확인 (예: https://your-app.streamlit.app/?pw=dfit2026)
user_pw = st.query_params.get("pw", "")
is_admin = (user_pw == ADMIN_PW)

with st.sidebar:
    if is_admin:
        st.success("✅ 관리자 모드 활성")
        st.caption("새로고침해도 로그인이 유지됩니다.")
        if st.button("로그아웃"):
            st.query_params.clear()
            st.rerun()
    else:
        st.warning("일반 사용자 모드")
        st.caption("관리자는 전용 URL로 접속하세요.")

# --- 2. API 설정 및 데이터 로드 ---
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

selected_match = st.selectbox("📅 경기 일정을 선택하세요", list(MATCH_CONFIG.keys()))
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

# --- 3. 세로형 전술 보드 시각화 함수 ---
def draw_pitch(positions_data):
    # 데이터가 문자열이면 딕셔너리로 변환 (매우 중요)
    if isinstance(positions_data, str):
        try:
            positions_data = json.loads(positions_data)
        except:
            return go.Figure().add_annotation(text="데이터 형식 오류", showarrow=False)

    fig = go.Figure()
    
    # 1. 경기장 배경 및 라인
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, fillcolor="seagreen", line_color="white", line_width=2)
    fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line_color="white", line_width=2)
    fig.add_shape(type="circle", x0=35, y0=40, x1=65, y1=60, line_color="white", line_width=2)
    # 골 박스 및 골대
    fig.add_shape(type="rect", x0=20, y0=0, x1=80, y1=12, line_color="white") # 하단
    fig.add_shape(type="rect", x0=20, y0=88, x1=80, y1=100, line_color="white") # 상단
    fig.add_shape(type="line", x0=40, y0=-2, x1=60, y1=-2, line_color="white", line_width=4)
    fig.add_shape(type="line", x0=40, y0=102, x1=60, y1=102, line_color="white", line_width=4)

    # 2. 좌표 설정 (키값 매칭 최적화)
    coords = {'gk': [50, 6]}
    # 데이터 키값을 소문자로 통일하여 비교
    normalized_data = {str(k).lower().strip(): v for k, v in positions_data.items()}
    
    for prefix, y_val in [('df', 28), ('mf', 53), ('fw', 78)]:
        p_keys = sorted([k for k in normalized_data.keys() if prefix in k])
        for i, k in enumerate(p_keys):
            x_val = (100 / (len(p_keys) + 1)) * (i + 1)
            coords[k] = [x_val, y_val]

    # 3. 선수 점 및 텍스트 추가
    x_f, y_f, labels = [], [], []
    for p_id, loc in coords.items():
        if p_id in normalized_data:
            info = normalized_data[p_id]
            if "|" in str(info):
                name, role = str(info).split("|")
                if name.strip() and name != "미배정":
                    x_f.append(loc[0])
                    y_f.append(loc[1])
                    labels.append(f"<b>{name}</b><br>{role}")

    if x_f:
        fig.add_trace(go.Scatter(
            x=x_f, y=y_f, mode="markers+text",
            marker=dict(size=24, color="white", line=dict(width=3, color="navy")),
            text=labels, textposition="top center",
            textfont=dict(color="white", size=14, family="Arial Black"),
            showlegend=False
        ))
    else:
        fig.add_annotation(x=50, y=50, text="배치된 선수가 없습니다", showarrow=False, font=dict(color="white", size=16))

    fig.update_layout(
        width=450, height=650,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 110]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 110]),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

# --- 4. 메인 UI 탭 구성 ---
tab1, tab2 = st.tabs(["📝 신청 및 명단", "🏃 라인업 전략"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🙋 참석 신청")
        with st.form("add_form", clear_on_submit=True):
            name_input = st.text_input("이름")
            if st.form_submit_button("참석 확정"):
                if name_input.strip():
                    now = datetime.datetime.now().strftime("%H:%M")
                    requests.post(API_URL, json={"action": "add", "date": selected_match, "name": name_input, "time": now})
                    st.cache_data.clear()
                    st.rerun()
    with col2:
        st.subheader("🚫 신청 취소")
        if is_admin:
            with st.form("del_form", clear_on_submit=True):
                del_name = st.text_input("취소할 이름")
                if st.form_submit_button("취소하기"):
                    requests.post(API_URL, json={"action": "delete", "date": selected_match, "name": del_name})
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.info("취소 권한은 관리자 전용입니다.")

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
    st.header("🏃 쿼터별 전략 보드")
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)
    
    # 데이터 로드 로직
    saved_positions = {}
    saved_formation = "4-3-3"
    
    for row in lineup_raw:
        if len(row) >= 3:
            if str(row[0]).strip() == selected_match.strip() and str(row[1]).strip() == q_choice.strip():
                try:
                    saved_positions = json.loads(str(row[2]))
                    if len(row) >= 4:
                        saved_formation = str(row[3]).replace("'", "").strip()
                    break
                except: pass

    if is_admin:
        formation = st.text_input(f"{q_choice} 포메이션 (예: 4-3-3)", value=saved_formation, key=f"f_in_{q_choice}")
    else:
        st.subheader(f"🏟️ {q_choice} 포메이션: {saved_formation}")
        formation = saved_formation

    try:
        df_n, mf_n, fw_n = map(int, formation.split('-'))
    except:
        df_n, mf_n, fw_n = 4, 3, 3

    # 관리자 입력 UI
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
            with c2: sel_r = st.selectbox(f"{label} 역할", options, key=f"{prefix}_{p_id}_role", index=options.index(s_role) if s_role in options else 0)
            return f"{sel_n}|{sel_r}"

        st.subheader("🧤 GK")
        pos_data['gk'] = q_role_box("골키퍼", "gk", ["GK"])
        st.subheader("🛡️ DF")
        for i in range(df_n): pos_data[f'df_{i+1}'] = q_role_box(f"수비수 {i+1}", f"df_{i+1}", ["LB", "LCB", "CB", "RCB", "RB"])
        st.subheader("🏃 MF")
        for i in range(mf_n): pos_data[f'mf_{i+1}'] = q_role_box(f"미드필더 {i+1}", f"mf_{i+1}", ["CAM", "LM", "CM", "RM", "CDM"])
        st.subheader("⚽ FW")
        for i in range(fw_n): pos_data[f'fw_{i+1}'] = q_role_box(f"공격수 {i+1}", f"fw_{i+1}", ["ST", "CF", "LW", "RW"])

        if st.button(f"💾 {q_choice} 라인업 저장"):
            requests.post(API_URL, json={"action": "save_lineup", "date": selected_match, "quarter": q_choice, "positions": pos_data, "formation": formation})
            st.cache_data.clear()
            st.rerun()
    else:
        pos_data = saved_positions

    # 전술 보드 시각화 출력 (최종)
    if pos_data:
        st.divider()
        
        st.plotly_chart(draw_pitch(pos_data), use_container_width=False)
