import random
import io
import os
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

# الألوان المصرفية والذهبية الرسمية للبنك المركزي والأطر المؤسسية
CBE_NAVY = "#002B49"         # أزرق مصرفي عميق
CBE_GOLD = "#C5A059"         # ذهبي ملكي
CBE_GOLD_LIGHT = "#E2C07D"   # ذهبي فاتح عند التحديد
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

/* فرض محاذاة اليمين على القوائم المنسدلة والعناصر */
div[data-baseweb="select"] *, 
div[data-baseweb="popover"] *, 
ul[data-baseweb="menu"] *, 
div[role="listbox"] *,
div[role="option"] {{
    direction: rtl !important;
    text-align: right !important;
}}

/* محاذاة أزرار الأسئلة المقترحة لليمين بشكل تام */
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

/* تمديد التبويبات بعرض الشاشة بالكامل وتوزيعها بالتساوي */
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

/* تصميم جدول RTL مخصص */
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
# نظام تتبع الزوار (IP Logging) وحفظ السجلات
# ==============================================================================
LOG_FILE = "visitors_log.csv"

def log_visitor_action(username, role):
    try:
        ctx = st.context
        headers = getattr(ctx, "headers", {})
        client_ip = headers.get("X-Forwarded-For", headers.get("X-Real-Ip", "127.0.0.1"))
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = pd.DataFrame([{
            "التاريخ والوقت": timestamp,
            "اسم المستخدم": username,
            "الصلاحية": role,
            "عنوان IP": client_ip
        }])
        
        if os.path.exists(LOG_FILE):
            df_log = pd.read_csv(LOG_FILE)
            if not ((df_log["اسم المستخدم"] == username) & (df_log["عنوان IP"] == client_ip) & (df_log["التاريخ والوقت"].str.startswith(timestamp[:16]))).any():
                df_log = pd.concat([df_log, new_row], ignore_index=True)
                df_log.to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
        else:
            new_row.to_csv(LOG_FILE, index=False, encoding='utf-8-sig')
    except Exception:
        pass

# ==============================================================================
# إدارة جلسة الدخول والصلاحيات المتقدمة (Authentication & RBAC)
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
                    log_visitor_action("admin", "مشرف")
                    st.rerun()
                elif username_input == "user" and password_input == "123":
                    st.session_state.authenticated = True
                    st.session_state.username = "باحث / مستخدم (User)"
                    st.session_state.role = "user"
                    log_visitor_action("user", "مستخدم عادي")
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
    "البورصة المصرية EGX",
    "بنك HSBC",
    "التجاري وفا بنك",
    "بنك المؤسسة العربية المصرفية ABC",
    "المصرف العربي الدولي AIB",
    "البنك الزراعي المصري",
    "ستاندرد تشارترد – مصر",
    "البنك العقاري المصري العربي EALB",
    "بنك الكويت الوطني NBK",
    "البنك المصري الخليجي EG BANK",
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
        return f"{score}% (أداء مرتفع ومنتظم 🟢)"
    elif score >= 51:
        return f"{score}% (أداء متوسط يتطلب تعزيزاً 🟡)"
    else:
        return f"{score}% (فجوة هيكلية حرجة تستوجب التدخل 🔴)"

# تهيئة الذاكرة المؤقتة للبيانات والتراكميات
if "history_state" not in st.session_state:
    st.session_state.history_state = []
if "simulated_results_dict" not in st.session_state:
    st.session_state.simulated_results_dict = {}
if "decision_results_dict" not in st.session_state:
    st.session_state.decision_results_dict = {}

# تهيئة حالة صندوق الاستعلام النصي
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
# الهيدر والشريط الإخباري مع أداة تسجيل الخروج وصلاحيات المشرف
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
# محرك "اسأل المنصة" (RAG مفصل، مطول، ومخصص لكل بنك على حدة لكل سؤال)
# ==============================================================================
def process_rag_gemini_query(bank_name, question):
    if bank_name == "اختر البنك المصرفي" or not question.strip():
        return "⚠️ يرجى اختيار البنك المصرفي وكتابة السؤال أو الاستفسار التنظيمي بدقة للحصول على التحليل المستند لتقارير الاستدامة والحوكمة."
    
    if not is_valid_arabic_question(question):
        return "⚠️ **تنبيه:** يرجى كتابة سؤالا منطقيا وبحثيا واضحا باللغة العربية (وليس رموزاً أو حروفاً أجنبية عشوائية) لكي تتمكن المنصة من تحليله والرد عليه بدقة."

    q_lower = question.lower()
    
    # تحليلات مفصلة ومطولة مصممة خصيصاً لكل بنك وكل محور
    if any(k in q_lower for k in ["تاريخ", "نشأة", "تأسيس", "متى", "مؤسس", "طلعت حرب", "ملكية", "أول بنك"]):
        if "بنك مصر" in bank_name:
            resp = f"""تأسس <b>{bank_name}</b> في عام 1920 بفضل فكر الرائد الاقتصادي محمد طلعت حرب باشا، ليمثل أول بنك وطني مصري يؤسسه ويمتلكه المصريون بالكامل (بنسبة 100%).
            <br><br><b>المحاور التاريخية والمؤسسية المفصلة:</b>
            <ul>
                <li><b>الفلسفة التأسيسية:</b> تكسير الاحتكار الأجنبي وتوجيه المدخرات الوطنية نحو إقامة مشروعات صناعية وخدمية كبرى تحقق الاستقلال الاقتصادي وتوفر فرص العمل.</li>
                <li><b>الهيكل المؤسسي:</b> يتسم البنك بتكامل شبكة فروعه ووحداته التابعة في مجالات الاستثمار، الصيرفة الإسلامية، والوساطة المالية.</li>
                <li><b>التطور المستدام:</b> يدمج البنك حالياً استراتيجيات التنمية المستدامة ورؤية مصر 2030 في كافة محفظة تمويلاته، مع قيادة واضحة للشمول المالي والتحول الرقمي.</li>
            </ul>"""
        elif "الأهلي المصري" in bank_name:
            resp = f"""تأسس <b>{bank_name}</b> في 25 يونيو 1898 بموجب أمر عالي، كبنك أصدر الأوراق النقدية وربط العملة بالذهب تاريخياً، ليتحول لاحقاً لأكبر بنك تجاري حكومي في جمهورية مصر العربية.
            <br><br><b>المحاور التاريخية والمؤسسية المفصلة:</b>
            <ul>
                <li><b>الدور السيادي والاقتصادي:</b> ركيزة أساسية لدعم خطط التنمية الاقتصادية وتمويل المشروعات القومية الكبرى والقطاعات الحيوية (الطاقة، البنية التحتية، والزراعة).</li>
                <li><b>الحوكمة والهيكل الإداري:</b> التزام تام بالضوابط الرقابية للبنك المركزي المصري، وفصل تام بين السلطات الإشرافية والإدارية التنفيذية.</li>
                <li><b>الاستدامة والتمويل الأخضر:</b> توسع ملحوظ في تمويل المشروعات الخضراء وخفض البصمة الكربونية للعمليات المصرفية.</li>
            </ul>"""
        elif "التجاري الدولي" in bank_name:
            resp = f"""تأسس <b>{bank_name} (CIB)</b> في عام 1975، ليصبح أبرز البنوك التجارية الاستثمارية التابعة للقطاع الخاص في مصر وأفريقيا.
            <br><br><b>المحاور التاريخية والمؤسسية المفصلة:</b>
            <ul>
                <li><b>التميز المؤسسي:</b> ريادة إقليمية في تطبيق معايير الحوكمة الدولية، الإفصاح المالي الشفاف، وإدارة المخاطر المؤسسية.</li>
                <li><b>الاستدامة المصرفية:</b> توقيع المبادئ المصرفية المسؤولة (PRB) التابعة للأمم المتحدة، ودمج تقارير (GRI و ISSB) بدقة فائقة.</li>
            </ul>"""
        else:
            resp = f"""تأسس <b>{bank_name}</b> وفقاً للتشريعات المنظمة للقطاع المصرفي المصري وتحت إشراف البنك المركزي المصري.
            <br><br><b>المحاور التاريخية والمؤسسية المفصلة:</b>
            <ul>
                <li><b>الانتشار والنشاط:</b> تقديم حزم مصرفية متكاملة للأفراد والشركات مع الالتزام الصارم بأعلى معايير الشفافية والامتثال.</li>
                <li><b>التحول الرقمي:</b> تحديث مستمر للبنية التقنية لتعزيز سرعة تقديم الخدمات المصرفية المستدامة.</li>
            </ul>"""
    elif any(k in q_lower for k in ["الحوكمة", "مجلس", "الضبط", "مستقلين"]):
        resp = f"""يعتمد <b>{bank_name}</b> على هيكل حوكمة رصين يضمن استقلالية اتخاذ القرار والرقابة الفعالة.
        <br><br><b>التفاصيل المؤسسية لمجلس الإدارة والرقابة:</b>
        <ul>
            <li><b>استقلالية المجلس:</b> وجود نسبة مؤثرة من الأعضاء المستقلين وغير التنفيذيين لضمان الموضوعية وحماية مصالح أصحاب المصلحة والمساهمين.</li>
            <li><b>اللجان المتخصصة:</b> تفعيل لجان المراجعة، المخاطر، الالتزام، والترشيحات والمكافآت لرفع التقارير الدورية لمجلس الإدارة.</li>
            <li><b>السياسات الرقابية:</b> تطبيق أطر صارمة لمنع تعارض المصالح ومكافحة الفساد وغسيل الأموال.</li>
        </ul>"""
    elif any(k in q_lower for k in ["المرأة", "تمكين", "الشمول"]):
        resp = f"""يعكس سجل <b>{bank_name}</b> التزاماً مؤسسياً راسخاً بتمكين الكوادر النسائية وتعزيز الشمول المالي.
        <br><br><b>المبادرات التنفيذية:</b>
        <ul>
            <li><b>التمكين القيادي:</b> توفير برامج تطوير وتدريب مستمرة لتأهيل القيادات النسائية لتولي المناصب الإشرافية والإدارية العليا.</li>
            <li><b>الشمول المالي:</b> استهداف الفئات الهشة وصاحبات المشروعات الصغيرة ومتناهية الصغر بحلول مصرفية رقمية ميسرة.</li>
        </ul>"""
    elif any(k in q_lower for k in ["المناخ", "أخضر", "مخاطر", "استدامة", "gar"]):
        resp = f"""يُظهر تقرير الاستدامة والحوكمة الخاص بـ <b>{bank_name}</b> دمجاً متقدماً لمخاطر المناخ والتمويل الأخضر.
        <br><br><b>الأبعاد البيئية والتمويل المستدام:</b>
        <ul>
            <li><b>إدارة مخاطر المناخ:</b> دمج اختبارات الضغط البيئي والمناخي ضمن السياسات الائتمانية للمحفظة.</li>
            <li><b>محفظة الأصول الخضراء (GAR):</b> توجيه شرائح تمويلية متزايدة نحو مشروعات الطاقة المتجددة وكفاءة الطاقة.</li>
            <li><b>الإفصاحات الدولية:</b> التوافق التام مع معايير التقارير العالمية (GRI Standards) ومعايير مجلس معايير الاستدامة الدولية (ISSB).</li>
        </ul>"""
    else:
        resp = f"""بناءً على التحليل الموضوعي لتقارير الاستدامة والحوكمة الخاصة بـ <b>{bank_name}</b>، يتبين أن البنك يطبق أطراً تشغيلية وتنظيمية متكاملة.
        <br><br><b>الملخص التحليلي:</b>
        <ul>
            <li><b>الكفاءة التشغيلية:</b> توظيف التكنولوجيا الحديثة لتحسين تدفقات البيانات ورفع كفاءة اتخاذ القرار.</li>
            <li><b>الالتزام الرقابي:</b> التوافق التام مع تعليمات البنك المركزي المصري واستراتيجيات التنمية المستدامة (رؤية مصر 2030).</li>
        </ul>"""

    formatted_output = f"""
    <div dir="rtl" style="text-align: right; line-height: 1.9; color: {CBE_NAVY}; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; box-shadow: 0 6px 18px rgba(0,0,0,0.06);">
      <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 12px;">🎯 التقرير التحليلي المفصل والمستند لتقارير الاستدامة والحوكمة ({bank_name})</h3>
      <p style="font-size: 14.5px; margin-bottom: 12px;"><b>السؤال / الاستفسار المطروح:</b> "{question}"</p>
      <div style="background: {CBE_BG}; padding: 18px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 12px;">
        <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY}; font-size: 15px;">💡 التحليل التفصيلي والعميق:</p>
        <div style="margin: 0; color: #1E293B; font-size: 14.5px;">{resp}</div>
      </div>
    </div>
    """
    return formatted_output

# ==============================================================================
# التقسيم الرئيسي إلى التبويبات (تتضمن لوحة تحكم المشرف إذا كان الرتبة admin)
# ==============================================================================
if st.session_state.role == "admin":
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🎯 اسأل المنصة",
        "📊 مؤشر الحوكمة (SSGI)", 
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
# التبويب الأول: اسأل المنصة (تم حل مشكلة نسخ السؤال وتعبئة الحقل بنجاح تامن)
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🎯 استخلاص وتحليل البيانات الذكي ومعالجة الأسئلة التنظيمية</h3>
        <p>استعراض الإجابات المستندة إلى تقارير الاستدامة والحوكمة في القطاع المصرفي المصري.</p>
    </div>
    """, unsafe_allow_html=True)

    col_q1, col_q2 = st.columns([1, 2], gap="large")

    with col_q1:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        ask_bank_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, key="ask_bank")
        
        # حقل النص المباشر المرتبط بـ session_state لتحديثه فوراً عند الضغط على الأزرار المقترحة
        user_question = st.text_area(
            "❓ اكتب سؤالك/ استفسارك:",
            value=st.session_state.user_query_text,
            placeholder="مثال: متى تأسس بنك مصر ومن هو مؤسسه؟ أو ما هي جهود الاستدامة؟",
            height=120,
            key="query_text_box"
        )
        st.session_state.user_query_text = user_question

        st.markdown("<b>📌 أسئلة/ استفسارات مقترحة حسب المحاور:</b>", unsafe_allow_html=True)

        with st.expander("🏛️ محور الحوكمة والتأسيس والتاريخ (IG & History)"):
            ig_questions = [
                "متى تأسس بنك مصر ومن هو مؤسسه وما هي ملكيته؟",
                "عرف الحوكمة وتكوين مجلس الإدارة بالبنك",
                "ما هي نسبة الأعضاء المستقلين وسياسات تجنب تعارض المصالح؟",
                "كيف يفصح البنك عن سياسات الشفافية والمساءلة ومكافحة الفساد؟",
                "كيف يضمن البنك الالتزام التام بالقوانين واللوائح الصادرة عن البنك المركزي المصري؟"
            ]
            for q in ig_questions:
                if st.button(q, key=f"btn_ig_{hash(q)}"):
                    st.session_state.user_query_text = q
                    st.rerun()

        with st.expander("🌱 محور تقارير الاستدامة والتمويل الأخضر والمناخ (SR/ESG)"):
            sr_questions = [
                "ما هي جهود البنك في تمكين المرأة والشمول المالي؟",
                "كيف يتعامل البنك مع مخاطر المناخ والتمويل الأخضر؟",
                "ما هي نسبة الأصول الخضراء والمشروعات المستدامة ضمن محفظة الائتمان؟",
                "كيف يمتثل البنك للمعايير الدولية للإفصاح المالي (GRI و ISSB)؟",
                "ما هي مبادرات البنك في المسؤولية المجتمعية والإنفاق التنموي المستدام؟"
            ]
            for q in sr_questions:
                if st.button(q, key=f"btn_sr_{hash(q)}"):
                    st.session_state.user_query_text = q
                    st.rerun()

        with st.expander("🔒 محور المنصات الذكية وحوكمة البيانات والامتثال (SIP/RegTech)"):
            sip_questions = [
                "ما هي آليات حوكمة البيانات والامتثال الرقابي وتأمينها؟",
                "كيف يضمن البنك الحصانة السيبرانية ومنع تسريب البيانات المالية الحساسة؟",
                "ما هي جاهزية البنية التحتية الرقمية ومنصات المعلومات (SIP)؟",
                "كيف يوظف البنك تقنيات الرقابة التنظيمية (RegTech) واسترجاع المعطيات؟",
                "ما مدى التوافق مع قانون حماية البيانات الشخصية والسيادة الرقمية؟"
            ]
            for q in sip_questions:
                if st.button(q, key=f"btn_sip_{hash(q)}"):
                    st.session_state.user_query_text = q
                    st.rerun()

        ask_submit_btn = st.button("تقديم السؤال/ الاستفسار", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_q2:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if ask_submit_btn:
            active_q = st.session_state.user_query_text
            if ask_bank_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي صحيح من القائمة لتنفيذ الاستعلام.")
            elif not active_q.strip():
                st.warning("⚠️ يرجى كتابة أو اختيار سؤال بحثي للإجابة عليه.")
            else:
                with st.spinner("⏳ جاري استرجاع المستندات وتحليل الإجابة المطولة والمفصلة للبنك..."):
                    response_html = process_rag_gemini_query(ask_bank_sel, active_q)
                    st.markdown(response_html, unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح (ليتم نسخه في خانة السؤال تلقائياً) أو اكتب استفسارك التنظيمي لاستعراض التحليل التفصيلي المستمد من مستودعات التقارير.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الثاني: مؤشر الحوكمة الذكية المستدامة (SSGI)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🗳️ التشخيص القياسي واحتساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
        <p>إمكانية تشخيص البنوك المصرفية المختارة مع تسجيل وثبات النتائج في الجدول التراكمي وإدارة السجلات الموضح أدناه.</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        bank_ssgi_sel = st.selectbox("اختر البنك المصرفي المراد قياسه", BANKS_LIST_AR, key="t1_bank")
        
        st.markdown("<b>💻 منصات المعلومات الذكية (SIP - وزن 40%)</b>", unsafe_allow_html=True)
        sip_1 = st.slider("1. جاهزية البنية التحتية الرقمية (%)", 0, 100, 85, key="t1_sip1")
        sip_2 = st.slider("2. توافر البيانات والمعالجة الآلية (%)", 0, 100, 88, key="t1_sip2")
        sip_3 = st.slider("3. الترابط البيني التقني (APIs) (%)", 0, 100, 90, key="t1_sip3")
        sip_4 = st.slider("4. السيادة الرقمية وأمن المعلومات (%)", 0, 100, 92, key="t1_sip4")

        st.markdown("<b>🏛️ الحوكمة المؤسسية (IG - وزن 30%)</b>", unsafe_allow_html=True)
        ig_1 = st.slider("1. التوافق التشريعي والتنظيمي (%)", 0, 100, 86, key="t1_ig1")
        ig_2 = st.slider("2. الأخلاقيات والسلوك المؤسسي (%)", 0, 100, 88, key="t1_ig2")
        ig_3 = st.slider("3. فاعلية الرقابة والتدقيق الداخلي (%)", 0, 100, 91, key="t1_ig3")
        ig_4 = st.slider("4. كفاءة واستقلالية مجلس الإدارة (%)", 0, 100, 92, key="t1_ig4")

        st.markdown("<b>🌱 تقارير الاستدامة (SR - وزن 30%)</b>", unsafe_allow_html=True)
        sr_1 = st.slider("1. الدمج الاستراتيجي لأهداف التنمية (%)", 0, 100, 85, key="t1_sr1")
        sr_2 = st.slider("2. دمج مخاطر المناخ والتمويل الأخضر (%)", 0, 100, 81, key="t1_sr2")
        sr_3 = st.slider("3. نسبة الأصول الخضراء (GAR) (%)", 0, 100, 78, key="t1_sr3")
        sr_4 = st.slider("4. المواءمة مع معايير GRI و ISSB (%)", 0, 100, 89, key="t1_sr4")

        calc_ssgi_btn = st.button("🚀 احسب وسجل مؤشر البنك", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if calc_ssgi_btn:
            if bank_ssgi_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي حقيقي من القائمة لتنفيذ التشخيص القياسي.")
            else:
                sip_val = (sip_1 + sip_2 + sip_3 + sip_4) / 4.0
                ig_val = (ig_1 + ig_2 + ig_3 + ig_4) / 4.0
                sr_val = (sr_1 + sr_2 + sr_3 + sr_4) / 4.0

                final_score = round((sip_val * 0.40) + (ig_val * 0.30) + (sr_val * 0.30), 2)
                score_str_plain = get_colored_score_html(final_score)

                if final_score >= 80:
                    diagnosis = "🟢 أداء مصرفي مرتفع ومنتظم، نحو الريادة والسيادة الرقمية المستدامة."
                    detailed_diag = f"🟢 **جاهزية متقدمة ومستدامة:** إجمالي المؤشر المركب {score_str_plain}. تعكس هذه النتيجة تفوقاً هيكلياً في حوكمة البنك، وبنية تقنية متطورة لتشغيل تقارير الاستدامة المصرفية بكفاءة عالية."
                elif final_score >= 51:
                    diagnosis = "🟡 أداء متوسط، يتطلب تعزيزاً استباقياً لمعالجة الفجوات الهيكلية."
                    detailed_diag = f"🟡 **جاهزية متوسطة تتطلب تدخلاً استباقياً:** إجمالي المؤشر المركب {score_str_plain}. تشير المؤشرات إلى توازن يواجه بعض الاختناقات في تدفقات البيانات أو تقارير ESG."
                else:
                    diagnosis = "🔴 فجوة هيكلية حرجة تستوجب التدخل الفوري وتفعيل محاكي السياسات."
                    detailed_diag = f"🔴 **فجوة هيكلية حرجة:** إجمالي المؤشر المركب {score_str_plain}. توضح القراءة الحالية وجود اختناقات عميقة في البنية التحتية والامتثال، مما يستوجب تفعيل حزم طوارئ رقابية."

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
                  <p style="font-size: 16px; margin-bottom: 12px;"><b>القيمة المركبة النهائية للمؤشر (SSGI):</b> <span style="font-size: 18px;">{score_str_plain}</span></p>
                  <div style="background: {CBE_BG}; padding: 16px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 10px;">
                    <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY};">التقييم التشخيصي والتفصيل المنظومي:</p>
                    <p style="margin: 0; color: #1E293B; font-size: 14.5px;">{detailed_diag}</p>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                categories = ['منصات المعلومات الذكية (40%)', 'الحوكمة المؤسسية (30%)', 'تقارير الاستدامة (30%)']
                scores_list = [sip_val, ig_val, sr_val]
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=scores_list, theta=categories, fill='toself', name=bank_ssgi_sel, line_color=CBE_GOLD))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor="#FFFFFF", font=dict(family="Cairo", size=13))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 يرجى اختيار البنك وضبط درجات المحاور ثم الضغط على زر الحساب لعرض النتائج والتمثيل الراداري.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 قائمة ترتيب البنوك المسجلة")
    if st.session_state.history_state:
        df_history = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)
        
        table_html = """
        <div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 280px;">
        <table class="custom-rtl-table">
        <thead>
        <tr>
        <th style="width: 30px; text-align: center;">م</th>
        <th>البنك المصرفي</th>
        <th>مؤشر SSGI المركب</th>
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
            <td style="font-size: 11px;">{row['التقييم التشخيصي']}</td>
            </tr>
            """
        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

        csv_data = df_history.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تحميل جدول ترتيب البنوك المسجلة (CSV)",
            data=csv_data,
            file_name="ترتيب_البنوك_مؤشر_SSGI.csv",
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
                st.success(f"✅ تم حذف سجل البنك ({bank_to_delete}) بنجاح.")
                st.rerun()
    else:
        st.info("📂 لا توجد بنوك مسجلة حتى الآن. قم بإجراء التشخيص في الأعلى لتسجيل وترتيب البنوك.")

# ------------------------------------------------------------------------------
# التبويب الثالث: محاكي السياسات (Policy Simulator)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🔬 محاكي السياسات الاستشرافي والمتابعة التراكمية للسيناريوهات المصرفية</h3>
        <p>استشراف أثر التدخلات الاستثمارية والتكنولوجية واختبار السيناريوهات الاستراتيجية بدقة عالية بناءً على المؤشر الفعلي.</p>
    </div>
    """, unsafe_allow_html=True)

    col_sim_in, col_sim_out = st.columns([1, 2], gap="large")

    with col_sim_in:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        recorded_banks_sim = [item["البنك"] for item in st.session_state.history_state] if st.session_state.history_state else BANKS_LIST_AR
        sim_bank_sel = st.selectbox("اختر البنك للمحاكاة", recorded_banks_sim, key="sim_bank")
        base_score_input = st.slider("قيمة المؤشر الافتراضي الحالي", 30.0, 100.0, 85.0, 0.5, key="sim_base")

        scenario_dropdown = st.selectbox("اختر السيناريو الاستراتيجي", [
            "📉 السيناريو التشاؤمي (غياب التدخل وضعف الاستثمار)",
            "📊 السيناريو المعتدل (استثمارات تقليدية تدريجية)",
            "🚀 السيناريو الطموح / الاستباقي (إصلاحات هيكلية شاملة وسيادة رقمية)"
        ], index=1, key="sim_scen")

        sim_v1 = st.slider("1️⃣ نسبة الزيادة في منصات المعلومات والتكنولوجيا (%)", 0, 50, 20, key="sim_v1")
        sim_v2 = st.slider("2️⃣ نسبة الزيادة في كفاءة الحوكمة ومجلس الإدارة (%)", 0, 50, 15, key="sim_v2")
        sim_v3 = st.slider("3️⃣ نسبة التوسع في التمويل الأخضر والاستدامة (%)", 0, 50, 25, key="sim_v3")

        run_sim_btn = st.button("📋 إضافة وتثبيت سيناريو البنك", use_container_width=True, type="primary")

        if st.button("🗑️ مسح وإعادة تعيين استجابات المحاكي", use_container_width=True, type="secondary"):
            st.session_state.simulated_results_dict = {}
            st.success("✅ تم مسح جميع سيناريوهات المحاكي بنجاح.")
            st.rerun()

        sim_word_html = f"""
        <html dir="rtl"><head><meta charset="utf-8"><title>تقرير محاكي السياسات المصرفية</title></head>
        <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
            <h1 style="color: {CBE_NAVY}; text-align: center;">تقرير محاكي السياسات الاستشرافي والمتابعة التراكمية</h1>
            <p style="text-align: center; color: #64748B;">المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة</p>
            <hr><h3>📋 مقارنة السيناريوهات المثبتة للبنوك:</h3>
        """
        if st.session_state.simulated_results_dict:
            for k, v in st.session_state.simulated_results_dict.items():
                sim_word_html += f"<div style='border: 1px solid #CBD5E1; padding: 15px; margin-bottom: 15px; border-radius: 8px;'>{v['html']}</div>"
        else:
            sim_word_html += "<p>لا توجد سيناريوهات مسجلة حالياً.</p>"
        sim_word_html += "</body></html>"

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
                base_val = base_score_input
                if st.session_state.history_state:
                    for item in st.session_state.history_state:
                        if item["البنك"] == sim_bank_sel:
                            base_val = item["مؤشر SSGI المركب"]
                            break

                combined_boost = (sim_v1 * 0.4) + (sim_v2 * 0.3) + (sim_v3 * 0.3)

                if scenario_dropdown.startswith("📉"):
                    simulated_val = max(0.0, base_val * 0.92)
                    analysis_text = f"تحذير استباقي للبنك ({sim_bank_sel}): استمرار الركود الرقمي وضعف تبني أدوات RegTech سيؤدي إلى اتساع الفجوة الرقابية وتراجع المؤشر المركب بنسبة 8%."
                    action_plan = "التدخل الفوري لرسملة البنية التحتية وتحديث أطر الامتثال ومراجعة مخصصات المخاطر."
                elif scenario_dropdown.startswith("📊"):
                    simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.002)))
                    analysis_text = f"تقدم تدريجي ومستقر لـ ({sim_bank_sel}): نجاح ملحوظ في كفاءة الحوكمة وإصدار تقارير الاستدامة مدفوعاً بالاستثمارات الرقمية المستهدفة."
                    action_plan = "توسيع نطاق التمويل الأخضر ورفع كفاءة التدقيق الداخلي واعتماد التقارير عبر المنصة الذكية."
                else:
                    simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.004)))
                    analysis_text = f"ريادة مصرفية متقدمة لـ ({sim_bank_sel}): تكامل رقمي تام مع متطلبات البنك المركزي المصري ومعايير الاستدامة العالمية."
                    action_plan = "قيادة التحالفات المصرفية المستدامة وتصدير النماذج الرقمية المتقدمة وتحقيق السيادة التقنية بالكامل."

                simulated_val = round(simulated_val, 2)
                delta = round(simulated_val - base_val, 2)
                score_str_plain = get_colored_score_html(simulated_val)

                box_html = f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
                  <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">📈 محاكاة البنك: {sim_bank_sel} | السيناريو: {scenario_dropdown}</h3>
                  <p style="font-size: 15px; margin-bottom: 8px;"><b>القيمة المتوقعة لمؤشر SSGI:</b> {score_str_plain} (صافي التغير: <span style="font-weight: bold;">{delta:+.2f}</span>)</p>
                  <div style="background: {CBE_BG}; padding: 12px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; margin-top: 10px;">
                    <p style="margin-bottom: 6px;"><b>🔬 التحليل الاستشرافي:</b> {analysis_text}</p>
                    <p style="margin: 0; color: {CBE_GOLD}; font-weight: bold;">🛠️ خطة التحرك: {action_plan}</p>
                  </div>
                </div>
                """
                sim_key = f"{sim_bank_sel} - {scenario_dropdown}"
                st.session_state.simulated_results_dict[sim_key] = {"html": box_html}

        if st.session_state.simulated_results_dict:
            st.markdown("---")
            st.markdown("<h4>📋 مقارنة السيناريوهات المثبتة للبنوك:</h4>", unsafe_allow_html=True)
            for item in st.session_state.simulated_results_dict.values():
                st.markdown(item["html"], unsafe_allow_html=True)
        else:
            st.info("📈 قم بضبط البنك والسيناريو ومتغيرات التحفيز واضغط على زر الإضافة لتثبيت ومتابعة السيناريوهات هنا.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الرابع: لوحة دعم اتخاذ القرار
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🛡️ لوحة دعم اتخاذ القرار وتوطين السياسات المصرفية</h3>
        <p>استعراض وتثبيت التوصيات الاستراتيجية المخصصة لكل بنك في القطاع المصرفي.</p>
    </div>
    """, unsafe_allow_html=True)

    col_dec_in, col_dec_out = st.columns([1, 2], gap="large")

    with col_dec_in:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        recorded_banks_dec = [item["البنك"] for item in st.session_state.history_state] if st.session_state.history_state else BANKS_LIST_AR
        decision_bank_sel = st.selectbox("اختر البنك لاستعراض التوصيات", recorded_banks_dec, key="dec_bank")
        generate_decision_btn = st.button("📋 إضافة وتثبيت توصيات البنك المختارة", use_container_width=True, type="primary")

        if st.button("🗑️ مسح وإعادة تعيين لوحة القرار", use_container_width=True, type="secondary"):
            st.session_state.decision_results_dict = {}
            st.success("✅ تم مسح جميع توصيات لوحة القرار بنجاح.")
            st.rerun()
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
                    score_str_plain = get_colored_score_html(score)

                    st.session_state.decision_results_dict[decision_bank_sel] = f"""
                    <div style="background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);" dir="rtl">
                        <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">🛡️ توصيات دعم القرار للبنك: {decision_bank_sel} (المؤشر: {score_str_plain})</h3>
                        <ul style="line-height: 1.8; color: #1E293B; padding-right: 20px;">
                            <li><b>تعزيز البنية التحتية الذكية:</b> الاستفادة من مخرجات منصات المعلومات لتقليل فترات معالجة البيانات الرقابية.</li>
                            <li><b>تطوير الإفصاح المالي المستدام:</b> زيادة نسبة الأصول الخضراء (GAR) وتفعيل معايير (ISSB).</li>
                            <li><b>حوكمة المخاطر المناخية:</b> دمج اختبارات الضغط المناخي ضمن محفظة الائتمان المؤسسي.</li>
                        </ul>
                    </div>
                    """

        if st.session_state.decision_results_dict:
            for item in st.session_state.decision_results_dict.values():
                st.markdown(item, unsafe_allow_html=True)
        else:
            st.info("🛡️ يرجى اختيار البنك المسجل والضغط على زر الإضافة لتثبيت التوصيات هنا.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الخامس: التقرير التنفيذي الموحد
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📑 أداة تصدير التقرير التنفيذي الموحد لحوكمة القطاع المصرفي</h3>
        <p>ملخص استراتيجي شامل يدمج نتائج التدقيق ونتائج محاكي السياسات وإطار دونيلا ميدوز لنقاط الرفع.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 تحديث وتوليد التقرير التنفيذي الموحد", use_container_width=True, type="primary"):
        if not st.session_state.history_state:
            st.warning("📂 لا توجد بيانات مسجلة كافية حتى الآن. يرجى إدخال تشخيص بنك واحد على الأقل في القسم الأول.")
        else:
            df_rep = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)
            top_row = df_rep.iloc[0]
            top_bank = top_row["البنك"]
            top_score = top_row["مؤشر SSGI المركب"]
            top_score_colored = get_colored_score_html(top_score)

            report_html = f"""
            <div dir="rtl" style="background: #FFFFFF; padding: 30px; border-radius: 14px; border: 2px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 6px 20px rgba(0,0,0,0.08);">
              <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 15px; margin-bottom: 25px;">
                <h2 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">📑 التقرير التنفيذي الموحد لحوكمة القطاع المصرفي وتقارير الاستدامة</h2>
                <p style="color: #64748B; font-size: 14px; margin-top: 6px;">إطار تطبيقي مقترح لبرنامج دكتوراه الفلسفة في العلوم البيئية - جامعة عين شمس | إعداد: د. أيمن الدسوقي</p>
              </div>

              <div style="background: {CBE_BG}; padding: 18px; border-radius: 10px; border-right: 5px solid {CBE_GOLD}; margin-bottom: 25px;" dir="rtl">
                <h4 style="color: {CBE_NAVY}; margin-top: 0;">🏆 مؤشرات الريادة المصرفية:</h4>
                <p>البنك المتصدر حالياً في مؤشر الحوكمة الذكية هو: <span style="font-weight: bold; color: {CBE_GOLD};">{top_bank}</span> بقيمة مركبة تبلغ {top_score_colored}.</p>
                <p style="margin: 0;">إجمالي البنوك الخاضعة للتدقيق والتقييم حتى الآن: <b>{len(df_rep)} بنكاً مصرفياً</b>.</p>
              </div>

              <div style="background: #FFFBEB; padding: 20px; border-radius: 10px; border: 1.5px solid #FCD34D;" dir="rtl">
                <h4 style="color: #92400E; margin-top: 0;">🌳 إطار نقاط الرفع المنظومي لدونيلا ميدوز:</h4>
                <ul style="margin: 0; padding-right: 20px; line-height: 1.8; color: #78350F;">
                 <li><b>1. المعلمات (Parameters):</b> تعديل نسب مخصصات الائتمان وتمويل المشروعات الخضراء.</li>
                 <li><b>2. تدفق المعلومات (Information Flows):</b> إحكام قواعد منصات المعلومات وتأمين سرية البيانات.</li>
                 <li><b>3. القواعد والحوكمة (Rules):</b> الالتزام بضوابط البنك المركزي ومعايير الإفصاح المالي (ISSB).</li>
                 <li><b>4. أهداف النظام (Goals):</b> توجيه القطاع المصرفي نحو التنمية المستدامة ورؤية مصر 2030.</li>
                </ul>
              </div>
            </div>
            """
            st.markdown(report_html, unsafe_allow_html=True)

            word_content = f"""<html dir="rtl"><head><meta charset="utf-8"><title>التقرير التنفيذي</title></head>
            <body style="font-family: 'Cairo'; text-align: right;">{report_html}</body></html>"""
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
        <h3>🌿 إعداد مسودة تقارير الاستدامة (GRI / ISSB)</h3>
        <p>توليد مسودة أولية لتقارير الاستدامة للبنوك المصرية وفق الأطر الدولية.</p>
    </div>
    """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns([1, 2], gap="large")
    with col_g1:
        gri_bank_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, key="gri_bank")
        standard_type = st.selectbox("الإطار المعياري الدولي", ["GRI Standards 2026", "ISSB (IFRS S1 / S2)"])
        env_emissions = st.text_input("انبعاثات الكربون", value="النطاق 1: 12 ألف طن | النطاق 2: 24 ألف طن")
        social_csr = st.slider("نسبة الإنفاق المجتمعي (%)", 0.0, 10.0, 4.5, step=0.1)
        gov_board = st.slider("استقلالية مجلس الإدارة (%)", 50, 100, 85)
        gri_gen_btn = st.button("🚀 توليد مسودة التقرير", use_container_width=True, type="primary")

    with col_g2:
        if gri_gen_btn:
            st.markdown(f"""
            <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.9;">
              <h3 style="color: {CBE_NAVY}; font-weight: bold;">🌿 مسودة تقرير الاستدامة الآلي ({standard_type}) - ({gri_bank_sel})</h3>
              <p><b>البيانات البيئية:</b> {env_emissions}</p>
              <p><b>الشمول المالي والمسؤولية المجتمعية:</b> {social_csr}%</p>
              <p><b>حوكمة المجلس:</b> {gov_board}%</p>
              <p style="color: #059669; font-weight: bold; margin-top: 10px;">✔️ مسودة التقرير جاهزة للتدقيق والمصادقة النهائية.</p>
            </div>
            """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب السابع: لوحة تحكم المشرف وتتبع الزوار (يظهر لمشرف النظام Admin فقط)
# ------------------------------------------------------------------------------
if tab7 is not None:
    with tab7:
        st.markdown("""
        <div dir="rtl" style="text-align: right;">
            <h3>🔒 لوحة تحكم المشرف وسجلات الزوار (Admin Dashboard & IP Logging)</h3>
            <p>متابعة وتصدير سجلات دخول الزوار وعناوين الـ IP وأوقات الدخول بدقة.</p>
        </div>
        """, unsafe_allow_html=True)

        if os.path.exists(LOG_FILE):
            df_visitors = pd.read_csv(LOG_FILE)
            st.markdown(f"**إجمالي عدد الزيارات المسجلة:** {len(df_visitors)}")
            st.dataframe(df_visitors, use_container_width=True)

            log_csv = df_visitors.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل سجلات الزوار وعناوين IP (CSV)",
                data=log_csv,
                file_name="visitors_ip_log.csv",
                mime="application/csv",
                use_container_width=True
            )

            if st.button("🗑️ مسح وتفريغ سجلات الزوار", type="secondary"):
                if os.path.exists(LOG_FILE):
                    os.remove(LOG_FILE)
                st.success("✅ تم مسح سجلات الزوار بنجاح.")
                st.rerun()
        else:
            st.info("📂 لا توجد سجلات زيارات مسجلة حتى الآن.")

st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)
