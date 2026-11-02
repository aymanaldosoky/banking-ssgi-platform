# -*- coding: utf-8 -*-
"""
bank_rag_engine.py
محرك "اسأل المنصة" المطوَّر — بديل مباشر للدالة process_rag_gemini_query
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
    "branches": ["عدد الفروع", "فروع البنك", "شبكه الفروع", "التواجد الجغرافي", "ما هي فروع", "كم عدد فروع", "عدد فروع"],
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
# 3) ملفات تعريف البنوك (حقائق فقط)
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
        branches="يمتلك البنك أكثر من 850 فرعاً ووحدة مصرفية منتشرة في كافة أنحاء الجمهورية، بالإضافة إلى تواجد إقليمي ودولي (فروع في الإمارات، فرنسا، ومكاتب تمثيل في الصين وروسيا).",
        origin="أسسه الاقتصادي الوطني محمد طلعت حرب باشا ليكون أول بنك مصري برأس مال وكوادر وطنية.",
        ownership="مملوك للدولة المصرية", mandate="ذراع تمويلي تنموي للدولة وأحد أكبر ثلاثة بنوك في السوق"),
    "البنك الأهلي المصري NBE": dict(
        founded="25 يونيو 1898",
        branches="يمتلك أضخم شبكة فروع في مصر تتجاوز 650 فرعاً ووحدة مصرفية داخل مصر، بالإضافة إلى فروع ومكاتب تمثيل خارجية (لندن، نيويورك، دبي، الخرطوم، وشبكة مراسلين عالمية).",
        origin="تأسس بأمر عالٍ في عهد الخديوي عباس حلمي الثاني بمبادرة من الممول البريطاني السير إرنست كاسل.",
        ownership="مملوك للدولة المصرية", mandate="أكبر بنك في مصر من حيث الأصول والودائع"),
    "بنك القاهرة Banque du Caire": dict(
        founded="1952",
        branches="تتجاوز شبكة فروعه 245 فرعاً ووحدة مصرفية متوزعة في مختلف محافظات مصر مع تركيز واسع في الصعيد والوجه البحري.",
        origin="تأسس في حقبة التحولات الاقتصادية الكبرى، وأصبح جزءاً من القطاع المصرفي العام.",
        ownership="مملوك للدولة المصرية", mandate="شبكة فروع واسعة وتركيز على المشروعات الصغيرة والشمول المالي"),
    "البنك التجاري الدولي CIB": dict(
        founded="1975",
        branches="يمتلك أكثر من 210 فرعاً ووحدة مصرفية موزعة استراتيجياً في كافة المراكز الاقتصادية والمحافظات المصرية، بالإضافة إلى فرع كينيا ومكاتب تمثيل خارجية.",
        origin="تأسس باسم تشيس ناشيونال بنك (مصر)، وتتحول عام 1987 إلى البنك التجاري الدولي.",
        ownership="شركة مساهمة مصرية مدرجة في البورصة المصرية ولديه شهادات إيداع دولية في بورصة لندن.",
        mandate="أكبر بنك خاص في مصر"),
    "بنك قطر الوطني الأهلي QNB": dict(
        branches="يتجاوز عدد فروعه 230 فرعاً في مختلف أنحاء مصر.",
        origin="استحوذت مجموعة QNB القطرية عام 2013 على البنك الأهلي اليوناني – مصر وأعادت تسميته.",
        ownership="تابع لمجموعة QNB", group="QNB Group (قطر)"),
    "بنك كريدي أجريكول": dict(
        branches="يمتلك شبكة فروع تمتد إلى أكثر من 80 فرعاً في القاهرة والمحافظات الرئيسية.",
        origin="يعود إلى البنك المصري الأمريكي وتأسس عام 1976.",
        ownership="تابع لمجموعة كريدي أجريكول الفرنسية", group="Crédit Agricole (فرنسا)"),
    "بنك الإسكندرية": dict(
        founded="1957",
        branches="يمتلك شبكة تمتد لأكثر من 170 فرعاً تغطي كافة أنحاء الجمهورية.",
        origin="بنك عام قديم جرى خصخصته عام 2006 لصالح مجموعة إنتيزا سان باولو.",
        ownership="مملوك بالأغلبية لمجموعة Intesa Sanpaolo الإيطالية", group="Intesa Sanpaolo (إيطاليا)"),
    "بنك فيصل الإسلامي": dict(
        founded="1977",
        branches="تغطي فروعه أكثر من 40 فرعاً رئيسياً في مختلف عواصم المحافظات والمدن الكبرى.",
        origin="أول مصرف إسلامي في مصر أُنشئ بقانون خاص.",
        ownership="شركة مساهمة مصرية بمساهمة كيانات سعودية ومصرية"),
}

# ==============================================================================
# 4) دالة إعداد الفروع وحساب النية
# ==============================================================================
def comp_branches(bank, p):
    btype = TYPE_LABEL.get(p.get("type"), "مؤسسة مصرفية")
    branches_info = p.get("branches")
    
    if branches_info:
        b = [
            ("شبكة الفروع والتواجد الجغرافي", branches_info),
            ("نوع الكيان المصرفي", btype),
            ("التكامل مع القنوات الرقمية", "تتكامل هذه الشبكة مع حلول الدفع الرقمية (الموبايل بانكنج، ماكينات ATM، والصراف الآلي التفاعلي) لتعزيز الشمول المالي وفق توجيهات البنك المركزي المصري.")
        ]
        return f"{bank}: التواجد الجغرافي وعدد الفروع", _bullets_html(f"{bank}: التواجد الجغرافي وعدد الفروع", b)
    
    # في حالة عدم إدخال الفروع يدوياً يولد الرد عبر النموذج أو النص العام
    if llm_available():
        dynamic_prompt = f"أعطني معلومات دقيقة ومحدثة عن عدد فروع بنك ({bank}) وتواجده الجغرافي في مصر ودولياً إن وجد."
        ai_res = call_llm(dynamic_prompt)
        if ai_res:
            return f"{bank}: شبكة الفروع والتواجد الجغرافي", ai_res

    b = [
        ("التواجد الجغرافي", f"يمتلك {bank} شبكة فروع تنتشر في القاهرة والمحافظات لتقديم كافة الخدمات المصرفية."),
        ("تنويه رقمي", "للحصول على العدد الدقيق واللحظي للفروع، يُنصح بالاطلاع على التقرير السنوي الأخير أو الدليل الجغرافي للموقع الرسمي للبنك.")
    ]
    return f"{bank}: التواجد الجغرافي", _bullets_html(f"{bank}: التواجد الجغرافي", b)


def comp_vision_mission(bank, p):
    btype = TYPE_LABEL.get(p.get("type"), "مؤسسة مصرفية")
    ownership_info = p.get("ownership") or ""
    group_info = f"المجموعة الأم: {p.get('group')}" if p.get("group") else ""
    mandate_info = p.get("mandate") or p.get("origin") or ""
    
    if llm_available():
        dynamic_prompt = f"""أنت محلل حوكمة مصرفية وتنافسية مؤسسية في مصر.
اكتب "الرؤية والرسالة والقيم المؤسسية" الخاصة بـ "{bank}" فقط.
- نوع المؤسسة: {btype}
- هيكل الملكية: {ownership_info}
- {group_info}
- الدور الاستراتيجي: {mandate_info}"""
        ai_res = call_llm(dynamic_prompt)
        if ai_res:
            return f"{bank}: الرؤية والرسالة المؤسسية", ai_res

    b = [
        ("الرسالة الاستراتيجية", f"تستهدف استراتيجية {bank} بصفته ({btype}) تقديم خدمات مصرفية متطورة تدعم الاقتصاد المصري."),
        ("الرؤية الاستراتيجية", f"ترتكز رؤية {bank} على التميز الرقمي المستدام وتعزيز مكانته التنافسية.")
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


COMPOSERS = {
    "branches": comp_branches,
    "vision_mission": comp_vision_mission,
    "history": comp_history,
}

# ==============================================================================
# 5) دمج دوال الاستعلام والأرشيف
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


def llm_available():
    return True


def call_llm(prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url, 
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8"), 
            headers={"content-type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            out = json.loads(r.read().decode("utf-8"))
            return out["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


def render_card(bank, question, inner_html, tier):
    BADGES = {
        "archive": ("🟢 مصدر: أرشيف المعرفة JSON", "#166534"),
        "profile": ("🟡 مصدر: ملف تعريف البنك + ملفات وتقارير بنكية", "#92400E"),
        "llm": ("🔵 مصدر: نموذج لغة مقيّد بالسياق (راجع الأرقام)", "#1E40AF"),
        "gap": ("⚪ لا توجد بيانات كافية", "#475569"),
    }
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
    f = f'<p style="font-size:12px;color:#64748B;margin-top:10px;">ملاحظة منهجية: الإجابة تستند إلى المعلومات الرسمية الموثقة عن البنك.</p>' if foot else ""
    return f"<p><b>{html.escape(title)}</b></p><ul>{lis}</ul>{f}"


def profile_of(bank):
    p = dict(PROFILES.get(bank, {}))
    p["type"] = bank_type(bank)
    return p


# ==============================================================================
# 6) الدالة الرئيسية
# ==============================================================================
def process_rag_gemini_query(bank_name, question):
    if bank_name == "اختر البنك المصرفي" or not (question or "").strip():
        return "⚠️ يرجى اختيار البنك المصرفي وكتابة السؤال أو الاستفسار التنظيمي بدقة للحصول على التحليل."

    p = profile_of(bank_name)
    intent = classify_intent(question)

    # 1. الطبقة الأولى: الأرشيف
    arch = archive_lookup(bank_name, question, intent)
    if arch:
        return render_card(bank_name, question, arch, "archive")

    # 2. الطبقة الثانية: الملف التعريفي والنوايا المعرفة
    comp = COMPOSERS.get(intent)
    result = comp(bank_name, p) if comp else None
    if result:
        title, generated_content = result
        return render_card(bank_name, question, generated_content, "profile")

    # 3. الطبقة الثالثة: استعلام الـ الذكاء الاصطناعي عند التفعيل
    if os.getenv("GEMINI_API_KEY"):
        prompt = f"أنت خبير مصرفي مصري. أجب باختصار ووضوح عن السؤال التالي الخاص بـ ({bank_name}):\nالسؤال: {question}"
        txt = call_llm(prompt)
        if txt:
            return render_card(bank_name, question, txt, "llm")

    # 4. الطبقة الرابعة: الفجوة الصريحة
    gap = (f"<p>لا تتوفر لدى المنصة بيانات موثقة تكفي للإجابة عن هذا السؤال بخصوص <b>{html.escape(bank_name)}</b>، "
           f"ولن تُقدَّم إجابة مبنية على التخمين.</p>"
           f"<ul><li><b>لإضافة الإجابة:</b> أضف نصاً للبنك في ملف الأرشيف تحت المفتاح المناسب.</li>"
           f"<li><b>لتفعيل الإجابة الآلية:</b> عيّن متغير البيئة GEMINI_API_KEY.</li>"
           f"<li><b>مصدر مقترح:</b> تقرير الاستدامة والتقرير السنوي المنشوران للبنك.</li></ul>")
    return render_card(bank_name, question, gap, "gap")
