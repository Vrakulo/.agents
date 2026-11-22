#!/usr/bin/env python3
"""Render the ZenAI corporate PDF template.

Cover style follows ZenAI 公司简介：full-bleed deep green hero,
white type, accent pills, soft ZEN watermark. Body pages stay light.

Dependency: reportlab, Pillow; optional pymupdf (SVG → PNG)
Example:
  python scripts/render_zenai_template.py --output examples/zenai-cover-template.pdf
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
import hashlib

ROOT = Path(__file__).resolve().parents[1]
LOGO_SVG = ROOT / "assets" / "zenai-logo.svg"
LOGO_PNG = ROOT / "assets" / "zenai-logo.png"
LOGO_WHITE = ROOT / "assets" / "zenai-logo-white.png"
LOGO_WATERMARK = ROOT / "assets" / "zenai-logo-watermark.png"

# Colors aligned with ZenAI 公司简介
HERO_GREEN = colors.HexColor("#26372f")
DEEP_GREEN = colors.HexColor("#1a2b24")
MID_GREEN = colors.HexColor("#4a6358")
SAGE = colors.HexColor("#6c846e")
LIGHT_GREEN = colors.HexColor("#a8c8bd")
ACCENT_PURPLE = colors.HexColor("#6c698e")
LIGHT_PURPLE_BLOCK = colors.HexColor("#8a89ac")
MID_PURPLE = colors.HexColor("#8f8bb0")
LIGHT_PURPLE = colors.HexColor("#dcd8eb")
DEEP_PURPLE = colors.HexColor("#2d2844")
# Logo accent stack (top → bottom), matching brand mark
BRAND_BLOCKS = (LIGHT_PURPLE_BLOCK, ACCENT_PURPLE, SAGE)
BG_WHITE = colors.HexColor("#fcfdfd")
SOFT_PURPLE = colors.HexColor("#f7f5fa")
SOFT_WHITE = colors.Color(1, 1, 1, alpha=0.72)
MUTED_WHITE = colors.Color(1, 1, 1, alpha=0.55)

LOGO_COVER_W = 16 * mm
LOGO_COVER_H = 8 * mm
LOGO_HEADER_W = 15 * mm
LOGO_HEADER_H = 7.5 * mm

DEFAULT_TAGS = ("技术文档", "正式发布", "版本受控", "企业交付")

AVATAR_PALETTE = (
    colors.HexColor("#6c698e"),
    colors.HexColor("#6c846e"),
    colors.HexColor("#8a89ac"),
    colors.HexColor("#4a6358"),
    colors.HexColor("#5a7d6e"),
    colors.HexColor("#7a739c"),
    colors.HexColor("#3d5248"),
    colors.HexColor("#9a8fb8"),
    colors.HexColor("#2d2844"),
    colors.HexColor("#a8c8bd"),
    colors.HexColor("#5c6b8a"),
    colors.HexColor("#8b7355"),
)


FONT_FILES: dict[str, Path] = {}
FONT_CMAPS: dict[str, set[int]] = {}
FONT_FALLBACK: dict[str, str] = {}


def _load_cmap(path: Path) -> set[int]:
    try:
        from fontTools.ttLib import TTFont as FTFont

        font = FTFont(str(path))
        cmap: set[int] = set()
        for table in font["cmap"].tables:
            cmap.update(table.cmap.keys())
        return cmap
    except Exception:
        return set()


def _register_ttfont(name: str, path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1024:
        return False
    try:
        pdfmetrics.registerFont(TTFont(name, str(path)))
        FONT_FILES[name] = path
        FONT_CMAPS[name] = _load_cmap(path)
        return True
    except Exception:
        return False


def register_fonts() -> tuple[str, str, str]:
    """Register Noto Serif SC + LGC fallback + Space Mono (OFL)."""
    font_dir = ROOT / "assets" / "fonts"

    serif = "STSong-Light"
    pdfmetrics.registerFont(UnicodeCIDFont(serif))
    serif_bold = serif

    if _register_ttfont("ZenSerif", font_dir / "NotoSerifSC-Regular.ttf"):
        serif = "ZenSerif"
        serif_bold = "ZenSerif"
        if _register_ttfont("ZenSerif-SemiBold", font_dir / "NotoSerifSC-SemiBold.ttf"):
            serif_bold = "ZenSerif-SemiBold"
        elif _register_ttfont("ZenSerif-Bold", font_dir / "NotoSerifSC-Bold.ttf"):
            serif_bold = "ZenSerif-Bold"
    else:
        for path, idx in (
            (Path("/System/Library/Fonts/Supplemental/Songti.ttc"), 0),
            (Path("/Library/Fonts/Arial Unicode.ttf"), None),
        ):
            try:
                if not path.exists():
                    continue
                if idx is None:
                    pdfmetrics.registerFont(TTFont("ZenSerif", str(path)))
                else:
                    pdfmetrics.registerFont(TTFont("ZenSerif", str(path), subfontIndex=idx))
                FONT_FILES["ZenSerif"] = path
                serif = serif_bold = "ZenSerif"
                break
            except Exception:
                continue

    # Latin / Greek / math companion for μ, Ω, ±, etc. missing from SC subset
    lgc = None
    lgc_bold = None
    if _register_ttfont("ZenSerifLGC", font_dir / "NotoSerifLGC-Regular.ttf"):
        lgc = "ZenSerifLGC"
    if _register_ttfont("ZenSerifLGC-SemiBold", font_dir / "NotoSerifLGC-SemiBold.ttf"):
        lgc_bold = "ZenSerifLGC-SemiBold"
    elif lgc:
        lgc_bold = lgc
    if lgc:
        FONT_FALLBACK[serif] = lgc
        if serif_bold != serif:
            FONT_FALLBACK[serif_bold] = lgc_bold or lgc
        else:
            FONT_FALLBACK[serif_bold] = lgc_bold or lgc

    mono = "Helvetica"
    if _register_ttfont("ZenMono", font_dir / "SpaceMono-Regular.ttf"):
        mono = "ZenMono"
        _register_ttfont("ZenMono-Bold", font_dir / "SpaceMono-Bold.ttf")

    return serif, serif_bold, mono


SERIF, SERIF_BOLD, MONO = register_fonts()


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _font_runs(text: str, primary: str) -> list[tuple[str, str]]:
    """Split text into (fontName, substring) runs using LGC fallback for missing glyphs."""
    if not text:
        return []
    fallback = FONT_FALLBACK.get(primary)
    primary_cmap = FONT_CMAPS.get(primary)
    fallback_cmap = FONT_CMAPS.get(fallback) if fallback else None
    if not fallback or not primary_cmap:
        return [(primary, text)]

    runs: list[tuple[str, str]] = []
    buf: list[str] = []
    current = primary

    def flush():
        nonlocal buf, current
        if buf:
            runs.append((current, "".join(buf)))
            buf = []

    for ch in text:
        cp = ord(ch)
        if cp in primary_cmap:
            want = primary
        elif fallback_cmap is not None and cp in fallback_cmap:
            want = fallback
        else:
            want = primary
        if want != current:
            flush()
            current = want
        buf.append(ch)
    flush()
    return runs


def with_font_fallback(text: str, primary: str) -> str:
    """ReportLab Paragraph markup with per-glyph font fallback (e.g. μ → LGC)."""
    runs = _font_runs(text, primary)
    if len(runs) == 1 and runs[0][0] == primary:
        return _xml_escape(text)
    parts: list[str] = []
    for font, chunk in runs:
        esc = _xml_escape(chunk)
        if font == primary:
            parts.append(esc)
        else:
            parts.append(f'<font name="{font}">{esc}</font>')
    return "".join(parts)


def para(text: str, style: ParagraphStyle) -> Paragraph:
    """Paragraph with automatic glyph fallback for the style's font."""
    return Paragraph(with_font_fallback(str(text), style.fontName), style)


def string_width_fb(text: str, font: str, size: float) -> float:
    return sum(
        pdfmetrics.stringWidth(chunk, run_font, size)
        for run_font, chunk in _font_runs(text, font)
    )


def draw_string_fb(c: Canvas, x: float, y: float, text: str, font: str, size: float):
    cursor = x
    for run_font, chunk in _font_runs(text, font):
        c.setFont(run_font, size)
        c.drawString(cursor, y, chunk)
        cursor += pdfmetrics.stringWidth(chunk, run_font, size)
    return cursor


def draw_centred_string_fb(
    c: Canvas, x: float, y: float, text: str, font: str, size: float
):
    total = string_width_fb(text, font, size)
    draw_string_fb(c, x - total / 2.0, y, text, font, size)

def ensure_logo_png() -> Path | None:
    """Prefer SVG source; rasterize to PNG for ReportLab Image/drawImage."""
    if LOGO_SVG.exists():
        needs = (not LOGO_PNG.exists()) or (LOGO_PNG.stat().st_mtime < LOGO_SVG.stat().st_mtime)
        if needs:
            try:
                import pymupdf

                doc = pymupdf.open(LOGO_SVG)
                pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=True)
                pix.save(str(LOGO_PNG))
                doc.close()
            except Exception:
                pass
        _ensure_white_logo()
    if LOGO_PNG.exists():
        return LOGO_PNG
    return None


def _ensure_white_logo() -> Path | None:
    """Tint black SVG raster to white and crop to ink for dark hero covers."""
    if not LOGO_PNG.exists():
        return None
    needs = (not LOGO_WHITE.exists()) or (LOGO_WHITE.stat().st_mtime < LOGO_PNG.stat().st_mtime)
    if needs:
        try:
            from PIL import Image

            src = Image.open(LOGO_PNG).convert("RGBA")
            px = src.load()
            w, h = src.size
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    if a == 0:
                        continue
                    lum = (r + g + b) / 3
                    if lum < 180:
                        px[x, y] = (255, 255, 255, a)
                    else:
                        px[x, y] = (255, 255, 255, int(a * 0.35))
            bbox = src.getbbox()
            if bbox:
                x0, y0, x1, y1 = bbox
                pad_w = int((x1 - x0) * 0.04)
                pad_h = int((y1 - y0) * 0.04)
                x0, y0 = max(0, x0 - pad_w), max(0, y0 - pad_h)
                x1, y1 = min(w, x1 + pad_w), min(h, y1 + pad_h)
                src = src.crop((x0, y0, x1, y1))
            src.save(LOGO_WHITE)
            # faint watermark variant
            wm = src.copy()
            wpx = wm.load()
            for y in range(wm.height):
                for x in range(wm.width):
                    r, g, b, a = wpx[x, y]
                    if a:
                        wpx[x, y] = (r, g, b, max(1, int(a * 0.08)))
            wm.save(LOGO_WATERMARK)
        except Exception:
            return None
    return LOGO_WHITE if LOGO_WHITE.exists() else None


def classify_color(level: str):
    return {
        "对外": SAGE,
        "内部": ACCENT_PURPLE,
        "机密": DEEP_PURPLE,
    }[level]


_CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")


def header_title_font(text: str) -> str:
    """Never draw CJK with mono/Helvetica — that becomes tofu boxes."""
    return SERIF if _CJK_RE.search(text) else MONO


def _wrap_cjk(text: str, font: str, size: float, max_width: float) -> list[str]:
    """Simple CJK/ASCII aware wrap for canvas text."""
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if string_width_fb(trial, font, size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines or [""]


_ink_mass_cache: dict[tuple[str, float, str], float] = {}


def _glyph_ink_mass_above_baseline(font: str, size: float, text: str) -> float:
    """Ink-mass center distance above the typographic baseline (PDF points)."""
    key = (font, round(size, 2), text)
    cached = _ink_mass_cache.get(key)
    if cached is not None:
        return cached

    path = FONT_FILES.get(font)
    cmap = FONT_CMAPS.get(font) or set()
    if path and text and any(ord(ch) not in cmap for ch in text):
        fb = FONT_FALLBACK.get(font)
        if fb and FONT_FILES.get(fb):
            path = FONT_FILES[fb]
    if not path or not text:
        try:
            face = pdfmetrics.getFont(font).face
            mid = (face.ascent + face.descent) * size / 2000.0
        except Exception:
            mid = size * 0.35
        _ink_mass_cache[key] = mid
        return mid

    from PIL import Image, ImageDraw, ImageFont

    scale = 8
    pil_size = max(8, int(round(size * scale)))
    pil_font = ImageFont.truetype(str(path), pil_size)
    ascent, descent = pil_font.getmetrics()  # descent >= 0 in Pillow
    pad = pil_size
    width = max(pil_size, int(pil_font.getlength(text)) + 2 * pad)
    height = ascent + descent + 2 * pad
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)
    baseline_y = pad + ascent
    draw.text((pad, baseline_y), text, font=pil_font, fill=255, anchor="ls")

    pixels = img.load()
    mass = 0.0
    moment = 0.0
    for y in range(height):
        row = 0
        for x in range(width):
            v = pixels[x, y]
            if v:
                row += v
        if row:
            mass += row
            moment += row * y
    if mass <= 0:
        mid = (ascent - descent) / 2.0 / scale
    else:
        # Image y grows downward; PDF offset above baseline is baseline_y - mass_y
        mid = (baseline_y - moment / mass) / scale
    _ink_mass_cache[key] = mid
    return mid


def _font_vcenter_baseline(
    box_y: float, box_h: float, font: str, size: float, text: str
) -> float:
    """Baseline Y so the glyph ink-mass center sits at the box midpoint."""
    return box_y + box_h / 2.0 - _glyph_ink_mass_above_baseline(font, size, text)


def _draw_pill(
    c: Canvas,
    x: float,
    y: float,
    text: str,
    *,
    font: str = SERIF,
    size: float = 9,
    h: float | None = None,
    fill=None,
    stroke=None,
    text_color=colors.white,
):
    """Draw a pill; `y` is the bottom of the pill. Returns advance width including gap."""
    pad_x = 3.4 * mm
    pill_h = h if h is not None else 7.5 * mm
    tw = pdfmetrics.stringWidth(text, font, size)
    w = tw + pad_x * 2
    radius = pill_h / 2
    if fill is not None:
        c.setFillColor(fill)
        c.roundRect(x, y, w, pill_h, radius, stroke=0, fill=1)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(0.8)
        c.setFillColor(colors.Color(1, 1, 1, alpha=0))
        c.roundRect(x, y, w, pill_h, radius, stroke=1, fill=0)
    c.setFillColor(text_color)
    draw_centred_string_fb(
        c,
        x + w / 2,
        _font_vcenter_baseline(y, pill_h, font, size, text),
        text,
        font,
        size,
    )
    return w + 2.2 * mm


class NumberedCanvas(Canvas):
    """Defer footer page numbers so we can render current/total after layout."""

    def __init__(self, *args, with_cover: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict] = []
        self._with_cover = with_cover
        self._zenai_page_marker = None

    def showPage(self):
        state = dict(self.__dict__)
        # Critical: copy page stream list; a shared _code leaks footers across pages
        state["_code"] = list(self._code)
        self._saved_page_states.append(state)
        self._zenai_page_marker = None
        self._startPage()

    def save(self):
        total_physical = len(self._saved_page_states)
        body_total = max(0, total_physical - (1 if self._with_cover else 0))
        for state in self._saved_page_states:
            self.__dict__.update(state)
            marker = state.get("_zenai_page_marker")
            self._draw_page_number(body_total, marker)
            Canvas.showPage(self)
        Canvas.save(self)

    def _draw_page_number(self, body_total: int, marker: dict | None):
        if not marker or body_total <= 0:
            return
        physical = marker["physical"]
        if self._with_cover and physical == 1:
            return
        current = physical - (1 if self._with_cover else 0)
        if current < 1:
            return
        self.saveState()
        self.setFont(MONO, 7)
        self.setFillColor(MID_GREEN)
        label = f"{current}/{body_total}"
        y = _font_vcenter_baseline(
            marker["band_y"], marker["band_h"], MONO, 7, label
        )
        self.drawRightString(marker["x"], y, label)
        self.restoreState()


def avatar_initial(name: str) -> str:
    """Pick a stable display glyph from a speaker name."""
    name = (name or "").strip()
    if not name:
        return "?"
    for ch in reversed(name):
        if "\u4e00" <= ch <= "\u9fff":
            return ch
    parts = [p for p in re.split(r"[\s._\-]+", name) if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[0].upper()


def avatar_color(name: str):
    """Stable brand color from name; prefer spread across the palette."""
    raw = (name or "?").encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    # mix several bytes so short CJK names don't clump
    idx = int.from_bytes(digest[:4], "big") ^ int.from_bytes(digest[4:8], "big")
    return AVATAR_PALETTE[idx % len(AVATAR_PALETTE)]


class SpeakerTurn(Flowable):
    """Meeting-minutes turn: name avatar + speaker name + spoken content."""

    def __init__(
        self,
        name: str,
        content: str,
        *,
        width: float | None = None,
        color=None,
    ):
        super().__init__()
        self.name = name.strip()
        self.content = content.strip()
        self._width = width
        self._color = color or avatar_color(self.name)
        self.avatar = 6.5 * mm
        self.gap = 2.4 * mm
        self._initial_size = 8.5
        self._name_style = ParagraphStyle(
            "SpeakerName",
            fontName=SERIF_BOLD,
            fontSize=9,
            leading=12,
            textColor=DEEP_GREEN,
        )
        self._body_style = ParagraphStyle(
            "SpeakerBody",
            fontName=SERIF,
            fontSize=9,
            leading=14.5,
            textColor=MID_GREEN,
            wordWrap="CJK",
        )
        self._name_p = para(self.name, self._name_style)
        body_markup = "<br/>".join(
            with_font_fallback(line, self._body_style.fontName)
            for line in self.content.split("\n")
        )
        self._body_p = Paragraph(body_markup, self._body_style)
        self._h = 0

    def wrap(self, availWidth, availHeight):
        self.width = self._width or availWidth
        text_w = max(20, self.width - self.avatar - self.gap)
        nw, nh = self._name_p.wrap(text_w, availHeight)
        bw, bh = self._body_p.wrap(text_w, max(0, availHeight - nh - 1.2 * mm))
        self._text_w = text_w
        self._name_h = nh
        self._body_h = bh
        self._h = max(self.avatar, nh + 1.0 * mm + bh) + 1.8 * mm
        return self.width, self._h

    def draw(self):
        c = self.canv
        # Avatar sits at the top of the turn
        cy = self._h - self.avatar / 2 - 0.2 * mm
        cx = self.avatar / 2
        c.setFillColor(self._color)
        c.circle(cx, cy, self.avatar / 2, fill=1, stroke=0)
        initial = avatar_initial(self.name)
        c.setFillColor(colors.white)
        c.setFont(SERIF_BOLD, self._initial_size)
        c.drawCentredString(
            cx,
            _font_vcenter_baseline(
                cy - self.avatar / 2,
                self.avatar,
                SERIF_BOLD,
                self._initial_size,
                initial,
            ),
            initial,
        )

        text_x = self.avatar + self.gap
        # Name row aligned with avatar vertical center
        name_y = self._h - self._name_h - (self.avatar - self._name_h) / 2
        self._name_p.drawOn(c, text_x, name_y)
        body_y = name_y - 1.0 * mm - self._body_h
        self._body_p.drawOn(c, text_x, body_y)


def assign_speaker_colors(names: list[str]) -> dict[str, colors.Color]:
    """Unique-as-possible colors within one meeting; same name stays stable."""
    mapping: dict[str, colors.Color] = {}
    used: set[int] = set()
    for name in names:
        if name in mapping:
            continue
        preferred = AVATAR_PALETTE.index(avatar_color(name)) if avatar_color(name) in AVATAR_PALETTE else 0
        # walk palette from preferred index until unused
        idx = preferred
        for _ in range(len(AVATAR_PALETTE)):
            if idx not in used:
                break
            idx = (idx + 1) % len(AVATAR_PALETTE)
        used.add(idx)
        mapping[name] = AVATAR_PALETTE[idx]
    return mapping


class ZenAIDocTemplate(BaseDocTemplate):
    def __init__(
        self,
        filename: str,
        *,
        title: str,
        classification: str,
        subtitle: str = "",
        version: str = "V1.0",
        date_str: str = "",
        department: str = "",
        tags: tuple[str, ...] = DEFAULT_TAGS,
        with_cover: bool = True,
        **kwargs,
    ):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=22 * mm,
            rightMargin=22 * mm,
            topMargin=14.5 * mm,
            bottomMargin=13 * mm,
            title=title,
            author="ZenAI Enterprise",
            subject=f"{classification}文档",
            **kwargs,
        )
        self.doc_title = title
        self.classification = classification
        self.subtitle = subtitle
        self.version = version
        self.date_str = date_str
        self.department = department
        self.tags = tags
        self.with_cover = with_cover
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="content",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        cover_frame = Frame(0, 0, A4[0], A4[1], id="cover", showBoundary=0)
        templates = []
        if with_cover:
            templates.append(PageTemplate(id="cover", frames=[cover_frame], onPage=self._cover_page))
        templates.append(PageTemplate(id="body", frames=[frame], onPage=self._body_page))
        self.addPageTemplates(templates)

    def afterPage(self):
        if self.with_cover and self.page == 1:
            self.handle_nextPageTemplate("body")

    def _cover_page(self, canvas: Canvas, doc):
        """Two-tone cover like 公司简介: deep-green hero on top, white below."""
        canvas.saveState()
        w, h = A4
        left = 22 * mm
        right = w - 22 * mm
        # Green occupies upper ~54% (split measured from page bottom)
        split_y = h * 0.46

        # --- bands ---
        canvas.setFillColor(BG_WHITE)
        canvas.rect(0, 0, w, split_y, fill=1, stroke=0)
        canvas.setFillColor(HERO_GREEN)
        canvas.rect(0, split_y, w, h - split_y, fill=1, stroke=0)

        # Watermark: mostly in green, bottom clipped at the split for a cut-off look
        _ensure_white_logo()
        wm = LOGO_WATERMARK if LOGO_WATERMARK.exists() else (LOGO_WHITE if LOGO_WHITE.exists() else None)
        if wm:
            from PIL import Image as _Image
            _iw, _ih = _Image.open(wm).size
            wm_h = 56 * mm
            wm_w = wm_h * (_iw / _ih)
            # Keep most of ZEN on-page; only a thin slice may exit the right edge
            wm_x = w - wm_w + 8 * mm
            canvas.saveState()
            clip = canvas.beginPath()
            clip.rect(0, split_y, w, h - split_y)
            canvas.clipPath(clip, stroke=0, fill=0)
            canvas.drawImage(
                str(wm),
                wm_x,
                split_y - 14 * mm,  # hangs past the split, then clipped
                width=wm_w,
                height=wm_h,
                mask="auto",
                preserveAspectRatio=False,
                anchor="sw",
            )
            canvas.restoreState()

        # Top-left: 3 brand blocks + logo + INTERNATIONAL CORP
        # Stack height spans ZEN + corp line (per brand mark)
        sq = 2.8 * mm
        gap = 1.0 * mm
        n_blocks = 3
        stack_h = n_blocks * sq + (n_blocks - 1) * gap
        brand_top = h - 18 * mm
        brand_bottom = brand_top - stack_h
        for i, block_color in enumerate(BRAND_BLOCKS):
            y_sq = brand_top - (i + 1) * sq - i * gap
            canvas.setFillColor(block_color)
            canvas.rect(left, y_sq, sq, sq, fill=1, stroke=0)

        # ZEN logo aligns with top of stack; height ≈ top two blocks
        logo_h = 2 * sq + gap
        logo_x = left + sq + 2.8 * mm
        logo_y = brand_top - logo_h
        if LOGO_WHITE.exists():
            from PIL import Image as _Image

            _lw, _lh = _Image.open(LOGO_WHITE).size
            logo_w = logo_h * (_lw / _lh)
            canvas.drawImage(
                str(LOGO_WHITE),
                logo_x,
                logo_y,
                width=logo_w,
                height=logo_h,
                mask="auto",
                preserveAspectRatio=False,
                anchor="sw",
            )
        # Corp line sits beside the bottom (sage) block
        canvas.setFillColor(MUTED_WHITE)
        canvas.setFont(MONO, 5.5)
        corp = "INTERNATIONAL CORP"
        canvas.drawString(
            logo_x,
            _font_vcenter_baseline(brand_bottom, sq, MONO, 5.5, corp),
            corp,
        )

        # Eyebrow + title + subtitle (stay inside green)
        ey_y = h - 68 * mm
        canvas.setFillColor(colors.white)
        canvas.circle(left + 1.2 * mm, ey_y + 1.5 * mm, 1.2 * mm, fill=1, stroke=0)
        canvas.setFont(SERIF, 9)
        canvas.setFillColor(SOFT_WHITE)
        canvas.drawString(left + 6 * mm, ey_y, "企业级正式文档")

        title_size = 24
        title_leading = 34
        title_font = SERIF_BOLD
        max_tw = right - left - 8 * mm
        title_lines = _wrap_cjk(self.doc_title, title_font, title_size, max_tw)
        y = h - 88 * mm
        canvas.setFillColor(colors.white)
        for line in title_lines[:3]:
            draw_string_fb(canvas, left, y, line, title_font, title_size)
            y -= title_leading

        y -= 2 * mm
        canvas.setFillColor(SOFT_WHITE)
        for line in _wrap_cjk(self.subtitle, SERIF, 10.5, max_tw)[:3]:
            draw_string_fb(canvas, left, y, line, SERIF, 10.5)
            y -= 16

        # Pills near bottom of green band
        y = max(y - 8 * mm, split_y + 14 * mm)
        # Classification chip + topic tags (shared height, ink-mass v-center)
        pill_h = 7.5 * mm
        pill_size = 9
        x = left
        x += _draw_pill(
            canvas,
            x,
            y,
            self.classification,
            size=pill_size,
            h=pill_h,
            fill=classify_color(self.classification),
            text_color=colors.white,
        )
        for tag in self.tags:
            x += _draw_pill(
                canvas,
                x,
                y,
                tag,
                size=pill_size,
                h=pill_h,
                stroke=colors.Color(1, 1, 1, alpha=0.85),
                text_color=colors.white,
            )
            if x > right - 18 * mm:
                break

        # --- white lower band ---
        # --- white lower band: meta rows only (no section title / rule) ---
        info_rows = [
            ("编制部门", self.department),
            ("文档版本", self.version),
            ("发布日期", self.date_str),
            ("密级标注", self.classification),
        ]
        row_y = split_y - 22 * mm
        lab_w = 28 * mm
        for lab, val in info_rows:
            canvas.setFillColor(ACCENT_PURPLE)
            canvas.setFont(SERIF, 9)
            canvas.drawString(left, row_y, lab)
            canvas.setFillColor(DEEP_GREEN)
            canvas.setFont(SERIF, 10)
            canvas.drawString(left + lab_w, row_y, val)
            row_y -= 9 * mm

        # Bottom brand on white
        canvas.setFillColor(MID_GREEN)
        canvas.setFont(SERIF, 8)
        canvas.drawString(left, 16 * mm, "为您的企业级系统注入 AI 动力")
        canvas.setFont(SERIF, 8)
        canvas.setFillColor(SAGE)
        canvas.drawRightString(right, 16 * mm, "www.zenaicorp.com")

        canvas.restoreState()

    def _body_page(self, canvas: Canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(BG_WHITE)
        canvas.rect(0, 0, w, h, fill=1, stroke=0)

        logo = ensure_logo_png()
        if logo:
            canvas.drawImage(
                str(logo),
                22 * mm,
                h - 11.5 * mm,
                width=LOGO_HEADER_W,
                height=LOGO_HEADER_H,
                mask="auto",
                preserveAspectRatio=True,
                anchor="sw",
            )
        title_font = header_title_font(self.doc_title)
        canvas.setFont(title_font, 7)
        canvas.setFillColor(MID_GREEN)
        canvas.drawRightString(w - 22 * mm, h - 8.2 * mm, self.doc_title[:46])
        canvas.setStrokeColor(LIGHT_PURPLE)
        canvas.setLineWidth(0.5)
        canvas.line(22 * mm, h - 12.5 * mm, w - 22 * mm, h - 12.5 * mm)

        canvas.line(22 * mm, 10 * mm, w - 22 * mm, 10 * mm)
        footer_band_y = 4 * mm
        footer_band_h = 5.5 * mm
        canvas.setFont(SERIF, 7)
        canvas.setFillColor(classify_color(self.classification))
        canvas.drawString(
            22 * mm,
            _font_vcenter_baseline(
                footer_band_y, footer_band_h, SERIF, 7, self.classification
            ),
            self.classification,
        )
        # Page "current/total" is drawn later by NumberedCanvas (needs final page count)
        canvas._zenai_page_marker = {
            "physical": canvas.getPageNumber(),
            "x": w - 22 * mm,
            "band_y": footer_band_y,
            "band_h": footer_band_h,
        }
        canvas.restoreState()


def styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName=SERIF_BOLD,
            fontSize=20,
            leading=28,
            textColor=DEEP_GREEN,
            wordWrap="CJK",
            spaceAfter=6 * mm,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName=SERIF_BOLD,
            fontSize=13.5,
            leading=21,
            textColor=ACCENT_PURPLE,
            wordWrap="CJK",
            spaceBefore=5 * mm,
            spaceAfter=3 * mm,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName=SERIF_BOLD,
            fontSize=11,
            leading=17,
            textColor=DEEP_GREEN,
            wordWrap="CJK",
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=SERIF,
            fontSize=10.5,
            leading=19,
            textColor=MID_GREEN,
            wordWrap="CJK",
            spaceAfter=3.2 * mm,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName=SERIF,
            fontSize=10.5,
            leading=18,
            textColor=MID_GREEN,
            wordWrap="CJK",
            leftIndent=5 * mm,
            firstLineIndent=-3.5 * mm,
            spaceAfter=1.2 * mm,
        ),
        "meta_label": ParagraphStyle(
            "MeetingMetaLabel",
            parent=base["Normal"],
            fontName=SERIF,
            fontSize=9,
            leading=13,
            textColor=ACCENT_PURPLE,
        ),
        "meta_value": ParagraphStyle(
            "MeetingMetaValue",
            parent=base["Normal"],
            fontName=SERIF,
            fontSize=10,
            leading=14,
            textColor=DEEP_GREEN,
            wordWrap="CJK",
        ),
        "block_title": ParagraphStyle(
            "BlockTitle",
            parent=base["Normal"],
            fontName=SERIF_BOLD,
            fontSize=10,
            leading=14,
            wordWrap="CJK",
            spaceAfter=1 * mm,
        ),
        "block_sub": ParagraphStyle(
            "BlockSub",
            parent=base["Normal"],
            fontName=SERIF_BOLD,
            fontSize=9,
            leading=13,
            textColor=DEEP_GREEN,
            wordWrap="CJK",
            spaceAfter=1.5 * mm,
        ),
        "block_bullet": ParagraphStyle(
            "BlockBullet",
            parent=base["Normal"],
            fontName=SERIF,
            fontSize=8.5,
            leading=13,
            textColor=MID_GREEN,
            wordWrap="CJK",
            leftIndent=3.2 * mm,
            firstLineIndent=-3.2 * mm,
            spaceAfter=0.8 * mm,
        ),
        "conclude_label": ParagraphStyle(
            "ConcludeLabel",
            parent=base["Normal"],
            fontName=SERIF_BOLD,
            fontSize=10,
            leading=14,
            textColor=DEEP_GREEN,
            wordWrap="CJK",
            spaceAfter=1.5 * mm,
        ),
    }


def cover_story():
    # Cover art is drawn in _cover_page; story only advances to body.
    return [NextPageTemplate("body"), PageBreak()]


def _meeting_meta_table(st, rows: list[tuple[str, str]]):
    data = [
        [para(label, st["meta_label"]), para(value, st["meta_value"])]
        for label, value in rows
        if value
    ]
    table = Table(data, colWidths=[28 * mm, 124 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), SOFT_PURPLE),
                ("BOX", (0, 0), (-1, -1), 0.5, LIGHT_PURPLE),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LIGHT_PURPLE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


# Soft fills matched to brand accents (no Feishu rainbow / icons)
_BLOCK_THEME = (
    (SOFT_PURPLE, ACCENT_PURPLE),
    (colors.HexColor("#f3f6f4"), SAGE),
    (colors.HexColor("#f5f4f9"), LIGHT_PURPLE_BLOCK),
)


def _normalize_summary_block(block) -> tuple[str, str, list[str]]:
    """Accept (title, bullets), (title, subtitle, bullets), or dict."""
    if isinstance(block, dict):
        return (
            str(block.get("title") or ""),
            str(block.get("subtitle") or ""),
            list(block.get("bullets") or []),
        )
    if len(block) == 2:
        title, bullets = block
        return str(title or ""), "", list(bullets or [])
    title, subtitle, bullets = block
    return str(title or ""), str(subtitle or ""), list(bullets or [])


def _summary_block_flowable(st, block, accent, fill, width: float) -> Table:
    title, subtitle, bullets = _normalize_summary_block(block)
    title_style = ParagraphStyle(
        "BlockTitleAccent",
        parent=st["block_title"],
        textColor=accent,
    )
    parts: list = []
    if title:
        parts.append(para(title, title_style))
    if subtitle:
        parts.append(para(subtitle, st["block_sub"]))
    for bullet in bullets:
        parts.append(para(f"• {bullet}", st["block_bullet"]))
    inner = Table([[parts]], colWidths=[width])
    inner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), fill),
                ("BOX", (0, 0), (-1, -1), 0.4, LIGHT_PURPLE),
                ("LINEBEFORE", (0, 0), (0, -1), 2.2, accent),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return inner


def _summary_block_grid(st, blocks: list, *, cols: int) -> Table:
    gap = 3 * mm
    usable = 152 * mm
    col_w = (usable - gap * (cols - 1)) / cols
    cells = []
    for i, block in enumerate(blocks):
        fill, accent = _BLOCK_THEME[i % len(_BLOCK_THEME)]
        cells.append(_summary_block_flowable(st, block, accent, fill, col_w))
    while len(cells) % cols:
        cells.append("")
    rows = [cells[i : i + cols] for i in range(0, len(cells), cols)]
    # Interleave gap columns for visual gutters
    if cols == 1:
        table = Table(rows, colWidths=[col_w])
    else:
        spaced_rows = []
        for row in rows:
            spaced = []
            for j, cell in enumerate(row):
                if j:
                    spaced.append("")
                spaced.append(cell)
            spaced_rows.append(spaced)
        widths = []
        for j in range(cols):
            if j:
                widths.append(gap)
            widths.append(col_w)
        table = Table(spaced_rows, colWidths=widths)
        rows = spaced_rows
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )
    return table


def _conclusions_banner(st, items: list[str]) -> Table:
    parts = [para("核心结论", st["conclude_label"])]
    for item in items:
        parts.append(para(f"• {item}", st["block_bullet"]))
    banner = Table([[parts]], colWidths=[152 * mm])
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f6f4")),
                ("BOX", (0, 0), (-1, -1), 0.4, LIGHT_PURPLE),
                ("LINEBEFORE", (0, 0), (0, -1), 3, SAGE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return banner


def meeting_story(args, st, meeting: dict):
    """Meeting minutes: meta → purpose → block summary → decisions → turns."""
    attendees = meeting.get("attendees") or sorted(
        {name for name, _ in meeting.get("turns", [])}
    )
    if isinstance(attendees, (list, tuple)):
        attendees_text = "、".join(attendees)
    else:
        attendees_text = str(attendees)

    meta_rows = [
        ("会议主题", args.title),
        ("会议时间", meeting.get("time") or args.date),
        ("会议地点", meeting.get("location", "")),
        ("组织部门", args.department),
        ("主持人", meeting.get("host", "")),
        ("记录人", meeting.get("recorder", "")),
        ("参会人员", attendees_text),
        ("缺席人员", meeting.get("absentees", "")),
    ]

    story: list = [
        para(args.title, st["h1"]),
        para(args.subtitle or "会议纪要", st["body"]),
        Spacer(1, 2 * mm),
        _meeting_meta_table(st, meta_rows),
    ]

    purpose = meeting.get("purpose") or ""
    if purpose:
        story.append(para("会议目的", st["h2"]))
        story.append(para(purpose, st["body"]))

    conclusions = meeting.get("conclusions")
    summary = meeting.get("summary") or []
    followups = meeting.get("followups") or []
    if conclusions or summary or followups:
        story.append(para("纪要摘要", st["h2"]))
        if conclusions:
            story.append(_conclusions_banner(st, list(conclusions)))
            story.append(Spacer(1, 3 * mm))
        if summary:
            cols = 3 if len(summary) >= 3 else max(1, len(summary))
            story.append(_summary_block_grid(st, list(summary), cols=cols))
        if followups:
            story.append(para("后续推进", st["h3"]))
            cols = 2 if len(followups) >= 2 else 1
            story.append(_summary_block_grid(st, list(followups), cols=cols))

    decisions = meeting.get("decisions") or []
    if decisions:
        story.append(para("决议事项", st["h2"]))
        for item in decisions:
            story.append(para(f"• {item}", st["bullet"]))

    turns = meeting.get("turns") or []
    if turns:
        story.append(para("发言记录", st["h2"]))
        colors_map = assign_speaker_colors([name for name, _ in turns])
        for name, content in turns:
            story.append(SpeakerTurn(name, content, color=colors_map[name]))
            story.append(Spacer(1, 1.2 * mm))

    return story


SAMPLE_MEETING = {
    "time": "2026-09-08（周二）14:00–15:20（GMT+08）",
    "location": "线上会议",
    "host": "陈思远",
    "recorder": "林晓",
    "attendees": ["陈思远", "林晓", "Alex Chen", "王敏", "赵倩"],
    "absentees": "周宁（出差）",
    "purpose": (
        "对齐核心系统改造本周进度与风险，确认灰度扩容节奏、回滚演练安排，"
        "以及合规侧对演练日志的归档要求，形成可执行的决议与跟进安排。"
    ),
    "conclusions": [
        "灰度扩至 50% 以周四回滚演练通过为前提，否则维持 30%。",
        "周四下午固定组织一键回切演练，覆盖登录链路与关键依赖。",
        "演练与扩容日志按项目编号归档，保留 180 天；关键路径采样间隔约 10 μs。",
    ],
    "summary": [
        (
            "改造进度",
            "登录链路与数据平台",
            [
                "灰度已至 30%，近七日错误率稳定在 0.2% 以下。",
                "批处理窗口今晚延长 40 分钟，告警阈值已调整。",
            ],
        ),
        (
            "回滚预案",
            "客户关注与演练安排",
            [
                "客户重点关注一键回切能力与值守协同。",
                "演练后输出耗时与失败路径记录。",
            ],
        ),
        (
            "合规约束",
            "日志与扩容门禁",
            [
                "演练日志保留 180 天，目录按项目编号落盘。",
                "扩容门禁：演练未通过则不提升灰度。",
            ],
        ),
    ],
    "followups": [
        (
            "验证与演练",
            [
                "周四下午执行回滚演练，林晓牵头、值守配合。",
                "演练报告同步客户侧与合规侧。",
            ],
        ),
        (
            "扩容与归档",
            [
                "演练通过后由陈思远推进灰度至 50%。",
                "王敏确认归档路径并抽查保留策略。",
            ],
        ),
    ],
    "decisions": [
        "本周登录链路灰度目标调整为 50%，前提是周四回滚演练通过。",
        "回滚演练固定于周四下午执行，由林晓牵头、值守同学配合。",
        "演练与扩容相关日志统一按项目编号归档，保留周期 180 天。",
    ],
    "turns": [
        ("陈思远", "先同步本周进度：登录链路灰度到 30%，错误率稳定在 0.2% 以下。"),
        ("林晓", "客户最关心回滚预案。建议周四下午做一键回切演练，并通知值守。"),
        ("Alex Chen", "同意。数据平台批处理窗口今晚会延长 40 分钟，告警阈值已调过。"),
        ("陈思远", "那把「灰度扩到 50%」和「回滚演练」写成待办，分别由我和林晓跟进。"),
        ("王敏", "合规补充：演练日志保留 180 天，归档目录按项目编号落盘。"),
    ],
}


def body_story(st):
    rows = [
        ["版本", "日期", "变更说明", "编制 / 审核"],
        ["V1.0", date.today().isoformat(), "首次发布", "ZenAI"],
        ["V1.1", "YYYY-MM-DD", "示例：补充修订内容", "—"],
    ]
    rev = Table(rows, colWidths=[22 * mm, 32 * mm, 66 * mm, 36 * mm], repeatRows=1)
    rev.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HERO_GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), SERIF),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.4, LIGHT_PURPLE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BG_WHITE, SOFT_PURPLE]),
                # Slightly larger top pad optically centers CJK in ReportLab cells
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    callout = Table(
        [[para("关键结论", st["h2"]), para("在此填写本节最重要的结论、决策或验收结果。", st["body"])]],
        colWidths=[34 * mm, 118 * mm],
    )
    callout.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT_PURPLE),
                ("BOX", (0, 0), (-1, -1), 0.8, LIGHT_PURPLE),
                ("LINEBEFORE", (0, 0), (0, -1), 3, SAGE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        para("文档控制", st["h1"]),
        para("本页用于维护文档的版本、变更、编制与审核信息。正式发布前请删除示例行。", st["body"]),
        Spacer(1, 3 * mm),
        rev,
        Spacer(1, 10 * mm),
        para("1. 文档概述", st["h1"]),
        para(
            "在此概述文档背景、目标、范围以及适用对象。技术、设计、需求、方案、投标与验收类文档默认使用本封面；会议纪要、简短通知等轻量文档默认不使用封面。",
            st["body"],
        ),
        para("1.1 背景与目标", st["h2"]),
        para(
            "用清晰、可验证的语言描述问题背景和期望成果。避免大段装饰性文字；优先使用结论、数据、约束和责任边界。",
            st["body"],
        ),
        callout,
        para("1.2 适用范围", st["h2"]),
        para(
            "列出包含与不包含的范围、依赖关系、关键假设以及风险。必要时插入架构图、流程图或高对比度黑白实景摄影，并使用深绿或灰紫叠色。",
            st["body"],
        ),
        PageBreak(),
        para("2. 正文版式示例", st["h1"]),
        para(
            "页面采用 A4 纵向版式。页眉左侧为 ZenAI Logo，右侧为文档标题；页脚左侧为密级，右侧为正文页码。封面采用公司简介同款深绿全幅英雄区，不计入正文页码。",
            st["body"],
        ),
        para("2.1 排版规范", st["h2"]),
        para(
            "中文标题与正文使用 Noto Serif SC（OFL，可商用）；英文标签、版本号与页码使用 Space Mono（OFL）。Logo 源文件为 SVG；封面使用白色 Logo，正文页眉使用深色 Logo。",
            st["body"],
        ),
        para("2.2 色彩与图像", st["h2"]),
        para(
            "封面主色为深绿 #26372f；强调色为灰紫 #6f6a92 与鼠尾草绿 #6e8670。正文背景 #fcfdfd。避免高饱和、多色混用和通用图库式笑脸照片。",
            st["body"],
        ),
        para("2.3 交付检查", st["h2"]),
        para(
            "导出后应检查：Logo 清晰、密级一致、日期和版本正确、页码连续、无文字溢出、无缺字方框、英文字距正常、无孤行、图片分辨率足够、文档元数据正确。",
            st["body"],
        ),
    ]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--mode",
        choices=["doc", "meeting"],
        default="doc",
        help="doc: formal document with cover; meeting: minutes/record without cover",
    )
    p.add_argument("--output", default="")
    p.add_argument("--title", default="")
    p.add_argument("--subtitle", default="")
    p.add_argument("--version", default="V1.0")
    p.add_argument("--classification", choices=["对外", "内部", "机密"], default="内部")
    p.add_argument("--date", default=date.today().isoformat())
    p.add_argument("--department", default="ZenAI Enterprise")
    p.add_argument(
        "--tags",
        default=",".join(DEFAULT_TAGS),
        help="Comma-separated cover tags, e.g. 技术文档,正式发布",
    )
    p.add_argument(
        "--meeting-json",
        default="",
        help="Path to meeting content JSON (mode=meeting). Falls back to built-in sample.",
    )
    return p.parse_args()


def load_meeting(path: str) -> dict:
    """Load meeting dict from JSON; tuples in summary/followups accepted as lists."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("meeting JSON must be an object")
    return data


def main():
    args = parse_args()
    mode = args.mode
    if not args.title:
        args.title = "周度项目同步会纪要" if mode == "meeting" else "ZenAI 公司通用文档模板"
    if not args.subtitle:
        args.subtitle = (
            "核心系统改造 · 灰度与回滚" if mode == "meeting" else "适用于技术、设计、需求、方案、投标与验收类正式文档"
        )
    if not args.output:
        args.output = str(
            ROOT
            / "examples"
            / ("zenai-meeting-minutes.pdf" if mode == "meeting" else "zenai-cover-template.pdf")
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    ensure_logo_png()
    tags = tuple(t.strip() for t in args.tags.split(",") if t.strip()) or DEFAULT_TAGS
    st = styles()
    with_cover = mode == "doc"
    doc = ZenAIDocTemplate(
        str(output),
        title=args.title,
        classification=args.classification,
        subtitle=args.subtitle,
        version=args.version,
        date_str=args.date,
        department=args.department,
        tags=tags,
        with_cover=with_cover,
    )
    if mode == "meeting":
        meeting = load_meeting(args.meeting_json) if args.meeting_json else SAMPLE_MEETING
        story = meeting_story(args, st, meeting)
    else:
        story = cover_story() + body_story(st)

    def _canvas_maker(*cargs, **ckw):
        return NumberedCanvas(*cargs, with_cover=with_cover, **ckw)

    doc.build(story, canvasmaker=_canvas_maker)
    print(output)


if __name__ == "__main__":
    main()
