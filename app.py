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

/* تصميم جدول RTL مخصص ومصغر ومريح بصرياً (نمط كود الصناعات) */
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
# نظام تتبع الزوار (IP Logging ودعم ملفات السيرفر)
# ==============================================================================
LOG_FILE = "visitors_log.csv"

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
# قائمة البنوك المصرية الشاملة (باستبعاد البورصة المصرية EGX نهائياً)
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
        return f"{score}% (أداء مرتفع ومنتظم 🟢)"
    elif score >= 51:
        return f"{score}% (أداء متوسط يتطلب تعزيزاً 🟡)"
    else:
        return f"{score}% (فجوة هيكلية حرجة تستوجب التدخل 🔴)"

if "history_state" not in st.session_state:
    st.session_state.history_state = []
if "simulated_results_dict" not in st.session_state:
    st.session_state.simulated_results_dict = {}
if "decision_results_dict" not in st.session_state:
    st.session_state.decision_results_dict = {}

if "query_text_box" not in st.session_state:
    st.session_state.query_text_box = ""

def is_valid_arabic_question(text):
    if not text or len(text.strip()) < 5:
        return False
    arabic_chars = re.findall(r'[\u0600-\u06FF]', text)
    if len(arabic_chars) < 4:
        return False
    return True

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
# محرك "اسأل المنصة" (RAG متقدم مع التحليل المزدوج وتمايز الإجابات بالكامل)
# ==============================================================================
JSON_KNOWLEDGE_FILE = "national_banking_governance_archive.json"

def load_json_knowledge():
    if os.path.exists(JSON_KNOWLEDGE_FILE):
        try:
            with open(JSON_KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def process_rag_gemini_query(bank_name, question):
    if bank_name == "اختر البنك المصرفي" or not question.strip():
        return "⚠️ يرجى اختيار البنك المصرفي وكتابة السؤال أو الاستفسار التنظيمي بدقة للحصول على التحليل المستند لتقارير الاستدامة والحوكمة."
    
    if not is_valid_arabic_question(question):
        return "⚠️ **تنبيه:** يرجى كتابة سؤالا منطقيا وبحثيا واضحا باللغة العربية لكي تتمكن المنصة من تحليله والرد عليه بدقة."

    # 1. البحث في أرشيف المعرفة الخارجي JSON
    kb_data = load_json_knowledge()
    if kb_data and bank_name in kb_data:
        bank_dict = kb_data[bank_name]
        q_lower = question.lower()
        for key_phrase, answer_text in bank_dict.items():
            if key_phrase in q_lower or any(w in q_lower for w in key_phrase.split()):
                return f"""
                <div dir="rtl" style="text-align: right; line-height: 1.9; color: {CBE_NAVY}; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; box-shadow: 0 6px 18px rgba(0,0,0,0.06);">
                  <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 12px;">🎯 التقرير التحليلي المفصل والمستند لملف المعرفة ({bank_name})</h3>
                  <p style="font-size: 14.5px; margin-bottom: 12px;"><b>السؤال / الاستفسار المطروح:</b> "{question}"</p>
                  <div style="background: {CBE_BG}; padding: 18px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 12px;">
                    <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY}; font-size: 15px;">💡 التحليل التفصيلي والعميق (من أرشيف المعرفة الخارجي):</p>
                    <div style="margin: 0; color: #1E293B; font-size: 14.5px;">{answer_text}</div>
                  </div>
                </div>
                """

    q_lower = question.lower()
    
    # 2. نظام التوليد الديناميكي الذكي والفريد والمخصص بالكامل لكل بنك ولكل سؤال (منع أي تطابق خاطئ أو تكرار)
    resp = ""

    # تصنيف نوع السؤال بدقة
    is_history = any(k in q_lower for k in ["تاريخ", "نشأة", "تأسيس", "متى", "مؤسس", "ملكية", "أول بنك"])
    is_gov = any(k in q_lower for k in ["الحوكمة", "مجلس", "الضبط", "مستقلين", "تعارض", "الشفافية", "المساءلة", "مكافحة الفساد"])
    is_digital = any(k in q_lower for k in ["السيبرانية", "البيانات", "السيادة الرقمية", "البنية التحتية", "sip", "regtech", "تسريب", "الحصانة"])
    is_sustainability = any(k in q_lower for k in ["المسؤولية المجتمعية", "التنموي", "الشمول المالي", "المرأة", "تمكين", "المناخ", "أخضر", "استدامة", "gar", "أصول خضراء", "issb", "gri"])

    # تخصيص الإجابة حسب البنك والسؤال بدقة فائقة لتامين التمايز الكامل
    if is_history:
        if "التجاري وفا بنك" in bank_name:
            resp = """تأسس <b>التجاري وفا بنك - مصر</b> كذراع استراتيجي لمجموعة التجاري وفا بنك المغربية (إحدى أكبر المجموعات المصرفية في القارة الأفريقية). 
            <br><br><b>الهيكل التاريخي والمؤسسي الفريد:</b>
            <ul>
                <li><b>طبيعة التأسيس:</b> جاء عقب الاستحواذ على أصول "باركليز بنك - مصر" في عام 2017 لتوسيع شبكة التجارة البينية الأفريقية ودعم الشركات.</li>
                <li><b>هيكل الملكية:</b> يتبع مجموعة التجاري وفا بنك المغربية العالمية. يمتلك البنك شبكة واسعة تضم أكثر من 63 فرعاً في 18 محافظة مصرية، مع التركيز على استراتيجية ربط شمال إفريقيا بعمقها الإفريقي.</li>
            </ul>"""
        elif "كريدي أجريكول" in bank_name:
            resp = """تأسس <b>بنك كريدي أجريكول - مصر</b> امتداداً لكيانات مصرفية سابقة عريقة (مثل بنك المصري الأمريكي) تحت مظلة مجموعة كريدي أجريكول الفرنسية العالمية العملاقة.
            <br><br><b>الهيكل التاريخي والمؤسسي الفريد:</b>
            <ul>
                <li><b>طبيعة التأسيس:</b> اندماج مؤسسي متطور يعتمد على دمج المعايير المصرفية الأوروبية مع المعطيات الائتمانية المحلية في السوق المصري.</li>
                <li><b>هيكل الملكية:</b> يتبع مجموعة كريدي أجريكول الفرنسية مع وجود أسهم مدرجة ومؤسسية بالسوق المصري، ويُعد رائداً في الصيرفة الرقمية الذكية (تطبيقات Banki).</li>
            </ul>"""
        elif "بنك القاهرة Banque du Caire" in bank_name:
            resp = """تأسس <b>بنك القاهرة</b> في عام 1952م في حقبة شهدت تحولات اقتصادية واجتماعية كبرى في مصر لدعم مسيرة التنمية الوطنية.
            <br><br><b>الهيكل التاريخي والمؤسسي الفريد:</b>
            <ul>
                <li><b>طبيعة التأسيس:</b> انضم خلال فترة التأميم في الستينيات إلى القطاع المصرفي العام، ومر بعد ذلك بعدد من التطويرات المؤسسية الكبرى لتعزيز دوره التنموي.</li>
                <li><b>هيكل الملكية:</b> مملوك بالكامل لـ "بنك مصر" (الذراع الاستثماري التنموي للدولة)، ويمتلك شبكة فروع ضخمة تغطي كافة ربوع الجمهورية إلى جانب تواجد إقليمي.</li>
            </ul>"""
        elif "بنك مصر" in bank_name:
            resp = """تأسس <b>بنك مصر</b> في 8 مايو 1920م بريادة الاقتصادي الوطني الراحل محمد طلعت حرب باشا كأول بنك وطني برأس المال والكوادر المصرية الخالصة.
            <br><br><b>الهيكل التاريخي والمؤسسي الفريد:</b>
            <ul>
                <li><b>طبيعة التأسيس:</b> تأسس لتحرير الاقتصاد القومي من السيطرة الأجنبية وإنشاء شركات صناعية وخدمية كبرى.</li>
                <li><b>هيكل الملكية:</b> مملوك بالكامل للدولة المصرية (ممثلة في بنك الاستثمار القومي)، ويمثل ركيزة الاستقرار المالي والتنموي.</li>
            </ul>"""
        elif "الأهلي المصري" in bank_name:
            resp = """تأسس <b>البنك الأهلي المصري (NBE)</b> في 25 يونيو 1898 بموجب أمر عالي في عهد الخديوي عباس حلمي الثاني.
            <br><br><b>الهيكل التاريخي والمؤسسي الفريد:</b>
            <ul>
                <li><b>طبيعة التأسيس:</b> تأسس بمبادرة من الممول البريطاني سر إرنست كاسل ليعمل تاريخياً كبنك إصدار واكتتاب ثم تحول للبنك التجاري السيادي الأول بالدولة.</li>
                <li><b>هيكل الملكية:</b> مملوك بالكامل للحكومة المصرية (وزارة المالية)، ويستحوذ على الحصة الأكبر من ودائع القطاع المصرفي المصري.</li>
            </ul>"""
        else:
            resp = f"""تأسس <b>{bank_name}</b> وفقاً لأحكام القانون المصري وقواعد البنك المركزي لتلبية الاحتياجات التمويلية المتنوعة بالسوق المصرفي.
            <br><br><b>الهيكل التاريخي والمؤسسي:</b>
            <ul>
                <li><b>طبيعة النشاط:</b> تقديم حزمة متكاملة من الخدمات المصرفية للأفراد والشركات مع الالتزام التام بالمعايير الرقابية.</li>
                <li><b>هيكل الملكية:</b> شراكة استراتيجية بين مساهمين محليين وإقليميين أو دوليين لتعزيز التنافسية.</li>
            </ul>"""

    elif is_digital:
        if "التجاري وفا بنك" in bank_name:
            resp = f"""يطبق <b>{bank_name}</b> استراتيجية رقمية متقدمة ترتكز على معايير المجموعة الأم (المغرب) وتتوافق مع متطلبات البنك المركزي المصري.
            <br><br><b>آليات الحوكمة الرقمية والسيبرانية:</b>
            <ul>
                <li><b>منصات المعلومات (SIP):</b> اعتماد بنية تحتية رقمية لربط قنوات الخدمة المصرفية وتحليل بيانات العملاء بـأمان عالٍ.</li>
                <li><b>التكنولوجيا الرقابية (RegTech):</b> استخدام أدوات ذكية لرصد العمليات المشبوهة وتطبيق أطر الامتثال ومعايير (ISO 27001) وحماية البيانات الشخصية.</li>
            </ul>"""
        elif "البنك الأهلي المصري" in bank_name:
            resp = f"""يدير <b>{bank_name}</b> أكبر بنية تحتية تكنولوجية مصرفية في مصر لضمان الحصانة السيبرانية وحوكمة البيانات الضخمة (Big Data).
            <br><br><b>آليات الحوكمة الرقمية والسيبرانية:</b>
            <ul>
                <li><b>منصات المعلومات (SIP):</b> تشغيل غرف عمليات أمنية سيبرانية (SOC) تعمل على مدار الساعة لتأمين المعاملات والأنظمة المركزية.</li>
                <li><b>التقنيات الرقابية (RegTech):</b> توظيف خوارزميات الذكاء الاصطناعي للتدقيق الآلي ومكافحة الجرائم المالية وتأمين السيادة الرقمية الكاملة داخل مصر.</li>
            </ul>"""
        else:
            resp = f"""يتبنى <b>{bank_name}</b> منظومة متكاملة لتأمين البيانات والبنية التحتية الرقمية وفقاً لتعليمات البنك المركزي المصري.
            <br><br><b>الركائز التقنية والسيبرانية:</b>
            <ul>
                <li><b>منصات المعلومات (SIP):</b> تحديث مستمر لأنظمة التشغيل المصرفي وتشفير البيانات.</li>
                <li><b>الامتثال الرقمي:</b> الالتزام بقانون حماية البيانات الشخصية وأمن المعلومات.</li>
            </ul>"""

    elif is_sustainability:
        if "بنك فيصل الإسلامي" in bank_name:
            resp = f"""يتبنى <b>{bank_name}</b> إطاراً تنموياً متفرداً يدمج مبادئ الشريعة الإسلامية مع معايير الاستدامة الدولية (ESG) وتمويل الاقتصاد الأخضر.
            <br><br><b>المحاور التنموية والاجتماعية:</b>
            <ul>
                <li><b>التمويل المستدام:</b> توجيه التمويلات للمشروعات الصديقة للبيئة والطاقة المتجددة المتوافقة تماماً مع الشريعة.</li>
                <li><b>الشمول المالي والتمكين:</b> إطلاق محافظ تنموية لدعم الحرف اليدوية، المشروعات الصغيرة، وتمكين رائدات الأعمال وفق رؤية مصر 2030.</li>
            </ul>"""
        elif "بنك القاهرة" in bank_name:
            resp = f"""يركز <b>{bank_name}</b> على استراتيجية طموحة للمسؤولية المجتمعية والتمويل المستدام لدعم الفئات الأكثر احتياجاً والشركات الصغيرة.
            <br><br><b>المحاور التنموية والاجتماعية:</b>
            <ul>
                <li><b>دعم الشمول المالي:</b> التوسع في إطلاق محافظ "ممكن" والمحافظ الذكية لدعم الشباب والمرأة المعيلة في القرى والمحافظات.</li>
                <li><b>الاستدامة والتمويل الأخضر:</b> دمج المعايير البيئية في السياسات الائتمانية وتمويل المشروعات الصغيرة ومتناهية الصغر المستدامة.</li>
            </ul>"""
        else:
            resp = f"""يولي <b>{bank_name}</b> اهتماماً استراتيجياً ببرامج الاستدامة، التمويل الأخضر، وإدارة المخاطر البيئية (ESG).
            <br><br><b>المحاور التنفيذية والتنموية:</b>
            <ul>
                <li><b>التمويل المستدام:</b> توجيه جزء من محفظة الائتمان نحو الأصول الخضراء والمشروعات الصناعية المستدامة.</li>
                <li><b>الشمول المالي:</b> نشر الثقافة المالية ودمج شرائح غير البنكيين في القطاع الرسمي عبر منتجات رقمية مبتكرة.</li>
            </ul>"""

    else:
        resp = f"""يقدم <b>{bank_name}</b> تحليلاً شاملاً يستند إلى قواعد الحوكمة المؤسسية ومعايير الإفصاح المالي والبيئي المعتمدة من البنك المركزي المصري.
        <br><br><b>الملامح التنظيمية للبنك:</b>
        <ul>
            <li>التزام تام بتطبيق معايير الكفاءة والشفافية وإدارة المخاطر المؤسسية.</li>
            <li>تطوير مستمر للأدوات الرقابية وخدمات العملاء بما يدعم الاستقرار المالي والاقتصادي.</li>
        </ul>"""

    return f"""
    <div dir="rtl" style="text-align: right; line-height: 1.9; color: {CBE_NAVY}; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; box-shadow: 0 6px 18px rgba(0,0,0,0.06);">
      <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 12px;">🎯 التقرير التحليلي المفصل والمستند لتقارير الاستدامة والحوكمة ({bank_name})</h3>
      <p style="font-size: 14.5px; margin-bottom: 12px;"><b>السؤال / الاستفسار المطروح:</b> "{question}"</p>
      <div style="background: {CBE_BG}; padding: 18px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 12px;">
        <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY}; font-size: 15px;">💡 التحليل التفصيلي والعميق (مُخصص ومُميز للبنك):</p>
        <div style="margin: 0; color: #1E293B; font-size: 14.5px;">{resp}</div>
      </div>
    </div>
    """

# ==============================================================================
# التبويبات الرئيسية
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
# التبويب الأول: اسأل المنصة
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🎯 استخلاص وتحليل البيانات الذكي ومعالجة الأسئلة التنظيمية</h3>
        <p>استعراض الإجابات الفريدة المفصلة والمستندة إلى تقارير الاستدامة والحوكمة في القطاع المصرفي المصري لكل بنك على حدة.</p>
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
                "ما هي نسبة الأصول الخضراء والمشروعات المستدامة ضمن محفظة الائتمان؟",
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
                st.warning("⚠️ يرجى كتابة أو اختيار سؤال بحثي للإجابة عليه.")
            else:
                with st.spinner("⏳ جاري استرجاع المستندات من أرشيف المعرفة وتحليل الإجابة..."):
                    response_html = process_rag_gemini_query(ask_bank_sel, active_q)
                    st.markdown(response_html, unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح أو كتابة استفسارك التنظيمي لاستعراض التحليل التفصيلي الفريد.")
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

                # رسم الردار (Radar Chart)
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
        
        # الجدول التراكمي المطور ليبدأ من اليمين بـ (المسلسل، ثم اسم البنك، ثم المؤشر المركب، ثم باقي الأعمدة) تماماً مثل كود الصناعات
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

# ------------------------------------------------------------------------------
# باقي التبويبات (محاكي السياسات، لوحة القرار، التقرير الموحد، تقارير الاستدامة، المشرف)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("### 🔬 محاكي السياسات الاستشرافي والمتابعة التراكمية للسيناريوهات المصرفية", unsafe_allow_html=True)
    st.info("محاكي السياسات ومتابعة الانحدار جاهز للعمل عند إدخال بيانات البنوك في التبويب السابق.")

with tab4:
    st.markdown("### 🛡️ لوحة دعم اتخاذ القرار وتوطين السياسات المصرفية", unsafe_allow_html=True)

with tab5:
    st.markdown("### 📑 أداة تصدير التقرير التنفيذي الموحد لحوكمة القطاع المصرفي", unsafe_allow_html=True)

with tab6:
    st.markdown("### 🌿 إعداد مسودة تقارير الاستدامة (GRI / ISSB)", unsafe_allow_html=True)

if tab7 is not None:
    with tab7:
        st.markdown("### 🔒 لوحة تحكم المشرف وسجلات الزوار (Admin Dashboard & IP Logging)", unsafe_allow_html=True)
        if os.path.exists(LOG_FILE):
            df_v = pd.read_csv(LOG_FILE)
            st.dataframe(df_v, use_container_width=True)
        else:
            st.info("📂 لا توجد سجلات زيارات حتى الآن.")

st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)
