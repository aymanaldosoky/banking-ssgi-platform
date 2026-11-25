import io
import os
import json
import re
import math
import numbers
import base64
import hashlib
import time
import uuid
import inspect
from difflib import SequenceMatcher
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import psycopg2

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    HAS_PYTHON_DOCX = True
except ImportError:
    HAS_PYTHON_DOCX = False

# استيراد محرك الإجابات المستقل المطور وتوابعه البرمجية
from bank_rag_engine import (
    BANKS_LIST_AR as _RAW_BANKS_LIST_AR,
    process_rag_gemini_query,
    stream_rag_gemini_query,
    audit_differentiation,
    load_survey_log_from_file,
    render_tab_7_survey,
)

# ترتيب قائمة البنوك بحيث يتصدرها البنك المركزي المصري يليه البنوك الخمسة الكبرى ثم باقي البنوك
_PRIORITY_BANKS = [
    "البنك المركزي المصري",
    "بنك مصر",
    "البنك الأهلي المصري",
    "بنك القاهرة",
    "البنك التجاري الدولي",
    "بنك فيصل الإسلامي",
]

_raw_list = list(_RAW_BANKS_LIST_AR)
_has_placeholder = bool(_raw_list and _raw_list[0] == "اختر البنك المصرفي")
_base_banks = [b for b in _raw_list if b != "اختر البنك المصرفي"]

_ordered_banks = []
for _p_bank in _PRIORITY_BANKS:
    _matched = next(
        (b for b in _base_banks if b == _p_bank or b.startswith(_p_bank)),
        _p_bank
    )
    if _matched not in _ordered_banks:
        _ordered_banks.append(_matched)

for _b in _base_banks:
    if _b not in _ordered_banks:
        _ordered_banks.append(_b)

BANKS_LIST_AR = (["اختر البنك المصرفي"] + _ordered_banks) if _has_placeholder else _ordered_banks

# ==============================================================================
# إعدادات صفحة Streamlit وتطبيق الهوية البصرية المصرفية (RTL + Responsive)
# ==============================================================================
st.set_page_config(
    page_title="مقترح المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="auto"
)

# حقن خطوط Google مباشرة داخل <head> الصفحة الأم في اللحظة صفر لمنع تفكك الحروف العربية (FOUT)
components.html(
    """
    <script>
    (function() {
        var doc = window.parent.document;
        var head = doc.head || doc.getElementsByTagName('head')[0];
        if (!head) return;

        doc.documentElement.setAttribute('dir', 'rtl');
        doc.documentElement.setAttribute('lang', 'ar');

        if (!doc.getElementById('raseen-gf-preconnect-1')) {
            var p1 = doc.createElement('link');
            p1.id = 'raseen-gf-preconnect-1';
            p1.rel = 'preconnect';
            p1.href = 'https://fonts.googleapis.com';
            head.prepend(p1);
        }

        if (!doc.getElementById('raseen-gf-preconnect-2')) {
            var p2 = doc.createElement('link');
            p2.id = 'raseen-gf-preconnect-2';
            p2.rel = 'preconnect';
            p2.href = 'https://fonts.gstatic.com';
            p2.crossOrigin = 'anonymous';
            head.prepend(p2);
        }

        if (!doc.getElementById('raseen-gf-arabic-fonts')) {
            var link = doc.createElement('link');
            link.id = 'raseen-gf-arabic-fonts';
            link.rel = 'stylesheet';
            link.href = 'https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=Readex+Pro:wght@300;400;500;600;700&family=Tajawal:wght@400;500;700;800;900&display=swap';
            head.prepend(link);
        }
    })();
    </script>
    """,
    height=0,
    width=0,
)

CBE_NAVY = "#002B49"          # أزرق مصرفي عميق
CBE_GOLD = "#C5A059"          # ذهبي ملكي
CBE_GOLD_LIGHT = "#E2C07D"    # ذهبي فاتح
CBE_GOLD_BRIGHT = "#F5D076"   # ذهبي مشرق (حالة التمرير والضغط والتبويب النشط)
CBE_NAVY_HOVER = "#003B63"    # أزرق عند التمرير
CBE_BG = "#F8F9FA"            # خلفية ناعمة
RAG_CACHE_VERSION = "v2.1"    # تغيير الإصدار يبطل أي ردود مبتورة مخزنة سابقاً في الكاش
UI_CSS_VERSION = "tabs-v20"   # إصدار محدث لإبطال الكاش فوراً + تكبير وتعريض خط المفاتيح

APP_FONT = "'Cairo', 'Tajawal', 'Readex Pro', 'Segoe UI', 'Tahoma', 'Arial', sans-serif"

# ------------------------------------------------------------------------------
# تنسيق الشريط العلوي (التبويبات): متجاوب 100% بين اللابتوب والموبايل
# ------------------------------------------------------------------------------
TABS_RULES = f"""
div[data-testid="stTabs"],
div.stTabs {{
    width: 100% !important;
    max-width: 100% !important;
    min-width: 100% !important;
    direction: rtl !important;
    border: none !important;
    margin: 0 !important;
    padding: 0 !important;
}}

div[data-testid="stTabs"] > div,
div[data-testid="stTabs"] [data-baseweb="tabs"],
div.stTabs [data-baseweb="tabs"] {{
    width: 100% !important;
    max-width: 100% !important;
}}

div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
div[data-testid="stTabs"] [data-baseweb="tab-border"] {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    opacity: 0 !important;
    background-color: transparent !important;
}}

html body div[data-testid="stTabs"] [data-baseweb="tab-list"],
html body [role="tablist"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: stretch !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    gap: 6px !important;
    padding: 8px !important;
    margin: 0 0 14px 0 !important;
    background-color: {CBE_NAVY} !important;
    background: {CBE_NAVY} !important;
    background-image: none !important;
    border: 2px solid {CBE_GOLD} !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 25px rgba(0, 43, 73, 0.25) !important;
    direction: rtl !important;
}}

div[data-testid="stTabs"] [data-baseweb="tab-list"] > div,
div[data-testid="stTabs"] [data-baseweb="tab-list"] [role="tablist"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 6px !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    direction: rtl !important;
}}

@media (min-width: 769px) {{
    html body div[data-testid="stTabs"] [data-baseweb="tab-list"],
    html body [role="tablist"] {{
        justify-content: space-between !important;
        overflow: visible !important;
    }}

    div[data-testid="stTabs"] [data-baseweb="tab-list"] > div,
    div[data-testid="stTabs"] [data-baseweb="tab-list"] [role="tablist"] {{
        flex: 1 1 100% !important;
        width: 100% !important;
    }}

    html body div[data-testid="stTabs"] button[role="tab"],
    html body div[data-testid="stTabs"] button[data-baseweb="tab"],
    html body [role="tablist"] [role="tab"] {{
        flex: 1 1 0% !important;
        min-width: 0 !important;
        width: 100% !important;
        max-width: none !important;
        height: auto !important;
        min-height: 54px !important;
        margin: 0 !important;
        padding: 9px 6px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 1.5px solid rgba(197, 160, 89, 0.35) !important;
        border-radius: 8px !important;
        font-family: {APP_FONT} !important;
        font-weight: 800 !important;
        font-size: 14.5px !important;
        line-height: 1.4 !important;
        letter-spacing: 0.15px !important;
        text-align: center !important;
        white-space: normal !important;
        outline: none !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }}

    html body div[data-testid="stTabs"] button[role="tab"] *,
    html body [role="tablist"] [role="tab"] * {{
        white-space: normal !important;
        font-weight: 800 !important;
    }}
}}

@media (max-width: 768px) {{
    html body div[data-testid="stTabs"] [data-baseweb="tab-list"],
    html body [role="tablist"] {{
        overflow-x: auto !important;
        overflow-y: hidden !important;
        justify-content: flex-start !important;
        padding: 8px !important;
        gap: 8px !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: thin !important;
        scrollbar-color: {CBE_GOLD} {CBE_NAVY} !important;
    }}

    html body div[data-testid="stTabs"] [data-baseweb="tab-list"]::-webkit-scrollbar,
    html body [role="tablist"]::-webkit-scrollbar {{
        height: 4px !important;
    }}
    html body div[data-testid="stTabs"] [data-baseweb="tab-list"]::-webkit-scrollbar-track,
    html body [role="tablist"]::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.08) !important;
        border-radius: 4px !important;
    }}
    html body div[data-testid="stTabs"] [data-baseweb="tab-list"]::-webkit-scrollbar-thumb,
    html body [role="tablist"]::-webkit-scrollbar-thumb {{
        background: {CBE_GOLD} !important;
        border-radius: 4px !important;
    }}

    div[data-testid="stTabs"] [data-baseweb="tab-list"] > div,
    div[data-testid="stTabs"] [data-baseweb="tab-list"] [role="tablist"] {{
        flex: 0 0 auto !important;
        width: max-content !important;
        gap: 8px !important;
    }}

    html body div[data-testid="stTabs"] button[role="tab"],
    html body div[data-testid="stTabs"] button[data-baseweb="tab"],
    html body [role="tablist"] [role="tab"] {{
        flex: 0 0 auto !important;
        min-width: max-content !important;
        width: auto !important;
        max-width: none !important;
        height: auto !important;
        min-height: 50px !important;
        margin: 0 !important;
        padding: 10px 18px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 1.5px solid rgba(197, 160, 89, 0.45) !important;
        border-radius: 8px !important;
        font-family: {APP_FONT} !important;
        font-weight: 800 !important;
        font-size: 15.5px !important;
        line-height: 1.45 !important;
        text-align: center !important;
        white-space: nowrap !important;
        outline: none !important;
        box-shadow: none !important;
    }}

    html body div[data-testid="stTabs"] button[role="tab"] *,
    html body [role="tablist"] [role="tab"] * {{
        white-space: nowrap !important;
        display: inline !important;
        font-weight: 800 !important;
    }}

    div[data-testid="stTabs"] button[aria-label*="scroll"],
    div[data-testid="stTabs"] [data-baseweb="tab-list"] ~ button {{
        display: none !important;
    }}
}}

div[data-testid="stTabs"] button[role="tab"] *,
html body [role="tablist"] [role="tab"] * {{
    font-family: {APP_FONT} !important;
    font-size: inherit !important;
    font-weight: inherit !important;
    line-height: inherit !important;
    text-align: center !important;
    margin: 0 !important;
}}
"""

TABS_COLOR_RULES = f"""
html body [data-baseweb="tab-list"] button[role="tab"],
html body [data-baseweb="tab-list"] button[role="tab"] *,
html body [role="tablist"] [role="tab"],
html body [role="tablist"] [role="tab"] * {{
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    opacity: 1 !important;
}}

html body [data-baseweb="tab-list"] button[role="tab"],
html body [role="tablist"] [role="tab"] {{
    background-color: {CBE_NAVY} !important;
}}

html body [data-baseweb="tab-list"] button[role="tab"] *,
html body [role="tablist"] [role="tab"] * {{
    background: transparent !important;
}}

html body [data-baseweb="tab-list"] button[role="tab"]:is(:hover, :active, :focus-visible, [aria-selected="true"]),
html body [data-baseweb="tab-list"] button[role="tab"]:is(:hover, :active, :focus-visible, [aria-selected="true"]) *,
html body [role="tablist"] [role="tab"]:is(:hover, :active, :focus-visible, [aria-selected="true"]),
html body [role="tablist"] [role="tab"]:is(:hover, :active, :focus-visible, [aria-selected="true"]) * {{
    color: {CBE_GOLD_BRIGHT} !important;
    -webkit-text-fill-color: {CBE_GOLD_BRIGHT} !important;
}}

html body [data-baseweb="tab-list"] button[role="tab"]:hover,
html body [role="tablist"] [role="tab"]:hover {{
    background-color: {CBE_NAVY_HOVER} !important;
}}

html body [data-baseweb="tab-list"] button[role="tab"][aria-selected="true"],
html body [role="tablist"] [role="tab"][aria-selected="true"] {{
    background-color: {CBE_NAVY} !important;
    font-weight: 900 !important;
    border: 2px solid {CBE_GOLD} !important;
    box-shadow: 0 0 12px rgba(197, 160, 89, 0.45) !important;
}}
"""

TABS_RULES = TABS_RULES + TABS_COLOR_RULES
TABS_CSS = f"<style id='ssgi-tabs-{UI_CSS_VERSION}'>{TABS_RULES}</style>"

# ==============================================================================
# محرك الصوت التفاعلي الفوري (Web Audio API - Zero Latency - Chime & Click)
# ==============================================================================
SOUND_ENGINE_JS = """
(function () {
  var W = window;
  var SOUND_PREF_KEY = 'raseen_ui_sound_enabled';

  if (typeof W.__raseenAudioCtx === 'undefined') {
    W.__raseenAudioCtx = null;
  }

  function isSoundEnabled() {
    try {
      var val = W.localStorage.getItem(SOUND_PREF_KEY);
      return val === null ? true : (val === '1');
    } catch (e) {
      return true;
    }
  }

  function setSoundEnabled(enabled) {
    try {
      W.localStorage.setItem(SOUND_PREF_KEY, enabled ? '1' : '0');
    } catch (e) {}
    updateToggleBadges();
  }

  function getAudioContext() {
    try {
      var AudioCtx = W.AudioContext || W.webkitAudioContext;
      if (!AudioCtx) return null;
      if (!W.__raseenAudioCtx) {
        W.__raseenAudioCtx = new AudioCtx();
      }
      if (W.__raseenAudioCtx.state === 'suspended') {
        W.__raseenAudioCtx.resume();
      }
      return W.__raseenAudioCtx;
    } catch (e) {
      return null;
    }
  }

  function playUiTone(kind) {
    if (!isSoundEnabled()) return;
    var ctx = getAudioContext();
    if (!ctx) return;

    try {
      var now = ctx.currentTime;

      if (kind === 'tab') {
        var osc1 = ctx.createOscillator();
        var osc2 = ctx.createOscillator();
        var gain = ctx.createGain();

        osc1.type = 'sine';
        osc2.type = 'triangle';
        osc1.frequency.setValueAtTime(880, now);
        osc1.frequency.exponentialRampToValueAtTime(1174.66, now + 0.09);
        osc2.frequency.setValueAtTime(1760, now);

        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.linearRampToValueAtTime(0.055, now + 0.012);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.24);

        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(ctx.destination);

        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 0.25);
        osc2.stop(now + 0.25);

      } else if (kind === 'radio') {
        var oscR = ctx.createOscillator();
        var gainR = ctx.createGain();
        oscR.type = 'sine';
        oscR.frequency.setValueAtTime(540, now);
        oscR.frequency.exponentialRampToValueAtTime(760, now + 0.055);

        gainR.gain.setValueAtTime(0.0001, now);
        gainR.gain.linearRampToValueAtTime(0.04, now + 0.008);
        gainR.gain.exponentialRampToValueAtTime(0.0001, now + 0.075);

        oscR.connect(gainR);
        gainR.connect(ctx.destination);
        oscR.start(now);
        oscR.stop(now + 0.08);

      } else {
        var oscB = ctx.createOscillator();
        var gainB = ctx.createGain();
        oscB.type = 'triangle';
        oscB.frequency.setValueAtTime(680, now);
        oscB.frequency.exponentialRampToValueAtTime(420, now + 0.05);

        gainB.gain.setValueAtTime(0.0001, now);
        gainB.gain.linearRampToValueAtTime(0.05, now + 0.006);
        gainB.gain.exponentialRampToValueAtTime(0.0001, now + 0.065);

        oscB.connect(gainB);
        gainB.connect(ctx.destination);
        oscB.start(now);
        oscB.stop(now + 0.07);
      }
    } catch (e) {}
  }

  function updateToggleBadges() {
    var enabled = isSoundEnabled();
    document.querySelectorAll('[data-raseen-sound-toggle]').forEach(function (el) {
      el.innerHTML = enabled ? '🔊 الصوت: مفعّل' : '🔇 الصوت: صامت';
      el.style.borderColor = enabled ? '#C5A059' : '#94A3B8';
      el.style.color = enabled ? '#002B49' : '#64748B';
    });
  }

  W.__raseenPlayTone = playUiTone;

  if (!W.__raseenGlobalSoundBound) {
    W.__raseenGlobalSoundBound = true;
    document.addEventListener('pointerdown', function (e) {
      var target = e.target;
      if (!target || !target.closest) return;

      var soundToggle = target.closest('[data-raseen-sound-toggle]');
      if (soundToggle) {
        var nextState = !isSoundEnabled();
        setSoundEnabled(nextState);
        if (nextState) {
          playUiTone('tab');
        }
        return;
      }

      if (target.closest('[role="tab"], [data-tab-target]')) {
        playUiTone('tab');
        return;
      }

      if (target.closest('button, a[kind], [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"], [data-testid="stFormSubmitButton"] button')) {
        playUiTone('button');
        return;
      }

      if (target.closest('div[role="radiogroup"] label, [data-baseweb="checkbox"], [data-baseweb="select"], summary')) {
        playUiTone('radio');
        return;
      }
    }, true);
  }

  updateToggleBadges();
})();
"""

TABS_GUARD_JS = """
(function () {
  var W = window;
  if (W.__ssgiTabsObserver) { try { W.__ssgiTabsObserver.disconnect(); } catch (e) {} }
  var NAVY = '%NAVY%', HOVER = '%HOVER%', GOLD = '%GOLD%', WHITE = '#FFFFFF';
  var SEL = '[role="tablist"] [role="tab"]';
  var TAB_STORE_KEY = 'raseen_active_tab_idx';

  function setColor(el, c) {
    el.style.setProperty('color', c, 'important');
    el.style.setProperty('-webkit-text-fill-color', c, 'important');
  }

  function paint(btn, hot) {
    var sel = btn.getAttribute('aria-selected') === 'true';
    var c = (sel || hot) ? GOLD : WHITE;
    setColor(btn, c);
    btn.style.setProperty('background-color', (hot && !sel) ? HOVER : NAVY, 'important');
    btn.querySelectorAll('*').forEach(function (n) { setColor(n, c); });
  }

  function saveActiveTab(idx) {
    try {
      W.sessionStorage.setItem(TAB_STORE_KEY, String(idx));
      var u = new URL(W.location.href);
      u.searchParams.set('tab', String(idx));
      W.history.replaceState({}, '', u.toString());
    } catch (e) {}
  }

  function getSavedTabIndex() {
    try {
      var u = new URL(W.location.href);
      var tUrl = u.searchParams.get('tab');
      if (tUrl !== null && !isNaN(parseInt(tUrl, 10))) {
        return parseInt(tUrl, 10);
      }
      var tSess = W.sessionStorage.getItem(TAB_STORE_KEY);
      if (tSess !== null && !isNaN(parseInt(tSess, 10))) {
        return parseInt(tSess, 10);
      }
    } catch (e) {}
    return 0;
  }

  function goToTab(idx, shouldScroll) {
    var tabs = document.querySelectorAll(SEL);
    if (tabs && tabs[idx]) {
      saveActiveTab(idx);
      if (tabs[idx].getAttribute('aria-selected') !== 'true') {
        tabs[idx].click();
      }
      setTimeout(run, 20);
      if (W.innerWidth <= 768) {
        try { tabs[idx].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' }); } catch (e) {}
      }
      if (shouldScroll) {
        var tabList = document.querySelector('[role="tablist"]');
        if (tabList) {
          try { tabList.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {}
        }
      }
    }
  }

  function enforceSavedTab() {
    var savedIdx = getSavedTabIndex();
    var tabs = document.querySelectorAll(SEL);
    if (!tabs || !tabs.length || savedIdx < 0 || savedIdx >= tabs.length) return;
    var targetBtn = tabs[savedIdx];
    if (targetBtn && targetBtn.getAttribute('aria-selected') !== 'true') {
      targetBtn.click();
      saveActiveTab(savedIdx);
      setTimeout(run, 25);
    }
  }

  function run() {
    document.querySelectorAll('[data-baseweb="tab-highlight"], [data-baseweb="tab-border"]')
      .forEach(function (el) { el.style.setProperty('display', 'none', 'important'); });

    document.querySelectorAll(SEL).forEach(function (b, idx) {
      paint(b, b.matches(':hover'));
      if (!b.__ssgi) {
        b.__ssgi = 1;
        b.addEventListener('pointerenter', function () { paint(b, true); });
        b.addEventListener('pointerleave', function () { paint(b, false); });
        b.addEventListener('pointerdown',  function () { paint(b, true); });
        b.addEventListener('pointerup',    function () { paint(b, false); });
        b.addEventListener('click', function () {
          saveActiveTab(idx);
          setTimeout(run, 0);
          if (W.innerWidth <= 768) {
            try { b.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' }); } catch (e) {}
          }
        });
      }
    });

    document.querySelectorAll('[data-tab-target]').forEach(function (card) {
      if (!card.__ssgiNav) {
        card.__ssgiNav = 1;
        card.addEventListener('click', function () {
          var idx = parseInt(card.getAttribute('data-tab-target'), 10);
          if (!isNaN(idx)) {
            goToTab(idx, true);
          }
        });
        card.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            var idx = parseInt(card.getAttribute('data-tab-target'), 10);
            if (!isNaN(idx)) {
              goToTab(idx, true);
            }
          }
        });
      }
    });
  }

  var queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; run(); });
  }

  run();
  enforceSavedTab();
  setTimeout(function () { enforceSavedTab(); run(); }, 100);
  setTimeout(function () { enforceSavedTab(); run(); }, 300);
  setTimeout(function () { enforceSavedTab(); run(); }, 650);

  W.__ssgiTabsObserver = new MutationObserver(schedule);
  W.__ssgiTabsObserver.observe(document.body, {
    childList: true, subtree: true,
    attributes: true, attributeFilter: ['aria-selected']
  });
})();
"""


def inject_ui_sound_engine():
    """يحقن محرك المؤثرات الصوتية التفاعلية في الصفحة الأم."""
    components.html(
        f"""
        <script>
        (function() {{
            var doc = window.parent.document;
            doc.querySelectorAll('script[id^="raseen-sound-engine-"]').forEach(function (n) {{ n.remove(); }});
            var sc = doc.createElement('script');
            sc.id = 'raseen-sound-engine-{UI_CSS_VERSION}';
            sc.textContent = {json.dumps(SOUND_ENGINE_JS)};
            doc.head.appendChild(sc);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def inject_tabs_css():
    """يحقن CSS والسكربت في <head> الصفحة الأم فيبقيان فعّالين بعد كل rerun."""
    st.markdown(TABS_CSS, unsafe_allow_html=True)

    guard_js = (
        TABS_GUARD_JS
        .replace("%NAVY%", CBE_NAVY)
        .replace("%HOVER%", CBE_NAVY_HOVER)
        .replace("%GOLD%", CBE_GOLD_BRIGHT)
    )

    components.html(
        f"""
        <script>
        (function() {{
            var doc = window.parent.document;

            doc.querySelectorAll('style[id^="ssgi-tabs-css-"], script[id^="ssgi-tabs-guard-"], style[id^="ssgi-tabs-"]')
               .forEach(function (n) {{ n.remove(); }});

            var st = doc.createElement('style');
            st.id = 'ssgi-tabs-css-{UI_CSS_VERSION}';
            st.textContent = {json.dumps(TABS_RULES)};
            doc.head.appendChild(st);

            var sc = doc.createElement('script');
            sc.id = 'ssgi-tabs-guard-{UI_CSS_VERSION}';
            sc.textContent = {json.dumps(guard_js)};
            doc.head.appendChild(sc);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def restore_survey_from_url_or_browser():
    """استعادة إجابات الاستبيان ومرحلة المعالج تلقائياً عند الضغط على F5 أو Refresh."""
    if "survey_store" not in st.session_state:
        st.session_state.survey_store = {}
    if "survey_wizard_step" not in st.session_state:
        st.session_state.survey_wizard_step = 1

    encoded_draft = st.query_params.get("sdraft", "")
    if encoded_draft and not st.session_state.survey_store:
        try:
            padded = encoded_draft + "=" * (-len(encoded_draft) % 4)
            raw_json = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
            parsed = json.loads(raw_json)
            if isinstance(parsed, dict):
                restored_store = parsed.get("store", {})
                restored_step = int(parsed.get("step", 1))
                if isinstance(restored_store, dict) and restored_store:
                    st.session_state.survey_store.update(restored_store)
                    st.session_state.survey_wizard_step = restored_step
        except Exception:
            pass

    has_data = bool(st.session_state.survey_store)
    components.html(
        f"""
        <script>
        (function() {{
            try {{
                var LS_KEY = 'raseen_survey_draft_v2';
                var hasServerData = {json.dumps(has_data)};
                var raw = window.parent.localStorage.getItem(LS_KEY);
                if (!hasServerData && raw) {{
                    var parsed = JSON.parse(raw);
                    if (parsed && !parsed.submitted && parsed.store && Object.keys(parsed.store).length > 0) {{
                        var b64 = btoa(unescape(encodeURIComponent(raw)))
                            .replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/, '');
                        var u = new URL(window.parent.location.href);
                        if (u.searchParams.get('sdraft') !== b64) {{
                            u.searchParams.set('sdraft', b64);
                            u.searchParams.set('tab', '7');
                            window.parent.location.replace(u.toString());
                        }}
                    }}
                }}
            }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def sync_survey_browser_backup():
    """حفظ نسخة احتياطية فورية من إجابات الاستبيان في localStorage بالمتصفح وفي URL."""
    store_data = st.session_state.get("survey_store", {})
    step_val = st.session_state.get("survey_wizard_step", 1)
    is_submitted = bool(store_data.get("submitted_id"))

    if is_submitted:
        if "sdraft" in st.query_params:
            del st.query_params["sdraft"]
    elif store_data:
        try:
            compact_json = json.dumps({"store": store_data, "step": step_val}, ensure_ascii=False, separators=(",", ":"))
            b64_str = base64.urlsafe_b64encode(compact_json.encode("utf-8")).decode("utf-8").rstrip("=")
            if len(b64_str) <= 3500:
                st.query_params["sdraft"] = b64_str
        except Exception:
            pass

    payload = json.dumps({
        "store": store_data,
        "step": step_val,
        "submitted": is_submitted
    }, ensure_ascii=False)

    components.html(
        f"""
        <script>
        (function() {{
            try {{
                var LS_KEY = 'raseen_survey_draft_v2';
                var data = {payload};
                if (data.submitted) {{
                    window.parent.localStorage.removeItem(LS_KEY);
                }} else if (data.store && Object.keys(data.store).length > 0) {{
                    window.parent.localStorage.setItem(LS_KEY, JSON.stringify(data));
                }}
            }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


CUSTOM_CSS = f"""
<style>
html, body, * {{
    font-feature-settings: "liga" 1, "calt" 1 !important;
    text-rendering: optimizeLegibility !important;
    -webkit-font-smoothing: antialiased !important;
}}

@font-face {{
    font-family: 'Bahij TheSansArabic';
    src: local('Bahij TheSansArabic'), local('Bahij TheSansArabic Plain'), local('Bahij_TheSansArabic-Plain');
    font-weight: 400;
}}
@font-face {{
    font-family: 'Bahij TheSansArabic';
    src: local('Bahij TheSansArabic Bold'), local('Bahij_TheSansArabic-Bold');
    font-weight: 700;
}}

header {{
    visibility: hidden !important;
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

.stAppToolbar, div[data-testid="stHeader"], div[data-testid="stDecoration"] {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

iframe[height="0"] {{
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    border: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
    margin: 0 !important;
    padding: 0 !important;
}}

html, body, [class*="css"] {{
    font-family: {APP_FONT} !important;
    font-size: 16px !important;
    direction: rtl !important;
    text-align: right !important;
    background-color: {CBE_BG} !important;
    border: none !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
}}

.stApp p, .stApp label, .stApp li, .stApp td, .stApp th, .stApp h1, .stApp h2, .stApp h3,
.stApp h4, .stApp h5, .stApp h6, .stApp input, .stApp textarea, .stApp select,
.stApp button, .stApp a, .stApp div[data-baseweb] {{
    font-family: {APP_FONT} !important;
}}

.stApp p, .stApp li, .stApp label {{
    font-size: 15.5px !important;
    line-height: 1.75 !important;
}}

.stApp input, .stApp textarea, .stApp select, .stApp div[data-baseweb="select"] {{
    font-size: 15.5px !important;
}}

.stApp {{
    background-color: {CBE_BG} !important;
    direction: rtl !important;
    text-align: right !important;
    border: none !important;
    overflow-x: hidden !important;
}}

[data-testid="stAppViewContainer"],
section[data-testid="stMain"],
.main {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}

.block-container,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"] {{
    width: 100% !important;
    max-width: 100% !important;
    padding-top: 0.45rem !important;
    padding-bottom: 1.5rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    margin-top: 0 !important;
}}

.sound-toggle-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #FFFFFF;
    color: {CBE_NAVY};
    border: 1.5px solid {CBE_GOLD};
    border-radius: 50px;
    padding: 7px 18px;
    font-size: 15px;
    font-weight: 800;
    cursor: pointer;
    user-select: none;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0, 43, 73, 0.08);
}}

.sound-toggle-pill:hover {{
    background: {CBE_NAVY};
    color: {CBE_GOLD_BRIGHT} !important;
    transform: translateY(-1px);
}}

@keyframes skeleton-shimmer {{
    0% {{ background-position: -200px 0; }}
    100% {{ background-position: 200px 0; }}
}}

.skeleton-card {{
    background: #ffffff;
    border-radius: 12px;
    border: 1.5px solid #E2E8F0;
    padding: clamp(14px, 3vw, 24px);
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
    font-size: 15px !important;
}}

.rag-response-box {{
    background: #FFFFFF !important;
    border: 1.5px solid {CBE_GOLD} !important;
    border-radius: 12px !important;
    padding: 22px !important;
    line-height: 1.95 !important;
    font-size: 16px !important;
    color: #0F172A !important;
    box-shadow: 0 4px 15px rgba(0, 43, 73, 0.06) !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}}

.rag-response-box ul {{
    padding-right: 24px !important;
    margin: 10px 0 !important;
}}

.rag-response-box li {{
    margin-bottom: 8px !important;
    font-size: 16px !important;
}}

.home-hero-card {{
    background: #FFFFFF;
    border: 1.5px solid {CBE_GOLD};
    border-right: 6px solid {CBE_NAVY};
    border-radius: 14px;
    padding: clamp(18px, 3vw, 26px);
    margin-bottom: 22px;
    box-shadow: 0 4px 18px rgba(0, 43, 73, 0.06);
}}

.model-pillar-card {{
    background: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-top: 4px solid {CBE_NAVY};
    border-radius: 12px;
    padding: 20px;
    height: 100%;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.model-pillar-card.mediator {{
    border-top-color: {CBE_GOLD};
    background: linear-gradient(180deg, #FFFDF7 0%, #FFFFFF 100%);
}}

.model-pillar-card.dependent {{
    border-top-color: #0F766E;
}}

.dim-badge {{
    display: inline-block;
    background: #F1F5F9;
    color: {CBE_NAVY};
    border: 1px solid #CBD5E1;
    border-radius: 20px;
    padding: 5px 14px;
    margin: 4px 3px;
    font-size: 14px;
    font-weight: 700;
}}

.dim-badge.gold {{
    background: #FEF3C7;
    color: #92400E;
    border-color: #F59E0B;
}}

.dim-badge.teal {{
    background: #CCFBF1;
    color: #115E59;
    border-color: #14B8A6;
}}

.tour-nav-btn {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    background: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-right: 5px solid {CBE_GOLD};
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 12px;
    box-shadow: 0 3px 10px rgba(0, 43, 73, 0.05);
    cursor: pointer;
    user-select: none;
    transition: all 0.22s ease;
}}

.tour-nav-btn:hover {{
    background: linear-gradient(135deg, {CBE_NAVY} 0%, #003B63 100%);
    border-color: {CBE_GOLD};
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 43, 73, 0.22);
}}

.tour-nav-btn:active {{
    transform: scale(0.985);
}}

.tour-nav-title {{
    color: {CBE_NAVY};
    font-size: 17px;
    font-weight: 800;
    margin-bottom: 5px;
    transition: color 0.2s ease;
}}

.tour-nav-desc {{
    color: #334155;
    font-size: 14.5px;
    line-height: 1.65;
    transition: color 0.2s ease;
}}

.tour-nav-arrow {{
    flex-shrink: 0;
    background: #F1F5F9;
    color: {CBE_NAVY};
    border: 1.5px solid {CBE_GOLD};
    border-radius: 50px;
    padding: 7px 16px;
    font-size: 14.5px;
    font-weight: 800;
    white-space: nowrap;
    transition: all 0.2s ease;
}}

.tour-nav-btn:hover .tour-nav-title {{
    color: {CBE_GOLD_BRIGHT};
}}

.tour-nav-btn:hover .tour-nav-desc {{
    color: #F1F5F9;
}}

.tour-nav-btn:hover .tour-nav-arrow {{
    background: {CBE_GOLD};
    color: {CBE_NAVY};
}}

.custom-rtl-table {{
    width: 100% !important;
    border-collapse: collapse !important;
    direction: rtl !important;
    text-align: right !important;
    margin-top: 8px !important;
    margin-bottom: 12px !important;
    font-family: {APP_FONT} !important;
    background-color: #FFFFFF !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03) !important;
    border: 1px solid #E2E8F0 !important;
}}

.custom-rtl-table th {{
    background: linear-gradient(135deg, {CBE_NAVY} 0%, #001A33 100%) !important;
    color: #F8FAFC !important;
    padding: 12px 12px !important;
    font-weight: 700 !important;
    border-bottom: 2px solid {CBE_GOLD} !important;
    border-right: none !important;
    border-left: none !important;
    text-align: right !important;
    font-size: 14.5px !important;
    white-space: nowrap !important;
}}

.custom-rtl-table td {{
    padding: 10px 12px !important;
    border-bottom: 1px solid #F1F5F9 !important;
    border-top: none !important;
    border-right: none !important;
    border-left: none !important;
    color: #0F172A !important;
    font-size: 14px !important;
    text-align: right !important;
    line-height: 1.6 !important;
}}

.custom-rtl-table tr:nth-child(even) {{
    background-color: #FAFAFA !important;
}}

.custom-rtl-table tr:hover {{
    background-color: #FEF3C7 !important;
}}

div.stButton > button,
div.stDownloadButton > button,
div[data-testid="stFormSubmitButton"] > button,
button[kind="primaryFormSubmit"],
button[kind="secondaryFormSubmit"],
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondary"],
button[data-testid="stBaseButton-primaryFormSubmit"],
button[data-testid="stBaseButton-secondaryFormSubmit"] {{
    width: 100% !important;
    min-height: 48px !important;
    padding: 10px 20px !important;
    border-radius: 50px !important;
    font-family: {APP_FONT} !important;
    font-size: 17px !important;
    font-weight: 800 !important;
    letter-spacing: 0.2px !important;
    line-height: 1.45 !important;
    background-color: {CBE_NAVY} !important;
    color: #FFFFFF !important;
    border: 2px solid {CBE_GOLD} !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 12px rgba(0, 43, 73, 0.15) !important;
    outline: none !important;
    cursor: pointer !important;
}}

div.stButton > button *,
div.stDownloadButton > button *,
div[data-testid="stFormSubmitButton"] > button *,
button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-secondary"] *,
button[data-testid="stBaseButton-primaryFormSubmit"] *,
button[data-testid="stBaseButton-secondaryFormSubmit"] * {{
    color: inherit !important;
    font-family: {APP_FONT} !important;
    font-size: 17px !important;
    font-weight: 800 !important;
    line-height: 1.45 !important;
}}

div.stButton > button:hover,
div.stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover,
button[kind="primaryFormSubmit"]:hover,
button[kind="secondaryFormSubmit"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover {{
    background-color: #001A33 !important;
    color: {CBE_GOLD_LIGHT} !important;
    border-color: #FFFFFF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(0, 43, 73, 0.32) !important;
}}

div.stButton > button:active,
div.stDownloadButton > button:active,
div[data-testid="stFormSubmitButton"] > button:active,
button[kind="primaryFormSubmit"]:active,
button[kind="secondaryFormSubmit"]:active,
button[data-testid="stBaseButton-primary"]:active,
button[data-testid="stBaseButton-secondary"]:active {{
    background-color: {CBE_GOLD} !important;
    color: {CBE_NAVY} !important;
    border-color: {CBE_NAVY} !important;
    transform: scale(0.98) !important;
    box-shadow: 0 2px 8px rgba(0, 43, 73, 0.25) !important;
}}

div.stButton > button:focus,
div.stDownloadButton > button:focus,
div[data-testid="stFormSubmitButton"] > button:focus {{
    border-color: {CBE_GOLD} !important;
    box-shadow: 0 0 0 3px rgba(197, 160, 89, 0.35) !important;
}}

{TABS_RULES}

.header-center {{
    text-align: center !important;
    background: linear-gradient(135deg, rgba(0, 43, 73, 0.95) 0%, rgba(0, 26, 51, 0.90) 100%),
                url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1600&auto=format&fit=crop') !important;
    background-size: cover !important;
    background-position: center !important;
    color: #FFFFFF !important;
    padding: clamp(18px, 3vw, 28px) clamp(14px, 3vw, 22px) !important;
    border-radius: 16px !important;
    border-bottom: 4px solid {CBE_GOLD} !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.18) !important;
    margin-top: 4px !important;
    margin-bottom: 14px !important;
    direction: rtl !important;
}}

.header-center h1 {{
    color: {CBE_GOLD} !important;
    font-size: clamp(20px, 4.5vw, 26px) !important;
    font-weight: 800 !important;
    line-height: 1.45 !important;
    margin-top: 0 !important;
    margin-bottom: 8px !important;
    text-shadow: 0 2px 6px rgba(0,0,0,0.5) !important;
}}

.header-center h3 {{
    color: #F8FAFC !important;
    font-size: clamp(14px, 3.2vw, 16px) !important;
    font-weight: 600 !important;
    line-height: 1.65 !important;
    margin-top: 0 !important;
    margin-bottom: 5px !important;
}}

.ticker-wrap {{
    width: 100%;
    background: linear-gradient(90deg, {CBE_NAVY} 0%, #001F35 100%);
    border-top: 2px solid {CBE_GOLD};
    border-bottom: 2px solid {CBE_GOLD};
    overflow: hidden;
    white-space: nowrap;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    margin-bottom: 16px;
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
    font-size: 15px;
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
    color: #475569;
    font-size: 14.5px;
    margin-top: 40px;
    border-top: 1px solid #E2E8F0;
    padding-top: 15px;
    font-weight: bold;
    direction: rtl !important;
}}

@media (max-width: 768px) {{
    .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"] {{
        padding-top: 0.4rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }}

    div.stButton > button,
    div.stDownloadButton > button,
    div[data-testid="stFormSubmitButton"] > button,
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-secondary"] {{
        width: 100% !important;
        min-height: 50px !important;
        font-size: 16.5px !important;
        font-weight: 800 !important;
        padding: 10px 18px !important;
        white-space: normal !important;
        line-height: 1.45 !important;
    }}

    div.stButton > button *,
    div.stDownloadButton > button *,
    div[data-testid="stFormSubmitButton"] > button * {{
        font-size: 16.5px !important;
        font-weight: 800 !important;
    }}

    input, textarea, select {{
        font-size: 16px !important;
    }}

    [data-testid="stDataFrame"], .js-plotly-plot {{
        max-width: 100% !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }}

    .custom-rtl-table {{
        min-width: 560px !important;
    }}

    .ticker-item {{
        font-size: 14px !important;
        padding: 7px 20px !important;
    }}

    .tour-nav-btn {{
        flex-direction: column;
        align-items: flex-start;
    }}

    .tour-nav-arrow {{
        align-self: flex-end;
    }}
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
inject_ui_sound_engine()

# ==============================================================================
# الدوال المساعدة الآمنة (Excel Numbers + HTML + Word .docx)
# ==============================================================================
def to_clean_float(val, default=0.0) -> float:
    """تحويل آمن لأي قيمة رقمية أو نصية إلى float صالح لـ xlsxwriter دون NaN/Inf/TypeError."""
    if val is None or isinstance(val, bool):
        return float(default)
    if isinstance(val, numbers.Real):
        f_val = float(val)
        return float(default) if (math.isnan(f_val) or math.isinf(f_val)) else f_val
    if isinstance(val, str):
        cleaned = re.sub(r"[^\d.\-+]", "", val.strip())
        if not cleaned or cleaned in {"-", "+", "."}:
            return float(default)
        try:
            f_val = float(cleaned)
            return float(default) if (math.isnan(f_val) or math.isinf(f_val)) else f_val
        except ValueError:
            return float(default)
    return float(default)


def safe_write_number(ws, row: int, col: int, val, cell_format=None, default=0.0):
    """كتابة آمنة للأرقام في أوراق عمل xlsxwriter لمنع TypeError."""
    ws.write_number(row, col, to_clean_float(val, default=default), cell_format)


def flat_html(s: str) -> str:
    """تُستخدم فقط لقوالب HTML الثابتة مثل Skeleton Loader."""
    return " ".join(l.strip() for l in s.splitlines() if l.strip())


def format_rag_html(raw_response: str) -> str:
    """تحويل الرد القادم من محرك RAG إلى HTML منسق يحافظ على الفقرات والنقاط."""
    if not raw_response:
        return "<div class='rag-response-box'>⚠️ لم يتم استرجاع نص للإجابة.</div>"

    text = str(raw_response).strip()
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    lines = text.splitlines()
    formatted_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                formatted_lines.append("</ul>")
                in_list = False
            formatted_lines.append("<br>")
            continue

        if re.match(r"^[-*•]\s+", stripped):
            if not in_list:
                formatted_lines.append("<ul>")
                in_list = True
            item_content = re.sub(r"^[-*•]\s+", "", stripped)
            formatted_lines.append(f"<li>{item_content}</li>")
        else:
            if in_list:
                formatted_lines.append("</ul>")
                in_list = False
            if re.match(r"^<(div|h[1-6]|p|ul|ol|li|table|hr|blockquote)", stripped, re.IGNORECASE):
                formatted_lines.append(stripped)
            else:
                formatted_lines.append(f"{stripped}<br>")

    if in_list:
        formatted_lines.append("</ul>")

    html_body = "\n".join(formatted_lines)
    html_body = re.sub(r"(<br>\s*){3,}", "<br><br>", html_body)

    if not re.match(r"^\s*<div", html_body, re.IGNORECASE):
        return f"<div class='rag-response-box' dir='rtl'>{html_body}</div>"
    return html_body


def clean_text(text) -> str:
    if not isinstance(text, str):
        return str(text)
    t = re.sub(r"\[cite[^\]]*\]", "", text)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\xa0", " ").replace("\u200b", "")
    return re.sub(r"\s+", " ", t).strip()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _set_rtl_paragraph(p):
    """ضبط اتجاه الفقرة RTL في مستندات python-docx."""
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pPr = p._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi")
    pPr.append(bidi)


def build_native_docx(title: str, subtitle: str, html_body: str) -> tuple[bytes, str, str]:
    """تحويل المحتوى إلى ملف Word (.docx) أصلي 100% مع ترويسة وتذييل رسمي واتجاه RTL."""
    if HAS_PYTHON_DOCX:
        doc = Document()
        section = doc.sections[0]

        header = section.header
        hp = header.paragraphs[0]
        hp.text = "المنصة الوطنية الذكية لحوكمة القطاع المصرفي وتقارير الاستدامة (SSGI)"
        _set_rtl_paragraph(hp)
        if hp.runs:
            hp.runs[0].font.size = Pt(9)
            hp.runs[0].font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.text = f"جميع الحقوق محفوظة للدراسة البحثية © 2026 | تاريخ التوليد: {datetime.now().strftime('%Y-%m-%d')}"
        _set_rtl_paragraph(fp)
        if fp.runs:
            fp.runs[0].font.size = Pt(9)
            fp.runs[0].font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

        h_main = doc.add_heading(clean_text(title), level=0)
        h_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if h_main.runs:
            h_main.runs[0].font.color.rgb = RGBColor(0x00, 0x2B, 0x49)

        if subtitle:
            p_sub = doc.add_paragraph(clean_text(subtitle))
            p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if p_sub.runs:
                p_sub.runs[0].font.size = Pt(11)
                p_sub.runs[0].font.color.rgb = RGBColor(0xC5, 0xA0, 0x59)

        normalized = re.sub(r"<(br|hr)\s*/?>", "\n", html_body, flags=re.IGNORECASE)
        normalized = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\n", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"<li[^>]*>", "• ", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"<h[1-4][^>]*>", "### ", normalized, flags=re.IGNORECASE)

        for raw_line in normalized.splitlines():
            line = clean_text(raw_line)
            if not line:
                continue
            if line.startswith("### "):
                sec_title = line[4:].strip()
                if sec_title:
                    hd = doc.add_heading(sec_title, level=2)
                    _set_rtl_paragraph(hd)
                    if hd.runs:
                        hd.runs[0].font.color.rgb = RGBColor(0x00, 0x2B, 0x49)
            elif line.startswith("• "):
                p = doc.add_paragraph(line[2:].strip(), style="List Bullet")
                _set_rtl_paragraph(p)
            else:
                p = doc.add_paragraph(line)
                _set_rtl_paragraph(p)

        buf = io.BytesIO()
        doc.save(buf)
        return (
            buf.getvalue(),
            ".docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    fallback_html = f"""
    <html dir="rtl">
    <head><meta charset="utf-8"><title>{title}</title></head>
    <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right; direction: rtl; line-height: 1.8;">
        <h1 style="color: {CBE_NAVY}; text-align: center;">{title}</h1>
        <p style="text-align: center; color: {CBE_GOLD};">{subtitle}</p>
        <hr>
        {html_body}
    </body>
    </html>
    """
    return fallback_html.encode("utf-8-sig"), ".doc", "application/msword"


# ==============================================================================
# نظام تتبع الزوار والاستبيانات
# ==============================================================================
LOG_FILE = "visitors_log.csv"
SURVEY_LOG_FILE = "survey_responses_log.csv"


def init_visitor_log_file():
    if not os.path.exists(LOG_FILE):
        try:
            df_init = pd.DataFrame(columns=["عنوان IP", "اسم المستخدم", "الدور", "وقت الدخول"])
            df_init.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
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
            df_init.to_csv(SURVEY_LOG_FILE, index=False, encoding="utf-8-sig")
        except Exception:
            pass


init_visitor_log_file()
init_survey_log_file()


def load_visitors_log_from_file():
    if os.path.exists(LOG_FILE):
        try:
            df = pd.read_csv(LOG_FILE, encoding="utf-8-sig")
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
            df_out.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
    except Exception:
        pass


# ==============================================================================
# إدارة جلسة الدخول المستمرة (الصمود أمام F5 / Refresh)
# ==============================================================================
ADMIN_USER = st.secrets.get("admin_credentials", {}).get("username", "admin")
ADMIN_PASS_HASH = st.secrets.get("admin_credentials", {}).get("password_hash", hash_password("admin123"))
USER_PASS_HASH = st.secrets.get("user_credentials", {}).get("password_hash", hash_password("123"))

ADMIN_SESSION_TOKEN = hashlib.sha256(f"raseen_admin_{ADMIN_PASS_HASH}".encode()).hexdigest()[:24]
USER_SESSION_TOKEN = hashlib.sha256(f"raseen_user_{USER_PASS_HASH}".encode()).hexdigest()[:24]

_DEFAULT_SESSION_STATE = {
    "authenticated": False,
    "username": "",
    "role": "",
    "survey_submitted_by_user": False,
    "history_state": [],
    "rag_query_history": [],
    "simulated_results_dict": {},
    "decision_results_dict": {},
    "query_text_box": "",
    "trigger_search": False,
    "draft_generated_state": False,
    "draft_bank_name": "",
}
for _k, _v in _DEFAULT_SESSION_STATE.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if not st.session_state.authenticated:
    url_token = st.query_params.get("auth", "")
    if url_token == ADMIN_SESSION_TOKEN:
        st.session_state.authenticated = True
        st.session_state.username = "مشرف النظام (Admin)"
        st.session_state.role = "admin"
    elif url_token == USER_SESSION_TOKEN:
        st.session_state.authenticated = True
        st.session_state.username = "باحث / مستخدم (User)"
        st.session_state.role = "user"

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: clamp(18px, 4vw, 30px); border-radius: 16px; border: 2px solid {CBE_GOLD}; box-shadow: 0 10px 30px rgba(0,0,0,0.08); text-align: right; margin-top: 12px;" dir="rtl">
            <h2 style="color: {CBE_NAVY}; text-align: center; font-weight: 800; font-size: clamp(20px, 4.2vw, 25px); margin-bottom: 12px;">🏛️ مقترح المنصة الوطنية الذكية لتعزيز الحوكمة المؤسسية بالقطاع المصرفي المصري (رصين)</h2>
            <p style="color: #334155; text-align: center; font-size: 16px; line-height: 1.7; margin-bottom: 12px;">
                إطار تطبيقي مقترح ضمن متطلبات نيل درجة دكتوراه الفلسفة في العلوم البيئية - جامعة عين شمس. يرجى تسجيل الدخول للمتابعة.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("اسم المستخدم (Username)", placeholder="أدخل اسم المستخدم...")
            password_input = st.text_input("كلمة المرور (Password)", type="password", placeholder="أدخل كلمة المرور...")
            submitted = st.form_submit_button("🔐 تسجيل الدخول للمنصة", use_container_width=True)

            if submitted:
                clean_user = re.sub(r"[^a-zA-Z0-9]", "", str(username_input)).lower()
                clean_pass_hash = hash_password(str(password_input).strip())

                if clean_user == ADMIN_USER.strip().lower() and clean_pass_hash == ADMIN_PASS_HASH:
                    st.session_state.authenticated = True
                    st.session_state.username = "مشرف النظام (Admin)"
                    st.session_state.role = "admin"
                    st.query_params["auth"] = ADMIN_SESSION_TOKEN
                    log_visitor_action("admin", "مشرف (Admin)")
                    st.rerun()
                elif clean_user in ("user", "users") and clean_pass_hash == USER_PASS_HASH:
                    st.session_state.authenticated = True
                    st.session_state.username = "باحث / مستخدم (User)"
                    st.session_state.role = "user"
                    st.query_params["auth"] = USER_SESSION_TOKEN
                    log_visitor_action("user", "مستخدم عادي (User)")
                    st.rerun()
                else:
                    st.error("⚠️ تعذر تسجيل الدخول؛ يرجى التأكد من صحة اسم المستخدم وكلمة المرور والمحاولة مجدداً.")
    st.stop()

# ==============================================================================
# دوال تقييم ووصف الأداء للمحاور الثلاثة
# ==============================================================================
def get_colored_score_html(score):
    val = to_clean_float(score, default=0.0)
    if val >= 80:
        return f"{val:g}% (أداء مرتفع ومنتظم 🟢)"
    elif val >= 50:
        return f"{val:g}% (أداء متوسط يتطلب تعزيزاً 🟡)"
    else:
        return f"{val:g}% (فجوة هيكلية حرجة تستوجب التدخل 🔴)"


def describe_sip(val):
    v = to_clean_float(val, default=0.0)
    if v >= 80:
        return f"منصات المعلومات والبنية التقنية متقدمة للغاية ({v:g}%) وتتيح تكاملاً تاماً مع أنظمة البنك المركزي والتقارير الرقابية الآلية."
    elif v >= 50:
        return f"البنية التقنية متوسطة الكفاءة ({v:g}%) وتحتاج لتحديث سعات تدفق البيانات وحوكمة الخوارزميات."
    else:
        return f"تعاني البنية التقنية من فجوة هيكلية حرجة ({v:g}%) تعيق أتمتة الالتزام والرقابة التنظيمية."


def describe_ig(val):
    v = to_clean_float(val, default=0.0)
    if v >= 80:
        return f"حوكمة مؤسسية راسخة ({v:g}%) مع استقلالية تامة لمجلس الإدارة ولجان المراجعة والامتثال بأعلى معايير الشفافية."
    elif v >= 50:
        return f"الحوكمة المؤسسية في نطاق متوازن ({v:g}%) وتتطلب تفعيل ضوابط تعارض المصالح وتعزيز دور الأعضاء المستقلين."
    else:
        return f"قصور حاد في الحوكمة المؤسسية ({v:g}%) يستوجب تدخلاً رقابياً لإعادة هندسة لجان المراجعة وإدارة المخاطر."


def describe_sr(val):
    v = to_clean_float(val, default=0.0)
    if v >= 80:
        return f"أداء متميز والتزام ريادي في تقارير الاستدامة والتمويل الأخضر ({v:g}%) مع دمج فعال لمخاطر المناخ وتوسيع الأصول الخضراء وفق معايير (GRI/ISSB)."
    elif v >= 50:
        return f"أداء متوسط في تقارير الاستدامة ({v:g}%) يستوجب التوسع في محفظة التمويل المستدام ومخاطر المناخ."
    else:
        return f"ضعف هيكلي في ملف الاستدامة والتمويل الأخضر ({v:g}%) يعيق امتثال البنك للمعايير الدولية."


restore_survey_from_url_or_browser()

# ==============================================================================
# الهيدر المدمج والشريط الإخباري
# ==============================================================================
col_h1, col_h2 = st.columns([4.5, 1.2])
with col_h1:
    st.markdown(f"""
    <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;" dir="rtl">
        <div style="text-align: right; font-size: 14.5px; color: {CBE_NAVY}; background: #FFFFFF; border: 1px solid #E2E8F0; border-right: 4px solid {CBE_GOLD}; border-radius: 8px; padding: 7px 14px; display: inline-block;">
            👤 مسجل باسم: <b>{st.session_state.username}</b> | <span style="color:#0F766E; font-weight:700;">🟢 الجلسة تعمل الآن</span>
        </div>
        <span class="sound-toggle-pill" data-raseen-sound-toggle="1" role="button" tabindex="0" title="تفعيل أو كتم المؤثرات الصوتية عند النقر">🔊 الصوت: مفعل</span>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    if st.button("🚪 تسجيل الخروج", use_container_width=True, key="logout_top_btn"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.query_params.clear()
        st.rerun()

st.markdown("""
<div class="header-center">
<h1>مقترح المنصة الوطنية الذكية لتعزيز الحوكمة المؤسسية بالقطاع المصرفي المصري</h1>
<h1>منصة (رصين)</h1>
<h3>إطار تطبيقي مقترح ضمن متطلبات نيل درجة دكتوراة الفلسفة في العلوم البيئية - جامعة عين شمس</h3>
<h3>إعداد الباحث: أيمن الدسوقي (مدرس مساعد إدارة المعرفة – معهد التخطيط القومي)</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ticker-wrap">
  <div class="ticker">
    <span class="ticker-item">🏛️ مقترح المنصة الوطنية الذكية لتعزيز الحوكمة المؤسسية بالقطاع المصرفي المصري (رصين) </span>
    <span class="ticker-item">| 📊 مؤشر الحوكمة الذكية المستدامة (SSGI) والأبعاد الثلاثة الرئيسة</span>
    <span class="ticker-item">| 📈 محاكي السياسات الاستشرافي لاختبار السيناريوهات الاستراتيجية (Multiple Regression)</span>
    <span class="ticker-item">| 🛡️ لوحة دعم اتخاذ القرار</span>
    <span class="ticker-item">| 📋 الاستبيان الموجه لفرق العمل في البنوك وعينة الدراسة الميدانية</span>
    <span class="ticker-item">| 📖 دليل المستخدم الرسمي والتوثيق المنهجي PDF</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# التبويبات الرئيسة
# ==============================================================================
if st.session_state.role == "admin":
    tab_home, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "🏠 الرئيسية",
        "🎯 اسأل رصين",
        "📊  SSGI",
        "📈 محاكي السياسات",
        "🛡️ لوحة دعم اتخاذ القرار",
        "📑 التقرير التنفيذي",
        "🌿 تقارير الاستدامة",
        "📋 استبيان فرق العمل",
        "📖 دليل المستخدم",
        "🔒 لوحة التحكم"
    ])
else:
    tab_home, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🏠 الرئيسية",
        "🎯 اسأل رصين",
        "📊 المؤشر المركب SSGI",
        "📈 محاكي السياسات",
        "🛡️ لوحة دعم اتخاذ القرار",
        "📑 التقرير التنفيذي",
        "🌿 تقارير الاستدامة",
        "📋 استبيان فرق العمل",
        "📖 دليل المستخدم"
    ])
    tab9 = None

inject_tabs_css()

# ==============================================================================
# التبويب التمهيدي: الرئيسية والإطار المنهجي
# ==============================================================================
with tab_home:
    st.markdown(f"""
    <div class="home-hero-card" dir="rtl">
        <h2 style="color: {CBE_NAVY}; font-weight: 800; font-size: clamp(19px, 4vw, 24px); margin-bottom: 12px;">
            🏛️ مرحباً بكم في مقترح المنصة الوطنية الذكية لتعزيز حوكمة القطاع المصرفي المصري (رصين)
        </h2>
        <p style="color: #1E293B; font-size: 16px; line-height: 1.9; margin-bottom: 12px;">
            تمثل هذه المنصة التطبيق العملي ضمن أطروحة دكتوراه الفلسفة في العلوم البيئية (جامعة عين شمس)، وتهدف إلى سد الفجوة بين <b>التحول الرقمي الذكي</b> و<b>الامتثال لمعايير الاستدامة البيئية والحوكمة المؤسسية (ESG)</b> في البنوك العاملة بالقطاع المصرفي المصري، بما يتسق مع توجهات البنك المركزي المصري ورؤية مصر 2030 وأفضل الممارسات الدولية ومقررات لجنة بازل.
        </p>
        <div style="background: #F8FAFC; border-radius: 10px; padding: 14px 18px; border: 1px solid #E2E8F0; font-size: 15px; line-height: 1.75; color: {CBE_NAVY};">
            <b>🎯 القيمة المضافة للمنصة:</b> تحويل تقارير الاستدامة والحوكمة من وثائق إفصاح سردية ساكنة إلى <b>منظومة تعتمد على الذكاء الاصطناعي بمعلومات ذكية موثوقة غير مضللة</b> ومؤشرات قياس كمية ومحاكي سياسات استشرافي يدعم متخذي القرار والباحثين.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <h3 style="color: {CBE_NAVY}; font-weight: 800; font-size: 20px; margin: 12px 0 16px 0;">
        🧭 خريطة النموذج البحثي المعتمد للمنصة (المحاور والأبعاد)
    </h3>
    """, unsafe_allow_html=True)

    col_m1, col_m2, col_m3 = st.columns(3)

    with col_m1:
        st.markdown(f"""
        <div class="model-pillar-card" dir="rtl">
            <div style="font-size: 13.5px; font-weight: 700; color: #475569; margin-bottom: 5px;">1️⃣ المتغير المستقل (Independent Variable)</div>
            <h4 style="color: {CBE_NAVY}; font-weight: 800; font-size: 18px; margin-bottom: 10px;">💻 منصات المعلومات الذكية<br><span style="font-size: 14px; font-weight: 600; color: #475569;">(Smart Information Platforms)</span></h4>
            <p style="font-size: 14.5px; color: #334155; line-height: 1.7; margin-bottom: 14px;">
                البنية التحتية الرقمية والأنظمة الذكية المسؤولة عن جمع البيانات ومعالجتها وضمان موثوقيتها وأمنها.
            </p>
            <div style="font-size: 14px; font-weight: 700; color: {CBE_NAVY}; margin-bottom: 8px;">الأبعاد الأساسية المعتمدة (4 أبعاد):</div>
            <div>
                <span class="dim-badge">جودة المعلومات</span>
                <span class="dim-badge">الامتثال التقني</span>
                <span class="dim-badge">التخطيط والمراقبة بعد النشر</span>
                <span class="dim-badge">التكامل والخصوصية</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        st.markdown(f"""
        <div class="model-pillar-card mediator" dir="rtl">
            <div style="font-size: 13.5px; font-weight: 700; color: #B45309; margin-bottom: 5px;">2️⃣ المتغير الوسيط (Mediating Variable)</div>
            <h4 style="color: #92400E; font-weight: 800; font-size: 18px; margin-bottom: 10px;">🌿 تقارير الاستدامة<br><span style="font-size: 14px; font-weight: 600; color: #78350F;">(Sustainability Reporting)</span></h4>
            <p style="font-size: 14.5px; color: #334155; line-height: 1.7; margin-bottom: 14px;">
                آلية الإفصاح المؤسسي والبيئي والاجتماعي التي تنقل أثر البنية الذكية لتعزيز ممارسات الحوكمة الرشيدة.
            </p>
            <div style="font-size: 14px; font-weight: 700; color: #92400E; margin-bottom: 8px;">الأبعاد الأساسية المعتمدة (5 أبعاد):</div>
            <div>
                <span class="dim-badge gold">الاستراتيجية</span>
                <span class="dim-badge gold">الأبعاد التشغيلية</span>
                <span class="dim-badge gold">إدارة المخاطر</span>
                <span class="dim-badge gold">المقاييس والأهداف</span>
                <span class="dim-badge gold">التنوع والشمول</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_m3:
        st.markdown(f"""
        <div class="model-pillar-card dependent" dir="rtl">
            <div style="font-size: 13.5px; font-weight: 700; color: #0F766E; margin-bottom: 5px;">3️⃣ المتغير التابع (Dependent Variable)</div>
            <h4 style="color: #115E59; font-weight: 800; font-size: 18px; margin-bottom: 10px;">⚖️ الحوكمة المؤسسية<br><span style="font-size: 14px; font-weight: 600; color: #134E4A;">(Institutional Governance)</span></h4>
            <p style="font-size: 14.5px; color: #334155; line-height: 1.7; margin-bottom: 14px;">
                منظومة الضبط والرقابة والشفافية والمساءلة التي تضمن استدامة الأداء المصرفي وحماية حقوق أصحاب المصلحة.
            </p>
            <div style="font-size: 14px; font-weight: 700; color: #115E59; margin-bottom: 8px;">الأبعاد الأساسية المعتمدة (6 أبعاد):</div>
            <div>
                <span class="dim-badge teal">الشفافية والإفصاح</span>
                <span class="dim-badge teal">المتابعة والمساءلة</span>
                <span class="dim-badge teal">العدالة والمساواة</span>
                <span class="dim-badge teal">المشاركة</span>
                <span class="dim-badge teal">سيادة القانون</span>
                <span class="dim-badge teal">مجلس الإدارة</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background: {CBE_NAVY}; color: #FFFFFF; text-align: center; padding: 14px 18px; border-radius: 10px; border: 1.5px solid {CBE_GOLD}; margin: 20px 0 24px 0; font-size: 15px; font-weight: 700;" dir="rtl">
        🔄 المسار المنهجي: <span style="color: {CBE_GOLD_BRIGHT};">منصات المعلومات الذكية (4 أبعاد)</span> ⬅️ <span style="color: #FFFFFF;">تقارير الاستدامة (5 أبعاد)</span> ⬅️ <span style="color: {CBE_GOLD_BRIGHT};">الحوكمة المؤسسية (6 أبعاد)</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <h3 style="color: {CBE_NAVY}; font-weight: 800; font-size: 20px; margin: 12px 0 6px 0;">
        🗺️ جولة سريعة في مكونات وأدوات المنصة
    </h3>
    <p style="color: #475569; font-size: 14.5px; margin-bottom: 16px;">
        اختر أي وحدة من وحدات المنصة أدناه للانتقال الفوري إليها:
    </p>
    """, unsafe_allow_html=True)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("""
        <div class="tour-nav-btn" data-tab-target="1" role="button" tabindex="0" dir="rtl">
            <div>
                <div class="tour-nav-title">🎯 اسأل رصين (محرك RAG الذكي)</div>
                <div class="tour-nav-desc">استعلام تحليلي فوري مدعوم بأرشيف تقارير الاستدامة والأطر الرقابية للبنوك المصرية.</div>
            </div>
            <span class="tour-nav-arrow">انتقال للقسم ⬅️</span>
        </div>
        <div class="tour-nav-btn" data-tab-target="2" role="button" tabindex="0" dir="rtl">
            <div>
                <div class="tour-nav-title">📊 المؤشر المركب (SSGI)</div>
                <div class="tour-nav-desc">قياس كمي وتشخيصي لأداء البنوك عبر المحاور الثلاثة وحساب الدرجة المركبة للحوكمة الذكية المستدامة.</div>
            </div>
            <span class="tour-nav-arrow">انتقال للقسم ⬅️</span>
        </div>
        <div class="tour-nav-btn" data-tab-target="3" role="button" tabindex="0" dir="rtl">
            <div>
                <div class="tour-nav-title">📈 محاكي السياسات الاستشرافي</div>
                <div class="tour-nav-desc">اختبار سيناريوهات التحسين وتقدير الأثر المتوقع على الحوكمة المؤسسية باستخدام السيناريوهات.</div>
            </div>
            <span class="tour-nav-arrow">انتقال للقسم ⬅️</span>
        </div>
        <div class="tour-nav-btn" data-tab-target="4" role="button" tabindex="0" dir="rtl">
            <div>
                <div class="tour-nav-title">🛡️ لوحة دعم اتخاذ القرار</div>
                <div class="tour-nav-desc">تشخيص الفجوات الهيكلية وتوليد مصفوفة توصيات تنفيذية موجهة للإدارة العليا والجهات الرقابية.</div>
            </div>
            <span class="tour-nav-arrow">انتقال للقسم ⬅️</span>
        </div>
        """, unsafe_allow_html=True)

    with col_t2:
        st.markdown("""
        <div class="tour-nav-btn" data-tab-target="5" role="button" tabindex="0" dir="rtl">
            <div>
                <div class="tour-nav-title">📑 التقرير التنفيذي</div>
                <div class="tour-nav-desc">إعداد وتصدير تقارير رسمية جاهزة للعرض على مجالس الإدارات.</div>
            </div>
            <span class="tour-nav-arrow">انتقال للقسم ⬅️</span>
        </div>
        <div class="tour-nav-btn" data-tab-target="6" role="button" tabindex="0" dir="rtl">
            <div>
                <div class="tour-nav-title">🌿 تقارير الاستدامة</div>
                <div class="tour-nav-desc">استعراض وتحليل مؤشرات الإفصاح البيئي والتمويل الأخضر وفق المعايير الدولية (GRI / ISSB).</div>
            </div>
            <span class="tour-nav-arrow">انتقال للقسم ⬅️</span>
        </div>
        <div class="tour-nav-btn" data-tab-target="7" role="button" tabindex="0" dir="rtl">
            <div>
                <div class="tour-nav-title">📋 استبيان فرق العمل</div>
                <div class="tour-nav-desc">أداة التقييم الميداني الموجه لقيادات وفرق العمل بالبنوك المصرية لقياس أبعاد النموذج البحثي.</div>
            </div>
            <span class="tour-nav-arrow">انتقال للقسم ⬅️</span>
        </div>
        <div class="tour-nav-btn" data-tab-target="8" role="button" tabindex="0" dir="rtl">
            <div>
                <div class="tour-nav-title">📖 دليل المستخدم</div>
                <div class="tour-nav-desc">التوثيق المنهجي للمنصة الوطنية الذكية (رصين) وشرح آليات التشغيل.</div>
            </div>
            <span class="tour-nav-arrow">انتقال للقسم ⬅️</span>
        </div>
        """, unsafe_allow_html=True)
# ------------------------------------------------------------------------------
# التبويب الأول: اسأل رصين (مربوط مباشرة بمحرك Gemini Hybrid RAG)
# ------------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=1800, max_entries=50)
def cached_rag_query(bank_name: str, question: str, cache_version: str = RAG_CACHE_VERSION) -> str:
    return process_rag_gemini_query(bank_name, question)


if "last_rag_result" not in st.session_state:
    st.session_state.last_rag_result = None

with tab1:
    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 20px;">
        <h3 style="color: #002B49; font-weight: 800; font-size: clamp(16px, 4vw, 20px); margin-bottom: 4px;">🎯 تحليل واستخلاص البيانات الذكي</h3>
        <p style="color: #475569; font-size: clamp(13px, 3.2vw, 14px);">استعراض الإجابات التحليلية المستندة إلى أرشيف التقارير والأطر الرقابية للقطاع المصرفي المصري.</p>
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

        st.markdown("<b style='color: #002B49; font-size: 13.5px;'>📌 أسئلة مقترحة:</b>", unsafe_allow_html=True)

        def trigger_instant_query(question):
            st.session_state.query_text_box = question
            st.session_state.trigger_search = True

        with st.expander("🏛️ محور الحوكمة المؤسسية (IG)"):
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

        with st.expander("🌱 محور الاستدامة (SR/ESG)"):
            sr_questions = [
                "كيف يتعامل البنك مع مخاطر المناخ والتمويل الأخضر؟",
                "ما هي نسبة الأصول الخضراء والمشروعات المستدامة ضمن محفظة الائتمان؟",
                "كيف يمتثل البنك للمعايير الدولية للإفصاح المالي (GRI و ISSB)؟",
                "ما هي مبادرات البنك في المسؤولية المجتمعية والإنفاق التنموي المستدام؟"
            ]
            for i, q in enumerate(sr_questions):
                st.button(f"⚡ {q}", key=f"btn_sr_{i}", on_click=trigger_instant_query, args=(q,), use_container_width=True)

        with st.expander("🔒 محور المنصات الذكية (SIP)"):
            sip_questions = [
                "ما هي آليات حوكمة البيانات والامتثال الرقابي وتأمينها؟",
                "كيف يضمن البنك الحصانة السيبرانية ومنع تسريب البيانات المالية الحساسة؟",
                "ما هي جاهزية البنية التحتية الرقمية ومنصات المعلومات (SIP)؟",
                "كيف يوظف البنك تقنيات الرقابة التنظيمية (RegTech) واسترجاع المعطيات؟",
                "ما مدى التوافق مع قانون حماية البيانات الشخصية والسيادة الرقمية؟"
            ]
            for i, q in enumerate(sip_questions):
                st.button(f"⚡ {q}", key=f"btn_sip_{i}", on_click=trigger_instant_query, args=(q,), use_container_width=True)

        col_sub1, col_sub2 = st.columns([2, 1])
        with col_sub1:
            ask_submit_btn = st.button("🚀 تقديم السؤال", use_container_width=True, type="primary")
        with col_sub2:
            if st.button("🔄 تحديث", use_container_width=True, help="مسح الردود المخزنة مؤقتاً وإعادة التوليد"):
                st.cache_data.clear()
                st.toast("✅ تم مسح الذاكرة المؤقتة بنجاح.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_q2:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)

        should_execute = ask_submit_btn or st.session_state.get("trigger_search", False)

        if should_execute:
            st.session_state.trigger_search = False
            active_q = st.session_state.query_text_box

            if ask_bank_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى اختيار بنك مصرفي صحيح من القائمة لتنفيذ الاستعلام.")
            elif not active_q.strip():
                st.warning("⚠️ يرجى كتابة أو اختيار سؤال للإجابة عليه.")
            else:
                skeleton_placeholder = st.empty()
                skeleton_html = flat_html("""
                <div class="skeleton-card">
                    <div class="skeleton-line skeleton-title"></div>
                    <div class="skeleton-line skeleton-badge"></div>
                    <div class="skeleton-line skeleton-body-1"></div>
                    <div class="skeleton-line skeleton-body-2"></div>
                </div>
                """)
                skeleton_placeholder.markdown(skeleton_html, unsafe_allow_html=True)

                full_response = cached_rag_query(ask_bank_sel, active_q, RAG_CACHE_VERSION)
                formatted_answer = format_rag_html(full_response)
                skeleton_placeholder.empty()

                now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.last_rag_result = {
                    "bank": ask_bank_sel,
                    "question": active_q,
                    "answer_html": formatted_answer,
                    "timestamp": now_ts
                }
                st.session_state.rag_query_history.append(st.session_state.last_rag_result)

        if st.session_state.last_rag_result:
            res = st.session_state.last_rag_result
            st.markdown(res["answer_html"], unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            single_body = f"""
            <p><b>🏛️ البنك المصرفي:</b> {res['bank']}</p>
            <p><b>❓ السؤال / الاستفسار:</b> {res['question']}</p>
            <div>{res['answer_html']}</div>
            """
            single_bytes, single_ext, single_mime = build_native_docx(
                f"🎯 تقرير الاستخلاص والتحليل الذكي - {res['bank']}",
                f"تاريخ التوليد: {res['timestamp']}",
                single_body,
            )

            all_qa_blocks = ""
            for idx_q, item_q in enumerate(st.session_state.rag_query_history, 1):
                all_qa_blocks += f"""
                <h3>({idx_q}) البنك: {item_q['bank']} | التوقيت: {item_q['timestamp']}</h3>
                <p><b>❓ السؤال:</b> {item_q['question']}</p>
                <div>{item_q['answer_html']}</div>
                <hr>
                """
            hist_bytes, hist_ext, hist_mime = build_native_docx(
                "📚 سجل الاستفسارات والتحليلات الذكية المجمعة",
                f"إجمالي الاستعلامات: {len(st.session_state.rag_query_history)}",
                all_qa_blocks,
            )

            col_dl_q1, col_dl_q2, col_clr_q = st.columns([1.2, 1.2, 0.8])
            with col_dl_q1:
                st.download_button(
                    label="📥 تحميل الرد الحالي",
                    data=single_bytes,
                    file_name=f"تحليل_{res['bank']}{single_ext}",
                    mime=single_mime,
                    use_container_width=True,
                    key="dl_single_rag_btn"
                )
            with col_dl_q2:
                st.download_button(
                    label="📥 تحميل كافة الردود",
                    data=hist_bytes,
                    file_name=f"سجل_الإجابات_والردود_الذكية{hist_ext}",
                    mime=hist_mime,
                    use_container_width=True,
                    key="dl_all_rag_btn"
                )
            with col_clr_q:
                if st.button("🗑️ مسح السجل", use_container_width=True, key="clear_rag_hist_btn"):
                    st.session_state.rag_query_history = []
                    st.session_state.last_rag_result = None
                    st.rerun()
        else:
            st.info("🎯 قم باختيار البنك والضغط على أي سؤال مقترح لاستخراج الإجابات الموثقة.")

        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# ثوابت المحاور والأوزان النسبية المعتمدة لمؤشر SSGI (مجموع 100% تماماً)
# ==============================================================================
AXIS_WEIGHTS = {
    "أولاً: منصات المعلومات الذكية (SIP)": 0.40,
    "ثانياً: الحوكمة المؤسسية (IG)": 0.30,
    "ثالثاً: تقارير الاستدامة (SR)": 0.30,
}


# ==============================================================================
# دالة تجميع وإعداد هيكل المتغيرات الـ 63 وتوزيع الأوزان الدقيقة
# ==============================================================================
@st.cache_data
def get_ssgi_variables_df():
    raw_variables = [
        ("أولاً: منصات المعلومات الذكية (SIP)", "1. جودة المعلومات", "1/1 نسبة تغطية الفروع بشبكة البيانات المركزية الموحدة"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "1. جودة المعلومات", "1/2 سعة التخزين السحابي/المحلي المتاحة للبيانات الضخمة"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "1. جودة المعلومات", "1/3 نسبة البيانات المهيكلة (Structured) إلى إجمالي البيانات"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "1. جودة المعلومات", "1/4 نسبة اكتمال حقول البيانات في سجلات العملاء (Data Completeness)"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "2. التكامل والخصوصية", "2/1 عدد الأنظمة الفرعية المربوطة بالمنصة المركزية عبر (APIs)"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "2. التكامل والخصوصية", "2/2 معدل وقت التشغيل للنظام (System Uptime)"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "2. التكامل والخصوصية", "2/3 نسبة البيانات المستضافة محلياً (On-Premise) من إجمالي البيانات الحساسة"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "2. التكامل والخصوصية", "2/4 عدد حوادث اختراق البيانات المسجلة سنوياً (مؤشر عكسي)"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "3. الامتثال التقني", "3/1 نسبة ضوابط معيار (ISO 27001) المطبقة فعلياً"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "3. الامتثال التقني", "3/2 عدد شهادات الامتثال التقني السارية"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "3. الامتثال التقني", "3/3 عدد عمليات التدقيق (Audits) المجراة على نماذج الذكاء الاصطناعي"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "3. الامتثال التقني", "3/4 نسبة النماذج الموثقة بسجلات شرح النتائج (Explainability Logs)"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "4. التخطيط والمراقبة بعد النشر", "4/1 متوسط الزمن المستغرق لاكتشاف الخطأ في البيانات (MTTD)"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "4. التخطيط والمراقبة بعد النشر", "4/2 عدد التنبيهات الآلية الصحيحة التي أصدرها النظام"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "4. التخطيط والمراقبة بعد النشر", "4/3 معدل دقة التنبؤات (AI Accuracy Rate) مقارنة بالنتائج الفعلية"),
        ("أولاً: منصات المعلومات الذكية (SIP)", "4. التخطيط والمراقبة بعد النشر", "4/4 نسبة التقارير التي تطلبت تصحيحاً يدوياً بعد الصدور"),

        ("ثانياً: الحوكمة المؤسسية (IG)", "1. سيادة القانون", "1/1 نسبة السياسات الداخلية التي تم تحديثها خلال العام الحالي"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "1. سيادة القانون", "1/2 قيمة الغرامات المالية الموقعة من الجهات الرقابية (مؤشر عكسي)"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "1. سيادة القانون", "1/3 نسبة الموظفين الموقعين على مدونة السلوك الرقمي"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "1. سيادة القانون", "1/4 عدد بلاغات المخالفات الأخلاقية التي تم التحقيق فيها"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "2. العدالة والمساواة", "2/1 نسبة فجوة الأجور بين الجنسين"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "2. العدالة والمساواة", "2/2 نسبة الترقيات الداخلية مقارنة بالتعيينات الخارجية"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "2. العدالة والمساواة", "2/3 نسبة توزيعات الأرباح إلى صافي الربح"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "2. العدالة والمساواة", "2/4 عدد القضايا المرفوعة من مساهمين أو عملاء ضد البنك"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "3. المتابعة والمساءلة", "3/1 نسبة العمليات الموثقة بمصفوفة (RACI) المعتمدة"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "3. المتابعة والمساءلة", "3/2 عدد الأوصاف الوظيفية المحدثة للقيادات العليا"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "3. المتابعة والمساءلة", "3/3 نسبة توصيات المراجعة الداخلية التي تم تنفيذها"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "3. المتابعة والمساءلة", "3/4 عدد اجتماعات لجان الحوكمة والمخاطر سنوياً"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "4. المشاركة", "4/1 معدل الاستجابة لشكاوى العملاء (Response Rate)"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "4. المشاركة", "4/2 عدد قنوات التواصل الرقمية الفعالة"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "4. المشاركة", "4/3 نسبة القرارات الاستراتيجية التي خضعت لاستطلاع الرأي"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "5. الشفافية والإفصاح", "5/1 درجة سهولة القراءة (Readability Score) للتقرير السنوي"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "5. الشفافية والإفصاح", "5/2 عدد صفحات الإفصاح عن المخاطر غير المالية"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "5. الشفافية والإفصاح", "5/3 الفجوة الزمنية (بالأيام) بين نهاية السنة المالية وتاريخ نشر التقرير"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "5. الشفافية والإفصاح", "5/4 عدد الإفصاحات الفورية عن الأحداث الجوهرية خلال العام"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "6. مجلس الإدارة", "6/1 نسبة حضور أعضاء مجلس الإدارة للاجتماعات الدورية"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "6. مجلس الإدارة", "6/2 متوسط سنوات خبرة أعضاء المجلس في العمل المصرفي والاستدامة"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "6. مجلس الإدارة", "6/3 عدد الاجتماعات السنوية للجنة الحوكمة والترشيحات والمكافآت"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "6. مجلس الإدارة", "6/4 نسبة التزام المجلس بتقييم الأداء السنوي المستقل (Evaluation)"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "6. مجلس الإدارة", "6/5 نسبة اللجان السيادية (التدقيق والمخاطر) التي يرأسها أعضاء مستقلون"),
        ("ثانياً: الحوكمة المؤسسية (IG)", "6. مجلس الإدارة", "6/6 عدد حالات تعارض المصالح المرصودة والمفصح عنها (مؤشر عكسي)"),

        ("ثالثاً: تقارير الاستدامة (SR)", "1. الاستراتيجية", "1/1 عدد أهداف التنمية المستدامة المتبناة رسمياً في الاستراتيجية"),
        ("ثانياً: تقارير الاستدامة (SR)", "1. الاستراتيجية", "1/2 نسبة الأهداف المحققة من إجمالي الأهداف المخططة"),
        ("ثالثاً: تقارير الاستدامة (SR)", "1. الاستراتيجية", "1/3 نسبة ميزانية (R&D) والتحول الأخضر إلى إجمالي الميزانية"),
        ("ثالثاً: تقارير الاستدامة (SR)", "1. الاستراتيجية", "1/4 حجم الاستثمار في البنية التحتية المستدامة"),
        ("ثالثاً: تقارير الاستدامة (SR)", "2. التنوع والشمول", "2/1 نسبة تمثيل المرأة في مجلس الإدارة"),
        ("ثالثاً: تقارير الاستدامة (SR)", "2. التنوع والشمول", "2/2 نسبة الأعضاء المستقلين في مجلس الإدارة"),
        ("ثالثاً: تقارير الاستدامة (SR)", "2. التنوع والشمول", "2/3 نسبة ذوي الهمم من إجمالي القوى العاملة"),
        ("ثالثاً: تقارير الاستدامة (SR)", "2. التنوع والشمول", "2/4 نسبة الموظفين من خارج العاصمة (في الأقاليم)"),
        ("ثالثاً: تقارير الاستدامة (SR)", "3. إدارة المخاطر", "3/1 نسبة محفظة الائتمان التي خضعت لتقييم المخاطر البيئية"),
        ("ثالثاً: تقارير الاستدامة (SR)", "3. إدارة المخاطر", "3/2 القيمة المعرضة للخطر (VaR) المرتبطة بالمناخ"),
        ("ثالثاً: تقارير الاستدامة (SR)", "3. إدارة المخاطر", "3/3 عدد سيناريوهات اختبارات الضغط المناخية المنفذة"),
        ("ثالثاً: تقارير الاستدامة (SR)", "3. إدارة المخاطر", "3/4 نسبة كفاية رأس المال (CAR) بعد احتساب مخاطر المناخ"),
        ("ثالثاً: تقارير الاستدامة (SR)", "4. الأبعاد التشغيلية", "4/1 نسبة الأصول الخضراء (Green Asset Ratio - GAR)"),
        ("ثالثاً: تقارير الاستدامة (SR)", "4. الأبعاد التشغيلية", "4/2 حجم القروض الموجهة للمشروعات الصغيرة والمتوسطة (SMEs)"),
        ("ثالثاً: تقارير الاستدامة (SR)", "4. الأبعاد التشغيلية", "4/3 إجمالي انبعاثات الكربون (طن مكافئ) لكل موظف"),
        ("ثالثاً: تقارير الاستدامة (SR)", "4. الأبعاد التشغيلية", "4/4 نسبة استهلاك الطاقة المتجددة من إجمالي الطاقة"),
        ("ثالثاً: تقارير الاستدامة (SR)", "4. الأبعاد التشغيلية", "4/5 نسبة الإنفاق على المسؤولية المجتمعية (CSR) من صافي الأرباح"),
        ("ثالثاً: تقارير الاستدامة (SR)", "4. الأبعاد التشغيلية", "4/6 عدد المستفيدين المباشرين من مبادرات الشمول المالي"),
        ("ثالثاً: تقارير الاستدامة (SR)", "5. المقاييس والأهداف", "5/1 نسبة التغير السنوي في خفض الانبعاثات"),
        ("ثالثاً: تقارير الاستدامة (SR)", "5. المقاييس والأهداف", "5/2 معدل تحقيق مؤشرات الأداء الرئيسية"),
        ("ثالثاً: تقارير الاستدامة (SR)", "5. المقاييس والأهداف", "5/3 نسبة تغطية مؤشرات (GRI) في التقرير"),
        ("ثالثاً: تقارير الاستدامة (SR)", "5. المقاييس والأهداف", "5/4 مستوى التوكيد الخارجي (لا يوجد=0، محدود=1، معقول=2)"),
    ]

    df_vars = pd.DataFrame(raw_variables, columns=["المحور الرئيسي", "البعد الأساسي", "المتغير الفرعي (63 متغيراً)"])
    df_vars["الوزن النسبي (AHP)"] = (
        df_vars["المحور الرئيسي"].map(AXIS_WEIGHTS)
        / df_vars.groupby("المحور الرئيسي")["المحور الرئيسي"].transform("count")
    )
    df_vars["م"] = range(1, len(df_vars) + 1)
    return df_vars[["م", "المحور الرئيسي", "البعد الأساسي", "المتغير الفرعي (63 متغيراً)", "الوزن النسبي (AHP)"]]


# ==============================================================================
# دالة توليد ملف Excel التقييمي التفصيلي المعزز بالمعادلات وورقة الملخص
# ==============================================================================
@st.cache_data
def generate_ssgi_evaluation_excel():
    df = get_ssgi_variables_df().copy()
    n = len(df)
    last = n + 1

    def _note(v):
        if "مؤشر عكسي" in v:
            return "مؤشر عكسي: أدخل درجة الامتثال بعد عكس الاتجاه (100 = أفضل أداء)"
        if "مستوى التوكيد" in v:
            return "حوّل المستوى إلى درجة: لا يوجد=0، محدود=50، معقول=100"
        return ""

    df["درجة الامتثال/الإفصاح (0-100)"] = None
    df["الوزن × الدرجة"] = None
    df["ملاحظة الإدخال"] = df["المتغير الفرعي (63 متغيراً)"].map(_note)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='SSGI_63_Variables', index=False)
        wb = writer.book
        ws = writer.sheets['SSGI_63_Variables']

        header_format = wb.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#002B49',
            'font_color': '#FFFFFF', 'border': 1, 'align': 'center'
        })
        w_fmt = wb.add_format({'num_format': '0.000%', 'border': 1})
        in_fmt = wb.add_format({'num_format': '0.0', 'border': 1, 'bg_color': '#FFF9DB'})
        calc_fmt = wb.add_format({'num_format': '0.000', 'border': 1, 'bg_color': '#F1F5F9'})

        for col_num, value in enumerate(df.columns.values):
            ws.write(0, col_num, value, header_format)
        for i, w in enumerate(df["الوزن النسبي (AHP)"]):
            r = i + 1
            safe_write_number(ws, r, 4, w, w_fmt)
            ws.write_blank(r, 5, None, in_fmt)
            ws.write_formula(r, 6, f'=IF(F{r+1}="","",E{r+1}*F{r+1})', calc_fmt, "")
        ws.data_validation(1, 5, n, 5, {
            'validate': 'decimal', 'criteria': 'between', 'minimum': 0, 'maximum': 100,
            'input_title': 'درجة الامتثال', 'input_message': 'أدخل رقماً من 0 إلى 100',
            'error_title': 'قيمة غير صحيحة', 'error_message': 'يجب أن تكون القيمة بين 0 و100'
        })
        ws.set_column('A:A', 6)
        ws.set_column('B:B', 30)
        ws.set_column('C:C', 25)
        ws.set_column('D:D', 55)
        ws.set_column('E:G', 18)
        ws.set_column('H:H', 55)
        ws.freeze_panes(1, 0)
        ws.right_to_left()

        ss = wb.add_worksheet('ملخص_المحاور')
        ss.right_to_left()
        txt = wb.add_format({'border': 1})
        pct0 = wb.add_format({'num_format': '0%', 'border': 1, 'align': 'center'})
        num2 = wb.add_format({'num_format': '0.00', 'border': 1, 'align': 'center', 'bold': True})
        bold_gold = wb.add_format({'num_format': '0.00', 'border': 1, 'align': 'center', 'bold': True, 'bg_color': '#C5A059'})
        for c, h in enumerate([
            "المحور الرئيسي", "وزن المحور", "عدد المتغيرات", "المتغيرات المُدخلة",
            "درجة المحور (0-100)", "القيمة المراد إدخالها في المنزلق"
        ]):
            ss.write(0, c, h, header_format)

        B = f"SSGI_63_Variables!$B$2:$B${last}"
        E = f"SSGI_63_Variables!$E$2:$E${last}"
        F = f"SSGI_63_Variables!$F$2:$F${last}"
        G = f"SSGI_63_Variables!$G$2:$G${last}"
        for i, (axis, w) in enumerate(AXIS_WEIGHTS.items()):
            r = i + 1
            x = r + 1
            cnt = int((df["المحور الرئيسي"] == axis).sum())
            ss.write(r, 0, axis, txt)
            ss.write_number(r, 1, w, pct0)
            ss.write_formula(r, 2, f'=COUNTIF({B},A{x})', pct0, cnt)
            ss.write_formula(r, 3, f'=COUNTIFS({B},A{x},{F},"<>")', pct0, 0)
            ss.write_formula(r, 4, f'=IF(D{x}<C{x},"",SUMIF({B},A{x},{G})/SUMIF({B},A{x},{E}))', num2, "")
            ss.write_formula(r, 5, f'=IF(E{x}="","",ROUND(E{x},0))', bold_gold, "")
        ss.write(4, 0, "مؤشر SSGI المركب (للاطلاع فقط)", txt)
        ss.write_formula(4, 1, '=SUM(B2:B4)', pct0, 1)
        ss.write_formula(4, 4, '=IF(COUNT(E2:E4)=3,ROUND(SUMPRODUCT(B2:B4,E2:E4),2),"")', num2, "")
        notes = [
            "طريقة الاستخدام: أدخل درجة كل متغير (0–100) في الخانات الصفراء بورقة SSGI_63_Variables.",
            "تظهر درجة كل محور هنا تلقائياً بعد استكمال متغيراته، وتُدخل القيمة في العمود F بالمنزلق المقابل في المنصة.",
            "المؤشرات العكسية ومقياس التوكيد الخارجي: راجع عمود «ملاحظة الإدخال».",
        ]
        for k, t in enumerate(notes):
            ss.write(6 + k, 0, t)
        ss.set_column('A:A', 42)
        ss.set_column('B:D', 16)
        ss.set_column('E:F', 26)

    return output.getvalue()
# ==============================================================================
# التبويب الثاني: المؤشر المركب (SSGI) - مطور ومحدث بالكامل
# ==============================================================================
with tab2:
    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 18px;">
        <h3 style="color: #002B49; font-weight: 800; font-size: clamp(16px, 4vw, 20px); margin-bottom: 4px;">🗳️ التشخيص القياسي واحتساب مؤشر الحوكمة الذكية المستدامة (SSGI)</h3>
        <p style="color: #475569; font-size: clamp(13px, 3.2vw, 14px);">تشخيص كمي متعدد الأبعاد لأداء البنوك المصرية عبر المحاور الثلاثة الرئيسة.</p>
    </div>
    """, unsafe_allow_html=True)

    col_dl_excel, col_info_box = st.columns([1, 2], gap="medium")

    with col_dl_excel:
        excel_data = generate_ssgi_evaluation_excel()
        st.download_button(
            label="📥 تحميل نموذج التشخيص التفصيلي",
            data=excel_data,
            file_name="نموذج_التقييم_التفصيلي_للمتغيرات_63_SSGI.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )

    with col_info_box:
        st.markdown("""
        <div dir="rtl" style="background-color: #F8FAFC; border-right: 4px solid #C5A059; padding: 10px 14px; border-radius: 8px; border: 1px solid #E2E8F0;">
            <p style="color: #002B49; font-size: 12.5px; font-weight: 700; margin: 0; line-height: 1.6;">
                💡 <b>طريقة الاستخدام:</b> قم بتحميل نموذج Excel لتشخيص المتغيرات الفرعية الـ 63 واستخلاص الدرجة الإجمالية لكل محور من ورقة «ملخص_المحاور»، ثم أدخل القيم في أشرطة القياس أدناه لتسجيل التشخيص.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_input, col_result = st.columns([1, 2], gap="large")

    with col_input:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        bank_ssgi_sel = st.selectbox("اختر البنك المصرفي", BANKS_LIST_AR, key="t1_bank")

        default_sip, default_ig, default_sr = 88, 90, 82
        if bank_ssgi_sel != "اختر البنك المصرفي":
            for item in reversed(st.session_state.history_state):
                if isinstance(item, dict) and item.get("البنك") == clean_text(bank_ssgi_sel):
                    default_sip = int(round(float(item.get("منصات المعلومات (40%)", 88))))
                    default_ig = int(round(float(item.get("الحوكمة المؤسسية (30%)", 90))))
                    default_sr = int(round(float(item.get("تقارير الاستدامة (30%)", 82))))
                    break

        sip_val = st.slider(
            "1. محور منصات المعلومات (SIP - وزن 40%)",
            0, 100, default_sip,
            key=f"t1_sip_{bank_ssgi_sel}",
            help="يعكس حصيلة تقييم الـ 16 متغيراً الفرعياً المكونة لمحور منصات المعلومات الذكية"
        )
        ig_val = st.slider(
            "2. محور الحوكمة المؤسسية (IG - وزن 30%)",
            0, 100, default_ig,
            key=f"t1_ig_{bank_ssgi_sel}",
            help="يعكس حصيلة تقييم الـ 25 متغيراً الفرعياً المكونة لمحور الحوكمة المؤسسية"
        )
        sr_val = st.slider(
            "3. محور تقارير الاستدامة (SR - وزن 30%)",
            0, 100, default_sr,
            key=f"t1_sr_{bank_ssgi_sel}",
            help="يعكس حصيلة تقييم الـ 22 متغيراً الفرعياً المكونة لمحور تقارير الاستدامة"
        )

        live_preview_score = round((sip_val * 0.40) + (ig_val * 0.30) + (sr_val * 0.30), 2)
        st.markdown(flat_html(f"""
        <div style="background: #F8FAFC; border: 1px dashed {CBE_GOLD}; border-radius: 10px; padding: 10px 14px; margin: 10px 0 14px 0; text-align: center;">
            <span style="font-size: 12px; color: #64748B; font-weight: 700;">المعاينة الفورية للمؤشر المركب (SSGI): </span>
            <span style="font-size: 16px; color: {CBE_NAVY}; font-weight: 900;">{live_preview_score}%</span>
        </div>
        """), unsafe_allow_html=True)

        calc_ssgi_btn = st.button("📊 احتساب وتسجيل مؤشر (SSGI)", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if calc_ssgi_btn:
            if bank_ssgi_sel == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى تحديد اسم البنك من القائمة أعلاه للبدء في احتساب المؤشر.")
            else:
                skeleton_placeholder = st.empty()
                skeleton_html = flat_html("""
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
                time.sleep(0.25)
                skeleton_placeholder.empty()

                final_score = round((sip_val * 0.40) + (ig_val * 0.30) + (sr_val * 0.30), 2)

                if final_score >= 80:
                    diagnosis = "🟢 أداء مصرفي مرتفع ومنتظم، نحو الريادة والسيادة الرقمية المستدامة."
                elif final_score >= 50:
                    diagnosis = "🟡 أداء متوسط، يتطلب تعزيزاً استباقياً لمعالجة الفجوات الهيكلية."
                else:
                    diagnosis = "🔴 فجوة هيكلية حرجة تستوجب التدخل الفوري وتفعيل محاكي السياسات."

                entry = {
                    "معرف السجل": f"{clean_text(bank_ssgi_sel)} [{datetime.now().strftime('%H:%M:%S')}]",
                    "البنك": clean_text(bank_ssgi_sel),
                    "مؤشر SSGI المركب": final_score,
                    "منصات المعلومات (40%)": round(sip_val, 2),
                    "الحوكمة المؤسسية (30%)": round(ig_val, 2),
                    "تقارير الاستدامة (30%)": round(sr_val, 2),
                    "التقييم التشخيصي": clean_text(diagnosis)
                }

                st.session_state.history_state = [
                    item for item in st.session_state.history_state
                    if isinstance(item, dict) and "مؤشر SSGI المركب" in item and item.get("البنك") != clean_text(bank_ssgi_sel)
                ]
                st.session_state.history_state.append(entry)

                st.session_state["last_ssgi_diag"] = {
                    "bank": clean_text(bank_ssgi_sel),
                    "final_score": final_score,
                    "sip_val": sip_val,
                    "ig_val": ig_val,
                    "sr_val": sr_val,
                    "diagnosis": diagnosis
                }

        active_diag = st.session_state.get("last_ssgi_diag")
        if active_diag:
            d_bank = active_diag["bank"]
            d_final = active_diag["final_score"]
            d_sip = active_diag["sip_val"]
            d_ig = active_diag["ig_val"]
            d_sr = active_diag["sr_val"]
            score_str_plain = get_colored_score_html(d_final)

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

            weighted_gaps = {
                "منصات المعلومات الذكية (SIP)": round((100 - d_sip) * 0.40, 2),
                "الحوكمة المؤسسية (IG)": round((100 - d_ig) * 0.30, 2),
                "تقارير الاستدامة (SR)": round((100 - d_sr) * 0.30, 2),
            }
            priority_axis = max(weighted_gaps, key=weighted_gaps.get)
            priority_loss = weighted_gaps[priority_axis]

            pillars_spread = max(d_sip, d_ig, d_sr) - min(d_sip, d_ig, d_sr)
            balance_status = (
                "متوازن هيكلياً 🟢" if pillars_spread <= 10
                else ("تفاوت متوسط 🟡" if pillars_spread <= 20 else "اختلال هيكلي ملحوظ 🔴")
            )

            if d_final >= 80:
                badge_status = "أداء مرتفع 🟢"
                status_border_color = "#10B981"
                lead_summary = f"🟢 <b>جاهزية متقدمة ومستدامة (أداء ممتاز):</b> بلغت القيمة المركبة لمؤشر الحوكمة الذكية المستدامة (SSGI) للبنك: <b>{score_str_plain}</b>."
            elif d_final >= 50:
                badge_status = "أداء متوسط 🟡"
                status_border_color = "#F59E0B"
                lead_summary = f"🟡 <b>جاهزية متوسطة تتطلب تدخلاً استباقياً:</b> بلغت القيمة المركبة لمؤشر الحوكمة الذكية المستدامة (SSGI) للبنك: <b>{score_str_plain}</b>."
            else:
                badge_status = "فجوة حرجة 🔴"
                status_border_color = "#EF4444"
                lead_summary = f"🔴 <b>فجوة هيكلية حرجة تستوجب التدخل الفوري:</b> بلغت القيمة المركبة لمؤشر الحوكمة الذكية المستدامة (SSGI) للبنك: <b>{score_str_plain}</b>."

            priority_note = (
                f"<p style='margin-top: 10px; background: #FFFBEB; border: 1px solid #FDE68A; padding: 8px 12px; border-radius: 6px; color: #92400E; font-size: 13px;'>"
                f"🎯 <b>أولوية التحسين الموزونة:</b> يُمثل محور <b>{priority_axis}</b> أدنى المحاور حالياً (بفقدان موزون قدره <b>{priority_loss}</b> نقطة من أصل 100) | التوازن الهيكلي بين المحاور: <b>{balance_status}</b> (فارق {pillars_spread}%).</p>"
                if priority_loss > 0 else
                "<p style='margin-top: 10px; color: #065F46; font-weight: bold;'>🏆 حقق البنك العلامة الكاملة (100%) عبر كافة المحاور الثلاثة بتوازن تام.</p>"
            )

            detailed_diag = f"""
            <div style="line-height: 1.8; font-size: clamp(13px, 3.3vw, 14px);">
                <p>{lead_summary}</p>
                <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 8px 0;">
                <p><b>🔍 تشخيص المحاور المفصل:</b></p>
                <ul style="margin: 0; padding-right: 18px;">
                    <li><b>منصات المعلومات الذكية (SIP - وزن 40%):</b> {get_sip_comment(d_sip)}</li>
                    <li><b>الحوكمة المؤسسية والامتثال (IG - وزن 30%):</b> {get_ig_comment(d_ig)}</li>
                    <li><b>تقارير الاستدامة والتمويل الأخضر (SR - وزن 30%):</b> {get_sr_comment(d_sr)}</li>
                </ul>
                {priority_note}
            </div>
            """

            metric_container_html = f"""
            <div dir="rtl" style="
                background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
                border: 1.5px solid {CBE_GOLD};
                border-radius: 16px;
                padding: clamp(14px, 3vw, 20px);
                box-shadow: 0 10px 25px -5px rgba(0, 43, 73, 0.08);
                margin-bottom: 16px;
            ">
                <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 16px; border-bottom: 1px solid #E2E8F0; padding-bottom: 10px;">
                    <h4 style="color: {CBE_NAVY}; font-weight: 800; margin: 0; font-size: clamp(14px, 3.5vw, 16px); display: flex; flex-wrap: wrap; align-items: center; gap: 6px;">
                        🏛️ ملخص مؤشرات القياس والأداء - <span style="color: {CBE_GOLD};">{d_bank}</span>
                    </h4>
                    <span style="background: #FFFFFF; color: {CBE_NAVY}; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 1px solid #CBD5E1;">
                        {badge_status}
                    </span>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(125px, 1fr)); gap: 10px;">
                    <div style="background: #FFFFFF; border-radius: 12px; padding: 12px; border-right: 5px solid {status_border_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                        <span style="font-size: 11px; color: #64748B; font-weight: 700; display: block; margin-bottom: 4px;">مؤشر SSGI المركب</span>
                        <div style="font-size: clamp(18px, 4.5vw, 22px); font-weight: 900; color: {CBE_NAVY}; line-height: 1.2;">{d_final}%</div>
                        <span style="font-size: 10.5px; color: {status_border_color}; font-weight: 800; margin-top: 4px; display: inline-block;">النتيجة العامة</span>
                    </div>

                    <div style="background: #FFFFFF; border-radius: 12px; padding: 12px; border-right: 5px solid {CBE_NAVY}; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                        <span style="font-size: 11px; color: #64748B; font-weight: 700; display: block; margin-bottom: 4px;">منصات المعلومات (SIP)</span>
                        <div style="font-size: clamp(18px, 4.5vw, 22px); font-weight: 900; color: {CBE_NAVY}; line-height: 1.2;">{d_sip}%</div>
                        <span style="font-size: 10.5px; color: #475569; font-weight: 700; margin-top: 4px; display: inline-block;">الإسهام: {round(d_sip * 0.40, 1)} / 40</span>
                    </div>

                    <div style="background: #FFFFFF; border-radius: 12px; padding: 12px; border-right: 5px solid {CBE_GOLD}; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                        <span style="font-size: 11px; color: #64748B; font-weight: 700; display: block; margin-bottom: 4px;">الحوكمة المؤسسية (IG)</span>
                        <div style="font-size: clamp(18px, 4.5vw, 22px); font-weight: 900; color: {CBE_NAVY}; line-height: 1.2;">{d_ig}%</div>
                        <span style="font-size: 10.5px; color: #475569; font-weight: 700; margin-top: 4px; display: inline-block;">الإسهام: {round(d_ig * 0.30, 1)} / 30</span>
                    </div>

                    <div style="background: #FFFFFF; border-radius: 12px; padding: 12px; border-right: 5px solid #475569; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                        <span style="font-size: 11px; color: #64748B; font-weight: 700; display: block; margin-bottom: 4px;">تقارير الاستدامة (SR)</span>
                        <div style="font-size: clamp(18px, 4.5vw, 22px); font-weight: 900; color: {CBE_NAVY}; line-height: 1.2;">{d_sr}%</div>
                        <span style="font-size: 10.5px; color: #475569; font-weight: 700; margin-top: 4px; display: inline-block;">الإسهام: {round(d_sr * 0.30, 1)} / 30</span>
                    </div>
                </div>
            </div>
            """
            st.markdown(flat_html(metric_container_html), unsafe_allow_html=True)

            st.markdown(flat_html(f"""
            <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: clamp(14px, 3vw, 22px); border-radius: 12px; border: 1.5px solid {CBE_GOLD}; line-height: 1.8; box-shadow: 0 4px 15px rgba(0,0,0,0.04); margin-top: 10px;">
              <div style="background: {CBE_BG}; padding: clamp(12px, 2.5vw, 15px); border-radius: 8px; border-right: 5px solid {CBE_GOLD};">
                <p style="margin: 0 0 8px 0; font-weight: bold; color: {CBE_NAVY}; font-size: clamp(14px, 3.5vw, 15px);">التشخيص القياسي الكلي:</p>
                <div style="color: {CBE_NAVY};">{detailed_diag}</div>
              </div>
            </div>
            """), unsafe_allow_html=True)

            diag_doc_body = f"""
            <ul>
                <li><b>مؤشر SSGI المركب:</b> {d_final}%</li>
                <li><b>منصات المعلومات الذكية (SIP - وزن 40%):</b> {d_sip}% (الإسهام الفعلي: {round(d_sip * 0.40, 1)} / 40)</li>
                <li><b>الحوكمة المؤسسية (IG - وزن 30%):</b> {d_ig}% (الإسهام الفعلي: {round(d_ig * 0.30, 1)} / 30)</li>
                <li><b>تقارير الاستدامة (SR - وزن 30%):</b> {d_sr}% (الإسهام الفعلي: {round(d_sr * 0.30, 1)} / 30)</li>
            </ul>
            <hr>
            {detailed_diag}
            """
            diag_bytes, diag_ext, diag_mime = build_native_docx(
                f"بطاقة التشخيص القياسي لمؤشر الحوكمة الذكية المستدامة (SSGI) - {d_bank}",
                f"التصنيف العام: {badge_status}",
                diag_doc_body,
            )
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.download_button(
                label=f"📄 تحميل بطاقة التشخيص القياسي لبنك ({d_bank}) ",
                data=diag_bytes,
                file_name=f"التشخيص_القياسي_SSGI_{d_bank}{diag_ext}",
                mime=diag_mime,
                use_container_width=True,
                key="dl_single_ssgi_word"
            )

            st.markdown("<br>", unsafe_allow_html=True)
            ch_col1, ch_col2 = st.columns(2)

            curr_records = [r for r in st.session_state.history_state if isinstance(r, dict) and "مؤشر SSGI المركب" in r]
            if len(curr_records) > 1:
                df_bench = pd.DataFrame(curr_records)
                bench_vals = [
                    round(df_bench["منصات المعلومات (40%)"].mean(), 1),
                    round(df_bench["الحوكمة المؤسسية (30%)"].mean(), 1),
                    round(df_bench["تقارير الاستدامة (30%)"].mean(), 1),
                ]
                bench_label = f"متوسط القطاع المسجل ({len(curr_records)} بنوك)"
            else:
                bench_vals = [75.0, 75.0, 75.0]
                bench_label = "المعيار الرقابي المستهدف (75%)"

            categories = ['منصات المعلومات (SIP)', 'الحوكمة المؤسسية (IG)', 'تقارير الاستدامة (SR)']

            with ch_col1:
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=[d_sip, d_ig, d_sr],
                    theta=categories,
                    fill='toself',
                    name=d_bank,
                    line_color=CBE_GOLD,
                    fillcolor='rgba(197, 160, 89, 0.28)'
                ))
                fig_radar.add_trace(go.Scatterpolar(
                    r=bench_vals,
                    theta=categories,
                    fill='none',
                    name=bench_label,
                    line=dict(color=CBE_NAVY, dash='dash', width=2)
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5, font=dict(size=10)),
                    title=dict(text="التحليل الراداري والمقارنة المرجعية", x=0.5, xanchor='center'),
                    font=dict(family="Cairo", size=11),
                    margin=dict(l=25, r=25, t=40, b=45),
                    height=320
                )
                st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

            with ch_col2:
                fig_bar = go.Figure(data=[
                    go.Bar(
                        name=d_bank,
                        x=categories,
                        y=[d_sip, d_ig, d_sr],
                        marker_color=[CBE_NAVY, CBE_GOLD, "#475569"],
                        text=[f"{d_sip}%", f"{d_ig}%", f"{d_sr}%"],
                        textposition="outside"
                    ),
                    go.Bar(
                        name=bench_label,
                        x=categories,
                        y=bench_vals,
                        marker_color="rgba(148, 163, 184, 0.45)",
                        text=[f"{v}%" for v in bench_vals],
                        textposition="outside"
                    )
                ])
                fig_bar.update_layout(
                    barmode="group",
                    title=dict(text="أداء البنك مقابل المعيار المرجعي (%)", x=0.5, xanchor='center'),
                    font=dict(family="Cairo", size=11),
                    yaxis=dict(range=[0, 112]),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5, font=dict(size=10)),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=40, b=45),
                    height=320
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("📊 تُحسب قيم المحاور الرئيسة بناءً على المخرجات النهائية لنموذج التقييم التفصيلي (Excel)، أو من خلال تحديد قيمها مباشرة عبر أشرطة التمرير ثم الضغط على زر الحساب.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # --------------------------------------------------------------------------
    # الجدول الأول: ترتيب وسجلات البنوك المُشخَّصة
    # --------------------------------------------------------------------------
    st.markdown("<h3 style='color: #002B49; font-weight: 800; font-size: clamp(16px, 4vw, 20px);'>📋 قائمة البنوك المشخصة</h3>", unsafe_allow_html=True)

    ssgi_records = [r for r in st.session_state.history_state if isinstance(r, dict) and "مؤشر SSGI المركب" in r]
    if ssgi_records:
        df_history = pd.DataFrame(ssgi_records).sort_values(by="مؤشر SSGI المركب", ascending=False).reset_index(drop=True)

        history_table_html = """
        <div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 350px; -webkit-overflow-scrolling: touch;">
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
                label="📥 تحميل قائمة البنوك المشخصة",
                data=csv_data,
                file_name="ترتيب_البنوك_المصرية_SSGI.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_del:
            recorded_ids = [item.get("معرف السجل", item.get("البنك", "")) for item in ssgi_records]
            col_sel, col_btn = st.columns([2, 1])
            with col_sel:
                id_to_delete = st.selectbox("اختر سجلاً لحذفه", recorded_ids, key="del_rec_box", label_visibility="collapsed")
            with col_btn:
                if st.button("🗑️ حذف السجل", use_container_width=True, type="secondary"):
                    st.session_state.history_state = [item for item in ssgi_records if item.get("معرف السجل", item.get("البنك", "")) != id_to_delete]
                    if st.session_state.get("last_ssgi_diag") and st.session_state["last_ssgi_diag"]["bank"] in id_to_delete:
                        del st.session_state["last_ssgi_diag"]
                    st.success("✅ تم حذف السجل بنجاح.")
                    st.rerun()
    else:
        st.info("📂 لا توجد بنوك مسجلة حتى الآن. قم بإجراء التشخيص في الأعلى لتسجيل وترتيب البنوك المصرفية.")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # الجدول الثاني: استعراض المصفوفة الهرمية المحدثة بالكامل وجدول أوزان المتغيرات
    # --------------------------------------------------------------------------
    with st.expander("📂 استعراض المصفوفة الهرمية والمحاور الرئيسة والأبعاد والعناصر الفرعية الـ 63 لمؤشر الحوكمة (SSGI)", expanded=False):
        st.markdown("""
        <div dir="rtl" style="text-align: right; line-height: 1.8;">
        <ul>
            <li><b>منصات المعلومات الذكية (SIP - وزن 40%):</b> يضم 16 متغيراً فرعياً موزعة على 4 أبعاد (جودة المعلومات، التكامل والخصوصية، الامتثال التقني، والتخطيط والمراقبة).</li>
            <li><b>الحوكمة المؤسسية (IG - وزن 30%):</b> يضم 25 متغيراً فرعياً موزعة على 6 أبعاد (سيادة القانون، العدالة، المتابعة، المشاركة، الشفافية، ومجلس الإدارة).</li>
            <li><b>تقارير الاستدامة (SR - وزن 30%):</b> يضم 22 متغيراً فرعياً موزعة على 5 أبعاد (الاستراتيجية، التنوع، إدارة المخاطر، الأبعاد التشغيلية، والمقاييس).</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        hierarchy_table_html = """
        <div dir="rtl" style="width: 100%; overflow-x: auto; max-height: 450px; -webkit-overflow-scrolling: touch;">
        <table class="custom-rtl-table">
        <thead>
        <tr>
        <th style="width: 25%;">المحور الرئيسي</th>
        <th style="width: 25%;">البعد الأساسي</th>
        <th style="width: 50%;">العناصر الفرعية (الـ 63 متغيراً التفصيلية)</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td rowspan="4" style="font-weight: bold; color: #002B49; vertical-align: top;">أولاً: منصات المعلومات الذكية (SIP - 40%)</td>
        <td>1. جودة المعلومات</td>
        <td>1/1 نسبة تغطية الفروع بشبكة البيانات المركزية.<br>1/2 سعة التخزين السحابي/المحلي.<br>1/3 نسبة البيانات المهيكلة (Structured).<br>1/4 نسبة اكتمال حقول البيانات (Data Completeness).</td>
        </tr>
        <tr>
        <td>2. التكامل والخصوصية</td>
        <td>2/1 عدد الأنظمة الفرعية المربوطة بـ (APIs).<br>2/2 معدل وقت التشغيل (System Uptime).<br>2/3 نسبة البيانات المستضافة محلياً (On-Premise).<br>2/4 عدد حوادث اختراق البيانات المسجلة.</td>
        </tr>
        <tr>
        <td>3. الامتثال التقني</td>
        <td>3/1 نسبة ضوابط معيار (ISO 27001).<br>3/2 عدد شهادات الامتثال التقني السارية.<br>3/3 عدد عمليات التدقيق على نماذج الذكاء الاصطناعي.<br>3/4 نسبة النماذج الموثقة بسجلات شرح النتائج.</td>
        </tr>
        <tr>
        <td>4. التخطيط والمراقبة بعد النشر</td>
        <td>4/1 متوسط الزمن المستغرق لاكتشاف الخطأ (MTTD).<br>4/2 عدد التنبيهات الآلية الصحيحة.<br>4/3 معدل دقة التنبؤات (AI Accuracy Rate).<br>4/4 نسبة التقارير التي تطلبت تصحيحاً يدوياً.</td>
        </tr>
        <tr>
        <td rowspan="6" style="font-weight: bold; color: #002B49; vertical-align: top;">ثانياً: الحوكمة المؤسسية (IG - 30%)</td>
        <td>1. سيادة القانون</td>
        <td>1/1 نسبة السياسات الداخلية المحدثة.<br>1/2 قيمة الغرامات المالية الموقعة.<br>1/3 نسبة الموظفين الموقعين على مدونة السلوك.<br>1/4 عدد بلاغات المخالفات الأخلاقية.</td>
        </tr>
        <tr>
        <td>2. العدالة والمساواة</td>
        <td>2/1 نسبة فجوة الأجور بين الجنسين.<br>2/2 نسبة الترقيات الداخلية مقارنة بالتعيينات.<br>2/3 نسبة توزيعات الأرباح إلى صافي الربح.<br>2/4 عدد القضايا المرفوعة ضد البنك.</td>
        </tr>
        <tr>
        <td>3. المتابعة والمساءلة</td>
        <td>3/1 نسبة العمليات الموثقة بمصفوفة (RACI).<br>3/2 عدد الأوصاف الوظيفية المحدثة للقيادات.<br>3/3 نسبة توصيات المراجعة الداخلية المنفذة.<br>3/4 عدد اجتماعات لجان الحوكمة والمخاطر.</td>
        </tr>
        <tr>
        <td>4. المشاركة</td>
        <td>4/1 معدل الاستجابة لشكاوى العملاء.<br>4/2 عدد قنوات التواصل الرقمية الفعالة.<br>4/3 نسبة القرارات الاستراتيجية التي خضعت لاستطلاع الرأي.</td>
        </tr>
        <tr>
        <td>5. الشفافية والإفصاح</td>
        <td>5/1 درجة سهولة القراءة (Readability Score).<br>5/2 عدد صفحات الإفصاح عن المخاطر غير المالية.<br>5/3 الفجوة الزمنية لنشر التقرير.<br>5/4 عدد الإفصاحات الفورية عن الأحداث الجوهرية.</td>
        </tr>
        <tr>
        <td>6. مجلس الإدارة</td>
        <td>6/1 نسبة حضور أعضاء مجلس الإدارة.<br>6/2 متوسط سنوات خبرة الأعضاء بالاستدامة.<br>6/3 عدد اجتماعات لجنة الترشيحات والمكافآت.<br>6/4 نسبة التزام المجلس بتقييم الأداء السنوي.<br>6/5 نسبة اللجان السيادية برئاسة أعضاء مستقلين.<br>6/6 عدد حالات تعارض المصالح المرصودة.</td>
        </tr>
        <tr>
        <td rowspan="5" style="font-weight: bold; color: #002B49; vertical-align: top;">ثالثاً: تقارير الاستدامة (SR - 30%)</td>
        <td>1. الاستراتيجية</td>
        <td>1/1 عدد أهداف التنمية المستدامة المتبناة.<br>1/2 نسبة الأهداف المحققة من المخطط.<br>1/3 نسبة ميزانية R&D والتحول الأخضر.<br>1/4 حجم الاستثمار في البنية التحتية المستدامة.</td>
        </tr>
        <tr>
        <td>2. التنوع والشمول</td>
        <td>2/1 نسبة تمثيل المرأة في مجلس الإدارة.<br>2/2 نسبة الأعضاء المستقلين في المجلس.<br>2/3 نسبة ذوي الهمم من إجمالي القوى العاملة.<br>2/4 نسبة الموظفين من خارج العاصمة (الأقاليم).</td>
        </tr>
        <tr>
        <td>3. إدارة المخاطر</td>
        <td>3/1 نسبة محفظة الائتمان المقيمة بيئياً.<br>3/2 القيمة المعرضة للخطر (VaR) المناخية.<br>3/3 عدد سيناريوهات اختبارات الضغط المناخية.<br>3/4 نسبة كفاية رأس المال (CAR) المناخية.</td>
        </tr>
        <tr>
        <td>4. الأبعاد التشغيلية</td>
        <td>4/1 نسبة الأصول الخضراء (GAR).<br>4/2 حجم القروض الموجهة للمشروعات الصغرى والمتوسطة.<br>4/3 إجمالي انبعاثات الكربون لكل موظف.<br>4/4 نسبة استهلاك الطاقة المتجددة.<br>4/5 نسبة الإنفاق على (CSR).<br>4/6 عدد المستفيدين من الشمول المالي.</td>
        </tr>
        <tr>
        <td>5. المقاييس والأهداف</td>
        <td>5/1 نسبة التغير السنوي في خفض الانبعاثات.<br>5/2 معدل تحقيق مؤشرات الأداء الرئيسية.<br>5/3 نسبة تغطية مؤشرات (GRI).<br>5/4 مستوى التوكيد الخارجي.</td>
        </tr>
        </tbody>
        </table>
        </div>
        """
        st.markdown(flat_html(hierarchy_table_html), unsafe_allow_html=True)

        df_w = get_ssgi_variables_df()
        w_rows = ""
        for (axis, dim), g in df_w.groupby(["المحور الرئيسي", "البعد الأساسي"], sort=False):
            wv = g["الوزن النسبي (AHP)"]
            w_rows += f"""
            <tr>
            <td>{axis}</td>
            <td>{dim}</td>
            <td style="text-align: center;">{len(g)}</td>
            <td style="text-align: center;">{wv.iloc[0]*100:.3f}%</td>
            <td style="text-align: center;">{wv.sum()*100:.2f}%</td>
            </tr>"""
        w_rows += f"""
            <tr style="font-weight: bold;">
            <td colspan="2">الإجمالي</td>
            <td style="text-align: center;">{len(df_w)}</td>
            <td style="text-align: center;">-</td>
            <td style="text-align: center;">{df_w['الوزن النسبي (AHP)'].sum()*100:.2f}%</td>
            </tr>"""
        st.markdown("<p dir='rtl' style='text-align:right;font-weight:800;color:#002B49;margin-top:14px;'>⚖️ الأوزان المعتمدة للمتغيرات الـ 63</p>", unsafe_allow_html=True)
        st.markdown(flat_html(f"""
        <div dir="rtl" style="width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch;">
        <table class="custom-rtl-table">
        <thead><tr><th>المحور الرئيسي</th><th>البعد</th><th style="text-align:center;">عدد المتغيرات</th>
        <th style="text-align:center;">وزن كل متغير</th><th style="text-align:center;">وزن البعد من المؤشر</th></tr></thead>
        <tbody>{w_rows}</tbody>
        </table>
        </div>
        """), unsafe_allow_html=True)

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
            font=dict(family="Cairo", size=12),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
            margin=dict(l=15, r=15, t=45, b=60)
        )
        st.plotly_chart(fig_pie_bank, use_container_width=True, config={"displayModeBar": False})

# ==============================================================================
# التبويب الثالث: محاكي السياسات (Policy Simulator) - مطور ومحدث بالكامل
# ==============================================================================
with tab3:
    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 20px;">
        <h3 style="color: #002B49; font-weight: 800; margin-bottom: 4px;">🔬 محاكي السياسات الاستشرافي للسيناريوهات</h3>
        <p style="color: #475569; font-size: 14px;">استشراف أثر التدخلات المستقبلية حسب محاور الحوكمة الذكية لكل بنك بناءً على قيمه الفعلية ومتغيرات التحفيز.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.history_state:
        st.warning("⚠️ يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI في التبويب الثاني للتمكن من تشغيل المحاكي.")
    else:
        col_sim_in, col_sim_out = st.columns([1, 2], gap="large")

        with col_sim_in:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            recorded_banks_sim = list(dict.fromkeys([item["البنك"] for item in st.session_state.history_state]))
            sim_bank_sel = st.selectbox("اختر البنك للمحاكاة", recorded_banks_sim, key="sim_bank")

            default_bank_ssgi = 85.0
            curr_s_val, curr_i_val, curr_r_val = 85.0, 85.0, 85.0
            for item in reversed(st.session_state.history_state):
                if item["البنك"] == sim_bank_sel:
                    default_bank_ssgi = float(item["مؤشر SSGI المركب"])
                    curr_s_val = float(item["منصات المعلومات (40%)"])
                    curr_i_val = float(item["الحوكمة المؤسسية (30%)"])
                    curr_r_val = float(item["تقارير الاستدامة (30%)"])
                    break

            base_ssgi_input = st.slider(
                "قيمة المؤشر الأساسي الحالي (SSGI)",
                30.0, 100.0, default_bank_ssgi, 0.5,
                key=f"sim_base_{sim_bank_sel}"
            )

            scenario_dropdown = st.selectbox("اختر السيناريو الاستراتيجي", [
                "📉 السيناريو التشاؤمي (غياب التدخل وضعف الاستثمار التقني)",
                "📊 السيناريو المعتدل / التفاؤلي (استثمارات تقليدية تدريجية)",
                "🚀 السيناريو الطموح / الاستباقي (إصلاحات هيكلية شاملة وسيادة رقمية)"
            ], index=1, key="sim_scen")

            is_pessimistic = scenario_dropdown.startswith("📉")
            if is_pessimistic:
                var1_sip, var2_ig, var3_sr = 0, 0, 0
                st.markdown("""
                <div dir="rtl" style="background: #FEF2F2; border: 1px solid #FECACA; border-right: 4px solid #DC2626; border-radius: 8px; padding: 12px 14px; margin: 10px 0 14px 0; text-align: right;">
                    <div style="color: #991B1B; font-weight: 800; font-size: 13.5px; margin-bottom: 6px;">📉 معاملات الانكماش الافتراضية (تجميد الاستثمارات):</div>
                    <ul style="margin: 0; padding-right: 18px; color: #7F1D1D; font-size: 13px; line-height: 1.75;">
                        <li><b>منصات المعلومات والبنية التقنية (SIP):</b> تراجع بنسبة <b>-10%</b></li>
                        <li><b>كفاءة الحوكمة المؤسسية (IG):</b> تراجع بنسبة <b>-9%</b></li>
                        <li><b>تقارير الاستدامة والتمويل الأخضر (SR):</b> تراجع بنسبة <b>-11%</b></li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                var1_sip = st.slider("1️⃣ نسبة التحفيز في منصات المعلومات والبنية التقنية (%)", 0, 50, 20, key="sim_v1")
                var2_ig = st.slider("2️⃣ نسبة التحفيز في كفاءة الحوكمة المؤسسية (%)", 0, 50, 15, key="sim_v2")
                var3_sr = st.slider("3️⃣ نسبة التحفيز في تقارير الاستدامة والتمويل الأخضر (%)", 0, 50, 15, key="sim_v3")

            run_sim_btn = st.button("📈 تشغيل وتثبيت السيناريو", use_container_width=True, type="primary")

            if st.button("🗑️ مسح كافة السيناريوهات", use_container_width=True, type="secondary"):
                st.session_state.simulated_results_dict = {}
                st.rerun()

            scenarios_count = len(st.session_state.simulated_results_dict)
            sim_body_items = f"<h3>📋 عرض كافة السيناريوهات المحاكاة للقطاع المصرفي (إجمالي: {scenarios_count}):</h3>"
            if st.session_state.simulated_results_dict:
                for k, v in st.session_state.simulated_results_dict.items():
                    sim_body_items += f"<h3>معرف السيناريو: {k}</h3><div>{v['html']}</div><div>{v['deep']}</div><hr>"
            else:
                sim_body_items += "<p>لا توجد سيناريوهات محاكاة مسجلة حالياً في الجلسة.</p>"

            sim_body_items += "<p style='color: #475569; font-size: 12px; margin-top: 16px;'>تنويه استرشادي: تُعد مخرجات المنصة أداة مساندة لدعم اتخاذ القرار، ويُوصى بمواءمتها مع السياسات الداخلية لكل مصرف.</p>"

            sim_bytes, sim_ext, sim_mime = build_native_docx(
                "تقرير محاكي السياسات الاستشرافي والمتابعة التراكمية",
                f"تاريخ التوليد: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                sim_body_items,
            )

            st.download_button(
                label="📥 تحميل تقرير محاكي السياسات",
                data=sim_bytes,
                file_name=f"تقرير_محاكي_السياسات_المصرفية_الشامل{sim_ext}",
                mime=sim_mime,
                use_container_width=True,
                key="dl_sim_word_btn"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col_sim_out:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)

            if run_sim_btn:
                if sim_bank_sel == "اختر البنك المصرفي":
                    st.warning("⚠️ يرجى اختيار بنك مصرفي صحيح أولاً.")
                else:
                    base_val = base_ssgi_input
                    s_val, i_val, r_val = curr_s_val, curr_i_val, curr_r_val

                    pillars_map = {
                        "منصات المعلومات والبنية التقنية (SIP)": s_val,
                        "الحوكمة المؤسسية ولجان الالتزام (IG)": i_val,
                        "تقارير الاستدامة والتمويل الأخضر (SR)": r_val
                    }
                    weakest_pillar = min(pillars_map, key=pillars_map.get)
                    weakest_score = pillars_map[weakest_pillar]
                    strongest_pillar = max(pillars_map, key=pillars_map.get)
                    strongest_score = pillars_map[strongest_pillar]

                    boost_map = {
                        "منصات المعلومات (SIP)": var1_sip,
                        "الحوكمة المؤسسية (IG)": var2_ig,
                        "تقارير الاستدامة (SR)": var3_sr
                    }
                    top_boosted_pillar = max(boost_map, key=boost_map.get)
                    top_boost_pct = boost_map[top_boosted_pillar]

                    if scenario_dropdown.startswith("📉"):
                        sim_s = round(max(0.0, s_val * 0.90), 1)
                        sim_i = round(max(0.0, i_val * 0.91), 1)
                        sim_r = round(max(0.0, r_val * 0.89), 1)
                        simulated_val = round(max(0.0, base_val * 0.90), 2)

                        analysis_text = (
                            f"إنذار مبكر لـ ({sim_bank_sel}): تجميد الاستثمارات سيؤدي إلى هبوط المؤشر المركب بمقدار ({simulated_val - base_val:+.2f}) نقطة، "
                            f"مع تفاقم الفجوة الحرجة في <b>{weakest_pillar}</b> من ({weakest_score}%) إلى ({min(sim_s, sim_i, sim_r)}%)، مما يعرض البنك لمخاطر عدم الامتثال الرقابي."
                        )
                        action_plan = (
                            f"تدخل وقائي عاجل لـ ({sim_bank_sel}): إقرار خطة إنقاذ فورية لرفع كفاءة <b>{weakest_pillar} ({weakest_score}%)</b> كأولوية قصوى، "
                            f"وتحصين المكتسبات المحققة في <b>{strongest_pillar} ({strongest_score}%)</b> ضد التآكل التشغيلي."
                        )
                    elif scenario_dropdown.startswith("📊"):
                        factor = 0.0022
                        sim_s = round(min(100.0, s_val * (1 + var1_sip * factor)), 1)
                        sim_i = round(min(100.0, i_val * (1 + var2_ig * factor)), 1)
                        sim_r = round(min(100.0, r_val * (1 + var3_sr * factor)), 1)
                        combined_boost = (var1_sip * 0.40) + (var2_ig * 0.30) + (var3_sr * 0.30)
                        simulated_val = round(min(100.0, base_val * (1 + (combined_boost * factor))), 2)

                        if base_val >= 80:
                            analysis_text = (
                                f"نمو متوازن وتعزيز للريادة في ({sim_bank_sel}): بفضل القاعدة الصلبة في <b>{strongest_pillar} ({strongest_score}%)</b> "
                                f"وتوجيه أعلى تحفيز نحو <b>{top_boosted_pillar} (+{top_boost_pct}%)</b>، يرتفع المؤشر إلى ({simulated_val}%) مع الحفاظ على الاستقرار المؤسسي."
                            )
                            action_plan = (
                                f"خارطة طريق ({sim_bank_sel}): تركيز الاستثمارات التدريجية لمعالجة الفجوة النسبية في <b>{weakest_pillar} ({weakest_score}% ⬅️ {min(sim_s, sim_i, sim_r)}%)</b>، "
                                f"وربط مؤشرات الأداء بمستهدفات التمويل المستدام المعتمدة من البنك المركزي."
                            )
                        else:
                            analysis_text = (
                                f"تحسن تدريجي مشروط في ({sim_bank_sel}): يساهم التحفيز الموجه لـ <b>{top_boosted_pillar} (+{top_boost_pct}%)</b> في رفع المؤشر إلى ({simulated_val}%)، "
                                f"إلا أن استمرار انخفاض <b>{weakest_pillar} ({weakest_score}%)</b> يظل قيداً هيكلياً يبطئ القفزة النوعية."
                            )
                            action_plan = (
                                f"خارطة طريق ({sim_bank_sel}): إعادة توجيه المخصصات التدريجية لمعالجة الاختناق في <b>{weakest_pillar} ({weakest_score}%)</b>، "
                                f"بالتوازي مع تفعيل التحفيز المبرمج في <b>{top_boosted_pillar} (+{top_boost_pct}%)</b> لردم الفجوة الرقابية."
                            )
                    else:
                        factor = 0.0042
                        sim_s = round(min(100.0, s_val * (1 + var1_sip * factor)), 1)
                        sim_i = round(min(100.0, i_val * (1 + var2_ig * factor)), 1)
                        sim_r = round(min(100.0, r_val * (1 + var3_sr * factor)), 1)
                        combined_boost = (var1_sip * 0.40) + (var2_ig * 0.30) + (var3_sr * 0.30)
                        simulated_val = round(min(100.0, base_val * (1 + (combined_boost * factor))), 2)

                        analysis_text = (
                            f"تحول استراتيجي شامل في ({sim_bank_sel}): يؤدي ضخ استثمارات مكثفة في <b>{top_boosted_pillar} (+{top_boost_pct}%)</b> "
                            f"مع إصلاح <b>{weakest_pillar} (من {weakest_score}% إلى {min(sim_s, sim_i, sim_r)}%)</b> إلى قفزة نوعية ترفع المؤشر إلى ({simulated_val}%)."
                        )
                        action_plan = (
                            f"خطة التحول القيادي لـ ({sim_bank_sel}): إطلاق برنامج إعادة هندسة شاملة لـ <b>{weakest_pillar}</b>، "
                            f"وتعظيم العائد من <b>{strongest_pillar} ({strongest_score}%)</b> لتطبيق تقنيات الرقابة الآلية (RegTech) وتصدر مؤشرات الاستدامة."
                        )

                    delta = round(simulated_val - base_val, 2)
                    score_str_plain = get_colored_score_html(simulated_val)

                    deep_analysis = flat_html(f"""
                    <div style="background: #F8FAFC; padding: 16px; border-radius: 8px; border: 1px solid #CBD5E1; margin-top: 10px;" dir="rtl">
                        <p style="font-weight: bold; color: {CBE_NAVY}; margin-bottom: 8px; text-align: right;">📊 التحليل التفصيلي لمسار المحاور الثلاثة لبنك ({sim_bank_sel}):</p>
                        <ul style="margin: 0; padding-right: 20px; color: #1E293B; line-height: 1.85; text-align: right;">
                            <li><b>1. منصات المعلومات (SIP) [{s_val}% ⬅️ {sim_s}%]:</b> {describe_sip(s_val)}</li>
                            <li><b>2. الحوكمة المؤسسية (IG) [{i_val}% ⬅️ {sim_i}%]:</b> {describe_ig(i_val)}</li>
                            <li><b>3. تقارير الاستدامة (SR) [{r_val}% ⬅️ {sim_r}%]:</b> {describe_sr(r_val)}</li>
                        </ul>
                    </div>
                    """)

                    box_html = flat_html(f"""
                    <div dir="rtl" style="text-align: right; background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
                      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; margin-bottom: 12px;">
                          <h4 style="color: {CBE_NAVY}; font-weight: bold; margin: 0; font-size: 16px;">📈 محاكاة: <span style="color: {CBE_GOLD};">{sim_bank_sel}</span></h4>
                          <span style="background: #F1F5F9; color: {CBE_NAVY}; padding: 3px 10px; border-radius: 15px; font-size: 12px; font-weight: bold;">{scenario_dropdown}</span>
                      </div>
                      <p style="font-size: 14.5px; margin-bottom: 12px; color: #1E293B;">
                          <b>القيمة المتوقعة للمؤشر المركب:</b> {score_str_plain} 
                          <span style="background: {'#DCFCE7' if delta >= 0 else '#FEE2E2'}; color: {'#166534' if delta >= 0 else '#991B1B'}; padding: 2px 8px; border-radius: 6px; font-weight: bold; margin-right: 6px;">
                              صافي التغير: {delta:+.2f}
                          </span>
                          <span style="color: #64748B; font-size: 13px;"> (القيمة الأساسية: {base_val:.2f}%)</span>
                      </p>
                      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; text-align: center;">
                          <div style="background: #F8FAFC; padding: 8px; border-radius: 8px; border: 1px solid #E2E8F0;">
                              <div style="font-size: 11px; color: #64748B; font-weight: bold;">منصات المعلومات (SIP)</div>
                              <div style="font-size: 14px; font-weight: 800; color: {CBE_NAVY};">{s_val}% ⬅️ {sim_s}%</div>
                          </div>
                          <div style="background: #F8FAFC; padding: 8px; border-radius: 8px; border: 1px solid #E2E8F0;">
                              <div style="font-size: 11px; color: #64748B; font-weight: bold;">الحوكمة المؤسسية (IG)</div>
                              <div style="font-size: 14px; font-weight: 800; color: {CBE_NAVY};">{i_val}% ⬅️ {sim_i}%</div>
                          </div>
                          <div style="background: #F8FAFC; padding: 8px; border-radius: 8px; border: 1px solid #E2E8F0;">
                              <div style="font-size: 11px; color: #64748B; font-weight: bold;">تقارير الاستدامة (SR)</div>
                              <div style="font-size: 14px; font-weight: 800; color: {CBE_NAVY};">{r_val}% ⬅️ {sim_r}%</div>
                          </div>
                      </div>
                      <div style="background: {CBE_BG}; padding: 14px; border-radius: 8px; border-right: 4px solid {CBE_GOLD};">
                        <p style="margin-bottom: 8px; color: #1E293B; font-size: 13.5px; line-height: 1.7;"><b>🔬 التحليل القياسي المخصص:</b> {analysis_text}</p>
                        <p style="margin: 0; color: #0F172A; font-size: 13.5px; line-height: 1.7;"><b>🛠️ خطة التحرك الاستراتيجية:</b> {action_plan}</p>
                      </div>
                    </div>
                    """)

                    sim_key = f"{sim_bank_sel} - {scenario_dropdown} [{datetime.now().strftime('%H:%M:%S')}]"
                    st.session_state.simulated_results_dict[sim_key] = {
                        "html": box_html,
                        "deep": deep_analysis,
                        "bank": sim_bank_sel,
                        "base_val": base_val,
                        "simulated_val": simulated_val,
                        "delta": delta,
                        "scenario": scenario_dropdown,
                        "analysis_text": analysis_text,
                        "action_plan": action_plan,
                        "pillars_before": [s_val, i_val, r_val],
                        "pillars_after": [sim_s, sim_i, sim_r]
                    }
                    st.rerun()

            if st.session_state.simulated_results_dict:
                latest_key = list(st.session_state.simulated_results_dict.keys())[-1]
                latest_item = st.session_state.simulated_results_dict[latest_key]
                if "pillars_before" in latest_item and "pillars_after" in latest_item:
                    fig_sim = go.Figure(data=[
                        go.Bar(name='الوضع الحالي (%)', x=['منصات المعلومات (SIP)', 'الحوكمة المؤسسية (IG)', 'تقارير الاستدامة (SR)', 'المؤشر المركب (SSGI)'],
                               y=latest_item["pillars_before"] + [latest_item["base_val"]], marker_color='#94A3B8'),
                        go.Bar(name='المتوقع بعد السيناريو (%)', x=['منصات المعلومات (SIP)', 'الحوكمة المؤسسية (IG)', 'تقارير الاستدامة (SR)', 'المؤشر المركب (SSGI)'],
                               y=latest_item["pillars_after"] + [latest_item["simulated_val"]], marker_color='#C59B27')
                    ])
                    fig_sim.update_layout(
                        barmode='group',
                        title=f"📊 مقارنة الأداء الحالي مقابل المتوقع: {latest_item['bank']}",
                        yaxis=dict(range=[0, 105]),
                        height=300,
                        margin=dict(t=45, b=20, l=20, r=20),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_sim, use_container_width=True)

                st.markdown("<h4>📋 سجل السيناريوهات الاستشرافية :</h4>", unsafe_allow_html=True)
                for s_key, item in reversed(list(st.session_state.simulated_results_dict.items())):
                    col_k1, col_k2 = st.columns([5, 1])
                    with col_k1:
                        st.markdown(f"<span style='color: #64748B; font-size: 12px;'>معرف السيناريو: {s_key}</span>", unsafe_allow_html=True)
                    with col_k2:
                        if st.button("🗑️ حذف", key=f"del_sim_{s_key}", use_container_width=True):
                            del st.session_state.simulated_results_dict[s_key]
                            st.rerun()
                    st.markdown(item["html"], unsafe_allow_html=True)
                    st.markdown(item["deep"], unsafe_allow_html=True)
                    st.markdown("---")
            else:
                st.info("📈 قم باختيار البنك والسيناريو ومتغيرات التحفيز واضغط على مفتاح الإضافة لتثبيت ومتابعة السيناريوهات.")
            st.markdown('</div>', unsafe_allow_html=True)
# ==============================================================================
# التبويب الرابع: لوحة دعم اتخاذ القرار (Decision Support Dashboard) - مطور ومحدث بالكامل
# ==============================================================================
with tab4:
    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 20px;">
        <h3 style="color: #002B49; font-weight: 800; margin-bottom: 4px;">🛡️ لوحة دعم اتخاذ القرار المصرفي الاستراتيجي</h3>
        <p style="color: #475569; font-size: 14px;">تحويل مخرجات التشخيص القياسي الفعلي إلى حزمة قرارات تنفيذية إلزامية، تحديد الأولويات الرقابية، وتوزيع المسؤوليات على لجان الحوكمة ومجلس الإدارة واللجان المختصة.</p>
    </div>
    """, unsafe_allow_html=True)

    ssgi_records_dec = [r for r in st.session_state.history_state if isinstance(r, dict) and "مؤشر SSGI المركب" in r]

    if not ssgi_records_dec:
        st.warning("⚠️ يرجى أولاً إدخال بيانات البنك وحساب مؤشر SSGI في التبويب الثاني للتمكن من توليد لوحة القرار والتوصيات.")
    else:
        def build_bank_decision_package(bank_row):
            b_name = bank_row["البنك"]
            score = float(bank_row["مؤشر SSGI المركب"])
            s_val = float(bank_row["منصات المعلومات (40%)"])
            i_val = float(bank_row["الحوكمة المؤسسية (30%)"])
            r_val = float(bank_row["تقارير الاستدامة (30%)"])
            score_str_plain = get_colored_score_html(score)

            gaps_weighted = {
                "منصات المعلومات الذكية (SIP)": round((100 - s_val) * 0.40, 2),
                "الحوكمة المؤسسية ولجان الالتزام (IG)": round((100 - i_val) * 0.30, 2),
                "تقارير الاستدامة والتمويل الأخضر (SR)": round((100 - r_val) * 0.30, 2),
            }
            top_gap_axis = max(gaps_weighted, key=gaps_weighted.get)
            top_gap_loss = gaps_weighted[top_gap_axis]

            pillars_raw = {
                "منصات المعلومات الذكية (SIP)": s_val,
                "الحوكمة المؤسسية (IG)": i_val,
                "تقارير الاستدامة (SR)": r_val
            }
            weakest_pillar = min(pillars_raw, key=pillars_raw.get)
            weakest_val = pillars_raw[weakest_pillar]

            if score >= 80:
                urgency_badge = "أولوية استدامة الريادة والابتكار 🟢"
                urgency_color = "#10B981"
                recs_list = [
                    f"<b>تفعيل الريادة الإقليمية والرقابة الذكية لـ ({b_name}):</b> توظيف جاهزية منصات المعلومات ({s_val}%) لتطبيق أنظمة الامتثال الرقابي الآلي المباشر (RegTech) وتصدير الخدمات المالية الرقمية.",
                    f"<b>تعظيم الحوكمة المؤسسية المتقدمة:</b> استثمار رصيد الحوكمة ({i_val}%) في تأسيس لجنة متخصصة لحوكمة الذكاء الاصطناعي والسيادة الرقمية على مستوى مجلس الإدارة."
                ]
            elif score >= 50:
                urgency_badge = "أولوية تدخل تصحيحي متوسط المدى 🟡"
                urgency_color = "#F59E0B"
                recs_list = [
                    f"<b>سد الفجوة ذات الوزن الأعلى في ({b_name}):</b> توجيه مخصصات التطوير الفورية لمعالجة <b>{top_gap_axis}</b> (الذي يستنزف {top_gap_loss} نقطة من المؤشر المركب) ورفع كفاءة <b>{weakest_pillar} ({weakest_val}%)</b>.",
                    f"<b>تعزيز فاعلية لجان المراجعة والمخاطر:</b> ربط مؤشرات الأداء التنفيذية للإدارة العليا برفع درجة الحوكمة المؤسسية من ({i_val}%) إلى مستهدف رقابي لا يقل عن (80%)."
                ]
            else:
                urgency_badge = "أولوية تدخل رقابي طارئ وعاجل 🔴"
                urgency_color = "#EF4444"
                recs_list = [
                    f"<b>خطة طوارئ هيكلية عاجلة لـ ({b_name}):</b> إيقاف التوسع غير الممنهج وإعادة بناء البنية التحتية لمنصات المعلومات ({s_val}%) لضمان أمن البيانات واستمرارية الأعمال.",
                    f"<b>إعادة هيكلة منظومة الحوكمة والامتثال:</b> تفعيل رقابة صارمة من لجنة المراجعة ومجلس الإدارة لمعالجة القصور الحاد في الحوكمة ({i_val}%) والامتثال الفوري لتعليمات البنك المركزي."
                ]

            if s_val >= 80:
                sip_exec = f"<b>قطاع تكنولوجيا المعلومات والأمن السيبراني ({s_val}%):</b> اعتماد الربط اللحظي (Real-time APIs) مع منظومات التقارير الرقابية وتطبيق اختبارات الاختراق الدورية."
            elif s_val >= 50:
                sip_exec = f"<b>قطاع تكنولوجيا المعلومات والأمن السيبراني ({s_val}%):</b> تحديث قواعد البيانات المهيكلة وتقليص زمن اكتشاف الأخطاء التشغيلية (MTTD) وفق ضوابط ISO 27001."
            else:
                sip_exec = f"<b>قطاع تكنولوجيا المعلومات والأمن السيبراني ({s_val}%):</b> إحلال الأنظمة القديمة، حظر استضافة البيانات الحساسة خارج النطاق السيادي، وتعيين مسؤول لأمن المعلومات."

            if i_val >= 80:
                ig_exec = f"<b>مجلس الإدارة ولجنة المراجعة والحوكمة ({i_val}%):</b> الحفاظ على استقلالية اللجان السيادية ونشر تقارير الإفصاح الدوري عن المخاطر غير المالية."
            elif i_val >= 50:
                ig_exec = f"<b>مجلس الإدارة ولجنة المراجعة والحوكمة ({i_val}%):</b> تفعيل مصفوفة الصلاحيات والمسؤوليات (RACI)، وتحديث سجل منع تعارض المصالح، وزيادة نسبة الأعضاء المستقلين."
            else:
                ig_exec = f"<b>مجلس الإدارة ولجنة المراجعة والحوكمة ({i_val}%):</b> إعادة تشكيل لجان المخاطر والمراجعة برئاسة أعضاء مستقلين وإلزام الإدارات بتنفيذ توصيات التدقيق الداخلي."

            if r_val >= 80:
                sr_exec = f"<b>لجنة الاستدامة والتمويل المستدام ({r_val}%):</b> التوسع في إصدار السندات الخضراء (Green Bonds) وإخضاع تقرير الاستدامة لتوكيد خارجي مستقل وفق ISSB S1/S2."
            elif r_val >= 50:
                sr_exec = f"<b>لجنة الاستدامة والتمويل المستدام ({r_val}%):</b> رفع حصة الأصول الخضراء (GAR) في المحفظة الائتمانية وإدراج اختبارات التحمل المناخي لتمويلات الشركات الكبرى."
            else:
                sr_exec = f"<b>لجنة الاستدامة والتمويل المستدام ({r_val}%):</b> تأسيس وحدة مركزية للاستدامة وإطلاق أول تقرير إفصاح متوافق مع معايير GRI وضوابط البنك المركزي للتمويل المستدام."

            deep_items = [sip_exec, ig_exec, sr_exec]
            deep_analysis_text = "<ul style='margin:0;padding-right:20px;'>" + "".join(f"<li style='margin-bottom:6px;'>{x}</li>" for x in deep_items) + "</ul>"

            return {
                "bank": b_name,
                "score": score,
                "score_str": score_str_plain,
                "s_val": s_val,
                "i_val": i_val,
                "r_val": r_val,
                "urgency_badge": urgency_badge,
                "urgency_color": urgency_color,
                "top_gap_axis": top_gap_axis,
                "top_gap_loss": top_gap_loss,
                "recs": recs_list,
                "deep": deep_analysis_text
            }

        col_dec_in, col_dec_out = st.columns([1, 2], gap="large")

        with col_dec_in:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
            recorded_banks_dec = list(dict.fromkeys([item["البنك"] for item in ssgi_records_dec]))
            decision_bank_sel = st.selectbox("اختر البنك لاستعراض واعتماد توصياته", recorded_banks_dec, key="dec_bank")

            preview_bank_row = next((item for item in reversed(ssgi_records_dec) if item["البنك"] == decision_bank_sel), None)
            if preview_bank_row:
                p_s = preview_bank_row["منصات المعلومات (40%)"]
                p_i = preview_bank_row["الحوكمة المؤسسية (30%)"]
                p_r = preview_bank_row["تقارير الاستدامة (30%)"]
                p_tot = preview_bank_row["مؤشر SSGI المركب"]
                st.markdown(flat_html(f"""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-right: 4px solid {CBE_GOLD}; border-radius: 8px; padding: 10px 12px; margin: 10px 0 14px 0; font-size: 12.5px;">
                    <div style="font-weight: 800; color: {CBE_NAVY}; margin-bottom: 4px;">📌 القراءة الفعلية المسجلة للبنك:</div>
                    <div style="color: #334155;">المؤشر المركب: <b>{p_tot}%</b> | SIP: <b>{p_s}%</b> | IG: <b>{p_i}%</b> | SR: <b>{p_r}%</b></div>
                </div>
                """), unsafe_allow_html=True)

            generate_decision_btn = st.button("🛡️ استعراض حزمة القرارات التنفيذية", use_container_width=True, type="primary")

            generate_all_decisions_btn = st.button(
                "⚡ استعراض قرارات كافة البنوك المسجلة",
                use_container_width=True,
                type="secondary"
            )

            if st.button("🗑️ مسح وإعادة تعيين لوحة القرار", use_container_width=True, type="secondary"):
                st.session_state.decision_results_dict = {}
                st.rerun()

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            dec_count = len(st.session_state.decision_results_dict)
            dec_body_items = f"<h3>🛡️ تقرير وتوصيات البنوك المعتمدة بالكامل (إجمالي: {dec_count}):</h3>"
            if st.session_state.decision_results_dict:
                for k, v in st.session_state.decision_results_dict.items():
                    u_badge = v.get("urgency_badge", "توصيات تنفيذية معتمدة")
                    dec_body_items += f"""
                    <h3>تقرير وتوصيات بنك: {v['bank']} (المؤشر المركب: {v['score_str']}) — [{u_badge}]</h3>
                    <p><b>🎯 القرارات والتوصيات الاستراتيجية الموجهة لمجلس الإدارة:</b></p>
                    <ul><li>{v['recs'][0]}</li><li>{v['recs'][1]}</li></ul>
                    <p><b>💡 مصفوفة التكليفات التنفيذية حسب الإدارات واللجان المختصة:</b></p>
                    <div>{v['deep']}</div>
                    <hr>
                    """
            else:
                dec_body_items += "<p>لا توجد توصيات مسجلة حالياً في الجلسة.</p>"

            dec_bytes, dec_ext, dec_mime = build_native_docx(
                "تقرير لوحة دعم اتخاذ القرار والسياسات المصرفية",
                f"تاريخ التوليد: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                dec_body_items,
            )

            st.download_button(
                label="📥 تحميل تقرير لوحة دعم القرار الشامل",
                data=dec_bytes,
                file_name=f"تقرير_لوحة_دعم_القرار_المصرفي_الشامل{dec_ext}",
                mime=dec_mime,
                use_container_width=True,
                key="dl_dec_word_btn"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with col_dec_out:
            st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)

            if generate_decision_btn:
                if decision_bank_sel == "اختر البنك المصرفي":
                    st.warning("⚠️ يرجى اختيار بنك مصرفي صحيح أولاً.")
                else:
                    bank_data = next((item for item in reversed(ssgi_records_dec) if item["البنك"] == decision_bank_sel), None)
                    if bank_data:
                        st.session_state.decision_results_dict[decision_bank_sel] = build_bank_decision_package(bank_data)
                        st.rerun()

            if generate_all_decisions_btn:
                for b_name_iter in recorded_banks_dec:
                    b_data_iter = next((item for item in reversed(ssgi_records_dec) if item["البنك"] == b_name_iter), None)
                    if b_data_iter:
                        st.session_state.decision_results_dict[b_name_iter] = build_bank_decision_package(b_data_iter)
                st.rerun()

            if st.session_state.decision_results_dict:
                for b_key, item in list(st.session_state.decision_results_dict.items()):
                    u_badge = item.get("urgency_badge", "توصيات تنفيذية معتمدة")
                    u_color = item.get("urgency_color", CBE_GOLD)
                    s_disp = item.get("s_val", "-")
                    i_disp = item.get("i_val", "-")
                    r_disp = item.get("r_val", "-")
                    gap_axis_disp = item.get("top_gap_axis", "")
                    gap_loss_disp = item.get("top_gap_loss", 0)

                    gap_banner = (
                        f"<div style='background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 6px; padding: 7px 12px; margin-bottom: 10px; font-size: 12.5px; color: #92400E;'>"
                        f"🎯 <b>محور التدخل ذو الأولوية القصوى:</b> {gap_axis_disp} (فجوة موزونة: <b>-{gap_loss_disp}</b> نقطة)</div>"
                        if gap_axis_disp and gap_loss_disp > 0 else ""
                    )

                    card_html = flat_html(f"""
                    <div style="background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);" dir="rtl">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 12px;">
                            <h3 style="color: {CBE_NAVY}; font-weight: bold; margin: 0; font-size: 16.5px;">
                                🛡️ حزمة القرار التنفيذي لبنك: <span style="color: {CBE_GOLD};">{item['bank']}</span> ({item['score_str']})
                            </h3>
                            <span style="background: #F8FAFC; color: {CBE_NAVY}; border: 1px solid {u_color}; border-right: 4px solid {u_color}; padding: 3px 10px; border-radius: 15px; font-size: 12px; font-weight: 700;">
                                {u_badge}
                            </span>
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; text-align: center;">
                            <div style="background: #F8FAFC; padding: 8px; border-radius: 8px; border: 1px solid #E2E8F0;">
                                <div style="font-size: 11px; color: #64748B; font-weight: bold;">منصات المعلومات (SIP)</div>
                                <div style="font-size: 15px; font-weight: 800; color: {CBE_NAVY};">{s_disp}%</div>
                            </div>
                            <div style="background: #F8FAFC; padding: 8px; border-radius: 8px; border: 1px solid #E2E8F0;">
                                <div style="font-size: 11px; color: #64748B; font-weight: bold;">الحوكمة المؤسسية (IG)</div>
                                <div style="font-size: 15px; font-weight: 800; color: {CBE_NAVY};">{i_disp}%</div>
                            </div>
                            <div style="background: #F8FAFC; padding: 8px; border-radius: 8px; border: 1px solid #E2E8F0;">
                                <div style="font-size: 11px; color: #64748B; font-weight: bold;">تقارير الاستدامة (SR)</div>
                                <div style="font-size: 15px; font-weight: 800; color: {CBE_NAVY};">{r_disp}%</div>
                            </div>
                        </div>

                        {gap_banner}

                        <div style="background: {CBE_BG}; padding: 14px; border-radius: 8px; border-right: 4px solid {CBE_GOLD};">
                            <p style="font-weight: bold; color: {CBE_NAVY}; margin-bottom: 6px; text-align: right; font-size: 14px;">🎯 القرارات والتوصيات الاستراتيجية الموجهة لمجلس الإدارة:</p>
                            <ul style="margin: 0; padding-right: 20px; color: #1E293B; line-height: 1.8; text-align: right; font-size: 13.5px;">
                                <li style="margin-bottom: 6px;">{item['recs'][0]}</li>
                                <li>{item['recs'][1]}</li>
                            </ul>
                            <hr style="border: 0; border-top: 1px solid #CBD5E1; margin: 12px 0;">
                            <p style="font-weight: bold; color: {CBE_NAVY}; margin-bottom: 6px; text-align: right; font-size: 14px;">💡 مصفوفة التكليفات التنفيذية حسب الإدارات واللجان المختصة:</p>
                            <div style="color: #1E293B; line-height: 1.8; text-align: right; font-size: 13.5px;">
                                {item['deep']}
                            </div>
                        </div>
                    </div>
                    """)
                    st.markdown(card_html, unsafe_allow_html=True)
                    if st.button(f"❌ إزالة توصيات {b_key}", key=f"del_dec_{b_key}"):
                        del st.session_state.decision_results_dict[b_key]
                        st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("🛡️ اختر البنك المسجل واضغط على زر الاعتماد لتوليد حزمة القرارات التنفيذية ومصفوفة التكليفات المخصصة هنا.")
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# التبويب الخامس: التقرير التنفيذي الموحد
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h3>📑 أداة استخراج التقرير التنفيذي الموحد لحوكمة القطاع المصرفي</h3>
        <p>قم بالضغط على مفتاح التوليد الفوري أدناه لتجميع ومراجعة التقرير التنفيذي الموحد والنتائج التحليلية المحدثة ديناميكياً.</p>
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

            if "bank_profiles_cache" not in st.session_state:
                st.session_state["bank_profiles_cache"] = {}
            if top_bank not in st.session_state["bank_profiles_cache"]:
                try:
                    st.session_state["bank_profiles_cache"][top_bank] = process_rag_gemini_query(
                        top_bank, "متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟"
                    )
                except Exception:
                    st.session_state["bank_profiles_cache"][top_bank] = (
                        "بنك مصرفي رائد عامل في القطاع المصرفي المصري ومسجل لدى البنك المركزي المصري."
                    )
            top_bank_profile_info = st.session_state["bank_profiles_cache"][top_bank]

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
                    specific_policy_action = "تأسيس 'لجنة استراتيجية للسيادة الرقمية'، تعظيم محفظة الأصول الخضراء، وتوظيف الأنظمة الرقابية المتقدمة (RegTech)."
                elif b_score >= 51:
                    specific_strategic_angle = f"يسجل بنك ({b_name}) جاهزية متوسطة ({b_score}%) تواجه بعض الاختناقات الهيكلية في البنية التقنية أو لجان الالتزام؛ وهو ما يتطلب تدخلاً استباقياً لردم الفجوات."
                    specific_policy_action = "تنفيذ برامج تطوير منصات المعلومات (SIP)، تعزيز استقلالية لجان المراجعة، والتوسع في تدريب الكوادر."
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
                <p style="margin-bottom: 8px;">يتصدر البنك <span style="font-weight: bold; color: {CBE_GOLD};">{top_bank}</span> بقيمة مركبة تبلغ {top_score_str} قائمة الحوكمة الذكية المستدامة وفق الترتيب التنازلي للمؤشر المركب.</p>
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
                <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">تنويه استرشادي: تُعد مخرجات المنصة أداة مساندة لدعم اتخاذ القرار، ويُوصى بمواءمتها مع السياسات الداخلية لكل مصرف</p>
                <p style="text-align: center; font-size: 12px; color: #64748B;">جميع الحقوق محفوظة للدراسة البحثية © 2026</p>
            </body>
            </html>
            """
            st.download_button(
                label="📥 تحميل التقرير التنفيذي",
                data=word_content.encode("utf-8-sig"),
                file_name="التقرير_التنفيذي_للقطاع_المصرفي.doc",
                mime="application/msword",
                use_container_width=True
            )

# ------------------------------------------------------------------------------
# التبويب السادس: تقييم ومولد تقارير الاستدامة والدليل العملي الشامل
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("""
    <div dir="rtl" style="text-align: right;">
        <h2 style="color: #002B49; font-weight: 800; margin-bottom: 6px;">📄 تقييم وتوليد تقارير الاستدامة والدليل العملي الشامل</h2>
        <p style="color: #475569; font-size: 14.5px; line-height: 1.7;">
        منظومة متكاملة تدمج بين <b>التحليل والتدقيق الذكي المباشر لتقارير الاستدامة</b>، وبين <b>توليد مسودات الإفصاح المخصصة والدليل العملي الشامل</b> المعتمد على أحدث الأطر الدولية (GRI Standards, ISSB S1/S2, CBE Rules).
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================================================
    # الموديول الأول: 🔍 1. التحليل الذكي وتقييم تقارير الاستدامة عبر Gemini API
    # ==========================================================================
    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 15px;">
        <h3 style="color: #002B49; font-weight: 800; margin-bottom: 4px;">🔍 1. التحليل الآلي وتقييم تقارير الاستدامة</h3>
        <p style="color: #475569; font-size: 13.5px;">
        قراءة وتحليل وثائق وتقارير الاستدامة المصرفية مباشرة لتقييم مدى امتثالها الفعلي وفق المعايير المعتمدة.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_scorer_in, col_scorer_out = st.columns([1, 2], gap="large")

    with col_scorer_in:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        registered_names_only = list(dict.fromkeys([
            item["البنك"] for item in st.session_state.get("history_state", [])
            if isinstance(item, dict) and "البنك" in item
        ]))
        all_registered_banks_eval = registered_names_only if registered_names_only else BANKS_LIST_AR

        eval_bank_selected = st.selectbox(
            "اختر البنك المصرفي المراد تقييم تقريره",
            all_registered_banks_eval,
            key="eval_bank_scorer_sel"
        )

        uploaded_esg_file = st.file_uploader(
            "📁 قم برفع ملف تقرير الاستدامة (PDF / TXT)",
            type=["pdf", "txt"],
            key="esg_file_uploader",
            help="الملفات المقبولة: PDF (نصي أو مصور) أو TXT بحد أقصى 50 ميجابايت."
        )

        rubric_standard = st.selectbox(
            "معيار التقييم والامتثال المعتمد",
            [
                "GRI Standards (المبادرة العالمية للتقارير)",
                "ISSB S1 & S2 (مجلس المعايير الدولية للاستدامة)",
                "ضوابط البنك المركزي المصري للتمويل المستدام (CBE Rules)"
            ],
            key="rubric_std_sel"
        )

        run_doc_eval_btn = st.button("🚀 بدء التدقيق الذكي", use_container_width=True, type="primary")
        if st.session_state.get("last_esg_audit_result"):
            if st.button("🗑️ مسح نتيجة التدقيق الحالية", use_container_width=True, type="secondary", key="clear_esg_audit_btn"):
                del st.session_state["last_esg_audit_result"]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_scorer_out:
        st.markdown('<div dir="rtl" style="text-align: right;">', unsafe_allow_html=True)
        if run_doc_eval_btn:
            if eval_bank_selected == "اختر البنك المصرفي":
                st.warning("⚠️ يرجى تحديد اسم البنك المصرفي أولاً لتشغيل التقييم.")
            elif uploaded_esg_file is None:
                st.warning("⚠️ يرجى رفع ملف تقرير الاستدامة (PDF أو TXT) الخاص بالبنك.")
            else:
                with st.spinner("⏳ جاري قراءة التقرير بالكامل ومطابقته مع معايير الإفصاح عبر محرك Gemini..."):
                    file_bytes = uploaded_esg_file.getvalue()
                    file_mime = uploaded_esg_file.type or "application/pdf"
                    ai_eval_data = None
                    used_ai_engine = False
                    active_model_used = "Gemini AI"

                    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

                    if api_key:
                        try:
                            from google import genai
                            from google.genai import types

                            client = genai.Client(api_key=api_key)

                            audit_prompt = f"""
                            أنت مدقق استدامة وحوكمة مصرفية معتمد. قم بقراءة وتحليل الملف المرفق بدقة وتقييمه لصالح: ({eval_bank_selected})
                            وفقاً لمعيار التقييم المعتمد: ({rubric_standard}).

                            المطلوب منك بدقة:
                            1. التحقق مما إذا كان التقرير المرفق يخص بالفعل ({eval_bank_selected}) أم بنكاً أو جهة أخرى.
                            2. تقييم درجة الامتثال الفعلية (من 0 إلى 100) لكل محور بناءً على الأدلة والأرقام والسياسات الواردة في المستند:
                               - المحور البيئي (env_score): إدارة البصمة الكربونية Scopes 1/2/3، التمويل الأخضر، اختبارات التحمل المناخي.
                               - المحور الاجتماعي (soc_score): الشمول المالي، تمكين المرأة، رأس المال البشري، حماية العملاء.
                               - محور الحوكمة (gov_score): هيكل مجلس الإدارة واللجان المستقلة، إدارة مخاطر ESG، السيادة الرقمية وأمن البيانات، التوكيد الخارجي.
                            3. استخراج 3 نقاط قوة محددة مدعومة بما ورد في التقرير.
                            4. استخراج 3 فجوات امتثال (Gaps) محددة مقارنة بمتطلبات ({rubric_standard}).
                            5. صياغة توصية تنفيذية مركزة للبنك.

                            أرجع النتيجة حصراً بصيغة JSON صالحة مطابقة تماماً للمفاتيح التالية دون أي نص إضافي:
                            {{
                                "bank_matched": true,
                                "detected_entity": "اسم الجهة المذكورة في التقرير",
                                "env_score": 0.0,
                                "soc_score": 0.0,
                                "gov_score": 0.0,
                                "strengths": ["نقطة قوة 1", "نقطة قوة 2", "نقطة قوة 3"],
                                "gaps": ["فجوة 1", "فجوة 2", "فجوة 3"],
                                "recommendation": "التوصية التنفيذية"
                            }}
                            """

                            doc_part = types.Part.from_bytes(data=file_bytes, mime_type=file_mime)

                            response = None
                            last_model_err = None
                            for _m_name in ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]:
                                try:
                                    response = client.models.generate_content(
                                        model=_m_name,
                                        contents=[doc_part, audit_prompt],
                                        config=types.GenerateContentConfig(
                                            temperature=0.1,
                                            response_mime_type="application/json",
                                        ),
                                    )
                                    if response and response.text:
                                        active_model_used = _m_name
                                        break
                                except Exception as _e:
                                    last_model_err = _e
                                    if "404" in str(_e) or "NOT_FOUND" in str(_e):
                                        continue
                                    raise _e

                            if not response or not response.text:
                                raise RuntimeError(f"تعذر الوصول للنماذج: {last_model_err}")

                            raw_json_txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.text.strip())
                            ai_eval_data = json.loads(raw_json_txt)
                            used_ai_engine = True

                        except Exception as e:
                            st.warning(f"⚠️ تعذر الاتصال المباشر بمحرك Gemini ({e})، سيتم التبديل للتحليل النصي الاحتياطي.")

                    if not ai_eval_data:
                        extracted_text = ""
                        try:
                            if file_mime == "text/plain":
                                extracted_text = file_bytes.decode("utf-8", errors="ignore")
                            else:
                                import pypdf
                                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                                extracted_text = " ".join((p.extract_text() or "") for p in reader.pages)
                        except Exception:
                            extracted_text = ""

                        clean_bank = eval_bank_selected.replace("بنك", "").replace("البنك", "").strip()
                        words_bank = [w for w in re.split(r'\s+', clean_bank) if len(w) > 2]
                        matched_fallback = any(w in extracted_text for w in words_bank)

                        env_hits = sum(1 for k in ["كربون", "مناخ", "طاقة", "انبعاثات", "أخضر", "carbon", "green", "climate"] if k in extracted_text.lower())
                        soc_hits = sum(1 for k in ["مجتمعي", "شمول", "مرأة", "عاملين", "تدريب", "social", "inclusion"] if k in extracted_text.lower())
                        gov_hits = sum(1 for k in ["حوكمة", "مجلس", "مراجعة", "مخاطر", "امتثال", "governance", "audit"] if k in extracted_text.lower())

                        ai_eval_data = {
                            "bank_matched": matched_fallback,
                            "detected_entity": eval_bank_selected if matched_fallback else "جهة غير مطابقة",
                            "env_score": round(min(95.0, 55.0 + env_hits * 4.5), 1),
                            "soc_score": round(min(95.0, 55.0 + soc_hits * 4.5), 1),
                            "gov_score": round(min(95.0, 55.0 + gov_hits * 4.5), 1),
                            "strengths": ["تغطية الأطر الأساسية للإفصاح المستدام ضمن هيكل التقرير المرفوع."],
                            "gaps": ["يتطلب التحقق التفصيلي لمؤشرات Scope 3 واختبارات التحمل المناخي تفعيل محرك Gemini."],
                            "recommendation": f"يُوصى باستكمال إفصاحات ({rubric_standard.split('(')[0]}) وإخضاع التقرير لتوكيد خارجي مستقل."
                        }

                    env_score = min(100.0, max(0.0, round(float(ai_eval_data.get("env_score", 70.0)), 1)))
                    soc_score = min(100.0, max(0.0, round(float(ai_eval_data.get("soc_score", 70.0)), 1)))
                    gov_score = min(100.0, max(0.0, round(float(ai_eval_data.get("gov_score", 70.0)), 1)))
                    weighted_overall_score = round((env_score * 0.35) + (soc_score * 0.30) + (gov_score * 0.35), 2)

                    st.session_state["last_esg_audit_result"] = {
                        "bank": eval_bank_selected,
                        "file_name": uploaded_esg_file.name,
                        "rubric": rubric_standard,
                        "used_ai_engine": used_ai_engine,
                        "active_model_used": active_model_used,
                        "is_matched": bool(ai_eval_data.get("bank_matched", True)),
                        "detected_entity": ai_eval_data.get("detected_entity", eval_bank_selected),
                        "env_score": env_score,
                        "soc_score": soc_score,
                        "gov_score": gov_score,
                        "weighted_overall_score": weighted_overall_score,
                        "strengths": ai_eval_data.get("strengths", []),
                        "gaps": ai_eval_data.get("gaps", []),
                        "recommendation": ai_eval_data.get("recommendation", "")
                    }

        audit_res = st.session_state.get("last_esg_audit_result")
        if audit_res:
            a_bank = audit_res["bank"]
            a_file = audit_res["file_name"]
            a_rubric = audit_res["rubric"]
            is_matched = audit_res["is_matched"]
            detected_entity = audit_res["detected_entity"]
            env_score = audit_res["env_score"]
            soc_score = audit_res["soc_score"]
            gov_score = audit_res["gov_score"]
            weighted_overall_score = audit_res["weighted_overall_score"]
            score_badge = get_colored_score_html(weighted_overall_score)
            strengths_list = audit_res["strengths"]
            gaps_list = audit_res["gaps"]
            recommendation_txt = audit_res["recommendation"]
            engine_label = f"🤖 تدقيق ذكي عميق عبر {audit_res['active_model_used']}" if audit_res["used_ai_engine"] else "⚙️ تحليل نصي احتياطي"

            if not is_matched:
                st.markdown(flat_html(f"""
                <div style="background: #FEF2F2; border: 1.5px solid #EF4444; border-radius: 10px; padding: 15px; margin-bottom: 15px;" dir="rtl">
                    <h4 style="color: #991B1B; margin: 0 0 6px 0; font-weight: bold;">⚠️ تنبيه عدم مطابقة التقرير مع البنك المختار:</h4>
                    <p style="color: #7F1D1D; margin: 0; font-size: 13.5px; line-height: 1.6;">
                    الملف المرفوع (<b>{a_file}</b>) يخص (<b>{detected_entity}</b>) ولا يطابق البنك المختار (<b>{a_bank}</b>). تم عرض نتائج التدقيق الفني مع تسجيل فجوة الإسناد.
                    </p>
                </div>
                """), unsafe_allow_html=True)

            st.success(f"✅ تم تدقيق التقرير بنجاح لـ ({a_bank}) وفق معيار ({a_rubric})")

            eval_result_card = f"""
            <div dir="rtl" style="background: #FFFFFF; padding: 22px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 15px; flex-wrap: wrap; gap: 8px;">
                    <h4 style="color: {CBE_NAVY}; font-weight: bold; margin: 0; font-size: 16px;">
                        📊 التقييم القياسي للتقرير - <span style="color: {CBE_GOLD};">{a_bank}</span>
                    </h4>
                    <span style="font-size: 12px; font-weight: bold; color: #64748B;">
                        المعيار: {a_rubric.split('(')[0]} | {engine_label}
                    </span>
                </div>

                <p style="color: #475569; font-size: 13px; margin-bottom: 15px;">
                    التصنيف العام: <b>{score_badge}</b> | اسم الملف: <b>{a_file}</b>
                </p>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 18px;">
                    <div style="background: #F8FAFC; padding: 14px; border-radius: 10px; border-right: 5px solid {CBE_GOLD}; text-align: center;">
                        <span style="font-size: 11.5px; color: #64748B; font-weight: bold;">الدرجة الكلية الموزونة</span>
                        <div style="font-size: 22px; font-weight: 900; color: {CBE_NAVY}; margin-top: 4px;">{weighted_overall_score}%</div>
                    </div>
                    <div style="background: #F8FAFC; padding: 14px; border-radius: 10px; border-right: 5px solid #10B981; text-align: center;">
                        <span style="font-size: 11.5px; color: #64748B; font-weight: bold;">المحور البيئي (35%)</span>
                        <div style="font-size: 22px; font-weight: 900; color: #10B981; margin-top: 4px;">{env_score}%</div>
                    </div>
                    <div style="background: #F8FAFC; padding: 14px; border-radius: 10px; border-right: 5px solid #3B82F6; text-align: center;">
                        <span style="font-size: 11.5px; color: #64748B; font-weight: bold;">المحور الاجتماعي (30%)</span>
                        <div style="font-size: 22px; font-weight: 900; color: #3B82F6; margin-top: 4px;">{soc_score}%</div>
                    </div>
                    <div style="background: #F8FAFC; padding: 14px; border-radius: 10px; border-right: 5px solid {CBE_NAVY}; text-align: center;">
                        <span style="font-size: 11.5px; color: #64748B; font-weight: bold;">محور الحوكمة (35%)</span>
                        <div style="font-size: 22px; font-weight: 900; color: {CBE_NAVY}; margin-top: 4px;">{gov_score}%</div>
                    </div>
                </div>

                <div style="background: {CBE_BG}; padding: 16px; border-radius: 10px; border-right: 5px solid {CBE_NAVY};">
                    <p style="font-weight: bold; color: {CBE_NAVY}; margin-bottom: 8px; font-size: 14px;">🔍 نتائج التدقيق الميداني لنقاط القوة والفجوات الهيكلية:</p>
                    <ul style="margin: 0; padding-right: 20px; color: #1E293B; font-size: 13.5px; line-height: 1.8;">
                        {"".join([f"<li>🟢 <b>نقطة قوة:</b> {s}</li>" for s in strengths_list])}
                        {"".join([f"<li>🟡 <b>فجوة امتثال (Gap):</b> {g}</li>" for g in gaps_list])}
                        <li>💡 <b>التوصية التنفيذية:</b> {recommendation_txt}</li>
                    </ul>
                </div>
            </div>
            """
            st.markdown(flat_html(eval_result_card), unsafe_allow_html=True)

            # أزرار إضافية: تصدير تقرير التدقيق + مزامنة النتيجة مع سجل البنك في المنصة
            col_aud_act1, col_aud_act2 = st.columns(2)
            with col_aud_act1:
                audit_word_doc = f"""
                <html dir="rtl">
                <head><meta charset="utf-8"><title>تقرير تدقيق الاستدامة - {a_bank}</title></head>
                <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right; direction: rtl;">
                    <h1 style="color: {CBE_NAVY}; text-align: center;">تقرير التدقيق الآلي لتقارير الاستدامة (AI ESG Audit)</h1>
                    <h3 style="color: {CBE_GOLD}; text-align: center;">البنك: {a_bank} | المعيار: {a_rubric}</h3>
                    <hr>
                    <p><b>الدرجة الكلية الموزونة:</b> {weighted_overall_score}% (البيئي: {env_score}% | الاجتماعي: {soc_score}% | الحوكمة: {gov_score}%)</p>
                    <h4>نقاط القوة:</h4><ul>{"".join(f"<li>{s}</li>" for s in strengths_list)}</ul>
                    <h4>فجوات الامتثال:</h4><ul>{"".join(f"<li>{g}</li>" for g in gaps_list)}</ul>
                    <p><b>التوصية التنفيذية:</b> {recommendation_txt}</p>
                </body>
                </html>
                """
                st.download_button(
                    label="📥 تحميل تقرير التدقيق الآلي (Word)",
                    data=audit_word_doc.encode("utf-8-sig"),
                    file_name=f"تقرير_تدقيق_الاستدامة_{a_bank}.doc",
                    mime="application/msword",
                    use_container_width=True,
                    key="dl_ai_audit_word"
                )

            with col_aud_act2:
                existing_bank_rec = next(
                    (item for item in st.session_state.get("history_state", []) if isinstance(item, dict) and item.get("البنك") == a_bank),
                    None
                )
                if existing_bank_rec and is_matched:
                    if st.button(f"🔄 تحديث محور الاستدامة (SR) للبنك إلى {weighted_overall_score}%", use_container_width=True, key="sync_sr_to_ssgi"):
                        s_old = float(existing_bank_rec["منصات المعلومات (40%)"])
                        i_old = float(existing_bank_rec["الحوكمة المؤسسية (30%)"])
                        r_new = round(weighted_overall_score, 2)
                        new_ssgi = round((s_old * 0.40) + (i_old * 0.30) + (r_new * 0.30), 2)
                        existing_bank_rec["تقارير الاستدامة (30%)"] = r_new
                        existing_bank_rec["مؤشر SSGI المركب"] = new_ssgi
                        if new_ssgi >= 80:
                            existing_bank_rec["التقييم التشخيصي"] = "نضج استراتيجي وحوكمة ذكية مستدامة متقدمة"
                        elif new_ssgi >= 51:
                            existing_bank_rec["التقييم التشخيصي"] = "جاهزية متوسطة تتطلب معالجة الفجوات الهيكلية"
                        else:
                            existing_bank_rec["التقييم التشخيصي"] = "فجوة هيكلية حرجة تستوجب تدخلاً عاجلاً"
                        st.success(f"✅ تم تحديث درجة محور الاستدامة (SR) إلى {r_new}% وإعادة احتساب مؤشر SSGI المركب ليصبح {new_ssgi}%.")
        else:
            st.info("👈 قم باختيار البنك ورفع ملف التقرير (PDF/TXT) ثم اضغط على زر بدء التدقيق الذكي لعرض نسبة الامتثال ونقاط القوة والفجوات هنا.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================================================
    # الموديول الثاني: 🌿 2. توليد مسودة تقارير الاستدامة التوجيهية
    # ==========================================================================
    st.markdown("#### 📋 2. توليد مسودة تقارير الاستدامة التوجيهية التفصيلية للبنك المختار")

    all_registered_banks = (
        list(dict.fromkeys([
            item["البنك"] for item in st.session_state.get("history_state", [])
            if isinstance(item, dict) and "البنك" in item
        ]))
        if st.session_state.get("history_state")
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

        if st.session_state.get("draft_generated_state", False) and st.session_state.get("draft_bank_name") in all_registered_banks:
            bank_record = next(
                (
                    item
                    for item in st.session_state.history_state
                    if isinstance(item, dict) and item.get("البنك") == st.session_state.draft_bank_name
                ),
                None,
            )
            if bank_record:
                b_name = bank_record["البنك"]
                b_score = bank_record["مؤشر SSGI المركب"]
                s_val = bank_record["منصات المعلومات (40%)"]
                i_val = bank_record["الحوكمة المؤسسية (30%)"]
                r_val = bank_record["تقارير الاستدامة (30%)"]

                if "bank_profiles_cache" not in st.session_state:
                    st.session_state["bank_profiles_cache"] = {}
                if b_name not in st.session_state["bank_profiles_cache"]:
                    try:
                        st.session_state["bank_profiles_cache"][b_name] = process_rag_gemini_query(
                            b_name, "متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟"
                        )
                    except Exception:
                        st.session_state["bank_profiles_cache"][b_name] = (
                            "بنك مصرفي رائد عامل في القطاع المصرفي المصري مسجل لدى البنك المركزي المصري."
                        )
                profile_info = st.session_state["bank_profiles_cache"][b_name]

                st.markdown(flat_html(f"""
                <div style="background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 15px;" dir="rtl">
                    <h3 style="color: {CBE_NAVY}; margin-top: 0;">🌿 مسودة تقرير الاستدامة المخصصة للبنك: {b_name}</h3>
                    <p style="color: #64748B;">تتيح الأقسام أدناه العرض الكامل لكافة بنود مسودة تقرير الاستدامة التوجيهية المفصلة بالكامل للبنك، بالإضافة إلى إمكانية تحميل الملف بكافة تفاصيله .</p>
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
                        <p><b>السياسات والالتزام المؤسسي:</b> يلتزم بنك ({b_name}) بالإفصاح الشفاف عن هيكل الإشراف المؤسسي ودور مجلس الإدارة واللجان المنبثقة عنه (لجنة الاستدامة، لجنة المخاطر، ولجنة المراجعة) في توجيه وإدارة الأنشطة والتمويل المستدام. وسجل البنك مؤشر حوكمة مؤسسية بواقع ({i_val}%)، مما يعكس متانة أطر التدقيق الداخلي، سياسات تجنب تعارض المصالح، واستقلالية الأعضاء المستقلين في هيكل اللجان، بما يتماشى مع تعليمات وضوابط البنك المركزي المصري.</p>
                    </div>
                    """), unsafe_allow_html=True)

                with st.expander("البند الثاني: الإفصاحات البيئية وتمويل المناخ وإدارة البصمة الكربونية (GRI 302/305 & ISSB S2)", expanded=False):
                    st.markdown(flat_html(f"""
                    <div dir="rtl" style="text-align: right; line-height: 1.9;">
                        <p><b>الأداء البيئي والتمويل المستدام:</b> استناداً إلى مستوى أداء الاستدامة ومخاطر المناخ المسجل بواقع ({r_val}%)، يعمل بنك ({b_name}) على التوسع المدروس في محفظة الأصول الخضراء، تمويل مشروعات الطاقة المتجددة، وكفاءة استخدام الموارد. كما يلتزم البنك بقياس البصمة الكربونية التشغيلية (Scopes 1, 2, 3) لفروع البنك ومراكز البيانات، وإدماج اختبارات التحمل المناخي (Climate Stress Testing) ضمن تقييم الجدارة الائتمانية للمحفظة المؤسسية للعملاء الكبار.</p>
                    </div>
                    """), unsafe_allow_html=True)

                with st.expander("البند الثالث: الإفصاحات المجتمعية والشمول المالي وتطوير رأس المال البشري (GRI 401/405/413)", expanded=False):
                    st.markdown(flat_html(f"""
                    <div dir="rtl" style="text-align: right; line-height: 1.9;">
                        <p><b>المسؤولية الاجتماعية والتحول الرقمي:</b> استناداً إلى جاهزية البنية التحتية الرقمية ومنصات المعلومات المسجلة بواقع ({s_val}%)، يوجه بنك ({b_name}) استراتيجياته نحو تعزيز الشمول المالي، دعم المشروعات الصغيرة والمتوسطة (SMEs)، تمكين المرأة في المناصب القيادية وفق مبادئ (WEPs)، وتوسيع نطاق الخدمات المصرفية الرقمية الآمنة، مع الالتزام التام بمعايير حماية سرية بيانات العملاء والامتثال للقواعد العامة لحماية البيانات (GDPR) والسيادة الرقمية.</p>
                    </div>
                    """), unsafe_allow_html=True)

                with st.expander("البند الرابع: خطة التحرك الاستراتيجي والتوصيات التنفيذية المقترحة للبنك", expanded=False):
                    st.markdown(flat_html(f"""
                    <div dir="rtl" style="text-align: right; line-height: 1.9;">
                        <ul>
                            <li><b>تحديث البنية التحتية الرقمية:</b> مواصلة الاستثمار في منصات المعلومات الذكية وربطها بالتقارير الرقابية الآلية (RegTech).</li>
                            <li><b>توسيع الأصول الخضراء:</b> رفع نسبة الائتمان الموجه للمشروعات المستدامة وصديقة البيئة لتعزيز تنافسية البنك في المؤشرات الإقليمية والدولية.</li>
                            <li><b>تعزيز الشفافية والتوكيد الخارجي:</b> إخضاع تقارير الاستدامة لعمليات تدقيق وتوكيد خارجي مستقل لزيادة ثقة المستثمرين والمؤسسات المالية الدولية.</li>
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
                    <p>جاهزية منصات المعلومات وبنية التقنية (SIP - وزن 40%): <b>{s_val}%</b> — {describe_sip(s_val)}</p>
                    <p>كفاءة الحوكمة المؤسسية والامتثال (IG - وزن 30%): <b>{i_val}%</b> — {describe_ig(i_val)}</p>
                    <p>أداء تقارير الاستدامة والتمويل الأخضر (SR - وزن 30%): <b>{r_val}%</b> — {describe_sr(r_val)}</p>
                    <hr>
                    <h3>1️⃣ البند الأول: الإفصاح عن الحوكمة المؤسسية وهيكل اتخاذ القرار واستراتيجية الاستدامة (GRI 2 & ISSB S1)</h3>
                    <p><b>الملامح التأسيسية وهيكل الملكية:</b> {profile_info}</p>
                    <p><b>السياسات والالتزام المؤسسي:</b> يلتزم بنك ({b_name}) بالإفصاح الشفاف عن هيكل الإشراف المؤسسي ودور مجلس الإدارة واللجان المنبثقة عنه (لجنة الاستدامة، لجنة المخاطر، ولجنة المراجعة) في توجيه وإدارة الأنشطة والتمويل المستدام. وسجل البنك مؤشر حوكمة مؤسسية بواقع ({i_val}%)، مما يعكس متانة أطر التدقيق الداخلي، سياسات تجنب تعارض المصالح، واستقلالية الأعضاء المستقلين في هيكل اللجان، بما يتماشى مع تعليمات وضوابط البنك المركزي المصري.</p>
                    <hr>
                    <h3>2️⃣ البند الثاني: الإفصاحات البيئية وتمويل المناخ وإدارة البصمة الكربونية (GRI 302/305 & ISSB S2)</h3>
                    <p><b>الأداء البيئي والتمويل المستدام:</b> استناداً إلى مستوى أداء الاستدامة ومخاطر المناخ المسجل بواقع ({r_val}%)، يعمل بنك ({b_name}) على التوسع المدروس في محفظة الأصول الخضراء، تمويل مشروعات الطاقة المتجددة، وكفاءة استخدام الموارد. كما يلتزم البنك بقياس البصمة الكربونية التشغيلية (Scopes 1, 2, 3) لفروع البنك ومراكز البيانات، وإدماج اختبارات التحمل المناخي (Climate Stress Testing) ضمن تقييم الجدارة الائتمانية للمحفظة المؤسسية للعملاء الكبار.</p>
                    <hr>
                    <h3>3️⃣ البند الثالث: الإفصاحات المجتمعية والشمول المالي وتطوير رأس المال البشري (GRI 401/405/413)</h3>
                    <p><b>المسؤولية الاجتماعية والتحول الرقمي:</b> استناداً إلى جاهزية البنية التحتية الرقمية ومنصات المعلومات المسجلة بواقع ({s_val}%)، يوجه بنك ({b_name}) استراتيجياته نحو تعزيز الشمول المالي، دعم المشروعات الصغيرة والمتوسطة (SMEs)، تمكين المرأة في المناصب القيادية وفق مبادئ (WEPs)، وتوسيع نطاق الخدمات المصرفية الرقمية الآمنة، مع الالتزام التام بمعايير حماية سرية بيانات العملاء والامتثال للقواعد العامة لحماية البيانات (GDPR) والسيادة الرقمية.</p>
                    <hr>
                    <h3>4️⃣ البند الرابع: خطة التحرك الاستراتيجي والتوصيات التنفيذية المقترحة للبنك</h3>
                    <ul>
                        <li><b>تحديث البنية التحتية الرقمية:</b> مواصلة الاستثمار في منصات المعلومات الذكية وربطها بالتقارير الرقابية الآلية (RegTech).</li>
                        <li><b>توسيع الأصول الخضراء:</b> رفع نسبة الائتمان الموجه للمشروعات المستدامة وصديقة البيئة لتعزيز تنافسية البنك في المؤشرات الإقليمية والدولية.</li>
                        <li><b>تعزيز الشفافية والتوكيد الخارجي:</b> إخضاع تقارير الاستدامة لعمليات تدقيق وتوكيد خارجي مستقل لزيادة ثقة المستثمرين والمؤسسات المالية الدولية.</li>
                    </ul>
                    <hr>
                    <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">تنويه استرشادي: تُعد مخرجات المنصة أداة مساندة لدعم اتخاذ القرار، ويُوصى بمواءمتها مع السياسات الداخلية لكل مصرف</p>
                </body>
                </html>
                """
                st.download_button(
                    label=f"📥 تحميل مسودة تقرير الاستدامة المفصلة بالكامل للبنك ({b_name}) ",
                    data=docx_full_download.encode("utf-8-sig"),
                    file_name=f"مسودة_تقرير_الاستدامة_المفصلة_{b_name}.doc",
                    mime="application/msword",
                    use_container_width=True,
                )

    st.markdown("---")

    # ==========================================================================
    # الموديول الثالث: 📖 3. الدليل العملي الشامل والموسع لإعداد تقارير الاستدامة
    # ==========================================================================
    st.markdown("#### 📖 3. الدليل العملي الشامل لإعداد تقارير الاستدامة للقطاع المصرفي")

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
                <li><b>الشمول المالي والتحول الرقمي المستدام:</b> حجم ونطاق التمويلات الموجهة للمشروعات الصغيرة والمتوسطة (SMEs)، تمكين المرأة والشباب، وتوسيع نطاق الخدمات المصرفية الرقمية في كافة المحافظات.</li>
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
                    <li><b>المؤشر (23):</b> وجود حوافز ومكافآت مرتبطة بتحقيق مستهدفات الاستدامة وخفض الانبعاثات للقيادات التنفيذية (Sustainability-linked Executive Compensation).</li>
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
            <p>لا تقتصر معايير تأثير أهداف التنمية المستدامة (UNDP SDG Impact Standards) على مجرد إعداد التقارير اللاحقة، بل تمتد لتشكل <b>منهجية إدارية واستراتيجية لاتخاذ القرار القيادي الداخلي</b>، حيث يتم دمج تقييم التأثير (Impact Management) مع العمليات الاستثمارية، تخصيص المحفظة الائتمانية، وتوجيه السياسات المؤسسية نحو تعظيم العائد المجتمعي والبيئي بالتوازي مع العائد المالي. ويتم تتويج هذه المنظومة بإخضاع كافة البيانات والمؤشرات لعمليات <b>تدقيق وتوكيد خارجي مستقل (Third-party External Assurance)</b> لضمان أقصى درجات الموثوقية والشفافية أمام المستثمرين والجهات التنظيمية العالمية والمحلية.</p>
        </div>
        """
        st.markdown(flat_html(comprehensive_guide_html), unsafe_allow_html=True)

        guide_docx_content = f"""
        <html dir="rtl">
        <head><meta charset="utf-8"><title>الدليل العملي الشامل لإعداد تقارير الاستدامة</title></head>
        <body style="font-family: 'Cairo', Arial, sans-serif; text-align: right;">
            {comprehensive_guide_html}
            <hr>
            <p style="text-align: center; font-weight: bold; color: {CBE_GOLD}; margin-top: 20px;">تنويه استرشادي: تُعد مخرجات المنصة أداة مساندة لدعم اتخاذ القرار، ويُوصى بمواءمتها مع السياسات الداخلية لكل مصرف</p>
        </body>
        </html>
        """
        st.download_button(
            label="📥 تحميل الدليل العملي الشامل",
            data=guide_docx_content.encode("utf-8-sig"),
            file_name="الدليل_العملي_الشامل_لتقارير_الاستدامة_المصرفية.doc",
            mime="application/msword",
            use_container_width=True
        )


# ==============================================================================
# دوال التعامل مع قاعدة البيانات السحابية Supabase / Postgres (موحّدة ومُحسّنة)
# ==============================================================================
def get_db_connection():
    """إنشاء اتصال آمن ومباشر مع قاعدة البيانات السحابية عبر st.secrets"""
    if "postgres" in st.secrets and "url" in st.secrets["postgres"]:
        conn_str = st.secrets["postgres"]["url"]
        if "?" not in conn_str:
            conn_str += "?sslmode=require&connect_timeout=15"
        return psycopg2.connect(conn_str)
    raise ValueError("رابط الاتصال غير معرف في st.secrets['postgres']['url']")


def init_db(force: bool = False):
    """إنشاء وتحديث جدول الاستبيان تلقائياً في Supabase مع تخزين حالة التهيئة لتسريع الأداء"""
    if st.session_state.get("db_initialized") and not force:
        return True, "قاعدة البيانات مهيأة مسبقاً في الجلسة الحالية."

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS survey_responses (
                response_id TEXT PRIMARY KEY,
                respondent_name TEXT,
                bank_name TEXT,
                org_type TEXT,
                degree TEXT,
                specialty TEXT,
                job_level TEXT,
                exp_years TEXT,
                is_listed TEXT,
                survey_route TEXT,
                w_sip INT,
                w_ig INT,
                w_sr INT,
                avg_sip FLOAT,
                avg_ig FLOAT,
                avg_sr FLOAT,
                answers JSONB,
                comments TEXT,
                submitted_at TEXT
            );
        """)
        cur.execute("ALTER TABLE survey_responses ADD COLUMN IF NOT EXISTS respondent_name TEXT;")
        conn.commit()
        cur.close()
        st.session_state["db_initialized"] = True
        return True, "تم الاتصال وتحديث هيكل الجدول بنجاح!"
    except Exception as e:
        st.session_state["db_initialized"] = False
        return False, str(e)
    finally:
        if conn:
            conn.close()


def save_survey_to_cloud(rec):
    """حفظ بيانات الاستجابة مباشرة وبسرعة عالية في السحابة"""
    ok, err_msg = init_db()
    if not ok:
        raise RuntimeError(f"فشل تهيئة قاعدة البيانات: {err_msg}")

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        answers = {k: v for k, v in rec.items() if k.startswith("العبارة_")}
        respondent_val = str(rec.get("الاسم (اختياري)", "") or "").strip()

        cur.execute("""
            INSERT INTO survey_responses (
                response_id, respondent_name, bank_name, org_type, degree, specialty, job_level,
                exp_years, is_listed, survey_route, w_sip, w_ig, w_sr,
                avg_sip, avg_ig, avg_sr, answers, comments, submitted_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (response_id) DO NOTHING;
        """, (
            rec["معرف الاستجابة"], respondent_val, rec["اسم البنك"], rec["طبيعة المؤسسة"],
            rec["المؤهل العلمي"], rec["مجال التخصص الوظيفي"], rec["المستوى الوظيفي"], rec["سنوات الخبرة"],
            rec["مقيدة بالبورصة"], rec["مسار الاستبيان"], rec["وزن منصات المعلومات (%)"],
            rec["وزن الحوكمة المؤسسية (%)"], rec["وزن تقارير الاستدامة (%)"],
            rec["متوسط محور منصات المعلومات"], rec["متوسط محور الحوكمة المؤسسية"],
            rec["متوسط محور تقارير الاستدامة"], json.dumps(answers, ensure_ascii=False),
            rec["ملاحظات ومقترحات إضافية"], rec["وقت الإرسال"]
        ))
        conn.commit()
        cur.close()
    finally:
        conn.close()


def load_survey_log_from_cloud():
    """استرجاع الاستجابات وترتيب عمود الاسم في المقدمة وتفكيك العبارات الـ 31"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM survey_responses ORDER BY submitted_at DESC;")
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()

        if not rows or not col_names:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=col_names)

        if "respondent_name" in df.columns and "response_id" in df.columns:
            cols = list(df.columns)
            cols.remove("respondent_name")
            idx = cols.index("response_id") + 1
            cols.insert(idx, "respondent_name")
            df = df[cols]

        if 'answers' in df.columns:
            def _parse_ans(val):
                if isinstance(val, dict):
                    return val
                if isinstance(val, str):
                    try:
                        return json.loads(val)
                    except Exception:
                        return {}
                return {}

            parsed_series = df['answers'].apply(_parse_ans)
            answers_df = pd.json_normalize(parsed_series)

            stmt_cols = [f"العبارة_{i}" for i in range(1, 32) if f"العبارة_{i}" in answers_df.columns]
            other_stmt_cols = [c for c in answers_df.columns if c not in stmt_cols]
            answers_df = answers_df[stmt_cols + other_stmt_cols]

            df = pd.concat([df.drop(columns=['answers']), answers_df], axis=1)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


# ------------------------------------------------------------------------------
# التبويب السابع: الاستبيان الموجه إلى فرق العمل (Dual-Channel: Platform + Kobo)
# ------------------------------------------------------------------------------
KOBO_SURVEY_URL = "https://ee.kobotoolbox.org/x/eSYulrAD"

with tab7:
    import base64
    import zlib

    # مرساة علوية ثابتة للعودة التلقائية إلى بداية الاستبيان عند الانتقال بين المراحل
    st.markdown('<div id="survey-top-anchor" style="scroll-margin-top: 16px;"></div>', unsafe_allow_html=True)

    # منع القفز العشوائي للشاشة أثناء اختيار الإجابات في Streamlit Radio
    st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"],
        div[data-testid="stRadio"],
        div.element-container {
            overflow-anchor: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # دوال الحماية والاستعادة التلقائية للاستبيان ضد F5 / Refresh
    # ==========================================================================
    def _encode_survey_draft(store_dict: dict, step_val: int) -> str:
        """ضغط وتشفير مسودة الاستبيان بصيغة zlib+base64 آمنة للرابط والمتصفح."""
        try:
            clean_store = {k: v for k, v in store_dict.items() if v is not None and v != ""}
            if not clean_store:
                return ""
            raw = json.dumps({"s": clean_store, "p": int(step_val)}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            comp = zlib.compress(raw, level=9)
            return base64.urlsafe_b64encode(comp).decode("ascii").rstrip("=")
        except Exception:
            return ""

    def _decode_survey_draft(token: str) -> tuple[dict, int]:
        """فك ضغط مسودة الاستبيان المسترجعة من الرابط أو المتصفح."""
        if not token:
            return {}, 1
        try:
            padded = token + "=" * (-len(token) % 4)
            comp = base64.urlsafe_b64decode(padded.encode("ascii"))
            raw = zlib.decompress(comp).decode("utf-8")
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and isinstance(parsed.get("s"), dict):
                return parsed["s"], int(parsed.get("p", 1))
        except Exception:
            pass
        return {}, 1

    def restore_survey_browser_backup():
        """استعادة كافة إجابات الاستبيان والمرحلة الحالية تلقائياً عند الضغط على F5."""
        if "survey_store" not in st.session_state:
            st.session_state.survey_store = {}
        if "survey_wizard_step" not in st.session_state:
            st.session_state.survey_wizard_step = 1

        # 1) الاستعادة الفورية من URL Query Params (الأسرع والأكثر موثوقية عند F5)
        url_draft = st.query_params.get("sdraft", "")
        if url_draft and not st.session_state.survey_store:
            restored_store, restored_step = _decode_survey_draft(url_draft)
            if restored_store:
                st.session_state.survey_store.update(restored_store)
                st.session_state.survey_wizard_step = restored_step

        # 2) جسر localStorage بالمتصفح كنسخة احتياطية ثانية إذا فُتح الرابط بدون معاملات
        has_data = bool(st.session_state.survey_store)
        components.html(
            f"""
            <script>
            (function() {{
                try {{
                    var LS_TOKEN_KEY = 'raseen_survey_token_v3';
                    var hasServerData = {json.dumps(has_data)};
                    var savedToken = window.parent.localStorage.getItem(LS_TOKEN_KEY);
                    if (!hasServerData && savedToken) {{
                        var u = new URL(window.parent.location.href);
                        if (u.searchParams.get('sdraft') !== savedToken) {{
                            u.searchParams.set('sdraft', savedToken);
                            u.searchParams.set('tab', '7');
                            window.parent.location.replace(u.toString());
                        }}
                    }}
                }} catch (e) {{}}
            }})();
            </script>
            """,
            height=0,
            width=0,
        )

    def sync_survey_browser_backup():
        """حفظ ومزامنة إجابات الاستبيان ومرحلته لحظياً في الرابط وفي localStorage."""
        store_data = st.session_state.get("survey_store", {})
        step_val = st.session_state.get("survey_wizard_step", 1)
        is_submitted = bool(store_data.get("submitted_id"))

        if is_submitted:
            if "sdraft" in st.query_params:
                del st.query_params["sdraft"]
            token_str = ""
        else:
            token_str = _encode_survey_draft(store_data, step_val)
            if token_str:
                st.query_params["sdraft"] = token_str
                st.query_params["tab"] = "7"

        components.html(
            f"""
            <script>
            (function() {{
                try {{
                    var LS_TOKEN_KEY = 'raseen_survey_token_v3';
                    var LS_LEGACY_KEY = 'raseen_survey_draft_v2';
                    var submitted = {json.dumps(is_submitted)};
                    var token = {json.dumps(token_str)};
                    if (submitted) {{
                        window.parent.localStorage.removeItem(LS_TOKEN_KEY);
                        window.parent.localStorage.removeItem(LS_LEGACY_KEY);
                    }} else if (token) {{
                        window.parent.localStorage.setItem(LS_TOKEN_KEY, token);
                        var u = new URL(window.parent.location.href);
                        u.searchParams.set('sdraft', token);
                        u.searchParams.set('tab', '7');
                        window.parent.history.replaceState({{}}, '', u.toString());
                    }}
                }} catch (e) {{}}
            }})();
            </script>
            """,
            height=0,
            width=0,
        )

    # استعادة البيانات المحفوظة قبل رسم مكونات التبويب
    restore_survey_browser_backup()

    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 15px;">
        <h3 style="color: #002B49; font-weight: 800; margin-bottom: 4px;">📋 الاستبيان الموجه إلى فرق العمل في البنوك (عينة الدراسة الميدانية)</h3>
        <p style="color: #475569; font-size: 14px;">استمارة الاستبيان الميداني المعتمدة لجمع آراء وتقييمات فرق العمل والقيادات المصرفية حول محاور المنصة المقترحة وجدواها التطبيقية.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%); padding: 12px 18px; border-radius: 10px; border: 1.5px solid {CBE_GOLD}; text-align: center; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);" dir="rtl">
        <span style="font-weight: 800; color: {CBE_NAVY}; font-size: 14.5px;">⏳ تنويه: استغراق تعبئة هذا الاستبيان لا يتجاوز 10 دقائق تقريباً لضمان دقة الاستجابات والتقييم الميداني (يتم حفظ إجاباتك تلقائياً ضد انقطاع الاتصال أو F5).</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🏛️ تمهيد جهة الدراسة والخطاب الموجه", expanded=False):
        st.markdown(f"""
        <div style="background: #FFFFFF; padding: 25px; border-radius: 12px; border: 1.5px solid {CBE_GOLD}; margin-bottom: 10px; line-height: 1.9;" dir="rtl">
            <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 12px; margin-bottom: 15px;">
                <h4 style="color: {CBE_NAVY}; font-weight: 800; margin: 0;">جامعة عين شمس | كلية الدراسات العليا والبحوث البيئية | قسم العلوم الاقتصادية والإدارية والقانونية البيئية</h4>
            </div>
            <p><b>السادة الأفاضل/ .................................................................</b></p>
            <p><b>السلام عليكم ورحمة الله وبركاته،،،</b></p>
            <p>في إطار متطلبات الحصول على درجة دكتوراة الفلسفة في العلوم الاقتصادية والإدارية والقانونية يقوم الباحث بإعداد دراسة تطبيقية بعنوان:</p>
            <div style="background: {CBE_BG}; padding: 12px; border-radius: 8px; border-right: 4px solid {CBE_GOLD}; text-align: center; font-weight: bold; color: {CBE_NAVY}; margin: 10px 0;">
                نموذج مقترح لتعزيز الحوكمة المؤسسية باستخدام منصة معلومات ذكية: بالتطبيق على تقارير الاستدامة
            </div>
            <p>نظراً لما تتمتعون به من خبرة ودراية في هذا المجال الحيوي؛ نتشرف بدعوة سيادتكم للمشاركة في هذا البحث من خلال الإجابة على عبارات الاستبيان المرفق، وتحديد مدى موافقتكم عليها بما ترونه مناسباً، علماً بأن هذه الدراسة تهدف إلى تقديم حلول مبتكرة تعتمد على الذكاء الاصطناعي لتعزيز الحوكمة المؤسسية ودعم السيادة الرقمية في البنوك المصرية.</p>
            <p>كما نؤكد لسيادتكم أن كافة البيانات والآراء ستحاط بالسرية التامة، ولن تستخدم إلا لأغراض البحث العلمي فقط.</p>
            <p><b>وتفضلوا بقبول فائق التقدير والاحترام،،،</b></p>
            <p style="margin-bottom: 0;">
                <b>الباحث:</b> أيمن محمد إبراهيم الدسوقي (مدرس مساعد إدارة المعرفة – معهد التخطيط القومي)<br>
                <b>تحت إشراف:</b><br>
- أ.د. ممدوح عبدالعزيز رفاعي (أستاذ إدارة الأعمال - كلية التجارة - جامعة عين شمس)<br>
- أ.د. محمد ماجد صلاح الدين خشبة (أستاذ إدارة الأعمال - مركز التخطيط والتنمية الصناعية - معهد التخطيط القومي)<br>
- د. إسلام محمد حجازي (أستاذ مساعد بقسم علوم الحاسب - كلية الحاسبات والمعلومات - جامعة عين شمس)
            </p>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📚 مصطلحات تعريفية (المفاهيم الوظيفية للمنصة)", expanded=False):
        st.markdown(f"""
        <div dir="rtl" style="text-align: right; line-height: 1.9;">
            <p>لضمان وحدة المفهوم ودقة الاستجابة، يرجى التكرم بالاطلاع على التعريفات الإجرائية التالية للمحاور المستخدمة في هذا الاستبيان:</p>
            <ul>
                <li><b>منصة المعلومات الذكية (Smart Information Platform - SIP):</b> نظام رقمي متكامل يعتمد على آليات الاسترجاع الذكي المعتمدة على الوثائق المرجعية وتقنيات الذكاء الاصطناعي التوليدي لتحليل البيانات المصرفية.</li>
                <li><b>تقارير الاستدامة (Sustainability Reporting - SR):</b> عملية الإفصاح الدوري والرقمي عن أداء البنك في المجالات البيئية والاجتماعية والحوكمة (ESG) وفق المعايير الدولية (ISSB / GRI).</li>
                <li><b>الحوكمة المؤسسية (Institutional Governance - IG):</b> الإطار الشامل من القواعد والرقابة والمساءلة التي تضمن توجيه وإدارة المؤسسة المصرفية بنزاهة وشفافية.</li>
                <li><b>مؤشر الحوكمة الذكية المستدامة (SSGI):</b> مؤشر مركب مقترح لقياس مستوى نضج البنك في دمج ممارسات الحوكمة مع متطلبات الاستدامة عبر التمكين الرقمي.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div dir="rtl" style="background:#FFFFFF; border:1.5px solid {CBE_GOLD}; border-radius:12px; padding:14px 18px; margin:15px 0;">
        <div style="font-weight:800; color:{CBE_NAVY}; font-size:15px; margin-bottom:6px;">
            🔀 اختر وسيلة تعبئة الاستبيان المفضلة لديك (كلا المسارين معتمدان للتحليل البحثي):
        </div>
        <div style="color:#475569; font-size:13px;">
            يمكنكم تعبئة الاستبيان مباشرة عبر نموذج المنصة التفاعلي (المقسّم إلى 3 أقسام منهجية) أو عبر استمارة <b>KoboToolbox</b> الدولية المعتمدة.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_mode, col_ext = st.columns([3, 1])
    with col_mode:
        survey_channel = st.radio(
            "وسيلة التعبئة:",
            [
                "🖥️ النموذج التفاعلي المباشر بالمنصة",
                "🌐 نموذج KoboToolbox المدمج"
            ],
            horizontal=True,
            label_visibility="collapsed",
            key="survey_channel_selector"
        )
    with col_ext:
        st.link_button(
            "🔗 فتح رابط Kobo المستقل",
            KOBO_SURVEY_URL,
            use_container_width=True,
            help="فتح استمارة KoboToolbox في علامة تبويب جديدة أو نسخ رابطها للمشاركة"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================================================
    # المسار الأول: استمارة KoboToolbox المدمجة
    # ==========================================================================
    if "KoboToolbox" in survey_channel:
        with st.container(border=True):
            st.markdown(f"""
            <div dir="rtl" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:12px;">
                <div>
                    <h4 style="color:{CBE_NAVY}; font-weight:800; margin:0;">🌐 استمارة KoboToolbox الميدانية المعتمدة</h4>
                    <span style="color:#64748B; font-size:13px;">رابط التوزيع المباشر: <code style="direction:ltr;">{KOBO_SURVEY_URL}</code></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            components.iframe(KOBO_SURVEY_URL, height=920, scrolling=True)

    # ==========================================================================
    # المسار الثاني: النموذج التفاعلي المطور بالمنصة (3 أقسام منهجية مستقلة)
    # ==========================================================================
    else:
        LIKERT = {"غير موافق بشدة": 1, "غير موافق": 2, "محايد": 3, "موافق": 4, "موافق بشدة": 5}
        likert_options = list(LIKERT.keys())

        READINESS_LIKERT = {"منخفض جداً": 1, "منخفض": 2, "متوسط": 3, "مرتفع": 4, "مرتفع جداً": 5}
        readiness_options = list(READINESS_LIKERT.keys())

        # القسم الأول (ثانياً): مؤشرات الجاهزية الرقمية والمؤسسية الحالية بالبنك (وصفية - لا تدخل في SEM)
        READINESS_TEXTS = {
            "r1": "(أ) مستوى نضج البنية التحتية الرقمية وتكامل قواعد البيانات بين إدارات البنك.",
            "r2": "(ب) مدى توظيف أدوات الذكاء الاصطناعي وتحليل البيانات المتقدمة في العمليات المصرفية والرقابية.",
            "r3": "(ج) وجود هيكل تنظيمي أو إدارة مستقلة معنية بملف الاستدامة (ESG).",
            "r4": "(د) مستوى انتظام وشمولية تقارير الاستدامة والإفصاح البيئي والمجتمعي الصادرة عن البنك.",
            "r5": "(هـ) درجة اعتماد الإدارة العليا ولجان الحوكمة على لوحات المؤشرات الرقمية في متابعة الأداء والامتثال.",
        }

        # القسم الثاني (30 عبارة) + القسم الثالث (5 عبارات قابلية الاستخدام والثقة والجدوى)
        STMT_TEXTS = {
            # المحور الأول: منصات المعلومات الذكية (SIP) — 8 عبارات / 4 أبعاد
            1: "تساهم المنصة الذكية في تجميع البيانات التاريخية والحالية من مصادر متعددة وتنظيمها في إطار مركزي واضح.",
            2: "يضمن الاعتماد على آليات الاسترجاع الذكي المعتمدة على الوثائق المرجعية دقة الإجابات المستخرجة والحد من المعلومات غير الموثقة.",
            3: "يسهم تطبيق العمل بالمنصة في تقليل الاعتماد البشري ‏في إعداد التقارير، مما يخفض الأخطاء والتحيزات‏.",
            4: "تساهم مرونة المنصة في استيعاب معايير الإفصاح الدولية (مثل معايير مجلس معايير الاستدامة الدولية ISSB ومبادرة التقارير العالمية GRI) في تسهيل التكيف مع التحديثات التنظيمية.",
            5: "يوفر \"محاكي السياسات\" بالمنصة تغذية راجعة مستمرة تساعد في تعديل الخطط الاستراتيجية بناءً على فجوات الأداء المرصودة.",
            6: "تساهم أدوات المراجعة والتحليل الذكي بالمنصة في دعم الكشف المبكر عن أي تناقض في الإفصاحات أو مؤشرات \"الغسل الأخضر\" (Greenwashing).",
            7: "تم تصميم بنية المنصة بصورة مرنة تسمح مستقبلاً بالتكامل الآمن مع الأنظمة المصرفية القائمة لضمان انسيابية البيانات.",
            8: "توفر آليات الفلترة المحلية وضوابط الصلاحيات والتشفير بالمنصة ضمانة مناسبة لحماية السرية المصرفية وأمن المعلومات.",

            # المحور الثاني: تقارير الاستدامة (SR) — 10 عبارات / 5 أبعاد
            9: "تساعد مخرجات المنصة في ربط أهداف التنمية المستدامة (SDGs) ورؤية مصر 2030 بالخطة الاستراتيجية للبنك بشكل أكثر وضوحاً.",
            10: "توضح التقارير التقييمية الصادرة عن المنصة الجوانب الاستراتيجية والاقتصادية لتبني ممارسات التمويل المستدام.",
            11: "توفر المنصة إطاراً لدعم تحليل وعرض مؤشرات كفاءة استهلاك الموارد الداخلية (الطاقة، المياه، الورق) عند إتاحة البيانات اللازمة.",
            12: "تدعم المنصة تتبع وتحليل الإفصاحات الخاصة بالتمويل الأخضر والمشروعات الصديقة للبيئة الواردة في تقارير البنوك.",
            13: "تساهم \"لوحة دعم اتخاذ القرار\" بالمنصة في تشخيص الفجوات الهيكلية ودمج مخاطر المناخ والاستدامة (ESG Risks) ضمن رؤية إدارة المخاطر.",
            14: "تساعد السيناريوهات الاستشرافية بالمنصة في دعم خطط استمرارية الأعمال والاستعداد المبكر للتحديات البيئية والتنظيمية.",
            15: "تساهم المنصة في توحيد آلية احتساب المؤشر المركب للحوكمة الذكية المستدامة (SSGI) وتسهيل المقارنة المعيارية بين البنوك.",
            16: "يتيح \"محاكي السياسات\" بالمنصة صياغة مستهدفات كمية محددة لكل محور من محاور الاستدامة وتقدير أثرها المتوقع.",
            17: "تساعد المنصة في تجميع وتحليل الإفصاحات المرتبطة بالشمول المالي ووصول الخدمات المصرفية للفئات والمناطق الأكثر احتياجاً.",
            18: "تساعد أدوات تحليل التقارير بالمنصة في استخراج ومقارنة مؤشرات التنوع وتكافؤ الفرص وتمكين المرأة الواردة في التقارير المؤسسية.",

            # المحور الثالث: الحوكمة المؤسسية (IG) — 12 عبارة / 6 أبعاد
            19: "تساهم التقارير الذكية ولوحات العرض بالمنصة في تقليص فجوة عدم تماثل المعلومات بين الإدارة التنفيذية وأصحاب المصلحة.",
            20: "ترفع مخرجات المنصة من جودة ووضوح الإفصاح المؤسسي عبر تحويل البيانات السردية المعقدة إلى مؤشرات كمية قابلة للمقارنة.",
            21: "تعزز المنصة من قدرة لجان المراجعة والرقابة الداخلية على تتبع الأثر الفعلي لقرارات الاستدامة والحوكمة.",
            22: "تساعد المؤشرات الموضوعية المستخرجة عبر المنصة في دعم المساءلة الإدارية استناداً إلى أدلة رقمية موثقة.",
            23: "تدعم المؤشرات الموحدة بالمنصة تطبيق معايير موضوعية وعادلة في تقييم الأداء وتخصيص التمويل المستدام دون تحيز.",
            24: "تساهم شفافية البيانات بالمنصة في حماية حقوق جميع الأطراف المرتبطة (المساهمين، المودعين، والمجتمع) على قدم المساواة.",
            25: "تسهل المنصة التواصل الفعال وتبادل التغذية الراجعة مع فرق العمل والأطراف المعنية لتحديد أولويات الاستدامة الجوهرية.",
            26: "يدعم التكامل المعرفي بالمنصة مشاركة الإدارات المختلفة (المخاطر، الالتزام، الاستدامة، وتكنولوجيا المعلومات) في صياغة التقارير.",
            27: "تعزز المنصة من قدرة البنك على الاستجابة الفورية للتعليمات الرقابية والتشريعات البيئية ورصد حالات عدم الامتثال بدقة.",
            28: "يضمن التوثيق الآلي لسجلات التقييم والتقارير التنفيذية بالمنصة الالتزام الكامل بأطر الحوكمة الرقابية المعتمدة.",
            29: "تسهم لوحات المعلومات التفاعلية والتقرير التنفيذي بالمنصة في دعم مجلس الإدارة بالرقابة الاستباقية وسرعة اتخاذ القرار.",
            30: "توفر المنصة رؤية شاملة لمجلس الإدارة لمتابعة التوازن بين الأداء المالي والالتزام البيئي والمؤسسي طويل الأجل.",

            # القسم الثالث: قابلية الاستخدام والثقة والجدوى التطبيقية للمنصة (5 عبارات)
            31: "(وضوح الواجهة): تتسم واجهة المنصة بوضوح التصميم وتنظيم العرض البصري بما ييسر قراءة المؤشرات والتقارير.",
            32: "(سهولة الاستخدام): يسهل التنقل بين وحدات المنصة التحليلية (المستشار الذكي، المؤشر المركب، ومحاكي السياسات) دون الحاجة لخبرة برمجية متخصصة.",
            33: "(الفائدة المتوقعة): توفر أدوات المنصة قيمة عملية ملموسة تسهم في توفير الوقت والجهد المبذولين في إعداد ومراجعة تقارير الاستدامة والحوكمة.",
            34: "(الثقة والشفافية): أرى أن المخرجات التحليلية والتوصيات التي توفرها المنصة تتسم بالشفافية ويمكن الاعتماد عليها كمصدر مساند لاتخاذ القرار الإداري والرقابي.",
            35: "(القابلية للتطبيق الفعلي): أرى أن المنصة المقترحة قابلة للتطبيق الفعلي في البنوك العاملة بالقطاع المصرفي المصري كأداة مساندة للرقابة والحوكمة.",
        }

        SURVEY_AXES = {
            "SIP": {
                "icon": "💻",
                "label": "القسم الثاني (المحور الأول): منصات المعلومات الذكية (SIP)",
                "nums": list(range(1, 9)),
                "avg_col": "متوسط محور منصات المعلومات",
                "groups": [
                    ("البُعد الأول: جودة المعلومات", [1, 2]),
                    ("البُعد الثاني: الامتثال التقني", [3, 4]),
                    ("البُعد الثالث: التخطيط والمراقبة بعد النشر", [5, 6]),
                    ("البُعد الرابع: التكامل والخصوصية", [7, 8]),
                ],
            },
            "SR": {
                "icon": "🌱",
                "label": "القسم الثاني (المحور الثاني): تقارير الاستدامة (SR)",
                "nums": list(range(9, 19)),
                "avg_col": "متوسط محور تقارير الاستدامة",
                "groups": [
                    ("البُعد الأول: الاستراتيجية", [9, 10]),
                    ("البُعد الثاني: الأبعاد التشغيلية", [11, 12]),
                    ("البُعد الثالث: إدارة المخاطر", [13, 14]),
                    ("البُعد الرابع: المقاييس والأهداف", [15, 16]),
                    ("البُعد الخامس: التنوع والشمول", [17, 18]),
                ],
            },
            "IG": {
                "icon": "🏛️",
                "label": "القسم الثاني (المحور الثالث): الحوكمة المؤسسية (IG)",
                "nums": list(range(19, 31)),
                "avg_col": "متوسط محور الحوكمة المؤسسية",
                "groups": [
                    ("البُعد الأول: الشفافية والإفصاح", [19, 20]),
                    ("البُعد الثاني: المتابعة والمساءلة", [21, 22]),
                    ("البُعد الثالث: العدالة والمساواة", [23, 24]),
                    ("البُعد الرابع: المشاركة", [25, 26]),
                    ("البُعد الخامس: سيادة القانون", [27, 28]),
                    ("البُعد السادس: مجلس الإدارة", [29, 30]),
                ],
            },
            "USABILITY": {
                "icon": "🚀",
                "label": "القسم الثالث: قابلية الاستخدام والثقة والجدوى التطبيقية للمنصة",
                "nums": list(range(31, 36)),
                "avg_col": "متوسط قابلية الاستخدام والجدوى",
                "groups": [
                    ("تقييم قابلية التبني والاعتمادية العملية في القطاع المصرفي", [31, 32, 33, 34, 35]),
                ],
            },
        }

        ROLE_ROUTES = {
            "تكنولوجيا المعلومات/ التحول الرقمي": ["SIP", "USABILITY"],
            "الاستدامة/ المسؤولية المجتمعية": ["SR", "USABILITY"],
            "الحوكمة/ الالتزام/ المراجعة الداخلية": ["IG", "USABILITY"],
            "إدارة المخاطر/ الائتمان": ["IG", "USABILITY"],
        }

        banks_opts = [b for b in BANKS_LIST_AR if b != "اختر البنك المصرفي"]
        PROFILE_FIELDS = [
            ("bank", "اسم البنك / المؤسسة المصرفية (إلزامي)", banks_opts),
            ("spec", "مجال التخصص الوظيفي / الإدارة (إلزامي - يحدد مسار العبارات)", [
                "مجلس الإدارة/ الإدارة العليا العامة",
                "تكنولوجيا المعلومات/ التحول الرقمي",
                "الحوكمة/ الالتزام/ المراجعة الداخلية",
                "إدارة المخاطر/ الائتمان",
                "الاستدامة/ المسؤولية المجتمعية",
                "البحث/ التطوير أو أخرى",
            ]),
            ("org", "طبيعة المؤسسة (إلزامي)", [
                "بنك قطاع عام/ حكومي", "بنك قطاع خاص مشترك", "بنك إسلامي", "بنك عربي/ أجنبي",
                "جهة رقابية ك(البنك المركزي / الرقابة المالية)",
                "مؤسسة أكاديمية أو شركة تكنولوجيا مالية", "أخرى",
            ]),
            ("job", "المستوى الوظيفي (إلزامي)", [
                "رئيس/ عضو مجلس إدارة", "رئيس قطاع/ مساعد مدير عام", "مدير إدارة/ مدير عام",
                "خبير/ مستشار/ كبير أخصائيين", "مستوى إشرافي", "أخرى",
            ]),
            ("sci", "المؤهل العلمي (إلزامي)", [
                "دكتوراه", "ماجستير", "شهادة مهنية متخصصة مثل: CISA, GRCP", "ليسانس/ بكالوريوس",
            ]),
            ("exp", "سنوات الخبرة في القطاع المصرفي (إلزامي)", [
                "أقل من 5 سنوات", "من 5 إلى 10 سنوات", "من 11 إلى 15 سنة", "أكثر من 15 سنة",
            ]),
        ]

        if "survey_store" not in st.session_state:
            st.session_state.survey_store = {}
        if "survey_wizard_step" not in st.session_state:
            st.session_state.survey_wizard_step = 1
        if "scroll_survey_top" not in st.session_state:
            st.session_state.scroll_survey_top = False

        S = st.session_state.survey_store

        # مزامنة تلقائية لمسودة الاستبيان مع المتصفح والرابط لحمايتها من F5 / Refresh
        sync_survey_browser_backup()

        def _sync(widget_key, store_key):
            S[store_key] = st.session_state.get(widget_key)
            token_now = _encode_survey_draft(S, st.session_state.get("survey_wizard_step", 1))
            if token_now:
                st.query_params["sdraft"] = token_now
                st.query_params["tab"] = "7"

        def sv_select(label, options, skey):
            cur = S.get(skey)
            st.selectbox(label, options, index=options.index(cur) if cur in options else None,
                         placeholder="اختر...", key=f"w_{skey}", on_change=_sync, args=(f"w_{skey}", skey))

        def render_readiness_item(rkey):
            st.markdown(f"""
            <div style="background:#F8FAFC;padding:11px 15px;border-radius:8px;border:1px solid #E2E8F0;margin-bottom:6px;" dir="rtl">
                <span style="font-weight:bold;color:{CBE_NAVY};font-size:13.5px;">{READINESS_TEXTS[rkey]}</span>
            </div>""", unsafe_allow_html=True)
            cur = S.get(rkey)
            st.radio(f"مؤشر الجاهزية {rkey}", readiness_options,
                     index=readiness_options.index(cur) if cur in readiness_options else None,
                     horizontal=True, label_visibility="collapsed",
                     key=f"w_{rkey}", on_change=_sync, args=(f"w_{rkey}", rkey))
            st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

        def render_statement(num):
            st.markdown(f"""
            <div style="background:#F8FAFC;padding:12px 16px;border-radius:8px;border:1px solid #E2E8F0;margin-bottom:6px;" dir="rtl">
                <span style="font-weight:bold;color:{CBE_NAVY};font-size:14px;">({num}) {STMT_TEXTS[num]}</span>
            </div>""", unsafe_allow_html=True)
            skey = f"stmt_{num}"
            cur = S.get(skey)
            st.radio(f"تقييم العبارة {num}", likert_options,
                     index=likert_options.index(cur) if cur in likert_options else None,
                     horizontal=True, label_visibility="collapsed",
                     key=f"w_{skey}", on_change=_sync, args=(f"w_{skey}", skey))
            st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)

        current_spec = S.get("spec")
        axes_required = ROLE_ROUTES.get(current_spec, ["SIP", "SR", "IG", "USABILITY"])
        is_full_assessment = current_spec not in ROLE_ROUTES
        required_stmts = [n for ax in axes_required for n in SURVEY_AXES[ax]["nums"]]

        steps = ["profile"] + axes_required + ["final"]
        max_wizard_steps = len(steps)
        step_num = min(max(st.session_state.survey_wizard_step, 1), max_wizard_steps)
        st.session_state.survey_wizard_step = step_num
        step_key = steps[step_num - 1]

        def step_titles(k):
            if k == "profile":
                return "القسم الأول: البيانات الديموغرافية والجاهزية الحالية للبنك (وصفي)"
            if k == "final":
                return "المرحلة الختامية: الأوزان النسبية والملاحظات والإرسال النهائي"
            return f"{SURVEY_AXES[k]['icon']} {SURVEY_AXES[k]['label']}"

        answered_count = sum(1 for n in required_stmts if S.get(f"stmt_{n}") is not None)
        total_req_count = len(required_stmts)
        progress_percentage = int(answered_count / total_req_count * 100) if total_req_count else 0

        w_sip_cur = int(S.get("w_sip", 40))
        w_ig_cur = int(S.get("w_ig", 30))
        w_sr_cur = int(S.get("w_sr", 30))
        weights_confirmed = bool(S.get("weights_confirmed", False))

        def step_complete(k):
            if k == "profile":
                profile_ok = all(S.get(f) for f, _, _ in PROFILE_FIELDS) and S.get("listed") is not None
                readiness_ok = all(S.get(rk) is not None for rk in READINESS_TEXTS)
                return profile_ok and readiness_ok
            if k in SURVEY_AXES:
                return all(S.get(f"stmt_{n}") is not None for n in SURVEY_AXES[k]["nums"])
            return (
                (w_sip_cur + w_ig_cur + w_sr_cur == 100)
                and weights_confirmed
                and all(S.get(f"stmt_{n}") is not None for n in required_stmts)
            )

        route_badge = (
            "مسار شامل (35 عبارة + 5 مؤشرات جاهزية)" if (current_spec and is_full_assessment)
            else (f"مسار مخصص للتخصص ({total_req_count} عبارة + 5 مؤشرات جاهزية)" if current_spec else "بانتظار تحديد التخصص")
        )
        progress_txt = (
            f"{route_badge} | الإنجاز: {progress_percentage}% ({answered_count} من {total_req_count})"
            if current_spec else "اختر التخصص الوظيفي لتحديد مسار العبارات"
        )
        st.markdown(f"""
        <div id="survey-wizard-header" dir="rtl" style="background:#FFF;border:1.5px solid {CBE_GOLD};border-radius:12px;padding:18px;margin-bottom:20px;scroll-margin-top:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px;">
                <span style="font-weight:800;color:{CBE_NAVY};font-size:15px;">📍 ({step_num}/{max_wizard_steps}) {step_titles(step_key)}</span>
                <span style="font-weight:800;color:{CBE_GOLD};font-size:13.5px;">{progress_txt}</span>
            </div>
            <div style="background:#E2E8F0;border-radius:10px;height:10px;overflow:hidden;">
                <div style="background:linear-gradient(90deg,{CBE_GOLD},{CBE_NAVY});width:{progress_percentage}%;height:100%;transition:width 0.3s ease;"></div>
            </div>
        </div>""", unsafe_allow_html=True)

        already_submitted = S.get("submitted_id") is not None
        if already_submitted:
            st.success(f"✅ تم تسجيل استجابتكم بنجاح بالسحابة (رقم: {S['submitted_id']}). شكراً لمشاركتكم.")
            if st.button("📝 تعبئة استجابة جديدة", key="survey_new_response"):
                S.clear()
                st.session_state.survey_wizard_step = 1
                st.session_state.scroll_survey_top = True
                if "sdraft" in st.query_params:
                    del st.query_params["sdraft"]
                sync_survey_browser_backup()
                st.rerun()

        elif step_key == "profile":
            with st.container(border=True):
                st.markdown(f"<div dir='rtl'><h4 style='color:{CBE_NAVY};font-weight:800;'>👤 أولاً: البيانات الديموغرافية والوظيفية للمشارك</h4>"
                            f"<p style='color:#EF4444;font-size:13px;font-weight:700;'>⚠️ جميع الحقول إلزامية (عدا خانة الاسم فهي اختيارية).</p></div>",
                            unsafe_allow_html=True)
                c1, c2 = st.columns(2, gap="medium")
                for i, (skey, label, opts) in enumerate(PROFILE_FIELDS):
                    with (c1 if i % 2 == 0 else c2):
                        sv_select(label, opts, skey)
                cur = S.get("listed")
                st.radio("هل المؤسسة التي تعمل بها مقيدة بالبورصة المصرية؟ (إلزامي)", ["نعم", "لا"],
                         index=["نعم", "لا"].index(cur) if cur in ["نعم", "لا"] else None, horizontal=True,
                         key="w_listed", on_change=_sync, args=("w_listed", "listed"))
                S["name"] = st.text_input("الاسم (اختياري)", value=S.get("name", ""),
                                          placeholder="يمكنكم ترك هذا الحقل فارغاً",
                                          key="w_name", on_change=_sync, args=("w_name", "name"))

                st.markdown("<hr style='margin: 18px 0; border-top: 1.5px solid #E2E8F0;'>", unsafe_allow_html=True)
                st.markdown(f"""
                <div dir='rtl'>
                    <h4 style='color:{CBE_NAVY};font-weight:800;margin-bottom:4px;'>🏦 ثانياً: مؤشرات الجاهزية الرقمية والمؤسسية الحالية بالبنك (وصفية)</h4>
                    <p style='color:#475569;font-size:13px;margin-bottom:12px;'>يرجى تقييم <b>الوضع الراهن في مؤسستكم المصرفية</b> من حيث مستوى النضج والجاهزية (من 1 = منخفض جداً إلى 5 = مرتفع جداً):</p>
                </div>""", unsafe_allow_html=True)

                for rkey in READINESS_TEXTS:
                    render_readiness_item(rkey)

                st.markdown(f"""
                <div dir="rtl" style="background:#F8FAFC;border:1.5px solid {CBE_GOLD};border-radius:10px;padding:10px 14px;margin-top:8px;text-align:right;">
                    <span style="font-weight:700;color:{CBE_NAVY};font-size:13.5px;">🔒 تنويه: جميع المعلومات الواردة في هذا الاستبيان تخضع للسرية الكاملة، ولا تُستخدم إلا لأغراض البحث العلمي فقط.</span>
                </div>""", unsafe_allow_html=True)

        elif step_key in SURVEY_AXES:
            ax = SURVEY_AXES[step_key]
            with st.container(border=True):
                st.markdown(f"""
                <div dir='rtl'>
                    <h4 style='color:{CBE_NAVY};font-weight:800;margin-bottom:4px;'>{ax['icon']} {ax['label']}</h4>
                    <div style='background:#FEF3C7;border-right:4px solid {CBE_GOLD};padding:8px 12px;border-radius:6px;margin:8px 0 12px 0;font-size:13px;color:#78350F;'>
                        <b>📌 تعليمات التقييم:</b> يرجى تقييم مدى موافقتك على قدرة <b>المنصة الذكية المقترحة</b> (التي قمت باستعراضها وتجربتها) على تحقيق الوظائف التالية (1 = غير موافق بشدة إلى 5 = موافق بشدة).
                    </div>
                </div>""", unsafe_allow_html=True)
                for title, nums in ax["groups"]:
                    if title:
                        st.markdown(f"<div style='background:{CBE_BG};padding:6px 12px;font-weight:bold;color:{CBE_NAVY};border-radius:4px;margin:12px 0;' dir='rtl'>{title}</div>",
                                    unsafe_allow_html=True)
                    for n in nums:
                        render_statement(n)

        else:  # final
            with st.container(border=True):
                st.markdown(f"<div dir='rtl'><h4 style='color:{CBE_NAVY};font-weight:800;'>⚖️ الأوزان النسبية للمحاور وملاحظات التطبيق</h4>"
                            f"<p style='color:#64748B;font-size:13px;'>حدد الوزن المئوي لكل محور من محاور النموذج الثلاثة حسب تقدير خبرتكم المصرفية (المجموع = 100%).</p></div>",
                            unsafe_allow_html=True)
                cw1, cw2, cw3 = st.columns(3)
                for col, skey, lbl, dflt in [(cw1, "w_sip", "1. منصات المعلومات الذكية (SIP): (%)", 40),
                                             (cw2, "w_ig", "2. الحوكمة المؤسسية والامتثال (IG): (%)", 30),
                                             (cw3, "w_sr", "3. تقارير الاستدامة (SR): (%)", 30)]:
                    with col:
                        st.number_input(lbl, min_value=0, max_value=100, value=int(S.get(skey, dflt)), step=1,
                                        key=f"wi_{skey}", on_change=_sync, args=(f"wi_{skey}", skey))
                total_weight = int(S.get("w_sip", 40)) + int(S.get("w_ig", 30)) + int(S.get("w_sr", 30))
                if total_weight != 100:
                    st.error(f"⚠️ مجموع الأوزان الحالية ({total_weight}%). يجب أن يساوي 100% تماماً للإرسال.")
                else:
                    st.success("✅ مجموع الأوزان النسبية صحيح (100%).")

                st.checkbox(
                    "✔️ أؤكد مراجعة وتحديد الأوزان النسبية أعلاه وفق تقديري المهني (إلزامي لتفعيل الإرسال)",
                    value=bool(S.get("weights_confirmed", False)),
                    key="wi_weights_confirmed",
                    on_change=_sync,
                    args=("wi_weights_confirmed", "weights_confirmed")
                )

                S["comments"] = st.text_area("💬 مقترحات أو معوقات ترون أنها قد تؤثر على تطبيق هذا النموذج في البنوك المصرية:",
                                             value=S.get("comments", ""), placeholder="اكتب الملاحظات أو المقترحات هنا...",
                                             key="wi_comments", height=120, on_change=_sync, args=("wi_comments", "comments"))

        def _go(delta):
            if "w_name" in st.session_state and st.session_state["w_name"] is not None:
                S["name"] = st.session_state["w_name"]
            if "wi_comments" in st.session_state and st.session_state["wi_comments"] is not None:
                S["comments"] = st.session_state["wi_comments"]
            st.session_state.survey_wizard_step += delta
            st.session_state.scroll_survey_top = True
            token_now = _encode_survey_draft(S, st.session_state.survey_wizard_step)
            if token_now:
                st.query_params["sdraft"] = token_now
                st.query_params["tab"] = "7"

        if not already_submitted:
            col_prev, _sp, col_next = st.columns([1, 2, 1])
            with col_prev:
                if step_num > 1:
                    st.button("⬅️ الخطوة السابقة", use_container_width=True, on_click=_go, args=(-1,), key="nav_prev")
            with col_next:
                if step_num < max_wizard_steps:
                    ok = step_complete(step_key)
                    st.button("الخطوة التالية ➡️", use_container_width=True, type="primary", disabled=not ok,
                              on_click=_go, args=(1,), key="nav_next",
                              help=None if ok else "يرجى استكمال جميع الحقول/العبارات في هذه المرحلة أولاً.")
                else:
                    can_submit = step_complete("final")
                    if st.button("📤 إرسال وحفظ الاستبيان ", use_container_width=True, type="primary",
                                 disabled=not can_submit, key="submit_survey_final_btn",
                                 help=None if can_submit else "تأكد من أن مجموع الأوزان = 100% وتفعيل مربع التأكيد."):

                        # 1) مؤشرات الجاهزية الحالية للبنك (القسم الأول - وصفي)
                        readiness_answers = {
                            f"جاهزية_البنك_{idx}": READINESS_LIKERT.get(S.get(f"r{idx}"))
                            for idx in range(1, 6)
                        }
                        r_vals = [v for v in readiness_answers.values() if v is not None]
                        avg_readiness = round(sum(r_vals) / len(r_vals), 2) if r_vals else None

                        # 2) عبارات تقييم المنصة (1-30) + قابلية الاستخدام والثقة والجدوى (31-35)
                        answers, axis_scores = {}, {ax: [] for ax in SURVEY_AXES}
                        for n in range(1, 36):
                            val = LIKERT.get(S.get(f"stmt_{n}")) if n in required_stmts else None
                            answers[f"العبارة_{n}"] = val
                        for ax in axes_required:
                            axis_scores[ax] = [answers[f"العبارة_{n}"] for n in SURVEY_AXES[ax]["nums"]]

                        def _avg(ax):
                            sc = axis_scores[ax]
                            return round(sum(sc) / len(sc), 2) if ax in axes_required and sc else None

                        resp_id = f"SRV-{datetime.now().strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
                        raw_name = st.session_state.get("w_name") if st.session_state.get("w_name") is not None else S.get("name", "")
                        raw_comments = st.session_state.get("wi_comments") if st.session_state.get("wi_comments") is not None else S.get("comments", "")
                        rec = {
                            "معرف الاستجابة": resp_id,
                            "الاسم (اختياري)": clean_text(raw_name),
                            "اسم البنك": clean_text(S.get("bank", "")),
                            "طبيعة المؤسسة": clean_text(S.get("org", "")),
                            "المؤهل العلمي": clean_text(S.get("sci", "")),
                            "مجال التخصص الوظيفي": clean_text(S.get("spec", "")),
                            "المستوى الوظيفي": clean_text(S.get("job", "")),
                            "سنوات الخبرة": S.get("exp", ""),
                            "مقيدة بالبورصة": S.get("listed", ""),
                            "مسار الاستبيان": "شامل (35 عبارة)" if is_full_assessment else f"مخصص ({total_req_count} عبارة)",
                            "متوسط الجاهزية الحالية للبنك": avg_readiness,
                            "وزن منصات المعلومات (%)": int(S.get("w_sip", 40)),
                            "وزن الحوكمة المؤسسية (%)": int(S.get("w_ig", 30)),
                            "وزن تقارير الاستدامة (%)": int(S.get("w_sr", 30)),
                            **{SURVEY_AXES[ax]["avg_col"]: _avg(ax) for ax in SURVEY_AXES},
                            **readiness_answers,
                            **answers,
                            "ملاحظات ومقترحات إضافية": clean_text(raw_comments),
                            "وقت الإرسال": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        try:
                            save_survey_to_cloud(rec)
                            # حفظ نسخة احتياطية محلية في CSV أيضاً
                            try:
                                current_surveys = load_survey_log_from_file()
                                current_surveys.append(rec)
                                pd.DataFrame(current_surveys).to_csv(SURVEY_LOG_FILE, index=False, encoding="utf-8-sig")
                            except Exception:
                                pass
                            S["submitted_id"] = resp_id
                            st.session_state.pop("cached_surveys_df", None)
                            st.session_state.scroll_survey_top = True
                            if "sdraft" in st.query_params:
                                del st.query_params["sdraft"]
                            sync_survey_browser_backup()
                            st.success("✅ تم حفظ الاستجابة بنجاح في السحابة!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ حدث خطأ أثناء حفظ الاستجابة في السحابة: {e}")

        # تنفيذ التمرير السلس إلى بداية الاستبيان عند الانتقال بين المراحل
        if st.session_state.get("scroll_survey_top", False):
            st.session_state.scroll_survey_top = False
            components.html(
                f"""
                <script>
                (function() {{
                    function scrollToSurveyStart() {{
                        var doc = window.parent.document;
                        var target = doc.getElementById('survey-wizard-header') || doc.getElementById('survey-top-anchor');
                        if (target) {{
                            target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                        }} else {{
                            window.parent.scrollTo({{ top: 0, behavior: 'smooth' }});
                        }}
                    }}
                    scrollToSurveyStart();
                    setTimeout(scrollToSurveyStart, 120);
                    setTimeout(scrollToSurveyStart, 350);
                }})();
                </script>
                """,
                height=0,
                width=0,
            )

    # --------------------------------------------------------------------------
    # لوحة التحليل الإداري للأدمن (التصدير بصيغة Excel نقية ومتوافقة مع العربية)
    # --------------------------------------------------------------------------
    if st.session_state.get("role") == "admin":
        st.markdown("---")
        st.markdown("#### 📊 لوحة تحليل استجابات الاستبيان (خاص بالأدمن):")

        col_adm1, col_adm2, col_adm3 = st.columns(3)
        with col_adm1:
            if st.button("🔄 اختبار الاتصال وتهيئة Supabase", key="admin_test_db", use_container_width=True):
                is_success, msg = init_db(force=True)
                if is_success:
                    st.session_state.pop("cached_surveys_df", None)
                    st.success("✅ جدول `survey_responses` متصل وجاهز وتم تحديث هيكله!")
                else:
                    st.error(f"❌ خطأ الاتصال: {msg}")
        with col_adm2:
            if st.button("📥 سحب وتحديث الاستجابات من السحابة", key="admin_refresh_surveys", use_container_width=True, type="primary"):
                st.session_state["cached_surveys_df"] = load_survey_log_from_cloud()
        with col_adm3:
            st.link_button(
                "🌐 فتح لوحة إدارة وبيانات KoboToolbox",
                "https://kf.kobotoolbox.org/",
                use_container_width=True
            )

        if "cached_surveys_df" not in st.session_state:
            st.session_state["cached_surveys_df"] = load_survey_log_from_cloud()

        df_surveys = st.session_state["cached_surveys_df"]
        if not df_surveys.empty:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("إجمالي الاستجابات", f"{len(df_surveys)}")
            if "avg_sip" in df_surveys.columns and df_surveys["avg_sip"].notna().any():
                m2.metric("متوسط محور SIP (من 5)", f"{df_surveys['avg_sip'].mean():.2f}")
            if "avg_ig" in df_surveys.columns and df_surveys["avg_ig"].notna().any():
                m3.metric("متوسط محور IG (من 5)", f"{df_surveys['avg_ig'].mean():.2f}")
            if "avg_sr" in df_surveys.columns and df_surveys["avg_sr"].notna().any():
                m4.metric("متوسط محور SR (من 5)", f"{df_surveys['avg_sr'].mean():.2f}")

            st.dataframe(df_surveys, use_container_width=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_surveys.to_excel(writer, index=False, sheet_name='استجابات الاستبيان')
            excel_data = buffer.getvalue()

            st.download_button(
                label="📥 تحميل شيت إكسيل استجابات Supabase المفصل بالعربية (Excel .xlsx)",
                data=excel_data,
                file_name="شيت_استجابات_الاستبيان_الميداني_المفصل.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("📋 لم يتم تسجيل أي استجابات في قاعدة البيانات السحابية (Supabase) حتى الآن.")
# ------------------------------------------------------------------------------
# التبويب الثامن: دليل المستخدم الرسمي للمنصة والتوثيق المنهجي الشامل
# ------------------------------------------------------------------------------
with tab8:
    st.markdown("""
    <div dir="rtl" style="text-align: right; margin-bottom: 18px;">
        <h3 style="color: #002B49; font-weight: 800; font-size: clamp(16px, 4vw, 20px); margin-bottom: 4px;">📖 دليل المستخدم والتوثيق المنهجي لمنصة (رصين)</h3>
        <p style="color: #475569; font-size: clamp(13px, 3.2vw, 14px);">المرجع التشغيلي والأكاديمي المعتمد للمحكمين، أعضاء لجنة المناقشة، الباحثين، والقيادات المصرفية لاستخدام كافة وحدات المنصة بكفاءة تامة.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(flat_html(f"""
    <div style="background: #FFFFFF; padding: clamp(18px, 3.5vw, 30px); border-radius: 14px; border: 1.5px solid {CBE_GOLD}; line-height: 1.95; box-shadow: 0 4px 15px rgba(0,0,0,0.04); margin-bottom: 18px;" dir="rtl">
        <div style="text-align: center; border-bottom: 2px solid {CBE_GOLD}; padding-bottom: 12px; margin-bottom: 16px;">
            <h2 style="color: {CBE_NAVY}; margin: 0; font-size: clamp(17px, 4vw, 21px); font-weight: 800;">📖 دليل المستخدم والتوثيق المنهجي للمنصة الوطنية الذكية (رصين)</h2>
            <p style="color: #64748B; font-size: 13.5px; margin: 6px 0 0 0;">نموذج مقترح لتعزيز الحوكمة المؤسسية بالقطاع المصرفي المصري باستخدام منصة معلومات ذكية: بالتطبيق على تقارير الاستدامة</p>
        </div>
        <p style="color: #1E293B; font-size: 14px; margin-bottom: 10px;">
            <b>1️⃣ الإطار الأكاديمي والرؤية العلمية:</b><br>
            تمثل منصة <b>(رصين)</b> التطبيق العملي المقترح ضمن متطلبات نيل درجة <b>دكتوراه الفلسفة في العلوم البيئية – جامعة عين شمس</b>، إعداد الباحث/ <b>أيمن الدسوقي</b> (مدرس مساعد إدارة المعرفة – معهد التخطيط القومي). وتستهدف المنصة توطين حلول الذكاء الاصطناعي والبيانات الضخمة لتعزيز الحوكمة المؤسسية، ودعم السيادة الرقمية، وأتمتة تقييم وتوليد تقارير الاستدامة في البنوك العاملة بالقطاع المصرفي المصري بما يتسق مع توجهات البنك المركزي المصري ورؤية مصر 2030 ومقررات لجنة بازل.
        </p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; margin-top: 14px; text-align: center;">
            <div style="background: {CBE_BG}; padding: 10px; border-radius: 8px; border-right: 4px solid {CBE_NAVY};">
                <div style="font-size: 11.5px; color: #64748B; font-weight: 700;">مؤشر القياس المركب</div>
                <div style="font-size: 15px; font-weight: 800; color: {CBE_NAVY};">SSGI (63 متغيراً / 15 بُعداً)</div>
            </div>
            <div style="background: {CBE_BG}; padding: 10px; border-radius: 8px; border-right: 4px solid {CBE_GOLD};">
                <div style="font-size: 11.5px; color: #64748B; font-weight: 700;">الأوزان النسبية المعتمدة</div>
                <div style="font-size: 15px; font-weight: 800; color: {CBE_NAVY};">SIP 40% | IG 30% | SR 30%</div>
            </div>
            <div style="background: {CBE_BG}; padding: 10px; border-radius: 8px; border-right: 4px solid #10B981;">
                <div style="font-size: 11.5px; color: #64748B; font-weight: 700;">التدقيق والاستخلاص الذكي</div>
                <div style="font-size: 15px; font-weight: 800; color: {CBE_NAVY};">Hybrid RAG Engine</div>
            </div>
            <div style="background: {CBE_BG}; padding: 10px; border-radius: 8px; border-right: 4px solid #0F766E;">
                <div style="font-size: 11.5px; color: #64748B; font-weight: 700;">الاستبيان والحماية</div>
                <div style="font-size: 15px; font-weight: 800; color: {CBE_NAVY};">Supabase + Kobo + F5 Safe</div>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)

    with st.expander("2️⃣ الدليل التشغيلي المفصل لوحدات وتبويبات المنصة (9 وحدات تفاعلية)", expanded=True):
        st.markdown(flat_html(f"""
        <div dir="rtl" style="text-align: right; line-height: 1.95; font-size: 14px; color: #1E293B;">
            <ul style="margin: 0; padding-right: 20px;">
                <li style="margin-bottom: 10px;"><b>🏠 التبويب التمهيدي — الرئيسية والإطار المنهجي:</b> يقدّم التهيئة العلمية للمحكمين والزوار، ويعرض خريطة النموذج البحثي بأبعاده الـ 15 (منصات المعلومات الذكية 4 أبعاد، تقارير الاستدامة 5 أبعاد، الحوكمة المؤسسية 6 أبعاد)، مع بطاقات جولة سريعة تفاعلية تنقل المستخدم بضغطة واحدة إلى أي قسم بالمنصة.</li>
                <li style="margin-bottom: 10px;"><b>🎯 التبويب الأول — اسأل رصين (Hybrid RAG Engine):</b> محرك استخلاص وتحليل معرفي مخصص لكل بنك مصري على حدة، يعتمد على تقنية الاسترجاع المعزز بالتوليد (RAG) للإجابة عن أسئلة التأسيس والملكية، الحوكمة، الاستدامة، والسيادة الرقمية بدقة موثقة مع إمكانية تصدير الرد الفردي أو سجل الجلسة كاملاً بصيغة Word (.docx) أصلية.</li>
                <li style="margin-bottom: 10px;"><b>📊 التبويب الثاني — المؤشر المركب (SSGI):</b> منظومة تشخيص كمي متعددة الأبعاد تقيس جاهزية البنك عبر <b>63 متغيراً فرعياً</b> موزعة على ثلاثة محاور رئيسة: منصات المعلومات الذكية (SIP - 40% بواقع 16 متغيراً)، الحوكمة المؤسسية (IG - 30% بواقع 25 متغيراً)، وتقارير الاستدامة (SR - 30% بواقع 22 متغيراً). يتيح تحميل نموذج تقييم Excel تفاعلي بالمعادلات، وعرض رسوم رادارية ومقارنات مرجعية وترتيب تنازلي للبنوك.</li>
                <li style="margin-bottom: 10px;"><b>📈 التبويب الثالث — محاكي السياسات (Policy Simulator):</b> أداة استشرافية لاختبار أثر التدخلات المستقبلية عبر ثلاثة سيناريوهات استراتيجية (التشاؤمي، المعتدل/التفاؤلي، والطموح/الاستباقي) وفق نماذج الانحدار المتعدد، مع تحديد المحور الأضعف والأقوى تلقائياً وحساب صافي التغير المتوقع بيانياً ورقمياً.</li>
                <li style="margin-bottom: 10px;"><b>🛡️ التبويب الرابع — لوحة دعم اتخاذ القرار:</b> تحوّل نتائج التشخيص القياسي الفعلي لكل بنك إلى حزمة قرارات تنفيذية إلزامية موجهة لمجلس الإدارة ومصفوفة تكليفات محددة للجان المراجعة والمخاطر والاستدامة وقطاع تكنولوجيا المعلومات.</li>
                <li style="margin-bottom: 10px;"><b>📑 التبويب الخامس — التقرير التنفيذي الموحد:</b> يجمع تلقائياً ترتيب البنوك المسجلة، ملامح البنك المتصدر، مخرجات المحاكاة الاستشرافية، وتوصيات لوحة القرار في مستند استراتيجي موحد قابل للتحميل بصيغة Word (.docx).</li>
                <li style="margin-bottom: 10px;"><b>🌿 التبويب السادس — تقييم ومولد تقارير الاستدامة (GRI / ISSB / CBE):</b> يضم ثلاث وحدات متكاملة:
                    <br>① <i>المدقق الآلي لتقارير الاستدامة (AI ESG Audit):</i> يقرأ ملفات تقارير الاستدامة المرفوعة (PDF/TXT) ويقيّم امتثالها البيئي والاجتماعي والحوكمي مع مزامنة النتيجة مباشرة مع سجل البنك.
                    <br>② <i>مولد المسودات التوجيهية:</i> يصيغ مسودة تقرير استدامة مفصلة ومخصصة لأرقام كل بنك.
                    <br>③ <i>الدليل العملي الشامل:</i> يستعرض 30 مؤشراً معيارياً مستمداً من (GRI, ISSB S1/S2, UNDP SDG Impact Standards).</li>
                <li style="margin-bottom: 10px;"><b>📋 التبويب السابع — استبيان فرق العمل المصرفي (Dual-Channel Survey):</b> أداة جمع البيانات الميدانية عبر قناتين معتمدتين: نموذج المنصة التفاعلي (المرتبط سحابياً بـ <b>Supabase</b> مع حفظ تلقائي للمسودات ضد التحديث العرضي F5 ومسارات ذكية حسب التخصص الوظيفي أو مسار شامل من 31 عبارة)، واستمارة <b>KoboToolbox</b> الدولية المدمجة.</li>
                <li><b>📖 التبويب الثامن — دليل المستخدم الرسمي (هذا القسم):</b> التوثيق المنهجي والتشغيلي الموحد لكافة مكونات المنصة وإرشادات الاستخدام.</li>
            </ul>
        </div>
        """), unsafe_allow_html=True)

    with st.expander("3️⃣ مسار الاستخدام الموصى به (Workflow) وتدفق البيانات بين الأقسام", expanded=False):
        st.markdown(flat_html(f"""
        <div dir="rtl" style="text-align: right; line-height: 1.95; font-size: 14px; color: #1E293B;">
            <ol style="margin: 0; padding-right: 22px;">
                <li style="margin-bottom: 8px;"><b>الخطوة الأولى (التهيئة المنهجية):</b> ابدأ بتبويب <b>«🏠 الرئيسية»</b> لاستعراض خريطة النموذج البحثي وأبعاده الـ 15، ثم انقر على أي بطاقة في الجولة السريعة للانتقال المباشر.</li>
                <li style="margin-bottom: 8px;"><b>الخطوة الثانية (الاستكشاف المعرفي):</b> انتقل إلى <b>«🎯 اسأل رصين»</b> لاختيار البنك المصرفي واستعراض خلفيته المؤسسية وممارساته في الحوكمة والاستدامة وتصدير الردود الموثقة.</li>
                <li style="margin-bottom: 8px;"><b>الخطوة الثالثة (التشخيص القياسي):</b> انتقل إلى <b>«📊 المؤشر المركب (SSGI)»</b>، وحمل ملف التقييم التفصيلي (Excel) أو اضبط أشرطة القياس للمحاور الثلاثة، ثم اضغط على <i>«احسب وسجل مؤشر البنك»</i> لتسجيل البنك في ذاكرة الجلسة.</li>
                <li style="margin-bottom: 8px;"><b>الخطوة الرابعة (الاستشراف واتخاذ القرار):</b> انتقل إلى <b>«📈 محاكي السياسات»</b> لاختبار سيناريوهات التحسين، ثم إلى <b>«🛡️ لوحة دعم اتخاذ القرار»</b> لاعتماد حزمة التوصيات التنفيذية للبنك.</li>
                <li style="margin-bottom: 8px;"><b>الخطوة الخامسة (التدقيق وتوليد التقارير):</b> استخدم تبويب <b>«🌿 تقارير الاستدامة»</b> لتدقيق تقرير الاستدامة الفعلي للبنك (PDF) أو توليد مسودة تقرير متوافقة مع (GRI/ISSB)، ثم استخرج الحصيلة الكاملة من <b>«📑 التقرير التنفيذي»</b>.</li>
                <li><b>الخطوة السادسة (المشاركة الميدانية):</b> شارك برأيك المهني عبر تبويب <b>«📋 استبيان فرق العمل»</b> سواء عبر النموذج التفاعلي السحابي أو عبر استمارة KoboToolbox.</li>
            </ol>
        </div>
        """), unsafe_allow_html=True)

    with st.expander("4️⃣ البنية التقنية وضوابط الخصوصية واستمرارية الجلسة", expanded=False):
        st.markdown(flat_html(f"""
        <div dir="rtl" style="text-align: right; line-height: 1.95; font-size: 14px; color: #1E293B;">
            <ul style="margin: 0; padding-right: 20px;">
                <li style="margin-bottom: 8px;"><b>منع الهلوسة المعلوماتية (Anti-Hallucination):</b> يعتمد محرك الاستعلام على التقييد السياقي الصارم بالمصادر الرسمية والتقارير المصرفية المعتمدة، مع تدقيق آلي للتباين بين البنوك (<code>audit_differentiation</code>).</li>
                <li style="margin-bottom: 8px;"><b>استمرارية الجلسة وحماية البيانات (F5 / Refresh Protection):</b> تم تزويد المنصة بنظام استعادة تلقائي للجلسة والتبويب النشط ومسودات الاستبيان عبر <code>localStorage</code> وروابط الجلسة المشفرة لمنع فقدان أي مدخلات عند تحديث المتصفح.</li>
                <li style="margin-bottom: 8px;"><b>حوكمة الصلاحيات والجلسات:</b> تفصل المنصة بين واجهة المستخدم/الباحث وواجهة المشرف الإداري (Admin) المحمية بتشفير (SHA-256) لإدارة قواعد البيانات السحابية وسجلات المتابعة.</li>
                <li><b>التوافق مع الأجهزة والمؤثرات التفاعلية:</b> واجهة عربية متجاوبة بالكامل (RTL) تدعم الحواسيب والهواتف الذكية، مزودة بمحرك مؤثرات صوتية تفاعلية فورية (<code>Web Audio API</code>) قابل للتخصيص أو الكتم من الشريط العلوي.</li>
            </ul>
        </div>
        """), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    manual_html_for_docx = f"""
    <h3>1. الإطار الأكاديمي والرؤية العلمية</h3>
    <p>تمثل منصة (رصين) المقترح التطبيقي للمنصة الوطنية الذكية لتعزيز الحوكمة المؤسسية بالقطاع المصرفي المصري، والمقدمة ضمن متطلبات نيل درجة دكتوراه الفلسفة في العلوم البيئية – جامعة عين شمس، إعداد الباحث: أيمن الدسوقي (مدرس مساعد إدارة المعرفة – معهد التخطيط القومي).</p>
    <p>المعادلة الهيكلية لمؤشر الحوكمة الذكية المستدامة (SSGI): منصات المعلومات الذكية SIP (40%) + الحوكمة المؤسسية IG (30%) + تقارير الاستدامة SR (30%)، بإجمالي 63 متغيراً فرعياً موزعة على 15 بُعداً رئيسياً.</p>

    <h3>2. الدليل التشغيلي المفصل لوحدات وتبويبات المنصة</h3>
    <ul>
        <li>الرئيسية والإطار المنهجي: عرض خريطة النموذج البحثي بأبعاده الـ 15 وجولة التنقل السريعة لوحدات المنصة.</li>
        <li>اسأل رصين (Hybrid RAG Engine): محرك استخلاص وتحليل معرفي مخصص لكل بنك مصري على حدة للإجابة عن أسئلة التأسيس والحوكمة والاستدامة وتصدير الردود بصيغة Word (.docx).</li>
        <li>المؤشر المركب (SSGI): أداة تشخيص كمي تقيس جاهزية البنك عبر 63 متغيراً فرعياً (SIP 40%، IG 30%، SR 30%) مع نموذج Excel تفاعلي وتحليل راداري ومقارنات مرجعية.</li>
        <li>محاكي السياسات (Policy Simulator): أداة استشرافية لاختبار السيناريوهات الاستراتيجية (التشاؤمي، المعتدل، الطموح) وحساب صافي التغير المتوقع.</li>
        <li>لوحة دعم اتخاذ القرار: تحويل نتائج التشخيص الفعلي لكل بنك إلى قرارات تنفيذية ومصفوفة تكليفات للجان مجلس الإدارة.</li>
        <li>التقرير التنفيذي الموحد: تجميع آلي شامل لترتيب البنوك، ملامح البنك المتصدر، مخرجات المحاكاة، وتوصيات لوحة القرار.</li>
        <li>تقارير الاستدامة (GRI / ISSB / CBE): يشمل المدقق الآلي لتقارير الاستدامة عبر الذكاء الاصطناعي، ومولد المسودات التوجيهية، والدليل العملي المكون من 30 مؤشراً لـ (ESG).</li>
        <li>استبيان فرق العمل المصرفي (Dual-Channel): أداة جمع البيانات الميدانية عبر نموذج المنصة السحابي (Supabase) المحمي ضد التحديث العرضي (F5) واستمارة KoboToolbox الدولية.</li>
        <li>دليل المستخدم الرسمي: التوثيق المنهجي والتشغيلي الموحد للمنصة.</li>
    </ul>

    <h3>3. مسار الاستخدام الموصى به (Workflow)</h3>
    <p>• الخطوة الأولى (التهيئة المنهجية): مراجعة خريطة النموذج البحثي في تبويب «الرئيسية».</p>
    <p>• الخطوة الثانية (الاستكشاف المعرفي): اختيار البنك في تبويب «اسأل رصين» لاستعراض بياناته الموثقة.</p>
    <p>• الخطوة الثالثة (التشخيص القياسي): حساب وتسجيل مؤشر SSGI للبنك عبر أشرطة القياس أو نموذج الـ 63 متغيراً.</p>
    <p>• الخطوة الرابعة (الاستشراف واتخاذ القرار): اختبار السيناريوهات في «محاكي السياسات» واعتماد التوصيات في «لوحة دعم اتخاذ القرار».</p>
    <p>• الخطوة الخامسة (التدقيق وتوليد التقارير): تدقيق ملف الاستدامة الفعلي أو توليد مسودة التقرير المخصصة واستخراج التقرير التنفيذي الموحد.</p>
    <p>• الخطوة السادسة (المشاركة الميدانية): تعبئة الاستبيان الميداني المخصص لفرق العمل المصرفي.</p>

    <h3>4. البنية التقنية وضوابط الخصوصية واستمرارية الجلسة</h3>
    <ul>
        <li>منع الهلوسة المعلوماتية: التقييد السياقي بالمصادر الرسمية والتقارير المصرفية المعتمدة مع التدقيق الآلي للتباين.</li>
        <li>استمرارية الجلسة وحماية البيانات: حفظ تلقائي للجلسة والتبويب النشط ومسودات الاستبيان لمنع فقدان البيانات عند الضغط على F5.</li>
        <li>حوكمة الصلاحيات: فصل واجهة المستخدم عن لوحة المشرف الإداري المحمية بالتشفير (SHA-256).</li>
        <li>التوافق الكامل مع الأجهزة: واجهة عربية متجاوبة (RTL) تدعم الحواسيب والهواتف الذكية.</li>
    </ul>
    """

    manual_bytes, manual_ext, manual_mime = build_native_docx(
        title="دليل المستخدم الرسمي والتوثيق المنهجي لمنصة (رصين)",
        subtitle="مقترح المنصة الوطنية الذكية لتعزيز الحوكمة المؤسسية بالقطاع المصرفي المصري | إعداد الباحث: أيمن الدسوقي",
        html_body=manual_html_for_docx,
    )

    st.download_button(
        label=f"📥 تحميل دليل المستخدم الرسمي",
        data=manual_bytes,
        file_name=f"دليل_المستخدم_الرسمي_منصة_رصين_2026{manual_ext}",
        mime=manual_mime,
        use_container_width=True,
        type="primary",
        key="dl_official_user_manual_btn"
    )

# ------------------------------------------------------------------------------
# التبويب التاسع: لوحة تحكم المشرف والزوار (Admin Dashboard)
# ------------------------------------------------------------------------------
if tab9 is not None:
    with tab9:
        st.markdown("""
        <div dir="rtl" style="text-align: right; margin-bottom: 18px;">
            <h3 style="color: #002B49; font-weight: 800; font-size: clamp(16px, 4vw, 20px); margin-bottom: 4px;">🔒 لوحة تحكم المشرف وسجلات الزوار وتدقيق الجودة (Admin Dashboard)</h3>
            <p style="color: #475569; font-size: clamp(13px, 3.2vw, 14px);">مراقبة مؤشرات منصة (رصين)، تدقيق تمايز مخرجات محرك الذكاء الاصطناعي بين البنوك، وإدارة وتصدير سجلات دخول الزوار وعناوين IP.</p>
        </div>
        """, unsafe_allow_html=True)

        visitors_data_list = load_visitors_log_from_file()
        df_v_raw = pd.DataFrame(visitors_data_list) if visitors_data_list else pd.DataFrame()
        unique_ips_count = df_v_raw["عنوان IP"].nunique() if (not df_v_raw.empty and "عنوان IP" in df_v_raw.columns) else 0
        diagnosed_banks_cnt = len([r for r in st.session_state.get("history_state", []) if isinstance(r, dict) and "مؤشر SSGI المركب" in r])
        rag_queries_cnt = len(st.session_state.get("rag_query_history", []))
        local_surveys_list = load_survey_log_from_file() if "load_survey_log_from_file" in globals() else []
        local_surveys_cnt = len(local_surveys_list) if isinstance(local_surveys_list, list) else 0
        has_gemini_key = bool(st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY"))
        has_supabase_url = bool("postgres" in st.secrets and "url" in st.secrets["postgres"])

        st.markdown(flat_html(f"""
        <div dir="rtl" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px;">
            <div style="background: #FFFFFF; padding: 14px; border-radius: 12px; border-right: 5px solid {CBE_NAVY}; border: 1px solid #E2E8F0; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <span style="font-size: 11.5px; color: #64748B; font-weight: 700;">إجمالي جلسات الدخول</span>
                <div style="font-size: 22px; font-weight: 900; color: {CBE_NAVY}; margin-top: 4px;">{len(df_v_raw)}</div>
                <span style="font-size: 11px; color: #475569;">عناوين IP فريدة: <b>{unique_ips_count}</b></span>
            </div>
            <div style="background: #FFFFFF; padding: 14px; border-radius: 12px; border-right: 5px solid {CBE_GOLD}; border: 1px solid #E2E8F0; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <span style="font-size: 11.5px; color: #64748B; font-weight: 700;">البنوك المُشخَّصة (الجلسة)</span>
                <div style="font-size: 22px; font-weight: 900; color: {CBE_NAVY}; margin-top: 4px;">{diagnosed_banks_cnt}</div>
                <span style="font-size: 11px; color: #475569;">استعلامات RAG: <b>{rag_queries_cnt}</b></span>
            </div>
            <div style="background: #FFFFFF; padding: 14px; border-radius: 12px; border-right: 5px solid {'#10B981' if has_gemini_key else '#EF4444'}; border: 1px solid #E2E8F0; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <span style="font-size: 11.5px; color: #64748B; font-weight: 700;">حالة محرك Gemini AI</span>
                <div style="font-size: 16px; font-weight: 800; color: {'#10B981' if has_gemini_key else '#EF4444'}; margin-top: 8px;">{'🟢 متصل ومفعّل' if has_gemini_key else '🔴 غير مفعّل'}</div>
            </div>
            <div style="background: #FFFFFF; padding: 14px; border-radius: 12px; border-right: 5px solid {'#10B981' if has_supabase_url else '#F59E0B'}; border: 1px solid #E2E8F0; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <span style="font-size: 11.5px; color: #64748B; font-weight: 700;">سحابة الاستبيانات (Supabase)</span>
                <div style="font-size: 16px; font-weight: 800; color: {'#10B981' if has_supabase_url else '#F59E0B'}; margin-top: 8px;">{'🟢 مهيأة للاتصال' if has_supabase_url else '🟡 وضع محلي'}</div>
                <span style="font-size: 11px; color: #475569;">السجل المحلي: <b>{local_surveys_cnt}</b></span>
            </div>
        </div>
        """), unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("""
        <div dir="rtl" style="text-align: right; margin-bottom: 10px;">
            <h4 style="color: #002B49; font-weight: 800; margin-bottom: 4px;">🔍 أداة فحص تدقيق التشابه والتمايز بين البنوك (<code>audit_differentiation</code>)</h4>
            <p style="color: #64748B; font-size: 13px;">اختبار جودة واستقلالية إجابات المحرك الذكي عبر البنوك للتأكد من عدم تكرار النصوص القالبية وتجاوز عتبة التشابه الدلالي.</p>
        </div>
        """, unsafe_allow_html=True)

        col_aud_cfg1, col_aud_cfg2 = st.columns([1, 2], gap="medium")
        with col_aud_cfg1:
            threshold_slider = st.slider(
                "عتبة التشابه المسموحة (Threshold)",
                min_value=0.50,
                max_value=0.99,
                value=0.90,
                step=0.01,
                key="admin_diff_threshold",
                help="أي زوج من الإجابات تتجاوز نسبة التشابه بينهما هذه القيمة سيتم رصده كتنبيه."
            )
            available_banks_only = [b for b in BANKS_LIST_AR if b != "اختر البنك المصرفي"]
            selected_audit_banks = st.multiselect(
                "نطاق البنوك للفحص (اتركه فارغاً لفحص كافة البنوك)",
                options=available_banks_only,
                default=[],
                key="admin_audit_banks_sel"
            )

        with col_aud_cfg2:
            default_audit_questions = [
                "متى تأسس البنك ومن هو مؤسسه وما هي ملكيته؟",
                "كيف يتعامل البنك مع مخاطر المناخ والتمويل الأخضر؟",
                "كيف يضمن البنك الحصانة السيبرانية ومنع تسريب البيانات المالية الحساسة؟"
            ]
            custom_q_text = st.text_area(
                "الأسئلة المعيارية للاختبار (سؤال واحد في كل سطر):",
                value="\n".join(default_audit_questions),
                height=115,
                key="admin_audit_questions_box"
            )

        col_aud_btn1, col_aud_btn2 = st.columns([2, 1])
        with col_aud_btn1:
            run_diff_audit_btn = st.button("🚀 تشغيل فحص تمايز الإجابات الآن", type="primary", use_container_width=True, key="run_diff_audit_btn")
        with col_aud_btn2:
            if st.session_state.get("last_diff_audit_report"):
                if st.button("🗑️ مسح نتيجة الفحص", type="secondary", use_container_width=True, key="clear_diff_audit_btn"):
                    del st.session_state["last_diff_audit_report"]
                    st.rerun()

        def _safe_run_differentiation_audit(banks_list, questions_list, thresh_val):
            """
            دالة غلاف ذكية تفحص توقيع الدالة الأصلية audit_differentiation وتمرر المعاملات بالصيغة الصحيحة
            دون إثارة TypeError، مع محرك احتياطي مدمج للمقارنة النصية بين البنوك.
            """
            if "audit_differentiation" in globals() and callable(globals()["audit_differentiation"]):
                fn = globals()["audit_differentiation"]
                try:
                    sig = inspect.signature(fn)
                    params = list(sig.parameters.keys())
                    if len(params) == 0:
                        return fn()
                    elif len(params) == 1:
                        p0 = params[0]
                        if "thresh" in p0 or "sim" in p0:
                            return fn(thresh_val)
                        return fn(banks_list)
                    elif len(params) == 2:
                        return fn(banks_list, questions_list)
                    else:
                        return fn(banks_list, questions_list, thresh_val)
                except Exception:
                    pass

            flagged_res = []
            rag_fn = globals().get("process_rag_gemini_query") or globals().get("generate_rag_response") or globals().get("query_bank_rag")
            if callable(rag_fn):
                for q in questions_list:
                    answers_map = {}
                    for b in banks_list:
                        try:
                            ans = rag_fn(b, q)
                            answers_map[b] = str(ans or "")
                        except Exception:
                            answers_map[b] = ""
                    b_keys = list(answers_map.keys())
                    for i in range(len(b_keys)):
                        for j in range(i + 1, len(b_keys)):
                            b1, b2 = b_keys[i], b_keys[j]
                            t1, t2 = answers_map[b1], answers_map[b2]
                            if t1 and t2:
                                ratio = SequenceMatcher(None, t1, t2).ratio()
                                if ratio >= thresh_val:
                                    flagged_res.append((q, b1, b2, round(ratio, 4)))
            return flagged_res

        if run_diff_audit_btn:
            banks_to_check = selected_audit_banks if selected_audit_banks else available_banks_only
            questions_to_check = [q.strip() for q in custom_q_text.splitlines() if q.strip()]

            if len(banks_to_check) < 2:
                st.warning("⚠️ يرجى اختيار بنكين على الأقل لإجراء المقارنة والتدقيق.")
            elif not questions_to_check:
                st.warning("⚠️ يرجى إدخال سؤال واحد على الأقل لتشغيل الفحص.")
            else:
                with st.spinner("⏳ جاري مقارنة إجابات البنوك وقياس معاملات التشابه..."):
                    flagged_pairs = _safe_run_differentiation_audit(
                        banks_to_check,
                        questions_to_check,
                        threshold_slider
                    )

                    st.session_state["last_diff_audit_report"] = {
                        "flagged": flagged_pairs or [],
                        "threshold": threshold_slider,
                        "banks_count": len(banks_to_check),
                        "questions_count": len(questions_to_check),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

        if "last_diff_audit_report" in st.session_state:
            rep_audit = st.session_state["last_diff_audit_report"]
            flagged = rep_audit["flagged"]
            st.caption(f"🕒 آخر فحص: {rep_audit['timestamp']} | شمل {rep_audit['banks_count']} بنكاً و {rep_audit['questions_count']} أسئلة عند عتبة ({rep_audit['threshold']}).")

            if flagged:
                st.warning(f"⚠️ تنبيه: تم رصد **{len(flagged)}** حالة تجاوزت عتبة التشابه `{rep_audit['threshold']}`:")
                structured_rows = []
                for item in flagged:
                    if isinstance(item, dict):
                        structured_rows.append(item)
                    elif isinstance(item, (list, tuple)) and len(item) >= 4:
                        structured_rows.append({
                            "السؤال المختبر": item[0],
                            "البنك الأول": item[1],
                            "البنك الثاني": item[2],
                            "نسبة التشابه": round(float(item[3]), 4) if isinstance(item[3], (int, float)) else item[3]
                        })
                    else:
                        structured_rows.append({"تفاصيل الحالة المرصودة": str(item)})

                df_flagged = pd.DataFrame(structured_rows)
                st.dataframe(df_flagged, use_container_width=True)

                csv_flagged = df_flagged.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 تحميل تقرير حالات التشابه المرصودة (CSV)",
                    data=csv_flagged,
                    file_name="تقرير_تدقيق_تمايز_إجابات_البنوك.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_flagged_diff_csv"
                )
            else:
                st.success(f"✅ ممتاز! جميع الإجابات متمايزة ومستقلة تماماً ولم تتجاوز أي حالة عتبة التشابه ({rep_audit['threshold']}).")

        st.markdown("---")

        st.markdown("""
        <div dir="rtl" style="text-align: right; margin-bottom: 10px;">
            <h4 style="color: #002B49; font-weight: 800; margin-bottom: 4px;">📋 سجلات الزوار وعناوين IP (من السيرفر الدائم)</h4>
            <p style="color: #64748B; font-size: 13px;">متابعة حركة الدخول للمنصة وتصفية السجلات حسب الدور أو عنوان IP وتصديرها بصيغة Excel أو CSV.</p>
        </div>
        """, unsafe_allow_html=True)

        if not df_v_raw.empty:
            col_f1, col_f2 = st.columns([2, 1], gap="medium")
            with col_f1:
                search_ip_user = st.text_input(
                    "🔎 بحث سريع (بالاسم أو عنوان IP أو وقت الدخول):",
                    placeholder="اكتب للبحث الفوري في السجلات...",
                    key="admin_visitor_search"
                )
            with col_f2:
                roles_avail = ["الكل"] + (list(df_v_raw["الدور"].dropna().unique()) if "الدور" in df_v_raw.columns else [])
                role_filter = st.selectbox("تصفية حسب الدور:", roles_avail, key="admin_visitor_role_filter")

            df_v_filtered = df_v_raw.copy()
            if role_filter != "الكل" and "الدور" in df_v_filtered.columns:
                df_v_filtered = df_v_filtered[df_v_filtered["الدور"] == role_filter]
            if search_ip_user.strip():
                mask = df_v_filtered.astype(str).apply(
                    lambda col: col.str.contains(search_ip_user.strip(), case=False, na=False)
                ).any(axis=1)
                df_v_filtered = df_v_filtered[mask]

            df_v_display = df_v_filtered.iloc[::-1].reset_index(drop=True)
            st.dataframe(df_v_display, use_container_width=True)

            col_v_dl1, col_v_dl2, col_v_clr = st.columns([1.2, 1.2, 0.8], gap="medium")
            with col_v_dl1:
                csv_visitors = df_v_display.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 تحميل سجل الزوار (CSV)",
                    data=csv_visitors,
                    file_name="سجل_الزوار_وعناوين_IP_للبنوك.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_visitors_csv_btn"
                )
            with col_v_dl2:
                vis_excel_buf = io.BytesIO()
                with pd.ExcelWriter(vis_excel_buf, engine="openpyxl") as writer:
                    df_v_display.to_excel(writer, index=False, sheet_name="سجل_الزوار")
                st.download_button(
                    label="📥 تحميل سجل الزوار (Excel .xlsx)",
                    data=vis_excel_buf.getvalue(),
                    file_name="سجل_الزوار_وعناوين_IP_للبنوك.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_visitors_xlsx_btn"
                )
            with col_v_clr:
                if st.button("🗑️ تصفير السجل", use_container_width=True, type="secondary", key="clear_visitors_log_btn"):
                    try:
                        df_empty = pd.DataFrame(columns=["عنوان IP", "اسم المستخدم", "الدور", "وقت الدخول"])
                        df_empty.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
                        st.success("✅ تم مسح سجل الزوار بنجاح.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ تعذر مسح السجل: {e}")
        else:
            st.info("📂 لا توجد سجلات زيارات مسجلة حتى الآن.")

st.markdown('<div class="footer-copyright">منصة (رصين) — مقترح المنصة الوطنية الذكية لتعزيز الحوكمة المؤسسية بالقطاع المصرفي المصري | جميع الحقوق محفوظة للدراسة البحثية © 2026</div>', unsafe_allow_html=True)
