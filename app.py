import io
import os
import json
import re
import hashlib
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
    page_title="المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CBE_NAVY = "#002B49"        # أزرق مصرفي عميق
CBE_GOLD = "#C5A059"        # ذهبي ملكي
CBE_GOLD_LIGHT = "#E2C07D"    # ذهبي فاتح
CBE_BG = "#F8F9FA"            # خلفية ناعمة

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
    border: none !important;
}}

.stApp {{
    background-color: {CBE_BG} !important;
    direction: rtl !important;
    text-align: right !important;
    border: none !important;
}}

div.stMarkdown, div.stText, div.stSelectbox, div.stSlider,
div.stDataFrame, div.stTable, .element-container,
div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"], section {{
    direction: rtl !important;
    text-align: right !important;
    outline: none !important;
    box-shadow: none !important;
    border: none !important;
}}

*:focus, *:active, *:focus-visible {{
    outline: none !important;
    box-shadow: none !important;
    border-color: transparent !important;
}}

div[data-baseweb="select"] *, 
div[data-baseweb="popover"] *, 
ul[data-baseweb="menu"] *, 
div[role="listbox"] *,
div[role="option"] {{
    direction: rtl !important;
    text-align: right !important;
    border: none !important;
    outline: none !important;
}}

.custom-rtl-table {{
    width: 100% !important;
    border-collapse: collapse !important;
    direction: rtl !important;
    text-align: right !important;
    margin-top: 8px !important;
    margin-bottom: 12px !important;
    font-family: 'Cairo', sans-serif !important;
    background-color: #FFFFFF !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03) !important;
    border: 1px solid #E2E8F0 !important;
}}

.custom-rtl-table th {{
    background: linear-gradient(135deg, {CBE_NAVY} 100%, #001A33 100%) !important;
    color: #F8FAFC !important;
    padding: 10px 10px !important;
    font-weight: 700 !important;
    border-bottom: 2px solid {CBE_GOLD} !important;
    text-align: right !important;
    font-size: 13px !important;
    white-space: nowrap !important;
}}

.custom-rtl-table td {{
    padding: 8px 10px !important;
    border-bottom: 1px solid #F1F5F9 !important;
    color: #1E293B !important;
    font-size: 12.5px !important;
    text-align: right !important;
    line-height: 1.5 !important;
}}

.custom-rtl-table tr:nth-child(even) {{
    background-color: #FAFAFA !important;
}}

.custom-rtl-table tr:hover {{
    background-color: #FEF3C7 !important;
}}

div.stButton > button, div.stDownloadButton > button {{
    width: 100% !important;
    border-radius: 50px !important;
    font-family: 'Cairo', sans-serif !important;
    font-weight: 700 !important;
    background-color: {CBE_NAVY} !important;
    color: #FFFFFF !important;
    border: 1.5px solid {CBE_GOLD} !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(0, 43, 73, 0.15) !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #001A33 !important;
    color: {CBE_GOLD_LIGHT} !important;
    border-color: #FFFFFF !important;
    box-shadow: 0 6px 16px rgba(0, 43, 73, 0.3) !important;
}}

.header-center {{
    text-align: center !important;
    background: linear-gradient(135deg, rgba(0, 43, 73, 0.95) 0%, rgba(0, 26, 51, 0.90) 100%),
                url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1600&auto=format&fit=crop') !important;
    background-size: cover !important;
    background-position: center !important;
    color: #FFFFFF !important;
    padding: 30px 20px !important;
    border-radius: 16px !important;
    border-bottom: 5px solid {CBE_GOLD} !important;
    box-shadow: 0 12px 35px rgba(0,0,0,0.2) !important;
    margin-bottom: 20px !important;
    direction: rtl !important;
}}

.header-center h1 {{
    color: {CBE_GOLD} !important;
    font-size: 22px !important;
    font-weight: 800 !important;
    margin-bottom: 8px !important;
}}

.header-center h3 {{
    color: #F1F5F9 !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    line-height: 1.6 !important;
    margin-bottom: 4px !important;
}}

.ticker-wrap {{
    width: 100%;
    background: linear-gradient(90deg, {CBE_NAVY} 0%, #001F35 100%);
    border-top: 2px solid {CBE_GOLD};
    border-bottom: 2px solid {CBE_GOLD};
    overflow: hidden;
    white-space: nowrap;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
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
    font-size: 13.5px;
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
    margin-top: 30px;
    border-top: 1px solid #E2E8F0;
    padding-top: 15px;
    font-weight: bold;
    direction: rtl !important;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# الدوال المساعدة (Flat HTML, Clean Text & Caching)
# ==============================================================================
def flat_html(s: str) -> str:
    return "\n".join(l.strip() for l in s.splitlines() if l.strip())

def clean_text(text) -> str:
    if not isinstance(text, str):
        return str(text)
    t = re.sub(r"\[cite[^\]]*\]", "", text)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\xa0", " ").replace("\u200b", "")
    return re.sub(r"\s+", " ", t).strip()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

LOG_FILE = "visitors_log.csv"
SURVEY_LOG_FILE = "survey_responses_log.csv"

@st.cache_data
def load_visitors_log_from_file():
    if os.path.exists(LOG_FILE):
        try:
            df = pd.read_csv(LOG_FILE, encoding='utf-8-sig')
            return df.to_dict(orient="records")
        except Exception:
            return []
    return []

@st.cache_data
def load_survey_log_from_file():
    if os.path.exists(SURVEY_LOG_FILE):
        try:
            df = pd.read_csv(SURVEY_LOG_FILE, encoding='utf-8-sig')
            return df.to_dict(orient="records")
        except Exception:
            return []
    return []

def init_visitor_log_file():
    if not os.path.exists(LOG_FILE):
        try:
            df_init = pd.DataFrame(columns=["عنوان IP", "اسم المستخدم", "الدور", "وقت الدخول"])
            df_init.to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
        except Exception:
            pass

def init_survey_log_file():
    if not os.path.exists(SURVEY_LOG_FILE):
        try:
            df_init = pd.DataFrame(columns=[
                "معرف الاستجابة", "اسم البنك", "المسمى الوظيفي / الإدارة", "سنوات الخبرة",
                "محور منصات المعلومات", "محور الحوكمة المؤسسية", "محور تقارير الاستدامة",
                "ملاحظات وتوصيات إضافية", "وقت الإرسال"
            ])
            df_init.to_csv(SURVEY_LOG_FILE, index=False, encoding='utf-8-sig')
        except Exception:
            pass

init_visitor_log_file()
init_survey_log_file()

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
            pd.DataFrame(existing_logs).to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
            st.cache_data.clear()
    except Exception:
        pass

# ==============================================================================
# إدارة جلسة الدخول والصلاحيات الآمنة
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "history_state" not in st.session_state:
    st.session_state.history_state = []
if "simulated_results_dict" not in st.session_state:
    st.session_state.simulated_results_dict = {}
if "decision_results_dict" not in st.session_state:
    st.session_state.decision_results_dict = {}
if "query_text_box" not in st.session_state:
    st.session_state.query_text_box = ""
if "draft_generated_state" not in st.session_state:
    st.session_state.draft_generated_state = False
if "draft_bank_name" not in st.session_state:
    st.session_state.draft_bank_name = ""

ADMIN_USER = st.secrets.get("admin_credentials", {}).get("username", "admin")
ADMIN_PASS_HASH = st.secrets.get("admin_credentials", {}).get("password_hash", hash_password("admin123"))

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 30px; border-radius: 16px; border: 2px solid {CBE_GOLD}; box-shadow: 0 10px 30px rgba(0,0,0,0.08); text-align: right;" dir="rtl">
            <h2 style="color: {CBE_NAVY}; text-align: center; font-weight: 800; margin-bottom: 10px;">🏛️ مقترح المنصة الوطنية الذكية لحوكمة القطاع المصرفي</h2>
            <p style="color: #475569; text-align: center; font-size: 14px; line-height: 1.6; margin-bottom: 25px;">
                إطار تطبيقي مقترح لبرنامج دكتوراه الفلسفة في العلوم البيئية - جامعة عين شمس. يرجى تسجيل الدخول للمتابعة.
            </p>
        </div>
        """, unsafe_allow_html=True)

        username_input = st.text_input("اسم المستخدم (Username)", placeholder="أدخل اسم المستخدم...")
        password_input = st.text_input("كلمة المرور (Password)", type="password", placeholder="أدخل كلمة المرور...")

        if st.button("🔐 تسجيل الدخول للمنصة", use_container_width=True):
            if username_input == ADMIN_USER and hash_password(password_input) == ADMIN_PASS_HASH:
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
# قاعدة معطيات البنوك
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

BANK_PROFILE_DATA = {
    "بنك مصر BM": {
       "founded": "تأسس في 7 مايو 1920 بريادة الاقتصاددي الوطني محمد طلعت حرب باشا.",
        "ownership": "مملوك بالكامل لحكومة جمهورية مصر العربية (مؤسسة مالية حكومية كبرى).",
       "profile": "أول بنك مصري بالكامل يهدف إلى استثمار المدخرات الوطنية وتوجيهها لخدمة الاقتصاد القومي والتنمية المستدامة."
    },
    "البنك الأهلي المصري NBE": {
        "founded": "تأسس في 25 يونيو 1898 بموجب أمر عالي.",
       "ownership": "مملوك بالكامل لحكومة جمهورية مصر العربية.",
       "profile": "يُعد أقدم وأكبر البنوك التجارية في مصر، ولعب تاريخياً دور البنك المركزي في إصدار النقد وتمويل التجارة."
    },
    "البنك التجاري الدولي CIB": {
       "founded": "تأسس عام 1975 تحت اسم (بنك تشيس مانهاتن التجاري الدولي) ثم تحول إلى اسمه الحالي.",
       "ownership": "شركة مساهمة مصرية مدرجة في البورصة المصرية (مملوك لمؤسسات ومستثمرين محليين وعالميين).",
        "profile": "يُعد أكبر البنوك التجارية الخاصة في مصر وسبّاقاً في تطبيق معايير الحوكمة والتحول الرقمي والاستدامة."
    },
    "بنك قطر الوطني الأهلي QNB": {
       "founded": "تأسس عام 1978 كشركة مساهمة مصرية.",
       "ownership": "تابع لمجموعة QNB العالمية (قطر الوطني) بنسبة سيطرة أغلبية.",
       "profile": "يُعد أحد أكبر البنوك الخاصة العاملة في السوق المصرفي المصري مع شبكة فروع واسعة وتمويلات مؤسسية ضخمة."
    }
}

def get_bank_founding_profile(bank_name):
    for key, data in BANK_PROFILE_DATA.items():
        if key in bank_name:
            return f"<b>تاريخ النشأة:</b> {data['founded']} | <b>هيكل الملكية:</b> {data['ownership']} | <b>نبذة تأسيسية:</b> {data['profile']}"
    return f"<b>بيانات تنظيمية:</b> بنك مصرفي مسجل وخاضع لإشراف البنك المركزي المصري ويعمل وفق المعايير المصرفية والرقابية المعتمدة."

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
        return f"حوكمة مؤسسية راسخة ({val}%) مع استقلالية تامة لمجلس الإدارة ولجان المراجعة والامتثال بأعلى معايير الشفافية."
    elif val >= 50:
        return f"الحوكمة المؤسسية في نطاق متوازن ({val}%) وتتطلب تفعيل ضوابط تعارض المصالح وتعزيز دور الأعضاء المستقلين."
    else:
        return f"قصور حاد في الحوكمة المؤسسية ({val}%) يستوجب تدخلاً رقابياً لإعادة هندسة لجان المراجعة وإدارة المخاطر."

def describe_sr(val):
    if val >= 80:
        return f"أداء متميز والتزام ريادي في تقارير الاستدامة والتمويل الأخضر ({val}%) مع دمج فعال لمخاطر المناخ وتوسيع الأصول الخضراء وفق معايير (GRI/ISSB)."
    elif val >= 50:
        return f"أداء متوسط في تقارير الاستدامة ({val}%) يستوجب التوسع في محفظة التمويل المستدام ومخاطر المناخ."
    else:
        return f"ضعف هيكلي في ملف الاستدامة والتمويل الأخضر ({val}%) يعيق امتثال البنك للمعايير الدولية."

# ==============================================================================
# الهيكل المحدث للقائمة الجانبية (Sidebar Navigation)
# ==============================================================================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: right; padding: 10px 0; border-bottom: 2px solid {CBE_GOLD}; margin-bottom: 15px;" dir="rtl">
        <h3 style="color: {CBE_NAVY}; font-size: 16px; font-weight: 800; margin: 0;">🏛️ المنصة الوطنية الذكية</h3>
        <p style="color: #475569; font-size: 12px; margin-top: 5px;">قائمة التنقل الجانبي ونظام الـ Stepper</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"👤 <b>المستخدم الحالي:</b><br>{st.session_state.username}", unsafe_allow_html=True)
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

    st.markdown("---")
    st.markdown("<b>📂 أقسام ووحدات المنصة:</b>", unsafe_allow_html=True)

    if st.session_state.role == "admin":
        nav_options = [
            "🎯 اسأل المنصة",
            "📊 مؤشر الحوكمة المركب (SSGI)", 
            "📈 محاكي السياسات (Policy Simulator)", 
            "🛡️ لوحة دعم اتخاذ القرار", 
            "📑 التقرير التنفيذي الموحد",
            "🌿 مولد تقارير الاستدامة (GRI/ISSB)",
            "📋 استبيان فرق العمل المصرفي",
            "📖 دليل المستخدم الرسمي PDF",
            "🔒 لوحة تحكم المشرف والزوار (Admin)"
        ]
    else:
        nav_options = [
            "🎯 اسأل المنصة",
            "📊 مؤشر الحوكمة المركب (SSGI)", 
            "📈 محاكي السياسات (Policy Simulator)", 
            "🛡️ لوحة دعم اتخاذ القرار", 
            "📑 التقرير التنفيذي الموحد",
            "🌿 مولد تقارير الاستدامة (GRI/ISSB)",
            "📋 استبيان فرق العمل المصرفي",
            "📖 دليل المستخدم الرسمي PDF"
        ]

    selected_nav = st.radio("اختر القسم للانتقال السريع:", nav_options, label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size: 11.5px; color: #64748B; line-height: 1.6;" dir="rtl">
    <b>📊 إحصائيات سريعة:</b><br>
    - البنوك المسجلة: <b>{len(st.session_state.history_state)}</b><br>
    - السيناريوهات النشطة: <b>{len(st.session_state.simulated_results_dict)}</b><br>
    - استجابات الاستبيان: <b>{len(load_survey_log_from_file())}</b>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# الهيدر والشريط الإخباري المتحرك
# ==============================================================================
st.markdown(f"""
<div class="header-center">
<h1>مقترح المنصة الوطنية الذكية لتعزيز الحوكمة وتقارير الاستدامة بالقطاع المصرفي المصري</h1>
<h3>إطار تطبيقي مقترح ضمن متطلبات نيل درجة دكتوراة الفلسفة في العلوم البيئية - جامعة عين شمس</h3>
<b>إعداد الباحث: أيمن الدسوقي (مدرس مساعد إدارة المعرفة – معهد التخطيط القومي)</b>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <span class="ticker-item">🏛️ مقترح المنصة الوطنية الذكية لتعزيز الحوكمة وتقارير الاستدامة بالقطاع المصرفي المصري</span>
    <span class="ticker-item">| 📊 مؤشر الحوكمة الذكية المستدامة (SSGI) والأبعاد الثلاثة الرئيسة</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي لاختبار السيناريوهات الاستراتيجية</span>
    <span class="ticker-item">| 🛡️ لوحة دعم اتخاذ القرار والسياسات المصرفية</span>
    <span class="ticker-item">| 📋 الاستبيان الموجه لفرق العمل في البنوك وعينة الدراسة الميدانية</span>
    <span class="ticker-item">| 📖 دليل المستخدم الرسمي والتوثيق المنهجي PDF</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# مطابقة التنقل الجانبي مع التبويبات الفعالة
# ==============================================================================
if st.session_state.role == "admin":
    tabs = st.tabs([
        "🎯 اسأل المنصة",
        "📊 مؤشر الحوكمة المركب (SSGI)", 
        "📈 محاكي السياسات (Policy Simulator)", 
        "🛡️ لوحة دعم اتخاذ القرار", 
        "📑 التقرير التنفيذي الموحد",
        "🌿 مولد تقارير الاستدامة (GRI/ISSB)",
        "📋 استبيان فرق العمل المصرفي",
        "📖 دليل المستخدم الرسمي PDF",
        "🔒 لوحة تحكم المشرف والزوار (Admin)"
    ])
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = tabs
else:
    tabs = st.tabs([
        "🎯 اسأل المنصة",
        "📊 مؤشر الحوكمة المركب (SSGI)", 
        "📈 محاكي السياسات (Policy Simulator)", 
        "🛡️ لوحة دعم اتخاذ القرار", 
        "📑 التقرير التنفيذي الموحد",
        "🌿 مولد تقارير الاستدامة (GRI/ISSB)",
        "📋 استبيان فرق العمل المصرفي",
        "📖 دليل المستخدم الرسمي PDF"
    ])
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = tabs
    tab9 = None

# ==============================================================================
# التبويب الأول: اسأل المنصة
# ==============================================================================
with tab1:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🎯 تحليل واستخلاص البيانات الذكي</h3>
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

        with st.expander("🏛️ محور الحوكمة والتأسيس والتاريخ"):
            ig_questions = [
                "متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟",
                "عرف الحوكمة وتكوين مجلس الإدارة بالبنك",
                "ما هي نسبة الأعضاء المستقلين وسياسات تجنب تعارض المصالح؟"
            ]
            for i, q in enumerate(ig_questions):
                st.button(q, key=f"btn_ig_{i}", on_click=set_suggested_question, args=(q,), use_container_width=True)

        with st.expander("🌱 محور الاستدامة والتمويل الأخضر"):
            sr_questions = [
                "كيف يتعامل البنك مع مخاطر المناخ والتمويل الأخضر؟",
                "ما هي نسبة الأصول الخضراء والمشروعات المستدامة؟",
                "كيف يمتثل البنك للمعايير الدولية للإفصاح المالي (GRI و ISSB)؟"
            ]
            for i, q in enumerate(sr_questions):
                st.button(q, key=f"btn_sr_{i}", on_click=set_suggested_question, args=(q,), use_container_width=True)

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
                with st.spinner("⏳ جاري استرجاع وتحليل الإجابة المخصصة للبنك..."):
                    response_html = process_rag_gemini_query(ask_bank_sel, active_q)
                    st.markdown(flat_html(response_html), unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح أو كتابة السؤال/ الاستفسار.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# التبويب الثاني: مؤشر الحوكمة المركب (SSGI) مع نظام Stepper
# ==============================================================================
with tab2:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🗳️ التشخيص القياسي واحتساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
        <p>نظام تشخيص متسلسل (Stepper Workflow) لتقييم البنوك عبر المحاور الثلاثة الرئيسية.</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        st.markdown("<b>الخطوة 1: اختيار المؤسسة المصرفية</b>", unsafe_allow_html=True)
        bank_ssgi_sel = st.selectbox("اختر البنك المصرفي للتشخيص", BANKS_LIST_AR, key="t1_bank")

        st.markdown("<br><b>الخطوة 2: ضبط أوزان ومستويات محاور المؤشر</b>", unsafe_allow_html=True)
        sip_val = st.slider("1. محور منصات المعلومات والبنية الرقمية (SIP - 40%)", 0, 100, 88, key="t1_sip")
        ig_val = st.slider("2. محور الحوكمة المؤسسية والامتثال (IG - 30%)", 0, 100, 90, key="t1_ig")
        sr_val = st.slider("3. محور تقارير الاستدامة ومخاطر المناخ (SR - 30%)", 0, 100, 82, key="t1_sr")

        st.markdown("<br><b>الخطوة 3: تنفيذ واحتساب المؤشر المركب</b>", unsafe_allow_html=True)
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

                diagnosis = "أداء مصرفي مرتفع ومنتظم، نحو الريادة والسيادة الرقمية المستدامة."
                detailed_diag = f"""
                <div style="line-height: 1.8; font-size: 14px;">
                    <p><b>القيمة المركبة للمؤشر (SSGI):</b> <b>{score_str_plain}</b>.</p>
                    <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 8px 0;">
                    <ul style="margin: 0; padding-right: 20px;">
                        <li><b>منصات المعلومات (SIP):</b> {describe_sip(sip_val)}</li>
                        <li><b>الحوكمة المؤسسية (IG):</b> {describe_ig(ig_val)}</li>
                        <li><b>تقارير الاستدامة (SR):</b> {describe_sr(sr_val)}</li>
                    </ul>
                </div>
                """

                entry = {
                    "معرف السجل": f"{clean_text(bank_ssgi_sel)} [{datetime.now().strftime('%H:%M:%S')}]",
                    "البنك": clean_text(bank_ssgi_sel),
                    "مؤشر SSGI المركب": final_score,
                    "منصات المعلومات (40%)": round(sip_val, 2),
                    "الحوكمة المؤسسية (30%)": round(ig_val, 2),
                    "تقارير الاستدامة (30%)": round(sr_val, 2),
                    "التقييم التشخيصي": clean_text(diagnosis)
                }

                st.session_state.history_state = [item for item in st.session_state.history_state if item["البنك"] != clean_text(bank_ssgi_sel)]
                st.session_state.history_state.append(entry)

                st.markdown(flat_html(f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.8;">
                    <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 10px;">📊 نتيجة حساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
                    <p style="font-size: 14.5px;"><b>اسم البنك:</b> <span style="color: {CBE_NAVY}; font-weight: bold;">{clean_text(bank_ssgi_sel)}</span></p>
                    <div style="background: {CBE_BG}; padding: 14px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 8px;">
                        {detailed_diag}
                    </div>
                </div>
                """), unsafe_allow_html=True)

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=[sip_val, ig_val, sr_val],
                    theta=['منصات المعلومات (SIP)', 'الحوكمة المؤسسية (IG)', 'تقارير الاستدامة (SR)'],
                    fill='toself',
                    name=bank_ssgi_sel,
                    line_color=CBE_GOLD
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=True,
                    title=dict(text=f"التحليل الرداري لمحاور الحوكمة الذكية المستدامة - {bank_ssgi_sel}", x=0.5, xanchor='center'),
                    font=dict(family="Cairo", size=12)
                )
                st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("📊 قم باختيار البنك وضبط درجات المحاور الثلاثة ثم اضغط على زر الحساب لعرض النتائج والتحليل الرداري.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 قائمة البنوك والسجلات المختصرة المسجلة")
    if st.session_state.history_state:
        df_history = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)
        st.dataframe(df_history, use_container_width=True)
        
        csv_data = df_history.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تحميل جدول ترتيب السجلات والبنوك (Excel/CSV)",
            data=csv_data,
            file_name="ترتيب_البنوك_المصرية_SSGI.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("📂 لا توجد بنوك مسجلة حتى الآن. قم بإجراء التشخيص في الأعلى لتسجيل وترتيب البنوك.")

# ==============================================================================
# التبويب الثالث: محاكي السياسات (Policy Simulator)
# ==============================================================================
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🔬 محاكي السياسات الاستشرافي للسيناريوهات المصرفية</h3>
        <p>استشراف أثر التدخلات الاستراتيجية والسيناريوهات (التشاؤمي، المعتدل، الطموح).</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI في القسم السابق.")
    else:
        col_sim_in, col_sim_out = st.columns([1, 2], gap="large")

        with col_sim_in:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            recorded_banks_sim = list(set([item["البنك"] for item in st.session_state.history_state]))
            sim_bank_sel = st.selectbox("اختر البنك للمحاكاة", recorded_banks_sim, key="sim_bank")
            
            scenario_dropdown = st.selectbox("اختر السيناريو الاستراتيجي", [
                "📉 السيناريو التشاؤمي (غياب التدخل وضعف الاستثمار التقني)",
                "📊 السيناريو المعتدل / التفاؤلي (استثمارات تقليدية تدريجية)",
                "🚀 السيناريو الطموح / الاستباقي (إصلاحات هيكلية شاملة وسيادة رقمية)"
            ], index=1, key="sim_scen")

            var1_sip = st.slider("1️⃣ نسبة الزيادة في منصات المعلومات والبنية التقنية (%)", 0, 50, 20, key="sim_v1")
            var2_ig = st.slider("2️⃣ نسبة الزيادة في كفاءة الحوكمة المؤسسية (%)", 0, 50, 15, key="sim_v2")
            var3_sr = st.slider("3️⃣ نسبة الزيادة في تقارير الاستدامة والتمويل الأخضر (%)", 0, 50, 15, key="sim_v3")

            run_sim_btn = st.button("📋 إضافة وتثبيت سيناريو إضافي للبنك", use_container_width=True, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_sim_out:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            if run_sim_btn:
                base_val = 85.0
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
                elif scenario_dropdown.startswith("📊"):
                    simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.0022)))
                else:
                    simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.0042)))

                simulated_val = round(simulated_val, 2)
                delta = round(simulated_val - base_val, 2)
                score_str_plain = get_colored_score_html(simulated_val)

                box_html = f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 20px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 15px;">
                    <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">📈 محاكاة بنك: {sim_bank_sel} | السيناريو: {scenario_dropdown}</h3>
                    <p style="font-size: 14.5px;"><b>القيمة المتوقعة للمؤشر:</b> {score_str_plain} (صافي التغير: <span style="font-weight: bold;">{delta:+.2f}</span>)</p>
                </div>
                """
                sim_key = f"{sim_bank_sel} - {scenario_dropdown} [{datetime.now().strftime('%H:%M:%S')}]"
                st.session_state.simulated_results_dict[sim_key] = {"html": box_html, "bank": sim_bank_sel}

            if st.session_state.simulated_results_dict:
                st.markdown("<h4>📋 مقارنة السيناريوهات المتعددة المثبتة للبنوك:</h4>", unsafe_allow_html=True)
                for s_key, item in st.session_state.simulated_results_dict.items():
                    st.markdown(f"<span style='color: #64748B; font-size: 12px;'>معرف السيناريو: {s_key}</span>", unsafe_allow_html=True)
                    st.markdown(flat_html(item["html"]), unsafe_allow_html=True)
            else:
                st.info("📈 قم بضبط البنك والسيناريو ومتغيرات التحفيز واضغط على زر الإضافة لتثبيت ومتابعة عدة سيناريوهات هنا.")
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# التبويب الرابع: لوحة دعم اتخاذ القرار
# ==============================================================================
with tab4:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🛡️ لوحة دعم اتخاذ القرار المصرفي</h3>
        <p>استعراض وتثبيت التوصيات الاستراتيجية المخصصة لكل بنك في القطاع المصرفي المصري.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI في القسم الأول.")
    else:
        recorded_banks_dec = list(set([item["البنك"] for item in st.session_state.history_state]))
        decision_bank_sel = st.selectbox("اختر البنك لاستعراض التوصيات", recorded_banks_dec, key="dec_bank")
        generate_decision_btn = st.button("📋 عرض وتثبيت توصيات البنك المختارة", use_container_width=True, type="primary")

        if generate_decision_btn:
            bank_data = next((item for item in st.session_state.history_state if item["البنك"] == decision_bank_sel), None)
            if bank_data:
                score = bank_data["مؤشر SSGI المركب"]
                score_str_plain = get_colored_score_html(score)
                st.markdown(f"""
                <div style="background: #FFFFFF; padding: 20px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-top: 15px;" dir="rtl">
                    <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">🛡️ توصيات بنك: {decision_bank_sel} (المؤشر المركب: {score_str_plain})</h3>
                    <p>• تعزيز ريادة الابتكار المصرفي وتوظيف منصات المعلومات المتقدمة لقيادة التحول نحو المعايير المستدامة.<br>
                    • تفعيل برامج الرقابة التنظيمية الآلية والذكية (RegTech) لرفع كفاءة تدفق البيانات والتقارير الرقابية.</p>
                </div>
                """, unsafe_allow_html=True)

# ==============================================================================
# التبويب الخامس: التقرير التنفيذي الموحد
# ==============================================================================
with tab5:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📑 التقرير التنفيذي الموحد لحوكمة القطاع المصرفي</h3>
        <p>ملخص استراتيجي موجه للقيادات العليا وصناع القرار بناءً على معطيات التشخيص.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("📂 لا توجد بيانات مسجلة كافية حتى الآن. يرجى إدخال تشخيص بنك واحد على الأقل في القسم الثاني.")
    else:
        if st.button("🚀 توليد وتحديث التقرير التنفيذي الموحد فورياً", use_container_width=True, type="primary"):
            df_rep = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)
            top_row = df_rep.iloc[0]
            st.markdown(f"""
            <div style="background: #FFFFFF; padding: 25px; border-radius: 14px; border: 2px solid {CBE_GOLD}; line-height: 1.8;" dir="rtl">
                <h3 style="color: {CBE_NAVY};">🏆 يتصدر القائمة: {top_row['البنك']} بقيمة مركبة تبلغ {get_colored_score_html(top_row['مؤشر SSGI المركب'])}</h3>
                <p>إجمالي البنوك الخضعة للتشخيص: <b>{len(df_rep)} سجل مصرفي</b>.</p>
            </div>
            """, unsafe_allow_html=True)
            st.dataframe(df_rep, use_container_width=True)

# ==============================================================================
# التبويب السادس: مولد تقارير الاستدامة (GRI / ISSB)
# ==============================================================================
with tab6:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🌿 نظام توليد تقارير الاستدامة المتقدم والدليل العملي الشامل (GRI / ISSB)</h3>
        <p>إطار توجيهي متكامل يربط بين معايير المبادرة العالمية (GRI) والإفصاح المالي (ISSB).</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("🌿 يمكنك عبر هذا القسم استعراض مسودات تقارير الاستدامة المخصصة للبنوك المسجلة أو الاطلاع على الدليل الشامل لـ 30 مؤشراً لـ ESG.")

# ==============================================================================
# التبويب السابع: الاستبيان الموجه لفرق العمل في البنوك
# ==============================================================================
with tab7:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📋 الاستبيان الموجه إلى فرق العمل في البنوك (عينة الدراسة الميدانية)</h3>
        <p>استمارة الاستبيان الميداني المعتمدة لجمع آراء وتقييمات فرق العمل والقيادات المصرفية.</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("📋 استمارة الاستبيان جاهزة لاستقبال استجابات الباحثين والمحكمين وحفظها مباشرة في شيت الإكسيل.")

# ==============================================================================
# التبويب الثامن: دليل المستخدم الرسمي PDF
# ==============================================================================
with tab8:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📖 دليل المستخدم الرسمي والتوثيق المنهجي لمنصة الحوكمة المصرفية</h3>
        <p>توثيق شامل لكل وظائف المنصة وإتاحة التصدير المباشر للملفات.</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("📖 دليل المستخدم والتوثيق المنهجي متاح للتحطلاع والتنزيل المباشر.")

# ==============================================================================
# التبويب التاسع: لوحة تحكم المشرف (Admin)
# ==============================================================================
if tab9 is not None:
    with tab9:
        st.markdown("""
        <div dir="rtl" style="text-align: right;">
            <h3>🔒 لوحة تحكم المشرف وسجلات الزوار (Admin Dashboard)</h3>
            <p>متابعة وتصدير سجلات دخول الزوار وعناوين الـ IP، واختبار أداة تمايز الإجابات للمحرك.</p>
        </div>
        """, unsafe_allow_html=True)
        
        visitors_data_list = load_visitors_log_from_file()
        if visitors_data_list:
            df_v = pd.DataFrame(visitors_data_list)
            st.dataframe(df_v, use_container_width=True)
        else:
            st.info("📂 لا توجد سجلات زيارات حتى الآن.")

st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)
