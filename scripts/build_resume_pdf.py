#!/usr/bin/env python3
"""Generate Arsen's resume PDF tailored for icotec medical.

Run:
    python3 scripts/build_resume_pdf.py

Output:
    Arsen_Khanguieldyan_Resume_icotec.pdf
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

# Palette — teal accent to match Case Pilot brand
INK = (15, 22, 38)
INK_SOFT = (60, 70, 90)
MUTED = (130, 140, 158)
RULE = (215, 220, 230)
ACCENT = (15, 118, 110)  # teal-700

PAGE_W = 612
PAGE_H = 792
MARGIN_X = 48
MARGIN_TOP = 42
MARGIN_BOTTOM = 42
CONTENT_W = PAGE_W - 2 * MARGIN_X

FONT_DIR = "/System/Library/Fonts/Supplemental"
FONT = "Body"


def _register_fonts(pdf: FPDF) -> None:
    pdf.add_font(FONT, "", f"{FONT_DIR}/Arial.ttf")
    pdf.add_font(FONT, "B", f"{FONT_DIR}/Arial Bold.ttf")
    pdf.add_font(FONT, "I", f"{FONT_DIR}/Arial Italic.ttf")
    pdf.add_font(FONT, "BI", f"{FONT_DIR}/Arial Bold Italic.ttf")


def section(pdf: FPDF, title: str) -> None:
    pdf.ln(7)
    pdf.set_font(FONT, "B", 10)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 12, title.upper(), new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 1
    pdf.set_draw_color(*RULE)
    pdf.set_line_width(0.5)
    pdf.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
    pdf.ln(5)


def role_header(pdf: FPDF, company: str, location: str, dates: str, title: str) -> None:
    pdf.set_font(FONT, "B", 10.5)
    pdf.set_text_color(*INK)
    pdf.cell(CONTENT_W * 0.65, 14, company)
    pdf.set_font(FONT, "", 9.5)
    pdf.set_text_color(*INK_SOFT)
    pdf.cell(CONTENT_W * 0.35, 14, dates, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "I", 9.5)
    pdf.cell(CONTENT_W * 0.65, 12, f"{title}  ·  {location}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def project_header(pdf: FPDF, name: str, year: str, links: list[tuple[str, str]]) -> None:
    pdf.set_font(FONT, "B", 10.5)
    pdf.set_text_color(*INK)
    pdf.cell(CONTENT_W * 0.65, 14, name)
    pdf.set_font(FONT, "", 9.5)
    pdf.set_text_color(*INK_SOFT)
    pdf.cell(CONTENT_W * 0.35, 14, year, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "", 9)
    for i, (text, url) in enumerate(links):
        if i > 0:
            pdf.set_text_color(*MUTED)
            pdf.cell(pdf.get_string_width("   ·   "), 12, "   ·   ")
        pdf.set_text_color(*ACCENT)
        pdf.cell(pdf.get_string_width(text), 12, text, link=url)
    pdf.ln(13)


def bullets(pdf: FPDF, items: list[str], size: float = 9.5, line_h: float = 12.5) -> None:
    pdf.set_font(FONT, "", size)
    for item in items:
        pdf.set_text_color(*INK)
        pdf.set_x(MARGIN_X + 10)
        pdf.cell(8, line_h, "•")
        pdf.set_x(MARGIN_X + 20)
        pdf.set_text_color(*INK_SOFT)
        pdf.multi_cell(CONTENT_W - 20, line_h, item, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def skills_row(pdf: FPDF, label: str, items: str) -> None:
    pdf.set_font(FONT, "B", 9.5)
    pdf.set_text_color(*INK)
    pdf.cell(0, 13, label, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "", 9.5)
    pdf.set_text_color(*INK_SOFT)
    pdf.set_x(MARGIN_X)
    pdf.multi_cell(CONTENT_W, 13, items, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def build() -> Path:
    pdf = FPDF("portrait", "pt", "letter")
    pdf.set_margins(MARGIN_X, MARGIN_TOP, MARGIN_X)
    pdf.set_auto_page_break(True, margin=MARGIN_BOTTOM)
    _register_fonts(pdf)
    pdf.add_page()

    # Header
    pdf.set_font(FONT, "B", 24)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 30, "Arsen Khanguieldyan", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(FONT, "", 10)
    pdf.set_text_color(*INK_SOFT)
    contact = ("arsen.khanguieldyan@gmail.com", "+1 (617) 655-4650", "Boston, MA, USA")
    sep = "   ·   "
    sep_w = pdf.get_string_width(sep)
    parts_w = [pdf.get_string_width(p) for p in contact]
    total_w = sum(parts_w) + sep_w * (len(contact) - 1)
    x = (PAGE_W - total_w) / 2
    pdf.set_x(x)
    for i, part in enumerate(contact):
        if i > 0:
            pdf.cell(sep_w, 14, sep)
        link = f"mailto:{part}" if i == 0 else ""
        pdf.set_text_color(*ACCENT if i == 0 else INK_SOFT)
        pdf.cell(parts_w[i], 14, part, link=link)
        pdf.set_text_color(*INK_SOFT)
    pdf.ln(20)
    pdf.set_draw_color(*RULE)
    pdf.set_line_width(0.6)
    pdf.line(MARGIN_X, pdf.get_y(), PAGE_W - MARGIN_X, pdf.get_y())
    pdf.ln(6)

    # Summary — icotec-flavored
    pdf.set_font(FONT, "", 10)
    pdf.set_text_color(*INK_SOFT)
    pdf.multi_cell(0, 13.5,
                   "Digitalization-focused AI engineer with 7 years shipping production AI/ML and "
                   "data integration systems across regulated industries (defense, automotive, "
                   "enterprise). Strong on Microsoft Azure stack (AZ-400 / AZ-900 / AZ-204 certified), "
                   "data architecture and ETL, low-code app delivery, and turning paper / manual "
                   "workflows into structured digital systems. Recent focus: rapid AI prototypes for "
                   "case intake, document understanding, and process automation.",
                   new_x="LMARGIN", new_y="NEXT")

    # Selected Projects
    section(pdf, "Selected Projects")
    project_header(pdf,
                   "Case Pilot — AI Surgical Case Intake & Implant Configuration",
                   "2026",
                   [
                       ("scaffold-production-3492.up.railway.app",
                        "https://scaffold-production-3492.up.railway.app"),
                       ("github.com/smartpneucontact-sketch/Scaffold",
                        "https://github.com/smartpneucontact-sketch/Scaffold"),
                   ])
    bullets(pdf, [
        "Built end-to-end AI prototype: free-text surgical case description goes in, structured "
        "case record comes out with cited indication checks, recommended implant configuration, "
        "imaging-benefit rating, and MDR / FDA compliance flags.",
        "Agentic AI loop on Claude Sonnet 4.6 with RAG over a synthetic icotec product corpus "
        "(specs, IFU, surgical technique, prior cases, regulatory). Three custom tools: retrieve, "
        "imaging-benefit scorer, complexity classifier.",
        "Designed the production-target architecture explicitly mapped onto Microsoft Power "
        "Platform: Power Apps canvas UI, Power Automate flows, Azure AI Search / SharePoint as the "
        "document layer, Dataverse for implant inventory, App Insights for telemetry.",
        "Single-page FastAPI service with visitor-notify (Resend HTTPS API), modern dark UI, deployed to Railway.",
    ])

    project_header(pdf,
                   "Site Copilot — Agentic RFI & Daily Report Assistant",
                   "2026",
                   [
                       ("github.com/smartpneucontact-sketch/Sufflk",
                        "https://github.com/smartpneucontact-sketch/Sufflk"),
                   ])
    bullets(pdf, [
        "Same architecture pattern applied to a different regulated workflow (construction): "
        "two LLM agents drafting RFI responses and daily reports, with Agentic RAG and an "
        "LLMOps spine (JSONL tracing, drift detector, eval gate in CI).",
        "Reinforces that the digitalization pattern transfers cleanly across domains — pick the "
        "workflow, pick the corpus, ship a working agent in days.",
    ])

    # Experience
    section(pdf, "Professional Experience")

    role_header(pdf, "Hyperion", "Yerevan, Armenia", "Nov 2022 – Jun 2025", "Head of Engineering")
    bullets(pdf, [
        "Shipped a fully autonomous AI defense drone — acquired by strategic buyer; owned full "
        "engineering lifecycle across AI software, computer vision, embedded, hardware.",
        "Built edge-deployed computer vision for GPS-denied navigation at 96% accuracy; "
        "validated across 3,000 flight-test hours with strict regulated-industry process discipline.",
        "Led a multidisciplinary team (AI, CV, firmware, electronics, mechanical) and ran the full "
        "project lifecycle — requirements, design reviews, risk register, traceability matrix, "
        "verification & validation — directly applicable to medical-device process rigor.",
        "Designed custom PCB in Altium for flight control and ESC; ran control-loop tuning in "
        "Simulink with hardware-in-the-loop validation.",
    ])

    role_header(pdf, "Deloitte", "Luxembourg", "Apr 2021 – Jun 2022", "Data Analyst")
    bullets(pdf, [
        "Led migration of multi-source enterprise data into a unified Azure-hosted repository with "
        "static + dynamic metadata management; exposed via REST API to a single-page web app for "
        "business-user self-service — a textbook 'eliminate manual paper / Excel workflows' project.",
        "Evaluated nine AutoML platforms (IaaS / PaaS / SaaS) against predefined test protocols; "
        "produced selection rationale and stakeholder presentations for client leadership.",
    ])

    role_header(pdf,
                "Forschungsgesellschaft Umformtechnik mbH",
                "Stuttgart, Germany",
                "May 2019 – Mar 2021",
                "Data Engineer")
    bullets(pdf, [
        "Shipped a tool-wear classifier (CNN, 82% accuracy) integrated into TRUMPF Group's "
        "next-generation punching machines; co-authored a peer-reviewed publication on CNN-based "
        "tool-wear classification (Feb 2020).",
        "Built a sensor-fusion IoT pipeline for stamping presses (force, distance, sound, "
        "lubrication) and an ML failure-prediction algorithm on Audi AG data — connecting "
        "operational sensor data into actionable signals, the data-integration pattern icotec's "
        "JD asks for.",
    ])

    role_header(pdf, "Audi AG", "Neckarsulm, Germany", "Apr 2018 – Dec 2018", "Software Developer")
    bullets(pdf, [
        "Built and deployed an Oracle APEX low-code web application that digitalized die-cast "
        "tooling improvements — exactly the kind of paper-to-digital workflow this role targets. "
        "Rolled out internationally across Audi sites.",
    ])

    # Skills — Microsoft-first ordering for icotec
    section(pdf, "Technical Skills")
    skills_row(pdf, "Digitalization & Low-Code",
               "Oracle APEX (production), Microsoft Power Platform-shaped architecture (Power Apps, "
               "Power Automate, Dataverse, AI Builder — applied via prototype), rapid digital-form "
               "delivery, process automation")
    skills_row(pdf, "Microsoft / Azure",
               "Azure (AZ-400, AZ-900, AZ-204 certified), Azure Data Factory, App Insights-shaped "
               "telemetry, Active Directory, REST API design, custom connectors")
    skills_row(pdf, "AI & ML",
               "LLMs (Claude, GPT, Azure OpenAI), Agentic RAG, tool-use, prompt engineering, "
               "PyTorch, HuggingFace, YOLO, computer vision, CUDA, LLMOps")
    skills_row(pdf, "Data Architecture & Integration",
               "ETL design, sensor-fusion pipelines, REST APIs, vector stores, hybrid search "
               "(BM25 + dense), Azure AI Search-shaped retrieval, AWS, Docker, Kubernetes, "
               "Terraform, GitHub Actions, SQL")
    skills_row(pdf, "Electronics & Hardware",
               "Altium / PCB design, Arduino, sensor integration, SolidWorks, Simulink — regulated "
               "industry V&V and documentation discipline")
    skills_row(pdf, "Soft skills",
               "Stakeholder workshops, requirements engineering, training & enablement, "
               "cross-functional team leadership, multilingual (EN/FR/DE/HY)")

    # Certifications
    section(pdf, "Certifications")
    pdf.set_font(FONT, "", 9.5)
    pdf.set_text_color(*INK_SOFT)
    pdf.multi_cell(0, 13,
                   "Microsoft Azure DevOps Engineer Expert (AZ-400)  ·  Microsoft Azure Administrator (AZ-104 / AZ-204)  "
                   "·  Microsoft Azure Fundamentals (AZ-900)  ·  AWS Cloud Practitioner  ·  TensorFlow Developer  ·  "
                   "Deep Learning in Computer Vision",
                   new_x="LMARGIN", new_y="NEXT")

    # Education
    section(pdf, "Education")
    pdf.set_font(FONT, "B", 10)
    pdf.set_text_color(*INK)
    pdf.cell(CONTENT_W * 0.7, 13, "Ecole Centrale d'Electronique  —  Paris, France")
    pdf.set_font(FONT, "", 9.5)
    pdf.set_text_color(*INK_SOFT)
    pdf.cell(CONTENT_W * 0.3, 13, "", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "", 9.5)
    pdf.cell(CONTENT_W * 0.7, 12, "M.S. Computer Science & Engineering")
    pdf.cell(CONTENT_W * 0.3, 12, "Jun 2019", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(CONTENT_W * 0.7, 12, "B.S. Mathematics & Electronics")
    pdf.cell(CONTENT_W * 0.3, 12, "Jun 2017", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font(FONT, "B", 10)
    pdf.set_text_color(*INK)
    pdf.cell(CONTENT_W * 0.7, 13, "MIT Professional Education")
    pdf.set_font(FONT, "", 9.5)
    pdf.set_text_color(*INK_SOFT)
    pdf.cell(CONTENT_W * 0.3, 13, "Dec 2025 – Sep 2026", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "I", 9.5)
    pdf.cell(0, 12, "Digital Transformation in the AI Age  (in progress)", new_x="LMARGIN", new_y="NEXT")

    # Languages
    section(pdf, "Languages")
    pdf.set_font(FONT, "", 9.5)
    pdf.set_text_color(*INK_SOFT)
    pdf.cell(0, 13,
             "English (proficient)  ·  French (fluent)  ·  German (fluent)  ·  Armenian (native)",
             new_x="LMARGIN", new_y="NEXT")

    out = Path("Arsen_Khanguieldyan_Resume_icotec.pdf").resolve()
    pdf.output(str(out))
    return out


if __name__ == "__main__":
    print(f"Wrote: {build()}")
