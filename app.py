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

# ==============================================================================
# 1. إعدادات صفحة Streamlit (يجب أن يكون هذا أول أمر برمجي بالملف)
# ==============================================================================
st.set_page_config(
    page_title="مقترح المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# استيراد محرك الإجابات المستقل المطور وتوابعه البرمجية بعد set_page_config
from bank_rag_engine import process_rag_gemini_query, audit_differentiation

CBE_NAVY = "#002B49"        # أزرق مصرفي عميق
CBE_GOLD = "#C5A059"        # ذهبي ملكي
CBE_GOLD_LIGHT = "#E2C07D"    # ذهبي فاتح
CBE_BG = "#F8F9FA"            # خلفية ناعمة

# تنسيق CSS محسن يضمن بقاء الشريط الجانبي ظاهراً وثابتاً ولا يتأثر بقواعد المحتوى
CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

/* إخفاء شريط العرض العلوي الافتراضي لـ Streamlit مع الحفاظ التام على الشريط الجانبي */
header[data-testid="stHeader"] {{
    background: transparent !important;
    visibility: hidden !important;
}}

.stAppToolbar {{
    display: none !important;
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

/* ضمان ظهور وثبات الشريط الجانبي وتحكمه الكامل بالعرض */
section[data-testid="stSidebar"] {{
    background-color: #FFFFFF !important;
    border-left: 1px solid #E2E8F0 !important;
    direction: rtl !important;
    text-align: right !important;
    z-index: 999999 !important;
}}

section[data-testid="stSidebar"] * {{
    direction: rtl !important;
    text-align: right !important;
}}

/* إصلاح الجداول وعناصر العرض */
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

/* تصميم الأزرار ومفاتيح التحميل */
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
    padding: 35px 20px !important;
    border-radius: 16px !important;
    border-bottom: 5px solid {CBE_GOLD} !important;
    box-shadow: 0 12px 35px rgba(0,0,0,0.2) !important;
    margin-bottom: 20px !important;
    direction: rtl !important;
}}

.header-center h1 {{
    color: {CBE_GOLD} !important;
    font-size: 24px !important;
    font-weight: 800 !important;
    margin-bottom: 10px !important;
    text-shadow: 0 2px 6px rgba(0,0,0,0.5) !important;
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
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
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
# الدوال المساعدة
# ==============================================================================
def flat_html(s: str) -> str:
    return " ".join(l.strip() for l in s.splitlines() if l.strip())

def clean_text(text) -> str:
    if not isinstance(text, str):
        return str(text)
    t = re.sub(r"\[cite[^\]]*\]", "", text)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\xa0", " ").replace("\u200b", "")
    return re.sub(r"\s+", " ", t).strip()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ==============================================================================
# قاعدة بيانات البنوك والملفات
# ==============================================================================
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

LOG_FILE = "visitors_log.csv"
SURVEY_LOG_FILE = "survey_responses_log.csv"

def init_visitor_log_file():
    if not os.path.exists(LOG_FILE):
        try:
            pd.DataFrame(columns=["عنوان IP", "اسم المستخدم", "الدور", "وقت الدخول"]).to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
        except Exception:
            pass

def init_survey_log_file():
    if not os.path.exists(SURVEY_LOG_FILE):
        try:
            pd.DataFrame(columns=[
                "معرف الاستجابة", "اسم البنك", "المسمى الوظيفي / الإدارة", "سنوات الخبرة",
                "محور منصات المعلومات", "محور الحوكمة المؤسسية", "محور تقارير الاستدامة",
                "ملاحظات وتوصيات إضافية", "وقت الإرسال"
            ]).to_csv(SURVEY_LOG_FILE, index=False, encoding='utf-8-sig')
        except Exception:
            pass

init_visitor_log_file()
init_survey_log_file()

def load_visitors_log_from_file():
    if os.path.exists(LOG_FILE):
        try:
            return pd.read_csv(LOG_FILE, encoding='utf-8-sig').to_dict(orient="records")
        except Exception:
            return []
    return []

def load_survey_log_from_file():
    if os.path.exists(SURVEY_LOG_FILE):
        try:
            return pd.read_csv(SURVEY_LOG_FILE, encoding='utf-8-sig').to_dict(orient="records")
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
        new_record = {"عنوان IP": client_ip, "اسم المستخدم": username, "الدور": role, "وقت الدخول": timestamp}
        existing_logs = load_visitors_log_from_file()
        if not any(item.get("عنوان IP") == client_ip and item.get("اسم المستخدم") == username for item in existing_logs):
            existing_logs.append(new_record)
            pd.DataFrame(existing_logs).to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
    except Exception:
        pass

# ==============================================================================
# إدارة الجلسة وتسجيل الدخول
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

ADMIN_USER = st.secrets.get("admin_credentials", {}).get("username", "admin")
ADMIN_PASS_HASH = st.secrets.get("admin_credentials", {}).get("password_hash", hash_password("admin123"))

if not st.session_state.authenticated:
    _, col2, _ = st.columns([1, 2, 1])
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

BANKS_LIST_AR = [
    "اختر البنك المصرفي",
    "بنك مصر BM", "البنك الأهلي المصري NBE", "البنك التجاري الدولي CIB", "بنك قطر الوطني الأهلي QNB",
    "بنك كريدي أجريكول", "بنك الإسكندرية", "بنك التعمير والإسكان HDB", "بنك قناة السويس SCBANK",
    "بنك أبوظبي الأول مصر FABMISR", "بنك فيصل الإسلامي", "بنك البركة الإسلامي", "بنك القاهرة Banque du Caire",
    "مصرف أبو ظبي الإسلامي ADIB", "بنك NEXT", "بنك الإمارات دبي الوطني NDB", "بنك HSBC",
    "التجاري وفا بنك", "بنك المؤسسة العربية المصرفية ABC", "المصرف العربي الدولي AIB", "البنك الزراعي المصري",
    "ستاندرد تشارترد – مصر", "البنك العقاري المصري العربي EALB", "بنك الكويت الوطني NBK", "بنك المصري الخليجي EG BANK",
    "المصرف المتحد UN", "ميد بنك MIDBANK", "بنك التنمية الصناعية IDB", "بنك المشرق",
    "بنك بيت التمويل الكويتي KFH", "بنك الأهلي الكويتي مصر ABK", "بنك تنمية الصادرات EBANK", "بنك سيب SAIB",
    "البنك العربي", "البنك العربي الأفريقي", "بنك أبوظبي التجاري ADCB", "بنك ناصر الاجتماعي",
    "بنك الاستثمار القومي", "بنك الأهلي المتحد KFH", "بنوك بلوم BLOM", "البنك الأهلي اليوناني", "بنك سيتي بنك CITIBANK"
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

# ==============================================================================
# الهيدر والشريط الإخباري والقائمة الجانبية (Sidebar)
# ==============================================================================
_, col_h2 = st.columns([4, 1])
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
<b>إعداد الباحث: أيمن الدسوقي (مدرس مساعد إدارة المعرفة – معهد التخطيط القومي)</b>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <span class="ticker-item">🏛️ مقترح المنصة الوطنية الذكية لتعزيز الحوكمة وتقارير الاستدامة بالقطاع المصرفي المصري</span>
    <span class="ticker-item">| 📊 مؤشر الحوكمة الذكية المستدامة (SSGI) والأبعاد الثلاثة الرئيسة</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي لاختبار السيناريوهات الاستراتيجية (Multiple Regression)</span>
    <span class="ticker-item">| 🛡️ لوحة دعم اتخاذ القرار</span>
    <span class="ticker-item">| 📋 الاستبيان الموجه لفرق العمل في البنوك وعينة الدراسة الميدانية</span>
    <span class="ticker-item">| 📖 دليل المستخدم الرسمي والتوثيق المنهجي PDF</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# القائمة الجانبية المنظمة والمضمونة الظهور (Sidebar Navigation)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: right; padding: 10px 0;" dir="rtl">
        <h3 style="color: {CBE_NAVY}; font-weight: 800; font-size: 16px;">🧭 التنقل الرئيسي للمنصة</h3>
        <p style="color: #64748B; font-size: 12.5px;">اختر القسم المطلوب للتصفح والتشغيل:</p>
    </div>
    """, unsafe_allow_html=True)
    
    navigation_options = [
        "🎯 اسأل المنصة (الاستعلام الذكي)",
        "📊 مؤشر الحوكمة المركب (SSGI)",
        "📈 محاكي السياسات (Policy Simulator)",
        "🛡️ لوحة دعم اتخاذ القرار",
        "📑 التقرير التنفيذي الموحد",
        "🌿 مولد تقارير الاستدامة (GRI/ISSB)",
        "📋 استبيان فرق العمل المصرفي",
        "📖 دليل المستخدم الرسمي والتوجيهي"
    ]
    
    if st.session_state.role == "admin":
        navigation_options.append("🔒 لوحة تحكم المشرف والزوار (Admin)")
        
    selected_page = st.radio(
        "اختر القسم:",
        navigation_options,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: right; font-size: 12px; color: #64748B;" dir="rtl">
        <p><b>معاهد وجهات الإشراف:</b><br>• جامعة عين شمس<br>• معهد التخطيط القومي</p>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# توجيه المحتوى بناءً على اختيار القائمة الجانبية
# ==============================================================================
if selected_page == "🎯 اسأل المنصة (الاستعلام الذكي)":
    st.markdown("<h3>🎯 تحليل واستخلاص البيانات</h3>", unsafe_allow_html=True)
    col_q1, col_q2 = st.columns([1, 2], gap="large")

    with col_q1:
        ask_bank_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, key="ask_bank")
        user_question = st.text_area("❓ اكتب سؤالك/ استفسارك:", placeholder="مثال: متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟", height=120, key="query_text_box")
        
        def set_suggested_question(q):
            st.session_state.query_text_box = q

        with st.expander("🏛️ محور الحوكمة والتأسيس والتاريخ"):
            for i, q in enumerate(["متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟", "عرف الحوكمة وتكوين مجلس الإدارة بالبنك"]):
                st.button(q, key=f"btn_ig_{i}", on_click=set_suggested_question, args=(q,), use_container_width=True)
        
        ask_submit_btn = st.button("تقديم السؤال/ الاستفسار", use_container_width=True, type="primary")

    with col_q2:
        if ask_submit_btn:
            if ask_bank_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي صحيح من القائمة.")
            elif not user_question.strip():
                st.warning("⚠️ يرجى كتابة أو اختيار سؤال.")
            else:
                with st.spinner("⏳ جاري تحليل واسترجاع الإجابة..."):
                    st.markdown(flat_html(process_rag_gemini_query(ask_bank_sel, user_question)), unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح أو كتابة الاستعلام ثم اضغط تقديم.")

elif selected_page == "📊 مؤشر الحوكمة المركب (SSGI)":
    st.markdown("<h3>🗳️ التشخيص القياسي واحتساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>", unsafe_allow_html=True)
    col_input, col_result = st.columns([1, 2], gap="large")
    with col_input:
        bank_ssgi_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, key="t1_bank")
        sip_val = st.slider("1. محور منصات المعلومات والبنية الرقمية (SIP - 40%)", 0, 100, 88, key="t1_sip")
        ig_val = st.slider("2. محور الحوكمة المؤسسية والامتثال (IG - 30%)", 0, 100, 90, key="t1_ig")
        sr_val = st.slider("3. محور تقارير الاستدامة ومخاطر المناخ (SR - 30%)", 0, 100, 82, key="t1_sr")
        calc_ssgi_btn = st.button("🚀 احسب وسجل مؤشر البنك", use_container_width=True, type="primary")

    with col_result:
        if calc_ssgi_btn:
            if bank_ssgi_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي حقيقي من القائمة.")
            else:
                final_score = round((sip_val * 0.40) + (ig_val * 0.30) + (sr_val * 0.30), 2)
                st.success(f"القيمة المركبة للمؤشر (SSGI) لبنك {bank_ssgi_sel}: {final_score}%")
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=[sip_val, ig_val, sr_val], theta=['SIP', 'IG', 'SR'], fill='toself', name=bank_ssgi_sel, line_color=CBE_GOLD))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
                st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("📊 اضغط على حساب المؤشر لعرض النتيجة والتحليل الرداري.")

elif selected_page == "📈 محاكي السياسات (Policy Simulator)":
    st.markdown("<h3>🔬 محاكي السياسات الاستشرافي للسيناريوهات المصرفية</h3>", unsafe_allow_html=True)
    st.info("قم بإجراء التشخيص في قسم مؤشر الحوكمة أولاً لتفعيل محاكي السياسات والسيناريوهات.")

elif selected_page == "🛡️ لوحة دعم اتخاذ القرار":
    st.markdown("<h3>🛡️ لوحة دعم اتخاذ القرار المصرفي</h3>", unsafe_allow_html=True)
    st.info("استعراض التوصيات والتوجيهات المخصصة لصناع القرار.")

elif selected_page == "📑 التقرير التنفيذي الموحد":
    st.markdown("<h3>📑 أداة توليد التقرير التنفيذي الموحد</h3>", unsafe_allow_html=True)
    if st.button("🚀 توليد وتحديث التقرير التنفيذي فورياً", type="primary"):
        st.success("✅ تم تحديث التقرير التنفيذي بنجاح.")

elif selected_page == "🌿 مولد تقارير الاستدامة (GRI/ISSB)":
    st.markdown("<h3>🌿 نظام توليد تقارير الاستدامة المتقدم والدليل العملي الشامل</h3>", unsafe_allow_html=True)
    st.info("استعراض وتوليد مسودات تقارير الاستدامة ومعايير الـ ESG.")

elif selected_page == "📋 استبيان فرق العمل المصرفي":
    st.markdown("<h3>📋 الاستبيان الموجه إلى فرق العمل في البنوك</h3>", unsafe_allow_html=True)
    st.success("استمارة الاستبيان الميداني لجمع وتحليل البيانات جاهزة للتعبئة.")

elif selected_page == "📖 دليل المستخدم الرسمي والتوجيهي":
    st.markdown("<h3>📖 دليل المستخدم الرسمي والتوثيق المنهجي لمنصة الحوكمة المصرفية</h3>", unsafe_allow_html=True)
    st.info("دليل تشغيلي متكامل للمحكمين والباحثين.")

elif selected_page == "🔒 لوحة تحكم المشرف والزوار (Admin)":
    st.markdown("<h3>🔒 لوحة تحكم المشرف وسجلات الزوار</h3>", unsafe_allow_html=True)
    visitors = load_visitors_log_from_file()
    if visitors:
        st.dataframe(pd.DataFrame(visitors), use_container_width=True)
    else:
        st.info("لا توجد سجلات زيارات مسجلة حتى الآن.")

st.markdown('<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)
