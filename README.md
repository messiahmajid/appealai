# AppealAI

## Overview

AppealAI helps clinicians and care teams draft insurance prior authorization appeal letters from clinical notes and denial details.

The app is built to do three things well:

- turn messy clinical notes into a structured, payer-ready appeal;
- keep the letter grounded in the uploaded chart, denial text, and retrieved policy sources;
- make the generation process transparent with progress steps, safety checks, and downloadable Word output.

AppealAI is drafting support software. It is not a medical decision-maker, legal advice, or a substitute for clinician review before submission.

## Problem

Prior authorization denials often require a clinician or staff member to write a detailed appeal that connects the patient's chart to the payer's medical-necessity criteria. That usually means reading the denial, finding the right policy language, extracting chart evidence, quoting labs or imaging correctly, and writing a rebuttal that is specific enough for medical review.

This is slow, repetitive, and easy to get wrong. A weak appeal may miss the exact denied criterion, cite the wrong policy, overstate the chart, or fail to explain why a formulary or step-therapy exception is medically appropriate.

## Why It Matters

Appeals can affect whether a patient receives a medication, imaging study, procedure, device, or specialist intervention on time. Delays add administrative burden for clinicians and can delay care for patients.

AppealAI focuses on the parts of the workflow where software can help: organizing the record, mapping evidence to criteria, checking for unsupported claims, and producing a complete draft that a clinician can review instead of starting from a blank page.

## What It Does

AppealAI takes:

- clinical notes, uploaded as `.txt`, `.md`, `.csv`, `.docx`, or text-based `.pdf`;
- payer denial details copied from the denial letter or portal;
- patient, payer, provider, CPT/HCPCS, ICD-10, and requested-service information.

It produces:

- a complete appeal letter;
- criterion-by-criterion medical necessity reasoning;
- direct rebuttal of payer denial reasons;
- citations to retrieved guideline/policy sources;
- optional PubMed literature support when relevant articles are found;
- a structured safety report showing unsupported quotes, invalid citations, placeholders, and documentation concerns;
- a `.docx` download for newly generated and historical appeals when running with the FastAPI backend.

## Key Features

- **Clinical note upload**: supports plain text, Markdown, CSV, DOCX, and text-based PDF extraction.
- **Denial detail parsing**: pasted denial details can populate payer, member, denial, diagnosis, service, and authorization fields.
- **Streaming generation**: the UI shows stages such as guideline retrieval, PubMed search, generation, safety checks, repair, and save.
- **Clinical note sufficiency check**: very thin notes are blocked before spending an LLM call.
- **Guideline retrieval**: exact CPT/HCPCS and ICD-10 matches are preferred before keyword fallback.
- **Medical safety checks**: deterministic checks catch unresolved placeholders, invalid citations, unsupported quotes, and unsupported numeric claims.
- **Repair pass**: unsafe drafts can be repaired before being stored.
- **Payer-safe language**: missing or unclear criteria are no longer presented as a payer-facing "Documentation Gaps" concession. They are reframed as exception rationale when appropriate.
- **Demo/sample cases**: the home screen includes realistic orthopedic, cardiology, and oncology sample cases.
- **Model fallback**: Gemini text generation tries multiple low-cost/free models before giving up, and can fall back to Anthropic or OpenRouter when keys are configured.

## Architecture

```text
Clinical notes + denial details
        |
        v
Field parsing and clinical-note sufficiency check
        |
        v
Guideline retrieval
  - exact code matches first
  - keyword fallback if no code match exists
        |
        v
Optional PubMed search
        |
        v
Prompt assembly with separated sources
  - Source A: patient clinical notes
  - Source B: guideline / policy sources
  - Source C: PubMed literature, when available
  - Payer denial details: administrative and denial-rebuttal context
        |
        v
LLM draft generation
        |
        v
Deterministic safety checks
        |
        v
Repair pass if needed
        |
        v
Saved appeal + citations + DOCX download
```

The prompt intentionally separates source types. Patient facts should come from clinical notes. Payer criteria and denial assertions should come from denial details and guideline sources. PubMed articles can support general medical reasoning, but they should not be treated as patient-specific chart evidence.

## Tech Stack

| Area | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, Tailwind CSS v4, lucide-react |
| Backend | FastAPI, SQLAlchemy async, PostgreSQL |
| Database | PostgreSQL for the FastAPI backend; local JSON fallback for prototype use |
| LLM providers | Gemini, Anthropic, OpenRouter |
| Document parsing | Built-in text/DOCX/text-PDF extraction |
| Word export | `python-docx` |
| Evidence search | PubMed NCBI E-utilities API |
| Testing | ESLint, TypeScript, pytest |
| Deployment | Docker Compose for PostgreSQL/backend; Next.js frontend |

## Technical Challenges

- **Grounding medical claims**: The letter must be persuasive without inventing facts. The app separates clinical notes, payer denial details, guidelines, and PubMed literature so the model does not treat one source as another.
- **Avoiding false safety warnings**: Medical text often differs by punctuation, hyphenation, section headings, or units such as `kg/m²` vs `kg/m2`. The safety checker normalizes harmless formatting differences while still flagging unsupported facts.
- **Handling incomplete documentation**: Some cases have real gaps, such as missing step-therapy trials. The app now avoids payer-facing "Documentation Gaps" sections and instead frames appropriate cases as exception rationale.
- **Parsing real-world uploads**: Users do not only upload `.txt` files. DOCX and text-based PDF extraction were added so common clinical note formats work without manual conversion.
- **Rate limits on free models**: Free Gemini/OpenRouter usage can hit per-minute, token, or daily quotas. The app now tries multiple Gemini models and supports provider fallback.
- **Keeping generation transparent**: Streaming progress turns a black-box wait into visible stages: retrieving policies, checking sufficiency, searching PubMed, generating, running safety checks, repairing, and saving.

## Results / Metrics

- Clinical note upload supports 5 common formats: `.txt`, `.md`, `.csv`, `.docx`, and text-based `.pdf`.
- Backend test suite currently has 51 passing tests.
- Evaluation coverage includes 50+ medical denial scenarios.
- Guideline retrieval covers common denial areas including cardiology, diabetes medications, oncology, orthopedics, spine procedures, home oxygen, and power mobility.
- Deterministic safety checks cover placeholders, invalid citations, unsupported quotes, and unsupported numeric claims.
- Demo flow includes 3 preloaded sample cases: orthopedics, cardiology, and oncology.

## What I Learned

- Medical AI products need source boundaries. The most important prompt rule is not "write better"; it is "know which source each fact is allowed to come from."
- A safety checker can be too strict. Exact quote matching sounds safe, but in practice it creates false alarms unless it tolerates punctuation, pluralization, units, and heading-style text.
- Payer-facing language matters. Calling something a "documentation gap" may be accurate internally, but it can weaken the appeal if shown directly to the payer.
- Free model APIs are useful for demos, but production-quality workflows need fallback providers, clear errors, caching, and rate-limit-aware behavior.
- Upload and export details matter. DOCX/PDF input and DOCX output are not extras for this domain; they match how clinical offices actually work.

## Next Steps

- Add OCR for scanned PDFs and image-only faxes.
- Expand the guideline/policy corpus with more payer-specific pharmacy, imaging, DME, and surgical policies.
- Add user-editable policy source management so teams can upload payer policies.
- Add stronger structured extraction for payer criteria, deadlines, NDC codes, and step-therapy rules.
- Add role-based accounts and organization-level appeal history.
- Add deployment documentation for a production environment.
- Add more evaluation cases with expected letter-quality rubrics, not just retrieval checks.

## Setup

The recommended local setup runs the full product:

- Next.js frontend at [http://localhost:3000](http://localhost:3000)
- FastAPI backend at [http://localhost:8000](http://localhost:8000)
- PostgreSQL through Docker
- DOCX upload/download support through the backend

After installation, you will use two terminal windows: one for the backend and one for the frontend.

### Prerequisites

Install:

- Node.js 18 or newer;
- Python 3.11 or newer;
- Docker, if you want PostgreSQL through `docker compose`;
- `uv` for the backend Python environment.

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Clone And Install

```bash
git clone https://github.com/messiahmajid/appealai.git
cd appealai
npm install
```

`npm install` installs the frontend/root JavaScript dependencies. Backend Python dependencies are installed later with `uv sync --extra dev`.

### 2. Configure API Keys

The app needs at least one text-generation API key.

For the easiest free setup, use a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). For more reliable demos, also add either an OpenRouter or Anthropic key so the app has a fallback if Gemini rate-limits.

For the FastAPI backend, copy the backend environment file:

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/appealai

# Free Gemini key from https://aistudio.google.com/apikey
GOOGLE_GENERATIVE_AI_API_KEY=

# Optional Gemini model order. The app tries these in order.
GEMINI_TEXT_MODELS=gemini-2.0-flash-lite,gemini-2.5-flash-lite,gemini-2.5-flash

# Optional fallbacks
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=

LOG_LEVEL=INFO
```

For the Next.js frontend, create `.env.local` in the project root:

```bash
cat > .env.local <<'EOF'
APPEALAI_USE_FASTAPI=true
APPEALAI_BACKEND_URL=http://localhost:8000

# Only needed if running the standalone Next.js prototype without FastAPI.
GOOGLE_GENERATIVE_AI_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=
GEMINI_TEXT_MODELS=gemini-2.0-flash-lite,gemini-2.5-flash-lite,gemini-2.5-flash
EOF
```

The resulting file should look like this:

```env
APPEALAI_USE_FASTAPI=true
APPEALAI_BACKEND_URL=http://localhost:8000

# Only needed if running the standalone Next.js prototype without FastAPI.
GOOGLE_GENERATIVE_AI_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=
GEMINI_TEXT_MODELS=gemini-2.0-flash-lite,gemini-2.5-flash-lite,gemini-2.5-flash
```

Recommended local development uses FastAPI, so the frontend proxies API calls to `http://localhost:8000`.

### 3. Start PostgreSQL

```bash
docker compose up -d postgres
```

PostgreSQL will be available at `localhost:5432` with the credentials from `backend/.env.example`.

### 4. Install Backend Dependencies And Run Migrations

```bash
cd backend
uv sync --extra dev
uv run alembic upgrade head
cd ..
```

You can also use the npm script:

```bash
npm run backend:migrate
```

This creates or updates the database tables used for saved appeals and appeal history.

### 5. Start The Backend

In terminal 1:

```bash
npm run backend:dev
```

The backend runs at [http://localhost:8000](http://localhost:8000). Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### 6. Start The Frontend

In terminal 2:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 7. Confirm The App Works

1. Open the home page.
2. Click one of the sample cases.
3. Generate an appeal.
4. Confirm the progress steps appear.
5. Open the saved appeal and download the `.docx` file.

If generation fails with a Gemini rate-limit message, the app is running but the configured Google project is out of available quota. Wait for quota reset or add `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` to `backend/.env`.

## Running With Docker

PostgreSQL is available through Docker Compose. The compose file also contains a backend service:

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Then run the frontend separately:

```bash
APPEALAI_USE_FASTAPI=true APPEALAI_BACKEND_URL=http://localhost:8000 npm run dev
```

Docker mode still needs valid API keys in `backend/.env`. The frontend is run separately so you can keep Next.js hot reload during development.

## Common Workflows

### Try A Demo Case

1. Open the home page.
2. Choose one of the sample cases.
3. Review the preloaded notes and denial details.
4. Generate the appeal.
5. Download the `.docx` file or open the saved appeal from history.

### Upload Clinical Notes

Supported uploads:

- `.txt`
- `.md`
- `.csv`
- `.docx`
- text-based `.pdf`

Scanned image PDFs are not OCR-supported yet. If a PDF is only an image, paste the note text into the clinical notes field.

### Paste Denial Details

Use the denial details box for payer language such as:

- payer name;
- plan type;
- member ID;
- denial date;
- authorization or case number;
- denied drug, service, CPT, HCPCS, NDC, or ICD-10 code;
- reason for denial;
- plan criteria;
- appeal deadline.

The parser tries to extract structured fields from either denial details or clinical notes. Denial details are preferred for administrative fields. Clinical notes remain the source of patient-specific medical facts.

### Download DOCX

DOCX download requires the FastAPI backend because Word export is handled by Python. Newly generated and historical saved appeals can be downloaded from the appeal detail page when `APPEALAI_USE_FASTAPI=true`.

## Rate Limits And Free APIs

Gemini and OpenRouter can be used free, but free tiers can rate-limit aggressively.

Important details:

- Gemini rate limits may be per minute, per token minute, or per day.
- Gemini limits are applied per Google project, not just per API key.
- Waiting one minute is not always enough if the daily quota or token quota is exhausted.
- AppealAI tries several Gemini models in order before failing.
- Adding `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` gives the app another fallback path.

For the most reliable demos, configure more than one provider.

## Testing

Run the frontend checks:

```bash
npx tsc --noEmit
npm run lint
```

Run backend tests:

```bash
npm run backend:test
```

Run a small evaluation sample:

```bash
npm run eval -- --limit 5
```

Run the full evaluation suite:

```bash
npm run eval
```

## Project Structure

```text
src/
  app/
    page.tsx                    Home page and sample-case entry
    new-appeal/page.tsx          Appeal creation wizard
    appeals/                     Appeal history and detail pages
    api/                         Next.js API routes and FastAPI proxy routes
  lib/
    detail-parser.ts             Denial and clinical text field extraction
    gemini.ts                    Next.js-side LLM helper and model fallback
    guidelines.ts                Local guideline corpus
    medical-analysis.ts          Sufficiency and structured criteria analysis
    medical-safety.ts            Deterministic safety checks and sanitizer
    prompts.ts                   Generation, repair, and verification prompts
    rag.ts                       Embedding cache and fallback retrieval
    web-evidence.ts              PubMed search integration

backend/
  app/
    main.py                      FastAPI app
    routers/
      appeals.py                 Generate, stream, list, detail, DOCX download
      codes.py                   CPT/ICD-10 search
      documents.py               Clinical-note extraction endpoint
      verification.py            On-demand verification
    services/
      appeal_generator.py        End-to-end appeal pipeline
      document_parser.py         TXT/DOCX/PDF extraction
      docx_export.py             Word export
      guidelines.py              Backend guideline corpus
      llm.py                     Provider fallback and response cache
      medical_analysis.py        Sufficiency and criteria matching
      medical_safety.py          Safety checks and repair sanitizer
      prompts.py                 Backend prompt templates
      rag.py                     Embedding cache and keyword fallback
      web_evidence.py            PubMed integration
  alembic/                       Database migrations
  eval/                          Evaluation scenarios
  tests/                         Backend tests
```

## Safety And Review Notes

AppealAI is designed to reduce drafting time, not remove professional review. Before submission, a clinician or authorized staff member should confirm:

- patient identifiers are correct;
- diagnosis and procedure/drug codes are correct;
- quoted clinical facts match the chart;
- the payer address and submission method are correct;
- the requested service matches the actual order or prescription;
- the final letter does not include unsupported statements.

## Troubleshooting

### "Unable to extract text from file"

The file may be scanned, encrypted, image-only, or in an unsupported format. Try copying the note text into the clinical notes field. For PDFs, text-based PDFs work better than scanned PDFs.

### "Gemini API is rate-limited"

This can be a per-minute, per-token-minute, or daily quota issue. Wait for quota reset, reduce repeated generations, or add another provider key.

### DOCX download returns 501

The frontend is not using the FastAPI backend. Set:

```env
APPEALAI_USE_FASTAPI=true
APPEALAI_BACKEND_URL=http://localhost:8000
```

Then run both backend and frontend.

### Generated letter is marked "Needs Review"

Needs Review means the deterministic safety checker found something worth inspecting. It does not always mean the appeal is clinically wrong. Common causes include a quote that does not exactly match the source, a number not found in the notes/guidelines, or a criterion that needs an exception rationale.

## License

MIT
