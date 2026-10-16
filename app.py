import random
import io
import os
import re
import socket
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# إعدادات صفحة Streamlit وتطبيق الهوية البصرية الأكاديمية (RTL)
# ==============================================================================
st.set_page_config(
    page_title="منصة منظومة القرار الثقافية والجاهزية الاستراتيجية (AACRI)",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# الألوان الرسمية للوحة التحكم الأكاديمية (أزرق ملكي وذهبي)
CBE_NAVY = "#002B49"         # أزرق عميق
CBE_GOLD = "#C5A059"         # ذهبي ملكي
CBE_GOLD_LIGHT = "#E2C07D"   # ذهبي فاتح
CBE_BG = "#F8F9FA"           # خلفية ناعمة

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

/* إخفاء شريط أدوات Streamlit العلوي للعرض الأكاديمي */
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
    color: {CBE_GOLD} !important;
    padding: 8px 6px !important;
    font-weight: 700 !important;
    border: 1px solid #475569 !important;
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
    font-size: 23px !important;
    font-weight: 800 !important;
    margin-bottom: 10px !important;
    text-shadow: 0 2px 6px rgba(0,0,0,0.7) !important;
}}

.header-center h3 {{
    color: #F1F5F9 !important;
    font-size: 14px !important;
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
# نظام تسجيل الزوار وحفظ عناوين الـ IP (IP Logging & Visitor Database)
# ==============================================================================
LOG_FILE_PATH = "visitors_log.csv"

def get_client_ip():
    try:
        # محاولة استخراج الـ IP الفعلي إذا توفرت هيدرات الشبكة
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            ip = st.context.headers.get("X-Forwarded-For") or st.context.headers.get("X-Real-Ip")
            if ip:
                return ip.split(",")[0].strip()
        host_name = socket.gethostname()
        return socket.gethostbyname(host_name)
    except Exception:
        return "127.0.0.1 (محلي)"

def log_visitor(username, role):
    client_ip = get_client_ip()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([{
        "وقت الدخول": current_time,
        "اسم المستخدم": username,
        "الصلاحية": role,
        "عنوان الـ IP": client_ip
    }])
    
    if os.path.exists(LOG_FILE_PATH):
        try:
            df_existing = pd.read_csv(LOG_FILE_PATH)
            df_combined = pd.concat([df_existing, new_log], ignore_index=True)
            df_combined.to_csv(LOG_FILE_PATH, index=False, encoding='utf-8-sig')
        except Exception:
            new_log.to_csv(LOG_FILE_PATH, index=False, encoding='utf-8-sig')
    else:
        new_log.to_csv(LOG_FILE_PATH, index=False, encoding='utf-8-sig')

# ==============================================================================
# إدارة جلسة الدخول وصلاحيات الأفراد (Authentication & RBAC)
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
                <h2 style="color: {CBE_NAVY}; text-align: center; font-weight: 800; margin-bottom: 10px;">🏛️ منصة منظومة القرار الثقافية والجاهزية الاستراتيجية</h2>
                <p style="color: #475569; text-align: center; font-size: 14px; line-height: 1.6; margin-bottom: 25px;">
                    إطار تطبيقي مقترح للبحوث المتقدمة ورسائل الدكتوراه. يرجى تسجيل الدخول (تجريبي: مستخدم عادي <b>user / 123</b> أو مشرف النظام <b>admin / admin123</b>).
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
                    log_visitor("مشرف النظام (Admin)", "Admin")
                    st.rerun()
                elif username_input == "user" and password_input == "123":
                    st.session_state.authenticated = True
                    st.session_state.username = "باحث / مستخدم (User)"
                    st.session_state.role = "user"
                    log_visitor("باحث / مستخدم (User)", "User")
                    st.rerun()
                else:
                    st.error("⚠️ بيانات الدخول غير صحيحة. (جرّب: user / 123 أو admin / admin123)")
    st.stop()

# ==============================================================================
# القوائم الجغرافية للأقاليم العربية والقطاعات الثقافية
# ==============================================================================
ARAB_REGIONS = [
    "اختر الإقليم الجغرافي العربي",
    "منطقة الخليج العربي (السعودية، الإمارات، قطر، الكويت، البحرين، عمان)",
    "منطقة وادي النيل (مصر، السودان)",
    "منطقة شمال إفريقيا (المغرب، الجزائر، تونس، ليبيا)",
    "منطقة بلاد الشام والعراق (الأردن، لبنان، سوريا، العراق)"
]

CULTURAL_DOMAINS = [
    "الصناعات الإبداعية الرقمية والمنصات التفاعلية",
    "التراث الثقافي الحي والمتاحف الافتراضية",
    "النشر الرقمي والمحتوى الصحفي والسيادي",
    "الفنون البصرية والسينمائية والألعاب الرقمية",
    "ريادة الأعمال الثقافية والاقتصاد البرتقالي"
]

def get_colored_score_html(score):
    if score >= 80:
        return f"{score}% (جاهزية مؤسسية متقدمة 🟢)"
    elif score >= 51:
        return f"{score}% (جاهزية متوسطة تحتاج تحفيزاً 🟡)"
    else:
        return f"{score}% (فجوة هيكلية حرجة تستوجب التدخل 🔴)"

# تهيئة الذاكرة المؤقتة للبيانات والتراكميات
if "history_state" not in st.session_state:
    st.session_state.history_state = []
if "simulated_results_dict" not in st.session_state:
    st.session_state.simulated_results_dict = {}
if "decision_results_dict" not in st.session_state:
    st.session_state.decision_results_dict = {}
if "user_query_text" not in st.session_state:
    st.session_state.user_query_text = ""

def is_valid_arabic_question(text):
    if not text or len(text.strip()) < 5:
        return False
    arabic_chars = re.findall(r'[\u0600-\u06FF]', text)
    if len(arabic_chars) < 4:
        return False
    return True

# ==============================================================================
# الهيدر والشريط الإخباري الأكاديمي
# ==============================================================================
st.markdown(f"""
<div class="header-center">
<h1>المنصة الذكية لدعم منظومة القرار الثقافي وقياس الجاهزية الاستراتيجية (AACRI)</h1>
<h3>إطار منهجي وتطبيقي متقدم لتوظيف تقنيات الذكاء الاصطناعي وحوكمة الصناعات الإبداعية في الأقاليم العربية</h3>
<b>إعداد الباحث: أيمن الدسوقي | معهد التخطيط القومي | المستخدم الحالي: {st.session_state.username}</b>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <span class="ticker-item">🏛️ منصة دعم منظومة القرار الثقافي والجاهزية الاستراتيجية (AACRI)</span>
    <span class="ticker-item">| 📊 مؤشر الجاهزية المركب والأبعاد الخمسة الكبرى للصناعات الثقافية</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي متعدد المتغيرات (Multiple Regression & AHP)</span>
    <span class="ticker-item">| 🛡️ دمج الملاحق الأكاديمية ونظام تتبع الزوار (Admin IP Logging & Appendices)</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# محرك الاستدلال والتحليل الذكي (RAG + Gemini Simulation)
# ==============================================================================
def process_rag_cultural_query(region, question):
    if region == "اختر الإقليم الجغرافي العربي" or not question.strip():
        return "⚠️ يرجى اختيار الإقليم الجغرافي العربي وكتابة السؤال أو الاستفسار بدقة للحصول على التحليل المستند للملاحق الأكاديمية."
    
    if not is_valid_arabic_question(question):
        return "⚠️ **تنبيه:** يرجى كتابة سؤال بحثي واضح باللغة العربية لتحليل المعطيات بدقة."

    if "التطعيم" in question or "الثقافي" in question or "السيادة" in question:
        resp = f"في {region}، يمثل التططعيم الثقافي آلية استراتيجية واعية لحماية الهوية الوطنية وتوظيف تقنيات الذكاء الاصطناعي التوليدي والبيانات الضخمة بما يضمن السيادة الرقمية ومنع الهيمنة الخوارزمية الخارجية."
    elif "الاقتصاد البرتقالي" in question or "ريادة" in question:
        resp = f"تشهد {region} نمواً متصاعداً في الاقتصاد البرتقالي، مدفوعاً بزيادة استثمارات رأس المال المخاطر في المنصات الإبداعية وتطبيقات الواقع المختلط والذكاء الاصطناعي."
    else:
        resp = f"استناداً إلى قواعد بيانات الملاحق البحثية وتحليل الشبكات العصبية لـ {region}، تتطلب المرحلة الحالية إرساء إطار مؤسسي متكامل يربط بين مخرجات التفكير المنظومي وتقارير الجاهزية الرقمية."

    return f"""
    <div dir="rtl" style="text-align: right; line-height: 1.8; color: {CBE_NAVY}; background: #FFFFFF; padding: 22px; border-radius: 10px; border: 1.5px solid {CBE_GOLD}; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">🎯 تحليل منظومة القرار الإقليمي ({region})</h3>
      <p style="margin-bottom: 10px;"><b>السؤال/ الاستفسار:</b> "{question}"</p>
      <div style="background: {CBE_BG}; padding: 16px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 10px;">
        <p style="margin: 0 0 6px 0; font-weight: bold; color: {CBE_NAVY};">💡 التحليل المستند إلى الإطار المنهجي والملاحق:</p>
        <p style="margin: 0; color: #1E293B; font-size: 14.5px;">{resp}</p>
      </div>
    </div>
    """

# ==============================================================================
# التقسيم الرئيسي إلى 7 تبويبات شاملة (Tabs) متضمنة لوحة تحكم الأدمن والملاحق
# ==============================================================================
tabs_list = [
    "🎯 اسأل المنصة",
    "📊 مؤشر الجاهزية (AACRI)", 
    "📈 محاكي السياسات", 
    "🛡️ دعم القرار", 
    "📑 التقرير الموحد",
    "📚 ملاحق الدراسة (PDF)",
    "⚙️ إدارة الزوار (Admin)"
] if st.session_state.role == "admin" else [
    "🎯 اسأل المنصة",
    "📊 مؤشر الجاهزية (AACRI)", 
    "📈 محاكي السياسات", 
    "🛡️ دعم القرار", 
    "📑 التقرير الموحد",
    "📚 ملاحق الدراسة (PDF)"
]

tabs_output = st.tabs(tabs_list)

tab1 = tabs_output[0]
tab2 = tabs_output[1]
tab3 = tabs_output[2]
tab4 = tabs_output[3]
tab5 = tabs_output[4]
tab6 = tabs_output[5]
tab7 = tabs_output[6] if st.session_state.role == "admin" else None

# ------------------------------------------------------------------------------
# التبويب الأول: اسأل المنصة
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🎯 استخلاص وتحليل البيانات الذكي ومعالجة الاستفسارات الإقليمية الثقافية</h3>
        <p>استعراض الإجابات المستندة إلى الملاحق البحثية ونماذج التفكير المنظومي والسياسات المقارنة.</p>
    </div>
    """, unsafe_allow_html=True)

    col_q1, col_q2 = st.columns([1, 2], gap="large")

    with col_q1:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        ask_region_sel = st.selectbox("اختر الإقليم الجغرافي العربي", ARAB_REGIONS, key="ask_reg")
        
        def update_text_area():
            st.session_state.user_query_text = st.session_state.temp_text_input

        user_question = st.text_area(
            "❓ اكتب سؤالك/ استفسارك المنظومي:",
            value=st.session_state.user_query_text,
            placeholder="مثال: ما هو دور التطعيم الثقافي في مواجهة الفجوة الرقمية؟",
            height=120,
            key="temp_text_input",
            on_change=update_text_area
        )

        st.markdown("<b>📌 أسئلة مقترحة حسب المحاور:</b>", unsafe_allow_html=True)
        with st.expander("🌐 محور السيادة الرقمية والتطعيم الثقافي"):
            if st.button("كيف تحمي الدول العربية سيادتها الرقمية والثقافية في عصر خوارزميات الذكاء الاصطناعي؟", key="bq1"):
                st.session_state.user_query_text = "كيف تحمي الدول العربية سيادتها الرقمية والثقافية في عصر خوارزميات الذكاء الاصطناعي؟"
                st.rerun()
        with st.expander("💼 محور الاقتصاد البرتقالي والصناعات الإبداعية"):
            if st.button("ما هي آليات تععزيز الاستثمار في ريادة الأعمال الثقافية والمنصات الإبداعية؟", key="bq2"):
                st.session_state.user_query_text = "ما هي آليات تععزيز الاستثمار في ريادة الأعمال الثقافية والمنصات الإبداعية؟"
                st.rerun()

        ask_submit_btn = st.button("تقديم السؤال واسترجاع التحليل", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_q2:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if ask_submit_btn:
            if ask_region_sel == "اختر الإقليم الجغرافي العربي":
                st.warning("⚠️ يرجى اختيار إقليم جغرافي لتنفيذ الاستعلام.")
            elif not st.session_state.user_query_text.strip():
                st.warning("⚠️ يرجى كتابة أو اختيار سؤال بحثي للإجابة عليه.")
            else:
                with st.spinner("⏳ جاري استرجاع مستندات الإقليم ومعالجة الإجابة بالذكاء الاصطناعي..."):
                    response_html = process_rag_cultural_query(ask_region_sel, st.session_state.user_query_text)
                    st.markdown(response_html, unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار الإقليم الجغرافي وطرح الاستفسار لاستعراض التحليل الدقيق المستمد من الأدبيات والملاحق.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الثاني: مؤشر الجاهزية (AACRI)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🗳️ التشخيص القياسي واحتساب مؤشر الجاهزية للبيئة الثقافية المركب (AACRI)</h3>
        <p>تقييم الأقاليم العربية والقطاعات الثقافية وفق الهيكل الهرمي الخماسي والـ 69 متغيراً.</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        eval_target = st.selectbox("اختر الإقليم أو القطاع المستهدف بالتقييم", ARAB_REGIONS[1:] + CULTURAL_DOMAINS, key="t2_target")
        
        st.markdown("<b>💻 البنية التحتية والمنصات التقنية (وزن 25%)</b>", unsafe_allow_html=True)
        v1 = st.slider("1. جاهزية شبكات النطاق العريض والذكاء الاصطناعي (%)", 0, 100, 82, key="t2_v1")
        v2 = st.slider("2. السحابة السيادية وأمن البيانات الإبداعية (%)", 0, 100, 85, key="t2_v2")

        st.markdown("<b>🧠 رأس المال البشري والمهارات الرقمية (وزن 25%)</b>", unsafe_allow_html=True)
        v3 = st.slider("3. البرامج الأكاديمية والتدريبية المتقدمة (%)", 0, 100, 78, key="t2_v3")
        v4 = st.slider("4. جاهزية الكوادر والمبدعين لتقنيات الجيل القادم (%)", 0, 100, 80, key="t2_v4")

        st.markdown("<b>⚖️ البيئة التشريعية وحوكمة الملكية الفكرية (وزن 20%)</b>", unsafe_allow_html=True)
        v5 = st.slider("5. تحديث قوانين الملكية الفكرية الرقمية (%)", 0, 100, 75, key="t2_v5")
        v6 = st.slider("6. حماية حقوق المبدعين والأمن السيبراني الثقافي (%)", 0, 100, 83, key="t2_v6")

        st.markdown("<b>🍊 الاقتصاد البرتقالي وحجم السوق الإبداعي (وزن 15%)</b>", unsafe_allow_html=True)
        v7 = st.slider("7. مساهمة الصناعات الإبداعية في الناتج المحلي (%)", 0, 100, 70, key="t2_v7")
        v8 = st.slider("8. حجم الاستثمار وتمويل الشركات الناشئة (%)", 0, 100, 74, key="t2_v8")

        st.markdown("<b>🛡️ المحددات الثقافية والتطعيم الرقمي (وزن 15%)</b>", unsafe_allow_html=True)
        v9 = st.slider("9. مؤشر التطعيم الثقافي والحفاظ على الهوية (%)", 0, 100, 88, key="t2_v9")
        v10 = st.slider("10. فاعلية استراتيجيات التوعية المجتمعية (%)", 0, 100, 86, key="t2_v10")

        calc_aacri_btn = st.button("🚀 احسب وسجل مؤشر الجاهزية المركب", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if calc_aacri_btn:
            tech_score = (v1 + v2) / 2.0
            hum_score = (v3 + v4) / 2.0
            leg_score = (v5 + v6) / 2.0
            eco_score = (v7 + v8) / 2.0
            cul_score = (v9 + v10) / 2.0

            final_aacri = round((tech_score * 0.25) + (hum_score * 0.25) + (leg_score * 0.20) + (eco_score * 0.15) + (cul_score * 0.15), 2)
            score_str = get_colored_score_html(final_aacri)

            entry = {
                "وحدة التقييم": eval_target,
                "مؤشر AACRI المركب": final_aacri,
                "البنية التقنية (25%)": round(tech_score, 2),
                "رأس المال البشري (25%)": round(hum_score, 2),
                "التشريعات وحوكمة الملكية (20%)": round(leg_score, 2),
                "الاقتصاد البرتقالي (15%)": round(eco_score, 2),
                "المحددات الثقافية (15%)": round(cul_score, 2)
            }

            updated = False
            for idx, item in enumerate(st.session_state.history_state):
                if item["وحدة التقييم"] == eval_target:
                    st.session_state.history_state[idx] = entry
                    updated = True
                    break
            if not updated:
                st.session_state.history_state.append(entry)

            st.markdown(f"""
            <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
              <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 12px;">📊 نتيجة احتساب مؤشر الجاهزية المركب (AACRI)</h3>
              <p style="font-size: 15px; margin-bottom: 8px;"><b>وحدة التقييم:</b> <span style="color: {CBE_NAVY}; font-weight: bold;">{eval_target}</span></p>
              <p style="font-size: 16px; margin-bottom: 12px;"><b>القيمة المركبة النهائية للمؤشر:</b> <span style="font-size: 18px;">{score_str}</span></p>
            </div>
            """, unsafe_allow_html=True)

            categories = ['البنية التقنية (25%)', 'رأس المال البشري (25%)', 'التشريعات والحوكمة (20%)', 'الاقتصاد البرتقالي (15%)', 'المحددات الثقافية (15%)']
            scores_list = [tech_score, hum_score, leg_score, eco_score, cul_score]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=scores_list, theta=categories, fill='toself', name=eval_target, line_color=CBE_GOLD))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor="#FFFFFF", font=dict(family="Cairo", size=13))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 قم بضبط درجات المحاور الخمسة ثم اضغط على زر الحساب لعرض النتائج والتمثيل البصري الراداري.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 جدول سجل تقييمات الأقاليم والقطاعات")
    if st.session_state.history_state:
        df_hist = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر AACRI المركب", ascending=False).reset_index(drop=True)
        
        table_html = """
        <div dir="rtl" style="width: 100%; overflow-x: auto;">
        <table class="custom-rtl-table">
        <thead>
        <tr>
        <th style="width: 30px; text-align: center;">م</th>
        <th>وحدة التقييم</th>
        <th>مؤشر AACRI المركب</th>
        <th>البنية التقنية</th>
        <th>رأس المال البشري</th>
        <th>التشريعات</th>
        <th>الاقتصاد البرتقالي</th>
        <th>المحددات الثقافية</th>
        </tr>
        </thead>
        <tbody>
        """
        for idx, row in df_hist.iterrows():
            table_html += f"""
            <tr>
            <td style="text-align: center; font-weight: bold;">{idx + 1}</td>
            <td style="font-weight: bold; color: {CBE_NAVY};">{row['وحدة التقييم']}</td>
            <td style="font-weight: bold; color: {CBE_GOLD};">{row['مؤشر AACRI المركب']}%</td>
            <td>{row['البنية التقنية (25%)']}%</td>
            <td>{row['رأس المال البشري (25%)']}%</td>
            <td>{row['التشريعات وحوكمة الملكية (20%)']}%</td>
            <td>{row['الاقتصاد البرتقالي (15%)']}%</td>
            <td>{row['المحددات الثقافية (15%)']}%</td>
            </tr>
            """
        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

        csv_data = df_hist.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تحميل جدول تقييمات الأقاليم (CSV)",
            data=csv_data,
            file_name="مؤشر_الجاهزية_AACRI.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("📂 لا توجد تقييمات مسجلة حتى الآن. قم بإجراء التشخيص في الأعلى لتسجيل وترتيب الوحدات.")

# ------------------------------------------------------------------------------
# التبويب الثالث: محاكي السياسات (Policy Simulator)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🔬 محاكي السياسات الاستشرافي والمتابعة التراكمية (Multiple Regression & AHP)</h3>
        <p>قياس أثر التغيرات في محاور الجاهزية الخمسة على مؤشر AACRI المركب واستشراف سيناريوهات التطوير المستقبلية.</p>
    </div>
    """, unsafe_allow_html=True)

    col_sim_in, col_sim_out = st.columns([1, 2], gap="large")

    with col_sim_in:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        recorded_units = [item["وحدة التقييم"] for item in st.session_state.history_state] if st.session_state.history_state else ARAB_REGIONS[1:]
        sim_unit_sel = st.selectbox("اختر الوحدة للمحاكاة والاستشراف", recorded_units, key="sim_unit")
        base_val_input = st.slider("قيمة المؤشر الافتراضي الحالي", 30.0, 100.0, 78.0, 0.5, key="sim_base_val")

        scenario_sel = st.selectbox("اختر السيناريو الاستراتيجي للاختبار", [
            "📉 السيناريو التشاؤمي (غياب الاستثمار الرقمي وضعف السياسات)",
            "📊 السيناريو المعتدل (تطوير تدريجي وفق الميزانيات الحالية)",
            "🚀 السيناريو الاستباقي / الطموح (إصلاحات هيكلية شاملة وسيادة رقمية كاملة)"
        ], index=1, key="sim_scen_sel")

        s_v1 = st.slider("1️⃣ نسبة الزيادة المقترحة في البنية التقنية (%)", 0, 50, 20, key="sim_s1")
        s_v2 = st.slider("2️⃣ نسبة الزيادة المقترحة في رأس المال البشري (%)", 0, 50, 15, key="sim_s2")
        s_v3 = st.slider("3️⃣ نسبة التطوير في التشريعات وحوكمة الملكية (%)", 0, 50, 25, key="sim_s3")

        run_sim_btn = st.button("📋 إضافة وتثبيت سيناريو المحاكاة", use_container_width=True, type="primary")

        if st.button("🗑️ مسح وإعادة تعيين سيناريوهات المحاكي", use_container_width=True, type="secondary"):
            st.session_state.simulated_results_dict = {}
            st.success("✅ تم مسح جميع سيناريوهات المحاكي بنجاح.")
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_sim_out:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if run_sim_btn:
            b_val = base_val_input
            if st.session_state.history_state:
                for item in st.session_state.history_state:
                    if item["وحدة التقييم"] == sim_unit_sel:
                        b_val = item["مؤشر AACRI المركب"]
                        break

            boost = (s_v1 * 0.25) + (s_v2 * 0.25) + (s_v3 * 0.50)

            if scenario_sel.startswith("📉"):
                sim_result = max(0.0, b_val * 0.90)
                analysis = f"تحذير استشرافي لـ ({sim_unit_sel}): استمرار جمود السياسات وغياب التحديث الرقمي سيؤدي إلى تراجع كفاءة الصناعات الإبداعية واتساع الفجوة الهيكلية."
                action = "سرعة تفعيل حزم الدعم التشريعي وتقوية البنية السحابية السيادية."
            elif scenario_sel.startswith("📊"):
                sim_result = min(100.0, b_val * (1 + (boost * 0.002)))
                analysis = f"نمو تدريجي ومستقر لـ ({sim_unit_sel}): نجاح ملحوظ في تعزيز المهارات الرقمية وتطوير الاقتصاد البرتقالي."
                action = "مواصلة الاستثمار في برامج التدريب والتوسع في منصات المحتوى الرقمي المعتمد."
            else:
                sim_result = min(100.0, b_val * (1 + (boost * 0.0045)))
                analysis = f"طفرة ريادية كبرى لـ ({sim_unit_sel}): تحقيق تكامل رقمي تام وتأسيس بيئة حاضنة للصناعات الثقافية والإبداعية وفق المعايير العالمية."
                action = "قيادة التحالفات الإقليمية وتصدير النماذج الإبداعية الرقمية وتعزيز السيادة الثقافية بالكامل."

            sim_result = round(sim_result, 2)
            delta = round(sim_result - b_val, 2)
            score_str_plain = get_colored_score_html(sim_result)

            box_html = f"""
            <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
              <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">📈 محاكاة: {sim_unit_sel} | السيناريو: {scenario_sel}</h3>
              <p style="font-size: 15px; margin-bottom: 8px;"><b>القيمة المتوقعة لمؤشر AACRI:</b> {score_str_plain} (صافي التغير: <span style="font-weight: bold;">{delta:+.2f}</span>)</p>
              <div style="background: {CBE_BG}; padding: 12px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; margin-top: 10px;">
                <p style="margin-bottom: 6px;"><b>🔬 التحليل الاستشرافي:</b> {analysis}</p>
                <p style="margin: 0; color: {CBE_GOLD}; font-weight: bold;">🛠️ خطة التحرك: {action}</p>
              </div>
            </div>
            """
            st.session_state.simulated_results_dict[f"{sim_unit_sel} - {scenario_sel}"] = {"html": box_html}

        if st.session_state.simulated_results_dict:
            st.markdown("---")
            st.markdown("<h4>📋 مقارنة السيناريوهات المثبتة:</h4>", unsafe_allow_html=True)
            for item in st.session_state.simulated_results_dict.values():
                st.markdown(item["html"], unsafe_allow_html=True)
        else:
            st.info("📈 قم بضبط الوحدة والسيناريو ومتغيرات التحفيز واضغط على زر الإضافة لتثبيت ومتابعة السيناريوهات هنا.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الرابع: لوحة دعم اتخاذ القرار
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🛡️ لوحة دعم اتخاذ القرار وتوطين السياسات الثقافية</h3>
        <p>استعراض التوصيات الاستراتيجية المخصصة لكل إقليم أو قطاع ثقافي بناءً على نتائج التشخيص.</p>
    </div>
    """, unsafe_allow_html=True)

    col_dec_in, col_dec_out = st.columns([1, 2], gap="large")

    with col_dec_in:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        recorded_units_dec = [item["وحدة التقييم"] for item in st.session_state.history_state] if st.session_state.history_state else ARAB_REGIONS[1:]
        dec_unit_sel = st.selectbox("اختر الوحدة لاستعراض توصيات القرار", recorded_units_dec, key="dec_unit")
        gen_dec_btn = st.button("📋 تثبيت توصيات دعم القرار", use_container_width=True, type="primary")

        if st.button("🗑️ مسح لوحة القرار", use_container_width=True, type="secondary"):
            st.session_state.decision_results_dict = {}
            st.success("✅ تم مسح التوصيات بنجاح.")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_dec_out:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if gen_dec_btn:
            if not st.session_state.history_state:
                st.warning("⚠️ يرجى أولاً إدخال وتقييم وحدة في تبويب مؤشر الجاهزية.")
            else:
                unit_data = next((item for item in st.session_state.history_state if item["وحدة التقييم"] == dec_unit_sel), None)
                if unit_data:
                    score = unit_data["مؤشر AACRI المركب"]
                    score_str = get_colored_score_html(score)
                    st.session_state.decision_results_dict[dec_unit_sel] = f"""
                    <div style="background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);" dir="rtl">
                        <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">🛡️ توصيات دعم القرار لـ: {dec_unit_sel} (المؤشر: {score_str})</h3>
                        <ul style="line-height: 1.8; color: #1E293B; padding-right: 20px;">
                            <li><b>تحديث التشريعات الرقمية:</b> سن قوانين مرنة تحمي حقوق الملكية الفكرية للمبدعين في بيئة الذكاء الاصطناعي التوليدي.</li>
                            <li><b>دعم الاقتصاد البرتقالي:</b> إنشاء صناديق تمويل استثمار جريء مخصصة للشركات الناشئة في الصناعات الإبداعية.</li>
                            <li><b>تفعيل التطعيم الثقافي:</b> بناء منصات وطنية للمحتوى الرقمي تعزز الهوية وتواجه الهيمنة الخوارزمية الخارجية.</li>
                        </ul>
                    </div>
                    """

        if st.session_state.decision_results_dict:
            for item in st.session_state.decision_results_dict.values():
                st.markdown(item, unsafe_allow_html=True)
        else:
            st.info("🛡️ قم باختيار الوحدة واضغط على زر الإضافة لتثبيت التوصيات الاستراتيجية هنا.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الخامس: التقرير التنفيذي الموحد
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📑 التقرير التنفيذي الموحد لمنظومة القرار والجاهزية الاستراتيجية</h3>
        <p>ملخص استراتيجي شامل يدمج مخرجات التشخيص ومحاكي السياسات وإطار نقاط الرفع لدونيلا ميدوز.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 توليد التقرير التنفيذي الموحد", use_container_width=True, type="primary"):
        if not st.session_state.history_state:
            st.warning("📂 لا توجد بيانات مسجلة كافية. يرجى إدخال تشخيص وحدة واحدة على الأقل.")
        else:
            df_rep = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر AACRI المركب", ascending=False).reset_index(drop=True)
            top_row = df_rep.iloc[0]
            top_unit = top_row["وحدة التقييم"]
            top_score = top_row["مؤشر AACRI المركب"]
            top_score_col = get_colored_score_html(top_score)

            report_html = f"""
            <div dir="rtl" style="background: #FFFFFF; padding: 30px; border-radius: 14px; border: 2px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 6px 20px rgba(0,0,0,0.08);">
              <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 15px; margin-bottom: 25px;">
                <h2 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">📑 التقرير التنفيذي الموحد لدعم منظومة القرار الثقافي (AACRI)</h2>
                <p style="color: #64748B; font-size: 14px; margin-top: 6px;">إطار تطبيقي للبحوث المتقدمة ورسائل الدكتوراه | إعداد الباحث: أيمن الدسوقي</p>
              </div>

              <div style="background: {CBE_BG}; padding: 18px; border-radius: 10px; border-right: 5px solid {CBE_GOLD}; margin-bottom: 25px;" dir="rtl">
                <h4 style="color: {CBE_NAVY}; margin-top: 0;">🏆 مؤشرات الريادة والجاهزية:</h4>
                <p>الوحدة المتصدرة حالياً في مؤشر الجاهزية هي: <span style="font-weight: bold; color: {CBE_GOLD};">{top_unit}</span> بقيمة مركبة تبلغ {top_score_col}.</p>
                <p style="margin: 0;">إجمالي الوحدات الخاضعة للتقييم حتى الآن: <b>{len(df_rep)} وحدة إقليمية وقطاعية</b>.</p>
              </div>

              <div style="background: #FFFBEB; padding: 20px; border-radius: 10px; border: 1.5px solid #FCD34D;" dir="rtl">
                <h4 style="color: #92400E; margin-top: 0;">🌳 إطار نقاط الرفع المنظومي لدونيلا ميدوز:</h4>
                <ul style="margin: 0; padding-right: 20px; line-height: 1.8; color: #78350F;">
                   <li><b>1. المعلمات (Parameters):</b> تعديل نسب مخصصات الاستثمار في الصناعات الإبداعية والبحث والتطوير.</li>
                   <li><b>2. تدفق المعلومات (Information Flows):</b> إحكام منصات البيانات الثقافية وتعزيز الشفافية والربط البيني.</li>
                   <li><b>3. القواعد والحوكمة (Rules):</b> تحديث قوانين حماية الملكية الفكرية ووضع ضوابط أخلاقية لاستخدام الذكاء الاصطناعي.</li>
                   <li><b>4. أهداف النظام (Goals):</b> توجيه السياسات الإقليمية نحو بناء مجتمع معرفي وإبداعي مستدام وسيادة رقمية واعية.</li>
                </ul>
              </div>
            </div>
            """
            st.markdown(report_html, unsafe_allow_html=True)

            word_content = f"""<html dir="rtl"><head><meta charset="utf-8"><title>التقرير التنفيذي الموحد</title></head>
            <body style="font-family: 'Cairo'; text-align: right;">{report_html}</body></html>"""
            st.download_button(
                label="📥 تحميل التقرير التنفيذي في مستند (Word)",
                data=word_content.encode("utf-8-sig"),
                file_name="التقرير_التنفيذي_لمنظومة_القرار_الثقافي.doc",
                mime="application/msword",
                use_container_width=True
            )

# ------------------------------------------------------------------------------
# التبويب السادس: ملاحق الدراسة الأكاديمية (PDF Integration)
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📚 ملاحق الدراسة البحثية والدليل الإرشادي الرسمي (PDF Integration)</h3>
        <p>استعراض وتحميل ملاحق الدراسة الستة والدليل الرسمي المعتمد لدعم موثوقية الأطروحة والبحث المتقدم.</p>
    </div>
    """, unsafe_allow_html=True)

    col_pdf1, col_pdf2 = st.columns(2, gap="medium")

    with col_pdf1:
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #CBD5E1; margin-bottom: 15px;" dir="rtl">
            <h4 style="color: {CBE_NAVY};">📁 الملحق الأول: الاستقراء الببليومتري وتحليل خرائط المعرفة</h4>
            <p style="font-size: 13.5px; color: #475569;">نتائج تحليل الكلمات المفتاحية باستخدام VOSviewer وخوارزميات LDA لدراسة تطور أدبيات حوكمة الصناعات الإبداعية والذكاء الاصطناعي.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #CBD5E1; margin-bottom: 15px;" dir="rtl">
            <h4 style="color: {CBE_NAVY};">📁 الملحق الثاني: خرائط حلقات السببية (CLDs) والتفكير المنظومي</h4>
            <p style="font-size: 13.5px; color: #475569;">نمذجة ديناميات التغذية الراجعة وحلقات التعزيز بين البنية التقنية، التطعيم الثقافي، والسيادة الرقمية.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #CBD5E1; margin-bottom: 15px;" dir="rtl">
            <h4 style="color: {CBE_NAVY};">📁 الملحق الثالث: المصفوفة الإجرائية لبناء مؤشر الجاهزية (AACRI)</h4>
            <p style="font-size: 13.5px; color: #475569;">التفصيل الرياضي للـ 69 متغيراً ومستويات القياس ومصادر البيانات الرسمية المعتمدة.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_pdf2:
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #CBD5E1; margin-bottom: 15px;" dir="rtl">
            <h4 style="color: {CBE_NAVY};">📁 الملحق الرابع: جداول المقارنات الزوجية ومعاملات الأوزان (AHP)</h4>
            <p style="font-size: 13.5px; color: #475569;">مصفوفات التحليل الهرمي وأوزان المحاور الخمسة وحسابات الاتساق الإحصائي.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #CBD5E1; margin-bottom: 15px;" dir="rtl">
            <h4 style="color: {CBE_NAVY};">📁 الملحق الخامس: معادلات التطبيع والمعياريّة الرياضية</h4>
            <p style="font-size: 13.5px; color: #475569;">الصيغ الرياضية المعتمدة لتحويل القيم الخام إلى مقاييس معيارية موحدة (0 - 100).</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #CBD5E1; margin-bottom: 15px;" dir="rtl">
            <h4 style="color: {CBE_NAVY};">📁 الملحق السادس والدليل الإرشادي الرسمي للمنصة</h4>
            <p style="font-size: 13.5px; color: #475569;">دليل المستخدم الشامل والبروتوكول الميداني لتشغيل لوحة التحكم واختبار السياسات الاستشرافية.</p>
        </div>
        """, unsafe_allow_html=True)

    # زر تحميل تجريبي جامع للملاحق
    dummy_pdf_content = b"%PDF-1.4 ملاحق الدراسة البحثية - منظومة القرار الثقافي والجاهزية الاستراتيجية (AACRI)"
    st.download_button(
        label="📥 تحميل الملف الشامل للملاحق والدليل الإرشادي (PDF)",
        data=dummy_pdf_content,
        file_name="ملاحق_الداسة_والدليل_الإرشادي_AACRI.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# ------------------------------------------------------------------------------
# التبويب السابع: لوحة تحكم المشرف وإدارة سجلات الزوار (Admin Dashboard & IP Logging)
# ------------------------------------------------------------------------------
if st.session_state.role == "admin" and tab7 is not None:
    with tab7:
        st.markdown("""
        <div dir="rtl" style="text-align: right;">
            <h3>⚙️ لوحة تحكم المشرف وسجلات الزوار وعناوين الـ IP (Admin Dashboard & IP Logging)</h3>
            <p>متابعة حركة دخول الزوار والمستخدمين وعناوين الـ IP وأوقات الاتصال بدقة عالية لأغراض المراجعة واختبار الميدان.</p>
        </div>
        """, unsafe_allow_html=True)

        if os.path.exists(LOG_FILE_PATH):
            try:
                df_logs = pd.read_csv(LOG_FILE_PATH)
                st.markdown(f"**📊 إجمالي عدد عمليات الدخول المسجلة:** {len(df_logs)}")
                
                log_table_html = """
                <div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 350px;">
                <table class="custom-rtl-table">
                <thead>
                <tr>
                <th style="width: 40px; text-align: center;">م</th>
                <th>وقت الدخول</th>
                <th>اسم المستخدم</th>
                <th>الصلاحية</th>
                <th>عنوان الـ IP</th>
                </tr>
                </thead>
                <tbody>
                """
                for idx, row in df_logs.iterrows():
                    log_table_html += f"""
                    <tr>
                    <td style="text-align: center; font-weight: bold;">{idx + 1}</td>
                    <td>{row['وقت الدخول']}</td>
                    <td style="font-weight: bold; color: {CBE_NAVY};">{row['اسم المستخدم']}</td>
                    <td>{row['الصلاحية']}</td>
                    <td style="font-family: monospace; color: {CBE_GOLD};">{row['عنوان الـ IP']}</td>
                    </tr>
                    """
                log_table_html += "</tbody></table></div>"
                st.markdown(log_table_html, unsafe_allow_html=True)

                csv_logs = df_logs.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 تصدير سجلات الزوار والـ IP بصيغة (CSV)",
                    data=csv_logs,
                    file_name="visitors_ip_logs.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                if st.button("🗑️ مسح وإعادة تعيين سجلات الزوار بالكامل", type="secondary"):
                    if os.path.exists(LOG_FILE_PATH):
                        os.remove(LOG_FILE_PATH)
                    st.success("✅ تم مسح سجلات الزوار بنجاح.")
                    st.rerun()

            except Exception as e:
                st.error(f"⚠️ حدث خطأ أثناء قراءة سجلات الزوار: {e}")
        else:
            st.info("📂 لا توجد سجلات دخول مسجلة حتى الآن.")

st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية ورسالة الدكتوراه © 2026 | إعداد الباحث: أيمن الدسوقي</div>', unsafe_allow_html=True)

<FollowUp>
هل ترغب في تعديل أوزان المحاور الخمسة لمؤشر الجاهزية (AACRI) أو إضافة متغيرات إضافية مرتبطة بأقاليم معينة؟
</FollowUp>

<ElicitationsGroup>
</ElicitationsGroup>
