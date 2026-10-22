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
# الدوال المساعدة المحدثة (Flat HTML & Clean Text) لمنع تحول النصوص لكود
# ==============================================================================
def flat_html(s: str) -> str:
    """يحذف المسافات البادئة والأسطر الفارغة حتى لا يفسّرها Markdown ككود، واضعاً مسافة للفصل الآمن."""
    return " ".join(l.strip() for l in s.splitlines() if l.strip())

def clean_text(text) -> str:
    """ينزع الوسوم الدخيلة وعلامات [cite] ويحافظ على الإيموجي والرموز."""
    if not isinstance(text, str):
        return str(text)
    t = re.sub(r"\[cite[^\]]*\]", "", text)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\xa0", " ").replace("\u200b", "")
    return re.sub(r"\s+", " ", t).strip()

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
                <h2 style="color: {CBE_NAVY}; text-align: center; font-weight: 800; margin-bottom: 10px;">🏛️ مقترح المنصة الوطنية الذكية لحوكمة القطاع المصرفي</h2>
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
    <span class="ticker-item">| 📊 مؤشر الحوكمة الذكية المستدامة (SSGI) والأبعاد الثلاثة الرئيسة</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي لاختبار السيناريوهات الاستراتيجية (Multiple Regression)</span>
    <span class="ticker-item">| 🛡️ لوحة دعم اتخاذ القرار </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# التبويبات الرئيسة
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
        "📊 مؤشر الحوكمة المركب (SSGI)", 
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
                with st.spinner("⏳ جاري استرجاع وتحليل الإجابة المخصصة للبنك..."):
                    if ask_bank_sel == "البنك الأهلي اليوناني":
                        if "تأسس" in active_q or "مؤسسه" in active_q:
                            st.markdown(flat_html(f"""
                            <div style="background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.8;" dir="rtl">
                                <h4 style="color: {CBE_NAVY}; margin-top: 0;">🎯 التقرير التحليلي المفصل ({ask_bank_sel})</h4>
                                <p><b>السؤال / الاستفسار المطروح:</b> "{active_q}"</p>
                                <div style="background: {CBE_BG}; padding: 15px; border-radius: 8px; border-right: 4px solid #D97706; margin-top: 10px;">
                                    <p style="margin: 0 0 8px 0; font-weight: bold; color: #92400E;">⚪ لا توجد بيانات كافية</p>
                                    <p style="margin: 0; color: #1E293B; font-size: 13.5px;">
                                    لا تتوفر لدى المنصة بيانات موثقة تكفي للإجابة عن هذا السؤال بخصوص البنك الأهلي اليوناني، ولن تُقدَّم إجابة مبنية على التخمين.
                                    </p>
                                </div>
                            </div>
                            """), unsafe_allow_html=True)
                        else:
                            response_html = process_rag_gemini_query(ask_bank_sel, active_q)
                            st.markdown(flat_html(response_html), unsafe_allow_html=True)
                    else:
                        response_html = process_rag_gemini_query(ask_bank_sel, active_q)
                        st.markdown(flat_html(response_html), unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح أو كتابة السؤال/ الاستفسار.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الثاني: مؤشر الحوكمة المركب (SSGI)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🗳️ التشخيص القياسي واحتساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
        <p>إمكانية تشخيص البنوك عبر المحاور الثلاثة الرئيسة.</p>
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

                def get_sr_comment(val):
                    if val >= 80:
                        return f"سجل البنك ({val}%)، مما يعكس أداءً متميزاً والتزاماً ريادياً في دمج معايير (GRI و ISSB)، والتوسع الفعال في محفظة التمويل المستدام والأصول الخضراء ومخاطر المناخ."
                    elif val >= 50:
                        return f"سجل البنك ({val}%)، مما يعكس أداءً متوسطاً يتطلب التوسع في محفظة التمويل المستدام ومخاطر المناخ."
                    else:
                        return f"سجل البنك ({val}%)، مما يعكس ضعفاً هيكلياً في ملف الاستدامة والتمويل الأخضر يعيق امتثال البنك للمعايير الدولية."

                def get_sip_comment(val):
                    if val >= 80:
                        return f"سجل البنك ({val}%)، وهو ما يعكس بنية تحتية رقمية متقدمة، تكاملاً تاماً مع الأنظمة الرقابية الآلية للبنك المركزي، وحوكمة فائقة للخوارزميات والبيانات."
                    elif val >= 50:
                        return f"سجل البنك ({val}%)، مما يشير إلى بنية رقمية متوسطة الكفاءة تحتاج إلى تحديث سعات تدفق البيانات وتوطين تقارير (RegTech)."
                    else:
                        return f"سجل البنك ({val}%)، وهو مستوى يعيق أتمتة الالتزام والرقابة التنظيمية ويشكل خطراً على السيادة الرقمية وأمن البيانات."

                def get_ig_comment(val):
                    if val >= 80:
                        return f"سجل البنك ({val}%)، مما يعبر عن استقلالية تامة لمجلس الإدارة ولجان المراجعة وإدارة المخاطر، والالتزام الصارم بسياسات الإفصاح والشفافية وتجنب تعارض المصالح."
                    elif val >= 50:
                        return f"سجل البنك ({val}%)، وهو ما يتطلب تفعيل ضوابط تعارض المصالح وتعزيز دور الأعضاء المستقلين في هيكل اللجان."
                    else:
                        return f"سجل البنك ({val}%)، مما يعكس قصوراً حاداً في هيكل الصلاحيات والتدقيق الداخلي يتطلب إعادة هندسة شاملة."

                if final_score >= 80:
                    diagnosis = "🟢 أداء مصرفي مرتفع ومنتظم، نحو الريادة والسيادة الرقمية المستدامة."
                    detailed_diag = f"""
                    <div style="line-height: 1.8; font-size: 14.5px;">
                        <p>🟢 <b>جاهزية متقدمة ومستدامة (أداء ممتاز):</b> بلغت القيمة المركبة لمؤشر الحوكمة الذكية المستدامة (SSGI) للبنك: <b>{score_str_plain}</b>.</p>
                        <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 8px 0;">
                        <p><b>🔍 التفصيل والتشخيص المعمق للمحاور:</b></p>
                        <ul style="margin: 0; padding-right: 20px;">
                            <li><b>منصات المعلومات الذكية (SIP - وزن 40%):</b> {get_sip_comment(sip_val)}</li>
                            <li><b>الحوكمة المؤسسية والامتثال (IG - وزن 30%):</b> {get_ig_comment(ig_val)}</li>
                            <li><b>تقارير الاستدامة والتمويل الأخضر (SR - وزن 30%):</b> {get_sr_comment(sr_val)}</li>
                        </ul>
                    </div>
                    """
                elif final_score >= 51:
                    diagnosis = "🟡 أداء متوسط، يتطلب تعزيزاً استباقياً لمعالجة الفجوات الهيكلية."
                    detailed_diag = f"""
                    <div style="line-height: 1.8; font-size: 14.5px;">
                        <p>🟡 <b>جاهزية متوسطة تتطلب تدخلاً استباقياً:</b> بلغت القيمة المركبة لمؤشر الحوكمة الذكية المستدامة (SSGI) للبنك: <b>{score_str_plain}</b>.</p>
                        <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 8px 0;">
                        <p><b>🔍 التفصيل والتشخيص المعمق للمحاور:</b></p>
                        <ul style="margin: 0; padding-right: 20px;">
                            <li><b>منصات المعلومات الذكية (SIP - وزن 40%):</b> {get_sip_comment(sip_val)}</li>
                            <li><b>الحوكمة المؤسسية والامتثال (IG - وزن 30%):</b> {get_ig_comment(ig_val)}</li>
                            <li><b>تقارير الاستدامة والتمويل الأخضر (SR - وزن 30%):</b> {get_sr_comment(sr_val)}</li>
                        </ul>
                    </div>
                    """
                else:
                    diagnosis = "🔴 فجوة هيكلية حرجة تستوجب التدخل الفوري وتفعيل محاكي السياسات."
                    detailed_diag = f"""
                    <div style="line-height: 1.8; font-size: 14.5px;">
                        <p>🔴 <b>فجوة هيكلية حرجة تستوجب التدخل الفوري:</b> بلغت القيمة المركبة لمؤشر الحوكمة الذكية المستدامة (SSGI) للبنك: <b>{score_str_plain}</b>.</p>
                        <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 8px 0;">
                        <p><b>🔍 التفصيل والتشخيص المعمق للمحاور:</b></p>
                        <ul style="margin: 0; padding-right: 20px;">
                            <li><b>منصات المعلومات الذكية (SIP - وزن 40%):</b> {get_sip_comment(sip_val)}</li>
                            <li><b>الحوكمة المؤسسية والامتثال (IG - وزن 30%):</b> {get_ig_comment(ig_val)}</li>
                            <li><b>تقارير الاستدامة والتمويل الأخضر (SR - وزن 30%):</b> {get_sr_comment(sr_val)}</li>
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
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                  <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 12px;">📊 نتيجة حساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
                  <p style="font-size: 15px; margin-bottom: 8px;"><b>اسم البنك:</b> <span style="color: {CBE_NAVY}; font-weight: bold;">{clean_text(bank_ssgi_sel)}</span></p>
                  <p style="font-size: 16px; margin-bottom: 12px;"><b>القيمة المركبة للمؤشر (SSGI):</b> <span style="font-size: 18px;">{score_str_plain}</span></p>
                  <div style="background: {CBE_BG}; padding: 16px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 10px;">
                    <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY};">التشخيص القياسي:</p>
                    <div style="color: #1E293B;">{detailed_diag}</div>
                  </div>
                </div>
                """), unsafe_allow_html=True)

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
    
    st.markdown("### 📋 قائمة البنوك والسجلات المختارة (تقتصر على ذكر البنك مرة واحدة حسب آخر تعديل)")
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
        <th>التقييم التشخيصي</th>
        </tr>
        </thead>
        <tbody>
        """
        
        for idx, row in df_history.iterrows():
            clean_bank_name = clean_text(str(row['البنك']))
            clean_diag = clean_text(str(row['التقييم التشخيصي']))
            rec_id = clean_text(str(row.get('معرف السجل', idx)))
            table_html += f"""
            <tr>
            <td style="text-align: center; font-weight: bold;">{idx + 1}</td>
            <td style="font-size: 11px; color: #64748B;">{rec_id}</td>
            <td style="font-weight: bold; color: {CBE_NAVY};">{clean_bank_name}</td>
            <td style="font-weight: bold; color: {CBE_GOLD};">{row['مؤشر SSGI المركب']}%</td>
            <td>{row['منصات المعلومات (40%)']}%</td>
            <td>{row['الحوكمة المؤسسية (30%)']}%</td>
            <td>{row['تقارير الاستدامة (30%)']}%</td>
            <td style="font-size: 11.5px;">{clean_diag}</td>
            </tr>
            """
        table_html += """
        </tbody>
        </table>
        </div>
        """
        st.markdown(flat_html(table_html), unsafe_allow_html=True)

        csv_data = df_history.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تحميل جدول ترتيب السجلات والبنوك (Excel/CSV)",
            data=csv_data,
            file_name="ترتيب_البنوك_المصرية_SSGI.csv",
            mime="text/csv",
            use_container_width=True
        )

        col_del1, col_del2 = st.columns([2, 1])
        with col_del1:
            recorded_ids = [item.get("معرف السجل", item["البنك"]) for item in st.session_state.history_state]
            id_to_delete = st.selectbox("اختر السجل المحدد لحذفه", recorded_ids, key="del_rec_box")
        with col_del2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ حذف السجل المحدد", use_container_width=True, type="secondary"):
                st.session_state.history_state = [item for item in st.session_state.history_state if item.get("معرف السجل", item["البنك"]) != id_to_delete]
                st.success("✅ تم حذف السجل بنجاح.")
                st.rerun()
    else:
        st.info("📂 لا توجد بنوك مسجلة حتى الآن. قم إجراء التشخيص في الأعلى لتسجيل وترتيب البنوك.")

    st.markdown("---")
    
    with st.expander("📂 استعراض المصفوفة الهرمية والمحاور الرئيسة والأبعاد والعناصر الفرعية لمؤشر الحوكمة (SSGI)", expanded=False):
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
        st.markdown(flat_html(hierarchy_table_html), unsafe_allow_html=True)

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
# التبويب الثالث: محاكي السياسات (Policy Simulator)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🔬 محاكي السياسات الاستشرافي للسيناريوهات المصرفية</h3>
        <p>استشراف أثر التدخلات.</p>
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
            
            var1_sip = st.slider("1️⃣ نسبة الزيادة في منصات المعلومات والبنية التقنية (%)", 0, 50, 20, key="sim_v1")
            var2_ig = st.slider("2️⃣ نسبة الزيادة في كفاءة الحوكمة المؤسسية (%)", 0, 50, 15, key="sim_v2")
            var3_sr = st.slider("3️⃣ نسبة الزيادة في تقارير الاستدامة والتمويل الأخضر (%)", 0, 50, 15, key="sim_v3")

            run_sim_btn = st.button("📋 إضافة وتثبيت سيناريو إضافي للبنك", use_container_width=True, type="primary")
            
            if st.button("🗑️ مسح وإعادة تعيين كافة سيناريوهات المحاكي", use_container_width=True, type="secondary"):
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
                <h3>📋 عرض السيناريوهات للبنوك:</h3>
            """
            if st.session_state.simulated_results_dict:
                for k, v in st.session_state.simulated_results_dict.items():
                    sim_word_html += f"""
                    <div style="border: 1px solid #CBD5E1; padding: 15px; margin-bottom: 15px; border-radius: 8px;">
                        <h4>معرف السيناريو: {k}</h4>
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
                        <p style="font-weight: bold; color: {CBE_NAVY}; margin-bottom: 8px; text-align: right;">📊 التشخيص القياسي المخصص لبنك ({sim_bank_sel}):</p>
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
                    
                    sim_key = f"{sim_bank_sel} - {scenario_dropdown} [{datetime.now().strftime('%H:%M:%S')}]"
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
                st.markdown("<h4>📋 مقارنة السيناريوهات المتعددة المثبتة للبنوك:</h4>", unsafe_allow_html=True)
                for s_key, item in st.session_state.simulated_results_dict.items():
                    st.markdown(f"<span style='color: #64748B; font-size: 12px;'>معرف السيناريو: {s_key}</span>", unsafe_allow_html=True)
                    st.markdown(flat_html(item["html"]), unsafe_allow_html=True)
                    st.markdown(flat_html(item["deep"]), unsafe_allow_html=True)
                    st.markdown("---")
            else:
                st.info("📈 قم بضبط البنك والسيناريو ومتغيرات التحفيز واضغط على زر الإضافة لتثبيت ومتابعة عدة سيناريوهات هنا بغرض المقارنة.")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الرابع: لوحة دعم اتخاذ القرار
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🛡️ لوحة دعم اتخاذ القرار المصرفي</h3>
        <p>استعراض وتثبيت التوصيات الاستراتيجية المخصصة لكل بنك في القطاع المصرفي.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI في القسم الأول.")
    else:
        col_dec_in, col_dec_out = st.columns([1, 2], gap="large")

        with col_dec_in:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            recorded_banks_dec = list(set([item["البنك"] for item in st.session_state.history_state]))
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
                                f"<b>الحوكمة المؤسسية المتقدمة:</b> استثمار رصيد لجان المراجعة واللتزام ({i_val}%) لقيادة تطبيق أحدث نظم الرقابة التنظيمية (RegTech)."
                            ]
                        elif score >= 51:
                            recs_list = [
                                f"<b>تطوير البنية والمؤسسية لـ ({decision_bank_sel}):</b> تحسين كفاءة منصات المعلومات بناءً على قراءة ({s_val}%).",
                                f"<b>دعم منظومة الالتزام:</b> تعزيز دور لجان المراجعة وإدارة المخاطر لتحسين مؤشر الحوكمة المسجل عند ({i_val}%)."
                            ]
                        else:
                            recs_list = [
                                f"<b>التدخل الاستباقي العاجل لـ ({decision_bank_sel}):</b> معالجة الاختناقات الهيكلية الحرجة في البنية التقنية ومنصات المعلومات ({s_val}%).",
                                f"<b>إعادة هيكلة أطر الحوكمة:</b> تفعيل التزام تام بتعليمات البنك المركزي ورفع كفاءة التدقيق الداخلي ({i_val}%)."
                            ]

                        if r_val >= 80:
                            sustainability_comment = f"الحفاظ على الأداء المتميز وتوسيع محفظة الأصول الخضراء والتمويل المستدام استناداً للججاهزية المرتفعة في الاستدامة ({r_val}%)."
                        elif r_val >= 50:
                            sustainability_comment = f"الاستمرار في توجيه الائتمان المصرفي نحو المشروعات الخضراء لتعزيز الأداء في الاستدامة ({r_val}%)."
                        else:
                            sustainability_comment = f"إطلاق برامج عاجلة لتطوير الإفصاح المالي وغير المالي وفق معايير الاستدامة لتعويض الضعف في ({r_val}%)."

                        deep_items = [
                            f"يتطلب متخذ القرار تفعيل <b>'برامج الرقابة التنظيمية الآلية والذكية'</b> لرفع كفاءة تدفق البيانات والتقارير الرقابية استناداً إلى قراءة منصات المعلومات ({s_val}%).",
                            sustainability_comment,
                            f"تحديث أطر إدارة المخاطر الكلية والتحوط المرن بالتوازي مع متطلبات الحوكمة ({i_val}%)."
                        ]
                        deep_analysis_text = "<ul style='margin:0;padding-right:20px;'>" + "".join(f"<li>{x}</li>" for x in deep_items) + "</ul>"

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
                            <div style="color: #1E293B; line-height: 1.8; text-align: right; padding-right: 0;">
                                {item['deep']}
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(flat_html(card_html), unsafe_allow_html=True)
            else:
                st.info("🛡️ يرجى اختيار البنك المسجل والضغط على زر الإضافة لتثبيت التوصيات هنا.")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الخامس: التقرير التنفيذي الموحد
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📑 أداة توليد التقرير التنفيذي الموحد لحوكمة القطاع المصرفي</h3>
        <p>قم بالضغط على زر التوليد الفوري أدناه لتجميع ومراجعة التقرير التنفيذي الموحد والنتائج التحليلية المحدثة ديناميكياً.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("📂 لا توجد بيانات مسجلة كافية حتى الآن. يرجى إدخال تشخيص بنك واحد على الأقل في القسم الثاني لتفعيل التقرير التنفيذي.")
    else:
        generate_exec_report = st.button("🚀 توليد وتحديث التقرير التنفيذي الموحد فورياً", use_container_width=True, type="primary")

        if "show_exec_report" not in st.session_state:
            st.session_state.show_exec_report = False

        if generate_exec_report:
            st.session_state.show_exec_report = True

        if st.session_state.show_exec_report:
            df_rep = pd.DataFrame(st.session_state.history_state).sort_values(
                by="مؤشر SSGI المركب", ascending=False
            ).reset_index(drop=True)
            
            top_row = df_rep.iloc[0]
            top_bank = top_row["البنك"]
            top_score = top_row["مؤشر SSGI المركب"]
            top_score_str = get_colored_score_html(top_score)
            top_bank_profile_info = get_bank_founding_profile(top_bank)

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

                matched_sims = {s_key: s_val_obj for s_key, s_val_obj in st.session_state.simulated_results_dict.items() if s_val_obj['bank'] == b_name}
                if matched_sims:
                    sim_details_list = []
                    for s_key, sim_data_obj in matched_sims.items():
                        sim_details_list.append(
                            f"• <b>السيناريو ({sim_data_obj['scenario']}):</b> القيمة المتوقعة ({sim_data_obj['simulated_val']}%) بصافي تغير ({sim_data_obj['delta']:+.2f}). "
                            f"<i>التحليل:</i> {sim_data_obj['analysis_text']} "
                            f"<i>خطة التحرك:</i> {sim_data_obj['action_plan']}"
                        )
                    sim_detail = "<br>".join(sim_details_list)
                else:
                    sim_detail = "<span style='background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #FCD34D;'>⚠️ لم يتم تسجيل سيناريوهات استشرافية لهذا البنك.</span>"
                
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
                        <li style="margin-top: 8px;"><b>🔬 مخرجات محاكي السياسات الاستشرافي (السيناريوهات المسجلة):</b><br>{sim_detail}</li>
                        <li style="margin-top: 8px;"><b>🛡️ مخرجات لوحة دعم القرار والسياسات:</b><br>{dec_detail}</li>
                    </ul>
                </div>
                """
                cards_html_list.append(single_card_html)
                word_blocks_html += single_card_html

            header_html = f"""
            <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 30px; border-radius: 14px; border: 2px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 6px 20px rgba(0,0,0,0.08);">
              <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 15px; margin-bottom: 25px;">
                <h2 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">📑 التقرير التنفيذي الموحد لحوكمة القطاع المصرفي وتقارير الاستدامة</h2>
                <p style="color: #64748B; font-size: 14.5px; margin-top: 6px;">ملخص استراتيجي موجه للقيادات العليا وصناع القرار - بناءً على معطيات ومخرجات (SSGI)</p>
              </div>
            """

            top_block_html = f"""
            <div style="background: {CBE_BG}; padding: 18px; border-radius: 10px; border-right: 5px solid {CBE_GOLD}; margin-bottom: 25px;" dir="rtl">
                <h4 style="color: {CBE_NAVY}; margin-top: 0;">🏆 مؤشرات الأداء العام والريادة المصرفية:</h4>
                <p style="margin-bottom: 8px;">يتصدّر البنك التالي قائمة الحوكمة الذكية المستدامة وفق الترتيب التنازلي للمؤشر المركب: <span style="font-weight: bold; color: {CBE_GOLD};">{top_bank}</span> بقيمة مركبة تبلغ {top_score_str}.</p>
                <div style="background: #FFFFFF; padding: 12px; border-radius: 6px; border: 1px solid #CBD5E1; margin-top: 10px; margin-bottom: 10px;">
                    <p style="margin: 0 0 6px 0; color: {CBE_NAVY}; font-weight: bold;">🏛️ الملامح التأسيسية والمعطيات التاريخية للبنك المتصدر ({top_bank}):</p>
                    <p style="margin: 0; color: #334155; font-size: 13.5px; line-height: 1.7;">{top_bank_profile_info}</p>
                </div>
                <p style="margin: 0;">إجمالي البنوك والسجلات الخاضعة للتشخيص والتحليل المنظومي حتى الآن: <b>{len(df_rep)} سجل مصرفي</b>.</p>
            </div>
            <h4 style='color: #002B49; margin-bottom: 12px;'>📋 ترتيب الملخص التراكمي للبنوك:</h4>
            """

            summary_cards = []
            for idx, row in df_rep.iterrows():
                s = row['مؤشر SSGI المركب']
                s_str = get_colored_score_html(s)
                summary_card = f"""
                <div style="margin-bottom: 12px; line-height: 1.8; background: #F8FAFC; padding: 12px 16px; border-radius: 8px; border: 1px solid #E2E8F0;" dir="rtl">
                    <b>المركز ({idx + 1}): {row['البنك']}</b> — المؤشر المركب: {s_str} | منصات المعلومات: {row['منصات المعلومات (40%)']}% | الحوكمة: {row['الحوكمة المؤسسية (30%)']}% <br>
                    <span style="color: #475569; font-size: 13.5px;"><b>التقييم التشخيصي:</b> {row['التقييم التشخيصي']}</span>
                </div>
                """
                summary_cards.append(summary_card)

            report_html = header_html + top_block_html + "".join(summary_cards) + "".join(cards_html_list) + "</div>"
            st.markdown(flat_html(report_html), unsafe_allow_html=True)

            word_content = f"""
            <html dir="rtl">
            <head><meta charset="utf-8"><title>التقرير التنفيذي الموحد للقطاع المصرفي</title></head>
            <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
                <h1 style="color: {CBE_NAVY}; text-align: center;">📑 التقرير التنفيذي الموحد لحوكمة القطاع المصرفي وتقارير الاستدامة</h1>
                <p style="text-align: center; color: #64748B;">ملخص استراتيجي موجه للقيادات العليا وصناع القرار (SSGI)</p>
                <hr>
                <h3>🏆 مؤشرات الأداء العام والريادة المصرفية:</h3>
                <p>يتصدّر البنك التالي قائمة الحوكمة الذكية المستدامة: <b>{top_bank}</b> بقيمة مركبة تبلغ {top_score_str}.</p>
                <p><b>معطيات وتاريخ التأسيس:</b> {top_bank_profile_info}</p>
                <p>إجمالي البنوك والسجلات الخاضعة للتشخيص والتحليل المنظومي: <b>{len(df_rep)} سجل مصرفي</b>.</p>
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

# ------------------------------------------------------------------------------
# التبويب السادس الموسع: مولد تقارير الاستدامة (GRI / ISSB) والدليل العملي الشامل
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🌿 القسم السادس الموسع: نظام توليد تقارير الاستدامة المتقدم والدليل العملي الشامل (GRI / ISSB / SDG Impact)</h3>
        <p>إطار توجيهي متكامل ومفصل للقطاع المصرفي المصري يربط بين معايير المبادرة العالمية (GRI Standards)، معايير الإفصاح المالي الدولي (ISSB S1/S2), معايير تأثير أهداف التنمية المستدامة (SDG Impact Standards)، و30 مؤشراً مقترحاً للأداء البيئي والمجتمعي والحوكمة (ESG).</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📋 1. توليد مسودة تقارير الاستدامة التوجيهية التفصيلية للبنك المختار")

    all_registered_banks = (
        list(set([item["البنك"] for item in st.session_state.history_state]))
        if st.session_state.history_state
        else []
    )

    if not all_registered_banks:
        st.warning("⚠️ يرجى أولاً إدخال وتسجيل بيانات بنك واحد على الأقل في (قسم مؤشر الحوكمة SSGI) لتفعيل مولد المسودة المخصصة.")
    else:
        col_gen1, col_gen2 = st.columns([2, 1])
        with col_gen1:
            selected_bank_for_report = st.selectbox(
                "اختر البنك لتوليد مسودة تقرير الاستدامة المخصصة والتفصيلية",
                all_registered_banks,
                key="rep_bank_sel",
            )
        with col_gen2:
            st.markdown("<br>", unsafe_allow_html=True)
            generate_draft_btn = st.button(
                "🌿 توليد المسودة التوجيهية الشاملة والمفصلة",
                use_container_width=True,
                type="primary",
            )

        if generate_draft_btn:
            st.session_state.draft_generated_state = True
            st.session_state.draft_bank_name = selected_bank_for_report

        if st.session_state.draft_generated_state and st.session_state.draft_bank_name in all_registered_banks:
            bank_record = next(
                (
                    item
                    for item in st.session_state.history_state
                    if item["البنك"] == st.session_state.draft_bank_name
                ),
                None,
            )
            if bank_record:
                b_name = bank_record["البنك"]
                b_score = bank_record["مؤشر SSGI المركب"]
                s_val = bank_record["منصات المعلومات (40%)"]
                i_val = bank_record["الحوكمة المؤسسية (30%)"]
                r_val = bank_record["تقارير الاستدامة (30%)"]
                profile_info = get_bank_founding_profile(b_name)

                detailed_draft_html = f"""
                <div style="background: #FFFFFF; padding: 35px; border-radius: 14px; border: 2px solid {CBE_GOLD}; line-height: 2.0; box-shadow: 0 6px 20px rgba(0,0,0,0.08);" dir="rtl">
                    <div style="text-align: center; border-bottom: 2.5px solid {CBE_GOLD}; padding-bottom: 20px; margin-bottom: 30px;">
                        <h2 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">🌿 مسودة تقرير الاستدامة والإفصاح المالي المتقدم (GRI / ISSB / SDG Impact)</h2>
                        <h3 style="color: {CBE_GOLD}; margin-top: 8px;">مستند توجيهي استرشادي مخصص وشامل لـ: {b_name}</h3>
                        <p style="color: #64748B; font-size: 13.5px; margin-top: 5px;"><b>⚠️ تنبيه إرشادي هام:</b> هذه المسودة تعتبر دليلاً توجيهياً استرشادياً مبنياً على المعطيات والتشخيص المرصود بالمنصة الوطنية الذكية وفق متطلبات البورصة والمعايير الدولية.</p>
                    </div>

                    <div style="background: {CBE_BG}; padding: 18px; border-radius: 10px; border-right: 5px solid {CBE_GOLD}; margin-bottom: 25px;">
                        <p style="margin: 0; font-weight: bold; color: {CBE_NAVY}; font-size: 15px;">📌 ملخص مؤشرات التشخيص المعتمدة في المنصة لبنك ({b_name}):</p>
                        <p style="margin: 8px 0 0 0; color: #1E293B; line-height: 1.8; font-size: 14px;">
                        - المؤشر المركب للحوكمة الذكية المستدامة (SSGI): <b>{b_score}%</b><br>
                        - جاهزية منصات المعلومات وبنية التقنية (SIP - وزن 40%): <b>{s_val}%</b> — {describe_sip(s_val)}<br>
                        - كفاءة الحوكمة المؤسسية والامتثال (IG - وزن 30%): <b>{i_val}%</b> — {describe_ig(i_val)}<br>
                        - أداء تقارير الاستدامة والتمويل الأخضر (SR - وزن 30%): <b>{r_val}%</b> — {describe_sr(r_val)}
                        </p>
                    </div>

                    <h3 style="color: {CBE_NAVY}; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px;">1️⃣ البند الأول: الإفصاح عن الحوكمة المؤسسية وهيكل اتخاذ القرار واستراتيجية الاستدامة (GRI 2 & ISSB S1)</h3>
                    <p><b>الملامح التأسيسية وهيكل الملكية:</b> {profile_info}</p>
                    <p><b>السياسات والالتزام المؤسسي:</b> يلتزم بنك ({b_name}) بالإفصاح الشفاف عن هيكل الإشراف المؤسسي ودور مجلس الإدارة واللجان المنبثقة عنه (لجنة الاستدامة، لجنة المخاطر، ولجنة المراجعة) في توجيه وإدارة الأنشطة والتمويل المستدام. وسجل البنك مؤشر حوكمة مؤسسية بواقع ({i_val}%), مما يعكس متانة أطر التدقيق الداخلي، سياسات تجنب تعارض المصالح، واستقلالية الأعضاء المستقلين في هيكل اللجان، بما يتماشى مع تعليمات وضوابط البنك المركزي المصري.</p>

                    <h3 style="color: {CBE_NAVY}; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; margin-top: 25px;">2️⃣ البند الثاني: الإفصاحات البيئية وتمويل المناخ وإدارة البصمة الكربونية (GRI 302/305 & ISSB S2)</h3>
                    <p><b>الأداء البيئي والتمويل المستدام:</b> استناداً إلى مستوى أداء الاستدامة ومخاطر المناخ المسجل بواقع ({r_val}%), يعمل بنك ({b_name}) على التوسع المدروس في محفظة الأصول الخضراء، تمويل مشروعات الطاقة المتجددة، وكفاءة استخدام الموارد. كما يلتزم البنك بقياس البصمة الكربونية التشغيلية (Scopes 1, 2, 3) لفروع البنك ومراكز البيانات، وإدماج اختبارات التحمل المناخي (Climate Stress Testing) ضمن تقييم الجدارة الائتمانية للمحفظة المؤسسية للعملاء الكبار.</p>

                    <h3 style="color: {CBE_NAVY}; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; margin-top: 25px;">3️⃣ البند الثالث: الإفصاحات المجتمعية والشمول المالي وتطوير رأس المال البشري (GRI 401/405/413)</h3>
                    <p><b>المسؤولية الاجتماعية والتحول الرقمي:</b> استناداً إلى جاهزية البنية التحتية الرقمية ومنصات المعلومات المسجلة بواقع ({s_val}%), يوجه بنك ({b_name}) استراتيجياته نحو تعزيز الشمول المالي، دعم المشروعات الصغيرة والمتوسطة (SMEs)، تمكين المرأة في المناصب القيادية وفق مبادئ (WEPs)، وتوسيع نطاق الخدمات المصرفية الرقمية الآمنة، مع الالتزام التام بمعايير حماية سرية بيانات العملاء والامتثال للقواعد العامة لحماية البيانات (GDPR) والسيادة الرقمية.</p>

                    <h3 style="color: {CBE_NAVY}; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; margin-top: 25px;">4️⃣ البند الرابع: خطة التحرك الاستراتيجي والتوصيات التنفيذية المقترحة للبنك</h3>
                    <ul>
                        <li><b>تحديث البنية التحتية الرقمية:</b> مواصلة الاستثمار في منصات المعلومات الذكية وربطها بالتقارير الرقابية الآلية (RegTech).</li>
                        <li><b>توسيع الأصول الخضراء:</b> رفع نسبة الائتمان الموجه للمشروعات المستدامة وصديقة البيئة لتعزيز تنافسية البنك في المؤشرات الإقليمية والدولية.</li>
                        <li><b>تعزيز الشفافية والتوكيد الخارجي:</b> إخضاع تقارير الاستدامة لعمليات تدقيق وتوكيد خارجي مستقل لزيادة ثقة الموتمرين والمؤسسات المالية الدولية.</li>
                    </ul>
                </div>
                """
                st.markdown(flat_html(detailed_draft_html), unsafe_allow_html=True)

                docx_full_download = f"""
                <html dir="rtl">
                <head><meta charset="utf-8"><title>مسودة تقرير الاستدامة المفصلة - {b_name}</title></head>
                <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
                    <h1 style="color: {CBE_NAVY}; text-align: center;">مسودة تقرير الاستدامة والإفصاح المالي (GRI / ISSB / SDG Impact)</h1>
                    <h3 style="text-align: center; color: {CBE_GOLD};">بنك: {b_name}</h3>
                    <p style="text-align: center; color: #64748B;">مستند توجيهي استرشادي مبني على معطيات التشخيص المرصود بالمنصة.</p>
                    <hr>
                    <h3>ملخص مؤشرات التشخيص المعتمدة:</h3>
                    <p>المؤشر المركب (SSGI): {b_score}% | منصات المعلومات: {s_val}% | الحوكمة المؤسسية: {i_val}% | الاستدامة: {r_val}%</p>
                    <hr>
                    <h3>1. الإفصاح عن الحوكمة المؤسسية واستراتيجية الاستدامة:</h3>
                    <p>{profile_info}</p>
                    <p>يسجل بنك ({b_name}) مؤشر حوكمة مؤسسية بواقع ({i_val}%), مع التزام تام باستقلالية لجان المراجعة وإدارة المخاطر وتجنب تعارض المصالح.</p>
                    <h3>2. الإفصاحات البيئية وتمويل المناخ:</h3>
                    <p>استناداً لأداء الاستدامة ({r_val}%), يتبنى البنك خططاً لتوسيع تمويل المشروعات الخضراء، قياس البصمة الكربونية، وإجراء اختبارات التحمل المناخي.</p>
                    <h3>3. الإفصاحات المجتمعية والشمول المالي:</h3>
                    <p>يوظف البنك بنيته التقنية المتقدمة ({s_val}%) لتسريع الشمول المالي، دعم المشروعات الصغيرة والمتوسطة، وتأمين البيانات المصرفية.</p>
                    <h3>4. خطة التحرك والتوصيات الاستراتيجية:</h3>
                    <p>مواصلة التحول الرقمي، تعزيز إفصاحات الاستدامة، والالتزام بمعايير التوكيد الخارجي المستقل.</p>
                    <hr>
                    <p style="text-align: center; font-size: 12px; color: #64748B;">جميع الحقوق محفوظة للدراسة البحثية © 2026</p>
                </body>
                </html>
                """
                st.download_button(
                    label=f"📥 تحميل مسودة تقرير الاستدامة التفصيلية للبنك ({b_name}) في ملف مستند (Word)",
                    data=docx_full_download.encode("utf-8-sig"),
                    file_name=f"مسودة_تقرير_الاستدامة_المفصلة_{b_name}.doc",
                    mime="application/msword",
                    use_container_width=True,
                )

    st.markdown("---")
    st.markdown("#### 📖 2. الدليل العملي الشامل والموسع والمفصل لجميع بنود وأقسام الاستدامة للقطاع المصرفي")

    with st.expander("📚 اضغط هنا لاستعراض الدليل العملي الشامل والموسع (GRI Standards / ISSB S1 & S2 / SDG Impact Standards / المؤشرات الثلاثين)", expanded=True):
        comprehensive_guide_html = f"""
        <div style="background: #FFFFFF; padding: 35px; border-radius: 14px; border: 1.5px solid {CBE_GOLD}; line-height: 2.1;" dir="rtl">
            <h2 style="color: {CBE_NAVY}; margin-top: 0; text-align: center;">📚 الدليل العملي الشامل والموسع لإعداد تقارير الاستدامة في القطاع المصرفي المصري</h2>
            <p style="text-align: center; color: #475569; font-size: 14.5px;">مرجع منهجي وتطبيقي متكامل لإعداد التقارير المالية وغير المالية المتعلقة بالاستدامة وفق أحدث المعايير الدولية المعاصرة (ISSB S1/S2, GRI Universal & Sector Standards, UNDP SDG Impact Standards)[cite: 74].</p>
            <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 25px 0;">

            <h3 style="color: {CBE_NAVY};">1️⃣ المحور الأول: المعايير العالمية للإفصاح المؤسسي (GRI Universal Standards: GRI 1, GRI 2, GRI 3)</h3>
            <ul>
                <li><b>GRI 1 (الأساسيات):</b> يحدد مبادئ إعداد التقارير المصرفية الأساسية (الدقة، القابلية للمقارنة، الوضوح، الموثوقية، والتوقيت المناسب) التي يجب الالتزام بها لضمان جودة الإفصاحات غير المالية[cite: 74, 84].</li>
                <li><b>GRI 2 (الإفصاحات العامة والتفاصيل التنظيمية):</b> يتضمن تفاصيل أنشطة البنك المصرفي، هيكل الحوكمة وتكوين مجلس الإدارة، سياسات الإفصاح، استراتيجية الاستدامة، وطرق إشراك أصحاب المصلحة (Stakeholder Engagement)[cite: 74, 84, 85].</li>
                <li><b>GRI 3 (الموضوعات الجوهرية - Material Topics):</b> إرشادات دقيقة لتحديد الموضوعات ذات الأولوية القصوى بناءً على تقييم التأثيرات الاقتصادية والبيئية والاجتماعية الفعلية والمحتملة لأنشطة البنوك[cite: 74, 85].</li>
            </ul>

            <h3 style="color: {CBE_NAVY}; margin-top: 25px;">2️⃣ المحور الثاني: الحوكمة المؤسسية وإدارة المخاطر الاستراتيجية (ISSB S1 & GRI 2)</h3>
            <ul>
                <li><b>هيكل الإشراف والمساءلة الحوكمية:</b> إفصاح البنك عن دور مجلس الإدارة واللجان المنبثقة عنه (لجنة الاستدامة، لجنة المخاطر، ولجنة المراجعة) في توجيه ومراقبة المخاطر والفرص المتعلقة بالاستدامة والتمويل المستدام[cite: 74, 80].</li>
                <li><b>تكامل الاستراتيجية ونماذج أعمال البنك:</b> توضيح كيفية تأثير المخاطر والفرص البيئية والاجتماعية على استراتيجية البنك بعيدة المدى، خطط أعماله الائتمانية، وقرارات تخصيص رأس المال[cite: 74, 80].</li>
                <li><b>أطر إدارة المخاطر الكلية:</b> سياسات دمج المخاطر البيئية والاجتماعية ومخاطر الحوكمة (ESG) ضمن السياسات الائتمانية وإدارة المخاطر المؤسسية للبنك[cite: 74, 79, 80].</li>
                <li><b>سياسات النزاهة ومكافحة الفساد:</b> الإفصاح عن مدونة السلوك الأخلاقي المصرفي، آليات الإبلاغ عن المخالفات، سياسات منع تضارب المصالح، ومكافحة غسل الأموال[cite: 74, 91].</li>
            </ul>

            <h3 style="color: {CBE_NAVY}; margin-top: 25px;">3️⃣ المحور الثالث: الإفصاحات البيئية وتمويل المناخ والطاقة (GRI 302/303/305 & ISSB S2)</h3>
            <ul>
                <li><b>إدارة البصمة الكربونية التشغيلية (Scopes 1, 2, 3):</b> قياس والإفصاح الشفاف عن الانبعاثات المباشرة وغير المباشرة الناتجة عن عمليات فروع البنك ومراكز البيانات وسلسلة التوريد[cite: 74, 87].</li>
                <li><b>محفظة التمويل الأخضر والأصول المستدامة:</b> قياس نسبة وحجم المحفظة الائتمانية الموجهة لمشروعات الطاقة المتجددة، كفاءة الطاقة، والنقل المستدام، بالإضافة إلى إصدار السندات الخضراء (Green Bonds)[cite: 74, 79, 88].</li>
                <li><b>اختبارات التحمل المناخي (Climate Stress Testing):</b> مدى جاهزية البنك لتقييم واختبار تأثير المخاطر المناخية الطبيعية والانتقالية على جودة أصوله ومحفظة عملائه الكبار[cite: 74, 88].</li>
                <li><b>إفصاحات التمويل المرتبط بالمناخ (Financed Emissions):</b> تقييم الانبعاثات المُموّلة عبر القطاعات عالية الانبعاثات ووضع خطط انتقالية واضحة لإزالة الكربون (Net-Zero Transition Plans)[cite: 74, 88].</li>
            </ul>

            <h3 style="color: {CBE_NAVY}; margin-top: 25px;">4️⃣ المحور الرابع: الإفصاحات المجتمعية والشمول المالي ورأس المال البشري (GRI 401/403/405/413)</h3>
            <ul>
                <li><b>الشمول المالي والتحول الرقمي المستدام:</b> حجم ونطاق التمويلات الموجهة للمشروعات الصغيرة والمتوسطة (SMEs)، تمكين المرأة والشباب، وتوسيع نطاق الخدمات المصرفية الرقمية في كافة المحافظات[cite: 74, 89, 90].</li>
                <li><b>رأس المال البشري وتكافؤ الفرص:</b> سياسات التوظيف العادل، برامج التدريب والتطوير المستمر للعاملين بالقطاع المصرفي، نسب تمثيل المرأة في الإدارة العليا، ومؤشرات الصحة والسلامة المهنية[cite: 74, 89, 90].</li>
                <li><b>المسؤولية المجتمعية والاستثمار التنموي:</b> حجم الإنفاق المجتمعي الموجه لدعم المبادرات القومية (مثل قطاعات الصحة، التعليم، ودعم الأسر الأولى بالرعاية)[cite: 74, 79].</li>
                <li><b>حماية حقوق العملاء وأمن البيانات:</b> معايير حماية سرية بيانات العملاء، سياسات الشفافية في تسعير الخدمات المصرفية، والامتثال لقواعد حماية البيانات الشخصية والسيادة الرقمية (GDPR)[cite: 74, 91].</li>
            </ul>

            <h3 style="color: {CBE_NAVY}; margin-top: 25px;">5️⃣ المحور الخامس: معايير تأثير أهداف التنمية المستدامة (UNDP SDG Impact Standards for Enterprises) ومقاييس الأداء الثلاثين (ESG)</h3>
            <p>يستند هذا الدليل إلى <b>30 مؤشراً مقترحاً للاستدامة</b> مقتبسة من الوثيقة التوجيهية للاتحاد الدولي للبورصات (WFE) والمبادرة العالمية (GRI) لتشمل الجوانب البيئية والمجتمعية والحوكمة[cite: 74, 86, 87]:</p>
            <ul>
                <li><b>مؤشرات الأداء البيئي (1 إلى 9):</b> انبعاثات الغازات الدفيئة (النطاق 1، 2، 3)، كثافة الانبعاثات، استهلاك وزدواجية الطاقة، إدارة الموارد المائية والنفايات السائلة، السياسات البيئية المعتمدة، وإدارة مخاطر المناخ[cite: 86, 87, 88].</li>
                <li><b>مؤشرات الأداء المجتمعي (10 إلى 20):</b> نسبة أجور المديرين التنفيذيين، نسبة الأجور بين الجنسين، معدل دوران الموظفين، التنوع بين الجنسين في المستويات القيادية، الصحة والسلامة المهنية، مناهضة التحرش وعمل الأطفال، وحقوق الإنسان[cite: 89, 90].</li>
                <li><b>مؤشرات الحوكمة والشفافية (21 إلى 30):</b> التنوع في مجلس الإدارة، استقلالية المجلس، الحوافز التشجيعية للاستدامة، مدونة قواعد سلوك الموردين، سياسات مكافحة الفساد والأخلاقيات، سرية البيانات وحماية الخصوصية (GDPR)، والتوكيد الخارجي المستقل[cite: 90, 91, 92].</li>
                <li><b>التركيز على اتخاذ القرار الداخلي والتوكيد الخارجي:</b> دمج إدارة التأثير والمساهمة الإيجابية في أهداف التنمية المستدامة (SDGs) ضمن استراتيجية البنك وصنع قراره القيادي، مع ضمان تدقيق مستقل من طرف ثالث لتعزيز موثوقية التقرير[cite: 74, 91, 95].</li>
            </ul>
        </div>
        """
        st.markdown(flat_html(comprehensive_guide_html), unsafe_allow_html=True)

        # زر تحميل الدليل العملي الشامل بتنسيق مستند Word
        guide_docx_content = f"""
        <html dir="rtl">
        <head><meta charset="utf-8"><title>الدليل العملي الشامل لإعداد تقارير الاستدامة</title></head>
        <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
            <h1 style="color: {CBE_NAVY}; text-align: center;">الدليل العملي الشامل والموسع لإعداد تقارير الاستدامة في القطاع المصرفي المصري</h1>
            <p style="text-align: center; color: #64748B;">مرجع منهجي وتطبيقي متكامل (GRI Standards / ISSB S1 & S2 / SDG Impact Standards)</p>
            <hr>
            {comprehensive_guide_html}
            <hr>
            <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">جميع الحقوق محفوظة للدراسة البحثية © 2026</p>
        </body>
        </html>
        """
        st.download_button(
            label="📥 تحميل الدليل العملي الشامل والموسع في ملف مستند (Word)",
            data=guide_docx_content.encode("utf-8-sig"),
            file_name="الدليل_العملي_الشامل_لتقارير_الاستدامة_المصرفية.doc",
            mime="application/msword",
            use_container_width=True
        )

# ------------------------------------------------------------------------------
# التبويب السابع: لوحة تحكم المشرف والزوار (Admin Dashboard)
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
