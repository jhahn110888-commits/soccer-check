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
    "2026-03-26 (
