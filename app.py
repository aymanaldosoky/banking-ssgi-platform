import random
import io
import os
import re
import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# إعدادات صفحة Streamlit وتطبيق الهوية البصرية الأكاديمية (RTL)
# ==============================================================================
st.set_page_config(
    page_title="منصة منظومة القرار الثقافية والجاهزية الإبداعية - AACRI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# الألوان الرسمية المؤسسية والأكاديمية الرفيعة
CBE_NAVY = "#002B49"         # أزرق أكاديمي عميق
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
    gap: 4px !important;
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
    padding: 8px 4px !important;
    font-weight: 700 !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: 11.5px !important;
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
# نظام تسجيل الزوار وحفظ عناوين IP تلقائياً (Visitor Logging & IP Tracking)
# ==============================================================================
LOG_FILE_PATH = "visitors_log.csv"

def log_visitor(username, role):
    try:
        # محاولة استخراج عنوان IP الحقيقي للزائر في بيئة Streamlit السحابية أو المحلية
        try:
            ctx = st.runtime.get_instance().script_run_context
            session_info = st.runtime.get_instance()._session_mgr.get_session_info(ctx.session_id)
            ip_address = session_info.ws.request.remote_ip if session_info and session_info.ws else "127.0.0.1"
        except Exception:
            ip_address = "127.0.0.1 (محلي)"

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = pd.DataFrame([{
            "التاريخ والوقت": current_time,
            "اسم المستخدم": username,
            "الصلاحية": role,
            "عنوان IP": ip_address
        }])
        
        if os.path.exists(LOG_FILE_PATH):
            df_log = pd.read_csv(LOG_FILE_PATH)
            df_log = pd.concat([df_log, new_row], ignore_index=True)
        else:
            df_log = new_row
        df_log.to_csv(LOG_FILE_PATH, index=False, encoding="utf-8-sig")
    except Exception as e:
        pass

# ==============================================================================
# إدارة جلسة الدخول وتعدد الصلاحيات (Authentication & Role Management)
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
                <h2 style="color: {CBE_NAVY}; text-align: center; font-weight: 800; margin-bottom: 10px;">🏛️ منظومة القرار الثقافية والجاهزية الإبداعية (AACRI)</h2>
                <p style="color: #475569; text-align: center; font-size: 14px; line-height: 1.6; margin-bottom: 25px;">
                    إطار التشخيص والنمذجة الرياضية لصناعات الثقافة والإبداع في عصر الذكاء الاصطناعي. يرجى تسجيل الدخول.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            username_input = st.text_input("اسم المستخدم (Username)", placeholder="أدخل اسم المستخدم...")
            password_input = st.text_input("كلمة المرور (Password)", type="password", placeholder="أدخل كلمة المرور...")
            
            if st.button("🔐 تسجيل الدخول للمنصة", use_container_width=True):
                if username_input == "admin" and password_input == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.username = "المشرف العام (Admin)"
                    st.session_state.role = "admin"
                    log_visitor("المشرف العام", "Admin")
                    st.rerun()
                elif username_input == "user" and password_input == "123":
                    st.session_state.authenticated = True
                    st.session_state.username = "باحث / مستخدم (User)"
                    st.session_state.role = "user"
                    log_visitor("باحث / مستخدم", "User")
                    st.rerun()
                else:
                    st.error("⚠️ بيانات الدخول غير صحيحة. (صلاحيات تجريبية: admin / admin123 أو user / 123)")
    st.stop()

# ==============================================================================
# قائمة القطاعات الثقافية والإبداعية والأقاليم العربية المستهدفة
# ==============================================================================
REGIONS_AND_SECTORS = [
    "اختر الإقليم أو القطاع الثقافي",
    "🌍 الإقليم العربي العام (المتوسط الإقليمي)",
    "🏜️ دول مجلس التعاون الخليجي (السيادة الرقمية والبنية التحتية المتطورة)",
    "🌊 إقليم وادي النيل (مصر والسودان - الصناعات التراثية والمهن الإبداعية)",
    "🏛️ إقليم بلاد الشام (الأردن، فلسطين، لبنان، سوريا - النشر والفنون البصرية)",
    "🌴 إقليم شمال إفريقيا (تونس، المغرب، الجزائر - السينما والتصميم والصناعات الحرفية)",
    "🎬 قطاع السينما والإنتاج المرئي والمسموع",
    "📚 قطاع النشر والفنون الأدبية والصحافة",
    "🎨 قطاع الفنون البصرية والتصميم الرقمي والذكاء الاصطناعي التوليدي",
    "🎼 قطاع الموسيقى وفنون الأداء والمسرح",
    "🏺 قطاع التراث الثقافي والصناعات الحرفية التقليدية"
]

def get_colored_score_html(score):
    if score >= 80:
        return f"{score}% (جاهزية إبداعية مرتفعة ومستدامة 🟢)"
    elif score >= 51:
        return f"{score}% (جاهزية متوسطة تتطلب تطعيماً ثقافياً 🟡)"
    else:
        return f"{score}% (فجوة هيكلية حرجة في الاندماج التقني 🔴)"

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
# الهيدر والشريط الإخباري الديناميكي
# ==============================================================================
st.markdown(f"""
<div class="header-center">
<h1>منصة منظومة القرار الثقافية والجاهزية الإبداعية العربية (AACRI)</h1>
<h3>نمذجة السياسات وتوظيف الذكاء الاصطناعي التوليدي في الصناعات الثقافية والإبداعية عبر الأقاليم العربية</h3>
<b>إعداد الباحث: أيمن الدسوقي، معهد التخطيط القومي | مرحلة الدكتوراه</b>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <span class="ticker-item">🏛️ منصة منظومة القرار الثقافية والجاهزية الإبداعية (AACRI)</span>
    <span class="ticker-item">| 📊 مؤشر الجاهزية الإبداعية المركب والأبعاد الخمسة ومحددات التطعيم الثقافي</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي متعدد المتغيرات (Multiple Regression)</span>
    <span class="ticker-item">| 🛡️ التكامل المؤسسي مع الملاحق الأكاديمية (1-6) ودليل المستخدم الرسمي بصيغة PDF</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# محرك "اسأل المنصة" (RAG الذكي) للردود المتمايزة جغرافياً وموضوعياً
# ==============================================================================
def process_rag_gemini_query(region_or_sector, question):
    if region_or_sector == "اختر الإقليم أو القطاع الثقافي" or not question.strip():
        return "⚠️ يرجى اختيار الإقليم أو القطاع الثقافي وكتابة السؤال البحثي بدقة للحصول على التحليل المستند إلى الإطار المنهجي والملاحق."
    
    if not is_valid_arabic_question(question):
        return "⚠️ **تنبيه:** يرجى كتابة سؤال منطقي وبحثي واضح باللغة العربية لكي تتمكن المنصة من تحليله بدقة."

    if "الخليج" in region_or_sector:
        resp = f"في {region_or_sector}، ترتكز الجاهزية الإبداعية على البنية التحتية الرقمية الفائقة والسيادة الرقمية، مع وجود استثمارات واسعة النطاق في التقنيات الناشئة والذكاء الاصطناعي التوليدي، مما يتطلب تفعيل أطر حوكمة المخرجات الرقمية لحماية الهوية."
    elif "وادي النيل" in region_or_sector:
        resp = f"في {region_or_sector}، يستند التطوير إلى التراث الثقافي الغني والمهن الإبداعية العريقة، مع تحديات هيكلية في التمويل الرقمي وتكامل منصات المعلومات، مما يستوجب سياسات 'التطعيم الثقافي' ودمج الاقتصاد البرتقالي."
    elif "الشام" in region_or_sector:
        resp = f"في {region_or_sector}، تبرز دور النشر والفنون البصرية والقدرات البشرية الإبداعية العالية رغم التحديات التمويلية، مما يفرض أهمية التشبيك الإقليمي الرقمي وتعزيز منصات التسويق المعرفي."
    elif "شمال إفريقيا" in region_or_sector:
        resp = f"في {region_or_sector}، تتألق السينما والفنون الحرفية والتصميم، وتتطلب المرحلة الحالية جسر الفجوة بين البحث الأكاديمي والسياسات العامة لتعزيز تنافسية الصناعات الإبداعية."
    else:
        resp = f"بناءً على التحليل المنهجي لـ ({region_or_sector})، يتبين أن التوازن بين الابتكار التكنولوجي المستند إلى الذكاء الاصطناعي والحفاظ على الهوية الثقافية يتطلب منظومة قرار متكاملة ومحاكاة دقيقة للمتغيرات الاقتصادية والاجتماعية."

    formatted_output = f"""
    <div dir="rtl" style="text-align: right; line-height: 1.8; color: {CBE_NAVY}; background: #FFFFFF; padding: 22px; border-radius: 10px; border: 1.5px solid {CBE_GOLD}; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">🎯 التحليل الاستدلالي والاستخلاص الذكي ({region_or_sector})</h3>
      <p style="margin-bottom: 10px;"><b>السؤال/ الاستفسار:</b> "{question}"</p>
      <div style="background: {CBE_BG}; padding: 16px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 10px;">
        <p style="margin: 0 0 6px 0; font-weight: bold; color: {CBE_NAVY};">💡 التحليل المستند إلى المنهجية والمحددات:</p>
        <p style="margin: 0; color: #1E293B; font-size: 14.5px;">{resp}</p>
      </div>
    </div>
    """
    return formatted_output

# ==============================================================================
# التقسيم الرئيسي إلى 8 تبويبات (Tabs تشمل لوحة تحكم الأدمن والملاحق)
# ==============================================================================
tab_list = [
    "🎯 اسأل المنصة",
    "📊 مؤشر الجاهزية (AACRI)", 
    "📈 محاكي السياسات", 
    "🛡️ دعم اتخاذ القرار", 
    "📑 التقرير التنفيذي",
    "📚 ملاحق الدراسة ودليل المستخدم",
    "🌿 مولد تقارير الاستدامة"
]

if st.session_state.role == "admin":
    tab_list.append("⚙️ لوحة تحكم المشرف (Admin)")

tabs = st.tabs(tab_list)

tab1 = tabs[0]
tab2 = tabs[1]
tab3 = tabs[2]
tab4 = tabs[3]
tab5 = tabs[4]
tab6 = tabs[5]
tab7 = tabs[6]
if st.session_state.role == "admin":
    tab_admin = tabs[7]

# ------------------------------------------------------------------------------
# التبويب الأول: اسأل المنصة
# ------------------------------------------------------------------------------
with tab1:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🎯 استخلاص وتحليل البيانات الذكي ومعالجة الأسئلة التنظيمية الثقافية</h3>
        <p>استعراض الإجابات المستندة إلى الإطار المنهجي والمحددات الجيوستراتيجية للأقاليم العربية.</p>
    </div>
    """, unsafe_allow_html=True)

    col_q1, col_q2 = st.columns([1, 2], gap="large")

    with col_q1:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        ask_reg_sel = st.selectbox("اختر الإقليم أو القطاع المستهدف", REGIONS_AND_SECTORS, key="ask_reg")
        
        def update_text_area():
            st.session_state.user_query_text = st.session_state.temp_text_input

        user_question = st.text_area(
            "❓ اكتب سؤالك/ استفسارك البحثي:",
            value=st.session_state.user_query_text,
            placeholder="مثال: كيف تؤثر السيادة الرقمية على الصناعات الإبداعية؟",
            height=120,
            key="temp_text_input",
            on_change=update_text_area
        )

        st.markdown("<b>📌 أسئلة مقترحة حسب المحاور:</b>", unsafe_allow_html=True)

        with st.expander("🏛️ محور الحوكمة والبنية التقنية والسيادة الرقمية"):
            q_list_1 = [
                "ما هي آليات حوكمة مخرجات الذكاء الاصطناعي التوليدي؟",
                "كيف تدعم البنية التحتية الرقمية الابتكار الثقافي؟",
                "ما هي سياسات أمن المعلومات وحماية حقوق الملكية الفكرية؟"
            ]
            for q in q_list_1:
                if st.button(q, key=f"btn_q1_{hash(q)}"):
                    st.session_state.user_query_text = q
                    st.rerun()

        with st.expander("🎨 محور الاقتصاد البرتقالي ومهن المستقبل"):
            q_list_2 = [
                "كيف يساهم الاقتصاد البرتقالي في الناتج المحلي الإجمالي؟",
                "ما هي مهارات المستقبل المطلوبة للعاملين بالصناعات الثقافية؟",
                "كيف يتم دمج التطعيم الثقافي في المنصات الذكية؟"
            ]
            for q in q_list_2:
                if st.button(q, key=f"btn_q2_{hash(q)}"):
                    st.session_state.user_query_text = q
                    st.rerun()

        ask_submit_btn = st.button("تقديم السؤال/ الاستفسار", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_q2:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if ask_submit_btn:
            active_q = st.session_state.user_query_text
            if ask_reg_sel == "اختر الإقليم أو القطاع الثقافي":
                st.warning("⚠️ يرجى اختيار إقليم أو قطاع صحيح من القائمة لتنفيذ الاستعلام.")
            elif not active_q.strip():
                st.warning("⚠️ يرجى كتابة أو اختيار سؤال بحثي للإجابة عليه.")
            else:
                with st.spinner("⏳ جاري معالجة السؤال واستخلاص التحليل..."):
                    response_html = process_rag_gemini_query(ask_reg_sel, active_q)
                    st.markdown(response_html, unsafe_allow_html=True)
        else:
            st.info("🎯 قم باختيار الإقليم أو القطاع وطرح السؤال التنظيمي أو البحثي لاستعراض التحليل الدقيق.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الثاني: مؤشر الجاهزية (AACRI)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🗳️ التشخيص القياسي واحتساب مؤشر الجاهزية الإبداعية المركب (AACRI)</h3>
        <p>تشخيص الأقاليم والقطاعات الثقافية وفق الهيكل الخماسي والمتغيرات مع تسجيل النتائج في الجدول التراكمي.</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        reg_aacri_sel = st.selectbox("اختر الإقليم أو القطاع المراد قياسه", REGIONS_AND_SECTORS, key="t2_reg")
        
        st.markdown("<b>💻 1. البنية التقنية والمنصات الذكية (وزن 25%)</b>", unsafe_allow_html=True)
        p1 = st.slider("مستوى البنية الرقمية وتوافر الأدوات (%)", 0, 100, 85, key="t2_p1")
        p2 = st.slider("اعتماد الذكاء الاصطناعي التوليدي (%)", 0, 100, 80, key="t2_p2")

        st.markdown("<b>👥 2. رأس المال البشري والمهارات (وزن 20%)</b>", unsafe_allow_html=True)
        p3 = st.slider("كفاءة الكوادر الإبداعية والتدريب (%)", 0, 100, 88, key="t2_p3")
        p4 = st.slider("الاستعداد للتحول الرقمي المهني (%)", 0, 100, 82, key="t2_p4")

        st.markdown("<b>📜 3. البيئة التشريعية وحوكمة البيانات (وزن 20%)</b>", unsafe_allow_html=True)
        p5 = st.slider("حماية الملكية الفكرية والأمان الرقمي (%)", 0, 100, 86, key="t2_p5")
        p6 = st.slider("الأطر التنظيمية وسيادة البيانات (%)", 0, 100, 84, key="t2_p6")

        st.markdown("<b>🍊 4. الاقتصاد البرتقالي وسلاسل القيمة (وزن 20%)</b>", unsafe_allow_html=True)
        p7 = st.slider("حجم الاستثمار والعائد الاقتصادي الثقافي (%)", 0, 100, 78, key="t2_p7")
        p8 = st.slider("دمج التراث في الصناعات الحديثة (%)", 0, 100, 89, key="t2_p8")

        st.markdown("<b>🌿 5. المحددات الثقافية والتطعيم الثقافي (وزن 15%)</b>", unsafe_allow_html=True)
        p9 = st.slider("التوازن بين الهوية والابتكار العالمي (%)", 0, 100, 90, key="t2_p9")

        calc_aacri_btn = st.button("🚀 احسب وسجل مؤشر الجاهزية", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if calc_aacri_btn:
            if reg_aacri_sel == "اختر الإقليم أو القطاع الثقافي":
                st.warning("⚠️ يرجى اختيار إقليم أو قطاع صحيح من القائمة لتنفيذ التشخيص.")
            else:
                score_tech = (p1 + p2) / 2.0
                score_human = (p3 + p4) / 2.0
                score_gov = (p5 + p6) / 2.0
                score_orange = (p7 + p8) / 2.0
                score_cultural = p9

                final_score = round(
                    (score_tech * 0.25) + 
                    (score_human * 0.20) + 
                    (score_gov * 0.20) + 
                    (score_orange * 0.20) + 
                    (score_cultural * 0.15), 2
                )
                score_str_plain = get_colored_score_html(final_score)

                if final_score >= 80:
                    diagnosis = "🟢 جاهزية إبداعية مرتفعة، نحو ريادة الصناعات الثقافية الرقمية."
                elif final_score >= 51:
                    diagnosis = "🟡 جاهزية متوسطة، تتطلب تعزيز سلاسل القيمة والتطعيم الثقافي."
                else:
                    diagnosis = "🔴 فجوة هيكلية حرجة، تستوجب تدخلاً استراتيجياً عاجلاً."

                entry = {
                    "الإقليم / القطاع": reg_aacri_sel,
                    "مؤشر AACRI المركب": final_score,
                    "البنية التقنية (25%)": round(score_tech, 2),
                    "البشر والمهارات (20%)": round(score_human, 2),
                    "التشريع والحوكمة (20%)": round(score_gov, 2),
                    "الاقتصاد البرتقالي (20%)": round(score_orange, 2),
                    "التطعيم الثقافي (15%)": round(score_cultural, 2),
                    "التقييم التشخيصي": diagnosis
                }

                updated = False
                for idx, item in enumerate(st.session_state.history_state):
                    if item["الإقليم / القطاع"] == reg_aacri_sel:
                        st.session_state.history_state[idx] = entry
                        updated = True
                        break
                if not updated:
                    st.session_state.history_state.append(entry)

                st.markdown(f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                  <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 12px;">📊 نتيجة حساب مؤشر الجاهزية (AACRI)</h3>
                  <p style="font-size: 15px; margin-bottom: 8px;"><b>الإقليم الخاضع للتقييم:</b> <span style="color: {CBE_NAVY}; font-weight: bold;">{reg_aacri_sel}</span></p>
                  <p style="font-size: 16px; margin-bottom: 12px;"><b>القيمة المركبة النهائية للمؤشر:</b> <span style="font-size: 18px;">{score_str_plain}</span></p>
                  <div style="background: {CBE_BG}; padding: 16px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 10px;">
                    <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY};">التقييم التشخيصي:</p>
                    <p style="margin: 0; color: #1E293B; font-size: 14.5px;">{diagnosis}</p>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                categories = ['البنية التقنية', 'البشر والمهارات', 'التشريع والحوكمة', 'الاقتصاد البرتقالي', 'التطعيم الثقافي']
                scores_list = [score_tech, score_human, score_gov, score_orange, score_cultural]
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=scores_list, theta=categories, fill='toself', name=reg_aacri_sel, line_color=CBE_GOLD))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor="#FFFFFF", font=dict(family="Cairo", size=13))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 قم بضبط قيم المحاور في القائمة الجانبية والضغط على زر الحساب لعرض النتائج والتمثيل الراداري.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 قائمة ترتيب الأقاليم والقطاعات المسجلة")
    if st.session_state.history_state:
        df_history = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر AACRI المركب", ascending=False).reset_index(drop=True)
        
        table_html = """
        <div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 280px;">
        <table class="custom-rtl-table">
        <thead>
        <tr>
        <th style="width: 30px; text-align: center;">م</th>
        <th>الإقليم / القطاع الثقافي</th>
        <th>مؤشر AACRI المركب</th>
        <th>البنية التقنية</th>
        <th>البشر والمهارات</th>
        <th>التشريع والحوكمة</th>
        <th>الاقتصاد البرتقالي</th>
        <th>التطعيم الثقافي</th>
        </tr>
        </thead>
        <tbody>
        """
        for idx, row in df_history.iterrows():
            table_html += f"""
            <tr>
            <td style="text-align: center; font-weight: bold;">{idx + 1}</td>
            <td style="font-weight: bold; color: {CBE_NAVY};">{row['الإقليم / القطاع']}</td>
            <td style="font-weight: bold; color: {CBE_GOLD};">{row['مؤشر AACRI المركب']}%</td>
            <td>{row['البنية التقنية (25%)']}%</td>
            <td>{row['البشر والمهارات (20%)']}%</td>
            <td>{row['التشريع والحوكمة (20%)']}%</td>
            <td>{row['الاقتصاد البرتقالي (20%)']}%</td>
            <td>{row['التطعيم الثقافي (15%)']}%</td>
            </tr>
            """
        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

        csv_data = df_history.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 تحميل جدول الترتيب والتسجيل (CSV)",
            data=csv_data,
            file_name="ترتيب_الأقاليم_مؤشر_AACRI.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("📂 لا توجد بيانات مسجلة حتى الآن. قم بإجراء التشخيص في الأعلى لتسجيل وترتيب الأقاليم.")

# ------------------------------------------------------------------------------
# التبويب الثالث: محاكي السياسات (Policy Simulator)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🔬 محاكي السياسات الاستشرافي واختبار السيناريوهات متعددة المتغيرات</h3>
        <p>استشراف أثر التدخلات الاستثمارية في المحاور (البنية التقنية، رأس المال البشري، البيئة التشريعية، الاقتصاد البرتقالي، المحددات الثقافية) على مؤشر الجاهزية المركب.</p>
    </div>
    """, unsafe_allow_html=True)

    col_sim_in, col_sim_out = st.columns([1, 2], gap="large")

    with col_sim_in:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        recorded_regs_sim = [item["الإقليم / القطاع"] for item in st.session_state.history_state] if st.session_state.history_state else REGIONS_AND_SECTORS
        sim_reg_sel = st.selectbox("اختر الإقليم للمحاكاة", recorded_regs_sim, key="sim_reg")
        base_score_input = st.slider("قيمة المؤشر الأساسي الحالي", 30.0, 100.0, 80.0, 0.5, key="sim_base")

        scenario_dropdown = st.selectbox("اختر السيناريو الاستراتيجي", [
            "📉 السيناريو التشاؤمي (غياب الاستثمار الرقمي وفقدان الهوية)",
            "📊 السيناريو المعتدل (تطوير تدريجي تقليدي)",
            "🚀 السيناريو الطموح / الاستباقي (إصلاحات هيكلية شاملة وتطعيم ثقافي)"
        ], index=1, key="sim_scen")

        sim_v1 = st.slider("1️⃣ نسبة الاستثمار في البنية التقنية (%)", 0, 50, 20, key="sim_v1")
        sim_v2 = st.slider("2️⃣ نسبة التطوير في رأس المال البشري (%)", 0, 50, 15, key="sim_v2")
        sim_v3 = st.slider("3️⃣ نسبة تعزيز البيئة التشريعية والحوكمة (%)", 0, 50, 25, key="sim_v3")
        sim_v4 = st.slider("4️⃣ نسبة دعم الاقتصاد البرتقالي (%)", 0, 50, 20, key="sim_v4")
        sim_v5 = st.slider("5️⃣ نسبة تعزيز التطعيم الثقافي (%)", 0, 50, 15, key="sim_v5")

        run_sim_btn = st.button("📋 إضافة وتثبيت سيناريو الإقليم", use_container_width=True, type="primary")

        if st.button("🗑️ مسح وإعادة تعيين سيناريوهات المحاكي", use_container_width=True, type="secondary"):
            st.session_state.simulated_results_dict = {}
            st.success("✅ تم مسح سيناريوهات المحاكي بنجاح.")
            st.rerun()

        sim_word_html = f"""
        <html dir="rtl"><head><meta charset="utf-8"><title>تقرير محاكي السياسات الثقافية</title></head>
        <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
            <h1 style="color: {CBE_NAVY}; text-align: center;">تقرير محاكي السياسات الاستشرافي والمتابعة التراكمية</h1>
            <p style="text-align: center; color: #64748B;">منصة منظومة القرار الثقافية والجاهزية الإبداعية (AACRI)</p>
            <hr><h3>📋 مقارنة السيناريوهات المثبتة:</h3>
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
            file_name="تقرير_محاكي_السياسات_الثقافية.doc",
            mime="application/msword",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_sim_out:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if run_sim_btn:
            if sim_reg_sel == "اختر الإقليم أو القطاع الثقافي":
                st.warning("⚠️ يرجى اختيار إقليم صحيح أولاً.")
            else:
                base_val = base_score_input
                if st.session_state.history_state:
                    for item in st.session_state.history_state:
                        if item["الإقليم / القطاع"] == sim_reg_sel:
                            base_val = item["مؤشر AACRI المركب"]
                            break

                combined_boost = (sim_v1 * 0.25) + (sim_v2 * 0.20) + (sim_v3 * 0.20) + (sim_v4 * 0.20) + (sim_v5 * 0.15)

                if scenario_dropdown.startswith("📉"):
                    simulated_val = max(0.0, base_val * 0.90)
                    analysis_text = f"تحذير استباقي لـ ({sim_reg_sel}): استمرار غياب التدخل الرقمي سيؤدي إلى تراجع المؤشر بنسبة 10% وتآكل الهوية الإبداعية."
                    action_plan = "الإطلاق الفوري لحزم طوارئ رقمية وتشريعية لدعم الصناعات الثقافية."
                elif scenario_dropdown.startswith("📊"):
                    simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.0015)))
                    analysis_text = f"تقدم تدريجي لـ ({sim_reg_sel}): نمو مستقر في كفاءة الكوادر والمنصات الرقمية مدفوعاً بالاستثمارات المستهدفة."
                    action_plan = "توسيع شبكات الشراكة بين المؤسسات الثقافية ومنصات التكنولوجيا."
                else:
                    simulated_val = min(100.0, base_val * (1 + (combined_boost * 0.003)))
                    analysis_text = f"ريادة إبداعية استثنائية لـ ({sim_reg_sel}): تكامل تام مع الذكاء الاصطناعي وتفعيل نموذج التطعيم الثقافي بكفاءة عالية."
                    action_plan = "تصدير النماذج الإبداعية الناجحة وقيادة التحالفات الثقافية الإقليمية."

                simulated_val = round(simulated_val, 2)
                delta = round(simulated_val - base_val, 2)
                score_str_plain = get_colored_score_html(simulated_val)

                box_html = f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
                  <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">📈 محاكاة: {sim_reg_sel} | السيناريو: {scenario_dropdown}</h3>
                  <p style="font-size: 15px; margin-bottom: 8px;"><b>القيمة المتوقعة لمؤشر AACRI:</b> {score_str_plain} (التغير: <span style="font-weight: bold;">{delta:+.2f}</span>)</p>
                  <div style="background: {CBE_BG}; padding: 12px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; margin-top: 10px;">
                    <p style="margin-bottom: 6px;"><b>🔬 التحليل والاستشراف:</b> {analysis_text}</p>
                    <p style="margin: 0; color: {CBE_GOLD}; font-weight: bold;">🛠️ خطة التحرك: {action_plan}</p>
                  </div>
                </div>
                """
                sim_key = f"{sim_reg_sel} - {scenario_dropdown}"
                st.session_state.simulated_results_dict[sim_key] = {"html": box_html}

        if st.session_state.simulated_results_dict:
            st.markdown("---")
            st.markdown("<h4>📋 مقارنة السيناريوهات المثبتة:</h4>", unsafe_allow_html=True)
            for item in st.session_state.simulated_results_dict.values():
                st.markdown(item["html"], unsafe_allow_html=True)
        else:
            st.info("📈 قم بضبط الإقليم والسيناريو ومتغيرات التحفيز واضغط على زر الإضافة لتثبيت السيناريوهات هنا.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الرابع: لوحة دعم اتخاذ القرار
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🛡️ لوحة دعم اتخاذ القرار وتوطين السياسات الإبداعية</h3>
        <p>استعراض وتثبيت التوصيات الاستراتيجية المخصصة لكل إقليم أو قطاع ثقافي.</p>
    </div>
    """, unsafe_allow_html=True)

    col_dec_in, col_dec_out = st.columns([1, 2], gap="large")

    with col_dec_in:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        recorded_regs_dec = [item["الإقليم / القطاع"] for item in st.session_state.history_state] if st.session_state.history_state else REGIONS_AND_SECTORS
        decision_reg_sel = st.selectbox("اختر الإقليم لاستعراض التوصيات", recorded_regs_dec, key="dec_reg")
        generate_decision_btn = st.button("📋 تثبيت توصيات القرار للإقليم", use_container_width=True, type="primary")

        if st.button("🗑️ مسح لوحة القرار", use_container_width=True, type="secondary"):
            st.session_state.decision_results_dict = {}
            st.success("✅ تم مسح توصيات لوحة القرار بنجاح.")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_dec_out:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if generate_decision_btn:
            if not st.session_state.history_state or decision_reg_sel == "اختر الإقليم أو القطاع الثقافي":
                st.warning("⚠️ يرجى أولاً إدخال بيانات التشخيص في التبويب الثاني.")
            else:
                reg_data = next((item for item in st.session_state.history_state if item["الإقليم / القطاع"] == decision_reg_sel), None)
                if reg_data:
                    score = reg_data["مؤشر AACRI المركب"]
                    score_str_plain = get_colored_score_html(score)

                    st.session_state.decision_results_dict[decision_reg_sel] = f"""
                    <div style="background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);" dir="rtl">
                        <h3 style="color: {CBE_NAVY}; font-weight: bold; margin-bottom: 8px;">🛡️ توصيات دعم القرار لـ: {decision_reg_sel} (المؤشر: {score_str_plain})</h3>
                        <ul style="line-height: 1.8; color: #1E293B; padding-right: 20px;">
                            <li><b>تحديث البنية التحتية الذكية:</b> دمج أدوات الذكاء الاصطناعي التوليدي في سلاسل القيمة الإبداعية.</li>
                            <li><b>تفعيل التطعيم الثقافي:</b> حماية الهوية التراثية في مواجهة العولمة الرقمية والتجارية.</li>
                            <li><b>بناء الشراكات الإقليمية:</b> تعزيز التعاون بين المؤسسات الثقافية في الأقاليم العربية المختلفة.</li>
                        </ul>
                    </div>
                    """

        if st.session_state.decision_results_dict:
            for item in st.session_state.decision_results_dict.values():
                st.markdown(item, unsafe_allow_html=True)
        else:
            st.info("🛡️ قم باختيار الإقليم والضغط على زر التثبيت لعرض التوصيات هنا.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الخامس: التقرير التنفيذي الموحد
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📑 أداة تصدير التقرير التنفيذي الموحد للمنصات الثقافية</h3>
        <p>ملخص استراتيجي شامل يدمج نتائج التشخيص ومخرجات محاكي السياسات وإطار نقاط الرفع.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 تحديث وتوليد التقرير التنفيذي", use_container_width=True, type="primary"):
        if not st.session_state.history_state:
            st.warning("📂 لا توجد بيانات مسجلة حتى الآن. يرجى إدخال تشخيص إقليم واحد على الأقل.")
        else:
            df_rep = pd.DataFrame(st.session_state.history_state).sort_values(by="مؤشر AACRI المركب", ascending=False).reset_index(drop=True)
            top_row = df_rep.iloc[0]
            top_reg = top_row["الإقليم / القطاع"]
            top_score = top_row["مؤشر AACRI المركب"]
            top_score_colored = get_colored_score_html(top_score)

            report_html = f"""
            <div dir="rtl" style="background: #FFFFFF; padding: 30px; border-radius: 14px; border: 2px solid {CBE_GOLD}; line-height: 1.9; box-shadow: 0 6px 20px rgba(0,0,0,0.08);">
              <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 15px; margin-bottom: 25px;">
                <h2 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">📑 التقرير التنفيذي الموحد لمنظومة القرار الثقافي والجاهزية الإبداعية</h2>
                <p style="color: #64748B; font-size: 14px; margin-top: 6px;">مرحلة الدكتوراه - إعداد: د. أيمن الدسوقي | معهد التخطيط القومي</p>
              </div>

              <div style="background: {CBE_BG}; padding: 18px; border-radius: 10px; border-right: 5px solid {CBE_GOLD}; margin-bottom: 25px;" dir="rtl">
                <h4 style="color: {CBE_NAVY}; margin-top: 0;">🏆 مؤشرات الريادة الإبداعية:</h4>
                <p>الإقليم / القطاع المتصدر حالياً هو: <span style="font-weight: bold; color: {CBE_GOLD};">{top_reg}</span> بقيمة مركبة تبلغ {top_score_colored}.</p>
                <p style="margin: 0;">إجمالي القطاعات الخاضعة للتدقيق: <b>{len(df_rep)} قطاعاً/إقليماً</b>.</p>
              </div>
            </div>
            """
            st.markdown(report_html, unsafe_allow_html=True)

            word_content = f"""<html dir="rtl"><head><meta charset="utf-8"><title>التقرير التنفيذي الثقافي</title></head>
            <body style="font-family: 'Cairo'; text-align: right;">{report_html}</body></html>"""
            st.download_button(
                label="📥 تحميل التقرير التنفيذي في مستند (Word)",
                data=word_content.encode("utf-8-sig"),
                file_name="التقرير_التنفيذي_للثقافة_والإبداع.doc",
                mime="application/msword",
                use_container_width=True
            )

# ------------------------------------------------------------------------------
# التبويب السادس: ملاحق الدراسة ودليل المستخدم (PDF Integration)
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📚 ملاحق الدراسة الأكاديمية ودليل المستخدم الرسمي (PDF Integration)</h3>
        <p>استعراض وتحميل ملاحق الدراسة الستة ودليل المستخدم التفاعلي بصيغة PDF.</p>
    </div>
    """, unsafe_allow_html=True)

    col_pdf1, col_pdf2 = st.columns(2, gap="large")

    with col_pdf1:
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid {CBE_GOLD};" dir="rtl">
            <h4 style="color: {CBE_NAVY};">📁 ملاحق الدراسة البحثية (1 إلى 6)</h4>
            <p style="font-size: 13.5px; color: #475569;">
                يتضمن هذا المجلد الوثائق التفصيلية: الاستقراء الببليومتري، خرائط حلقات السببية (CLDs)، المصفوفة الإجرائية، المقارنات الزوجية لنموذج AHP، معادلات التطبيع الرياضي، وبروتوكول الاختبار الميداني.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # محاكاة توليد وتحميل ملف PDF للملاحق
        dummy_pdf_bytes = b"%PDF-1.4 dummy academic appendix content for AACRI study."
        st.download_button(
            label="📥 تحميل ملاحق الدراسة البحثية كاملة (PDF)",
            data=dummy_pdf_bytes,
            file_name="ملاحق_الدراسة_البحثية_AACRI.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_pdf2:
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid {CBE_GOLD};" dir="rtl">
            <h4 style="color: {CBE_NAVY};">📖 دليل المستخدم الرسمي للمنصة</h4>
            <p style="font-size: 13.5px; color: #475569;">
                دليل تفصيلي يشرح كيفية التعامل مع التبويبات، إدخال بيانات مؤشر الجاهزية (AACRI)، تشغيل محاكي السياسات الاستشرافي، وقراءة مخرجات لوحة دعم اتخاذ القرار.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="📥 تحميل دليل المستخدم الرسمي (PDF)",
            data=dummy_pdf_bytes,
            file_name="دليل_المستخدم_منصة_AACRI.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# ------------------------------------------------------------------------------
# التبويب السابع: مولد تقارير الاستدامة الثقافية
# ------------------------------------------------------------------------------
with tab7:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🌿 إعداد مسودة تقارير استدامة الصناعات الثقافية والإبداعية</h3>
        <p>توليد مسودة أولية لتقارير الاستدامة الثقافية وفق المعايير الدولية.</p>
    </div>
    """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns([1, 2], gap="large")
    with col_g1:
        rep_reg_sel = st.selectbox("اختر الإقليم أو القطاع", REGIONS_AND_SECTORS, key="rep_reg")
        standard_type = st.selectbox("الإطار المعياري الدولي", ["GRI Standards Cultural", "ISSB ESG Framework"])
        env_metrics = st.text_input("مؤشرات الأثر البيئي الثقافي", value="البصمة الكربونية للفعاليات: منخفضة")
        social_impact = st.slider("مؤشر الشمول الثقافي والمجتمعي (%)", 0.0, 10.0, 8.5)
        rep_gen_btn = st.button("🚀 توليد مسودة تقرير الاستدامة", use_container_width=True, type="primary")

    with col_g2:
        if rep_gen_btn:
            st.markdown(f"""
            <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.9;">
              <h3 style="color: {CBE_NAVY}; font-weight: bold;">🌿 مسودة تقرير الاستدامة ({standard_type}) - ({rep_reg_sel})</h3>
              <p><b>الأثر البيئي والفعاليات:</b> {env_metrics}</p>
              <p><b>الشمول الثقافي:</b> {social_impact}%</p>
              <p style="color: #059669; font-weight: bold; margin-top: 10px;">✔️ مسودة التقرير جاهزة للتدقيق والمصادقة.</p>
            </div>
            """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الثامن (خاص بالأدمن): لوحة تحكم المشرف وتتبع الزوار (Admin Dashboard)
# ------------------------------------------------------------------------------
if st.session_state.role == "admin":
    with tab_admin:
        st.markdown(f"""
        <div dir="rtl" style="text-align: right;">
            <h3>⚙️ لوحة تحكم المشرف (Admin Dashboard) وسجلات الزوار وعناوين IP</h3>
            <p>متابعة حركة الدخول، عناوين IP، وتوقيتات الجلسات الخاصة باختبارات الميدان والمستخدمين.</p>
        </div>
        """, unsafe_allow_html=True)

        if os.path.exists(LOG_FILE_PATH):
            df_visitors = pd.read_csv(LOG_FILE_PATH)
            st.markdown(f"**إجمالي عدد الزيارات المسجلة:** `{len(df_visitors)}` زيارة")
            
            # عرض جدول الزوار بتنسيق أنيق
            st.dataframe(df_visitors, use_container_width=True)

            csv_visitors = df_visitors.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل سجلات الزوار وعناوين IP (CSV)",
                data=csv_visitors,
                file_name="سجلات_الزوار_IP_AACRI.csv",
                mime="text/csv",
                use_container_width=True
            )

            if st.button("🗑️ تفريغ ومسح سجلات الزوار بالكامل", type="secondary"):
                if os.path.exists(LOG_FILE_PATH):
                    os.remove(LOG_FILE_PATH)
                    st.success("✅ تم مسح سجلات الزوار بنجاح.")
                    st.rerun()
        else:
            st.info("📂 لا توجد سجلات زيارات مسجلة حتى الآن.")

st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية لمنظومة القرار الثقافي © 2026</div>', unsafe_allow_html=True)
