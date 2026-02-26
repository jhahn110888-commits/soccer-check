import streamlit as st
import pandas as pd
import requests
import datetime
import json

# --- 설정 및 디자인 ---
st.set_page_config(page_title="D'fit 통합 관리", layout="centered", page_icon="⚽")

# CSS로 디자인 강화
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    .stTable { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- API 설정 (본인의 구글 앱 스크립트 URL을 입력하세요) ---
API_URL = "https://script.google.com/macros/s/AKfycbzYMf0rfazFlzLrGuzq6o4QH37Dgpp3p_7M91yNykTjuEN9C7sbYwWIrKKWj6P9LB4A/exec"

st.title("⚽ D'fit 운영 시스템")

# 1. 일정 및 인원 제한 설정
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
                name = st.text_input("이름", placeholder="이름을 입력하세요")
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
            del_name = st.text_input("이름")
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

    # (기존 확정 명단 표 아래에 추가)
    st.divider()
    st.subheader("🧺 오늘 조끼 빨 사람?")
    
    if not current_match_df.empty:
        # 세션 상태를 사용해서 버튼을 눌러도 당첨자가 바로 바뀌지 않게 고정할 수 있습니다.
        if 'laundry_hero' not in st.session_state:
            st.session_state.laundry_hero = None

        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🎰 랜덤 추첨하기"):
                import random
                # 현재 신청자 명단에서 랜덤 추출
                winner = random.choice(current_match_df['이름'].tolist())
                st.session_state.laundry_hero = winner
                st.balloons() # 축하 풍선 효과!

        with col2:
            if st.session_state.laundry_hero:
                st.markdown(f"### 🎉 당첨자: **{st.session_state.laundry_hero}** 님!")
                st.write("축하합니다! 깨끗한 조끼 부탁드려요. 😉")
            else:
                st.write("버튼을 눌러 당번을 정해주세요.")
    else:
        st.write("신청자가 있어야 당번을 뽑을 수 있습니다.")
# [탭 2: 쿼터별 라인업 (날짜/쿼터 연동 저장)]
with tab2: # 이전 코드에서 tab2로 통합된 전략판 부분
    st.header("📝 쿼터별 라인업")
    q_choice = st.radio("쿼터 선택", ["1쿼터", "2쿼터", "3쿼터", "4쿼터"], horizontal=True)
    
    # 1. 저장된 라인업 불러오기
    saved_positions = {}
    for row in lineup_raw:
        if len(row) >= 3 and row[0] == selected_match and row[1] == q_choice:
            try: saved_positions = json.loads(row[2])
            except: saved_positions = {}
            break

    # 2. 현재 해당 쿼터에서 선택된 모든 이름 추적 (실시간 반영을 위해 session_state 활용)
    # 초기화
    pos_keys = ['fw1', 'fw2', 'mf1', 'mf2', 'mf3', 'mf4', 'df1', 'df2', 'df3', 'df4', 'gk']
    all_players = current_match_df['이름'].tolist()
    
    st.divider()
    st.subheader(f"🏟️ {selected_match} - {q_choice}")

    # 현재 화면상에서 선택된 사람들을 모으는 함수
    def get_currently_selected(exclude_key):
        selected = []
        for k in pos_keys:
            if k != exclude_key:
                val = st.session_state.get(f"{selected_match}_{q_choice}_{k}", "미배정")
                if val != "미배정":
                    selected.append(val)
        return selected

    pos_data = {}
    
    # 포지션 배치 UI 구성
    # 각 포지션마다 다른 포지션에서 선택된 사람을 제외한 목록을 보여줌
    def position_box(label, key):
        already_taken = get_currently_selected(key)
        # 현재 명단에서 이미 선점된 사람 제외
        available_options = ["미배정"] + [p for p in all_players if p not in already_taken]
        
        # 기본값 설정 (저장된 값이 명단에 없으면 미배정)
        default_val = saved_positions.get(key, "미배정")
        if default_val not in available_options:
            # 만약 저장된 사람이 다른 곳에 배정되어 있다면 미배정으로 표시하거나, 
            # 목록에 강제로 추가(현재 자기 자리니까)
            if default_val in all_players:
                available_options.append(default_val)
                available_options = sorted(list(set(available_options)), key=lambda x: (x != "미배정", x))
        
        try:
            idx = available_options.index(default_val)
        except ValueError:
            idx = 0
            
        return st.selectbox(label, available_options, index=idx, key=f"{selected_match}_{q_choice}_{key}")

    # --- 화면 배치 ---
    st.caption("공격수 (FW)")
    f1, f2 = st.columns(2)
    pos_data['fw1'] = position_box("ST(L)", 'fw1')
    pos_data['fw2'] = position_box("ST(R)", 'fw2')

    st.caption("미드필더 (MF)")
    m1, m2, m3, m4 = st.columns(4)
    pos_data['mf1'] = position_box("LM", 'mf1')
    pos_data['mf2'] = position_box("CM(L)", 'mf2')
    pos_data['mf3'] = position_box("CM(R)", 'mf3')
    pos_data['mf4'] = position_box("RM", 'mf4')

    st.caption("수비수 (DF)")
    d1, d2, d3, d4 = st.columns(4)
    pos_data['df1'] = position_box("LB", 'df1')
    pos_data['df2'] = position_box("CB(L)", 'df2')
    pos_data['df3'] = position_box("CB(R)", 'df3')
    pos_data['df4'] = position_box("RB", 'df4')

    st.caption("골키퍼 (GK)")
    pos_data['gk'] = position_box("GK", 'gk')

    st.divider()
    if st.button("💾 저장하기"):
        with st.spinner("구글 시트에 저장 중..."):
            requests.post(API_URL, json={
                "action": "save_lineup",
                "date": selected_match,
                "quarter": q_choice,
                "positions": pos_data
            })
            st.cache_data.clear()
            st.success("저장되었습니다!")
            st.rerun()

