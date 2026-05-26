# Case Pilot

AI-assisted **surgical case intake + BlackArmor® implant configuration** assistant. Portfolio demo for [icotec medical](https://www.icotec-medical.com) — *Digitalization & AI Professional* role (Boston).

> A surgeon's free-text case description goes in. A structured case record comes out — with cited indication checks, recommended implant configuration, imaging-benefit rating, and MDR/FDA compliance flags. The kind of paper-to-digital workflow icotec's Digitalization & AI role explicitly calls out.

## Demo (60 seconds)

```bash
make install          # pip install -e .
make ingest           # smoke-test the corpus
export ANTHROPIC_API_KEY=sk-ant-...
make serve            # http://localhost:8000
```

## How it maps to icotec's stack

| This demo | icotec production target |
| --- | --- |
| Anthropic Claude Sonnet 4.6 | **Azure OpenAI** via Power Platform AI Builder |
| BM25 over markdown corpus | **Azure AI Search** / SharePoint Search on a Document Library |
| FastAPI + Pydantic backend | **Power Automate** + custom connector to **Azure Function** |
| Single-page UI | **Power Apps** canvas app, embedded in Dynamics 365 / Teams |
| JSONL traces on disk | **App Insights** → Azure Data Explorer / Fabric |
| Synthetic corpus | icotec IFU + surgical guides in **SharePoint** + **Dataverse** |
| Visitor-notify webhook | **Power Automate** flow → Outlook / Teams alert |

The agent loop and the corpus contract stay; the surfaces change. That's the digitalization role in one sentence.

## What it does

**One agent**: `CaseAgent` (case intake + configuration).

**Tools**:
- `retrieve` — search the icotec corpus (specs, IFU, surgical technique, prior cases, compliance).
- `check_imaging_benefit` — rate how much this case benefits from going radiolucent (oncology + post-op radiation + serial MRI + pediatric all push the score up).
- `classify_case_complexity` — flag cases that should route to a clinical specialist.

**Output** (structured JSON):
- Normalized case summary
- Per-indication check with source citations
- Recommended construct + screws + rods + rationale
- Imaging benefit band, complexity band, specialist-review flag
- MDR / FDA compliance flags
- Open questions for the surgeon

## Corpus

Synthetic but realistic:
- `data/corpus/specs/blackarmor_pedicle_screws.md` — device description, materials, imaging properties.
- `data/corpus/indications/blackarmor_pedicle_screws_ifu.md` — IFU language including off-label flags.
- `data/corpus/surgical_technique/blackarmor_pedicle_screw_technique.md` — preop / placement / imaging steps.
- `data/corpus/cases/case_001.md`...`case_003.md` — oncology, degenerative, trauma exemplars.
- `data/corpus/compliance/regulatory_summary.md` — FDA / MDR / 13485 / UDI.

## Visitor notify

When someone lands on `/`, the middleware looks up their IP via ipapi.co and emails the author via the Resend HTTPS API. Same module the Site Copilot demo uses — Railway blocks SMTP, so HTTPS is the only viable transport.

Set in Railway Variables:
- `RESEND_API_KEY=re_...`
- `NOTIFY_TO_EMAIL=arsen.khanguieldyan@gmail.com`
- (Optional) `VISITOR_NOTIFY_ENABLED=0` to kill-switch.

## Honest limits

- **Synthetic corpus.** Real icotec docs would be PDF (IFUs) and SharePoint pages — needs OCR + table extraction + UDI lookup.
- **No Dataverse / Power Platform integration yet.** This is the FastAPI prototype; the natural next step is to wrap the agent in a Power Automate custom connector so a Case Pilot Power App can call it from inside Dynamics 365.
- **No PHI / clinical-grade safety.** This is a planning aid, not a regulated decision-support tool. Any production deployment would need IRB / clinical workflow review.
- **No UDI lookup.** Production would call the Dataverse implant inventory table for live UDI tracking.

---

Author: **Arsen Khanguieldyan** · arsen.khanguieldyan@gmail.com
