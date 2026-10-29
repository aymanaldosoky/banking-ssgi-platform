import io
import os
import json
import re
import hashlib
import time
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
    border: none !important;
}}

.stApp {{
    background-color: {CBE_BG} !important;
    direction: rtl !important;
    text-align: right !important;
    border: none !important;
}}

/* تصميم Skeleton Loader ذكي ومخصص */
@keyframes skeleton-shimmer {{
    0% {{ background-position: -200px 0; }}
    100% {{ background-position: 200px 0; }}
}}

.skeleton-card {{
    background: #ffffff;
    border-radius: 12px;
    border: 1.5px solid #E2E8F0;
    padding: 24px;
    margin-top: 15px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}}

.skeleton-line {{
    height: 16px;
    margin-bottom: 12px;
    border-radius: 6px;
    background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
    background-size: 400px 100%;
    animation: skeleton-shimmer 1.4s infinite ease-in-out;
}}

.skeleton-title {{ height: 24px; width: 50%; margin-bottom: 20px; }}
.skeleton-body-1 {{ width: 100%; }}
.skeleton-body-2 {{ width: 92%; }}
.skeleton-body-3 {{ width: 85%; }}
.skeleton-badge {{ height: 35px; width: 30%; border-radius: 20px; margin-bottom: 15px; }}

/* إزالة أي إطارات رمادية أو تأثيرات عند التنقل بين الأقسام والعناصر والتمرير */
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

/* تصميم جدول RTL مخصص ونظيف بلا إطارات مشوشة */
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
    border-right: none !important;
    border-left: none !important;
    text-align: right !important;
    font-size: 13px !important;
    white-space: nowrap !important;
}}

.custom-rtl-table td {{
    padding: 8px 10px !important;
    border-bottom: 1px solid #F1F5F9 !important;
    border-top: none !important;
    border-right: none !important;
    border-left: none !important;
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

/* توحيد تصميم الأزرار ومفاتيح التحميل بدون إطارات تركيز رمادية */
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
    outline: none !important;
}}

div.stButton > button:hover, div.stDownloadButton > button:hover {{
    background-color: #001A33 !important;
    color: {CBE_GOLD_LIGHT} !important;
    border-color: #FFFFFF !important;
    box-shadow: 0 6px 16px rgba(0, 43, 73, 0.3) !important;
}}

div.stTabs {{
    width: 100% !important;
    max-width: 100% !important;
    direction: rtl !important;
    border: none !important;
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
    box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
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
    outline: none !important;
    box-shadow: none !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
    background-color: #1D4ED8 !important;
    color: #FFFFFF !important;
    border-color: #FFFFFF !important;
}}

.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    border: 2px solid #FFFFFF !important;
    font-weight: 800 !important;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important;
    outline: none !important;
}}

.stTabs [data-baseweb="tab"] p {{ color: inherit !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: #60A5FA !important; }}
.stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

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
# الدوال المساعدة (Flat HTML & Clean Text)
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
# نظام تتبع الزوار والاستبيانات
# ==============================================================================
LOG_FILE = "visitors_log.csv"
SURVEY_LOG_FILE = "survey_responses_log.csv"

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

def load_visitors_log_from_file():
    if os.path.exists(LOG_FILE):
        try:
            df = pd.read_csv(LOG_FILE, encoding='utf-8-sig')
            return df.to_dict(orient="records")
        except Exception:
            return []
    return []

def load_survey_log_from_file():
    if os.path.exists(SURVEY_LOG_FILE):
        try:
            df = pd.read_csv(SURVEY_LOG_FILE, encoding='utf-8-sig')
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
        login_container = st.container()
        with login_container:
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
if "trigger_search" not in st.session_state:
    st.session_state.trigger_search = False
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
<b>إعداد الباحث:  أيمن الدسوقي (مدرس مساعد إدارة المعرفة – معهد التخطيط القومي)</b>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <span class="ticker-item">🏛️ مقترح المنصة الوطنية الذكية لتعزيز الحوكمة وتقارير الاستدامة بالقطاع المصرفي المصري</span>
    <span class="ticker-item">| 📊 مؤشر الحوكمة الذكية المستدامة (SSGI) والأبعاد الثلاثة الرئيسة</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي لاختبار السيناريوهات الاستراتيجية (Multiple Regression)</span>
    <span class="ticker-item">| 🛡️ لوحة دعم اتخاذ القرار </span>
    <span class="ticker-item">| 📋 الاستبيان الموجه لفرق العمل في البنوك وعينة الدراسة الميدانية </span>
    <span class="ticker-item">| 📖 دليل المستخدم الرسمي والتوثيق المنهجي PDF </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# التبويبات الرئيسة
# ==============================================================================
if st.session_state.role == "admin":
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "🎯اسأل المنصة",
        "📊مؤشر الحوكمة المركب (SSGI)", 
        "📈محاكي السياسات (Policy Simulator)", 
        "🛡️لوحة دعم اتخاذ القرار", 
        "📑التقرير التنفيذي الموحد",
        "🌿مولد تقارير الاستدامة (GRI/ISSB)",
        "📋استبيان فرق العمل المصرفي",
        "📖دليل المستخدم الرسمي PDF",
        "🔒 لوحة تحكم المشرف والزوار (Admin)"
    ])
else:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🎯اسأل المنصة",
        "📊مؤشر الحوكمة المركب (SSGI)", 
        "📈محاكي السياسات (Policy Simulator)", 
        "🛡️لوحة دعم اتخاذ القرار", 
        "📑التقرير التنفيذي الموحد",
        "🌿مولد تقارير الاستدامة (GRI/ISSB)",
        "📋استبيان فرق العمل المصرفي",
        "📖دليل المستخدم الرسمي PDF"
    ])
    tab9 = None

# ------------------------------------------------------------------------------
# التبويب الأول: اسأل المنصة (مُطور بالكامل - Zero-Click Trigger & Quick Chips UX)
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 20px;">
        <h3 style="color: #002B49; font-weight: 800; margin-bottom: 4px;">🎯 تحليل واستخلاص البيانات الذكي (RAG Engine)</h3>
        <p style="color: #475569; font-size: 14px;">استعراض الإجابات المستندة إلى تقارير الاستدامة والحوكمة في القطاع المصرفي المصري لكل بنك على حدة.</p>
    </div>
    """, unsafe_allow_html=True)

    col_q1, col_q2 = st.columns([1, 2], gap="large")

    with col_q1:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        ask_bank_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, key="ask_bank")

        user_question = st.text_area(
            "❓ اكتب سؤالك / استفسارك:",
            placeholder="مثال: متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟",
            height=100,
            key="query_text_box"
        )

        st.markdown("<b style='color: #002B49; font-size: 13.5px;'>📌 أسئلة مقترحة (Zero-Click - اضغط للتنفيذ المباشر):</b>", unsafe_allow_html=True)

        # دالة الاستجابة الفورية عند النقر على الأسئلة المقترحة
        def trigger_instant_query(question):
            st.session_state.query_text_box = question
            st.session_state.trigger_search = True

        with st.expander("🏛️ محور الحوكمة والتأسيس والتاريخ (IG & History)"):
            ig_questions = [
                "متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟",
                "عرف الحوكمة وتكوين مجلس الإدارة بالبنك",
                "ما هي نسبة الأعضاء المستقلين وسياسات تجنب تعارض المصالح؟",
                "ما هي جهود البنك في تمكين المرأة والشمول المالي؟",
                "كيف يفصح البنك عن سياسات الشفافية والمساءلة ومكافحة الفساد؟",
                "كيف يضمن البنك الالتزام التام بالقوانين واللوائح الصادرة عن البنك المركزي المصري؟"
            ]
            for i, q in enumerate(ig_questions):
                st.button(f"⚡ {q}", key=f"btn_ig_{i}", on_click=trigger_instant_query, args=(q,), use_container_width=True)

        with st.expander("🌱 محور تقارير الاستدامة والتمويل الأخضر والمناخ (SR/ESG)"):
            sr_questions = [
                "كيف يتعامل البنك مع مخاطر المناخ والتمويل الأخضر؟",
                "ما هي نسبة الأصول الخضراء والمشروعات المستدامه ضمن محفظة الائتمان؟",
                "كيف يمتثل البنك للمعايير الدولية للإفصاح المالي (GRI و ISSB)؟",
                "ما هي مبادرات البنك في المسؤولية المجتمعية والإنفاق التنموي المستدام؟"
            ]
            for i, q in enumerate(sr_questions):
                st.button(f"⚡ {q}", key=f"btn_sr_{i}", on_click=trigger_instant_query, args=(q,), use_container_width=True)

        with st.expander("🔒 محور المنصات الذكية وحوكمة البيانات والامتثال (SIP/RegTech)"):
            sip_questions = [
                "ما هي آليات حوكمة البيانات والامتثال الرقابي وتأمينها؟",
                "كيف يضمن البنك الحصانة السيبرانية ومنع تسريب البيانات المالية الحساسة؟",
                "ما هي جاهزية البنية التحتية الرقمية ومنصات المعلومات (SIP)؟",
                "كيف يوظف البنك تقنيات الرقابة التنظيمية (RegTech) واسترجاع المعطيات؟",
                "ما مدى التوافق مع قانون حماية البيانات الشخصية والسيادة الرقمية؟"
            ]
            for i, q in enumerate(sip_questions):
                st.button(f"⚡ {q}", key=f"btn_sip_{i}", on_click=trigger_instant_query, args=(q,), use_container_width=True)

        ask_submit_btn = st.button("🚀 تقديم السؤال والتحليل المباشر", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_q2:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)

        # التحقق مما إذا تم ضغط زر التقديم أو تمت إثارة السؤال فورياً عبر Zero-Click Trigger
        should_execute = ask_submit_btn or st.session_state.get("trigger_search", False)

        if should_execute:
            # إعادة تعيين التنبيه الفوري للجلسة بعد بدء التنفيذ
            st.session_state.trigger_search = False
            active_q = st.session_state.query_text_box

            if ask_bank_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي صحيح من القائمة لتنفيذ الاستعلام.")
            elif not active_q.strip():
                st.warning("⚠️ يرجى كتابة أو اختيار سؤال للإجابة عليه.")
            else:
                # --------------------------------------------------------------
                # 1. عرض Skeleton Loader أثناء التجهيز الأولي
                # --------------------------------------------------------------
                skeleton_placeholder = st.empty()
                skeleton_html = flat_html(f"""
                <div class="skeleton-card">
                    <div class="skeleton-line skeleton-title"></div>
                    <div class="skeleton-line skeleton-badge"></div>
                    <div class="skeleton-line skeleton-body-1"></div>
                    <div class="skeleton-line skeleton-body-2"></div>
                    <div class="skeleton-line skeleton-body-3"></div>
                </div>
                """)
                skeleton_placeholder.markdown(skeleton_html, unsafe_allow_html=True)

                # --------------------------------------------------------------
                # 2. معالجة الحالات الخاصة وتوليد الإجابة
                # --------------------------------------------------------------
                if ask_bank_sel == "البنك الأهلي اليوناني" and ("تأسس" in active_q or "مؤسسه" in active_q):
                    skeleton_placeholder.empty()
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
                    # جلب النص النهائي من محرك RAG
                    full_response = process_rag_gemini_query(ask_bank_sel, active_q)

                    # تفريغ الـ Skeleton وإفراغ المساحة للـ Streaming
                    skeleton_placeholder.empty()

                    # ----------------------------------------------------------
                    # 3. محاكاة التدفق المباشر (Streaming Generator)
                    # ----------------------------------------------------------
                    def stream_response_generator(text_html):
                        # تقسيم المخرجات حسب الكلمات مع الحفاظ على وسم الـ HTML
                        tokens = text_html.split(" ")
                        for token in tokens:
                            yield token + " "
                            time.sleep(0.01) # سرعة البث لتقليل Latency الظاهري

                    # تنفيذ العرض التفاعلي التدريجي
                    response_box = st.empty()
                    accumulated_text = ""
                    for chunk in stream_response_generator(flat_html(full_response)):
                        accumulated_text += chunk
                        response_box.markdown(accumulated_text, unsafe_allow_html=True)

        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح لتوليد التقرير فوراً دون الحاجة للضغط على زر إضافي.")

        st.markdown('</div>', unsafe_allow_html=True)
# ------------------------------------------------------------------------------
# التبويب الثاني: مؤشر الحوكمة المركب (SSGI) - مُطور بتجربة مستخدم عالمية (Enterprise UX)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 20px;">
        <h3 style="color: #002B49; font-weight: 800; margin-bottom: 4px;">🗳️ التشخيص القياسي واحتساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
        <p style="color: #475569; font-size: 14px;">إمكانية تشخيص قياس أداء البنوك المصرية عبر المحاور الثلاثة الرئيسة بالأوزان النسبية المعتمدة.</p>
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
                # --------------------------------------------------------------
                # 1. عرض Skeleton Loader أثناء التجهيز والحساب
                # --------------------------------------------------------------
                skeleton_placeholder = st.empty()
                skeleton_html = flat_html(f"""
                <div class="skeleton-card">
                    <div class="skeleton-line skeleton-title"></div>
                    <div class="skeleton-line skeleton-badge"></div>
                    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                        <div class="skeleton-line" style="flex: 1; height: 50px;"></div>
                        <div class="skeleton-line" style="flex: 1; height: 50px;"></div>
                        <div class="skeleton-line" style="flex: 1; height: 50px;"></div>
                    </div>
                    <div class="skeleton-line skeleton-body-1"></div>
                    <div class="skeleton-line skeleton-body-2"></div>
                </div>
                """)
                skeleton_placeholder.markdown(skeleton_html, unsafe_allow_html=True)
                time.sleep(0.3) # إعطاء إحساس تفاعلي بالمعالجة
                skeleton_placeholder.empty()

                # --------------------------------------------------------------
                # 2. احتساب المؤشر المركب والصياغات التشخيصية
                # --------------------------------------------------------------
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
                    badge_status = "أداء مرتفع 🟢"
                    status_border_color = "#10B981"  # Emerald Green
                    detailed_diag = f"""
                    <div style="line-height: 1.8; font-size: 14px;">
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
                    badge_status = "أداء متوسط 🟡"
                    status_border_color = "#F59E0B"  # Amber Yellow
                    detailed_diag = f"""
                    <div style="line-height: 1.8; font-size: 14px;">
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
                    badge_status = "فجوة حرجة 🔴"
                    status_border_color = "#EF4444"  # Coral Red
                    detailed_diag = f"""
                    <div style="line-height: 1.8; font-size: 14px;">
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

                # --------------------------------------------------------------
                # 3. عرض البطاقات الرقمية الرئيسية داخل حاوية فخمة (Executive Metric Container)
                # --------------------------------------------------------------
                metric_container_html = f"""
                <div dir="rtl" style="
                    background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
                    border: 1.5px solid {CBE_GOLD};
                    border-radius: 16px;
                    padding: 20px;
                    box-shadow: 0 10px 25px -5px rgba(0, 43, 73, 0.08);
                    margin-bottom: 20px;
                ">
                    <!-- عنوان الحاوية المؤسسية -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid #E2E8F0; padding-bottom: 10px;">
                        <h4 style="color: {CBE_NAVY}; font-weight: 800; margin: 0; font-size: 16px; display: flex; align-items: center; gap: 8px;">
                            🏛️ ملخص مؤشرات القياس والأداء - <span style="color: {CBE_GOLD};">{clean_text(bank_ssgi_sel)}</span>
                        </h4>
                        <span style="background: #FFFFFF; color: {CBE_NAVY}; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 1px solid #CBD5E1;">
                            {badge_status}
                        </span>
                    </div>
                    
                    <!-- شبكة البطاقات الرقمية الأربع -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px;">
                        
                        <!-- بطاقة 1: SSGI -->
                        <div style="background: #FFFFFF; border-radius: 12px; padding: 14px; border-right: 5px solid {status_border_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                            <span style="font-size: 11.5px; color: #64748B; font-weight: 700; display: block; margin-bottom: 4px;">مؤشر SSGI المركب</span>
                            <div style="font-size: 22px; font-weight: 900; color: {CBE_NAVY}; line-height: 1.2;">{final_score}%</div>
                            <span style="font-size: 10.5px; color: {status_border_color}; font-weight: 800; margin-top: 4px; display: inline-block;">النتيجة العامة</span>
                        </div>

                        <!-- بطاقة 2: SIP -->
                        <div style="background: #FFFFFF; border-radius: 12px; padding: 14px; border-right: 5px solid {CBE_NAVY}; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                            <span style="font-size: 11.5px; color: #64748B; font-weight: 700; display: block; margin-bottom: 4px;">منصات المعلومات (SIP)</span>
                            <div style="font-size: 22px; font-weight: 900; color: {CBE_NAVY}; line-height: 1.2;">{sip_val}%</div>
                            <span style="font-size: 10.5px; color: #475569; font-weight: 700; margin-top: 4px; display: inline-block;">الوزن: 40%</span>
                        </div>

                        <!-- بطاقة 3: IG -->
                        <div style="background: #FFFFFF; border-radius: 12px; padding: 14px; border-right: 5px solid {CBE_GOLD}; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                            <span style="font-size: 11.5px; color: #64748B; font-weight: 700; display: block; margin-bottom: 4px;">الحوكمة المؤسسية (IG)</span>
                            <div style="font-size: 22px; font-weight: 900; color: {CBE_NAVY}; line-height: 1.2;">{ig_val}%</div>
                            <span style="font-size: 10.5px; color: #475569; font-weight: 700; margin-top: 4px; display: inline-block;">الوزن: 30%</span>
                        </div>

                        <!-- بطاقة 4: SR -->
                        <div style="background: #FFFFFF; border-radius: 12px; padding: 14px; border-right: 5px solid #475569; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                            <span style="font-size: 11.5px; color: #64748B; font-weight: 700; display: block; margin-bottom: 4px;">تقارير الاستدامة (SR)</span>
                            <div style="font-size: 22px; font-weight: 900; color: {CBE_NAVY}; line-height: 1.2;">{sr_val}%</div>
                            <span style="font-size: 10.5px; color: #475569; font-weight: 700; margin-top: 4px; display: inline-block;">الوزن: 30%</span>
                        </div>

                    </div>
                </div>
                """
                st.markdown(flat_html(metric_container_html), unsafe_allow_html=True)

                # --------------------------------------------------------------
                # 4. حفظ البيانات والتحديث الفوري للذاكرة الجلسية
                # --------------------------------------------------------------
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
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.8; box-shadow: 0 4px 15px rgba(0,0,0,0.04); margin-top: 10px;">
                  <div style="background: {CBE_BG}; padding: 15px; border-radius: 8px; border-right: 5px solid {CBE_GOLD};">
                    <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY}; font-size: 15px;">التشخيص القياسي المفصل:</p>
                    <div style="color: {CBE_NAVY};">{detailed_diag}</div>
                  </div>
                </div>
                """), unsafe_allow_html=True)

                # --------------------------------------------------------------
                # 5. عرض الرسوم البيانية التفاعلية المزدوجة (Plotly Charts)
                # --------------------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                ch_col1, ch_col2 = st.columns(2)

                with ch_col1:
                    categories = ['منصات المعلومات (SIP)', 'الحوكمة المؤسسية (IG)', 'تقارير الاستدامة (SR)']
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=[sip_val, ig_val, sr_val],
                        theta=categories,
                        fill='toself',
                        name=bank_ssgi_sel,
                        line_color=CBE_GOLD,
                        fillcolor='rgba(197, 160, 89, 0.25)'
                    ))
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=False,
                        title=dict(text="التحليل الرداري لمحاور SSGI", x=0.5, xanchor='center'),
                        font=dict(family="Cairo", size=11),
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=320
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)

                with ch_col2:
                    fig_bar = px.bar(
                        x=categories,
                        y=[sip_val, ig_val, sr_val],
                        labels={'x': 'المحور', 'y': 'الدرجة (%)'},
                        title="مقارنة الدرجات الفعلية للمحاور الثلاثة",
                        color=categories,
                        color_discrete_sequence=[CBE_NAVY, CBE_GOLD, "#475569"]
                    )
                    fig_bar.update_layout(
                        showlegend=False,
                        font=dict(family="Cairo", size=11),
                        yaxis=dict(range=[0, 100]),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=320
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

        else:
            st.info("📊 يرجى اختيار البنك وضبط درجات المحاور الثلاثة ثم الضغط على زر الحساب لعرض البطاقات الرقمية والتحليل القياسي المباشر.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # --------------------------------------------------------------------------
    # الجدول الأول: ترتيب وسجلات البنوك (تم تطبيق نفس الهوية البصرية للجدول الثاني)
    # --------------------------------------------------------------------------
    st.markdown("<h3 style='color: #002B49; font-weight: 800;'>📋 ترتيب وسجلات البنوك المُشخَّصة</h3>", unsafe_allow_html=True)
    
    if st.session_state.history_state:
        df_history = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)
        
        # صياغة جدول HTML مخصص متوافق مع نفس كلاس وألوان الجدول الثاني custom-rtl-table
        history_table_html = """
        <div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 350px;">
        <table class="custom-rtl-table">
        <thead>
        <tr>
        <th style="width: 40px; text-align: center;">م</th>
        <th>معرف السجل / التوقيت</th>
        <th>اسم البنك</th>
        <th style="text-align: center;">مؤشر SSGI (%)</th>
        <th style="text-align: center;">SIP (40%)</th>
        <th style="text-align: center;">IG (30%)</th>
        <th style="text-align: center;">SR (30%)</th>
        <th>التقييم التشخيصي القياسي</th>
        </tr>
        </thead>
        <tbody>
        """
        
        for idx, row in df_history.iterrows():
            clean_bank_name = clean_text(str(row['البنك']))
            clean_diag = clean_text(str(row['التقييم التشخيصي']))
            rec_id = clean_text(str(row.get('معرف السجل', idx + 1)))
            score_val = row['مؤشر SSGI المركب']
            
            # إعطاء إشارة ملونة لدرجة المؤشر
            score_badge = f"<span style='color: {CBE_GOLD}; font-weight: 800;'>{score_val}%</span>"
            
            history_table_html += f"""
            <tr>
            <td style="text-align: center; font-weight: bold; color: {CBE_NAVY};">{idx + 1}</td>
            <td style="font-size: 11.5px; color: #64748B;">{rec_id}</td>
            <td style="font-weight: 700; color: {CBE_NAVY};">{clean_bank_name}</td>
            <td style="text-align: center; font-size: 13px;">{score_badge}</td>
            <td style="text-align: center;">{row['منصات المعلومات (40%)']}%</td>
            <td style="text-align: center;">{row['الحوكمة المؤسسية (30%)']}%</td>
            <td style="text-align: center;">{row['تقارير الاستدامة (30%)']}%</td>
            <td style="font-size: 12px; color: #334155;">{clean_diag}</td>
            </tr>
            """
            
        history_table_html += """
        </tbody>
        </table>
        </div>
        """
        st.markdown(flat_html(history_table_html), unsafe_allow_html=True)

        col_dl, col_del = st.columns([1, 1], gap="medium")
        with col_dl:
            csv_data = df_history.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل جدول ترتيب البنوك والسجلات (Excel / CSV)",
                data=csv_data,
                file_name="ترتيب_البنوك_المصرية_SSGI.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_del:
            recorded_ids = [item.get("معرف السجل", item["البنك"]) for item in st.session_state.history_state]
            col_sel, col_btn = st.columns([2, 1])
            with col_sel:
                id_to_delete = st.selectbox("اختر سجلاً لحذفه", recorded_ids, key="del_rec_box", label_visibility="collapsed")
            with col_btn:
                if st.button("🗑️ حذف السجل", use_container_width=True, type="secondary"):
                    st.session_state.history_state = [item for item in st.session_state.history_state if item.get("معرف السجل", item["البنك"]) != id_to_delete]
                    st.success("✅ تم حذف السجل بنجاح.")
                    st.rerun()
    else:
        st.info("📂 لا توجد بنوك مسجلة حتى الآن. قم بإجراء التشخيص في الأعلى لتسجيل وترتيب البنوك المصرفية.")

    st.markdown("---")
    
    # --------------------------------------------------------------------------
    # الجدول الثاني: استعراض المصفوفة الهرمية والمحاور الرئيسة والأبعاد والعناصر الفرعية لمؤشر الحوكمة (SSGI)
    # --------------------------------------------------------------------------
    with st.expander("📂 استعراض المصفوفة الهرمية والمحاور الرئيسة والأبعاد والعناصر الفرعية لمؤشر الحوكمة (SSGI)", expanded=False):
        st.markdown("""
        <div dir="rtl" style="text-align: right; line-height: 1.8;">
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
            title=dict(text="توزيع الأوزان النسبية لمؤشر الحوكمة الذكية المستدامة (SSGI)", x=0.5, xanchor='center'),
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
                <p>يغطي هذا التقرير مخرجات النمذجة القياسية ومتغيرات التحفيز الاستراتيجي للقيادات المصرفيية.</p>
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
                        action_plan = "قيادة التحول الرقمي المصرفي الكامل، وتطبيق أحدث أنظمة (RegTech), وتصدر التصنيفات الإقليمية في التمويل الأخضر."

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

# ------------------------------------------------------------------------------
# التبويب الرابع: لوحة دعم اتخاذ القرار
# ------------------------------------------------------------------------------
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
                <p style="color: #64748B; font-size: 14.5px; margin-top: 6px;">ملخص استراتيجي موجه للقيادات العليا وصناع القرار - بناءً على المعطيات والمخرجات المطلوبة </p>
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

# ------------------------------------------------------------------------------
# التبويب السادس: مولد تقارير الاستدامة (GRI / ISSB)
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🌿 نظام توليد تقارير الاستدامة المتقدم والدليل العملي الشامل (GRI / ISSB / SDG Impact)</h3>
        <p>إطار توجيهي متكامل ومفصل للقطاع المصرفي المصري يربط بين معايير المبادرة العالمية (GRI Standards), معايير الإفصاح المالي الدولي (ISSB S1/S2), معايير تأثير أهداف التنمية المستدامة (SDG Impact Standards), و30 مؤشراً مقترحاً للأداء البيئي والمجتمعي والحوكمة (ESG).</p>
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
        col_gen1, col_gen2, col_gen3 = st.columns([2, 1, 1])
        with col_gen1:
            selected_bank_for_report = st.selectbox(
                "اختر البنك لتوليد مسودة تقرير الاستدامة المخصصة والتفصيلية",
                all_registered_banks,
                key="rep_bank_sel",
            )
        with col_gen2:
            st.markdown("<br>", unsafe_allow_html=True)
            generate_draft_btn = st.button(
                "🌿 توليد المسودة",
                use_container_width=True,
                type="primary",
            )
        with col_gen3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ مسح وإعادة تعيين", use_container_width=True, type="secondary"):
                st.session_state.draft_generated_state = False
                st.session_state.draft_bank_name = ""
                st.success("✅ تم مسح وإعادة تعيين مسودة التقرير بنجاح.")
                st.rerun()

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

                st.markdown(flat_html(f"""
                <div style="background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 15px;" dir="rtl">
                    <h3 style="color: {CBE_NAVY}; margin-top: 0;">🌿 مسودة تقرير الاستدامة المخصصة للبنك: {b_name}</h3>
                    <p style="color: #64748B;">تتيح لك الأقسام أدناه التحكم الكامل في توسيع أو تقليص بنود مسودة تقرير الاستدامة التوجيهية المفصلة بالكامل للبنك، بالإضافة إلى إمكانية تحميل الملف بكافة تفاصيله دون اختصار.</p>
                </div>
                """), unsafe_allow_html=True)

                with st.expander("📌 البند التمهيدي: الملخص التنفيذي ومؤشرات التشخيص المعتمدة بالمنصة", expanded=True):
                    st.markdown(flat_html(f"""
                    <div style="background: {CBE_BG}; padding: 18px; border-radius: 10px; border-right: 5px solid {CBE_GOLD};" dir="rtl">
                        <p style="margin: 0; font-weight: bold; color: {CBE_NAVY}; font-size: 15px;">📌 ملخص مؤشرات التشخيص المعتمدة في المنصة لبنك ({b_name}):</p>
                        <p style="margin: 8px 0 0 0; color: #1E293B; line-height: 1.8; font-size: 14px;">
                        - المؤشر المركب للحوكمة الذكية المستدامة (SSGI): <b>{b_score}%</b><br>
                        - جاهزية منصات المعلومات وبنية التقنية (SIP - وزن 40%): <b>{s_val}%</b> — {describe_sip(s_val)}<br>
                        - كفاءة الحوكمة المؤسسية والامتثال (IG - وزن 30%): <b>{i_val}%</b> — {describe_ig(i_val)}<br>
                        - أداء تقارير الاستدامة والتمويل الأخضر (SR - وزن 30%): <b>{r_val}%</b> — {describe_sr(r_val)}
                        </p>
                    </div>
                    """), unsafe_allow_html=True)

                with st.expander("البند الأول: الإفصاح عن الحوكمة المؤسسية وهيكل اتخاذ القرار واستراتيجية الاستدامة (GRI 2 & ISSB S1)", expanded=False):
                    st.markdown(flat_html(f"""
                    <div dir="rtl" style="text-align: right; line-height: 1.9;">
                        <p><b>الملامح التأسيسية وهيكل الملكية:</b> {profile_info}</p>
                        <p><b>السياسات والالتزام المؤسسي:</b> يلتزم بنك ({b_name}) بالإفصاح الشفاف عن هيكل الإشراف المؤسسي ودور مجلس الإدارة واللجان المنبثقة عنه (لجنة الاستدامة، لجنة المخاطر، ولجنة المراجعة) في توجيه وإدارة الأنشطة والتمويل المستدام. وسجل البنك مؤشر حوكمة مؤسسية بواقع ({i_val}%), مما يعكس متانة أطر التدقيق الداخلي، سياسات تجنب تعارض المصالح، واستقلالية الأعضاء المستقلين في هيكل اللجان، بما يتماشى مع تعليمات وضوابط البنك المركزي المصري.</p>
                    </div>
                    """), unsafe_allow_html=True)

                with st.expander("البند الثاني: الإفصاحات البيئية وتمويل المناخ وإدارة البصمة الكربونية (GRI 302/305 & ISSB S2)", expanded=False):
                    st.markdown(flat_html(f"""
                    <div dir="rtl" style="text-align: right; line-height: 1.9;">
                        <p><b>الأداء البيئي والتمويل المستدام:</b> استناداً إلى مستوى أداء الاستدامة ومخاطر المناخ المسجل بواقع ({r_val}%), يعمل بنك ({b_name}) على التوسع المدروس في محفظة الأصول الخضراء، تمويل مشروعات الطاقة المتجددة، وكفاءة استخدام الموارد. كما يلتزم البنك بقياس البصمة الكربونية التشغيلية (Scopes 1, 2, 3) لفروع البنك ومراكز البيانات، وإدماج اختبارات التحمل المناخي (Climate Stress Testing) ضمن تقييم الجدارة الائتمانية للمحفظة المؤسسية للعملاء الكبار.</p>
                    </div>
                    """), unsafe_allow_html=True)

                with st.expander("البند الثالث: الإفصاحات المجتمعية والشمول المالي وتطوير رأس المال البشري (GRI 401/405/413)", expanded=False):
                    st.markdown(flat_html(f"""
                    <div dir="rtl" style="text-align: right; line-height: 1.9;">
                        <p><b>المسؤولية الاجتماعية والتحول الرقمي:</b> استناداً إلى جاهزية البنية التحتية الرقمية ومنصات المعلومات المسجلة بواقع ({s_val}%), يوجه بنك ({b_name}) استراتيجياته نحو تعزيز الشمول المالي، دعم المشروعات الصغيرة والمتوسطة (SMEs), تمكين المرأة في المناصب القيادية وفق مبادئ (WEPs)، وتوسيع نطاق الخدمات المصرفية الرقمية الآمنة، مع الالتزام التام بمعايير حماية سرية بيانات العملاء والامتثال للقواعد العامة لحماية البيانات (GDPR) والسيادة الرقمية.</p>
                    </div>
                    """), unsafe_allow_html=True)

                with st.expander("البند الرابع: خطة التحرك الاستراتيجي والتوصيات التنفيذية المقترحة للبنك", expanded=False):
                    st.markdown(flat_html(f"""
                    <div dir="rtl" style="text-align: right; line-height: 1.9;">
                        <ul>
                            <li><b>تحديث البنية التحتية الرقمية:</b> مواصلة الاستثمار في منصات المعلومات الذكية وربطها بالتقارير الرقابية الآلية (RegTech).</li>
                            <li><b>توسيع الأصول الخضراء:</b> رفع نسبة الائتمان الموجه للمشروعات المستدامة وصديقة البيئة لتعزيز تنافسية البنك في المؤشرات الإقليمية والدولية.</li>
                            <li><b>تعزيز الشفافية والتوكيد الخارجي:</b> إخضاع تقارير الاستدامة لعمليات تدقيق وتوكيد خارجي مستقل لزيادة ثقة الموتمرين والمؤسسات المالية الدولية.</li>
                        </ul>
                    </div>
                    """), unsafe_allow_html=True)

                docx_full_download = f"""
                <html dir="rtl">
                <head><meta charset="utf-8"><title>مسودة تقرير الاستدامة المفصلة - {b_name}</title></head>
                <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
                    <h1 style="color: {CBE_NAVY}; text-align: center;">مسودة تقرير الاستدامة والإفصاح المالي الشامل (GRI / ISSB / SDG Impact)</h1>
                    <h3 style="text-align: center; color: {CBE_GOLD};">البنك المصرفي: {b_name}</h3>
                    <p style="text-align: center; color: #64748B;">مستند توجيهي استرشادي مفصل بالكامل ومبني على معطيات التشخيص المرصود بالمنصة.</p>
                    <hr>
                    <h3>📌 البند التمهيدي: ملخص مؤشرات التشخيص المعتمدة:</h3>
                    <p>المؤشر المركب للحوكمة الذكية المستدامة (SSGI): <b>{b_score}%</b></p>
                    <p>جهازية منصات المعلومات وبنية التقنية (SIP - وزن 40%): <b>{s_val}%</b> — {describe_sip(s_val)}</p>
                    <p>كفاءة الحوكمة المؤسسية والامتثال (IG - وزن 30%): <b>{i_val}%</b> — {describe_ig(i_val)}</p>
                    <p>أداء تقارير الاستدامة والتمويل الأخضر (SR - وزن 30%): <b>{r_val}%</b> — {describe_sr(r_val)}</p>
                    <hr>
                    <h3>1️⃣ البند الأول: الإفصاح عن الحوكمة المؤسسية وهيكل اتخاذ القرار واستراتيجية الاستدامة (GRI 2 & ISSB S1)</h3>
                    <p><b>الملامح التأسيسية وهيكل الملكية:</b> {profile_info}</p>
                    <p><b>السياسات والالتزام المؤسسي:</b> يلتزم بنك ({b_name}) بالإفصاح الشفاف عن هيكل الإشراف المؤسسي ودور مجلس الإدارة واللجان المنبثقة عنه (لجنة الاستدامة، لجنة المخاطر، ولجنة المراجعة) في توجيه وإدارة الأنشطة والتمويل المستدام. وسجل البنك مؤشر حوكمة مؤسسية بواقع ({i_val}%), مما يعكس متانة أطر التدقيق الداخلي، سياسات تجنب تعارض المصالح، واستقلالية الأعضاء المستقلين في هيكل اللجان، بما يتماشى مع تعليمات وضوابط البنك المركزي المصري.</p>
                    <hr>
                    <h3>2️⃣ البند الثاني: الإفصاحات البيئية وتمويل المناخ وإدارة البصمة الكربونية (GRI 302/305 & ISSB S2)</h3>
                    <p><b>الأداء البيئي والتمويل المستدام:</b> استناداً إلى مستوى أداء الاستدامة ومخاطر المناخ المسجل بواقع ({r_val}%), يعمل بنك ({b_name}) على التوسع المدروس في محفظة الأصول الخضراء، تمويل مشروعات الطاقة المتجددة، وكفاءة استخدام الموارد. كما يلتزم البنك بقياس البصمة الكربونية التشغيلية (Scopes 1, 2, 3) لفروع البنك ومراكز البيانات، وإدماج اختبارات التحمل المناخي (Climate Stress Testing) ضمن تقييم الجدارة الائتمانية للمحفظة المؤسسية للعملاء الكبار.</p>
                    <hr>
                    <h3>3️⃣ البند الثالث: الإفصاحات المجتمعية والشمول المالي وتطوير رأس المال البشري (GRI 401/405/413)</h3>
                    <p><b>المسؤولية الاجتماعية والتحول الرقمي:</b> استناداً إلى جاهزية البنية التحتية الرقمية ومنصات المعلومات المسجلة بواقع ({s_val}%), يوجه بنك ({b_name}) استراتيجياته نحو تعزيز الشمول المالي، دعم المشروعات الصغيرة والمتوسطة (SMEs), تمكين المرأة في المناصب القيادية وفق مبادئ (WEPs)، وتوسيع نطاق الخدمات المصرفية الرقمية الآمنة، مع الالتزام التام بمعايير حماية سرية بيانات العملاء والامتثال للقواعد العامة لحماية البيانات (GDPR) والسيادة الرقمية.</p>
                    <hr>
                    <h3>4️⃣ البند الرابع: خطة التحرك الاستراتيجي والتوصيات التنفيذية المقترحة للبنك</h3>
                    <ul>
                        <li><b>تحديث البنية التحتية الرقمية:</b> مواصلة الاستثمار في منصات المعلومات الذكية وربطها بالتقارير الرقابية الآلية (RegTech).</li>
                        <li><b>توسيع الأصول الخضراء:</b> رفع نسبة الائتمان الموجه للمشروعات المستدامة وصديقة البيئة لتعزيز تنافسية البنك في المؤشرات الإقليمية والدولية.</li>
                        <li><b>تعزيز الشفافية والتوكيد الخارجي:</b> إخضاع تقارير الاستدامة لعمليات تدقيق وتوكيد خارجي مستقل لزيادة ثقة الموتمرين والمؤسسات المالية الدولية.</li>
                    </ul>
                    <hr>
                    <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">يُنصح بالمراجعة الدقيقة للقرارات الاستراتيجية</p>
                    <p style="text-align: center; font-size: 12px; color: #64748B;">جميع الحقوق محفوظة للدراسة البحثية © 2026</p>
                </body>
                </html>
                """
                st.download_button(
                    label=f"📥 تحميل مسودة تقرير الاستدامة المفصلة بالكامل للبنك ({b_name}) بدون اختصار (Word)",
                    data=docx_full_download.encode("utf-8-sig"),
                    file_name=f"مسودة_تقرير_الاستدامة_المفصلة_{b_name}.doc",
                    mime="application/msword",
                    use_container_width=True,
                )

    st.markdown("---")
    st.markdown("#### 📖 2. الدليل العملي الشامل والموسع لإعداد تقارير الاستدامة للقطاع المصرفي")

    with st.expander("📚 اضغط هنا لاستعراض الدليل العملي الشامل والموسع (GRI Standards / ISSB S1 & S2 / SDG Impact Standards)", expanded=True):
        comprehensive_guide_html = f"""
        <div style="background: #FFFFFF; padding: 35px; border-radius: 14px; border: 1.5px solid {CBE_GOLD}; line-height: 2.1;" dir="rtl">
            <h2 style="color: {CBE_NAVY}; margin-top: 0; text-align: center;">📚 الدليل العملي الشامل والموسع لإعداد تقارير الاستدامة في القطاع المصرفي المصري</h2>
            <p style="text-align: center; color: #475569; font-size: 14.5px;">مرجع منهجي وتطبيقي متكامل لإعداد التقارير المالية وغير المالية المتعلقة بالاستدامة وفق أحدث المعايير الدولية المعاصرة (ISSB S1/S2, GRI Universal & Sector Standards, UNDP SDG Impact Standards).</p>
            <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 25px 0;">

            <h3 style="color: {CBE_NAVY};">1️⃣ المحور الأول: المعايير العالمية للإفصاح المؤسسي (GRI Universal Standards: GRI 1, GRI 2, GRI 3)</h3>
            <ul>
                <li><b>GRI 1 (الأساسيات):</b> يحدد مبادئ إعداد التقارير المصرفية الأساسية (الدقة، القابلية للمقارنة، الوضوح، الموثوقية، والتوقيت المناسب) التي يجب الالتزام بها لضمان جودة الإفصاحات غير المالية.</li>
                <li><b>GRI 2 (الإفصاحات العامة والتفاصيل التنظيمية):</b> يتضمن تفاصيل أنشطة البنك المصرفي، هيكل الحوكمة وتكوين مجلس الإدارة، سياسات الإفصاح، استراتيجية الاستدامة، وطرق إشراك أصحاب المصلحة (Stakeholder Engagement).</li>
                <li><b>GRI 3 (الموضوعات الجوهرية - Material Topics):</b> إرشادات دقيقة لتحديد الموضوعات ذات الأولوية القصوى بناءً على تقييم التأثيرات الاقتصادية والبيئية والاجتماعية الفعلية والمحتملة لأنشطة البنوك.</li>
            </ul>

            <h3 style="color: {CBE_NAVY}; margin-top: 25px;">2️⃣ المحور الثاني: الحوكمة المؤسسية وإدارة المخاطر الاستراتيجية (ISSB S1 & GRI 2)</h3>
            <ul>
                <li><b>هيكل الإشراف والمساءلة الحوكمية:</b> إفصاح البنك عن دور مجلس الإدارة واللجان المنبثقة عنه (لجنة الاستدامة، لجنة المخاطر، ولجنة المراجعة) في توجيه ومراقبة المخاطر والفرص المتعلقة بالاستدامة والتمويل المستدام.</li>
                <li><b>تكامل الاستراتيجية ونماذج أعمال البنك:</b> توضيح كيفية تأثير المخاطر والفرص البيئية والاجتماعية على استراتيجية البنك بعيدة المدى، خطط أعماله الائتمانية، وقرارات تخصيص رأس المال.</li>
                <li><b>أطر إدارة المخاطر الكلية:</b> سياسات دمج المخاطر البيئية والاجتماعية ومخاطر الحوكمة (ESG) ضمن السياسات الائتمانية وإدارة المخاطر المؤسسية للبنك.</li>
                <li><b>سياسات النزاهة ومكافحة الفساد:</b> الإفصاح عن مدونة السلوك الأخلاقي المصرفي، آليات الإبلاغ عن المخالفات، سياسات منع تضارب المصالح، ومكافحة غسل الأموال.</li>
            </ul>

            <h3 style="color: {CBE_NAVY}; margin-top: 25px;">3️⃣ المحور الثالث: الإفصاحات البيئية وتمويل المناخ والطاقة (GRI 302/303/305 & ISSB S2)</h3>
            <ul>
                <li><b>إدارة البصمة الكربونية التشغيلية (Scopes 1, 2, 3):</b> قياس والإفصاح الشفاف عن الانبعاثات المباشرة وغير المباشرة الناشئة عن عمليات فروع البنك ومراكز البيانات وسلسلة التوريد.</li>
                <li><b>محفظة التمويل الأخضر والأصول المستدامة:</b> قياس نسبة وحجم المحفظة الائتمانية الموجهة لمشروعات الطاقة المتجددة، كفاءة الطاقة، والنقل المستدام، بالإضافة إلى إصدار السندات الخضراء (Green Bonds).</li>
                <li><b>اختبارات التحمل المناخي (Climate Stress Testing):</b> مدى جاهزية البنك لتقييم واختبار تأثير المخاطر المناخية الطبيعية والانتقالية على جودة أصوله ومحفظة عملائه الكبار.</li>
                <li><b>إفصاحات التمويل المرتبط بالمناخ (Financed Emissions):</b> تقييم الانبعاثات المُمولة عبر القطاعات عالية الانبعاثات ووضع خطط انتقالية واضحة لإزالة الكربون (Net-Zero Transition Plans).</li>
            </ul>

            <h3 style="color: {CBE_NAVY}; margin-top: 25px;">4️⃣ المحور الرابع: الإفصاحات المجتمعية والشمول المالي ورأس المال البشري (GRI 401/403/405/413)</h3>
            <ul>
                <li><b>الشمول المالي والتحول الرقمي المستدام:</b> حجم ونطاق التمويلات الموجهة للمشروعات الصغيرة والمتوسطة (SMEs), تمكين المرأة والشباب، وتوسيع نطاق الخدمات المصرفية الرقمية في كافة المحافظات.</li>
                <li><b>رأس المال البشري وتكافؤ الفرص:</b> سياسات التوظيف العادل، برامج التدريب والتطوير المستمر للعاملين بالقطاع المصرفي، نسب تمثيل المرأة في الإدارة العليا، ومؤشرات الصحة والسلامة المهنية.</li>
                <li><b>المسؤولية المجتمعية والاستثمار التنموي:</b> حجم الإنفاق المجتمعي الموجه لدعم المبادرات القومية (مثل قطاعات الصحة، التعليم، ودعم الأسر الأولى بالرعاية).</li>
                <li><b>حماية حقوق العملاء وأمن البيانات:</b> معايير حماية سرية بيانات العملاء، سياسات الشفافية في تسعير الخدمات المصرفية، والامتثال لقواعد حماية البيانات الشخصية والسيادة الرقمية (GDPR).</li>
            </ul>

            <h3 style="color: {CBE_NAVY}; margin-top: 25px;">5️⃣ المحور الخامس الموسع والمفصل: معايير تأثير أهداف التنمية المستدامة (UNDP SDG Impact Standards for Enterprises) ومقاييس الأداء الثلاثين (ESG)</h3>
            <p>يستند هذا المحور الاستراتيجي إلى إطار منهجي متكامل يربط بدقة بين <b>30 مؤشراً معيارياً للاستدامة (ESG)</b> مستمدة ومطورة من الوثائق التوجيهية للاتحاد الدولي للبورصات (WFE)، معايير المبادرة العالمية للتقارير (GRI)، ومعايير برنامج الأمم المتحدة الإنمائي لتأثير أهداف التنمية المستدامة (UNDP SDG Impact Standards). وتنقسم هذه المؤشرات بدقة إلى ثلاثة قطاعات رئيسية موجهة لعمليات القطاع المصرفي:</p>
            
            <div style="background: #F8FAFC; padding: 18px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; margin-top: 15px; margin-bottom: 15px;">
                <h4 style="color: {CBE_NAVY}; margin-top: 0;">🌱 أولاً: مؤشرات الأداء البيئي (Environmental Indicators - من المؤشر 1 إلى 9)</h4>
                <ul style="margin-bottom: 0;">
                    <li><b>المؤشر (1):</b> إجمالي انبعاثات الغازات الدفيئة المباشرة (Scope 1 GHG Emissions) الناشئة عن عمليات الفروع ومقار البنوك ومولدات الطاقة الاحتياطية.</li>
                    <li><b>المؤشر (2):</b> انبعاثات الغازات الدفيئة غير المباشرة المعتمدة على الطاقة المستهلكة (Scope 2 GHG Emissions) من الكهرباء والطاقة المشتراة.</li>
                    <li><b>المؤشر (3):</b> انبعاثات سلسلة التوريد والتمويل الموسعة (Scope 3 GHG Emissions / Financed Emissions) الناتجة عن المحفظة الائتمانية والتمويلية للعملاء والشركات الكبرى.</li>
                    <li><b>المؤشر (4):</b> مؤشر كثافة الانبعاثات الكربونية (Carbon Intensity Ratio) لكل مليون جنيه من الأصول المُموّلة أو الإيرادات التشغيلية.</li>
                    <li><b>المؤشر (5):</b> معدل استهلاك الطاقة الكلي ونسبة اعتماد البنك على مصادر الطاقة المتجددة والنظيفة (Renewable Energy Consumption Ratio).</li>
                    <li><b>المؤشر (6):</b> كفاءة إدارة الموارد المائية ومعدلات الاستهلاك وترشيد المياه في المباني الإدارية الرئيسية والمقار والفروع.</li>
                    <li><b>المؤشر (7):</b> إدارة النفايات الصلبة والسائلة، ومعدلات إعادة التدوير، والسياسات المعتمدة للتخلص الآمن من النفايات الإلكترونية والورقية (E-Waste & Paperless Banking).</li>
                    <li><b>المؤشر (8):</b> وجود وفاعلية "السياسات البيئية المعتمدة" من مجلس الإدارة وتكاملها مع السياسات الائتمانية للبنك.</li>
                    <li><b>المؤشر (9):</b> نظام تقييم وإدارة مخاطر المناخ (Climate Risk Management Framework) واختبارات التحمل المرتبطة بالمخاطر الطبيعية والانتقالية.</li>
                </ul>
            </div>

            <div style="background: #F8FAFC; padding: 18px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; margin-top: 15px; margin-bottom: 15px;">
                <h4 style="color: {CBE_NAVY}; margin-top: 0;">👥 ثانياً: مؤشرات الأداء المجتمعي (Social Indicators - من المؤشر 10 إلى 20)</h4>
                <ul style="margin-bottom: 0;">
                    <li><b>المؤشر (10):</b> نسبة تعويضات وأجور المديرين التنفيذيين إلى متوسط أجور العاملين بالبنك (Executive-to-Median Worker Pay Ratio).</li>
                    <li><b>المؤشر (11):</b> مؤشر الفجوة في الأجور بين الجنسين (Gender Pay Gap Ratio) لضمان المساواة التامة في العوائد الوظيفية للأعمال المتساوية.</li>
                    <li><b>المؤشر (12):</b> معدل دوران الموظفين واستبقاء الكوادر البشرية (Employee Turnover & Retention Rate).</li>
                    <li><b>المؤشر (13):</b> نسبة التمثيل النسائي وتنوع الهيكل القيادي في المناصب الإدارية العليا ومجلس الإدارة (Gender Diversity in Leadership).</li>
                    <li><b>المؤشر (14):</b> معايير الصحة والسلامة المهنية (Occupational Health & Safety) ومعدلات الإصابات وحوادث العمل في مقار البنك.</li>
                    <li><b>المؤشر (15):</b> سياسات وممارسات مناهضة التحرش والتمييز في بيئة العمل وتوفير قنوات آمنة ومحايدة للشكاوى.</li>
                    <li><b>المؤشر (16):</b> التزام سلسلة التوريد بعدم التشغيل القسري أو تشغيل الأطفال (Anti-Child Labor & Forced Labor Compliance).</li>
                    <li><b>المؤشر (17):</b> احترام حقوق الإنسان الأساسية في كافة المعاملات والأنشطة المصرفية والتمويلية للبنك.</li>
                    <li><b>المؤشر (18):</b> حجم ونطاق استثمارات ومبادرات المسؤولية المجتمعية والإنفاق التنموي الموجه لدعم قطاعات الصحة والتعليم.</li>
                    <li><b>المؤشر (19):</b> مؤشرات الشمول المالي وتوسيع قاعدة المستفيدين من الخدمات المصرفية الرقمية والمشروعات الصغيرة (Financial Inclusion Index).</li>
                    <li><b>المؤشر (20):</b> برامج التدريب والتطوير المستمر وساعات التدريب السنوية المخصصة لكل موظف لدعم رأس المال البشري.</li>
                </ul>
            </div>

            <div style="background: #F8FAFC; padding: 18px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; margin-top: 15px; margin-bottom: 15px;">
                <h4 style="color: {CBE_NAVY}; margin-top: 0;">🏛️ ثالثاً: مؤشرات الحوكمة والشفافية والالتزام (Governance & Transparency - من المؤشر 21 إلى 30)</h4>
                <ul style="margin-bottom: 0;">
                    <li><b>المؤشر (21):</b> التنوع الهيكلي والمهني في تشكيل مجلس الإدارة (Board Diversity & Expertise).</li>
                    <li><b>المؤشر (22):</b> نسبة الأعضاء المستقلين غير التنفيذيين في مجلس الإدارة ولجان المراجعة والترشيحات (Independent Board Members Ratio).</li>
                    <li><b>المؤشر (23):</b> وجود حوافز ومكافطات مرتبطة تحقيق مستهدفات الاستدامة وخفض الانبعاثات للقيادات التنفيذية (Sustainability-linked Executive Compensation).</li>
                    <li><b>المؤشر (24):</b> مدونة قواعد سلوك الموردين والشركاء التجاريين ومعايير تقييمهم بيئياً ومجتمعياً (Supplier Code of Conduct).</li>
                    <li><b>المؤشر (25):</b> فاعلية سياسات وإجراءات مكافحة الفساد، الرشوة، وغسل الأموال (Anti-Corruption & Anti-Bribery Policies).</li>
                    <li><b>المؤشر (26):</b> سياسات حماية سرية البيانات الشخصية للعملاء والسيادة الرقمية (GDPR & Data Privacy Compliance).</li>
                    <li><b>المؤشر (27):</b> كفاءة أمن المعلومات والحصانة السيبرانية لمنصات المعلومات الذكية (Cybersecurity & Information Security Resilience).</li>
                    <li><b>المؤشر (28):</b> آليات الإفصاح المالي وغير المالي ودورية إعداد التقارير وفق معايير (GRI و ISSB).</li>
                    <li><b>المؤشر (29):</b> إدارة وتجنب حالات تعارض المصالح (Conflict of Interest Management) على مستوى أعضاء المجلس والإدارة العليا.</li>
                    <li><b>المؤشر (30):</b> الحصول على التوكيد والتدقيق الخارجي المستقل (Independent External Assurance) لتقرير الاستدامة من جهة رقابية معتمدة.</li>
                </ul>
            </div>

            <h3 style="color: {CBE_NAVY}; margin-top: 25px;">🎯 التركيز على اتخاذ القرار الداخلي والتوكيد الخارجي (SDG Impact Integration):</h3>
            <p>لا تقتصر معايير تأثير أهداف التنمية المستدامة (UNDP SDG Impact Standards) على مجرد إعداد التقارير اللاحقة، بل تمتد لتشكل <b>منهجية إدارية واستراتيجية لاتخاذ القرار القيادي الداخلي</b>، حيث يتم دمج تقييم التأثير (Impact Management) في صلب العمليات الاستثمارية، تخصيص المحفظة الائتمانية، وتوجيه السياسات المؤسسية نحو تعظيم العائد المجتمعي والبيئي بالتوازي مع العائد المالي. ويتم تتويج هذه المنظومة بإخضاع كافة البيانات والمؤشرات لعمليات <b>تدقيق وتوكيد خارجي مستقل (Third-party External Assurance)</b> لضمان أقصى درجات الموثوقية والشفافية أمام المستثمرين والجهات التنظيمية العالمية والمحلية.</p>
        </div>
        """
        st.markdown(flat_html(comprehensive_guide_html), unsafe_allow_html=True)

        guide_docx_content = f"""
        <html dir="rtl">
        <head><meta charset="utf-8"><title>الدليل العملي الشامل لإعداد تقارير الاستدامة</title></head>
        <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
            <h1 style="color: {CBE_NAVY}; text-align: center;">الدليل العملي الشامل والموسع لإعداد تقارير الاستدامة في القطاع المصرفي المصري</h1>
            <p style="text-align: center; color: #64748B;">مرجع منهجي وتطبيقي متكامل (GRI Standards / ISSB S1 & S2 / SDG Impact Standards)</p>
            <hr>
            {comprehensive_guide_html}
            <hr>
            <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">يُنصح بالمراجعة الدقيقة للقرارات الاستراتيجية</p>
            <p style="text-align: center; font-size: 12px; color: #64748B;">جميع الحقوق محفوظة للدراسة البحثية © 2026</p>
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
# التبويب السابع: الاستبيان الموجه إلى فرق العمل (معالج متعدد الخطوات التكيّفي 4-Step Wizard UX)
# ------------------------------------------------------------------------------
with tab7:
    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 15px;">
        <h3 style="color: #002B49; font-weight: 800; margin-bottom: 4px;">📋 الاستبيان الموجه إلى فرق العمل في البنوك (عينة الدراسة الميدانية)</h3>
        <p style="color: #475569; font-size: 14px;">استمارة الاستبيان الميداني المعتمدة لجمع آراء وتقييمات فرق العمل والقيادات المصرفية حول محاور المنصة.</p>
    </div>
    """, unsafe_allow_html=True)

    # تنويه مدة تعبئة الاستبيان
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%); padding: 12px 18px; border-radius: 10px; border: 1.5px solid {CBE_GOLD}; text-align: center; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);" dir="rtl">
        <span style="font-weight: 800; color: {CBE_NAVY}; font-size: 14.5px;">⏳ تنويه: استغراق تعبئة هذا الاستبيان لا يتجاوز 15 دقيقة تقريباً لضمان دقة الاستجابات.</span>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # القوائم الموسعة للخطاب الموجه والتعريفات الإجرائية
    # --------------------------------------------------------------------------
    with st.expander("🏛️ عرض ترويسة جهة الدراسة والبحث العلمي والخطاب الموجه (اضغط للتمديد أو التقليص)", expanded=False):
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 10px; line-height: 1.9;" dir="rtl">
            <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 12px; margin-bottom: 15px;">
                <h4 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">جامعة عين شمس | كلية الدراسات العليا والبحوث البيئية | قسم العلوم الاقتصادية والإدارية والقانونية البيئية</h4>
            </div>
            <p><b>السادة الأفاضل/ .................................................................</b></p>
            <p><b>السلام عليكم ورحمة الله وبركاته،,,</b></p>
            <p>في إطار متطلبات الحصول على درجة دكتوراة فلسفة العلوم الاقتصادية والإدارية والقانونية يقوم الباحث بإعداد دراسة تطبيقية بعنوان:</p>
            <div style="background: {CBE_BG}; padding: 12px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; text-align: center; font-weight: bold; color: {CBE_NAVY}; margin: 10px 0;">
                نموذج مقترح لتعزيز الحوكمة المؤسسية باستخدام منصة معلومات ذكية: بالتطبيق على تقارير الاستدامة
            </div>
            <p>ونظراً لما تتمتعون به من خبرة ودراية في هذا المجال الحيوي؛ نتشرف بدعوة سيادتكم للمشاركة في هذا البحث من خلال الإجابة على عبارات الاستبيان المرفق، وتحديد مدى موافقتكم عليها بما ترونه مناسباً، علما بأن هذه الدراسة تهدف إلى تقديم حلول مبتكرة تعتمد على الذكاء الاصطناعي لتعزيز الحوكمة المؤسسية ودعم السيادة الرقمية في البنوك المصرية.</p>
            <p>كما نؤكد لسيادتكم أن كافة البيانات والآراء ستحاط بالسرية التامة، ولن تستخدم إلا لأغراض البحث العلمي فقط.</p>
            <p><b>وتفضلوا بقبول فائق التقدير والاحترام،,,</b></p>
            <p style="margin-bottom: 0;">
                <b>الباحث:</b> أيمن محمد إبراهيم الدسوقي (مدرس مساعد إدارة المعرفة – معهد التخطيط القومي)<br>
                <b>تحت إشراف:</b><br>
                • أ.د. ممدوح عبدالعزيز رفاعي (أستاذ إدارة الأعمال - كلية التجارة - جامعة عين شمس)<br>
                • أ.د. محمد ماجد صلاح الدين خشبة (أستاذ إدارة الأعمال - مركز التخطيط والتنمية الصناعية - معهد التخطيط القومي)<br>
                • د. إسلام محمد حجازي (أستاذ مساعد بقسم علوم الحاسب - كلية الحاسبات والمعلومات - جامعة عين شمس)
            </p>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📚 أولاً: مصطلحات تعريفية (اضغط للاطلاع على التعريفات الإجرائية)", expanded=False):
        st.markdown(f"""
        <div dir="rtl" style="text-align: right; line-height: 1.9;">
            <p>لضمان وحدة المفهوم ودقة الاستجابة، يرجى التكرم بالاطلاع على التعريفات الإجرائية التالية للمصطلحات المستخدمة في هذا الاستبيان:</p>
            <ul>
                <li><b>منصة المعلومات الذكية (Smart Information Platform - SIP):</b> نظام تقني متكامل يعتمد على دمج تقنيات البيانات الضخمة (Big Data) وخوارزميات الذكاء الاصطناعي التوليدي (Generative AI)؛ بهدف تجميع ومعالجة البيانات المصرفية من مصادرها المختلفة وتحويلها آلياً إلى مؤشرات دقيقة.</li>
                <li><b>نماذج اللغة الكبيرة الموطنة (Localized Large Language Models - LLMs):</b> استخدام نماذج الذكاء الاصطناعي مفتوحة المصدر أو الهجينة وتأمين قنوات اتصالها سحابياً بروابط مشفرة ومعززة بآليات استرجاع الأدلة (RAG).</li>
                <li><b>الحوكمة المؤسسية (Institutional Governance - IG):</b> الإطار الشامل من القواعد والعمليات التي تضمن توجيه وإدارة المؤسسة المصرفية بنزاهة وشفافية.</li>
                <li><b>تقارير الاستدامة (Sustainability Reporting - SR):</b> عملية الإفصاح الدوري عن أداء البنك في المجالات البيئية والاجتماعية والحوكمة (ESG).</li>
                <li><b>مؤشر الحوكمة الذكية المستدامة (SSGI):</b> مؤشر مركب مقترح لقياس مستوى نضج البنك في دمج ممارسات الحوكمة مع متطلبات الاستدامة عبر التمكين الرقمي.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # تهيئة إدارة الحالة وتخزين البيانات (Session State Management)
    # --------------------------------------------------------------------------
    if "survey_wizard_step" not in st.session_state:
        st.session_state.survey_wizard_step = 1

    likert_mapping = {
        "غير موافق تماماً": 1,
        "غير موافق": 2,
        "محايد": 3,
        "موافق": 4,
        "موافق تماماً": 5
    }
    likert_options = ["غير موافق تماماً", "غير موافق", "محايد", "موافق", "موافق تماماً"]

    # تحديد التخصص الوظيفي وتحديد العبارات المستهدفة ديناميكياً
    spec_field = st.session_state.get("spec_field_u_dyn", None)
    
    # تحديد نطاق العبارات المخصصة لكل تخصص
    if spec_field == "تكنولوجيا المعلومات/ التحول الرقمي":
        target_statements = list(range(1, 12))  # SIP (1-11)
    elif spec_field == "الحوكمة/ الالتزام/ المراجعة الداخلية" or spec_field == "إدارة المخاطر/ الائتمان":
        target_statements = list(range(12, 20)) # IG (12-19)
    elif spec_field == "الاستدامة/ المسؤولية المجتمعية":
        target_statements = list(range(20, 32)) # SR (20-31)
    else:
        # باقي التخصصات (مجلس الإدارة، الإدارة العليا، البحث والتطوير) تجيب على كافة العبارات
        target_statements = list(range(1, 32))

    # --------------------------------------------------------------------------
    # حساب نسبة الإكمال الحقيقية بمرونة وربطها بشريط التقدم
    # --------------------------------------------------------------------------
    total_required_items = len(target_statements) + 2  # العبارات المستهدفة + البيانات الأولية + الأوزان
    
    # التحقق من إكمال البيانات الأولية
    step1_completed = (
        st.session_state.get("survey_bank_user_main") not in [None, "-- اختر البنك المصرفي --"] and
        st.session_state.get("org_nat_u_dyn") not in [None, "-- اختر طبيعة المؤسسة --"] and
        st.session_state.get("sci_deg_u_dyn") not in [None, "-- اختر المؤهل العلمي --"] and
        st.session_state.get("spec_field_u_dyn") not in [None, "-- اختر مجال التخصص الوظيفي --"] and
        st.session_state.get("job_level_u_dyn") not in [None, "-- اختر المستوى الوظيفي --"] and
        st.session_state.get("exp_yrs_u_dyn") not in [None, "-- اختر سنوات الخبرة --"] and
        st.session_state.get("is_listed_u_dyn") is not None
    )

    answered_stmt_count = sum(1 for i in target_statements if st.session_state.get(f"stmt_{i}") is not None)
    step1_score = 1 if step1_completed else 0
    weights_score = 1 if (st.session_state.get("weight_sip_input", 40) + st.session_state.get("weight_ig_input", 30) + st.session_state.get("weight_sr_input", 30)) == 100 else 0

    current_progress_count = step1_score + answered_stmt_count + weights_score
    progress_percentage = min(100, int((current_progress_count / total_required_items) * 100))

    # --------------------------------------------------------------------------
    # شريط التقدم التفاعلي والعناوين
    # --------------------------------------------------------------------------
    step_titles = {
        1: "المرحلة الأولى: البيانات الأولية والمهنية الإلزامية",
        2: "المرحلة الثانية: منصات المعلومات الذكية (SIP)",
        3: "المرحلة الثالثة: الحوكمة المؤسسية والامتثال (IG)",
        4: "المرحلة الرابعة: تقارير الاستدامة (SR) والأوزان والملاحظات"
    }

    step_num = st.session_state.survey_wizard_step

    st.markdown(f"""
    <div dir="rtl" style="background: #FFFFFF; border: 1.5px solid {CBE_GOLD}; border-radius: 12px; padding: 18px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-weight: 800; color: {CBE_NAVY}; font-size: 15px;">📍 {step_titles[step_num]}</span>
            <span style="font-weight: 800; color: {CBE_GOLD}; font-size: 14px;">نسبة إكمال الاستبيان التفاعلي: {progress_percentage}%</span>
        </div>
        <div style="background-color: #E2E8F0; border-radius: 10px; height: 10px; width: 100%; overflow: hidden;">
            <div style="background: linear-gradient(90deg, {CBE_GOLD} 0%, {CBE_NAVY} 100%); width: {progress_percentage}%; height: 100%; transition: width 0.4s ease;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 12px; font-size: 12px; font-weight: 700; color: #64748B;">
            <span style="color: {'#002B49' if step_num == 1 else '#94A3B8'};">1. البيانات الأولية</span>
            <span style="color: {'#002B49' if step_num == 2 else '#94A3B8'};">2. منصات SIP</span>
            <span style="color: {'#002B49' if step_num == 3 else '#94A3B8'};">3. الحوكمة IG</span>
            <span style="color: {'#002B49' if step_num == 4 else '#94A3B8'};">4. الاستدامة SR والأوزان</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # دالة تعريض وتقييم العبارة المصرفية
    def render_wizard_statement(num, text):
        st.markdown(f"""
        <div style="background: #F8FAFC; padding: 12px 16px; border-radius: 8px; border: 1px solid #E2E8F0; margin-bottom: 8px;" dir="rtl">
            <span style="font-weight: bold; color: {CBE_NAVY}; font-size: 14px;">({num}) {text}</span>
        </div>
        """, unsafe_allow_html=True)
        
        saved_val = st.session_state.get(f"stmt_{num}", None)
        ans = st.radio(
            f"تقييم العبارة {num}",
            likert_options,
            index=likert_options.index(saved_val) if saved_val in likert_options else None,
            horizontal=True,
            label_visibility="collapsed",
            key=f"stmt_{num}"
        )
        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
        return ans

    # --------------------------------------------------------------------------
    # المرحلة الأولى: البيانات الأولية والمهنية (جميع الاختيارات خالية وتعيين الإلزام)
    # --------------------------------------------------------------------------
    if step_num == 1:
        st.markdown(f"""
        <div dir="rtl" style="background: #FFFFFF; padding: 22px; border-radius: 12px; border-right: 5px solid {CBE_NAVY}; border-top: 1px solid #E2E8F0; border-left: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;">
            <h4 style="color: {CBE_NAVY}; font-weight: 800; margin-bottom: 6px;">👤 المرحلة الأولى: البيانات الأولية والمهنية للمستجيب (حقول إلزامية)</h4>
            <p style="color: #EF4444; font-size: 12.5px; font-weight: 700; margin-bottom: 15px;">⚠️ يرجى اختيار الإجابة المناسبة لكل بند؛ حيث لن يمكنك الانتقال للمرحلة التالية إلا بعد تعبئة كافة الحقول.</p>
        """, unsafe_allow_html=True)
        
        col_inf1, col_inf2 = st.columns(2, gap="medium")
        with col_inf1:
            banks_options_none = ["-- اختر البنك المصرفي --"] + BANKS_LIST_AR
            survey_bank_sel = st.selectbox(
                "اختر البنك المصرفي *",
                banks_options_none,
                index=0 if st.session_state.get("survey_bank_user_main") is None else banks_options_none.index(st.session_state.get("survey_bank_user_main", banks_options_none[0])),
                key="survey_bank_user_main"
            )

            org_nat_options = ["-- اختر طبيعة المؤسسة --", "بنك قطاع عام/ حكومي", "بنك قطاع خاص مشترك", "بنك إسلامي", "بنك عربي/ أجنبي", "جهة رقابية ك(البنك المركزي / الرقابة المالية)", "مؤسسة أكاديمية أو شركة تكنولوجيا مالية", "أخرى"]
            org_nature_u = st.selectbox(
                "طبيعة المؤسسة *",
                org_nat_options,
                index=0 if st.session_state.get("org_nat_u_dyn") is None else org_nat_options.index(st.session_state.get("org_nat_u_dyn", org_nat_options[0])),
                key="org_nat_u_dyn"
            )

            sci_deg_options = ["-- اختر المؤهل العلمي --", "دكتوراه", "ماجستير", "شهادة مهنية متخصصة مثل: CISA, GRCP", "ليسانس/ بكالوريوس"]
            sci_degree_u = st.selectbox(
                "المؤهل العلمي *",
                sci_deg_options,
                index=0 if st.session_state.get("sci_deg_u_dyn") is None else sci_deg_options.index(st.session_state.get("sci_deg_u_dyn", sci_deg_options[0])),
                key="sci_deg_u_dyn"
            )

        with col_inf2:
            spec_field_options = [
                "-- اختر مجال التخصص الوظيفي --",
                "مجلس الإدارة/ الإدارة العليا العامة",
                "الحوكمة/ الالتزام/ المراجعة الداخلية",
                "الاستدامة/ المسؤولية المجتمعية",
                "تكنولوجيا المعلومات/ التحول الرقمي",
                "إدارة المخاطر/ الائتمان",
                "البحث/ التطوير أو أخرى"
            ]
            spec_field_u = st.selectbox(
                "مجال التخصص الوظيفي *",
                spec_field_options,
                index=0 if st.session_state.get("spec_field_u_dyn") is None else spec_field_options.index(st.session_state.get("spec_field_u_dyn", spec_field_options[0])),
                key="spec_field_u_dyn"
            )

            job_level_options = ["-- اختر المستوى الوظيفي --", "رئيس/ عضو مجلس إدارة", "رئيس قطاع/ مساعد مدير عام", "مدير إدارة/ مدير عام", "خبير/ مستشار/ كبير أخصائيين", "مستوى إشرافي", "أخرى"]
            job_level_u = st.selectbox(
                "المستوى الوظيفي *",
                job_level_options,
                index=0 if st.session_state.get("job_level_u_dyn") is None else job_level_options.index(st.session_state.get("job_level_u_dyn", job_level_options[0])),
                key="job_level_u_dyn"
            )

            exp_yrs_options = ["-- اختر سنوات الخبرة --", "أقل من 10 سنوات", "من 10 سنوات إلى أقل من 15 سنة", "من 15 سنة إلى أقل من 20 سنة", "20 سنة فأكثر"]
            exp_years_u = st.selectbox(
                "سنـوات الخبرة في القطاع المصرفي *",
                exp_yrs_options,
                index=0 if st.session_state.get("exp_yrs_u_dyn") is None else exp_yrs_options.index(st.session_state.get("exp_yrs_u_dyn", exp_yrs_options[0])),
                key="exp_yrs_u_dyn"
            )

        is_listed_saved = st.session_state.get("is_listed_u_dyn", None)
        is_listed_u = st.radio(
            "هل المؤسسة التي تعمل بها مقيدة بالبورصة المصرية؟ *",
            ["نعم", "لا"],
            index=["نعم", "لا"].index(is_listed_saved) if is_listed_saved in ["نعم", "لا"] else None,
            horizontal=True,
            key="is_listed_u_dyn"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # المرحلة الثانية: منصات المعلومات الذكية SIP (العبارات 1 إلى 11)
    # --------------------------------------------------------------------------
    elif step_num == 2:
        st.markdown(f"""
        <div dir="rtl" style="background: #FFFFFF; padding: 22px; border-radius: 12px; border-right: 5px solid {CBE_GOLD}; border-top: 1px solid #E2E8F0; border-left: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;">
            <h4 style="color: {CBE_NAVY}; font-weight: 800; margin-bottom: 10px;">💻 المرحلة الثانية: محور منصة المعلومات الذكية (SIP)</h4>
            <p style="color: #64748B; font-size: 13px;">مقياس التقييم: (1) غير موافق تماماً | (2) غير موافق | (3) محايد | (4) موافق | (5) موافق تماماً</p>
        """, unsafe_allow_html=True)

        if 1 not in target_statements:
            st.info("ℹ️ بناءً على تخصصك الوظيفي المحدد، تم تخصيص المحاور الأكثر صلة بطبيعة عملك. يمكنك الانتقال للمرحلة القادمة أو التخطي مباشرة للأوزان والملاحظات.")
        else:
            render_wizard_statement(1, "يمتلك البنك بنية تحتية تتيح تجميع البيانات التاريخية والآنية من كافة الفروع والإدارات بشكل مركزي وموحد.")
            render_wizard_statement(2, "تتطلب طبيعة البيانات المصرفية الضخمة وغير المهيكلة اعتماد منصة ذكية تتجاوز قدرات النظم التقليدية في التجميع والتحليل.")
            render_wizard_statement(3, "يساهم الاعتماد على تقنية الاسترجاع المعزز بالتوليد (RAG) في ضمان دقة نتائج الذكاء الاصطناعي وتقليل احتمالات الهلوسة المعلوماتية.")
            render_wizard_statement(4, "يعد دمج نماذج اللغة الكبيرة (LLMs) توجهاً ضرورياً لتحويل النصوص السردية في التقارير إلى مؤشرات رقمية قابلة للقياس.")

            st.markdown(f"<div style='background: {CBE_BG}; padding: 6px 12px; font-weight: bold; color: {CBE_NAVY}; border-radius: 4px; margin: 12px 0;'>الامتثال التقني</div>", unsafe_allow_html=True)
            render_wizard_statement(5, "يسهم تطبيق العمل بمنصات الذكاء الاصطناعي التوليدي (GenAI) في تقليل الاعتماد البشري في إعداد التقارير، مما يخفض الأخطاء والتحيزات.")
            render_wizard_statement(6, "تساهم قدرة النموذج المقترح على استيعاب معايير (IFRS S1/S2) بشكل آلي في تحقيق مرونة عالية مع التغيرات التنظيمية السريعة.")
            render_wizard_statement(7, "تعمل الخوارزميات الذكية بالمنصة على التحقق الآلي من استيفاء كافة العناصر الإلزامية التي يفرضها البنك المركزي المصري (CBE).")

            st.markdown(f"<div style='background: {CBE_BG}; padding: 6px 12px; font-weight: bold; color: {CBE_NAVY}; border-radius: 4px; margin: 12px 0;'>التخطيط والمراقبة بعد النشر</div>", unsafe_allow_html=True)
            render_wizard_statement(8, "يوفر النموذج تغذية راجعة (Feedback Loop) تسمح بتعديل الخطط بناءً على المتغيرات وفجوات الأداء المرصودة.")
            render_wizard_statement(9, "تساهم أدوات المراقبة الذكية في الكشف المبكر عن أي شبهة غسل أخضر (Greenwashing) في البيانات قبل تفاقمها.")

            st.markdown(f"<div style='background: {CBE_BG}; padding: 6px 12px; font-weight: bold; color: {CBE_NAVY}; border-radius: 4px; margin: 12px 0;'>التكامل والخصوصية</div>", unsafe_allow_html=True)
            render_wizard_statement(10, "يمثل الاعتماد على آليات الفلترة المحلية للوثائق والمعالجة المشفرة عبر روابط ذكية مدمجة الضمانة المثلى لحماية السرية المصرفية وأمن البيانات.")
            render_wizard_statement(11, "يسمح النموذج بتكامل تقني (APIs) مع الأنظمة المصرفية الأساسية (Core Banking) لضمان دقة البيانات المستقاة.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # المرحلة الثالثة: الحوكمة المؤسسية IG (العبارات 12 إلى 19)
    # --------------------------------------------------------------------------
    elif step_num == 3:
        st.markdown(f"""
        <div dir="rtl" style="background: #FFFFFF; padding: 22px; border-radius: 12px; border-right: 5px solid {CBE_NAVY}; border-top: 1px solid #E2E8F0; border-left: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;">
            <h4 style="color: {CBE_NAVY}; font-weight: 800; margin-bottom: 10px;">🏛️ المرحلة الثالثة: محور الحوكمة المؤسسية والامتثال (IG)</h4>
            <p style="color: #64748B; font-size: 13px;">مقياس التقييم: (1) غير موافق تماماً | (2) غير موافق | (3) محايد | (4) موافق | (5) موافق تماماً</p>
        """, unsafe_allow_html=True)

        if 12 not in target_statements:
            st.info("ℹ️ تم تجاوز هذه المرحلة بناءً على تخصصك الوظيفي المحدد للوصول المباشر للمحاور المتخصصة أو الأوزان النسبية.")
        else:
            st.markdown(f"<div style='background: {CBE_BG}; padding: 6px 12px; font-weight: bold; color: {CBE_NAVY}; border-radius: 4px; margin: 10px 0;'>الشفافية والإفصاح</div>", unsafe_allow_html=True)
            render_wizard_statement(12, "تساهم الشفافية الرقمية والتحول نحو الإفصاح الذكي عبر المنصة في تقليص فجوة عدم تماثل المعلومات بين الإدارة والمساهمين والمستثمرين.")
            render_wizard_statement(13, "يساهم النموذج في رفع جودة الإفصاح المؤسسي عبر تقديم بيانات دقيقة وواضحة لأصحاب المصلحة.")

            st.markdown(f"<div style='background: {CBE_BG}; padding: 6px 12px; font-weight: bold; color: {CBE_NAVY}; border-radius: 4px; margin: 10px 0;'>المتابعة والمساءلة</div>", unsafe_allow_html=True)
            render_wizard_statement(14, "يعزز النموذج من فاعلية لجنة المراجعة في تتبع الأثر الفعلي لقرارات الاستدامة.")
            render_wizard_statement(15, "يساعد النموذج مجلس الإدارة على تفعيل المساءلة بناءً على بيانات موضوعية مستخرجة آلياً لا تقبل التأويل.")

            st.markdown(f"<div style='background: {CBE_BG}; padding: 6px 12px; font-weight: bold; color: {CBE_NAVY}; border-radius: 4px; margin: 10px 0;'>العدالة والمساواة</div>", unsafe_allow_html=True)
            render_wizard_statement(16, "تعزز مخرجات النموذج من سياسات الشمول والعدالة في توزيع الفرص الائتمانية ومنع التمييز الخوارزمي بناءً على معايير ESG موضوعية.")

            st.markdown(f"<div style='background: {CBE_BG}; padding: 6px 12px; font-weight: bold; color: {CBE_NAVY}; border-radius: 4px; margin: 10px 0;'>المشاركة وسيادة القانون ومجلس الإدارة</div>", unsafe_allow_html=True)
            render_wizard_statement(17, "يسهم النموذج في تعزيز التواصل الفعال وإشراك الأطراف المعنية في تحديد الموضوعات الجوهرية (Materiality).")
            render_wizard_statement(18, "يعزز النموذج من قدرة البنك على الاستجابة الفورية للتعديلات التشريعية والمصرفية ورصد حالات عدم الامتثال القانوني بدقة.")
            render_wizard_statement(19, "تسهم لوحات المعلومات التفاعلية والتقارير الفورية التي توفرها المنصة في دعم مجلس الإدارة في المراقبة الاستباقية وصنع القرار.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # المرحلة الرابعة: تقارير الاستدامة SR والأوزان والملاحظات (العبارات 20 إلى 31 والإرسال)
    # --------------------------------------------------------------------------
    elif step_num == 4:
        st.markdown(f"""
        <div dir="rtl" style="background: #FFFFFF; padding: 22px; border-radius: 12px; border-right: 5px solid {CBE_GOLD}; border-top: 1px solid #E2E8F0; border-left: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;">
            <h4 style="color: {CBE_NAVY}; font-weight: 800; margin-bottom: 10px;">🌱 المرحلة الرابعة: محور تقارير الاستدامة (SR) والأوزان والملاحظات</h4>
            <p style="color: #64748B; font-size: 13px;">مقياس التقييم: (1) غير موافق تماماً | (2) غير موافق | (3) محايد | (4) موافق | (5) موافق تماماً</p>
        """, unsafe_allow_html=True)

        if 20 in target_statements:
            st.markdown(f"<div style='background: {CBE_BG}; padding: 6px 12px; font-weight: bold; color: {CBE_NAVY}; border-radius: 4px; margin: 10px 0;'>الاستراتيجية والبعد البيئي والاجتماعي والاقتصادي</div>", unsafe_allow_html=True)
            render_wizard_statement(20, "تعكس التقارير الصادرة عن النموذج دمجاً حقيقياً لأهداف التنمية المستدامة (SDGs) ورؤية مصر 2030 في استراتيجية البنك طويلة الأجل.")
            render_wizard_statement(21, "يتيح النموذج قياس والإفصاح بدقة عن البصمة الكربونية للبنك (النطاقات 1، 2، 3) وتوضيح حجم التمويل الأخضر والطاقة المتجددة (Green Finance).")
            render_wizard_statement(22, "يوفر النموذج مؤشرات كمية دقيقة لقياس كفاءة رصد معدلات خفض استهلاك الموارد الداخلية (الطاقة، المياه، الورق).")
            render_wizard_statement(23, "تفصح التقارير بالأرقام عن جهود البنك في تعزيز الشمول المالي ووصول الخدمات للفئات المهمشة والمناطق النائية.")
            render_wizard_statement(24, "يتم قياس أثر مبادرات المسؤولية المجتمعية (CSR) وتوضيح العائد الاجتماعي منها (SROI) بشكل كمي.")
            render_wizard_statement(25, "توضح التقارير العوائد الاقتصادية المباشرة وغير المباشرة لتبني ممارسات الاستدامة ودعم التوجه نحو المشتريات المستدامة.")

            st.markdown(f"<div style='background: {CBE_BG}; padding: 6px 12px; font-weight: bold; color: {CBE_NAVY}; border-radius: 4px; margin: 10px 0;'>إدارة المخاطر والمقاييس والتنوع</div>", unsafe_allow_html=True)
            render_wizard_statement(26, "يتم دمج مخاطر المناخ والاستدامة (ESG Risks) ضمن إطار إدارة المخاطر الكلي للبنك بشكل منهجي.")
            render_wizard_statement(27, "توجد خطط طوارئ واستمرارية أعمال محدثة لمواجهة الأزمات المحتملة المرتبطة بالاستدامة أو التقنية.")
            render_wizard_statement(28, "يتم وضع أهداف مستقبلية (Targets) ذكية ومحددة زمنياً لكل محور من محاور الاستدامة.")
            render_wizard_statement(29, "يضمن النموذج دقة احتساب المؤشرات المركبة، ويسهل عملية المقارنة المعيارية (Benchmarking) مع المنافسين.")
            render_wizard_statement(30, "يحرص البنك على تنوع الخبرات والخلفيات المهنية في تشكيل مجلس الإدارة والإدارة العليا.")
            render_wizard_statement(31, "تسمح المنصة برصد ومتابعة معدلات تمكين المرأة وزيادة تمثيلها في المناصب القيادية ومراكز اتخاذ القرار بالقطاع المصرفي.")

        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown("<h5 style='color: #002B49; font-weight: 800;'>⚖️ تحديد الأوزان النسبية المقترحة للمحاور الثلاثة (متاح لجميع المستجيبين - المجموع = 100%)</h5>", unsafe_allow_html=True)
        
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            w_sip = st.number_input("منصات المعلومات الذكية: (%)", min_value=0, max_value=100, value=st.session_state.get("weight_sip_input", 40), key="weight_sip_input")
        with col_w2:
            w_ig = st.number_input("الحوكمة المؤسسية: (%)", min_value=0, max_value=100, value=st.session_state.get("weight_ig_input", 30), key="weight_ig_input")
        with col_w3:
            w_sr = st.number_input("تقارير الاستدامة: (%)", min_value=0, max_value=100, value=st.session_state.get("weight_sr_input", 30), key="weight_sr_input")

        total_weight = w_sip + w_ig + w_sr
        if total_weight != 100:
            st.error(f"⚠️ مجموع الأوزان الحالية هو ({total_weight}%). يجب أن يكون المجموع الكلي مساوياً لـ 100% تماماً.")
        else:
            st.success("✅ مجموع الأوزان متطابق وصحيح (100%).")

        survey_comments = st.text_area(
            "💬 مقترحات أو معوقات ترون أنها قد تؤثر على تطبيق هذا النموذج في البنوك المصرية:",
            value=st.session_state.get("user_survey_comments", ""),
            placeholder="اكتب ملاحظاتك ومقترحاتك هنا...",
            key="user_survey_comments"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # أزرار التوجيه والتنقل بالمعالج (Previous / Next Buttons UX)
    # --------------------------------------------------------------------------
    col_prev, col_spacer, col_next = st.columns([1, 2, 1])

    with col_prev:
        if step_num > 1:
            if st.button("⬅️ الخطوة السابقة", use_container_width=True, type="secondary"):
                st.session_state.survey_wizard_step -= 1
                st.rerun()

    with col_next:
        if step_num < 4:
            # زر الخطوة التالية مع التحقق الشامل من الشروط الإلزامية في الخطوة 1
            next_disabled = False
            if step_num == 1 and not step1_completed:
                next_disabled = True
                st.warning("⚠️ يرجى استكمال اختيار جميع الحقول الإلزامية أولاً لتفعيل التنسيق والانتقال.")
            
            if st.button("الخطوة التالية ➡️", use_container_width=True, type="primary", disabled=next_disabled):
                st.session_state.survey_wizard_step += 1
                st.rerun()

        elif step_num == 4:
            submit_survey_btn = st.button("📤 إرسال وحفظ الاستبيان النهائي", use_container_width=True, type="primary", key="submit_survey_final_btn")

            if submit_survey_btn:
                # التحقق والتأكد من استكمال الشروط
                statement_answers_dict = {}
                sip_scores, ig_scores, sr_scores = [], [], []

                missing_answers = False
                for i in range(1, 32):
                    ans_str = st.session_state.get(f"stmt_{i}")
                    if i in target_statements:
                        if ans_str in likert_mapping:
                            score_val = likert_mapping[ans_str]
                            statement_answers_dict[f"العبارة_{i}"] = score_val
                            if i <= 11:
                                sip_scores.append(score_val)
                            elif i <= 19:
                                ig_scores.append(score_val)
                            else:
                                sr_scores.append(score_val)
                        else:
                            missing_answers = True
                            statement_answers_dict[f"العبارة_{i}"] = None
                    else:
                        statement_answers_dict[f"العبارة_{i}"] = "غير موجه للتخصص"

                survey_bank_sel = st.session_state.get("survey_bank_user_main")
                w_sip_val = st.session_state.get("weight_sip_input", 40)
                w_ig_val = st.session_state.get("weight_ig_input", 30)
                w_sr_val = st.session_state.get("weight_sr_input", 30)
                tot_w = w_sip_val + w_ig_val + w_sr_val

                if not step1_completed:
                    st.warning("⚠️ يرجى العودة للمرحلة الأولى واستكمال كافة حقول البيانات الإلزامية قبل الإرسال.")
                elif tot_w != 100:
                    st.error("⚠️ لا يمكن الحفظ: مجموع الأوزان النسبية للمحاور يجب أن يساوي 100%.")
                elif missing_answers:
                    st.error("⚠️ يرجى تقييم كافة العبارات المخصصة لتخصصك قبل الإرسال النهائي.")
                else:
                    avg_sip_val = round(sum(sip_scores) / len(sip_scores), 2) if sip_scores else "N/A"
                    avg_ig_val = round(sum(ig_scores) / len(ig_scores), 2) if ig_scores else "N/A"
                    avg_sr_val = round(sum(sr_scores) / len(sr_scores), 2) if sr_scores else "N/A"

                    new_survey_rec = {
                        "معرف الاستجابة": f"SRV-{datetime.now().strftime('%H%M%S')}",
                        "اسم البنك": clean_text(survey_bank_sel),
                        "طبيعة المؤسسة": clean_text(st.session_state.get("org_nat_u_dyn", "")),
                        "المؤهل العلمي": clean_text(st.session_state.get("sci_deg_u_dyn", "")),
                        "المسمى الوظيفي / الإدارة": f"{st.session_state.get('spec_field_u_dyn', '')} - {st.session_state.get('job_level_u_dyn', '')}",
                        "المستوى الوظيفي": clean_text(st.session_state.get("job_level_u_dyn", "")),
                        "سنوات الخبرة": st.session_state.get("exp_yrs_u_dyn", ""),
                        "مقيدة بالبورصة": st.session_state.get("is_listed_u_dyn", ""),
                        "وزن منصات المعلومات (%)": w_sip_val,
                        "وزن الحوكمة المؤسسية (%)": w_ig_val,
                        "وزن تقارير الاستدامة (%)": w_sr_val,
                        "متوسط محور منصات المعلومات": avg_sip_val,
                        "متوسط محور الحوكمة المؤسسية": avg_ig_val,
                        "متوسط محور تقارير الاستدامة": avg_sr_val,
                        **statement_answers_dict,
                        "ملاحظات وتوصيات إضافية": clean_text(st.session_state.get("user_survey_comments", "")),
                        "وقت الإرسال": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    current_surveys = load_survey_log_from_file()
                    current_surveys.append(new_survey_rec)
                    try:
                        pd.DataFrame(current_surveys).to_csv(SURVEY_LOG_FILE, index=False, encoding='utf-8-sig')
                        st.markdown("""
                        <div style="background: #D1FAE5; padding: 18px; border-radius: 10px; border: 1.5px solid #059669; text-align: center; margin-top: 15px;" dir="rtl">
                            <h4 style="color: #065F46; margin: 0;">✅ تم تسجيل وحفظ الاستجابة بنجاح بكافة تفاصيل العبارات والأوزان في شيت الإكسيل الميداني!</h4>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء حفظ الاستجابة: {e}")

    # --------------------------------------------------------------------------
    # لوحة التحليل الإداري للأدمن
    # --------------------------------------------------------------------------
    if st.session_state.get("role") == "admin":
        st.markdown("---")
        st.markdown("#### 📊 لوحة تحليل استجابات الاستبيان (خاص بالأدمن):")
        updated_surveys_data = load_survey_log_from_file()
        if updated_surveys_data:
            df_surveys = pd.DataFrame(updated_surveys_data)
            st.markdown(f"<p><b>إجمالي الاستجابات المرصودة في شيت الإكسيل:</b> {len(df_surveys)} استجابة</p>", unsafe_allow_html=True)
            st.dataframe(df_surveys, use_container_width=True)

            csv_surveys_bytes = df_surveys.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل شيت إكسيل استجابات الاستبيان الميداني بالكامل (Excel/CSV)",
                data=csv_surveys_bytes,
                file_name="شيت_إكسيل_استجابات_استبيان_فرق_العمل_المصرفي_التفصيلي.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("📋 لم يتم تسجيل أي استجابات في شيت الإكسيل حتى الآن.")

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748B; font-size: 13px; padding: 10px 0;" dir="rtl">
        جميع الحقوق محفوظة للدراسة البحثية © 2026
    </div>
    """, unsafe_allow_html=True)
# ------------------------------------------------------------------------------
# التبويب الثامن: دليل المستخدم الرسمي للمنصة والتوثيق المنهجي PDF
# ------------------------------------------------------------------------------
with tab8:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📖 دليل المستخدم الرسمي والتوثيق المنهجي لمنصة الحوكمة المصرفية (PDF / Docs)</h3>
        <p>استعراض وتحميل دليل المستخدم الرسمي والتوثيق المنهجي للمنصة لتمكين المحكمين والباحثين من الاطلاع الفوري على فلسفة وأقسام المنصة .</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    user_manual_html = f"""
    <div style="background: #FFFFFF; padding: 35px; border-radius: 14px; border: 1.5px solid {CBE_GOLD}; line-height: 2.1;" dir="rtl">
        <h2 style="color: {CBE_NAVY}; margin-top: 0; text-align: center;">📖 دليل المستخدم الرسمي والتوثيق المنهجي للمنصة الوطنية الذكية</h2>
        <p style="text-align: center; color: #475569; font-size: 14.5px;">دليل تشغيلي وتعريفي شامل موجه للمحكمين، أعضاء لجنة المناقشة، الباحثين، والقيادات المصرفية لاستخدام المنصة بكفاءة تامة.</p>
        <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 25px 0;">

        <h3 style="color: {CBE_NAVY};">1️⃣ نظرة عامة ورؤية المنصة</h3>
        <p>تمثل هذه المنصة الإطار التطبيقي الميداني والبرمجي لرسالة الدكتوراه في العلوم البيئية (كلية الدراسات والبحوث البيئية- جامعة عين شمس) للباحث/ <b>أيمن الدسوقي</b>. والتي تستهدف توفير بيئة ذكية متكاملة ومستقلة لتعزيز حوكمة البنوك المصرية عبر تقارير الاستدامة ومؤشر الحوكمة الذكية المستدامة (SSGI)، مع دعم اتخاذ القرار، محاكاة السيناريوهات الاستراتيجية، جمع استبيانات فرق العمل، واستخلاص الإجابات والتقارير عبر محرك ذكاء اصطناعي مستقل (RAG).</p>

        <h3 style="color: {CBE_NAVY}; margin-top: 25px;">2️⃣ دليل الأقسام والأقسام التفاعلية في المنصة</h3>
        <ul>
            <li><b>🎯 اسأل المنصة:</b> محرك استعلام ذكي ومخصص لكل بنك على حدة للإجابة عن أسئلة التأسيس، الحوكمة، والاستدامة مع منع التخمين والهلوسة.</li>
            <li><b>📊 مؤشر الحوكمة المركب (SSGI):</b> أداة تشخيص قياسي تدمج منصات المعلومات (40%)، الحوكمة المؤسسية (30%)، وتقارير الاستدامة (30%) مع تحليل رداري وترتيب تنازلي.</li>
            <li><b>📈 محاكي السياسات (Policy Simulator):</b> أداة استشرافية لاختبار أثر التدخلات الاستراتيجية والسيناريوهات (التشاؤمي، المعتدل، الطموح) وصافي التغير.</li>
            <li><b>🛡️ لوحة دعم اتخاذ القرار:</b> توفير توصيات استراتيجية وتوجيهية مخصصة لكل بنك حسب قراءته التشخيصية.</li>
            <li><b>📑 التقرير التنفيذي الموحد:</b> أداة لتوليد تقرير شامل ومحدث ديناميكياً لكافة البنوك المسجلة مع إمكانية التحميل بصيغة (Word).</li>
            <li><b>🌿 مولد تقارير الاستدامة والدليل العملي:</b> توليد مسودات تقارير الاستدامة (GRI/ISSB/SDG Impact) والاطلاع على 30 مؤشراً لـ (ESG).</li>
            <li><b>📋 استبيان فرق العمل المصرفي:</b> استمارة ميدانية لجمع استجابات العاملين بالبنوك في شيت الإكسيل وتحليلها وتصديرها.</li>
            <li><b>📖 دليل المستخدم الرسمي (هذا القسم):</b> توثيق شامل لكل وظائف المنصة وإتاحة التصدير المباشر للملفات.</li>
        </ul>
    </div>
    """
    
    st.markdown(flat_html(user_manual_html), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    manual_download_data = f"""
    <html dir="rtl">
    <head><meta charset="utf-8"><title>دليل المستخدم الرسمي للمنصة الوطنية الذكية</title></head>
    <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
        {user_manual_html}
        <hr>
        <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">يُنصح بالمراجعة الدقيقة للقرارات الاستراتيجية</p>
        <p style="text-align: center; font-size: 12px; color: #64748B;">جميع الحقوق محفوظة للدراسة البحثية © 2026</p>
    </body>
    </html>
    """
    
    st.download_button(
        label="📥 تحميل دليل المستخدم الرسمي والتوثيق المنهجي للمنصة (Word / PDF)",
        data=manual_download_data.encode("utf-8-sig"),
        file_name="دليل_المستخدم_الرسمي_للمنصة_المصرفية.doc",
        mime="application/msword",
        use_container_width=True
    )

# ------------------------------------------------------------------------------
# التبويب التاسع: لوحة تحكم المشرف والزوار (Admin Dashboard)
# ------------------------------------------------------------------------------
if tab9 is not None:
    with tab9:
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
