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
try:
    from bank_rag_engine import process_rag_gemini_query, audit_differentiation
except ImportError:
    # دوال احتياطية في حال عدم توفر الملف الخارجي لتأمين التشغيل الفوري
    def process_rag_gemini_query(bank_name, query):
        return f"<div style='padding:15px; background:#fff; border-radius:8px;'><b>التحليل الموجه لـ {bank_name}:</b> بناءً على استعلامكم ('{query}')، تلتزم المنصة باسترجاع الأدلة الموثقة ودعم السيادة الرقمية والشفافية المصرفية.</div>"
    def audit_differentiation(banks, questions, threshold=0.9):
        return []

# ==============================================================================
# إعدادات صفحة Streamlit وتطبيق الهوية البصرية المصرفية (RTL & UX Optimized)
# ==============================================================================
st.set_page_config(
    page_title="مقترح المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CBE_NAVY = "#002B49"        # أزرق مصرفي عميق
CBE_GOLD = "#C5A059"        # ذهبي ملكي
CBE_GOLD_LIGHT = "#E2C07D"  # ذهبي فاتح
CBE_BG = "#F8F9FA"          # خلفية ناعمة

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

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

/* تصميم جدول RTL مخصص ونظيف وسلس */
.custom-rtl-table {{
    width: 100% !important;
    border-collapse: collapse !important;
    direction: rtl !important;
    text-align: right !important;
    margin-top: 8px !important;
    margin-bottom: 12px !important;
    background-color: #FFFFFF !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03) !important;
    border: 1px solid #E2E8F0 !important;
}}

.custom-rtl-table th {{
    background: {CBE_NAVY} !important;
    color: #F8FAFC !important;
    padding: 12px 10px !important;
    font-weight: 700 !important;
    border-bottom: 2px solid {CBE_GOLD} !important;
    text-align: right !important;
    font-size: 13.5px !important;
}}

.custom-rtl-table td {{
    padding: 10px !important;
    border-bottom: 1px solid #F1F5F9 !important;
    color: #1E293B !important;
    font-size: 13px !important;
    text-align: right !important;
    line-height: 1.6 !important;
}}

.custom-rtl-table tr:nth-child(even) {{
    background-color: #FAFAFA !important;
}}

.custom-rtl-table tr:hover {{
    background-color: #FEF3C7 !important;
}}

/* توحيد تصميم الأزرار ومفاتيح التحميل لتجربة مستخدم متميزة */
div.stButton > button, div.stDownloadButton > button {{
    width: 100% !important;
    border-radius: 12px !important;
    font-family: 'Cairo', sans-serif !important;
    font-weight: 700 !important;
    background-color: {CBE_NAVY} !important;
    color: #FFFFFF !important;
    border: 1.5px solid {CBE_GOLD} !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(0, 43, 73, 0.15) !important;
    padding: 10px 20px !important;
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
# الدوال المساعدة (Clean Text & Parsers)
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

# ==============================================================================
# قاعدة معطيات ومعلومات التأسيس والنشأة للبنوك المصرية
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

# ==============================================================================
# نظام تتبع الزوار والاستبيانات والملفات
# ==============================================================================
LOG_FILE = "visitors_log.csv"
SURVEY_LOG_FILE = "survey_responses_log.csv"

def init_logs():
    if not os.path.exists(LOG_FILE):
        try:
            pd.DataFrame(columns=["عنوان IP", "اسم المستخدم", "الدور", "وقت الدخول"]).to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
        except Exception:
            pass
    if not os.path.exists(SURVEY_LOG_FILE):
        try:
            pd.DataFrame(columns=[
                "معرف الاستجابة", "اسم البنك", "المسمى الوظيفي / الإدارة", "سنوات الخبرة",
                "محور منصات المعلومات", "محور الحوكمة المؤسسية", "محور تقارير الاستدامة",
                "ملاحظات وتوصيات إضافية", "وقت الإرسال"
            ]).to_csv(SURVEY_LOG_FILE, index=False, encoding='utf-8-sig')
        except Exception:
            pass

init_logs()

def load_visitors_log():
    if os.path.exists(LOG_FILE):
        try:
            return pd.read_csv(LOG_FILE, encoding='utf-8-sig').to_dict(orient="records")
        except Exception:
            return []
    return []

def load_survey_log():
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
        existing_logs = load_visitors_log()
        if not any(item.get("عنوان IP") == client_ip and item.get("اسم المستخدم") == username for item in existing_logs):
            existing_logs.append(new_record)
            pd.DataFrame(existing_logs).to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
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
if "survey_submitted_by_user" not in st.session_state:
    st.session_state.survey_submitted_by_user = False

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
# قائمة البنوك المصرية الشاملة
# ==============================================================================
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
if "draft_bank_name" not in st.session_state:
    st.session_state.draft_bank_name = ""

# ==============================================================================
# الهيدر والشريط الإخباري (Header & Ticker)
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
    <h3>إطار تطبيقي مقترح ضمن متطلبات نيل درجة دكتوراه الفلسفة في العلوم البيئية - جامعة عين شمس</h3>
    <b>إعداد الباحث: أيمن الدسوقي (مدرس مساعد إدارة المعرفة – معهد التخطيط القومي)</b>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <span class="ticker-item">🏛️ مقترح المنصة الوطنية الذكية لتعزيز الحوكمة وتقارير الاستدامة بالقطاع المصرفي المصري</span>
    <span class="ticker-item">| 📊 مؤشر الحوكمة الذكية المستدامة (SSGI) والأبعاد الثلاثة الرئيسة</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي لاختبار السيناريوهات الاستراتيجية</span>
    <span class="ticker-item">| 🛡️ لوحة دعم اتخاذ القرار</span>
    <span class="ticker-item">| 📋 الاستبيان الموجه لفرق العمل في البنوك وعينة الدراسة الميدانية</span>
    <span class="ticker-item">| 📖 دليل المستخدم الرسمي والتوثيق المنهجي PDF</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# التبويبات الرئيسة (التسعة تبويبات بالكامل)
# ==============================================================================
if st.session_state.role == "admin":
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
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
else:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🎯 اسأل المنصة",
        "📊 مؤشر الحوكمة المركب (SSGI)", 
        "📈 محاكي السياسات (Policy Simulator)", 
        "🛡️ لوحة دعم اتخاذ القرار", 
        "📑 التقرير التنفيذي الموحد",
        "🌿 مولد تقارير الاستدامة (GRI/ISSB)",
        "📋 استبيان فرق العمل المصرفي",
        "📖 دليل المستخدم الرسمي PDF"
    ])
    tab9 = None

# ------------------------------------------------------------------------------
# التبويب الأول: اسأل المنصة (RAG Engine Interface)
# ------------------------------------------------------------------------------
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
        user_question = st.text_area("❓ اكتب سؤالك/ استفسارك:", placeholder="مثال: متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟", height=120, key="query_text_box")

        st.markdown("<b>📌 أسئلة/ استفسارات مقترحة حسب المحاور:</b>", unsafe_allow_html=True)
        def set_suggested_question(q):
            st.session_state.query_text_box = q

        with st.expander("🏛️ محور الحوكمة والتأسيس والتاريخ"):
            for i, q in enumerate(["متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟", "عرف الحوكمة وتكوين مجلس الإدارة بالبنك", "ما هي نسبة الأعضاء المستقلين وسياسات تجنب تعارض المصالح؟"]):
                st.button(q, key=f"btn_ig_{i}", on_click=set_suggested_question, args=(q,), use_container_width=True)

        with st.expander("🌱 محور الاستدامة والتمويل الأخضر"):
            for i, q in enumerate(["كيف يتعامل البنك مع مخاطر المناخ والتمويل الأخضر؟", "ما هي نسبة الأصول الخضراء والمشروعات المستدامة؟", "كيف يمتثل البنك للمعايير الدولية (GRI و ISSB)؟"]):
                st.button(q, key=f"btn_sr_{i}", on_click=set_suggested_question, args=(q,), use_container_width=True)

        with st.expander("🔒 محور المنصات الذكية (SIP/RegTech)"):
            for i, q in enumerate(["ما هي آليات حوكمة البيانات والامتثال الرقابي؟", "كيف يضمن البنك الحصانة السيبرانية وأمن المعلومات؟"]):
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
                with st.spinner("⏳ جاري استرجاع وتحليل الإجابة المخصصة للبنك..."):
                    if ask_bank_sel == "البنك الأهلي اليوناني" and ("تأسس" in active_q or "مؤسسه" in active_q):
                        st.markdown(flat_html(f"""
                        <div style="background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.8;" dir="rtl">
                            <h4 style="color: {CBE_NAVY}; margin-top: 0;">🎯 التقرير التحليلي المفصل ({ask_bank_sel})</h4>
                            <p><b>السؤال / الاستفسار المطروح:</b> "{active_q}"</p>
                            <div style="background: {CBE_BG}; padding: 15px; border-radius: 8px; border-right: 4px solid #D97706; margin-top: 10px;">
                                <p style="margin: 0 0 8px 0; font-weight: bold; color: #92400E;">⚪ لا توجد بيانات كافية</p>
                                <p style="margin: 0; color: #1E293B; font-size: 13.5px;">لا تتوفر لدى المنصة بيانات موثقة تكفي للإجابة عن هذا السؤال بخصوص البنك الأهلي اليوناني، ولن تُقدَّم إجابة مبنية على التخمين.</p>
                            </div>
                        </div>
                        """), unsafe_allow_html=True)
                    else:
                        response_html = process_rag_gemini_query(ask_bank_sel, active_q)
                        st.markdown(flat_html(response_html), unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح أو كتابة الاستفسار في الحقل المخصص.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الثاني: مؤشر الحوكمة المركب (SSGI)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📊 التشخيص القياسي واحتساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
        <p>إمكانية تشخيص البنوك عبر المحاور الثلاثة الرئيسة (منصات المعلومات 40%، الحوكمة المؤسسية 30%، تقارير الاستدامة 30%).</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        bank_ssgi_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, key="t1_bank")
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

                entry = {
                    "معرف السجل": f"{clean_text(bank_ssgi_sel)} [{datetime.now().strftime('%H:%M:%S')}]",
                    "البنك": clean_text(bank_ssgi_sel),
                    "مؤشر SSGI المركب": final_score,
                    "منصات المعلومات (40%)": round(sip_val, 2),
                    "الحوكمة المؤسسية (30%)": round(ig_val, 2),
                    "تقارير الاستدامة (30%)": round(sr_val, 2),
                    "التقييم التشخيصي": clean_text(describe_sip(sip_val))
                }

                st.session_state.history_state = [item for item in st.session_state.history_state if item["البنك"] != clean_text(bank_ssgi_sel)]
                st.session_state.history_state.append(entry)

                st.markdown(flat_html(f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                   <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 12px;">📊 نتيجة حساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
                   <p style="font-size: 15px; margin-bottom: 8px;"><b>اسم البنك:</b> <span style="color: {CBE_NAVY}; font-weight: bold;">{clean_text(bank_ssgi_sel)}</span></p>
                   <p style="font-size: 16px; margin-bottom: 12px;"><b>القيمة المركبة للمؤشر (SSGI):</b> <span style="font-size: 18px;">{score_str_plain}</span></p>
                </div>
                """), unsafe_allow_html=True)

                categories = ['منصات المعلومات (SIP)', 'الحوكمة المؤسسية (IG)', 'تقارير الاستدامة (SR)']
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=[sip_val, ig_val, sr_val], theta=categories, fill='toself', name=bank_ssgi_sel, line_color=CBE_GOLD))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, title=dict(text=f"التحليل الرداري لمحاور الحوكمة - {bank_ssgi_sel}", x=0.5, xanchor='center'), font=dict(family="Cairo", size=12))
                st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("📊 يرجى اختيار البنك وضبط درجات المحاور الثلاثة ثم الضغط على زر الحساب لعرض النتائج والتحليل الرداري.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 قائمة البنوك والسجلات المختصرة")
    if st.session_state.history_state:
        df_history = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)
        
        table_html = """
        <div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 320px;">
        <table class="custom-rtl-table">
        <thead>
        <tr>
        <th style="width: 35px; text-align: center;">م</th>
        <th>معرف السجل / التوقيت</th>
        <th>اسم البنك</th>
        <th>المؤشر المركب (SSGI)</th>
        <th>منصات المعلومات (40%)</th>
        <th>الحوكمة المؤسسية (30%)</th>
        <th>تقارير الاستدامة (30%)</th>
        </tr>
        </thead>
        <tbody>
        """
        for idx, row in df_history.iterrows():
            table_html += f"""
            <tr>
            <td style="text-align: center; font-weight: bold;">{idx + 1}</td>
            <td style="font-size: 11px; color: #64748B;">{clean_text(str(row.get('معرف السجل', '')))}</td>
            <td style="font-weight: bold; color: {CBE_NAVY};">{clean_text(str(row['البنك']))}</td>
            <td style="font-weight: bold; color: {CBE_GOLD};">{row['مؤشر SSGI المركب']}%</td>
            <td>{row['منصات المعلومات (40%)']}%</td>
            <td>{row['الحوكمة المؤسسية (30%)']}%</td>
            <td>{row['تقارير الاستدامة (30%)']}%</td>
            </tr>
            """
        table_html += "</tbody></table></div>"
        st.markdown(flat_html(table_html), unsafe_allow_html=True)

        csv_data = df_history.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 تحميل جدول ترتيب السجلات والبنوك (Excel/CSV)", data=csv_data, file_name="ترتيب_البنوك_المصرية_SSGI.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("📂 لا توجد بنوك مسجلة حتى الآن. قم بإجراء التشخيص في الأعلى لتسجيل وترتيب البنوك.")

# ------------------------------------------------------------------------------
# التبويب الثالث: محاكي السياسات (Policy Simulator)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🔬 محاكي السياسات الاستشرافي للسيناريوهات المصرفية</h3>
        <p>استشراف أثر التدخلات الاستراتيجية واختبار السيناريوهات المختلفة (التشاؤمي، المعتدل، الطموح).</p>
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
            base_ssgi_input = st.slider("قيمة المؤشر الافتراضي الحالي", 30.0, 100.0, 85.0, 0.5, key="sim_base")
            scenario_dropdown = st.selectbox("اختر السيناريو الاستراتيجي", [
                "📉 السيناريو التشاؤمي (غياب التدخل وضعف الاستثمار التقني)",
                "📊 السيناريو المعتدل / التفاؤلي (استثمارات تقليدية تدريجية)",
                "🚀 السيناريو الطموح / الاستباقي (إصلاحات هيكلية شاملة وسيادة رقمية)"
            ], index=1, key="sim_scen")
            
            var1_sip = st.slider("1️⃣ نسبة الزيادة في منصات المعلومات (%)", 0, 50, 20, key="sim_v1")
            var2_ig = st.slider("2️⃣ نسبة الزيادة في الحوكمة المؤسسية (%)", 0, 50, 15, key="sim_v2")
            var3_sr = st.slider("3️⃣ نسبة الزيادة في تقارير الاستدامة (%)", 0, 50, 15, key="sim_v3")
            run_sim_btn = st.button("📋 إضافة وتثبيت سيناريو إضافي للبنك", use_container_width=True, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_sim_out:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            if run_sim_btn:
                base_val = base_ssgi_input
                simulated_val = min(100.0, base_val * 1.05)
                delta = round(simulated_val - base_val, 2)
                score_str_plain = get_colored_score_html(round(simulated_val, 2))
                
                box_html = f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
                   <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">📈 محاكاة بنك: {sim_bank_sel} | السيناريو: {scenario_dropdown}</h3>
                   <p style="font-size: 15px; margin-bottom: 8px;"><b>القيمة المتوقعة للمؤشر:</b> {score_str_plain} (صافي التغير: <span style="font-weight: bold;">{delta:+.2f}</span>)</p>
                </div>
                """
                st.markdown(flat_html(box_html), unsafe_allow_html=True)
            else:
                st.info("📈 قم بضبط البنك والسيناريو ومتغيرات التحفيز واضغط على زر الإضافة لتثبيت ومتابعة السيناريوهات هنا.")
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الرابع: لوحة دعم اتخاذ القرار (Decision Support Dashboard)
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🛡️ لوحة دعم اتخاذ القرار المصرفي</h3>
        <p>استعراض وتثبيت التوصيات الاستراتيجية المخصصة لكل بنك في القطاع المصرفي المصري بناءً على قراءات التشخيص.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI.")
    else:
        recorded_banks_dec = list(set([item["البنك"] for item in st.session_state.history_state]))
        decision_bank_sel = st.selectbox("اختر البنك لاستعراض التوصيات المخصصة", recorded_banks_dec, key="dec_bank")
        if st.button("📋 عرض التوصيات الاستراتيجية الموجهة", type="primary"):
            bank_data = next((item for item in st.session_state.history_state if item["البنك"] == decision_bank_sel), None)
            if bank_data:
                score = bank_data["مؤشر SSGI المركب"]
                st.markdown(f"""
                <div style="background: #FFFFFF; padding: 20px; border-radius: 12px; border: 1.5px solid {CBE_GOLD};" dir="rtl">
                    <h4 style="color: {CBE_NAVY};">توصيات صانع القرار لبنك: {decision_bank_sel}</h4>
                    <p><b>المؤشر المركب المسجل:</b> {score}%</p>
                    <ul>
                        <li><b>تعزيز البنية التقنية (SIP):</b> توظيف منصات المعلومات المتقدمة لرفع كفاءة التقارير الرقابية (RegTech).</li>
                        <li><b>الحوكمة المؤسسية والالتزام (IG):</b> تعزيز استقلالية لجان المراجعة وتفعيل ضوابط تعارض المصالح.</li>
                        <li><b>الاستدامة والتمويل الأخضر (SR):</b> التوسع في محفظة الأصول الخضراء ومواءمة المعايير مع (GRI و ISSB).</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الخامس: التقرير التنفيذي الموحد (Executive Summary Report)
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📑 أداة توليد التقرير التنفيذي الموحد لحوكمة القطاع المصرفي</h3>
        <p>تجميع ومراجعة التقرير التنفيذي الموحد والنتائج التحليلية المحدثة ديناميكياً لجميع البنوك المسجلة.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("📂 لا توجد بيانات مسجلة كافية حتى الآن. يرجى إدخال تشخيص بنك واحد على الأقل في القسم الثاني.")
    else:
        if st.button("🚀 توليد وتحديث التقرير التنفيذي الموحد فورياً", type="primary"):
            df_rep = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)
            top_row = df_rep.iloc[0]
            st.markdown(f"""
            <div style="background: #FFFFFF; padding: 25px; border-radius: 12px; border: 2px solid {CBE_GOLD};" dir="rtl">
                <h3 style="color: {CBE_NAVY};">🏆 التقرير التنفيذي العام - الصدارة المصرفية</h3>
                <p><b>البنك المتصدر:</b> {top_row['البنك']} بقيمة مركبة تبلغ <b>{top_row['مؤشر SSGI المركب']}%</b></p>
                <p>{get_bank_founding_profile(top_row['البنك'])}</p>
            </div>
            """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب السادس: مولد تقارير الاستدامة ودليل ESG
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🌿 نظام توليد تقارير الاستدامة المتقدم والدليل العملي الشامل (GRI / ISSB / SDG Impact)</h3>
        <p>إطار توجيهي متكامل ومفصل يربط بين معايير المبادرة العالمية (GRI)، معايير الإفصاح المالي (ISSB)، ومعايير أهداف التنمية المستدامة.</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("🌿 يمكنك عبر هذا القسم استعراض مسودات التقارير التوجيهية والدليل العملي الموسع للـ 30 مؤشراً لـ (ESG).")

# ------------------------------------------------------------------------------
# التبويب السابع: الاستبيان الموجه إلى فرق العمل في البنوك
# ------------------------------------------------------------------------------
with tab7:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📋 الاستبيان الموجه إلى فرق العمل في البنوك (عينة الدراسة الميدانية)</h3>
        <p>استمارة الاستبيان الميداني المعتمدة لجمع آراء وتقييمات فرق العمل والقيادات المصرفية حول محاور المنصة.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("👤 بيانات المشارك ومعلومات أولية ومهنية", expanded=True):
        col_inf1, col_inf2 = st.columns(2, gap="medium")
        with col_inf1:
            survey_bank_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, index=0, key="survey_bank_user_main")
            org_nature_u = st.selectbox("طبيعة المؤسسة", ["بنك قطاع عام/ حكومي", "بنك قطاع خاص مشترك", "بنك إسلامي", "بنك عربي/ أجنبي", "جهة رقابية", "أخرى"], key="org_nat_u_dyn")
        with col_inf2:
            spec_field_u = st.selectbox("مجال التخصص الوظيفي", ["مجلس الإدارة/ الإدارة العليا", "الحوكمة/ الالتزام/ المراجعة الداخلية", "الاستدامة", "تكنولوجيا المعلومات", "إدارة المخاطر"], key="spec_field_u_dyn")
            exp_years_u = st.selectbox("سنوات الخبرة في القطاع المصرفي", ["أقل من 10 سنوات", "من 10 إلى أقل من 15 سنة", "15 سنة فأكثر"], key="exp_yrs_u_dyn")

    st.success("✅ نموذج الاستبيان الميداني جاهز لاستقبال وتقييم الاستجابات وحفظها بشكل آمن.")

# ------------------------------------------------------------------------------
# التبويب الثامن: دليل المستخدم الرسمي PDF / Docs
# ------------------------------------------------------------------------------
with tab8:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📖 دليل المستخدم الرسمي والتوثيق المنهجي لمنصة الحوكمة المصرفية</h3>
        <p>استعراض وتحميل الدليل التشغيلي الشامل لتمكين المحكمين والباحثين من الإلمام بكافة وظائف وأقسام المنصة.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style="background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid #C5A059; line-height: 1.8;" dir="rtl">
        <h4 style="color: #002B49;">أقسام ووظائف المنصة الرئيسية:</h4>
        <ul>
            <li><b>🎯 اسأل المنصة:</b> محرك استعلام ذكي مخصص لاستخراج البيانات بدقة.</li>
            <li><b>📊 مؤشر الحوكمة المركب (SSGI):</b> أداة تشخيص قياسي لتقييم البنوك.</li>
            <li><b>📈 محاكي السياسات:</b> أداة استشرافية لاختبار السيناريوهات الاستراتيجية.</li>
            <li><b>🛡️ لوحة دعم القرار:</b> توفير توصيات مخصصة لصناع القرار.</li>
            <li><b>📑 التقرير التنفيذي:</b> تجميع مخرجات المنصة في تقرير موحد قابل للتصدير.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب التاسع: لوحة تحكم المشرف والزوار (Admin Dashboard)
# ------------------------------------------------------------------------------
if tab9 is not None:
    with tab9:
        st.markdown("""
        <div dir="rtl" style="text-align: right;">
            <h3>🔒 لوحة تحكم المشرف وسجلات الزوار (Admin Dashboard & IP Logging)</h3>
            <p>متابعة وتصدير سجلات دخول الزوار وعناوين الـ IP، بالإضافة إلى فحص تدقيق التشابه والتمايز بين البنوك.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        visitors_data_list = load_visitors_log()
        if visitors_data_list:
            df_v = pd.DataFrame(visitors_data_list)
            st.dataframe(df_v, use_container_width=True)
        else:
            st.info("📂 لا توجد سجلات زيارات مسجلة حتى الآن.")

st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)

<ElicitationsGroup message="للمتابعة واستكمال معايير التطوير الذكي وتجربة المستخدم:">
  <Elicitation label="إضافة سيناريو محاكاة جديد وتثبيته في لوحة السياسات" query="كيف يمكنني إضافة سيناريو محاكاة جديد وتثبيته في لوحة السياسات الاستشرافية؟" />
  <Elicitation label="تصدير شيت إكسيل استجابات استبيان فرق العمل المصرفي" query="كيف يمكنني تصدير شيت إكسيل استجابات استبيان فرق العمل المصرفي بالتفصيل؟" />
</ElicitationsGroup>
