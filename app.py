import random
import io
import os
import json
import re
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# إعدادات صفحة Streamlit وتطبيق الهوية البصرية المصرفية (RTL)
# ==============================================================================
st.set_page_config(
    page_title="المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة",
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
    padding: 8px 6px !important;
    font-weight: 700 !important;
    border: 1px solid #002B49 !important;
    text-align: right !important;
    font-size: 12px !important;
    white-space: nowrap !important;
}}

.custom-rtl-table td {{
    padding: 6px 6px !important;
    border: 1px solid #E2E8F0 !important;
    color: #1E293B !important;
    font-size: 11.5px !important;
    text-align: right !important;
    line-height: 1.3 !important;
}}

.custom-rtl-table tr:nth-child(even) {{
    background-color: #F8FAFC !important;
}}

.custom-rtl-table tr:hover {{
    background-color: #FEF3C7 !important;
}}

div.stButton > button {{
    width: 100% !important;
    border-radius: 8px !important;
    font-family: 'Cairo', sans-serif !important;
    font-weight: 600 !important;
    text-align: right !important;
    justify-content: flex-start !important;
    padding-right: 15px !important;
    background-color: #FFFFFF !important;
    color: {CBE_NAVY} !important;
    border: 1px solid #CBD5E1 !important;
    margin-bottom: 4px !important;
    transition: all 0.2s ease !important;
}}

div.stButton > button:hover {{
    background-color: {CBE_GOLD} !important;
    color: {CBE_NAVY} !important;
    border-color: {CBE_GOLD} !important;
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
    padding: 10px 6px !important;
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
# دالة استخراج عنوان الـ IP الحقيقي للزائر بدقة
# ==============================================================================
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

LOG_FILE_PATH = "visitors_log.csv"

def init_visitor_log_file():
    if not os.path.exists(LOG_FILE_PATH):
        try:
            df_init = pd.DataFrame(columns=["عنوان IP", "اسم المستخدم", "الدور", "وقت الدخول"])
            df_init.to_csv(LOG_FILE_PATH, index=False, encoding='utf-8-sig')
        except Exception:
            pass

init_visitor_log_file()

def load_visitors_log_from_file():
    if os.path.exists(LOG_FILE_PATH):
        try:
            df = pd.read_csv(LOG_FILE_PATH, encoding='utf-8-sig')
            return df.to_dict(orient="records")
        except Exception:
            return []
    return []

def append_visitor_to_file(visitor_entry):
    existing_logs = load_visitors_log_from_file()
    exists = any(
        item.get("عنوان IP") == visitor_entry.get("عنوان IP") and 
        item.get("اسم المستخدم") == visitor_entry.get("اسم المستخدم") 
        for item in existing_logs
    )
    if not exists:
        existing_logs.append(visitor_entry)
        df_out = pd.DataFrame(existing_logs)
        df_out.to_csv(LOG_FILE_PATH, index=False, encoding='utf-8-sig')

# ==============================================================================
# إدارة جلسة الدخول والصلاحيات
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

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
            
            username = st.text_input("اسم المستخدم (Username)", placeholder="أدخل اسم المستخدم...")
            password = st.text_input("كلمة المرور (Password)", type="password", placeholder="أدخل كلمة المرور...")
            
            if st.button("🔐 تسجيل الدخول للمنصة", use_container_width=True):
                visitor_ip_addr = get_visitor_ip()
                current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if username == "admin" and password == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.current_user = "admin"
                    new_record = {
                        "عنوان IP": visitor_ip_addr,
                        "اسم المستخدم": "admin",
                        "الدور": "مشرف (Admin)",
                        "وقت الدخول": current_time_str
                    }
                    append_visitor_to_file(new_record)
                    st.rerun()
                elif username == "user" and password == "123":
                    st.session_state.authenticated = True
                    st.session_state.current_user = "user"
                    new_record = {
                        "عنوان IP": visitor_ip_addr,
                        "اسم المستخدم": "user",
                        "الدور": "مستخدم عادي (User)",
                        "وقت الدخول": current_time_str
                    }
                    append_visitor_to_file(new_record)
                    st.rerun()
                else:
                    st.error("⚠️ اسم المستخدم أو كلمة المرور خاطئة.")
    st.stop()

logout_col1, logout_col2 = st.columns([6, 1])
with logout_col2:
    if st.button("🚪 تسجيل الخروج", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.session_state.current_user = ""
        st.rerun()

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
    "البنك الأهلي اليوناني أو البنك الوطني اليوناني",
    "بنك سيتي بنك CITIBANK"
]

def get_colored_score_html(score):
    if score >= 80:
        return f"{score}% (أداء مرتفع 🟢)"
    elif score >= 51:
        return f"{score}% (أداء متوسط 🟡)"
    else:
        return f"{score}% (فجوة هيكلية حرجة 🔴)"

def describe_sip(val, bank_name):
    return f"تتميز منصات المعلومات الذكية والبنية التقنية لـ ({bank_name}) بكفاءة تبلغ ({val}%)، مما يضمن تدفقاً آمناً ولحظياً للبيانات الرقارية والمالية وفق معايير الحصانة السيبرانية."

def describe_ig(val, bank_name):
    return f"تشير مؤشرات الحوكمة المؤسسية لـ ({bank_name}) عند ({val}%) إلى التزام تام باستقلالية مجلس الإدارة وتفعيل لجان التدقيق والالتزام الرقابي."

def describe_sr(val, bank_name):
    return f"تعكس تقارير الاستدامة والتمويل الأخضر لـ ({bank_name}) بمعدل ({val}%) دمجاً فعالاً لمعايير المخاطر البيئية والمناخية وإفصاحات الاستدامة الدولية."

def get_bank_profile_features(bank_name):
    return f"يعد ({bank_name}) ركيزة استراتيجية أساسية في القطاع المصرفي المصري، حيث يساهم بفاعلية في تمويل الاقتصاد القومي، دعم الشمول المالي، وتحقيق مستهدفات التنمية المستدامة ورؤية مصر 2030."

if "history_state" not in st.session_state:
    st.session_state.history_state = []
if "simulated_results_dict" not in st.session_state:
    st.session_state.simulated_results_dict = {}
if "decision_results_dict" not in st.session_state:
    st.session_state.decision_results_dict = {}

# ==============================================================================
# الهيدر والشريط الإخباري
# ==============================================================================
st.markdown(f"""
<div class="header-center">
<h1>مقترح المنصة الوطنية الذكية لتعزيز الحوكمة وتقارير الاستدامة بالقطاع المصرفي المصري</h1>
<h3>إطار تطبيقي مقترح ضمن متطلبات نيل درجة دكتوراة الفلسفة في العلوم البيئية - جامعة عين شمس</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <span class="ticker-item">🏛️ مقترح المنصة الوطنية الذكية لتعزيز الحوكمة وتقارير الاستدامة بالقطاع المصرفي المصري</span>
    <span class="ticker-item">| 📊 مؤشر الحوكمة الذكية المستدامة (SSGI) والأبعاد الثلاثة الرئيسية</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي لاختبار السيناريوهات الاستراتيجية (Multiple Regression)</span>
    <span class="ticker-item">| 🛡️ لوحة دعم اتخاذ القرار وتوطين المعايير الرقابية وإطار دونيلا ميدوز لنقاط الرفع</span>
    <span class="ticker-item">| 📑 التقرير التنفيذي الموحد للقطاع المصرفي | جميع الحقوق محفوظة للدراسة البحثية © 2026</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# التقسيم الرئيسي إلى التبويبات
# ==============================================================================
if st.session_state.current_user == "admin":
    tab1, tab2, tab3, tab4, tab5, tab6, tab_admin = st.tabs([
        "📊 تشخيص مؤشر الحوكمة (SSGI)", 
        "📈 محاكي السياسات (Policy Simulator)", 
        "🛡️ لوحة دعم اتخاذ القرار", 
        "📑 التقرير التنفيذي الموحد",
        "🌿 مولد تقارير الاستدامة (GRI/ISSB)",
        "📖 دليل المستخدم الرسمي",
        "🔒 سجل الزوار والأفراد (Admin)"
    ])
else:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 تشخيص مؤشر الحوكمة (SSGI)", 
        "📈 محاكي السياسات (Policy Simulator)", 
        "🛡️ لوحة دعم اتخاذ القرار", 
        "📑 التقرير التنفيذي الموحد",
        "🌿 مولد تقارير الاستدامة (GRI/ISSB)",
        "📖 دليل المستخدم الرسمي"
    ])

# ------------------------------------------------------------------------------
# التبويب الأول: تشخيص مؤشر الحوكمة (SSGI)
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📊 التشخيص القياسي لمؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
        <p>إمكانية تشخيص البنوك المختارة عبر المحاور الثلاثة مع تسجيل وثبات النتائج في الجدول التراكمي وإدارة السجلات الموضح أدناه.</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        bank_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, key="t1_bank")
        sip_slider = st.slider("1️⃣ منصات المعلومات الذكية وحوكمة البيانات (وزن 40%)", 0, 100, 85, key="t1_sip")
        ig_slider = st.slider("2️⃣ الحوكمة المؤسسية والامتثال (وزن 30%)", 0, 100, 88, key="t1_ig")
        sr_slider = st.slider("3️⃣ تقارير الاستدامة والتمويل الأخضر (وزن 30%)", 0, 100, 82, key="t1_sr")

        calc_clicked = st.button("🚀 احسب وسجل قياس البنك", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if calc_clicked:
            if bank_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي حقيقي من القائمة لتنفيذ التشخيص القياسي.")
            else:
                weights = {'SIP': 0.40, 'IG': 0.30, 'SR': 0.30}
                final_score = round((sip_slider * weights['SIP']) + (ig_slider * weights['IG']) + (sr_slider * weights['SR']), 2)
                score_str_plain = get_colored_score_html(final_score)

                if final_score >= 80:
                    diagnosis = "🟢 أداء مصرفي مرتفع ومنتظم، نحو الريادة والسيادة الرقمية المستدامة."
                    detailed_diag = f"🟢 **جاهزية متقدمة ومستدامة:** إجمالي المؤشر المركب {score_str_plain}. تعكس هذه النتيجة تفوقاً هيكلياً في حوكمة ({bank_sel})، وبنية تقنية متطورة لتشغيل تقارير الاستدامة المصرفية بكفاءة عالية."
                elif final_score >= 51:
                    diagnosis = "🟡 أداء متوسط، يتطلب تعزيزاً استباقياً لمعالجة الفجوات الهيكلية."
                    detailed_diag = f"🟡 **جاهزية متوسطة تتطلب تدخلاً استباقياً:** إجمالي المؤشر المركب {score_str_plain}. تشير المؤشرات إلى توازن يواجه بعض الاختناقات في تدفقات البيانات أو تقارير ESG لـ ({bank_sel})."
                else:
                    diagnosis = "🔴 فجوة هيكلية حرجة تستوجب التدخل الفوري وتفعيل محاكي السياسات."
                    detailed_diag = f"🔴 **فجوة هيكلية حرجة:** إجمالي المؤشر المركب {score_str_plain}. توضح القراءة الحالية لوجود اختناقات عميقة في البنية التحتية والامتثال لـ ({bank_sel})."

                entry = {
                    "البنك": bank_sel,
                    "المؤشر المركب (SSGI)": final_score,
                    "منصات المعلومات (40%)": sip_slider,
                    "الحوكمة المؤسسية (30%)": ig_slider,
                    "تقارير الاستدامة (30%)": sr_slider,
                    "التقييم التشخيصي": diagnosis
                }

                updated = False
                for idx, item in enumerate(st.session_state.history_state):
                    if item["البنك"] == bank_sel:
                        st.session_state.history_state[idx] = entry
                        updated = True
                        break
                if not updated:
                    st.session_state.history_state.append(entry)

                st.markdown(f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                  <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 12px;">📊 نتائج التشخيص المنظومي للبنك (إطار SSGI)</h3>
                  <p style="font-size: 15px; margin-bottom: 8px;"><b>البنك الخاضع للتشخيص:</b> <span style="color: {CBE_NAVY}; font-weight: bold;">{bank_sel}</span></p>
                  <p style="font-size: 16px; margin-bottom: 12px;"><b>القيمة المركبة للمؤشر (SSGI):</b> <span style="font-size: 18px;">{score_str_plain}</span></p>
                  <div style="background: {CBE_BG}; padding: 16px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 10px;">
                    <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY};">التقييم التشخيصي والتفصيل المنظومي:</p>
                    <p style="margin: 0; color: #1E293B; font-size: 14.5px;">{detailed_diag}</p>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                categories = ['منصات المعلومات (40%)', 'الحوكمة المؤسسية (30%)', 'تقارير الاستدامة (30%)']
                scores_list = [sip_slider, ig_slider, sr_slider]
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=scores_list, theta=categories, fill='toself', name=bank_sel, line_color=CBE_GOLD))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor="#FFFFFF", font=dict(family="Cairo", size=13))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 يرجى اختيار البنك وضبط درجات المحاور ثم الضغط على زر الحساب لعرض النتائج والتمثيل الراداري.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📋 قائمة ترتيب البنوك المسجلة</h3>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.history_state:
        df_history = pd.DataFrame(st.session_state.history_state).sort_values(by="المؤشر المركب (SSGI)", ascending=False).reset_index(drop=True)
        
        table_html = """
<div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 280px;">
<table class="custom-rtl-table">
<thead>
<tr>
<th style="width: 30px; text-align: center;">م</th>
<th>البنك</th>
<th>المؤشر المركب</th>
<th>منصات المعلومات</th>
<th>الحوكمة المؤسسية</th>
<th>تقارير الاستدامة</th>
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
<td style="font-weight: bold; color: {CBE_GOLD};">{row['المؤشر المركب (SSGI)']}%</td>
<td>{row['منصات المعلومات (40%)']}%</td>
<td>{row['الحوكمة المؤسسية (30%)']}%</td>
<td>{row['تقارير الاستدامة (30%)']}%</td>
<td style="font-size: 11px;">{row['التقييم التشخيصي']}</td>
</tr>
"""
        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

        csv_data = df_history.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تحميل جدول ترتيب البنوك المسجلة (Excel/CSV)",
            data=csv_data,
            file_name="ترتيب_البنوك_المسجلة_SSGI.csv",
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

# ------------------------------------------------------------------------------
# التبويب الثاني: محاكي السياسات (Policy Simulator)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🔬 محاكي السياسات الاستشرافي والمتابعة التراكمية للسيناريوهات</h3>
        <p>استشراف أثر التدخلات التكنولوجية واستثمارات حوكمة البيانات وتقارير الاستدامة عبر النمذجة القياسية ومتغيرات التحفيز الاستراتيجي.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI في القسم الأول.")
    else:
        col_sim_in, col_sim_out = st.columns([1, 2], gap="large")

        with col_sim_in:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            recorded_banks_sim = [item["البنك"] for item in st.session_state.history_state]
            sim_bank_sel = st.selectbox("اختر البنك للمحاكاة", recorded_banks_sim, key="sim_bank")
            base_ssgi_input = st.slider("قيمة المؤشر الافتراضي الحالي", 30.0, 100.0, 85.0, 0.5, key="sim_base")
            
            scenario_dropdown = st.selectbox("اختر السيناريو الاستراتيجي", [
                "📉 السيناريو التشاؤمي (تراجع الامتثال وضغط المخاطر)",
                "📊 السيناريو المعتدل / التفاؤلي (تطوير تدريجي لمنصات البيانات)",
                "🚀 السيناريو الطموح / الاستباقي (تحول رقمي شامل ومعايير تمويل أخضر متقدمة)"
            ], index=1, key="sim_scen")
            
            var1_sip = st.slider("1️⃣ نسبة الزيادة في كفاءة منصات المعلومات (SIP) (%)", 0, 50, 20, key="sim_v1")
            var2_ig = st.slider("2️⃣ نسبة الزيادة في استقلالية وحوكمة الإدارة (%)", 0, 50, 15, key="sim_v2")
            var3_sr = st.slider("3️⃣ نسبة الزيادة في أصول التمويل الأخضر (GAR) (%)", 0, 50, 25, key="sim_v3")

            run_sim_btn = st.button("📋 إضافة وتثبيت سيناريو البنك", use_container_width=True, type="primary")
            
            if st.button("🗑️ مسح وإعادة تعيين استجابات المحاكي", use_container_width=True, type="secondary"):
                st.session_state.simulated_results_dict = {}
                st.success("✅ تم مسح جميع سيناريوهات المحاكي بنجاح.")
                st.rerun()

            sim_word_html = f"""
            <html dir="rtl">
            <head><meta charset="utf-8"><title>تقرير محاكي السياسات المصرفية</title></head>
            <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
                <h1 style="color: {CBE_NAVY}; text-align: center;">تقرير محاكي السياسات الاستشرافي والمتابعة التراكمية للسيناريوهات</h1>
                <p style="text-align: center; color: #64748B;">المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة</p>
                <hr>
                <h3>📋 مقارنة السيناريوهات المثبتة للبنوك:</h3>
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
                <p>يغطي هذا التقرير مخرجات النمذجة القياسية ومتغيرات التحفيز الاستراتيجي لصنّاع القرار المصرفي.</p>
                <hr>
                <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">يُنصح بالمراجعة الدقيقة للقرارات الاستراتيجية المصرفية</p>
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
                    s_val, i_val, r_val = 85, 88, 82
                    for item in st.session_state.history_state:
                        if item["البنك"] == sim_bank_sel:
                            base_val = item["المؤشر المركب (SSGI)"]
                            s_val = item["منصات المعلومات (40%)"]
                            i_val = item["الحوكمة المؤسسية (30%)"]
                            r_val = item["تقارير الاستدامة (30%)"]
                            break

                    combined_boost = (var1_sip * 0.4) + (var2_ig * 0.3) + (var3_sr * 0.3)

                    if scenario_dropdown.startswith("📉"):
                        simulated_val = max(0.0, base_val * 0.90)
                        analysis_text = f"تحذير استباقي لـ ({sim_bank_sel}): غياب الاستثمار في منصات المعلومات وتراجع الالتزام سيؤدي إلى انكماش أداء مؤشر الحوكمة."
                        action_plan = f"تفعيل حزم طوارئ رقابية وترميم قنوات تدفق البيانات لضمان عدم تأثر تصنيف البنك."
                    elif scenario_dropdown.startswith("📊"):
                        simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.0025)))
                        analysis_text = f"استقرار تطوري لـ ({sim_bank_sel}): نمو مستقر في كفاءة حوكمة البيانات والتمويل المستدام مدعوماً بتحديثات البنية التحتية."
                        action_plan = f"مواصلة تدريب الكوادر البشرية وتوسيع محفظة الأصول الخضراء."
                    else:
                        simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.0045)))
                        analysis_text = f"قفزة استراتيجية كبرى لـ ({sim_bank_sel}): نجاح شامل في تحقيق التحول الرقمي وتوطين معايير الاستدامة المصرفية (GRI/ISSB)."
                        action_plan = f"قيادة التحالفات المصرفية المستدامة وتوظيف تقنيات التكنولوجيا الرقابية (RegTech) بأعلى كفاءة."

                    simulated_val = round(simulated_val, 2)
                    delta = round(simulated_val - base_val, 2)
                    score_str_plain = get_colored_score_html(simulated_val)

                    deep_analysis = f"""
                    <div style="background: #F8FAFC; padding: 16px; border-radius: 8px; border: 1px solid #CBD5E1; margin-top: 10px;" dir="rtl">
                        <p style="font-weight: bold; color: {CBE_NAVY}; margin-bottom: 8px; text-align: right;">📊 التشخيص القياسي المخصص والمبني على محاور الحوكمة لـ ({sim_bank_sel}):</p>
                        <ul style="margin: 0; padding-right: 20px; color: #1E293B; line-height: 1.8; text-align: right;">
                            <li><b>1. منصات المعلومات (SIP):</b> {describe_sip(s_val, sim_bank_sel)}</li>
                            <li><b>2. الحوكمة المؤسسية (IG):</b> {describe_ig(i_val, sim_bank_sel)}</li>
                            <li><b>3. تقارير الاستدامة (SR):</b> {describe_sr(r_val, sim_bank_sel)}</li>
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

# ------------------------------------------------------------------------------
# التبويب الثالث: لوحة دعم اتخاذ القرار
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🛡️ لوحة دعم اتخاذ القرار وتوطين السياسات</h3>
        <p>استعراض وتثبيت التوصيات المخصصة لكل بنك مختص بديناميكية تمنع التكرار وتدعم متطلبات البنك المركزي المصري ومعايير الاستدامة.</p>
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
            generate_decision_btn = st.button("📋 إضافة وتثبيت توصيات البنك المختار", use_container_width=True, type="primary")
            
            if st.button("🗑️ مسح وإعادة تعيين لوحة القرار", use_container_width=True, type="secondary"):
                st.session_state.decision_results_dict = {}
                st.success("✅ تم مسح جميع توصيات لوحة القرار بنجاح.")
                st.rerun()

            dec_word_html = f"""
            <html dir="rtl">
            <head><meta charset="utf-8"><title>تقرير لوحة دعم القرار المصرفي</title></head>
            <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
                <h1 style="color: {CBE_NAVY}; text-align: center;">تقرير لوحة دعم اتخاذ القرار وتوطين السياسات</h1>
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
                <p>تعكس هذه التوصيات متطلبات الحصانة السيبرانية والتوطين الرقابي للقطاع المصرفي.</p>
                <hr>
                <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">يُنصح بالمراجعة الدقيقة للقرارات الاستراتيجية المصرفية</p>
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
                        score = bank_data["المؤشر المركب (SSGI)"]
                        s_val = bank_data["منصات المعلومات (40%)"]
                        i_val = bank_data["الحوكمة المؤسسية (30%)"]
                        r_val = bank_data["تقارير الاستدامة (30%)"]
                        score_str_plain = get_colored_score_html(score)

                        if score >= 80:
                            recs_list = [
                                f"<b>تعزيز ريادة الابتكار المصرفي لـ ({decision_bank_sel}):</b> توظيف منصات المعلومات المتقدمة ({s_val}%) لتصدير الخدمات الرقمية وتطبيق معايير التكنولوجيا الرقابية (RegTech).",
                                f"<b>الحوكمة المتقدمة:</b> استثمار استقلالية مجلس الإدارة ({i_val}%) لقيادة المبادرات الخضراء وإصدار تقارير استدامة توافق معايير ISSB."
                            ]
                            deep_analysis_text = f"""
- توصي المنصة بتأسيس <b>'لجنة سيادية للتحول الرقمي والمناخ'</b> مستفيدين من رصيد الحوكمة المرتفع المقدر بـ ({i_val}%).
- تفعيل أطر التمويل الأخضر لدعم المشروعات الصديقة للبيئة والنزول ببصمة الكربون المصرفية للحد الأدنى.
                            """
                        elif score >= 51:
                            recs_list = [
                                f"<b>ردم الفجوة الرقمية بـ ({decision_bank_sel}):</b> تطوير البنية التحتية لمنصات المعلومات المسجلة عند ({s_val}%).",
                                f"<b>تعزيز الرقابة الداخلية:</b> رفع كفاءة لجان التدقيق والالتزام لتعزيز الالتزام بمتطلبات البنك المركزي."
                            ]
                            deep_analysis_text = f"""
- تتطلب صانعة القرار تفعيل <b>'برامج الحصانة السيبرانية والتأمين المتقدم'</b> لرفع كفاءة منصات البيانات ({s_val}%).
- توسيع نطاق الشمول المالي وتمكين المشروعات الصغيرة والمتناهية الصغر وفق الأطر المستدامة.
                            """
                        else:
                            recs_list = [
                                f"<b>التدخل الاستباقي العاجل لـ ({decision_bank_sel}):</b> معالجة الاختناقات الهيكلية في البنية التقنية ومنصات المعلومات ({s_val}%).",
                                f"<b>إصلاح حوكمي شامل:</b> إعادة هيكلة لجان التدقيق وضبط الالتزام الرقابي لتفادي المخاطر التشغيلية."
                            ]
                            deep_analysis_text = f"""
- تفرض الضرورة القصوى استدعاء حزم طوارئ رقابية لترميم قواعد المعطيات والالتزام الصارم بتعليمات البنك المركزي المصري.
- وضع خطة عمل عاجلة لرفع نسبة مساهمة الأصول الخضراء ضمن المحفظة الائتمانية.
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

# ------------------------------------------------------------------------------
# التبويب الرابع: التقرير التنفيذي الموحد
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📑 أداة التقرير التنفيذي الموحد لحوكمة القطاع المصرفي</h3>
        <p>ملخص استراتيجي شامل يدمج نتائج التدقيق ونتائج محاكي السياسات ولوحة دعم اتخاذ القرار في تقرير موحد جاهز للعرض على القيادات العليا.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 تحديث وتوليد التقرير التنفيذي الموحد", use_container_width=True, type="primary"):
        if not st.session_state.history_state:
            st.warning("📂 لا توجد بيانات مسجلة كافية حتى الآن. يرجى إدخال تشخيص بنك واحد على الأقل في القسم الأول.")
        else:
            df_rep = pd.DataFrame(st.session_state.history_state).sort_values(
                by="المؤشر المركب (SSGI)", ascending=False
            ).reset_index(drop=True)
            
            top_row = df_rep.iloc[0]
            top_bank = top_row["البنك"]
            top_score = top_row["المؤشر المركب (SSGI)"]
            top_score_str = get_colored_score_html(top_score)
            bank_profile_text = get_bank_profile_features(top_bank)

            cards_html_list = []
            word_blocks_html = ""

            for idx, row in df_rep.iterrows():
                b_name = row['البنك']
                b_score = row['المؤشر المركب (SSGI)']
                b_diag = row['التقييم التشخيصي']
                
                s_val = row['منصات المعلومات (40%)']
                i_val = row['الحوكمة المؤسسية (30%)']
                r_val = row['تقارير الاستدامة (30%)']
                
                if b_score >= 80:
                    specific_strategic_angle = f"يتمتع بنك ({b_name}) بأداء مرتفع ومنتظم ({b_score}%), مما يمنحه ريادة في السيادة الرقمية وتطبيق أعلى معايير الحوكمة والتمويل المستدام بالقطاع المصرفي."
                    specific_policy_action = f"تأسيس 'لجنة استراتيجية للاستدامة والتكنولوجيا'، قيادة التحالفات المصرفية الخضراء، وتوظيف منصات المعلومات ({s_val}%)."
                elif b_score >= 51:
                    specific_strategic_angle = f"يسجل بنك ({b_name}) جاهزية متوسطة ({b_score}%) تتطلب تعزيزاً استباقياً لتدفقات البيانات الرقابية وإفصاحات الاستدامة."
                    specific_policy_action = f"تطوير البنية التقنية لـ ({s_val}%) وتعزيز أطر الالتزام ومواجهة مخاطر المناخ."
                else:
                    specific_strategic_angle = f"تظهر قراءة بنك ({b_name}) فجوة هيكلية حرجة ({b_score}%) تستوجب تدخلاً فورياً وإصلاحاً شاملاً للبنية التحتية والامتثال."
                    specific_policy_action = f"إعلان حالة طوارئ وتفعيل آليات محاكي السياسات لرفع كفاءة منصات المعلومات وحوكمة الإدارة."

                matched_sims = [s_key for s_key in st.session_state.simulated_results_dict.keys() if s_key.startswith(b_name)]
                if matched_sims:
                    latest_sim_key = matched_sims[-1]
                    sim_data_obj = st.session_state.simulated_results_dict[latest_sim_key]
                    sim_detail = (
                        f"تم تطبيق سيناريو ({sim_data_obj['scenario']}); "
                        f"حيث بلغت القيمة المتوقعة للمؤشر ({sim_data_obj['simulated_val']}%) بصافي تغير قدره ({sim_data_obj['delta']:+.2f}). "
                        f"<b>التحليل:</b> {sim_data_obj['analysis_text']} "
                        f"<b>خطة التحرك:</b> {sim_data_obj['action_plan']}"
                    )
                else:
                    sim_detail = "<span style='background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #FCD34D;'>⚠️ تنبيه توثيقي: لم يتم تسجيل أي سيناريو لهذا البنك.</span>"
                
                if b_name in st.session_state.decision_results_dict:
                    dec_item = st.session_state.decision_results_dict[b_name]
                    dec_detail = f"{dec_item['recs'][0]} — وكذلك: {dec_item['recs'][1]}"
                else:
                    dec_detail = "<span style='background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #FCD34D;'>⚠ تنبيه توثيقي: لم يتم اعتماد توصيات لوحة القرار لهذا البنك.</span>"

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
                        <li><b>محاور الحوكمة المرصودة:</b> منصات المعلومات ({s_val}%) | الحوكمة المؤسسية ({i_val}%) | تقارير الاستدامة ({r_val}%)</li>
                        <li><b>المسار التنفيذي الموصى به:</b> {specific_policy_action}</li>
                        <li style="margin-top: 8px;"><b>🔬 مخرجات محاكي السياسات:</b><br>{sim_detail}</li>
                        <li style="margin-top: 8px;"><b>🛡️ مخرجات لوحة دعم القرار:</b><br>{dec_detail}</li>
                    </ul>
                </div>
                """
                cards_html_list.append(single_card_html)
                word_blocks_html += single_card_html

            st.markdown(f"""
            <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 30px; border-radius: 14px; border: 2px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 6px 20px rgba(0,0,0,0.08);">
              <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 15px; margin-bottom: 25px;">
                <h2 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">📑 التقرير التنفيذي الموحد لحوكمة القطاع المصرفي</h2>
                <p style="color: #64748B; font-size: 14.5px; margin-top: 6px;">ملخص استراتيجي موجه للقيادات العليا وصناع القرار - بناءً على مخرجات الدراسة المنهجية (SSGI)</p>
              </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: {CBE_BG}; padding: 18px; border-radius: 10px; border-right: 5px solid {CBE_GOLD}; margin-bottom: 25px;" dir="rtl">
                <h4 style="color: {CBE_NAVY}; margin-top: 0;">🏆 مؤشرات الأداء العام والريادة المصرفية:</h4>
                <p style="margin-bottom: 8px;">يتصدر البنك التالي قائمة الحوكمة الذكية وفق الترتيب التنازلي للمؤشر المركب: <span style="font-weight: bold; color: {CBE_GOLD};">{top_bank}</span> بقيمة مركبة تبلغ {top_score_str}.</p>
                <p style="margin-bottom: 8px; line-height: 1.8;"><b>الملامح الاستراتيجية والدור المصرفي:</b> {bank_profile_text}</p>
                <p style="margin: 0;">إجمالي البنوك الخاضعة للتشخيص والتحليل المنظومي حتى الآن: <b>{len(df_rep)} بنك مصرفي</b>.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<h4 style='color: #002B49; margin-bottom: 12px;'>📋 ترتيب الملخص التراكمي للبنوك:</h4>", unsafe_allow_html=True)
            for idx, row in df_rep.iterrows():
                s = row['المؤشر المركب (SSGI)']
                s_str = get_colored_score_html(s)
                summary_card = f"""
                <div style="margin-bottom: 12px; line-height: 1.8; background: #F8FAFC; padding: 12px 16px; border-radius: 8px; border: 1px solid #E2E8F0;" dir="rtl">
                    <b>المركز ({idx + 1}): {row['البنك']}</b> — المؤشر المركب: {s_str} | منصات المعلومات: {row['منصات المعلومات (40%)']}% | الحوكمة المؤسسية: {row['الحوكمة المؤسسية (30%)']}% <br>
                    <span style="color: #475569; font-size: 13.5px;"><b>التقييم التشخيصي:</b> {row['التقييم التشخيصي']}</span>
                </div>
                """
                st.markdown(summary_card, unsafe_allow_html=True)

            for card_code in cards_html_list:
                st.markdown(card_code, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            word_content = f"""
            <html dir="rtl">
            <head><meta charset="utf-8"><title>التقرير التنفيذي الموحد</title></head>
            <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
                <h1 style="color: {CBE_NAVY}; text-align: center;">📑 التقرير التنفيذي الموحد لحوكمة القطاع المصرفي</h1>
                <p style="text-align: center; color: #64748B;">ملخص استراتيجي موجه للقيادات العليا (SSGI)</p>
                <hr>
                <h3>🏆 مؤشرات الأداء العام والريادة:</h3>
                <p>يتصدر البنك التالي القائمة: <b>{top_bank}</b> بقيمة مركبة تبلغ {top_score_str}.</p>
                <p><b>الملامح المؤسسية:</b> {bank_profile_text}</p>
                <p>إجمالي البنوك الخاضعة للتشخيص: <b>{len(df_rep)} بنك</b>.</p>
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
# التبويب الخامس: مولد تقارير الاستدامة (GRI / ISSB)
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🌿 إعداد مسودة تقارير الاستدامة (GRI / ISSB)</h3>
        <p>توليد مسودة أولية شاملة ومفصلة لتقارير الاستدامة والحوكمة والتمويل الأخضر لكل بنك، متضمنة الإشارات والتوجيهات وفق أحدث المعايير الدولية.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("⚠️ يرجى أولاً إجراء التشخيص القياسي للبنوك في القسم الأول لتوليد مسودة تقارير الاستدامة المخصصة.")
    else:
        recorded_banks_gri = [item["البنك"] for item in st.session_state.history_state]
        gri_bank_sel = st.selectbox("اختر البنك لتوليد مسودة تقرير الاستدامة", recorded_banks_gri, key="gri_bank")
        
        if st.button("🚀 توليد مسودة تقرير الاستدامة المصرفية (GRI / ISSB)", use_container_width=True, type="primary"):
            b_data = next((item for item in st.session_state.history_state if item["البنك"] == gri_bank_sel), None)
            if b_data:
                b_score = b_data["المؤشر المركب (SSGI)"]
                s_val = b_data["منصات المعلومات (40%)"]
                i_val = b_data["الحوكمة المؤسسية (30%)"]
                r_val = b_data["تقارير الاستدامة (30%)"]
                
                sim_match = [v for k, v in st.session_state.simulated_results_dict.items() if k.startswith(gri_bank_sel)]
                sim_text_info = sim_match[-1]['analysis_text'] if sim_match else "لم يتم رصد سيناريو محاكاة سابق؛ يعتمد التقرير على القراءة القياسية الراهنة."
                
                dec_match = st.session_state.decision_results_dict.get(gri_bank_sel, None)
                dec_text_info = f"{dec_match['recs'][0]} | {dec_match['recs'][1]}" if dec_match else "توصيات حوكمية قياسية متوافقة مع متطلبات البنك المركزي."

                gri_report_html = f"""
                <div style="background: #FFFFFF; padding: 30px; border-radius: 14px; border: 2px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 6px 20px rgba(0,0,0,0.08);" dir="rtl">
                    <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 15px; margin-bottom: 25px;">
                        <h2 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">🌿 مسودة تقرير الاستدامة المصرفية (GRI / ISSB)</h2>
                        <h3 style="color: {CBE_GOLD}; margin: 8px 0 0 0;">البنك المصرفي: {gri_bank_sel}</h3>
                        <p style="color: #64748B; font-size: 13.5px; margin-top: 5px;">تقرير مفصل يدمج مخرجات التشخيص، محاكي السياسات، ولوحة اتخاذ القرار وفق أطر الإفصاح المالي الدولي لعام 2026</p>
                    </div>

                    <h4 style="color: {CBE_NAVY}; border-right: 4px solid {CBE_GOLD}; padding-right: 10px;">1. الملخص التنفيذي والإطار العام للبنوك المستدامة:</h4>
                    <p>يستعرض هذا التقرير أداء <b>{gri_bank_sel}</b> في ضوء مؤشر الحوكمة الذكية المستدامة (SSGI)، مسجلاً قيمة مركبة تبلغ <b>{b_score}%</b>. يعكس التقرير التزام البنك بمعايير الشفافية، الإفصاح المالي، الحصانة السيبرانية، وتوجيه التمويلات نحو الاقتصاد الأخضر.</p>

                    <h4 style="color: {CBE_NAVY}; border-right: 4px solid {CBE_GOLD}; padding-right: 10px;">2. نتائج الأبعاد الثلاثة الرئيسية وتقييم الجاهزية:</h4>
                    <ul style="line-height: 1.8; color: #1E293B;">
                        <li><b>محور منصات المعلومات وحوكمة البيانات (SIP):</b> سجل كفاءة بنسبة <b>{s_val}%</b>. {describe_sip(s_val, gri_bank_sel)}</li>
                        <li><b>محور الحوكمة المؤسسية والامتثال (IG):</b> سجل أداء بنسبة <b>{i_val}%</b>. {describe_ig(i_val, gri_bank_sel)}</li>
                        <li><b>محور تقارير الاستدامة والتمويل الأخضر (SR):</b> سجل معدلاً بنسبة <b>{r_val}%</b>. {describe_sr(r_val, gri_bank_sel)}</li>
                    </ul>

                    <h4 style="color: {CBE_NAVY}; border-right: 4px solid {CBE_GOLD}; padding-right: 10px;">3. رؤية سيناريوهات محاكي السياسات وآفاق التطوير:</h4>
                    <p style="background: {CBE_BG}; padding: 12px; border-radius: 8px; border: 1px solid #E2E8F0;">{sim_text_info}</p>

                    <h4 style="color: {CBE_NAVY}; border-right: 4px solid {CBE_GOLD}; padding-right: 10px;">4. مخرجات لوحة دعم القرار والتوصيات الاستراتيجية المعتمدة:</h4>
                    <p style="background: {CBE_BG}; padding: 12px; border-radius: 8px; border: 1px solid #E2E8F0;">{dec_text_info}</p>

                    <h4 style="color: {CBE_NAVY}; border-right: 4px solid {CBE_GOLD}; padding-right: 10px;">5. التوصيات الختامية لإفصاحات GRI و ISSB:</h4>
                    <ul style="line-height: 1.8; color: #1E293B;">
                        <li>توسيع محفظة القروض الخضراء بنسبة لا تقل عن 25% سنوياً.</li>
                        <li>إدراج مخاطر المناخ بصفة دورية ضمن جدول أعمال لجنة المخاطر بمجلس الإدارة.</li>
                        <li>تعزيز الشمول المالي وتسهيل وصول الخدمات الرقمية لرائدات الأعمال والمشروعات المتوسطة والصغيرة.</li>
                    </ul>
                </div>
                """
                st.markdown(gri_report_html, unsafe_allow_html=True)

                st.download_button(
                    label="📥 تحميل مسودة تقرير الاستدامة (Word)",
                    data=gri_report_html.encode("utf-8-sig"),
                    file_name=f"تقرير_استدامة_{gri_bank_sel}.doc",
                    mime="application/msword",
                    use_container_width=True
                )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب السادس: دليل المستخدم الرسمي (User Guide)
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📖 دليل المستخدم الرسمي لمنصة "المنصة الوطنية الذكية" (PDF)</h3>
        <p>استعراض وتحميل دليل المستخدم والتوثيق المنهجي الرسمي للمنصة بصيغة PDF لتمكين المحكمين والمستخدمين من الاطلاع الفوري.</p>
    </div>
    """, unsafe_allow_html=True)

    user_guide_filename = "دليل المستخدم.pdf"
    with st.expander("📑 دليل المستخدم الرسمي للمنصة"):
        if os.path.exists(user_guide_filename):
            st.success(f"✅ ملف دليل المستخدم متوفر وجاهز للتحميل: `{user_guide_filename}`")
            with open(user_guide_filename, "rb") as f:
                pdf_bytes_ug = f.read()
            st.download_button(
                label="📥 تحميل دليل المستخدم الرسمي (PDF)",
                data=pdf_bytes_ug,
                file_name=user_guide_filename,
                mime="application/pdf",
                use_container_width=True,
                key="dl_user_guide"
            )
        else:
            st.warning(f"⚠️ تنبيه: الملف `{user_guide_filename}` غير موجود حالياً في مجلد المشروع الرئيسي. تأكد من تطابق اسم الملف في المستودع.")

    st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب السابع: سجل الزوار والأفراد (مخصص للأدمن فقط)
# ------------------------------------------------------------------------------
if st.session_state.current_user == "admin":
    with tab_admin:
        st.markdown("""
        <div dir="rtl" style="text-align: right;">
            <h3>🔒 سجل الزوار والأفراد المسجلين (خاص بالأدمن فقط)</h3>
            <p>متابعة وتصدير سجلات دخول الزوار وعناوين الـ IP وأوقات الدخول بدقة من السيرفر.</p>
        </div>
        """, unsafe_allow_html=True)

        visitors_data_list = load_visitors_log_from_file()
        if visitors_data_list:
            df_visitors = pd.DataFrame(visitors_data_list)
            st.dataframe(df_visitors, use_container_width=True)
            
            csv_visitors = df_visitors.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل سجل الزوار والأفراد وعناوين IP (CSV)",
                data=csv_visitors,
                file_name="سجل_الزوار_وعناوين_IP.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("ℹ️ لا توجد سجلات زوار مسجلة حتى الآن في الملف الخارجي.")

        st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)
