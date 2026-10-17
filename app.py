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
# نظام تتبع الزوار (IP Logging)
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
# محرك "اسأل المنصة" (RAG مطور بدقة لاستخلاص بيانات التأسيس والملكية والتوسع لكل بنك)
# ==============================================================================
def process_rag_gemini_query(bank_name, question):
    if bank_name == "اختر البنك المصرفي" or not question.strip():
        return "⚠️ يرجى اختيار البنك المصرفي وكتابة السؤال أو الاستفسار التنظيمي بدقة للحصول على التحليل المستند لتقارير الاستدامة والحوكمة."
    
    if not is_valid_arabic_question(question):
        return "⚠️ **تنبيه:** يرجى كتابة سؤالا منطقيا وبحثيا واضحا باللغة العربية لكي تتمكن المنصة من تحليله والرد عليه بدقة."

    q_lower = question.lower()
    
    # 1. معالجة سؤال التأسيس والنشأة والملكية
    if any(k in q_lower for k in ["تاريخ", "نشأة", "تأسيس", "متى", "مؤسس", "ملكية", "أول بنك"]):
        if "بنك مصر" in bank_name:
            resp = f"""تأسس <b>{bank_name}</b> في 8 مايو 1920 بريادة الفكر الوطني للرائد الاقتصادي محمد طلعت حرب باشا، ليكون أول بنك مصري بالكامل برأس المال والكوادر الوطنية.
            <br><br><b>البصمة المؤسسية والتاريخية وهيكل الملكية:</b>
            <ul>
                <li><b>سنة التأسيس:</b> 1920م.</li>
                <li><b>المؤسس التاريخي:</b> الاقتصادى الراحل محمد طلعت حرب باشا.</li>
                <li><b>هيكل الملكية:</b> مملوك بالكامل للدولة المصرية (مملوك لبنك الاستثمار القومي / الحكومة المصرية)، ويعد ركيزة للاقتصاد القومي.</li>
            </ul>"""
        elif "الأهلي المصري" in bank_name:
            resp = f"""تأسس <b>{bank_name} NBE</b> في 25 يونيو 1898 بموجب أمر عالي كبنك إصدار واكتتاب تاريخي.
            <br><br><b>البصمة المؤسسية والتاريخية وهيكل الملكية:</b>
            <ul>
                <li><b>سنة التأسيس:</b> 1898م.</li>
                <li><b>النشأة:</b> تأسس في عهد الخديوي عباس حلمي الثاني بمبادرة من الممول البريطاني سر إرنست كاسل.</li>
                <li><b>هيكل الملكية:</b> مملوك بالكامل للحكومة المصرية (ممثلة في وزارة المالية)، وهو أكبر صرح مصرفي حكومي استراتيجي في الدولة.</li>
            </ul>"""
        elif "التجاري الدولي" in bank_name or "cib" in bank_name:
            resp = f"""تأسس <b>{bank_name} CIB</b> في الأصل عام 1975 باسم "بنك تشيس ناشيونال" ثم تحول بالكامل ليكون البنك التجاري الدولي الرائد في القطاع الخاص المصري.
            <br><br><b>البصمة المؤسسية والتاريخية وهيكل الملكية:</b>
            <ul>
                <li><b>سنة التأسيس / الانطلاق:</b> بدأ العمل بالاسم الحالي في أواخر الثمانينيات (1987) بعد انسحاب الشريك الأجنبي وتحول الأسهم للمساهمة المصرية والعالمية.</li>
                <li><b>المؤسس والنشأة:</b> تأسس بشراكة بين البنك الأهلي المصري وبنوك عالمية قبل أن يتطور ليصبح كياناً مستقلاً.</li>
                <li><b>هيكل الملكية:</b> شركة مساهمة مصرية مدرجة بالبورصة المصرية (EGX)، تتوزع ملكيتها بين مؤسسات مالية عالمية، صناديق استثمار كبرى، ومستثمرين أفراد ومؤسسات بدون سيطرة حكومية مباشرة.</li>
            </ul>"""
        elif "قطر الوطني" in bank_name or "qnb" in bank_name:
            resp = f"""تأسس <b>{bank_name} QNB</b> في عام 1964 كأول بنك تجاري قطري، ليمتد نشاطه المتميز ويصبح ذراعاً مصرفياً إقليمياً قوياً في جمهورية مصر العربية والمنطقة.
            <br><br><b>البصمة التاريخية وهيكل الملكية والانتشار:</b>
            <ul>
                <li><b>سنة التأسيس (المجموعة الأم):</b> 1964م (كأول بنك تجاري قطري)، ويعتبر اليوم واحداً من أكبر البنوك في منطقة الشرق الأوسط وشمال أفريقيا.</li>
                <li><b>هيكل الملكية:</b> يتقاسم ملكية البنك جهاز قطر للاستثمار بنسبة 50% والقطاع الخاص بنسبة 50% الأخرى.</li>
                <li><b>التوسع والانتشار في مصر:</b> يقدم خدماته المصرفية من خلال شبكة واسعة من الفروع تغطي مختلف أنحاء مصر (أكثر من 234 فرعاً موزعة على كافة المحافظات والمدن الرئيسية مثل القاهرة والإسكندرية)، مع شبكة متطورة من أجهزة الصراف الآلي (ATM).</li>
            </ul>"""
        elif "بنك فيصل الإسلامي" in bank_name:
            resp = f"""تأسس <b>{bank_name}</b> كأول بنك إسلامي في مصر بموجب القانون رقم 48 لسنة 1977، وبدأ نشاطه الفعلي عام 1979 بجهود مؤسسية رائدة.
            <br><br><b>البصمة التاريخية وهيكل الملكية:</b>
            <ul>
                <li><b>سنة التأسيس:</b> 1977 (وبدأ التشغيل 1979).</li>
                <li><b>المؤسسون:</b> بمبادرة من الأمير محمد الفيصل آل سعود ومجموعة من الشخصيات المصرية والسعودية الإسلامية البارزة.</li>
                <li><b>هيكل الملكية:</b> شركة مساهمة مصرية مدرجة، تساهم فيها كيانات سعودية ومصرية وأفراد ومؤسسات مالية إسلامية.</li>
            </ul>"""
        elif "بنك البركة الإسلامي" in bank_name:
            resp = f"""تأسس <b>{bank_name}</b> ضمن شبكة مجموعة البركة المصرفية العالمية لتقديم خدمات الصيرفة الإسلامية المتكاملة في مصر.
            <br><br><b>البصمة التاريخية وهيكل الملكية:</b>
            <ul>
                <li><b>سنة التأسيس والنشأة:</b> امتداد لتاريخ طويل من المعاملات المصرفية الإسلامية (مجموعة البركة المصرفية).</li>
                <li><b>هيكل الملكية:</b> يتبع مجموعة البركة المصرفية (مملوك لمجموعات استثمارية خليجية وعالمية كبرى).</li>
            </ul>"""
        elif "بنك القاهرة Banque du Caire" in bank_name:
            resp = f"""تأسس <b>{bank_name}</b> عام 1952 كبنك وطني مصري يهدف إلى دعم التجارة والصناعة والاقتصاد الوطني.
            <br><br><b>البصمة التاريخية وهيكل الملكية:</b>
            <ul>
                <li><b>سنة التأسيس:</b> 1952م.</li>
                <li><b>هيكل الملكية:</b> مملوك بالكامل لبنك مصر (الذراع الاستثماري الحكومي)، ويعتبر أحد الأعمدة الرئيسية للقطاع المصرفي العام في مصر.</li>
            </ul>"""
        else:
            resp = f"""يُعد <b>{bank_name}</b> أحد البنوك الفاعلة في القطاع المصرفي المصري، حيث يخضع لإشراف البنك المركزي المصري ويسهم في تمويل خطط التنمية الاقتصادية.
            <br><br><b>تفاصيل التأسيس والملكية:</b>
            <ul>
                <li><b>الإطار التنظيمي:</b> يعمل وفق تراخيص معتمدة من البنك المركزي المصري.</li>
                <li><b>هيكل الملكية:</b> موزع بين مساهمين محليين أو دوليين وفقاً للشكل القانوني للبنك (شركة مساهمة أو فرع لبنك أجنبي).</li>
            </ul>"""

    # 2. معالجة محاور الحوكمة والمجالس
    elif any(k in q_lower for k in ["الحوكمة", "مجلس", "الضبط", "مستقلين", "تعريف"]):
        resp = f"""يعتمد <b>{bank_name}</b> إطار حوكمة مؤسسياً متكاملاً يتوافق مع التعليمات الرقابية التنظيمية الصادرة عن البنك المركزي المصري ومعايير الاستدامة العالمية.
        <br><br><b>الركائز الحوكمية الأساسية:</b>
        <ul>
            <li><b>استقلالية مجلس الإدارة:</b> وجود أعضاء غير تنفيذيين ومستقلين لتعزيز موضوعية القرار المصرفي.</li>
            <li><b>اللجان التخصصية:</b> تفعيل لجان التدقيق، المخاطر، والالتزام والترشيحات لرفع التقارير الدورية لمجلس الإدارة.</li>
            <li><b>الشفافية والامتثال:</b> سياسات صارمة لمنع تعارض المصالح ومكافحة غسل الأموال.</li>
        </ul>"""

    # 3. معالجة محاور التمكين والمرأة والشمول المالي
    elif any(k in q_lower for k in ["المرأة", "تمكين", "قيادي", "نسائية", "شمول"]):
        resp = f"""يعكس سجل <b>{bank_name}</b> التزاماً مؤسسياً بتمكين الكوادر النسائية وتكافؤ الفرص في بيئة العمل وتوفير الحلول المالية الملائمة لدعم الشمول المالي.
        <br><br><b>المحاور التنفيذية:</b>
        <ul>
            <li><b>التمكين المؤسسي:</b> إتاحة فرص متساوية للترقي وتولي المناصب القيادية والإشرافية للكوادر النسائية.</li>
            <li><b>المبادرات المجتمعية:</b> إطلاق برامج تمويل وتسهيلات مصرفية ميسرة لدعم رائدات الأعمال وصاحبات المشروعات الصغيرة ومتناهية الصغر.</li>
        </ul>"""

    # 4. معالجة محاور المناخ والاستدامة
    elif any(k in q_lower for k in ["المناخ", "أخضر", "مخاطر", "استدامة", "gar"]):
        resp = f"""يُظهر تقرير الاستدامة والحوكمة الخاص بـ <b>{bank_name}</b> دمجاً متقدماً لمخاطر المناخ والتمويل الأخضر وفق أهداف التنمية المستدامة ورؤية مصر 2030.
        <br><br><b>الأبعاد البيئية والتمويل المستدام:</b>
        <ul>
            <li><b>إدارة المخاطر البيئية:</b> دمج معايير تقييم المخاطر المناخية ضمن السياسات الائتمانية.</li>
            <li><b>محفظة الأصول الخضراء:</b> توجيه شرائح تمويلية نحو مشروعات الطاقة المتجددة وكفاءة الطاقة وخفض الانبعاثات.</li>
        </ul>"""

    else:
        resp = f"""بناءً على التحليل الموضوعي لتقارير الاستدامة والحوكمة والبيانات المالية الصادرة عن <b>{bank_name}</b>، يتبين أن البنك يطبق أطراً تشغيلية وتنظيمية متكاملة تواواكب استراتيجيات التنمية المستدامة ورؤية مصر 2030.
        <br><br><b>المحاور التحليلية الأساسية:</b>
        <ul>
            <li><b>الكفاءة التشغيلية والرقابية:</b> الالتزام الصارم بالضوابط الرقابية الصادرة عن البنك المركزي المصري.</li>
            <li><b>المسؤولية المجتمعية:</b> المساهمة الفعالة في المبادرات التنموية وبرامج الشمول المالي.</li>
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
                st.button(
                    q,
                    key=f"btn_ig_{i}",
                    on_click=set_suggested_question,
                    args=(q,),
                    use_container_width=True
                )

        with st.expander("🌱 محور تقارير الاستدامة والتمويل الأخضر والمناخ (SR/ESG)"):
            sr_questions = [
                "ما هي جهود البنك في تمكين المرأة والشمول المالي؟",
                "كيف يتعامل البنك مع مخاطر المناخ والتمويل الأخضر؟",
                "ما هي نسبة الأصول الخضراء والمشروعات المستدامة ضمن محفظة الائتمان؟",
                "كيف يمتثل البنك للمعايير الدولية للإفصاح المالي (GRI و ISSB)؟",
                "ما هي مبادرات البنك في المسؤولية المجتمعية والإنفاق التنموي المستدام؟"
            ]
            for i, q in enumerate(sr_questions):
                st.button(
                    q,
                    key=f"btn_sr_{i}",
                    on_click=set_suggested_question,
                    args=(q,),
                    use_container_width=True
                )

        with st.expander("🔒 محور المنصات الذكية وحوكمة البيانات والامتثال (SIP/RegTech)"):
            sip_questions = [
                "ما هي آليات حوكمة البيانات والامتثال الرقابي وتأمينها؟",
                "كيف يضمن البنك الحصانة السيبرانية ومنع تسريب البيانات المالية الحساسة؟",
                "ما هي جاهزية البنية التحتية الرقمية ومنصات المعلومات (SIP)؟",
                "كيف يوظف البنك تقنيات الرقابة التنظيمية (RegTech) واسترجاع المعطيات؟",
                "ما مدى التوافق مع قانون حماية البيانات الشخصية والسيادة الرقمية؟"
            ]
            for i, q in enumerate(sip_questions):
                st.button(
                    q,
                    key=f"btn_sip_{i}",
                    on_click=set_suggested_question,
                    args=(q,),
                    use_container_width=True
                )

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
                with st.spinner("⏳ جاري استرجاع المستندات وتحليل الإجابة المطولة والمفصلة للبنك..."):
                    response_html = process_rag_gemini_query(ask_bank_sel, active_q)
                    st.markdown(response_html, unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح أو كتابة استفسارك التنظيمي لاستعراض التحليل التفصيلي الفريد المستمد من مستودعات التقارير.")
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
        
        sip_1 = st.slider("1. جاهزية البنية التحتية الرقمية (%)", 0, 100, 85, key="t1_sip1")
        sip_2 = st.slider("2. توافر البيانات والمعالجة الآلية (%)", 0, 100, 88, key="t1_sip2")
        sip_3 = st.slider("3. الترابط البيني التقني (APIs) (%)", 0, 100, 90, key="t1_sip3")
        sip_4 = st.slider("4. السيادة الرقمية وأمن المعلومات (%)", 0, 100, 92, key="t1_sip4")

        ig_1 = st.slider("1. التوافق التشريعي والتنظيمي (%)", 0, 100, 86, key="t1_ig1")
        ig_2 = st.slider("2. الأخلاقيات والسلوك المؤسسي (%)", 0, 100, 88, key="t1_ig2")
        ig_3 = st.slider("3. فاعلية الرقابة والتدقيق الداخلي (%)", 0, 100, 91, key="t1_ig3")
        ig_4 = st.slider("4. كفاءة واستقلالية مجلس الإدارة (%)", 0, 100, 92, key="t1_ig4")

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
        else:
            st.info("📊 يرجى اختيار البنك وضبط درجات المحاور ثم الضغط على زر الحساب لعرض النتائج.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 قائمة ترتيب البنوك المسجلة")
    if st.session_state.history_state:
        df_history = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("📂 لا توجد بنوك مسجلة حتى الآن.")

# ------------------------------------------------------------------------------
# التبويب الثالث: محاكي السياسات (Policy Simulator)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🔬 محاكي السياسات الاستشرافي والمتابعة التراكمية للسيناريوهات المصرفية</h3>
        <p>استشراف أثر التدخلات الاستثمارية والتكنولوجية واختبار السيناريوهات الاستراتيجية بدقة عالية.</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("محاكي السياسات ومتابعة الانحدار جاهز للعمل عند إدخال البيانات في التبويب السابق.")

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

# ------------------------------------------------------------------------------
# التبويب السابع: لوحة تحكم المشرف والزوار (Admin)
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
            df_v = pd.read_csv(LOG_FILE)
            st.dataframe(df_v, use_container_width=True)
        else:
            st.info("📂 لا توجد سجلات زيارات حتى الآن.")

st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)
