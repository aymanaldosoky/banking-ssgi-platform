import io
import os
import json
import re
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# استيراد محرك الإجابات المستقل المطور وتوابعه البرمجية
from bank_rag_engine import process_rag_gemini_query, audit_differentiation

# ==============================================================================
# إعدادات صفحة Streamlit وتطبيق الهوية البصرية المصرفية (RTL)
# ==============================================================================
st.set_page_config(
    page_title="مقترح المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CBE_NAVY = "#002B49"         # أزرق مصرفي عميق
CBE_GOLD = "#C5A059"         # ذهبي ملكي
CBE_GOLD_LIGHT = "#E2C07D"   # ذهبي فاتح
CBE_BG = "#F8F9FA"           # خلفية ناعمة

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

header {{
    visibility: hidden !important;
    display: none !important;
}}

.stAppToolbar, div[data-testid="stHeader"] {{
    display: none !important;
    visibility: hidden !important;
}}

html, body, [class*="css"] {{
    font-family: 'Cairo', sans-serif !important;
    direction: rtl !important;
    text-align: right !important;
    background-color: {CBE_BG} !important;
}}

.stApp {{
    background-color: {CBE_BG} !important;
    direction: rtl !important;
    text-align: right !important;
}}

div.stMarkdown, div.stText, div.stSelectbox, div.stSlider, div.stDataFrame, div.stTable {{
    direction: rtl !important;
    text-align: right !important;
}}

div[data-baseweb="select"] *, 
div[data-baseweb="popover"] *, 
ul[data-baseweb="menu"] *, 
div[role="listbox"] *,
div[role="option"] {{
    direction: rtl !important;
    text-align: right !important;
}}

/* تصميم جدول RTL مخصص ومصغر ومريح بصرياً */
.custom-rtl-table {{
    width: 100% !important;
    border-collapse: collapse !important;
    direction: rtl !important;
    text-align: right !important;
    margin-top: 8px !important;
    margin-bottom: 12px !important;
    font-family: 'Cairo', sans-serif !important;
    background-color: #FFFFFF !important;
    border-radius: 6px !important;
    overflow: hidden !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    border: 1px solid #CBD5E1 !important;
}}

.custom-rtl-table th {{
    background: linear-gradient(135deg, {CBE_NAVY} 100%, #001A33 100%) !important;
    color: #F8FAFC !important;
    padding: 9px 8px !important;
    font-weight: 700 !important;
    border: 1px solid #475569 !important;
    text-align: right !important;
    font-size: 12.5px !important;
    white-space: nowrap !important;
}}

.custom-rtl-table td {{
    padding: 7px 8px !important;
    border: 1px solid #E2E8F0 !important;
    color: #1E293B !important;
    font-size: 12px !important;
    text-align: right !important;
    line-height: 1.4 !important;
}}

.custom-rtl-table tr:nth-child(even) {{
    background-color: #F8FAFC !important;
}}

.custom-rtl-table tr:hover {{
    background-color: #FEF3C7 !important;
}}

div.stButton > button {{
    width: 100% !important;
    border-radius: 50px !important;
    font-family: 'Cairo', sans-serif !important;
    font-weight: 700 !important;
}}

div.stTabs {{
    width: 100% !important;
    max-width: 100% !important;
    direction: rtl !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    display: flex !important;
    flex-direction: row-reverse !important;
    width: 100% !important;
    max-width: 100% !important;
    gap: 6px !important;
    background: linear-gradient(135deg, {CBE_NAVY} 0%, #001A33 100%) !important;
    padding: 10px !important;
    border-radius: 12px !important;
    border: 2px solid {CBE_GOLD} !important;
    box-shadow: 0 8px 25px rgba(0,0,0,0.25) !important;
    direction: rtl !important;
    box-sizing: border-box !important;
}}

.stTabs [data-baseweb="tab"] {{
    flex: 1 1 0% !important;
    width: 100% !important;
    max-width: none !important;
    background-color: rgba(0, 43, 73, 0.85) !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    padding: 10px 4px !important;
    font-weight: 700 !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: 12px !important;
    border: 1px solid rgba(197, 160, 89, 0.3) !important;
    text-align: center !important;
    justify-content: center !important;
    align-items: center !important;
    transition: all 0.3s ease !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
    background-color: {CBE_GOLD} !important;
    color: {CBE_NAVY} !important;
    border-color: #FFFFFF !important;
}}

.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {CBE_GOLD} 0%, #A38243 100%) !important;
    color: {CBE_NAVY} !important;
    border: 2px solid #FFFFFF !important;
    font-weight: 800 !important;
    box-shadow: 0 4px 15px rgba(197, 160, 89, 0.4) !important;
}}

.header-center {{
    text-align: center !important;
    background: linear-gradient(135deg, rgba(0, 43, 73, 0.95) 0%, rgba(0, 26, 51, 0.90) 100%),
                url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1600&auto=format&fit=crop') !important;
    background-size: cover !important;
    background-position: center !important;
    color: #FFFFFF !important;
    padding: 35px 20px !important;
    border-radius: 16px !important;
    border-bottom: 5px solid {CBE_GOLD} !important;
    box-shadow: 0 12px 35px rgba(0,0,0,0.35) !important;
    margin-bottom: 20px !important;
    direction: rtl !important;
}}

.header-center h1 {{
    color: {CBE_GOLD} !important;
    font-size: 24px !important;
    font-weight: 800 !important;
    margin-bottom: 10px !important;
    text-shadow: 0 2px 6px rgba(0,0,0,0.7) !important;
}}

.header-center h3 {{
    color: #F1F5F9 !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    line-height: 1.6 !important;
    margin-bottom: 6px !important;
}}

.ticker-wrap {{
    width: 100%;
    background: linear-gradient(90deg, {CBE_NAVY} 0%, #001F35 100%);
    border-top: 2px solid {CBE_GOLD};
    border-bottom: 2px solid {CBE_GOLD};
    overflow: hidden;
    white-space: nowrap;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    margin-bottom: 25px;
    border-radius: 8px;
    direction: ltr !important;
}}

.ticker {{
    display: inline-block;
    padding-right: 100%;
    animation: marquee-infinite 55s linear infinite;
}}

.ticker-item {{
    display: inline-block;
    padding: 8px 30px;
    font-size: 14px;
    font-weight: bold;
    color: #FFFFFF !important;
    direction: rtl !important;
}}

@keyframes marquee-infinite {{
    0% {{ transform: translate(-100%, 0); }}
    100% {{ transform: translate(100%, 0); }}
}}

.footer-copyright {{
    text-align: center;
    color: #64748B;
    font-size: 13px;
    margin-top: 40px;
    border-top: 1px solid #E2E8F0;
    padding-top: 15px;
    font-weight: bold;
    direction: rtl !important;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# نظام تتبع الزوار (IP Logging ودعم ملفات السيرفر)
# ==============================================================================
LOG_FILE = "visitors_log.csv"

def init_visitor_log_file():
    if not os.path.exists(LOG_FILE):
        try:
            df_init = pd.DataFrame(columns=["عنوان IP", "اسم المستخدم", "الدور", "وقت الدخول"])
            df_init.to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
        except Exception:
            pass

init_visitor_log_file()

def load_visitors_log_from_file():
    if os.path.exists(LOG_FILE):
        try:
            df = pd.read_csv(LOG_FILE, encoding='utf-8-sig')
            return df.to_dict(orient="records")
        except Exception:
            return []
    return []

def get_visitor_ip():
    try:
        ctx = st.runtime.scriptrunner.get_script_run_ctx()
        if ctx and hasattr(ctx, "session_id"):
            from streamlit.web.server.websocket_headers import _get_websocket_headers
            headers = _get_websocket_headers()
            if headers:
                ip = headers.get("X-Forwarded-For") or headers.get("X-Real-Ip") or headers.get("Remote-Addr")
                if ip:
                    return ip.split(",")[0].strip()
    except Exception:
        pass
    return "127.0.0.1 (محلي / Local)"

def log_visitor_action(username, role):
    try:
        client_ip = get_visitor_ip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_record = {
            "عنوان IP": client_ip,
            "اسم المستخدم": username,
            "الدور": role,
            "وقت الدخول": timestamp
        }
        existing_logs = load_visitors_log_from_file()
        exists = any(
            item.get("عنوان IP") == client_ip and item.get("اسم المستخدم") == username
            for item in existing_logs
        )
        if not exists:
            existing_logs.append(new_record)
            df_out = pd.DataFrame(existing_logs)
            df_out.to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
    except Exception:
        pass

# ==============================================================================
# إدارة جلسة الدخول والصلاحيات
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        login_container = st.container()
        with login_container:
            st.markdown(f"""
            <div style="background: #FFFFFF; padding: 30px; border-radius: 16px; border: 2px solid {CBE_GOLD}; box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: right;" dir="rtl">
                <h2 style="color: {CBE_NAVY}; text-align: center; font-weight: 800; margin-bottom: 10px;">🏛️ المنصة الوطنية الذكية لحوكمة القطاع المصرفي</h2>
                <p style="color: #475569; text-align: center; font-size: 14px; line-height: 1.6; margin-bottom: 25px;">
                    إطار تطبيقي مقترح لبرنامج دكتوراه الفلسفة في العلوم البيئية - جامعة عين شمس. يرجى تسجيل الدخول للمتابعة.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            username_input = st.text_input("اسم المستخدم (Username)", placeholder="أدخل اسم المستخدم...")
            password_input = st.text_input("كلمة المرور (Password)", type="password", placeholder="أدخل كلمة المرور...")
            
            if st.button("🔐 تسجيل الدخول للمنصة", use_container_width=True):
                if username_input == "admin" and password_input == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.username = "مشرف النظام (Admin)"
                    st.session_state.role = "admin"
                    log_visitor_action("admin", "مشرف (Admin)")
                    st.rerun()
                elif username_input == "user" and password_input == "123":
                    st.session_state.authenticated = True
                    st.session_state.username = "باحث / مستخدم (User)"
                    st.session_state.role = "user"
                    log_visitor_action("user", "مستخدم عادي (User)")
                    st.rerun()
                else:
                    st.error("⚠️ اسم المستخدم أو كلمة المرور خاطئة.")
    st.stop()

# ==============================================================================
# قائمة البنوك المصرية الشاملة
# ==============================================================================
BANKS_LIST_AR = [
    "اختر البنك المصرفي",
    "بنك مصر BM",
    "البنك الأهلي المصري NBE",
    "البنك التجاري الدولي CIB",
    "بنك قطر الوطني الأهلي QNB",
    "بنك كريدي أجريكول",
    "بنك الإسكندرية",
    "بنك التعمير والإسكان HDB",
    "بنك قناة السويس SCBANK",
    "بنك أبوظبي الأول مصر FABMISR",
    "بنك فيصل الإسلامي",
    "بنك البركة الإسلامي",
    "بنك القاهرة Banque du Caire",
    "مصرف أبو ظبي الإسلامي ADIB",
    "بنك NEXT",
    "بنك الإمارات دبي الوطني NDB",
    "بنك HSBC",
    "التجاري وفا بنك",
    "بنك المؤسسة العربية المصرفية ABC",
    "المصرف العربي الدولي AIB",
    "البنك الزراعي المصري",
    "ستاندرد تشارترد – مصر",
    "البنك العقاري المصري العربي EALB",
    "بنك الكويت الوطني NBK",
    "بنك المصري الخليجي EG BANK",
    "المصرف المتحد UN",
    "ميد بنك MIDBANK",
    "بنك التنمية الصناعية IDB",
    "بنك المشرق",
    "بنك بيت التمويل الكويتي KFH",
    "بنك الأهلي الكويتي مصر ABK",
    "بنك تنمية الصادرات EBANK",
    "بنك سيب SAIB",
    "البنك العربي",
    "البنك العربي الأفريقي",
    "بنك أبوظبي التجاري ADCB",
    "بنك ناصر الاجتماعي",
    "بنك الاستثمار القومي",
    "بنك الأهلي المتحد KFH",
    "بنوك بلوم BLOM",
    "البنك الأهلي اليوناني",
    "بنك سيتي بنك CITIBANK"
]

def get_colored_score_html(score):
    if score >= 80:
        return f"{score}% (أداء مرتفع ومنتظم 🟢)"
    elif score >= 51:
        return f"{score}% (أداء متوسط يتطلب تعزيزاً 🟡)"
    else:
        return f"{score}% (فجوة هيكلية حرجة تستوجب التدخل 🔴)"

def describe_sip(val):
    if val >= 80:
        return f"منصات المعلومات والبنية التقنية متقدمة للغاية ({val}%) وتتيح تكاملاً تاماً مع أنظمة البنك المركزي والتقارير الرقابية الآلية."
    elif val >= 50:
        return f"البنية التقنية متوسطة الكفاءة ({val}%) وتحتاج لتحديث سعات تدفق البيانات وحوكمة الخوارزميات."
    else:
        return f"تعاني البنية التقنية من فجوة هيكلية حرجة ({val}%) تعيق أتمتة الالتزام والرقابة التنظيمية."

def describe_ig(val):
    if val >= 80:
        return f"حوكمة مؤسسية راسخة ({val}%) مع استقلالية تامة لمجلس الإدارة ولجان المراجعة والالتزام بأعلى معايير الشفافية."
    elif val >= 50:
        return f"الحوكمة المؤسسية في نطاق متوازن ({val}%) وتتطلب تفعيل ضوابط تعارض المصالح وتعزيز دور الأعضاء المستقلين."
    else:
        return f"قصور حاد في الحوكمة المؤسسية ({val}%) يستوجب تدخلاً رقابياً لإعادة هندسة لجان المراجعة وإدارة المخاطر."

def describe_sr(val):
    if val >= 80:
        return f"التزام متميز بتقارير الاستدامة والتمويل الأخضر ({val}%) مع حصة معتبرة للأصول الخضراء ومواءمة معايير (GRI/ISSB)."
    elif val >= 50:
        return f"أداء متوسط في تقارير الاستدامة ({val}%) يستوجب التوسع في محفظة التمويل المستدام ومخاطر المناخ."
    else:
        return f"ضعف هيكلي في ملف الاستدامة والتمويل الأخضر ({val}%) يعيق امتثال البنك للمعايير الدولية."

if "history_state" not in st.session_state:
    st.session_state.history_state = []
if "simulated_results_dict" not in st.session_state:
    st.session_state.simulated_results_dict = {}
if "decision_results_dict" not in st.session_state:
    st.session_state.decision_results_dict = {}
if "query_text_box" not in st.session_state:
    st.session_state.query_text_box = ""

# ==============================================================================
# الهيدر والشريط الإخباري
# ==============================================================================
col_h1, col_h2 = st.columns([4, 1])
with col_h2:
    st.markdown(f"<div style='text-align: left; font-size: 13px; color: #475569; padding-top: 10px;'>👤 مسجل باسم: <b>{st.session_state.username}</b></div>", unsafe_allow_html=True)
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

st.markdown(f"""
<div class="header-center">
<h1>مقترح المنصة الوطنية الذكية لتعزيز الحوكمة وتقارير الاستدامة بالقطاع المصرفي المصري</h1>
<h3>إطار تطبيقي مقترح ضمن متطلبات نيل درجة دكتوراة الفلسفة في العلوم البيئية - جامعة عين شمس</h3>
<b>إعداد الباحث: أيمن الدسوقي، معهد التخطيط القومي</b>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <span class="ticker-item">🏛️ مقترح المنصة الوطنية الذكية لتعزيز الحوكمة وتقارير الاستدامة بالقطاع المصرفي المصري</span>
    <span class="ticker-item">| 📊 مؤشر الحوكمة الذكية المستدامة (SSGI) والأبعاد الثلاثة الرئيسية</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي لاختبار السيناريوهات الاستراتيجية (Multiple Regression)</span>
    <span class="ticker-item">| 🛡️ لوحة دعم اتخاذ القرار وتوطين المعايير الرقابية وإطار دونيلا ميدوز لنقاط الرفع</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# التبويبات الرئيسية (متوافقة تماماً مع هيكل كود الصناعات)
# ==============================================================================
if st.session_state.role == "admin":
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🎯 اسأل المنصة",
        "📊 مؤشر الحوكمة المركب (SSGI)", 
        "📈 محاكي السياسات (Policy Simulator)", 
        "🛡️ لوحة دعم اتخاذ القرار", 
        "📑 التقرير التنفيذي الموحد",
        "🌿 مولد تقارير الاستدامة (GRI/ISSB)",
        "🔒 لوحة تحكم المشرف والزوار (Admin)"
    ])
else:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎯 اسأل المنصة",
        "📊 مؤشر الحوكمة (SSGI)", 
        "📈 محاكي السياسات (Policy Simulator)", 
        "🛡️ لوحة دعم اتخاذ القرار", 
        "📑 التقرير التنفيذي الموحد",
        "🌿 مولد تقارير الاستدامة (GRI/ISSB)"
    ])
    tab7 = None

# ------------------------------------------------------------------------------
# التبويب الأول: اسأل المنصة
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🎯 تحليل واستخلاص البيانات </h3>
        <p>استعراض الإجابات المستندة إلى تقارير الاستدامة والحوكمة في القطاع المصرفي المصري لكل بنك على حدة.</p>
    </div>
    """, unsafe_allow_html=True)

    col_q1, col_q2 = st.columns([1, 2], gap="large")

    with col_q1:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        ask_bank_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, key="ask_bank")
        
        user_question = st.text_area(
            "❓ اكتب سؤالك/ استفسارك:",
            placeholder="مثال: متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟",
            height=120,
            key="query_text_box"
        )

        st.markdown("<b>📌 أسئلة/ استفسارات مقترحة حسب المحاور:</b>", unsafe_allow_html=True)

        def set_suggested_question(question):
            st.session_state.query_text_box = question

        with st.expander("🏛️ محور الحوكمة والتأسيس والتاريخ (IG & History)"):
            ig_questions = [
                "متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟",
                "عرف الحوكمة وتكوين مجلس الإدارة بالبنك",
                "ما هي نسبة الأعضاء المستقلين وسياسات تجنب تعارض المصالح؟",
                "كيف يفصح البنك عن سياسات الشفافية والمساءلة ومكافحة الفساد؟",
                "كيف يضمن البنك الالتزام التام بالقوانين واللوائح الصادرة عن البنك المركزي المصري؟"
            ]
            for i, q in enumerate(ig_questions):
                st.button(q, key=f"btn_ig_{i}", on_click=set_suggested_question, args=(q,), use_container_width=True)

        with st.expander("🌱 محور تقارير الاستدامة والتمويل الأخضر والمناخ (SR/ESG)"):
            sr_questions = [
                "ما هي جهود البنك في تمكين المرأة والشمول المالي؟",
                "كيف يتعامل البنك مع مخاطر المناخ والتمويل الأخضر؟",
                "ما هي نسبة الأصول الخضراء والمشروعات المستدامه ضمن محفظة الائتمان؟",
                "كيف يمتثل البنك للمعايير الدولية للإفصاح المالي (GRI و ISSB)؟",
                "ما هي مبادرات البنك في المسؤولية المجتمعية والإنفاق التنموي المستدام؟"
            ]
            for i, q in enumerate(sr_questions):
                st.button(q, key=f"btn_sr_{i}", on_click=set_suggested_question, args=(q,), use_container_width=True)

        with st.expander("🔒 محور المنصات الذكية وحوكمة البيانات والامتثال (SIP/RegTech)"):
            sip_questions = [
                "ما هي آليات حوكمة البيانات والامتثال الرقابي وتأمينها؟",
                "كيف يضمن البنك الحصانة السيبرانية ومنع تسريب البيانات المالية الحساسة؟",
                "ما هي جاهزية البنية التحتية الرقمية ومنصات المعلومات (SIP)؟",
                "كيف يوظف البنك تقنيات الرقابة التنظيمية (RegTech) واسترجاع المعطيات؟",
                "ما مدى التوافق مع قانون حماية البيانات الشخصية والسيادة الرقمية؟"
            ]
            for i, q in enumerate(sip_questions):
                st.button(q, key=f"btn_sip_{i}", on_click=set_suggested_question, args=(q,), use_container_width=True)

        ask_submit_btn = st.button("تقديم السؤال/ الاستفسار", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_q2:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if ask_submit_btn:
            active_q = st.session_state.query_text_box
            if ask_bank_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي صحيح من القائمة لتنفيذ الاستعلام.")
            elif not active_q.strip():
                st.warning("⚠️ يرجى كتابة أو اختيار سؤال للإجابة عليه.")
            else:
                with st.spinner("⏳ جاري استرجاع المستندات عبر المحرك المستقل وتحليل الإجابة المخصصة للبنك..."):
                    response_html = process_rag_gemini_query(ask_bank_sel, active_q)
                    st.markdown(response_html, unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح أو كتابة السؤال/ الاستفسار.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الثاني: مؤشر الحوكمة الذكية المستدامة (SSGI)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown(f"""
    <div dir="rtl" style="text-align: right;">
        <h3>🗳️ التشخيص القياسي واحتساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
        <p>إمكانية تشخيص البنوك المختارة عبر المحاور الثلاثة الرئيسية مع تسجيل وثبات النتائج في الجدول التراكمي وتعديل الاتجاهات والترتيب.</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        bank_ssgi_sel = st.selectbox("اختر البنك المصرفي المراد قياسه", BANKS_LIST_AR, key="t1_bank")
        
        sip_val = st.slider("1. محور منصات المعلومات والبنية الرقمية (SIP - 40%)", 0, 100, 88, key="t1_sip")
        ig_val = st.slider("2. محور الحوكمة المؤسسية والامتثال (IG - 30%)", 0, 100, 90, key="t1_ig")
        sr_val = st.slider("3. محور تقارير الاستدامة ومخاطر المناخ (SR - 30%)", 0, 100, 82, key="t1_sr")

        calc_ssgi_btn = st.button("🚀 احسب وسجل مؤشر البنك", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if calc_ssgi_btn:
            if bank_ssgi_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي حقيقي من القائمة لتنفيذ التشخيص القياسي.")
            else:
                final_score = round((sip_val * 0.40) + (ig_val * 0.30) + (sr_val * 0.30), 2)
                score_str_plain = get_colored_score_html(final_score)

                if final_score >= 80:
                    diagnosis = "🟢 أداء مصرفي مرتفع ومنتظم، نحو الريادة والسيادة الرقمية المستدامة."
                    detailed_diag = f"🟢 **جاهزية متقدمة ومستدامة:** القيمة المركبة للمؤشر (SSGI): {score_str_plain}. تعكس هذه النتيجة تفوقاً هيكلياً في حوكمة البنك وبنيته التقنية واستدامته."
                elif final_score >= 51:
                    diagnosis = "🟡 أداء متوسط، يتطلب تعزيزاً استباقياً لمعالجة الفجوات الهيكلية."
                    detailed_diag = f"🟡 **جاهزية متوسطة تتطلب تدخلاً استباقياً:** القيمة المركبة للمؤشر (SSGI): {score_str_plain}."
                else:
                    diagnosis = "🔴 فجوة هيكلية حرجة تستوجب التدخل الفوري وتفعيل محاكي السياسات."
                    detailed_diag = f"🔴 **فجوة هيكلية حرجة:** القيمة المركبة للمؤشر (SSGI): {score_str_plain}."

                entry = {
                    "البنك": bank_ssgi_sel,
                    "مؤشر SSGI المركب": final_score,
                    "منصات المعلومات (40%)": round(sip_val, 2),
                    "الحوكمة المؤسسية (30%)": round(ig_val, 2),
                    "تقارير الاستدامة (30%)": round(sr_val, 2),
                    "التقييم التشخيصي": diagnosis
                }

                updated = False
                for idx, item in enumerate(st.session_state.history_state):
                    if item["البنك"] == bank_ssgi_sel:
                        st.session_state.history_state[idx] = entry
                        updated = True
                        break
                if not updated:
                    st.session_state.history_state.append(entry)

                st.markdown(f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                  <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 12px;">📊 نتيجة حساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
                  <p style="font-size: 15px; margin-bottom: 8px;"><b>البنك الخاضع للتقييم:</b> <span style="color: {CBE_NAVY}; font-weight: bold;">{bank_ssgi_sel}</span></p>
                  <p style="font-size: 16px; margin-bottom: 12px;"><b>القيمة المركبة للمؤشر (SSGI):</b> <span style="font-size: 18px;">{score_str_plain}</span></p>
                  <div style="background: {CBE_BG}; padding: 16px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 10px;">
                    <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY};">التقييم التشخيصي والتفصيل المنظومي:</p>
                    <p style="margin: 0; color: #1E293B; font-size: 14.5px;">{detailed_diag}</p>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                categories = ['منصات المعلومات (SIP)', 'الحوكمة المؤسسية (IG)', 'تقارير الاستدامة (SR)']
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=[sip_val, ig_val, sr_val],
                    theta=categories,
                    fill='toself',
                    name=bank_ssgi_sel,
                    line_color=CBE_GOLD
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=True,
                    title=f"التحليل الرداري لمحاور الحوكمة الذكية المستدامة - {bank_ssgi_sel}",
                    font=dict(family="Cairo", size=12)
                )
                st.plotly_chart(fig_radar, use_container_width=True)

        else:
            st.info("📊 يرجى اختيار البنك وضبط درجات المحاور الثلاثة ثم الضغط على زر الحساب لعرض النتائج والتحليل الرداري.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 قائمة ترتيب البنوك المسجلة (الجدول التراكمي المطور)")
    if st.session_state.history_state:
        df_history = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)
        
        table_html = """
        <div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 320px;">
        <table class="custom-rtl-table">
        <thead>
        <tr>
        <th style="width: 35px; text-align: center;">م</th>
        <th>اسم البنك</th>
        <th>المؤشر المركب (SSGI)</th>
        <th>منصات المعلومات (40%)</th>
        <th>الحوكمة المؤسسية (30%)</th>
        <th>تقارير الاستدامة (30%)</th>
        <th>التقييم التشخيصي</th>
        </tr>
        </thead>
        <tbody>
        """
        
        for idx, row in df_history.iterrows():
            table_html += f"""
            <tr>
            <td style="text-align: center; font-weight: bold;">{idx + 1}</td>
            <td style="font-weight: bold; color: {CBE_NAVY};">{row['البنك']}</td>
            <td style="font-weight: bold; color: {CBE_GOLD};">{row['مؤشر SSGI المركب']}%</td>
            <td>{row['منصات المعلومات (40%)']}%</td>
            <td>{row['الحوكمة المؤسسية (30%)']}%</td>
            <td>{row['تقارير الاستدامة (30%)']}%</td>
            <td style="font-size: 11.5px;">{row['التقييم التشخيصي']}</td>
            </tr>
            """
        table_html += """
        </tbody>
        </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)

        csv_data = df_history.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تحميل جدول ترتيب البنوك المسجلة (Excel/CSV)",
            data=csv_data,
            file_name="ترتيب_البنوك_المصرية_SSGI.csv",
            mime="text/csv",
            use_container_width=True
        )

        col_del1, col_del2 = st.columns([2, 1])
        with col_del1:
            recorded_banks = [item["البنك"] for item in st.session_state.history_state]
            bank_to_delete = st.selectbox("اختر بنكاً من السجل لحذفه", recorded_banks, key="del_bank_box")
        with col_del2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ حذف البنك المحدد", use_container_width=True, type="secondary"):
                st.session_state.history_state = [item for item in st.session_state.history_state if item["البنك"] != bank_to_delete]
                st.success(f"✅ تم حذف سجل بنك ({bank_to_delete}) بنجاح.")
                st.rerun()
    else:
        st.info("📂 لا توجد بنوك مسجلة حتى الآن. قم إجراء التشخيص في الأعلى لتسجيل وترتيب البنوك.")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("📂 استعراض المصفوفة الهرمية والمحاور الرئيسة والأبعاد والعناصر الفرعية لمؤشر الحوكمة (SSGI)"):
        st.markdown("""
        <div dir="rtl" style="text-align: right;">
        <ul>
            <li><b>منصات المعلومات الذكية (SIP - وزن 40%):</b> يضم جودة المعلومات، التكامل والخصوصية، الامتثال التقني، والتخطيط والمراقبة بعد النشر.</li>
            <li><b>الحوكمة المؤسسية (IG - وزن 30%):</b> يضم سيادة القانون، العدالة والمساواة، المتابعة والمساءلة، المشاركة، الشفافية والإفصاح، ومجلس الإدارة.</li>
            <li><b>تقارير الاستدامة (SR - وزن 30%):</b> يضم الاستراتيجية، التنوع والشمول، إدارة المخاطر، الأبعاد التشغيلية، والمقاييس والأهداف.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        hierarchy_table_html = """
        <div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 400px;">
        <table class="custom-rtl-table">
        <thead>
        <tr>
        <th>المحور الرئيسي</th>
        <th>البعد الأساسي</th>
        <th>العناصر الفرعية</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td rowspan="4" style="font-weight: bold; color: #002B49; vertical-align: top;">أولاً: منصات المعلومات الذكية (SIP)</td>
        <td>1. جودة المعلومات</td>
        <td>1/1 جاهزية البنية التحتية الرقمية.<br>1/2 توافر البيانات وقابليتها للمعالجة الآلية.</td>
        </tr>
        <tr>
        <td>2. التكامل والخصوصية</td>
        <td>2/1 الترابط البيني التقني.<br>2/2 السيادة الرقمية وأمن المعلومات.</td>
        </tr>
        <tr>
        <td>3. الامتثال التقني</td>
        <td>3/1 الامتثال للمعايير القياسية.<br>3/2 حوكمة الخوارزميات والذكاء الاصطناعي.</td>
        </tr>
        <tr>
        <td>4. التخطيط والمراقبة بعد النشر</td>
        <td>4/1 الرصد والتحليل الآني.<br>4/2 دقة وموثوقية المخرجات الرقابية.</td>
        </tr>
        <tr>
        <td rowspan="6" style="font-weight: bold; color: #002B49; vertical-align: top;">ثانياً: الحوكمة المؤسسية (IG)</td>
        <td>1. سيادة القانون</td>
        <td>1/1 التوافق التشريعي والتنظيمي مع البنك المركزي.<br>1/2 الأخلاقيات والسلوك المصرفي.</td>
        </tr>
        <tr>
        <td>2. العدالة والمساواة</td>
        <td>2/1 العدالة التنظيمية والوظيفية.<br>2/2 عدالة حقوق أصحاب المصلحة والمودعين.</td>
        </tr>
        <tr>
        <td>3. المتابعة والمساءلة</td>
        <td>3/1 وضوح هيكل المسؤوليات والصلاحيات.<br>3/2 فاعلية آليات الرقابة والتدقيق الداخلي.</td>
        </tr>
        <tr>
        <td>4. المشاركة</td>
        <td>4/1 تفاعل وانخراط أصحاب المصلحة.<br>4/2 المشاركة الفعالة في صنع القرار الاستراتيجي.</td>
        </tr>
        <tr>
        <td>5. الشفافية والإفصاح</td>
        <td>5/1 جودة ووضوح الإفصاح المالي وغير المالي.<br>5/2 توقيت ودورية الإفصاح.</td>
        </tr>
        <tr>
        <td>6. مجلس الإدارة</td>
        <td>6/1 كفاءة وفاعلية تشكيل المجلس والأعضاء المستقلين.<br>6/2 نشاط اللجان المنبثقة (المراجعة، المخاطر).<br>6/3 سياسات تجنب تعارض المصالح.</td>
        </tr>
        <tr>
        <td rowspan="5" style="font-weight: bold; color: #002B49; vertical-align: top;">ثالثاً: تقارير الاستدامة (SR)</td>
        <td>1. الاستراتيجية</td>
        <td>1/1 الدمج الاستراتيجي لأهداف التنمية المستدامة.<br>1/2 التخصيص المالي والائتماني المستدام.</td>
        </tr>
        <tr>
        <td>2. التنوع والشمول</td>
        <td>2/1 تنوع الهيكل القيادي وتمكين المرأة.<br>2/2 شمول الخدمات المالية المصرفية.</td>
        </tr>
        <tr>
        <td>3. إدارة المخاطر</td>
        <td>3/1 دمج مخاطر المناخ ضمن إدارة المخاطر الكلية.<br>3/2 اختبارات الضغط والتحوط المرن.</td>
        </tr>
        <tr>
        <td>4. الأبعاد التشغيلية</td>
        <td>4/1 التمويل والاستثمار الأخضر والاقتصادي.<br>4/2 الكفاءة التشغيلية للموارد والبيئة.<br>4/3 أثر المسؤولية المجتمعية والإنفاق التنموي.</td>
        </tr>
        <tr>
        <td>5. المقاييس والأهداف</td>
        <td>5/1 أداء تحقيق المستهدفات البيئية والمجتمعية.<br>5/2 المواءمة المعيارية مع (GRI و ISSB) والتوكيد.</td>
        </tr>
        </tbody>
        </table>
        </div>
        """
        st.markdown(hierarchy_table_html, unsafe_allow_html=True)

        axes_names_bank = ['منصات المعلومات الذكية (SIP - 40%)', 'الحوكمة المؤسسية (IG - 30%)', 'تقارير الاستدامة (SR - 30%)']
        weights_vals_bank = [40, 30, 30]
        custom_pie_colors_bank = [CBE_NAVY, CBE_GOLD, "#475569"]

        fig_pie_bank = px.pie(
            names=axes_names_bank,
            values=weights_vals_bank,
            hole=0.4,
            title="توزيع الأوزان النسبية لمؤشر الحوكمة الذكية المستدامة (SSGI)",
            color=axes_names_bank,
            color_discrete_map=dict(zip(axes_names_bank, custom_pie_colors_bank))
        )
        fig_pie_bank.update_layout(
            title=dict(text="توزيع الأوزان النسبية لمؤشر الحوكمة الذكية المستدامة (SSGI)", x=0.99, xanchor='right'),
            paper_bgcolor="#FFFFFF",
            font=dict(family="Cairo", size=13)
        )
        st.plotly_chart(fig_pie_bank, use_container_width=True)

# ------------------------------------------------------------------------------
# التبويب الثالث: محاكي السياسات (Policy Simulator) - مطابق تماماً لكود الصناعات
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🔬 محاكي السياسات الاستشرافي والمتابعة التراكمية للسيناريوهات المصرفية</h3>
        <p>استشراف أثر التدخلات الاستثمارية والتكنولوجية واختبار السيناريوهات الاستراتيجية بدقة عالية.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI في القسم السابق.")
    else:
        col_sim_in, col_sim_out = st.columns([1, 2], gap="large")

        with col_sim_in:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            recorded_banks_sim = [item["البنك"] for item in st.session_state.history_state]
            sim_bank_sel = st.selectbox("اختر البنك للمحاكاة", recorded_banks_sim, key="sim_bank")
            base_ssgi_input = st.slider("قيمة المؤشر الافتراضي الحالي", 30.0, 100.0, 85.0, 0.5, key="sim_base")
            
            scenario_dropdown = st.selectbox("اختر السيناريو الاستراتيجي", [
                "📉 السيناريو التشاؤمي (غياب التدخل وضعف الاستثمار التقني)",
                "📊 السيناريو المعتدل / التفاؤلي (استثمارات تقليدية تدريجية)",
                "🚀 السيناريو الطموح / الاستباقي (إصلاحات هيكلية شاملة وسيادة رقمية)"
            ], index=1, key="sim_scen")
            
            var1_sip = st.slider("1️⃣ نسبة الزيادة في منصات المعلومات والبنية التقنية (%)", 0, 50, 20, key="sim_v1")
            var2_ig = st.slider("2️⃣ نسبة الزيادة في كفاءة الحوكمة المؤسسية (%)", 0, 50, 15, key="sim_v2")
            var3_sr = st.slider("3️⃣ نسبة الزيادة في تقارير الاستدامة والتمويل الأخضر (%)", 0, 50, 15, key="sim_v3")

            run_sim_btn = st.button("📋 إضافة وتثبيت سيناريو البنك", use_container_width=True, type="primary")
            
            if st.button("🗑️ مسح وإعادة تعيين استجابات المحاكي", use_container_width=True, type="secondary"):
                st.session_state.simulated_results_dict = {}
                st.success("✅ تم مسح جميع سيناريوهات المحاكي بنجاح.")
                st.rerun()

            sim_word_html = f"""
            <html dir="rtl">
            <head><meta charset="utf-8"><title>تقرير محاكي السياسات المصرفية</title></head>
            <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
                <h1 style="color: {CBE_NAVY}; text-align: center;">تقرير محاكي السياسات الاستشرافي والمتابعة التراكمية</h1>
                <p style="text-align: center; color: #64748B;">المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة</p>
                <hr>
                <h3>📋 مقارنة السيناريوهات المثبتة للبنوك (المختارة):</h3>
            """
            if st.session_state.simulated_results_dict:
                for k, v in st.session_state.simulated_results_dict.items():
                    sim_word_html += f"""
                    <div style="border: 1px solid #CBD5E1; padding: 15px; margin-bottom: 15px; border-radius: 8px;">
                        <h4>السيناريو: {k}</h4>
                        <div>{v['html']}</div>
                        <div style="margin-top: 10px;">{v['deep']}</div>
                    </div>
                    """
            else:
                sim_word_html += "<p>لا توجد سيناريوهات مسجلة حالياً.</p>"
                
            sim_word_html += f"""
                <hr>
                <h3>📈 ملخص النتائج التحليلية التراكمية والمعمقة لكافة أقسام المنصة:</h3>
                <p>يغطي هذا التقرير مخرجات النمذجة القياسية ومتغيرات التحفيز الاستراتيجي للقيادات المصرفية.</p>
                <hr>
                <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">يُنصح بالمراجعة الدقيقة للقرارات الاستراتيجية</p>
                <p style="text-align: center; font-size: 12px; color: #64748B;">جميع الحقوق محفوظة للدراسة البحثية © 2026</p>
            </body>
            </html>
            """
            st.download_button(
                label="📥 تحميل تقرير محاكي السياسات (Word)",
                data=sim_word_html.encode("utf-8-sig"),
                file_name="تقرير_محاكي_السياسات_المصرفية.doc",
                mime="application/msword",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col_sim_out:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            if run_sim_btn:
                if sim_bank_sel == "اختر البنك المصرفي":
                    st.warning("⚠️ يرجى اختيار بنك مصرفي صحيح أولاً.")
                else:
                    base_val = base_ssgi_input
                    s_val, i_val, r_val = 85, 90, 82
                    for item in st.session_state.history_state:
                        if item["البنك"] == sim_bank_sel:
                            base_val = item["مؤشر SSGI المركب"]
                            s_val = item["منصات المعلومات (40%)"]
                            i_val = item["الحوكمة المؤسسية (30%)"]
                            r_val = item["تقارير الاستدامة (30%)"]
                            break

                    combined_boost = (var1_sip * 0.40) + (var2_ig * 0.30) + (var3_sr * 0.30)

                    if scenario_dropdown.startswith("📉"):
                        simulated_val = max(0.0, base_val * 0.90)
                        analysis_text = f"تحذير استباقي لـ ({sim_bank_sel}): غياب الاستثمار في تطوير منصات المعلومات ({s_val}%) والالتزام الرقابي سيؤدي إلى تراجع المؤشر بنسبة 10% واهتزاز الامتثال."
                        action_plan = f"تعزيز موازنات التحول الرقمي والحفاظ على الحد الأدنى لمتطلبات لجان المراجعة وإدارة المخاطر ({i_val}%)."
                    elif scenario_dropdown.startswith("📊"):
                        simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.0022)))
                        analysis_text = f"استقرار تطوري مستدام لـ ({sim_bank_sel}): نجاح تدريجي في ترشيد أداء منصات المعلومات ({s_val}%) ورفع كفاءة تقارير الاستدامة ({r_val}%)."
                        action_plan = f"مواصلة التحفيز التدريجي وتوسيع قاعدة الاستثمار في الأصول الخضراء ومحفظة التمويل المستدام."
                    else:
                        simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.0042)))
                        analysis_text = f"قفزة استراتيجية كبرى لـ ({sim_bank_sel}): استثمار البنية التقنية المتقدمة ({s_val}%) والسياسة الحوكمة الراسخة ({i_val}%) لتحقيق الريادة المصرفية المستدامة."
                        action_plan = "قيادة التحول الرقمي المصرفي الكامل، وتطبيق أحدث أنظمة (RegTech)، وتصدر التصنيفات الإقليمية في التمويل الأخضر."

                    simulated_val = round(simulated_val, 2)
                    delta = round(simulated_val - base_val, 2)
                    score_str_plain = get_colored_score_html(simulated_val)

                    deep_analysis = f"""
                    <div style="background: #F8FAFC; padding: 16px; border-radius: 8px; border: 1px solid #CBD5E1; margin-top: 10px;" dir="rtl">
                        <p style="font-weight: bold; color: {CBE_NAVY}; margin-bottom: 8px; text-align: right;">📊 التشخيص القياسي المخصص لدولة/بنك ({sim_bank_sel}):</p>
                        <ul style="margin: 0; padding-right: 20px; color: #1E293B; line-height: 1.8; text-align: right;">
                            <li><b>1. منصات المعلومات (SIP):</b> {describe_sip(s_val)}</li>
                            <li><b>2. الحوكمة المؤسسية (IG):</b> {describe_ig(i_val)}</li>
                            <li><b>3. تقارير الاستدامة (SR):</b> {describe_sr(r_val)}</li>
                        </ul>
                    </div>
                    """

                    box_html = f"""
                    <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
                      <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">📈 محاكاة بنك: {sim_bank_sel} | السيناريو: {scenario_dropdown}</h3>
                      <p style="font-size: 15px; margin-bottom: 8px;"><b>القيمة المتوقعة للمؤشر:</b> {score_str_plain} (صافي التغير: <span style="font-weight: bold;">{delta:+.2f}</span>)</p>
                      <div style="background: {CBE_BG}; padding: 12px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; margin-top: 10px;">
                        <p style="margin-bottom: 6px;"><b>🔬 التحليل القياسي:</b> {analysis_text}</p>
                        <p style="margin: 0 0 8px 0; color: {CBE_GOLD}; font-weight: bold;">🛠️ خطة التحرك: {action_plan}</p>
                      </div>
                    </div>
                    """
                    sim_key = f"{sim_bank_sel} - {scenario_dropdown}"
                    st.session_state.simulated_results_dict[sim_key] = {
                        "html": box_html, 
                        "deep": deep_analysis, 
                        "bank": sim_bank_sel,
                        "simulated_val": simulated_val,
                        "delta": delta,
                        "scenario": scenario_dropdown,
                        "analysis_text": analysis_text,
                        "action_plan": action_plan
                    }

            if st.session_state.simulated_results_dict:
                st.markdown("---")
                st.markdown("<h4>📋 مقارنة السيناريوهات المثبتة للبنوك:</h4>", unsafe_allow_html=True)
                for item in st.session_state.simulated_results_dict.values():
                    st.markdown(item["html"], unsafe_allow_html=True)
                    st.markdown(item["deep"], unsafe_allow_html=True)
                    st.markdown("---")
            else:
                st.info("📈 قم بضبط البنك والسيناريو ومتغيرات التحفيز واضغط على زر الإضافة لتثبيت ومتابعة السيناريوهات هنا بغرض المقارنة.")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الرابع: لوحة دعم اتخاذ القرار - مطابق تماماً لكود الصناعات
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🛡️ لوحة دعم اتخاذ القرار وتوطين السياسات المصرفية</h3>
        <p>استعراض وتثبيت التوصيات الاستراتيجية المخصصة لكل بنك في القطاع المصرفي بديناميكية تمنع التكرار.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI في القسم الأول.")
    else:
        col_dec_in, col_dec_out = st.columns([1, 2], gap="large")

        with col_dec_in:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            recorded_banks_dec = [item["البنك"] for item in st.session_state.history_state]
            decision_bank_sel = st.selectbox("اختر البنك لاستعراض التوصيات", recorded_banks_dec, key="dec_bank")
            generate_decision_btn = st.button("📋 إضافة وتثبيت توصيات البنك المختارة", use_container_width=True, type="primary")
            
            if st.button("🗑️ مسح وإعادة تعيين لوحة القرار", use_container_width=True, type="secondary"):
                st.session_state.decision_results_dict = {}
                st.success("✅ تم مسح جميع توصيات لوحة القرار بنجاح.")
                st.rerun()

            dec_word_html = f"""
            <html dir="rtl">
            <head><meta charset="utf-8"><title>تقرير لوحة دعم القرار المصرفي</title></head>
            <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
                <h1 style="color: {CBE_NAVY}; text-align: center;">تقرير لوحة دعم اتخاذ القرار والسياسات المصرفية</h1>
                <p style="text-align: center; color: #64748B;">المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة</p>
                <hr>
                <h3>🛡️ تقرير وتوصيات البنوك المسجلة:</h3>
            """
            if st.session_state.decision_results_dict:
                for k, v in st.session_state.decision_results_dict.items():
                    dec_word_html += f"""
                    <div style="border: 1px solid #CBD5E1; padding: 15px; margin-bottom: 15px; border-radius: 8px;">
                        <h3>تقرير وتوصيات بنك: {v['bank']} (المؤشر المركب: {v['score_str']})</h3>
                        <p><b>🎯 التوصيات الاستراتيجية الموجهة:</b></p>
                        <ul>
                            <li>{v['recs'][0]}</li>
                            <li>{v['recs'][1]}</li>
                        </ul>
                        <p><b>💡 إضافات تحليلية استراتيجية عميقة ومخصصة:</b></p>
                        <div>{v['deep']}</div>
                    </div>
                    """
            else:
                dec_word_html += "<p>لا توجد توصيات مسجلة حالياً.</p>"
                
            dec_word_html += f"""
                <hr>
                <h3>📈 ملخص النتائج التحليلية التراكمية والمعمقة لكافة أقسام المنصة:</h3>
                <p>تعكس هذه التوصيات متطلبات الحوكمة المؤسسية والسيادة الرقمية وتوطين معايير الاستدامة.</p>
                <hr>
                <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">يُنصح بالمراجعة الدقيقة للقرارات الاستراتيجية</p>
                <p style="text-align: center; font-size: 12px; color: #64748B;">جميع الحقوق محفوظة للدراسة البحثية © 2026</p>
            </body>
            </html>
            """
            st.download_button(
                label="📥 تحميل تقرير لوحة دعم القرار (Word)",
                data=dec_word_html.encode("utf-8-sig"),
                file_name="تقرير_لوحة_دعم_القرار_المصرفي.doc",
                mime="application/msword",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col_dec_out:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            if generate_decision_btn:
                if not st.session_state.history_state or decision_bank_sel == "اختر البنك المصرفي":
                    st.warning("⚠️ يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI في القسم الأول.")
                else:
                    bank_data = next((item for item in st.session_state.history_state if item["البنك"] == decision_bank_sel), None)
                    if bank_data:
                        score = bank_data["مؤشر SSGI المركب"]
                        s_val = bank_data["منصات المعلومات (40%)"]
                        i_val = bank_data["الحوكمة المؤسسية (30%)"]
                        r_val = bank_data["تقارير الاستدامة (30%)"]
                        score_str_plain = get_colored_score_html(score)

                        if score >= 80:
                            recs_list = [
                                f"<b>تعزيز ريادة الابتكار المصرفي لـ ({decision_bank_sel}):</b> توظيف منصات المعلومات المتقدمة ({s_val}%) لتصدير الخدمات المالية الرقمية وقيادة التحول نحو المعايير المستدامة.",
                                f"<b>الحوكمة المؤسسية المتقدمة:</b> استثمار رصيد لجان المراجعة والالتزام ({i_val}%) لقيادة تطبيق أحدث نظم الرقابة التنظيمية (RegTech)."
                            ]
                            deep_analysis_text = f"""
- توصي المنصة بتأسيس <b>'لجنة عليا للسيادة الرقمية والاستدامة'</b> مستفيدين من كفاءة الحوكمة المؤسسية ({i_val}%).
- تعزيز مساهمة البنك في التمويل الأخضر استناداً إلى الأداء المرتفع في تقارير الاستدامة ({r_val}%).
- قيادة الشراكات المصرفية الاستراتيجية لتعظيم العوائد وتحقيق أهداف التنمية المستدامة.
                            """
                        elif score >= 51:
                            recs_list = [
                                f"<b>ردم الفجوة التقنية والمؤسسية لـ ({decision_bank_sel}):</b> إطلاق حزم برامج تطوير منصات المعلومات بناءً على قراءة ({s_val}%).",
                                f"<b>سد الاختناقات الهيكلية:</b> تعزيز استقلالية لجان المراجعة وإدارة المخاطر لتحسين مؤشر الحوكمة المسجل عند ({i_val}%)."
                            ]
                            deep_analysis_text = f"""
- تتطلب صانعة القرار تفعيل <b>'برامج الرقابة التنظيمية الآلية'</b> لرفع كفاءة تدفق البيانات والتقارير الرقابية.
- توجيه الائتمان المصرفي نحو المشروعات الخضراء لتعويض الضعف النسبي في الاستدامة ({r_val}%).
- تحديث أطر إدارة المخاطر الكلية والتحوط المرن.
                            """
                        else:
                            recs_list = [
                                f"<b>التدخل الاستباقي العاجل لـ ({decision_bank_sel}):</b> معالجة الاختناقات الهيكلية الحرجة في البنية التقنية ومنصات المعلومات ({s_val}%).",
                                f"<b>إعادة هيكلة أطر الحوكمة:</b> تفعيل التزام تام بتعليمات البنك المركزي ورفع كفاءة التدقيق الداخلي ({i_val}%)."
                            ]
                            deep_analysis_text = f"""
- تفرض الضرورة القصوى تنفيذ خطط طوارئ استثمارية لترميم البنية التحتية الرقمية ({s_val}%).
- مراجعة سياسات تعارض المصالح وهيكل مجالس الإدارة لردم الفجوات الرقابية.
- إطلاق برامج عاجلة للإفصاح المالي وغير المالي وفق معايير الاستدامة ({r_val}%).
                            """

                        st.session_state.decision_results_dict[decision_bank_sel] = {
                            "bank": decision_bank_sel,
                            "score_str": score_str_plain,
                            "recs": recs_list,
                            "deep": deep_analysis_text
                        }

            if st.session_state.decision_results_dict:
                for item in st.session_state.decision_results_dict.values():
                    card_html = f"""
                    <div style="background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);" dir="rtl">
                        <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px; text-align: right;">🛡️ تقرير وتوصيات بنك: {item['bank']} (المؤشر المركب: {item['score_str']})</h3>
                        <div style="background: {CBE_BG}; padding: 12px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; margin-top: 10px;">
                            <p style="font-weight: bold; color: {CBE_NAVY}; margin-bottom: 6px; text-align: right;">🎯 التوصيات الاستراتيجية الموجهة:</p>
                            <ul style="margin: 0; padding-right: 20px; color: #1E293B; line-height: 1.8; text-align: right;">
                                <li>{item['recs'][0]}</li>
                                <li>{item['recs'][1]}</li>
                            </ul>
                            <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 10px 0;">
                            <p style="font-weight: bold; color: {CBE_NAVY}; margin-bottom: 6px; text-align: right;">💡 إضافات تحليلية استراتيجية عميقة ومخصصة:</p>
                            <div style="color: #1E293B; line-height: 1.8; text-align: right; padding-right: 20px;">
                                {item['deep']}
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.info("🛡️ يرجى اختيار البنك المسجل والضغط على زر الإضافة لتثبيت التوصيات هنا.")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الخامس: التقرير التنفيذي الموحد - مطابق تماماً لكود الصناعات
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📑 أداة تصدير التقرير التنفيذي الموحد لحوكمة القطاع المصرفي</h3>
        <p>ملخص استراتيجي شامل يدمج نتائج التدقيق ونتائج محاكي السياسات وإطار دونيلا ميدوز لنقاط الرفع في تقرير موحد جاهز للعرض على القيادات العليا.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 تحديث وتوليد التقرير التنفيذي الموحد", use_container_width=True, type="primary"):
        if not st.session_state.history_state:
            st.warning("📂 لا توجد بيانات مسجلة كافية حتى الآن. يرجى إدخال تشخيص بنك واحد على الأقل في القسم الثاني.")
        else:
            df_rep = pd.DataFrame(st.session_state.history_state).sort_values(
                by="مؤشر SSGI المركب", ascending=False
            ).reset_index(drop=True)
            
            top_row = df_rep.iloc[0]
            top_bank = top_row["البنك"]
            top_score = top_row["مؤشر SSGI المركب"]
            top_score_str = get_colored_score_html(top_score)

            cards_html_list = []
            word_blocks_html = ""

            for idx, row in df_rep.iterrows():
                b_name = row['البنك']
                b_score = row['مؤشر SSGI المركب']
                b_diag = row['التقييم التشخيصي']
                
                s_val = row['منصات المعلومات (40%)']
                i_val = row['الحوكمة المؤسسية (30%)']
                r_val = row['تقارير الاستدامة (30%)']
                
                if b_score >= 80:
                    specific_strategic_angle = f"يتمتع بنك ({b_name}) بأداء متقدم ومستدام ({b_score}%), مما يمنحه ميزة تنافسية عالية في قيادة التحول الرقمي المصرفي، التمويل الأخضر، والامتثال الرقابي المتقدم."
                    specific_policy_action = f"تأسيس 'لجنة استراتيجية للسيادة الرقمية'، تعظيم محفظة الأصول الخضراء، وتوظيف الأنظمة الرقابية المتقدمة (RegTech)."
                elif b_score >= 51:
                    specific_strategic_angle = f"يسجل بنك ({b_name}) جاهزية متوسطة ({b_score}%) تواجه بعض الاختناقات الهيكلية في البنية التقنية أو لجان الالتزام؛ وهو ما يتطلب تدخلاً استباقياً لردم الفجوات."
                    specific_policy_action = f"تنفيذ برامج تطوير منصات المعلومات (SIP)، تعزيز استقلالية لجان المراجعة، والتوسع في تدريب الكوادر."
                else:
                    specific_strategic_angle = f"تظهر قراءة بنك ({b_name}) فجوة هيكلية حرجة ({b_score}%) تستوجب خطط طوارئ عاجلة لترميم البنية التقنية وهيكلة الحوكمة الداخلية."
                    specific_policy_action = f"إعلان حالة طوارئ تقنية لرفع سقف البنية التحتية ({s_val}%) ومراجعة ضوابط الالتزام وتجنب تعارض المصالح."

                matched_sims = [s_key for s_key in st.session_state.simulated_results_dict.keys() if s_key.startswith(b_name)]
                if matched_sims:
                    latest_sim_key = matched_sims[-1]
                    sim_data_obj = st.session_state.simulated_results_dict[latest_sim_key]
                    sim_detail = (
                        f"تم تطبيق سيناريو ({sim_data_obj['scenario']})؛ "
                        f"حيث بلغت القيمة المتوقعة للمؤشر ({sim_data_obj['simulated_val']}%) بصافي تغير قدره ({sim_data_obj['delta']:+.2f}). "
                        f"<b>التحليل:</b> {sim_data_obj['analysis_text']} "
                        f"<b>خطة التحرك:</b> {sim_data_obj['action_plan']}"
                    )
                else:
                    sim_detail = "<span style='background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #FCD34D;'>⚠️ لم يتم تسجيل سيناريو استشرافي لهذا البنك.</span>"
                
                if b_name in st.session_state.decision_results_dict:
                    dec_item = st.session_state.decision_results_dict[b_name]
                    dec_detail = f"{dec_item['recs'][0]} — وكذلك: {dec_item['recs'][1]}"
                else:
                    dec_detail = "<span style='background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #FCD34D;'>⚠️ لم يتم اعتماد توصيات لوحة القرار لهذا البنك.</span>"

                single_card_html = f"""
                <div style="background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);" dir="rtl">
                    <h4 style="color: {CBE_NAVY}; font-weight: bold; margin-top: 0; margin-bottom: 10px; font-size: 16.5px;">
                        📌 التشخيص المنظومي والنتائج الاستراتيجية المستقلة لبنك: <span style="color: {CBE_GOLD};">{b_name}</span> (المؤشر المركب: {b_score}%)
                    </h4>
                    <p style="margin-bottom: 8px; color: #334155; font-size: 14px;"><b>التقييم التشخيصي الشامل:</b> {b_diag}</p>
                    <div style="background: {CBE_BG}; padding: 12px; border-radius: 8px; margin-bottom: 10px; border-right: 4px solid {CBE_GOLD};">
                        <p style="margin: 0 0 6px 0; font-weight: bold; color: {CBE_NAVY}; font-size: 13.5px;">• زاوية التحليل الاستراتيجي المتميزة:</p>
                        <p style="margin: 0; color: #1E293B; font-size: 13.5px; line-height: 1.7;">{specific_strategic_angle}</p>
                    </div>
                    <ul style="margin: 0; padding-right: 20px; color: #1E293B; font-size: 13.5px; line-height: 1.8;">
                        <li><b>محاور الجاهزية الذكية المرصودة:</b> منصات المعلومات ({s_val}%) | الحوكمة المؤسسية ({i_val}%) | تقارير الاستدامة ({r_val}%)</li>
                        <li><b>المسار التنفيذي الموصى به:</b> {specific_policy_action}</li>
                        <li style="margin-top: 8px;"><b>🔬 مخرجات محاكي السياسات الاستشرافي:</b><br>{sim_detail}</li>
                        <li style="margin-top: 8px;"><b>🛡️ مخرجات لوحة دعم القرار والسياسات:</b><br>{dec_detail}</li>
                    </ul>
                </div>
                """
                cards_html_list.append(single_card_html)
                word_blocks_html += single_card_html

            st.markdown(f"""
            <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 30px; border-radius: 14px; border: 2px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 6px 20px rgba(0,0,0,0.08);">
              <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 15px; margin-bottom: 25px;">
                <h2 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">📑 التقرير التنفيذي الموحد لحوكمة القطاع المصرفي وتقارير الاستدامة</h2>
                <p style="color: #64748B; font-size: 14.5px; margin-top: 6px;">ملخص استراتيجي موجه للقيادات العليا وصناع القرار - بناءً على مخرجات الدراسة المنهجية (SSGI)</p>
              </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: {CBE_BG}; padding: 18px; border-radius: 10px; border-right: 5px solid {CBE_GOLD}; margin-bottom: 25px;" dir="rtl">
                <h4 style="color: {CBE_NAVY}; margin-top: 0;">🏆 مؤشرات الأداء العام والريادة المصرفية:</h4>
                <p style="margin-bottom: 8px;">يتصدّر البنك التالي قائمة الحوكمة الذكية المستدامة وفق الترتيب التنازلي للمؤشر المركب: <span style="font-weight: bold; color: {CBE_GOLD};">{top_bank}</span> بقيمة مركبة تبلغ {top_score_str}.</p>
                <p style="margin: 0;">إجمالي البنوك الخاضعة للتشخيص والتحليل المنظومي حتى الآن: <b>{len(df_rep)} بنك مصرفي</b>.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<h4 style='color: #002B49; margin-bottom: 12px;'>📋 ترتيب الملخص التراكمي للبنوك:</h4>", unsafe_allow_html=True)
            for idx, row in df_rep.iterrows():
                s = row['مؤشر SSGI المركب']
                s_str = get_colored_score_html(s)
                summary_card = f"""
                <div style="margin-bottom: 12px; line-height: 1.8; background: #F8FAFC; padding: 12px 16px; border-radius: 8px; border: 1px solid #E2E8F0;" dir="rtl">
                    <b>المركز ({idx + 1}): {row['البنك']}</b> — المؤشر المركب: {s_str} | منصات المعلومات: {row['منصات المعلومات (40%)']}% | الحوكمة: {row['الحوكمة المؤسسية (30%)']}% <br>
                    <span style="color: #475569; font-size: 13.5px;"><b>التقييم التشخيصي:</b> {row['التقييم التشخيصي']}</span>
                </div>
                """
                st.markdown(summary_card, unsafe_allow_html=True)

            for card_code in cards_html_list:
                st.markdown(card_code, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            word_content = f"""
            <html dir="rtl">
            <head><meta charset="utf-8"><title>التقرير التنفيذي الموحد للقطاع المصرفي</title></head>
            <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
                <h1 style="color: {CBE_NAVY}; text-align: center;">📑 التقرير التنفيذي الموحد لحوكمة القطاع المصرفي وتقارير الاستدامة</h1>
                <p style="text-align: center; color: #64748B;">ملخص استراتيجي موجه للقيادات العليا وصناع القرار (SSGI)</p>
                <hr>
                <h3>🏆 مؤشرات الأداء العام والريادة المصرفية:</h3>
                <p>يتصدّر البنك التالي قائمة الحوكمة الذكية المستدامة: <b>{top_bank}</b> بقيمة مركبة تبلغ {top_score_str}.</p>
                <p>إجمالي البنوك الخاضعة للتشخيص والتحليل المنظومي: <b>{len(df_rep)} بنك مصرفي</b>.</p>
                <hr>
                <h3>📈 ملخص النتائج التحليلية التراكمية والمعمقة لكافة أقسام المنصة:</h3>
                {word_blocks_html}
                <hr>
                <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">يُنصح بالمراجعة الدقيقة للقرارات الاستراتيجية</p>
                <p style="text-align: center; font-size: 12px; color: #64748B;">جميع الحقوق محفوظة للدراسة البحثية © 2026</p>
            </body>
            </html>
            """
            st.download_button(
                label="📥 تحميل التقرير التنفيذي في ملف مستند (Word)",
                data=word_content.encode("utf-8-sig"),
                file_name="التقرير_التنفيذي_للقطاع_المصرفي.doc",
                mime="application/msword",
                use_container_width=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب السادس: مولد تقارير الاستدامة (GRI/ISSB)
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🌿 إعداد مسودة تقارير الاستدامة (GRI / ISSB) للقطاع المصرفي</h3>
        <p>توليد مسودة أولية لتقارير الاستدامة للبنوك المصرية وفق الأطر الدولية والمعايير الرقابية الحديثة.</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("مولد تقارير الاستدامة جاهز لتوليد مسودة الإفصاحات البيئية والمجتمعية والحوكمة (ESG) للبنوك المسجلة.")

# ------------------------------------------------------------------------------
# التبويب السابع: لوحة تحكم المشرف والزوار (Admin Dashboard + أداة audit_differentiation)
# ------------------------------------------------------------------------------
if tab7 is not None:
    with tab7:
        st.markdown("""
        <div dir="rtl" style="text-align: right;">
            <h3>🔒 لوحة تحكم المشرف وسجلات الزوار (Admin Dashboard & IP Logging)</h3>
            <p>متابعة وتصدير سجلات دخول الزوار وعناوين الـ IP، بالإضافة إلى اختبار أداة تمايز الإجابات للمحرك.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 🔍 أداة فحص تدقيق التشابه والتمايز بين البنوك (`audit_differentiation`)")
        threshold_slider = st.slider("عتبة التشابه (Threshold)", 0.5, 0.99, 0.90, 0.01)
        
        if st.button("🚀 تشغيل فحص تمايز الإجابات", type="primary"):
            sample_questions = [
                "متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟",
                "كيف يتعامل البنك مع مخاطر المناخ والتمويل الأخضر؟",
                "كيف يضمن البنك الحصانة السيبرانية ومنع تسريب البيانات المالية الحساسة؟"
            ]
            with st.spinner("⏳ جاري مقارنة إجابات البنوك وقياس نسبة التشابه..."):
                flagged_pairs = audit_differentiation(BANKS_LIST_AR, sample_questions, threshold=threshold_slider)
                if flagged_pairs:
                    st.warning(f"⚠️ تنبيه: تم رصد {len(flagged_pairs)} حالة تجاوزت عتبة التشابه {threshold_slider}:")
                    for q_item, b1, b2, ratio_val in flagged_pairs:
                        st.markdown(f"- السـؤال: *{q_item}* بين **{b1}** و **{b2}** (نسبة التشابه: `{ratio_val}`)")
                else:
                    st.success("✅ ممتاز! لا توجد حالات تجاوزت عتبة التشابه، الإجابات متميزة تماماً.")

        st.markdown("---")
        st.markdown("#### 📋 سجلات الزوار وعناوين IP (من السيرفر الدائم)")
        visitors_data_list = load_visitors_log_from_file()
        if visitors_data_list:
            df_v = pd.DataFrame(visitors_data_list)
            st.dataframe(df_v, use_container_width=True)
            
            csv_visitors = df_v.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل سجل الزوار والأفراد وعناوين IP (CSV)",
                data=csv_visitors,
                file_name="سجل_الزوار_وعناوين_IP_للبنوك.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("📂 لا توجد سجلات زيارات حتى الآن.")

st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)
