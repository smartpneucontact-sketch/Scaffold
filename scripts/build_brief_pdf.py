#!/usr/bin/env python3
"""Generate the Case Pilot product brief PDF.

Run:
    python3 scripts/build_brief_pdf.py
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

INK = (15, 22, 38)
INK_SOFT = (60, 70, 90)
MUTED = (130, 140, 158)
TEAL = (15, 118, 110)
TEAL_SOFT = (228, 246, 244)
BORDER = (215, 220, 230)
CODE_BG = (244, 246, 250)
CODE_INK = (40, 50, 75)
ROW_ALT = (250, 251, 253)

PAGE_W = 612
MARGIN = 56
CONTENT_W = PAGE_W - 2 * MARGIN

FONT_DIR = "/System/Library/Fonts/Supplemental"
FONT = "Body"
MONO = "Mono"


class Brief(FPDF):
    def footer(self):
        self.set_y(-32)
        self.set_font(FONT, size=8)
        self.set_text_color(*MUTED)
        self.set_draw_color(*BORDER)
        self.set_line_width(0.4)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.set_y(-26)
        self.cell(0, 10, "Case Pilot  ·  portfolio brief", align="L")
        self.set_y(-26)
        self.cell(0, 10, f"page {self.page_no()} of {{nb}}", align="R")


def _register_fonts(pdf: FPDF) -> None:
    pdf.add_font(FONT, "", f"{FONT_DIR}/Arial.ttf")
    pdf.add_font(FONT, "B", f"{FONT_DIR}/Arial Bold.ttf")
    pdf.add_font(FONT, "I", f"{FONT_DIR}/Arial Italic.ttf")
    pdf.add_font(FONT, "BI", f"{FONT_DIR}/Arial Bold Italic.ttf")
    pdf.add_font(MONO, "", f"{FONT_DIR}/Courier New.ttf")


def rule(pdf: FPDF, width: float = 72, height: float = 2.5) -> None:
    pdf.set_fill_color(*TEAL)
    pdf.rect(pdf.get_x(), pdf.get_y(), width, height, "F")
    pdf.ln(height + 14)


def h1(pdf: FPDF, text: str) -> None:
    pdf.set_font(FONT, "B", 30)
    pdf.set_text_color(*INK)
    pdf.cell(0, 36, text, new_x="LMARGIN", new_y="NEXT")


def h2(pdf: FPDF, text: str) -> None:
    pdf.ln(4)
    pdf.set_font(FONT, "B", 9)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 12, text.upper(), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def body(pdf: FPDF, text: str, size: int = 10.5) -> None:
    pdf.set_font(FONT, "", size)
    pdf.set_text_color(*INK_SOFT)
    pdf.multi_cell(0, 15, text, new_x="LMARGIN", new_y="NEXT")


def bullets(pdf: FPDF, items: list[str]) -> None:
    pdf.set_font(FONT, "", 10.5)
    pdf.set_text_color(*INK_SOFT)
    for item in items:
        x0 = pdf.get_x()
        pdf.set_x(x0 + 4)
        pdf.cell(10, 15, "•")
        pdf.set_x(x0 + 16)
        pdf.multi_cell(CONTENT_W - 16, 15, item, new_x="LMARGIN", new_y="NEXT")


def hero_link_card(pdf: FPDF, primary_url: str, primary_display: str,
                   sub_lines: list[tuple[str, str, str | None]]) -> None:
    y0 = pdf.get_y()
    height = 36 + 28 + 18 * len(sub_lines) + 14
    pdf.set_fill_color(*TEAL_SOFT)
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(1.0)
    pdf.rect(MARGIN, y0, CONTENT_W, height, "DF")
    pdf.set_fill_color(*TEAL)
    pdf.rect(MARGIN, y0, 4, height, "F")

    pdf.set_xy(MARGIN + 18, y0 + 12)
    pdf.set_font(FONT, "B", 9)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 12, "OPEN THE LIVE DEMO", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(MARGIN + 18)
    pdf.set_font(FONT, "B", 17)
    pdf.set_text_color(*INK)
    pdf.cell(CONTENT_W - 36, 26, primary_display, new_x="LMARGIN", new_y="NEXT", link=primary_url)
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(0.8)
    text_w = pdf.get_string_width(primary_display)
    pdf.line(MARGIN + 18, y0 + 46, MARGIN + 18 + text_w, y0 + 46)

    pdf.ln(4)
    for label, value, url in sub_lines:
        pdf.set_x(MARGIN + 18)
        pdf.set_font(FONT, "B", 10)
        pdf.set_text_color(*INK)
        pdf.cell(80, 16, label)
        pdf.set_font(FONT, "", 10)
        if url:
            pdf.set_text_color(*TEAL)
            pdf.cell(0, 16, value, new_x="LMARGIN", new_y="NEXT", link=url)
        else:
            pdf.set_text_color(*INK_SOFT)
            pdf.cell(0, 16, value, new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(y0 + height + 12)


def stack_table(pdf: FPDF, rows: list[tuple[str, str]]) -> None:
    col_w = CONTENT_W / 2
    row_h = 22
    pdf.set_fill_color(*INK)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(FONT, "B", 9)
    pdf.cell(col_w, row_h, "  THIS DEMO", border=0, fill=True)
    pdf.cell(col_w, row_h, "  ICOTEC PRODUCTION TARGET", new_x="LMARGIN", new_y="NEXT", border=0, fill=True)
    pdf.set_font(FONT, "", 10)
    for i, (left, right) in enumerate(rows):
        bg = ROW_ALT if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*INK)
        pdf.set_draw_color(*BORDER)
        pdf.cell(col_w, row_h, "  " + left, border="B", fill=True)
        pdf.set_text_color(*INK_SOFT)
        pdf.cell(col_w, row_h, "  " + right, new_x="LMARGIN", new_y="NEXT", border="B", fill=True)
    pdf.ln(6)


def trace_block(pdf: FPDF, title: str, lines: list[str]) -> None:
    y0 = pdf.get_y()
    line_h = 13
    pad_y = 12
    height = pad_y * 2 + line_h * len(lines) + 16
    pdf.set_fill_color(*CODE_BG)
    pdf.set_draw_color(*BORDER)
    pdf.set_line_width(0.4)
    pdf.rect(MARGIN, y0, CONTENT_W, height, "DF")
    pdf.set_xy(MARGIN + 14, y0 + 10)
    pdf.set_font(FONT, "B", 8)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 11, title.upper(), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(MONO, "", 8.8)
    pdf.set_text_color(*CODE_INK)
    for line in lines:
        pdf.set_x(MARGIN + 14)
        pdf.cell(0, line_h, line, new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(y0 + height + 10)


def build() -> Path:
    pdf = Brief("portrait", "pt", "letter")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(True, margin=66)
    pdf.alias_nb_pages()
    _register_fonts(pdf)
    pdf.add_page()

    # Page 1
    h1(pdf, "Case Pilot")
    pdf.set_font(FONT, "", 13)
    pdf.set_text_color(*INK_SOFT)
    pdf.cell(0, 18, "AI surgical case intake + BlackArmor implant configuration assistant.",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    rule(pdf)

    pdf.set_font(FONT, "B", 10)
    pdf.set_text_color(*INK)
    pdf.cell(0, 14, "Arsen Khanguieldyan", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "", 10)
    pdf.set_text_color(*INK_SOFT)
    pdf.cell(0, 14, "arsen.khanguieldyan@gmail.com", new_x="LMARGIN", new_y="NEXT",
             link="mailto:arsen.khanguieldyan@gmail.com")
    pdf.cell(0, 14, "Portfolio piece for icotec medical", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    hero_link_card(
        pdf,
        primary_url="https://case-pilot.up.railway.app",
        primary_display="case-pilot.up.railway.app",
        sub_lines=[
            ("Source code", "github.com/[your-handle]/case-pilot",
             "https://github.com/"),
            ("Model", "Anthropic Claude Sonnet 4.6  ·  ~$0.06 per case", None),
        ],
    )

    h2(pdf, "Summary")
    body(pdf,
         "Case Pilot is a working portfolio demo aligned to the icotec Digitalization & AI "
         "Professional role. A surgeon's free-text case description goes in, a structured case "
         "record comes out — cited indication checks, recommended BlackArmor implant "
         "configuration, imaging-benefit rating, MDR / FDA compliance flags. The agent loop and "
         "corpus contract map cleanly onto a Microsoft Power Platform + Azure AI production "
         "deployment.")

    h2(pdf, "The problem this solves")
    body(pdf,
         "Surgical case intake at a medical-device company today is mostly paper or free-text "
         "email. A clinical specialist reads the surgeon's description, manually checks indication "
         "alignment against the IFU, picks an implant configuration from the product catalog, "
         "flags any off-label use, and produces a structured record for the OR and the regulatory "
         "trail. High-frequency, citation-heavy, document-bound — the textbook 'paper-to-digital "
         "with AI' workflow icotec's JD explicitly names.")

    h2(pdf, "What it ships")
    bullets(pdf, [
        "Single AI agent that runs a tool-use loop on Claude Sonnet 4.6: retrieve corpus, check "
        "imaging benefit, classify case complexity, then draft the structured record.",
        "Synthetic but realistic icotec corpus: BlackArmor device specification, Indications for "
        "Use, surgical technique guide, prior cases, regulatory & quality summary.",
        "FastAPI service with visitor-notify (Resend HTTPS, dedup + bot filter), modern dark UI "
        "with semantic rendering of every output field, deployed to Railway.",
        "The same shape ports to a Power Platform deploy: Power Apps canvas UI, Power Automate "
        "flow → Azure Function custom connector, Azure AI Search over the SharePoint document "
        "library, Dataverse for implant inventory, App Insights for telemetry.",
    ])

    # Page 2
    pdf.add_page()

    h2(pdf, "How it maps to icotec's stack")
    body(pdf,
         "The agent loop and the corpus contract are the durable part. The surfaces around them "
         "change to fit icotec's Microsoft-first environment.")
    pdf.ln(4)
    stack_table(pdf, [
        ("Anthropic SDK + Claude Sonnet 4.6", "Azure OpenAI via Power Platform AI Builder"),
        ("BM25 over markdown corpus", "Azure AI Search / SharePoint Search"),
        ("FastAPI + Pydantic backend", "Power Automate flow + custom connector to Azure Function"),
        ("Single-page HTML UI", "Power Apps canvas app, embedded in Dynamics 365 / Teams"),
        ("JSONL traces on disk", "App Insights → Azure Data Explorer / Fabric"),
        ("Synthetic corpus", "icotec IFU + surgical guides in SharePoint + Dataverse"),
        ("Visitor-notify webhook", "Power Automate flow → Outlook / Teams alert"),
        ("GitHub Actions CI", "Same"),
    ])

    h2(pdf, "Sample agent reasoning (real run)")
    body(pdf,
         "Tool sequence for an oncology case: 55F with T8 metastatic breast carcinoma, planned "
         "post-op radiation. Every retrieval and classification is captured in the trace.")
    trace_block(pdf, "run_abcd1234ef56  ·  3 steps  ·  oncology case", [
        "step 0  retrieve(query=\"BlackArmor pedicle screw indications oncology\")",
        "        -> indications:blackarmor_pedicle_screws_ifu  (score 12.4)",
        "        -> case:case_001                                (score 8.9)",
        "",
        "step 0  retrieve(query=\"radiation planning imaging artifact titanium\",",
        "                  source_type=\"surgical_technique\")",
        "        -> surgical_technique:blackarmor_pedicle_screw_technique  (score 7.1)",
        "",
        "step 0  check_imaging_benefit(oncology=true, post_op_radiation=true,",
        "                                post_op_mri_planned=true)",
        "        -> benefit_band=\"high\", score=5",
        "",
        "step 1  classify_case_complexity(levels=5, revision=false,",
        "                                  osteoporosis=false, deformity=false)",
        "        -> complexity_band=\"medium\"",
        "",
        "step 2  final answer (cited): T6-T10 fusion, BlackArmor 6.0x45 mm screws,",
        "        CFR-PEEK rods, on-label, no specialist review required.",
    ])

    h2(pdf, "Why this fits the role")
    body(pdf,
         "icotec's JD describes someone who turns paper processes into digital ones, builds quick "
         "wins with low-code, applies AI to streamline workflows, and runs adoption. Case Pilot is "
         "exactly that artifact: a paper-to-structured-record workflow built in days, with a "
         "clear production path onto the Microsoft stack icotec already uses. The agent pattern "
         "transfers — the next workflow could be adverse-event triage, complaint handling, "
         "regulatory submission drafting, or sales-rep training-completion checks. Same loop, "
         "different corpus, weeks not quarters.")

    h2(pdf, "Honest gaps")
    bullets(pdf, [
        "Synthetic corpus, not real IFUs. Real deployment needs PDF OCR + table extraction.",
        "No Dataverse / Power Platform integration yet — this is the FastAPI prototype.",
        "No PHI or clinical-grade safety story. This is a planning aid, not regulated decision support.",
        "No live UDI lookup. Production would call Dataverse implant inventory in real time.",
    ])

    h2(pdf, "In one line")
    pdf.set_font(FONT, "I", 11.5)
    pdf.set_text_color(*INK)
    pdf.multi_cell(0, 16,
                   "Paper-to-digital, AI-powered, icotec-shaped — shippable to a real workflow in "
                   "a sprint on the Microsoft stack icotec already runs on.",
                   new_x="LMARGIN", new_y="NEXT")

    out = Path("Case_Pilot_Brief.pdf").resolve()
    pdf.output(str(out))
    return out


if __name__ == "__main__":
    print(f"Wrote: {build()}")
