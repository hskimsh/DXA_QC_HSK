import os
import json
import hmac
import hashlib
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -------------------------------------------------------------
# Configuration & Constants
# -------------------------------------------------------------
st.set_page_config(
    page_title="DXA_QC_HSK 중앙 관제 & 비밀번호 발급 센터 | 김호성 교수",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

LICENSE_SECRET_SALT = 'DXA_QC_HSK_SHINHAN_UNIV_PROF_KIM_HO_SUNG_2026_SECURE_SALT_!#%'
DATA_DIR = os.path.join(os.path.dirname(__file__), 'server', 'data')
DB_FILE = os.path.join(DATA_DIR, 'hospital_qc_db.json')
KEYGEN_HISTORY_FILE = os.path.join(DATA_DIR, 'keygen_history.json')

os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------------------
# Database Helpers
# -------------------------------------------------------------
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"hospitals": {}}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_keygen_history():
    if os.path.exists(KEYGEN_HISTORY_FILE):
        try:
            with open(KEYGEN_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_keygen_history(history):
    with open(KEYGEN_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def generate_hospital_password(hospital_name: str, machine_id: str) -> str:
    clean_hosp = hospital_name.strip().upper()
    clean_mach = machine_id.strip().upper()
    message = f"{clean_hosp}::{clean_mach}".encode('utf-8')
    key = LICENSE_SECRET_SALT.encode('utf-8')
    h = hmac.new(key, message, hashlib.sha256).hexdigest()
    numeric_val = int(h[:8], 16)
    return str(100000 + (numeric_val % 900000))

# -------------------------------------------------------------
# Custom Styling
# -------------------------------------------------------------
st.markdown("""
<style>
    .main-title {
        font-size: 26px;
        font-weight: 900;
        color: #1e3a8a;
        margin-bottom: 2px;
    }
    .sub-title {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 18px;
    }
    .kpi-card {
        background-color: #ffffff;
        padding: 16px 20px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .kpi-title {
        font-size: 12px;
        font-weight: 700;
        color: #64748b;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 900;
        color: #0f172a;
        margin-top: 4px;
    }
    .badge-normal {
        background-color: #dcfce7;
        color: #15803d;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
    }
    .badge-action {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Top Header & Branding
# -------------------------------------------------------------
col_logo, col_info = st.columns([1, 10])
with col_logo:
    st.markdown("<div style='font-size: 40px; text-align: center;'>🏥</div>", unsafe_allow_html=True)
with col_info:
    st.markdown("<div class='main-title'>신한대학교 방사선학과 김호성 교수 | DXA_QC_HSK 중앙 관제 & 비밀번호 발급 센터</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>전국 병원 DXA 주간 정도관리(Shewhart Control Chart) 실시간 모니터링 & 정품 라이선스 원격 발급 시스템</div>", unsafe_allow_html=True)

db = load_db()
hospitals = db.get("hospitals", {})

# Calculate KPI stats
total_hospitals = len(hospitals)
total_devices = 0
action_required_count = 0
warning_count = 0
normal_count = 0

for h in hospitals.values():
    devs = h.get("devices", [])
    total_devices += len(devs)
    has_action = False
    has_warn = False
    for d in devs:
        status = d.get("latestScan", {}).get("status", "NORMAL")
        if status == "ACTION_REQUIRED":
            has_action = True
        elif status == "WARNING":
            has_warn = True
    if has_action:
        action_required_count += 1
    elif has_warn:
        warning_count += 1
    else:
        normal_count += 1

# KPI Row
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric("총 연동 병원 수", f"{total_hospitals} 개 기관")
with kpi2:
    st.metric("총 관리 DXA 장비", f"{total_devices} 대")
with kpi3:
    st.metric("정상 관리 기관 (ISCD 적합)", f"{normal_count} 곳", delta=f"{normal_count}/{total_hospitals}" if total_hospitals else None)
with kpi4:
    st.metric("점검/조치 요망 기관", f"{action_required_count} 곳", delta="-주의 요망" if action_required_count > 0 else "정상", delta_color="inverse")
with kpi5:
    compliance_rate = round(((total_hospitals - action_required_count) / total_hospitals) * 100) if total_hospitals else 100
    st.metric("주간 정도관리 적합률", f"{compliance_rate}%")

st.divider()

# -------------------------------------------------------------
# Main Navigation Tabs
# -------------------------------------------------------------
tab_keygen, tab_monitor, tab_guide = st.tabs([
    "🔑 병원별 정품 인증 비밀번호 발급기",
    "📈 전국 병원 DXA 정도관리 중앙 모니터링 (Shewhart)",
    "☁️ Streamlit Cloud 배포 & 병원 앱 연결 가이드"
])

# =============================================================
# TAB 1: Admin Keygen (Hospital Password Generator)
# =============================================================
with tab_keygen:
    st.subheader("🔑 병원별 DXA_QC_HSK 정품 인증 비밀번호 발급")
    st.caption("외부 스마트폰이나 어디서든 병원 담당자에게 받은 기기 코드로 6자리 인증 비밀번호를 즉시 생성합니다.")

    # Master password check in session state
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        with st.form("master_login_form"):
            st.info("🔐 관리자 마스터 비밀번호 인증이 필요합니다.")
            master_pass = st.text_input("마스터 비밀번호 입력 (예: hsk2026)", type="password")
            submit_auth = st.form_submit_button("관리자 인증")
            if submit_auth:
                if master_pass in ['hsk2026', 'shinhan2026', 'shinhan']:
                    st.session_state.admin_authenticated = True
                    st.success("관리자 인증이 완료되었습니다.")
                    st.rerun()
                else:
                    st.error("관리자 마스터 비밀번호가 올바르지 않습니다.")
    else:
        col_gen_left, col_gen_right = st.columns([3, 2])

        with col_gen_left:
            st.markdown("#### 1. 대상 병원 및 기기 정보 입력")
            
            # Allow choosing existing hospital or entering new
            existing_hosp_names = [h.get("name") for h in hospitals.values()]
            choose_existing = st.checkbox("기존 등록된 병원 목록에서 선택하기", value=False)
            
            if choose_existing and existing_hosp_names:
                selected_hosp = st.selectbox("등록 병원 선택", existing_hosp_names)
                hosp_input = selected_hosp
                # Pre-fill machineId if known
                target_mach = next((h.get("machineId") for h in hospitals.values() if h.get("name") == selected_hosp), "")
            else:
                hosp_input = st.text_input("병원명 입력", placeholder="예: 서울아산병원, 신한대병원")
                target_mach = ""

            mach_input = st.text_input(
                "병원 PC 기기 고유 식별 코드 (Machine ID)",
                value=target_mach,
                placeholder="예: HSK-8F2A-9C4B (담당자가 프로그램 첫 화면에서 복사한 코드)"
            )

            if st.button("✨ 6자리 정품 비밀번호 즉시 발급", type="primary", use_container_width=True):
                if not hosp_input.strip():
                    st.error("병원명을 입력해주세요.")
                elif not mach_input.strip():
                    st.error("기기 고유 코드(Machine ID)를 입력해주세요.")
                else:
                    gen_pin = generate_hospital_password(hosp_input, mach_input)
                    st.session_state.last_generated_pin = gen_pin
                    st.session_state.last_generated_hosp = hosp_input.strip()
                    st.session_state.last_generated_mach = mach_input.strip()

                    # Save to History
                    history = load_keygen_history()
                    history.insert(0, {
                        "hospital": hosp_input.strip(),
                        "machineId": mach_input.strip(),
                        "pin": gen_pin,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    save_keygen_history(history[:20])

        with col_gen_right:
            st.markdown("#### 2. 발급 결과 및 카카오톡 전송 템플릿")
            if "last_generated_pin" in st.session_state:
                pin = st.session_state.last_generated_pin
                hosp = st.session_state.last_generated_hosp
                mach = st.session_state.last_generated_mach

                st.success("✅ 정품 인증 비밀번호 생성 완료!")
                st.markdown(f"""
                <div style='background-color: #ecfdf5; border: 2px solid #10b981; border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 12px;'>
                    <div style='font-size: 13px; color: #047857; font-weight: bold;'>생성된 6자리 비밀번호 (Node-Lock 적용)</div>
                    <div style='font-size: 34px; font-weight: 900; letter-spacing: 6px; color: #065f46; font-family: monospace; margin: 8px 0;'>
                        {pin}
                    </div>
                    <div style='font-size: 11px; color: #059669;'>등록 병원: {hosp} | 기기: {mach}</div>
                </div>
                """, unsafe_allow_html=True)

                kakao_template = f"""[DXA_QC_HSK 정품 인증 비밀번호 발급 안내]
- 발급 기관: 신한대학교 방사선학과 김호성 교수
- 등록 병원: {hosp}
- 기기 코드: {mach}
- 인증 비밀번호: {pin}

* 안내사항:
본 프로그램은 단일 컴퓨터 한정(Node-Lock)이 적용되어 있어 해당 기기에서만 유효하며, 다른 컴퓨터로 복제 시 실행이 차단됩니다. 프로그램을 실행하여 상기 병원명과 비밀번호를 입력해주시기 바랍니다."""

                st.text_area("카카오톡/문자 발송용 안내 양식 (우측 상단 복사 아이콘 클릭)", value=kakao_template, height=180)
            else:
                st.info("좌측에서 병원명과 기기 코드를 입력하고 발급 버튼을 누르면 여기에 즉시 생성됩니다.")

        st.markdown("---")
        st.markdown("#### 📋 최근 비밀번호 발급 이력")
        hist = load_keygen_history()
        if hist:
            df_hist = pd.DataFrame(hist)
            df_hist.columns = ["병원명", "기기 코드 (Machine ID)", "발급 비밀번호", "발급 일시"]
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.caption("아직 발급 이력이 없습니다.")

# =============================================================
# TAB 2: Shewhart Central Monitoring Dashboard
# =============================================================
with tab_monitor:
    st.subheader("📈 전국 병원 DXA 주간 정도관리 중앙 모니터링")
    st.caption("각 병원에서 실시간 또는 주간으로 전송된 팬텀 스캔 데이터와 Shewhart 관리도를 확인하고 원격 지도 소견을 등록합니다.")

    if not hospitals:
        st.warning("현재 등록된 병원 데이터가 없습니다. 병원 앱에서 동기화를 수행하거나 아래 데모 데이터를 확인하세요.")
    else:
        # Hospital Selector
        hosp_options = {h["id"]: f"{h['name']} ({len(h.get('devices', []))}대 장비)" for h in hospitals.values()}
        selected_hosp_id = st.selectbox("관제 대상 병원 선택", list(hosp_options.keys()), format_func=lambda x: hosp_options[x])

        hosp_data = hospitals[selected_hosp_id]
        devices = hosp_data.get("devices", [])

        st.markdown(f"**병원명**: `{hosp_data.get('name')}` | **기기 코드**: `{hosp_data.get('machineId')}` | **최근 동기화**: `{hosp_data.get('lastSync', '-')[:19]}`")

        if not devices:
            st.info("등록된 DXA 측정 장비가 없습니다.")
        else:
            dev_names = [f"{d['name']} ({d.get('department', '영상의학과')})" for d in devices]
            dev_idx = st.radio("장비 선택", range(len(dev_names)), format_func=lambda i: dev_names[i], horizontal=True)
            cur_dev = devices[dev_idx]

            mean_val = cur_dev.get("baselineMean", 1.020)
            sd_val = cur_dev.get("baselineSd", 0.007)
            history = cur_dev.get("history", [])

            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("제조사", cur_dev.get("manufacturer", "GE Lunar"))
            with m2:
                st.metric("팬텀 일련번호", cur_dev.get("phantomSerial", "-"))
            with m3:
                st.metric("기준 평균값 (Mean)", f"{mean_val:.4f} g/cm²")
            with m4:
                ucl = mean_val * 1.015
                lcl = mean_val * 0.985
                st.metric("ISCD ±1.5% 한계선", f"{lcl:.4f} ~ {ucl:.4f}")

            # Plotly Interactive Shewhart Chart
            if history:
                df_hist = pd.DataFrame(history)
                dates = df_hist["scanDate"].tolist()
                bmds = df_hist["bmd"].tolist()
                statuses = df_hist.get("status", ["NORMAL"] * len(bmds)).tolist()

                fig = go.Figure()

                # Mean Line
                fig.add_trace(go.Scatter(
                    x=dates, y=[mean_val] * len(dates),
                    mode='lines', name='평균선 (Mean)',
                    line=dict(color='#10b981', width=2, dash='dash')
                ))

                # UCL / LCL Lines (+-1.5%)
                fig.add_trace(go.Scatter(
                    x=dates, y=[ucl] * len(dates),
                    mode='lines', name='UCL (+1.5% 허용한계)',
                    line=dict(color='#ef4444', width=1.5, dash='dot')
                ))
                fig.add_trace(go.Scatter(
                    x=dates, y=[lcl] * len(dates),
                    mode='lines', name='LCL (-1.5% 허용한계)',
                    line=dict(color='#ef4444', width=1.5, dash='dot')
                ))

                # 3SD Lines
                fig.add_trace(go.Scatter(
                    x=dates, y=[mean_val + 3 * sd_val] * len(dates),
                    mode='lines', name='3SD 상한',
                    line=dict(color='#94a3b8', width=1, dash='dashdot')
                ))
                fig.add_trace(go.Scatter(
                    x=dates, y=[mean_val - 3 * sd_val] * len(dates),
                    mode='lines', name='3SD 하한',
                    line=dict(color='#94a3b8', width=1, dash='dashdot')
                ))

                # BMD Data Points
                point_colors = ['#ef4444' if s == 'ACTION_REQUIRED' else ('#f59e0b' if s == 'WARNING' else '#2563eb') for s in statuses]
                point_symbols = ['diamond' if s == 'ACTION_REQUIRED' else 'circle' for s in statuses]

                fig.add_trace(go.Scatter(
                    x=dates, y=bmds,
                    mode='lines+markers', name='측정 BMD (g/cm²)',
                    line=dict(color='#2563eb', width=2),
                    marker=dict(size=9, color=point_colors, symbol=point_symbols),
                    hovertemplate='<b>날짜</b>: %{x}<br><b>BMD</b>: %{y:.4f} g/cm²<extra></extra>'
                ))

                fig.update_layout(
                    title=f"<b>{cur_dev['name']} Shewhart 정도관리 차트 (ISCD 기준)</b>",
                    xaxis_title="스캔 측정일",
                    yaxis_title="골밀도 BMD (g/cm²)",
                    template="plotly_white",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=420,
                    margin=dict(l=40, r=40, t=60, b=40)
                )

                st.plotly_chart(fig, use_container_width=True)

                # Show Scan Table
                with st.expander("📊 세부 스캔 측정 이력 데이터 테이블 확인"):
                    st.dataframe(df_hist, use_container_width=True)
            else:
                st.info("해당 장비에 등록된 스캔 이력이 아직 없습니다.")

            # Professor Feedback & Action Advice
            st.markdown("---")
            st.markdown("#### 💬 김호성 교수 원격 기술 지도 소견 작성")
            col_fb_in, col_fb_list = st.columns([1, 1])

            with col_fb_in:
                new_fb_msg = st.text_area("해당 병원 담당자에게 전달할 판독 소견 및 점검 권고사항", placeholder="예: 주간 관리도 추이가 기준치 대비 안정적입니다. 다음 주 정기 팬텀 스캔을 권고합니다.")
                if st.button("📨 기술 지도 소견 병원 앱으로 전송", type="primary"):
                    if not new_fb_msg.strip():
                        st.error("소견 내용을 입력해주세요.")
                    else:
                        feedbacks = hosp_data.get("feedbacks", [])
                        feedbacks.insert(0, {
                            "id": f"fb-{int(datetime.now().timestamp()*1000)}",
                            "author": "신한대학교 방사선학과 김호성 교수",
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "timestamp": datetime.now().isoformat(),
                            "message": new_fb_msg.strip()
                        })
                        hosp_data["feedbacks"] = feedbacks
                        hospitals[selected_hosp_id] = hosp_data
                        save_db(db)
                        st.success("지도 소견이 저장되었습니다! 병원 앱에 실시간 반영됩니다.")
                        st.rerun()

            with col_fb_list:
                st.markdown("**기존 발송 소견 목록**")
                fb_list = hosp_data.get("feedbacks", [])
                if fb_list:
                    for fb in fb_list:
                        st.markdown(f"""
                        <div style='background-color: #f8fafc; border-left: 4px solid #6366f1; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;'>
                            <div style='font-size: 11px; color: #64748b;'>{fb.get('author')} • {fb.get('date')}</div>
                            <div style='font-size: 13px; color: #1e293b; font-weight: 500; margin-top: 4px;'>{fb.get('message')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("작성된 소견 이력이 없습니다.")

# =============================================================
# TAB 3: Cloud Deployment & Hospital App Connection Guide
# =============================================================
with tab_guide:
    st.subheader("☁️ Streamlit Community Cloud 배포 및 병원 앱 연동 방법")
    st.markdown("""
    김호성 교수님께서 복잡한 공유기 포트포워딩이나 로컬 네트워크 연결 없이,
    **Streamlit Community Cloud(무료)**를 이용하여 전 세계 어디서나 접속 가능한 관제센터를 운영하시는 가이드입니다.

    ---
    ### 1단계: GitHub에 본 프로젝트 코드 올리기
    1. 본 프로젝트 폴더(`DXA`)를 GitHub 저장소(예: `DXA_QC_HSK_Center`)에 푸시합니다.
    2. 저장소 루트에 `requirements.txt`와 `streamlit_app.py`가 포함되어 있습니다.

    ---
    ### 2단계: Streamlit Cloud에서 1분 만에 배포하기
    1. 웹 브라우저에서 [share.streamlit.io](https://share.streamlit.io)에 접속하여 로그인합니다.
    2. **[New app]** 클릭 -> GitHub 저장소(`DXA_QC_HSK_Center`) 선택
    3. Main file path: `streamlit_app.py` 입력 후 **[Deploy]** 클릭!
    4. 즉시 고유한 공개 URL이 생성됩니다 (예: `https://dxa-qc-kim.streamlit.app`).

    ---
    ### 3단계: 병원 클라이언트 앱(`DXA_QC_HSK`) 연결
    1. 각 병원 담당자에게 배포된 `DXA_QC_HSK_Portable.exe`를 실행합니다.
    2. 우측 상단 **[설정(⚙️)]** -> **[중앙 관제센터 & 저장소]** 탭 선택
    3. **[중앙 온라인 원격 관제센터 연동]** 스위치를 **ON**으로 켭니다.
    4. 위에서 생성된 Streamlit 또는 관제 서버 주소(예: `https://dxa-qc-kim.streamlit.app`)를 입력하고 [설정 저장]을 누르면 연동이 완료됩니다!
    """)

# -------------------------------------------------------------
# Footer
# -------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 12px; color: #94a3b8;'>"
    "신한대학교 방사선학과 김호성 교수 | DXA_QC_HSK 주간 정도관리 & Shewhart 관리도 중앙 관제 플랫폼<br>"
    "ISCD (International Society for Clinical Densitometry) Quality Control Standards"
    "</div>",
    unsafe_allow_html=True
)
