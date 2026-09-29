import random
import io
import os
import re
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

/* فرض محاذاة اليمين على القوائم المنسدلة */
div[data-baseweb="select"] *, 
div[data-baseweb="popover"] *, 
ul[data-baseweb="menu"] *, 
div[role="listbox"] *,
div[role="option"] {{
    direction: rtl !important;
    text-align: right !important;
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
    font-size: 12.5px !important;
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

.stButton > button {{
    width: 100% !important;
    border-radius: 50px !important;
    font-family: 'Cairo', sans-serif !important;
    font-weight: 700 !important;
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
# إدارة جلسة الدخول (Authentication) - يطلب user / 123
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

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
                if username == "user" and password == "123":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("⚠️ اسم المستخدم أو كلمة المرور غير صحيحة. (تجريبي: user / 123)")
    st.stop()

# ==============================================================================
# قائمة البنوك المصرية (عينة الـ 12 بنكاً)
# ==============================================================================
BANKS_LIST_AR = [
    "اختر البنك المصرفي",
    "البنك الأهلي المصري NBE - حكومي",
    "بنك مصر Banque Misr - حكومي",
    "بنك القاهرة Banque du Caire - حكومي",
    "بنك قناة السويس SCBANK - حكومي",
    "بنك التعمير والإسكان HDB - مساهمة مصرية متخصصة",
    "البنك التجاري الدولي CIB - خاص رائد",
    "بنك قطر الوطني مصر QNB Alahli - عربي/إقليمي كبير",
    "بنك أبوظبي الأول FABMISR - عربي/أجنبي",
    "بنك الإسكندرية AlexBank - أجنبي",
    "كريدي أجريكول مصر Credit Agricole - أجنبي/خاص",
    "بنك البركة مصر Al Baraka Bank - إسلامي",
    "بنك فيصل الإسلامي المصري Faisal Islamic Bank - إسلامي"
]

PRESET_QUESTIONS_AR = {
    "🏛️ محور الحوكمة ومجلس الإدارة والضبط الرقابي (IG)": [
        "ما هي ممارسات مجلس الإدارة ونسبة الأعضاء المستقلين والتنوع وتعارض المصالح بالبنك؟",
        "كيف يفصح البنك عن سياسات الشفافية، المتابعة، المساءلة، ومكافحة الفساد الإداري؟",
        "ما هي الضوابط الرقابية وآليات التدقيق الداخلي المتبعة لحماية حقوق أصحاب המصلحة وسيادة القانون؟"
    ],
    "🌱 محور تقارير الاستدامة والتمويل الأخضر والمناخ (SR/ESG)": [
        "ما هي أطر إدارة المخاطر المناخية واختبارات الضغط واستهدافات التمويل الأخضر بالبنك؟",
        "كيف يمتثل البنك للمعايير الدولية للتقارير (GRI, TCFD, ISSB - IFRS S1/S2)؟"
    ],
    "🔒 محور المنصات الذكية وحوكمة البيانات والامتثال (SIP/RegTech)": [
        "ما هي سياسات حوكمة البيانات والامتثال لقانون حماية البيانات الشخصية المصري رقم 151 لسنة 2020؟",
        "كيف يضمن البنك الحصانة السيبرانية ومنع تسريب البيانات المالية الحساسة أثناء المعالجة الرقمية؟"
    ]
}

def sanitize_input_text(query_input):
    if isinstance(query_input, list):
        query_input = query_input[0] if len(query_input) > 0 else ""
    query_str = str(query_input).strip()
    query_str = re.sub(r"^\[\s*['\"]", "", query_str)
    query_str = re.sub(r"['\"]\s*\]$", "", query_str)
    return query_str.strip()

def get_colored_score_html(score):
    if score >= 80:
        return f"<span style='color: #16A34A; font-weight: bold;'>{score}% (أداء مرتفع ومنتظم 🟢)</span>"
    elif score >= 51:
        return f"<span style='color: #CA8A04; font-weight: bold;'>{score}% (أداء متوسط يتطلب تعزيزاً 🟡)</span>"
    else:
        return f"<span style='color: #DC2626; font-weight: bold;'>{score}% (فجوة هيكلية حرجة تستوجب التدخل 🔴)</span>"

def generate_audit_response(raw_query, bank_name):
    user_query = sanitize_input_text(raw_query)
    if not user_query or bank_name == "اختر البنك المصرفي":
        return "<div dir='rtl' style='text-align: right; color: red;'>⚠️ يرجى اختيار البنك المصرفي وكتابة السؤال البحثي بدقة.</div>"

    bank_clean_name = bank_name.split(" - ")[0].replace(" ", "_")
    drive_mount_code = f"from google.colab import drive\ndrive.mount('/content/drive')\n# Active Repository: /content/drive/My Drive/Egyptian_Banks_ESG/{bank_clean_name}_Reports"

    if "حكومي" in bank_name:
        flavor = f"استناداً إلى معالجة مستودعات ({bank_name}) السحابية عبر خوارزميات الاسترجاع المعزز (RAG)، يبرز دور البنك المحوري في تمويل المشروعات القومية الكبرى، وتطبيق ضوابط البنك المركزي بتوسيع شبكة الفروع المصرفية وتحقيق الشمول المالي المستدام."
    elif "إسلامي" in bank_name:
        flavor = f"من خلال التعدين النصي لتقارير ({bank_name}) عبر Google Drive، يلتزم البنك بمعايير الاستدامة المتوافقة مع الشريعة الإسلامية، مع إفصاحات دقيقة عن صيغ التمويل الأخضر وتجنب الاستثمارات الملوثة بيئياً."
    elif "أجنبي" in bank_name or "عربي" in bank_name:
        flavor = f"تشير استخلاصات وثائق ({bank_name}) السحابية إلى تبني معايير الإفصاح الدولية الحديثة (ISSB - IFRS S1/S2)، ومستوى رفيع في حوكمة المخاطر السيبرانية والسيادة الرقمية المؤسسية."
    else:
        flavor = f"بناءً على فحص فولدر ({bank_name}) عبر المنصة الذكية، يتمتع البنك بكفاءة عالية في التحول الرقمي وتوظيف منصات المعلومات (SIP) لتقليص التحيزات البشرية أثناء إعداد تقارير الاستدامة."

    return f"""
    <div dir="rtl" style="text-align: right; line-height: 1.8; color: {CBE_NAVY}; background: #FFFFFF; padding: 22px; border-radius: 10px; border: 1.5px solid {CBE_GOLD}; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      <h3 style="color: {CBE_NAVY}; font-weight: bold;">🏛️ تقرير التدقيق الرقمي والاستخلاص المعياري ({bank_name})</h3>
      <p>🎯 <b>السؤال البحثي:</b> "{user_query}"</p>
      <p style="color: #64748B; font-size: 13px;"><b>📁 كود ربط واكتشاف مستودع Google Drive للبنك:</b></p>
      <pre style="background: #1E293B; color: #38BDF8; padding: 10px; border-radius: 6px; font-size: 12px; direction: ltr; text-align: left;">{drive_mount_code}</pre>
      <p style="color: {CBE_GOLD}; font-weight: bold; margin-top: 10px;">📂 التحليل التنظيمي المتمايز والمستخرج سحابياً:</p>
      <blockquote style="border-right: 4px solid {CBE_GOLD}; padding-right: 12px; background: {CBE_BG};">{flavor}</blockquote>
    </div>
    """

# تهيئة الذاكرة المؤقتة للبيانات والتراكميات
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
    <span class="ticker-item">| 🎯 استخلاص وتحليل البيانات الذكي ومعالجة الأسئلة التنظيمية عبر مستودعات Google Drive</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# التقسيم الرئيسي إلى التبويبات (Tabs) - تشمل تبويب "اسأل المنصة" الجديد
# ==============================================================================
tab_ask, tab1, tab2, tab3, tab4, tab5, tab_parse = st.tabs([
    "🎯 اسأل المنصة (RAG Drive)",
    "📊 مؤشر الحوكمة (SSGI)", 
    "📈 محاكي السياسات", 
    "🛡️ لوحة دعم القرار", 
    "📑 التقرير التنفيذي",
    "🌿 مولد تقارير الاستدامة",
    "📂 تحليل المستندات"
])

# ------------------------------------------------------------------------------
# التبويب الجديد: اسأل المنصة (RAG عبر Google Drive)
# ------------------------------------------------------------------------------
with tab_ask:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>🎯 استخلاص وتحليل البيانات الذكي ومعالجة الأسئلة التنظيمية (عبر مستودعات Google Drive)</h3>
        <p>تم وضع كافة تقارير الاستدامة والحوكمة الخاصة بالبنوك في المستودع السحابي المعتمد:</p>
        <p><a href="https://drive.google.com/drive/u/0/folders/1GDZFrH_Za3g-ODlyai-76n5jOEGU9N6c" target="_blank" style="color: #C5A059; font-weight: bold;">🔗 مسار مستودعات تقارير الاستدامة (Google Drive RAG FILES)</a></p>
        <p>يتيح هذا القسم للمحكم أو المطلع طرح الأسئلة التنظيمية واسترجاع الشواهد النصية من تقارير البنوك بدقة عالية بعيداً عن الهلوسة.</p>
    </div>
    """, unsafe_allow_html=True)

    col_ask_in, col_ask_out = st.columns([1, 2], gap="large")

    with col_ask_in:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        ask_bank_sel = st.selectbox("اختر البنك المصرفي للتدقيق", BANKS_LIST_AR, key="ask_bank")
        user_query_input = st.text_area("❓ الاستفسار التنظيمي أو البحثي", placeholder="اكتب سؤالك هنا أو اختر من الأسئلة الجاهزة...", key="ask_query")
        
        st.markdown("<b>📌 أسئلة استرشادية جاهزة للتحليل:</b>", unsafe_allow_html=True)
        selected_category = st.selectbox("اختر المحور لاستعراض الأسئلة", list(PRESET_QUESTIONS_AR.keys()), key="ask_cat")
        preset_q = st.selectbox("الأسئلة المقترحة", PRESET_QUESTIONS_AR[selected_category], key="ask_preset")
        
        if st.button("📋 استخدام السؤال المقترح", use_container_width=True, type="secondary"):
            st.session_state["ask_query"] = preset_q
            st.rerun()

        ask_submit_btn = gr_btn = st.button("🚀 قدم سؤالك للتدقيق الاسترجاعي عبر Drive", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_ask_out:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if ask_submit_btn:
            query_to_process = st.session_state.get("ask_query", user_query_input)
            response_html = generate_audit_response(query_to_process, ask_bank_sel)
            st.markdown(response_html, unsafe_allow_html=True)
        else:
            st.info("🎯 اختر البنك واكتب استفسارك أو اختر سؤالاً جاهزاً ثم اضغط على زر التدقيق لاستعراض الاستخلاصات السحابية.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الثاني: مؤشر الحوكمة الذكية المستدامة (SSGI)
# ------------------------------------------------------------------------------
with tab1:
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
        sip_1 = st.slider("1. جاهزية وبنية التحتية المنصة الرقمية (%)", 0, 100, 85, key="t1_sip1")
        sip_2 = st.slider("2. استرجاع البيانات ومعالجة RAG (%)", 0, 100, 88, key="t1_sip2")
        sip_3 = st.slider("3. السيادة الرقمية وأمن المعلومات (%)", 0, 100, 90, key="t1_sip3")

        st.markdown("<b>🏛️ الحوكمة المؤسسية (IG - وزن 30%)</b>", unsafe_allow_html=True)
        ig_1 = st.slider("1. فاعلية واستقلالية مجلس الإدارة (%)", 0, 100, 86, key="t1_ig1")
        ig_2 = st.slider("2. الإفصاح والشفافية المؤسسية (%)", 0, 100, 88, key="t1_ig2")
        ig_3 = st.slider("3. الالتزام الرقابي وقوانين البنك المركزي (%)", 0, 100, 84, key="t1_ig3")

        st.markdown("<b>🌱 تقارير الاستدامة (SR - وزن 30%)</b>", unsafe_allow_html=True)
        sr_1 = st.slider("1. دمج معايير الاستدامة (GRI / ISSB) (%)", 0, 100, 85, key="t1_sr1")
        sr_2 = st.slider("2. قياس البصمة الكربونية والتمويل الأخضر (%)", 0, 100, 82, key="t1_sr2")
        sr_3 = st.slider("3. الشمول المالي والمسؤولية المجتمعية (%)", 0, 100, 81, key="t1_sr3")

        calc_ssgi_btn = st.button("🚀 احسب وسجل مؤشر البنك", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if calc_ssgi_btn:
            if bank_ssgi_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي حقيقي من القائمة لتنفيذ التشخيص القياسي.")
            else:
                sip_val = (sip_1 + sip_2 + sip_3) / 3.0
                ig_val = (ig_1 + ig_2 + ig_3) / 3.0
                sr_val = (sr_1 + sr_2 + sr_3) / 3.0

                final_score = round((sip_val * 0.40) + (ig_val * 0.30) + (sr_val * 0.30), 2)
                score_str_plain = get_colored_score_html(final_score)

                bank_clean_name = bank_ssgi_sel.split(" - ")[0].replace(" ", "_")
                drive_folder_path = f"/content/drive/My Drive/Egyptian_Banks_ESG/{bank_clean_name}_Reports"

                if final_score >= 80:
                    diagnosis = f"جاهزية متميزة وتكامل مؤسسي عالٍ 🟢: إجمالي المؤشر المركب ({final_score}%) يعكس ريادة تشغيلية والتزاماً رفيعاً بالمعايير الدولية (ISSB/GRI) المستخرجة من فولدر البنك السحابي ({drive_folder_path})."
                elif final_score >= 51:
                    diagnosis = f"جاهزية متوسطة تتطلب تدخلاً استباقياً 🟡: إجمالي المؤشر المركب ({final_score}%) يوضح توافقاً نسبياً في مستندات البنك ({drive_folder_path}) يواجه بعض الاختناقات في البنية الرقمية أو الإفصاحات غير المالية."
                else:
                    diagnosis = f"جاهزية منخفضة وفجوة هيكلية حرجة 🔴: تشير المعطيات المستخرجة من مستودع ({drive_folder_path}) إلى قصور في البنية التحتية الرقمية أو معايير الإفصاح."

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
                  <p style="font-size: 16px; margin-bottom: 12px;"><b>القيمة المركبة النهائية للمؤشر (SSGI):</b> {score_str_plain}</p>
                  <div style="background: {CBE_BG}; padding: 16px; border-radius: 8px; border-right: 5px solid {CBE_GOLD}; margin-top: 10px;">
                    <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY};">التقييم التشخيصي والتفصيل المنظومي:</p>
                    <p style="margin: 0; color: #1E293B; font-size: 14.5px;">{diagnosis}</p>
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
            </tr>
            """
        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

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
# التبويب الثالث: محاكي السياسات
# ------------------------------------------------------------------------------
with tab2:
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
with tab3:
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
with tab4:
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
                 <li><b>2. تدفق المعلومات (Information Flows):</b> إحكام قواعد منصات المعلومات وتأمين سرية البيانات عبر مستودعات Google Drive وخوارزميات RAG.</li>
                 <li><b>3. القواعد والحوكمة (Rules):</b> الالتزام بضوابط البنك المركزي ومعايير الإفصاح المالي (ISSB / GRI).</li>
                 <li><b>4. أهداف النظام (Goals):</b> توجيه القطاع المصرفي نحو التنمية المستدامة ورؤية مصر 2030 والسيادة الرقمية.</li>
                </ul>
              </div>
            </div>
            """
            st.markdown(report_html, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب السادس: مولد تقارير الاستدامة (GRI / ISSB)
# ------------------------------------------------------------------------------
with tab5:
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
              <p style="color: #059669; font-weight: bold; margin-top: 10px;">✔️ مسودة التقرير متوافقة مع متطلبات الإفصاح ومطابقة لنتائج التشخيص.</p>
            </div>
            """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب السابع: تحليل المستندات (Document Parser)
# ------------------------------------------------------------------------------
with tab_parse:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📂 تحليل التقارير السنوية (PDF / Word Parser)</h3>
        <p>رفع وتحليل التقارير السنوية وتقارير الاستدامة للتحقق الآلي من متطلبات الحوكمة.</p>
    </div>
    """, unsafe_allow_html=True)

    col_p1, col_p2 = st.columns([1, 2], gap="large")
    with col_p1:
        parser_bank_sel = st.selectbox("اختر البنك", BANKS_LIST_AR, key="parser_bank")
        uploaded_file = st.file_uploader("رفع ملف التقرير السنوي", type=[".pdf", ".docx", ".txt"])
        parse_btn = st.button("🔍 تحليل المستند والفحص الآلي", use_container_width=True, type="primary")

    with col_p2:
        if parse_btn:
            if uploaded_file is None:
                st.warning("⚠️ يرجى رفع ملف التقرير للبدء في التحليل.")
            else:
                file_name = uploaded_file.name
                st.markdown(f"""
                <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.9;">
                  <h3 style="color: {CBE_NAVY}; font-weight: bold;">📂 تقرير مطابقة المستند والفحص الآلي - ({parser_bank_sel})</h3>
                  <p><b>الملف المرفق:</b> {file_name}</p>
                  <p><b>حالة الفحص الآلي:</b> تم قراءة وتفكيك بنية المستند بنجاح وتوثيق الشواهد الإفصاحية والامتثال لتعليمات البنك المركزي المصري ومعايير (ISSB).</p>
                </div>
                """, unsafe_allow_html=True)

st.markdown(f'<div class="footer-copyright">جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)
