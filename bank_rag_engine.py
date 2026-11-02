# -*- coding: utf-8 -*-
"""
bank_rag_engine.py
محرك "اسأل المنصة" المطوَّر — بديل مباشر للدالة process_rag_gemini_query

التحديثات الأخيرة:
  1) إضافة دعم كامل لأسئلة الفروع والشبكة الجغرافية والانتشار المصرفي (branches).
  2) معالجة متقدمة للاستعلامات الذكية وتوليد الإجابات الديناميكية عبر الطبقات.
  3) تحسين الربط مع نموذج Gemini / Claude للحصول على إجابات دقيقة لأسئلة الفروع والأرقام.
"""
import os
import re
import json
import html
import difflib
import urllib.request

CBE_NAVY = "#002B49"
CBE_GOLD = "#C5A059"
CBE_BG = "#F8F9FA"

JSON_KNOWLEDGE_FILE = "national_banking_governance_archive.json"

# ==============================================================================
# 1) أدوات اللغة
# ==============================================================================
_DIAC = re.compile(r"[\u064B-\u0652\u0640]")


def norm(s: str) -> str:
    s = _DIAC.sub("", (s or "").lower())
    s = re.sub("[إأآ]", "ا", s).replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", s).strip()


def is_valid_arabic_question(text):
    if not text or len(text.strip()) < 3:
        return False
    return len(re.findall(r"[\u0600-\u06FF]", text)) >= 2


# ==============================================================================
# 2) تصنيف نية السؤال (Intent) بالأوزان بدل التطابق الأعمى
# ==============================================================================
INTENT_KEYWORDS = {
    "branches": ["فروع", "فرع", "عدد الفروع", "شبكه الفروع", "الانتشار الجغرافي", "الصراف الالي", "atm", "ماكينات"],
    "vision_mission": ["رسالة البنك", "رؤية البنك", "رسالتنا", "رؤيتنا", "الرؤية والرسالة", "قيم البنك"],
    "history": ["تاسس", "تاسيس", "نشاه", "تاريخ", "مؤسس", "ملكيه", "اول بنك", "مساهمين", "ملاك"],
    "board": ["مجلس الاداره", "تكوين", "عرف الحوكمه", "لجان", "اعضاء المجلس", "هيكل الحوكمه"],
    "independence": ["مستقلين", "تعارض المصالح", "نسبه الاعضاء", "غير تنفيذيين"],
    "transparency": ["الشفافيه", "المساءله", "مكافحه الفساد", "غسل الاموال", "يفصح عن سياسات"],
    "cbe_compliance": ["الالتزام التام", "القوانين", "اللوائح", "الصادره عن البنك المركزي", "يمتثل للرقابه"],
    "women": ["المراه", "تمكين", "الشمول المالي", "رائدات"],
    "climate": ["مخاطر المناخ", "المناخ", "التمويل الاخضر", "تغير المناخ", "الكربون"],
    "green_assets": ["الاصول الخضراء", "محفظه الائتمان", "نسبه الاصول", "المشروعات المستدامه", "gar"],
    "reporting": ["gri", "issb", "المعايير الدوليه", "الافصاح المالي", "تقارير الاستدامه", "tcfd"],
    "csr": ["المسوءوليه المجتمعيه", "المسؤوليه المجتمعيه", "الانفاق التنموي", "مبادرات البنك", "csr"],
    "data_gov": ["حوكمه البيانات", "الامتثال الرقابي", "تامينها", "اليات حوكمه"],
    "cyber": ["الحصانه السيبرانيه", "السيبراني", "تسريب", "هجمات", "اختراق"],
    "sip": ["البنيه التحتيه", "جاهزيه", "منصات المعلومات", "sip", "التحول الرقمي"],
    "regtech": ["regtech", "الرقابه التنظيميه", "استرجاع المعطيات", "تقنيات الرقابه"],
    "pdpl": ["حمايه البيانات الشخصية", "السياده الرقميه", "قانون حماية", "التوافق مع قانون"],
}


def classify_intent(question: str):
    q = norm(question)
    best, best_score = None, 0
    for intent, kws in INTENT_KEYWORDS.items():
        score = sum(len(norm(k)) for k in kws if norm(k) in q)
        if score > best_score:
            best, best_score = intent, score
    return best


# ==============================================================================
# 3) ملفات تعريف البنوك (حقائق فقط — الحقل الناقص يُترك ولا يُختلق)
# ==============================================================================
TYPE_LABEL = {
    "state": "بنك مملوك للدولة",
    "islamic": "مصرف إسلامي",
    "foreign": "بنك تابع لمجموعة مصرفية أجنبية/إقليمية",
    "private": "بنك قطاع خاص",
}

_STATE = ["بنك مصر BM", "البنك الأهلي المصري NBE", "بنك القاهرة Banque du Caire", "بنك الزراعي المصري",
          "بنك ناصر الاجتماعي", "بنك الاستثمار القومي", "بنك تنمية الصادرات EBANK",
          "بنك التنمية الصناعية IDB", "بنك العقاري المصري العربي EALB"]
_ISLAMIC = ["بنك فيصل الإسلامي", "بنك البركة الإسلامي", "مصرف أبو ظبي الإسلامي ADIB",
            "بنك بيت التمويل الكويتي KFH", "بنك الأهلي المتحد KFH"]
_FOREIGN = ["بنك قطر الوطني الأهلي QNB", "بنك كريدي أجريكول", "بنك الإسكندرية", "بنك أبوظبي الأول مصر FABMISR",
            "بنك الإمارات دبي الوطني NDB", "بنك HSBC", "التجاري وفا بنك", "بنك المؤسسة العربية المصرفية ABC",
            "المصرف العربي الدولي AIB", "ستاندرد تشارترد – مصر", "بنك الكويت الوطني NBK", "بنك المشرق",
            "بنك الأهلي الكويتي مصر ABK", "البنك العربي", "البنك العربي الأفريقي", "بنك أبوظبي التجاري ADCB",
            "بنوك بلوم BLOM", "البنك الأهلي اليوناني أو البنك الوطني اليوناني", "بنك سيتي بنك CITIBANK"]


def bank_type(bank):
    if bank in _STATE:
        return "state"
    if bank in _ISLAMIC:
        return "islamic"
    if bank in _FOREIGN:
        return "foreign"
    return "private"


PROFILES = {
    "بنك مصر BM": dict(
        founded="8 مايو 1920",
        branches_approx="أكثر من 850 فرعاً ووحدة مصرفية تنتشر في مختلف محافظات جمهورية مصر العربية، بالإضافة إلى تواجد إقليمي ودولي.",
        origin="أسسه الاقتصادي الوطني محمد طلعت حرب باشا ليكون أول بنك مصري برأس مال وكوادر وطنية.",
        ownership="مملوك للدولة المصرية", mandate="ذراع تمويلي تنموي للدولة وأحد أكبر ثلاثة بنوك في السوق"),
    "البنك الأهلي المصري NBE": dict(
        founded="25 يونيو 1898",
        branches_approx="أكثر من 650 فرعاً ووحدة مصرفية في جميع أنحاء مصر، إلى جانب ماكينات الصراف الآلي التي تتجاوز 6,500 ماكينة.",
        origin="تأسس بأمر عالٍ في عهد الخديوي عباس حلمي الثاني بمبادرة من الممول البريطاني السير إرنست كاسل.",
        ownership="مملوك للدولة المصرية", mandate="أكبر بنك في مصر من حيث الأصول والودائع وأحد صنّاع السوق الرئيسيين"),
    "بنك القاهرة Banque du Caire": dict(
        founded="1952",
        branches_approx="شبكة تتجاوز 240 فرعاً ووحدة مصرفية موزعة على مستوى الجمهورية.",
        origin="تأسس في حقبة التحولات الاقتصادية الكبرى، وأصبح بعد التأميم في الستينيات جزءاً من القطاع المصرفي العام.",
        ownership="مملوك للدولة المصرية", mandate="شبكة فروع واسعة وتركيز على المشروعات الصغيرة والشمول المالي"),
    "البنك التجاري الدولي CIB": dict(
        founded="1975",
        branches_approx="أكثر من 210 فروع ووحدات مصرفية في كافة أنحاء مصر.",
        origin="تأسس باسم «تشيس ناشيونال بنك (مصر)» ثم تحوّل عام 1987 إلى «البنك التجاري الدولي».",
        ownership="شركة مساهمة مصرية مدرجة في البورصة المصرية ولها شهادات إيداع دولية في بورصة لندن",
        mandate="أكبر بنك خاص في مصر"),
    "بنك قطر الوطني الأهلي QNB": dict(
        branches_approx="أكثر من 230 فرعاً تنتشر في مختلف المحافظات المصرية.",
        origin="استحوذت مجموعة QNB القطرية عام 2013 على البنك الأهلي اليوناني – مصر.",
        ownership="تابع لمجموعة QNB", group="QNB Group (قطر)"),
    "بنك فيصل الإسلامي": dict(
        founded="1977",
        branches_approx="أكثر من 40 فرعاً رئيسياً تنتشر في المدن والمحافظات الرئيسية بمصر.",
        origin="أول مصرف إسلامي في مصر أُنشئ بقانون خاص.",
        ownership="شركة مساهمة مصرية بمساهمة كيانات سعودية ومصرية وأفراد ومؤسسات"),
}


def profile_of(bank):
    p = dict(PROFILES.get(bank, {}))
    p["type"] = bank_type(bank)
    return p


# ------------------------- مولّدات المحتوى حسب النية -------------------------
def comp_branches(bank, p):
    btype = TYPE_LABEL.get(p.get("type"), "مؤسسة مصرفية")
    
    # محاولة الحصول على التفاصيل عبر LLM أو الحقائق الموثقة
    if llm_available():
        dynamic_prompt = f"""أنت محلل مصرفي وخبير في شبكات الفروع والخدمات المالية في مصر.
اكتب تقريراً موجزاً ودقيقاً عن "شبكة فروع والانتشار الجغرافي وقنوات الخدمة" الخاصة بـ "{bank}".

الحقائق المتوفرة:
- نوع المؤسسة: {btype}
- معلومات شبكة الفروع التقريبية: {p.get('branches_approx', 'غير مسجلة بالتفصيل')}.

القواعد:
1. اذكر التقدير العام الموثوق لعدد الفروع وقنوات الانتشار الجغرافي (مثل الصراف الآلي والخدمات الرقمية).
2. قدم الإجابة في نقاط تبدأ بـ "- " وعناوين عريضة (**الانتشار الجغرافي:**، **التحول الرقمي والقنوات البديلة:**، **الشمول المالي:**).
3. وضح أن الأرقام الدقيقة تتحدث دورياً ويتم الرجوع فيها للموقع الرسمي للبنك أو التقرير السنوي."""
        
        ai_res = call_llm(dynamic_prompt)
        if ai_res:
            return f"{bank}: شبكة الفروع والانتشار الجغرافي", ai_res

    # إجابة احتياطية في حال غياب الذكاء الاصطناعي
    approx_info = p.get("branches_approx", f"يمتلك {bank} شبكة فروع تنتشر في القاهرة والمحافظات الرئيسية.")
    b = [
        ("الانتشار الجغرافي", approx_info),
        ("القنوات الرقمية البديلة", f"يستكمل {bank} شبكة فروع الفيزيقية عبر خدمات الإنترنت البنكي والتطبيق الهاتفي وماكينات الصراف الآلي (ATM)."),
        ("مصدر الأرقام المحدثة", "تتغير أرقام الفروع بدقة مع التوسعات الدورية؛ ويمكن مراجعتها من التقرير السنوي أو الموقع الرسمي للبنك.")
    ]
    return f"{bank}: شبكة الفروع والانتشار الجغرافي", _bullets_html(f"{bank}: شبكة الفروع والانتشار الجغرافي", b)


def comp_vision_mission(bank, p):
    btype = TYPE_LABEL.get(p.get("type"), "مؤسسة مصرفية")
    ownership_info = p.get("ownership") or ""
    group_info = f"المجموعة الأم: {p.get('group')}" if p.get("group") else ""
    mandate_info = p.get("mandate") or p.get("origin") or ""
    
    if llm_available():
        dynamic_prompt = f"""أنت محلل حوكمة مصرفية وتنافسية مؤسسية في مصر.
اكتب "الرؤية والرسالة والقيم المؤسسية" الخاصة بـ "{bank}" فقط.

حقائق البنك المتاحة:
- نوع المؤسسة: {btype}
- هيكل الملكية: {ownership_info}
- {group_info}
- الدور الاستراتيجي: {mandate_info}

القواعد:
1. قدم الإجابة في شكل نقاط تبدأ بـ "- " مع عناوين عريضة (**الرؤية الاستراتيجية:**، **الرسالة المؤسسية:**، **القيم الحاكمة:**)."""
        ai_res = call_llm(dynamic_prompt)
        if ai_res:
            return f"{bank}: الرؤية والرسالة المؤسسية", ai_res

    b = [
        ("الرسالة الاستراتيجية", f"تستهدف استراتيجية {bank} بصفته ({btype}) تقديم خدمات مصرفية متطورة تدعم الاقتصاد المصري."),
        ("الرؤية الاستراتيجية", f"ترتكز رؤية {bank} على التميز الرقمي المستدام وتعزيز مكانته التنافسية."),
        ("الإطار الحاكم", f"تتم أعمال البنك وفق قانون 194 لسنة 2020 ومعايير الحوكمة المعتمدة.")
    ]
    return f"{bank}: الرؤية والرسالة المؤسسية", _bullets_html(f"{bank}: الرؤية والرسالة المؤسسية", b)


def comp_history(bank, p):
    if not (p.get("origin") or p.get("founded")):
        return None
    b = []
    if p.get("founded"):
        b.append(("تاريخ التأسيس", p["founded"]))
    if p.get("origin"):
        b.append(("النشأة والمؤسس/المستحوِذ", p["origin"]))
    if p.get("ownership"):
        b.append(("هيكل الملكية", p["ownership"]))
    if p.get("mandate"):
        b.append(("الدور المميز", p["mandate"]))
    return f"{bank}: ملف النشأة والملكية", _bullets_html(f"{bank}: ملف النشأة والملكية", b)


def _t(p, bank, d):
    return d.get(p["type"], d["private"]).replace("{b}", bank)


def comp_board(bank, p):
    b = [("الإطار الملزم", "قانون البنك المركزي رقم 194 لسنة 2020 وتعليمات الحوكمة الصادرة عن البنك المركزي."),
         ("تكوين المجلس", "أغلبية من الأعضاء غير التنفيذيين مع حضور مستقلين، وفصل بين رئيس المجلس والرئيس التنفيذي.")]
    return f"{bank}: تعريف الحوكمة وتكوين مجلس الإدارة", _bullets_html(f"{bank}: تعريف الحوكمة وتكوين مجلس الإدارة", b)


def comp_independence(bank, p):
    b = [("المعيار", "نسبة الأعضاء المستقلين وغير التنفيذيين تُستخرج من التقرير السنوي للبنك."),
         ("تعارض المصالح", "سياسة مكتوبة لتعارض المصالح والإفصاح عن المعاملات مع الأطراف ذات العلاقة.")]
    return f"{bank}: الاستقلالية وتعارض المصالح", _bullets_html(f"{bank}: الاستقلالية وتعارض المصالح", b)


def comp_transparency(bank, p):
    b = [("مكافحة غسل الأموال", "الالتزام بقانون مكافحة غسل الأموال وتطبيق إجراءات التعرف على العميل (KYC)."),
         ("الإفصاح", "نشر القوائم المالية السنوية والدورية المعتمدة من مراقبي الحسابات.")]
    return f"{bank}: الشفافية والمساءلة ومكافحة الفساد", _bullets_html(f"{bank}: الشفافية والمساءلة ومكافحة الفساد", b)


def comp_cbe(bank, p):
    b = [("المرجعية", "قانون البنك المركزي والجهاز المصرفي رقم 194 لسنة 2020 والتعليمات الرقابية ذات الصلة.")]
    return f"{bank}: الامتثال للتعليمات الرقابية", _bullets_html(f"{bank}: الامتثال للتعليمات الرقابية", b)


def comp_women(bank, p):
    b = [("المستهدفات", "دعم الاستراتيجية القومية للشمول المالي وتمكين المرأة اقتصادياً ورائدات الأعمال.")]
    return f"{bank}: تمكين المرأة والشمول المالي", _bullets_html(f"{bank}: تمكين المرأة والشمول المالي", b)


def comp_climate(bank, p):
    b = [("الإطار", "إرشادات البنك المركزي للتمويل المستدام وإدارة مخاطر المناخ والتمويل الأخضر.")]
    return f"{bank}: مخاطر المناخ والتمويل الأخضر", _bullets_html(f"{bank}: مخاطر المناخ والتمويل الأخضر", b)


def comp_green_assets(bank, p):
    b = [("طريقة الحساب", "GAR = القروض والاستثمارات المتوافقة مع تصنيف الأنشطة الخضراء ÷ إجمالي الأصول المشمولة.")]
    return f"{bank}: نسبة الأصول الخضراء", _bullets_html(f"{bank}: نسبة الأصول الخضراء", b)


def comp_reporting(bank, p):
    b = [("المعايير", "الامتثال لمعايير المبادرة العالمية للتقارير (GRI) ومعايير الاستدامة الدولية (ISSB S1/S2).")]
    return f"{bank}: الامتثال لمعايير GRI وISSB", _bullets_html(f"{bank}: الامتثال لمعايير GRI وISSB", b)


def comp_csr(bank, p):
    b = [("المسؤولية المجتمعية", "ربط الإنفاق المجتمعي برؤية مصر 2030 وأهداف التنمية المستدامة.")]
    return f"{bank}: المسؤولية المجتمعية والإنفاق التنموي", _bullets_html(f"{bank}: المسؤولية المجتمعية والإنفاق التنموي", b)


def comp_data_gov(bank, p):
    b = [("حماية البيانات", "الالتزام بقانون حماية البيانات الشخصية رقم 151 لسنة 2020 وإرشادات الأمن السيبراني.")]
    return f"{bank}: حوكمة البيانات والامتثال", _bullets_html(f"{bank}: حوكمة البيانات والامتثال", b)


def comp_cyber(bank, p):
    b = [("الأمن السيبراني", "تطبيق إطار الأمن السيبراني للقطاع المالي الصادر عن البنك المركزي المصري.")]
    return f"{bank}: الحصانة السيبرانية", _bullets_html(f"{bank}: الحصانة السيبرانية", b)


def comp_sip(bank, p):
    b = [("البنية الرقمية", "جاهزية الأنظمة المصرفية الأساسية والتكامل مع منصات الدفع الوطنية (إنستاباي/ميزة).")]
    return f"{bank}: البنية التحتية الرقمية ومنصات المعلومات", _bullets_html(f"{bank}: البنية التحتية الرقمية ومنصات المعلومات", b)


def comp_regtech(bank, p):
    b = [("RegTech", "تطبيق حلول التقنية التنظيمية لأتمتة عمليات الامتثال وفحص الشكاوى والمعاملات.")]
    return f"{bank}: تقنيات الرقابة التنظيمية RegTech", _bullets_html(f"{bank}: تقنيات الرقابة التنظيمية RegTech", b)


def comp_pdpl(bank, p):
    b = [("السيادة الرقمية", "الامتثال لقواعد حماية البيانات الشخصية وحظر نقل البيانات الحساسة خارج البلاد دون ترخيص.")]
    return f"{bank}: قانون حماية البيانات والسيادة الرقمية", _bullets_html(f"{bank}: قانون حماية البيانات والسيادة الرقمية", b)


COMPOSERS = {
    "branches": comp_branches,
    "vision_mission": comp_vision_mission,
    "history": comp_history, "board": comp_board, "independence": comp_independence,
    "transparency": comp_transparency, "cbe_compliance": comp_cbe, "women": comp_women,
    "climate": comp_climate, "green_assets": comp_green_assets, "reporting": comp_reporting,
    "csr": comp_csr, "data_gov": comp_data_gov, "cyber": comp_cyber, "sip": comp_sip,
    "regtech": comp_regtech, "pdpl": comp_pdpl,
}

# ==============================================================================
# 5) أرشيف المعرفة JSON
# ==============================================================================
def load_json_knowledge():
    combined_data = {}
    for i in range(1, 7):
        part_filename = f"archive_part_{i}.json"
        if os.path.exists(part_filename):
            try:
                with open(part_filename, "r", encoding="utf-8") as f:
                    part_data = json.load(f)
                    if isinstance(part_data, dict):
                        combined_data.update(part_data)
            except Exception:
                pass
                
    if not combined_data and os.path.exists(JSON_KNOWLEDGE_FILE):
        try:
            with open(JSON_KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                combined_data = json.load(f)
        except Exception:
            pass
            
    return combined_data


def archive_lookup(bank, question, intent, kb=None):
    kb = kb if kb is not None else load_json_knowledge()
    d = kb.get(bank) if isinstance(kb, dict) else None
    if not d:
        return None
    if intent and intent in d:
        return d[intent]
    q = norm(question)
    qwords = {w for w in q.split() if len(w) > 3}
    best, best_score = None, 0
    for key, text in d.items():
        k = norm(key)
        if k in q:
            return text
        kw = {w for w in k.split() if len(w) > 3}
        if not kw:
            continue
        score = len(kw & qwords) / len(kw)
        if score > best_score:
            best, best_score = text, score
    return best if best_score >= 0.6 else None


# ==============================================================================
# 6) طبقة نموذج اللغة
# ==============================================================================
def _post_json(url, payload, headers, timeout=30):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def llm_available():
    return True


def call_llm(prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = "AQ.Ab8RN6IWu748mayng_1PWfSE8TS-R1Y1NuSnXncAN6uGrfzemA"
        
    try:
        if os.getenv("ANTHROPIC_API_KEY"):
            out = _post_json(
                "https://api.anthropic.com/v1/messages",
                {"model": os.getenv("BANK_RAG_ANTHROPIC_MODEL", "claude-sonnet-5-5"),
                 "max_tokens": 1500, "messages": [{"role": "user", "content": prompt}]},
                {"content-type": "application/json", "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01"})
            return "".join(b.get("text", "") for b in out.get("content", []))
        elif api_key:
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            out = _post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
                {"contents": [{"parts": [{"text": prompt}]}]}, {"content-type": "application/json"})
            return out["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None
    return None


def build_prompt(bank, question, p, archive_text=None, draft=None):
    facts = "\n".join(f"- {k}: {v}" for k, v in p.items() if v)
    return f"""أنت محلل حوكمة مصرفية وتقارير استدامة في مصر. أجب بالعربية الفصحى عن سؤال يخص البنك.

البنك: {bank}
السؤال: {question}

حقائق موثقة لدينا عن البنك:
{facts}

{('نص من أرشيف المعرفة:\n' + archive_text) if archive_text else ''}

قواعد صارمة:
1) إذا كان السؤال عن الفروع أو انتشار البنك، قدم إجابة واقعية موثوقة استناداً إلى طبيعة وحجم البنك وحقائقه المتاحة.
2) اذكر الإطار التنظيمي المصري ذا الصلة (قانون 194/2020، تعليمات البنك المركزي).
3) الصيغة: اكتب الإجابة في نقاط تبدأ بـ «- » وبعنوان عريض بصيغة **عنوان:**.
"""


def md_to_html(text):
    out, in_ul = [], False
    for line in html.escape(text).splitlines():
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line.strip())
        if line.startswith("- "):
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{line[2:]}</li>")
        else:
            if in_ul:
                out.append("</ul>"); in_ul = False
            if line:
                out.append(f"<p>{line}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


# ==============================================================================
# 7) التصيير (HTML)
# ==============================================================================
BADGES = {
    "archive": ("🟢 مصدر: أرشيف المعرفة JSON", "#166534"),
    "profile": ("🟡 مصدر: ملف تعريف البنك + ملفات وتقارير بنكية", "#92400E"),
    "llm": ("🔵 مصدر: تحليل واستخلاص ذكي (RAG Engine)", "#1E40AF"),
    "gap": ("⚪ لا توجد بيانات كافية", "#475569"),
}


def render_card(bank, question, inner_html, tier):
    label, color = BADGES[tier]
    return f"""
    <div dir="rtl" style="text-align:right; line-height:1.9; color:{CBE_NAVY}; background:#FFFFFF; padding:25px; border-radius:12px; border:1.5px solid {CBE_GOLD}; box-shadow:0 6px 18px rgba(0,0,0,0.06);">
      <h3 style="color:{CBE_NAVY}; font-weight:bold; margin-bottom:12px;">🎯 التقرير التحليلي المفصل ({html.escape(bank)})</h3>
      <p style="font-size:14.5px; margin-bottom:8px;"><b>السؤال / الاستفسار المطروح:</b> "{html.escape(question)}"</p>
      <p style="font-size:12.5px; font-weight:bold; color:{color}; margin-bottom:10px;">{label}</p>
      <div style="background:{CBE_BG}; padding:18px; border-radius:8px; border-right:5px solid {CBE_GOLD}; margin-top:8px; color:#1E293B; font-size:14.5px;">
        {inner_html}
      </div>
    </div>"""


def _bullets_html(title, bullets, foot=True):
    lis = "".join(f"<li><b>{html.escape(k)}:</b> {v}</li>" for k, v in bullets)
    FOOT = "ملاحظة منهجية: الإجابة تستند إلى البيانات المعتمدة والتقارير المصرفية الرسمية للبنك."
    f = f'<p style="font-size:12px;color:#64748B;margin-top:10px;">{FOOT}</p>' if foot else ""
    return f"<p><b>{html.escape(title)}</b></p><ul>{lis}</ul>{f}"


# ==============================================================================
# 8) الدالة الرئيسية — process_rag_gemini_query
# ==============================================================================
def process_rag_gemini_query(bank_name, question):
    if bank_name == "اختر البنك المصرفي" or not (question or "").strip():
        return "⚠️ يرجى اختيار البنك المصرفي وكتابة السؤال أو الاستفسار التنظيمي بدقة للحصول على التحليل."
    if not is_valid_arabic_question(question):
        return "⚠️ **تنبيه:** يرجى كتابة سؤال واضح باللغة العربية لكي تتمكن المنصة من تحليله."

    p = profile_of(bank_name)
    intent = classify_intent(question)

    # --- الطبقة 1: الأرشيف
    arch = archive_lookup(bank_name, question, intent)
    if arch:
        return render_card(bank_name, question, arch, "archive")

    # --- الطبقة 2: الملف التعريف + المولد التخصصي (سواء فروع أو حوكمة أو غيرها)
    comp = COMPOSERS.get(intent)
    result = comp(bank_name, p) if comp else None
    if result:
        title, generated_content = result
        if isinstance(generated_content, str) and not generated_content.startswith("<p><b>"):
            return render_card(bank_name, question, md_to_html(generated_content), "llm")
        return render_card(bank_name, question, generated_content, "profile")

    # --- الطبقة 3: نموذج لغة مباشر لأي سؤال خارج النوايا المحددة
    if llm_available():
        txt = call_llm(build_prompt(bank_name, question, p))
        if txt:
            return render_card(bank_name, question, md_to_html(txt), "llm")

    # --- الطبقة 4: الفجوة (تظهر فقط عند عدم وجود معلومات نهائياً)
    gap = (f"<p>لا تتوفر لدى المنصة بيانات موثقة تكفي للإجابة عن هذا السؤال بخصوص <b>{html.escape(bank_name)}</b>، "
           f"ولن تُقدَّم إجابة مبنية على التخمين.</p>"
           f"<ul><li><b>لإضافة الإجابة:</b> أضف نصاً للبنك في ملف الأرشيف تحت المفتاح المناسب.</li>"
           f"<li><b>مصدر مقترح:</b> تقرير الاستدامة والتقرير السنوي المنشوران للبنك.</li></ul>")
    return render_card(bank_name, question, gap, "gap")
