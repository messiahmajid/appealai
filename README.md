# AppealAI

AI-powered insurance prior authorization appeal letter generator. Upload clinical notes, enter denial details, and get a professionally structured appeal letter grounded in real medical guidelines and peer-reviewed literature.

## The Problem

Insurance companies deny **15-20% of all prior authorization requests** in the US healthcare system. When a claim is denied, physicians must write detailed appeal letters that map the patient's clinical findings to the insurer's exact coverage criteria — citing CMS policies, NCCN guidelines, and medical literature.

This process takes **30-60 minutes per letter**, pulls physicians away from patient care, and is error-prone. A misquoted lab value, a wrong guideline citation, or a missed approval criterion means the appeal gets denied again — delaying or preventing medically necessary care.

Despite this, **50-70% of denied claims are overturned on appeal** when the documentation is right.

**AppealAI reduces this to under 2 minutes** while producing letters that are more thorough and better-cited than most manually written appeals.

## What It Does

1. **Upload clinical notes** — paste or drag-drop physician notes, discharge summaries, or consultation reports
2. **Enter denial details** — patient info, insurance company, denied service, denial reason, CPT/ICD-10 codes (with autocomplete)
3. **Generate appeal letter** — AI produces a structured letter with:
   - Criterion-by-criterion mapping of patient findings to coverage guidelines
   - Direct point-by-point rebuttal of the denial reason
   - Real citations from CMS NCDs/LCDs, NCCN guidelines, and payer policies
   - Live PubMed literature references with PMIDs
   - Documentation gap flagging where clinical evidence is insufficient
4. **Verify accuracy** — optional AI-powered accuracy check that cross-references the letter against the source clinical notes and guidelines
5. **Export** — copy to clipboard or download as markdown

## Key Features

- **Anti-hallucination system** — 5-layer safeguard ensures every claim is traceable to the clinical notes, medical guidelines, or peer-reviewed literature. No fabricated statistics, no made-up guideline references.
- **RAG over 11 medical guidelines** — coverage criteria for CT, MRI, PET/CT, total knee arthroplasty, spinal fusion, cardiac catheterization, NSCLC staging, biologic DMARDs, power mobility devices, bariatric surgery, and sleep studies. Each guideline includes evidence-based statistics from landmark studies.
- **Live PubMed search** — queries NCBI E-utilities API (free, no key needed) for relevant peer-reviewed studies before each generation.
- **Multi-model LLM support** — Claude 3.5 Haiku (primary) with automatic fallback to Gemini Flash-Lite and OpenRouter free models.
- **Evaluation harness** — deterministic 50+ scenario suite across 11 medical policy areas, plus API and retrieval tests.
- **Appeal history** — browse, search, and revisit previously generated appeals.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 16 (App Router), FastAPI |
| Frontend | React 19 |
| Styling | Tailwind CSS v4 + custom CSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy |
| Primary LLM | Claude 3.5 Haiku (Anthropic) |
| Fallback LLMs | Gemini 2.0 Flash-Lite, OpenRouter free models |
| Evidence Search | PubMed NCBI E-utilities API |
| Medical Codes | In-memory ICD-10 + CPT lookup (~130 codes) |
| Storage | PostgreSQL for FastAPI backend; local JSON fallback for standalone Next.js prototype |

## Setup

### Prerequisites
- Node.js 18+
- An Anthropic API key (recommended) or Google Gemini API key (free)

### Installation

```bash
git clone https://github.com/messiahmajid/appealai.git
cd appealai
npm install
```

### Environment Variables

Create a `.env.local` file in the project root:

```env
# Primary (recommended) — ~$0.03 per appeal
ANTHROPIC_API_KEY=sk-ant-...

# Free fallback — get a key at https://aistudio.google.com
GOOGLE_GENERATIVE_AI_API_KEY=your-gemini-key

# Free fallback — get a key at https://openrouter.ai
OPENROUTER_API_KEY=your-openrouter-key
```

You need **at least one** API key. The app will use whichever is available in priority order: Anthropic > Gemini > OpenRouter.

### Run the Standalone Next.js Prototype

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Run the FastAPI + PostgreSQL Backend

```bash
docker compose up -d postgres
cp backend/.env.example backend/.env
npm run backend:migrate
npm run backend:dev
```

In a second terminal:

```bash
APPEALAI_USE_FASTAPI=true APPEALAI_BACKEND_URL=http://localhost:8000 npm run dev
```

The frontend still calls `/api/*`; with `APPEALAI_USE_FASTAPI=true`, those routes forward to the FastAPI backend.

### Test and Evaluate

```bash
npm run lint
npm run build
npm run backend:test
npm run eval -- --limit 5
```

Omit `--limit 5` to run all 55 evaluation scenarios against a live backend.

### Try a Sample Case

From the dashboard, click one of the three sample cases (Orthopedics, Cardiology, or Oncology) to see a pre-populated clinical scenario. Click "Generate Appeal Letter" to see the full pipeline in action.

## How It Works

```
User Input (clinical notes + denial details)
       |
       v
+------------------------------------------+
|  RAG Retrieval                           |
|  Exact CPT/ICD-10 matches first          |
|  Keyword fallback only when no code hit  |
|  Cap at 3 relevant guidelines            |
+-------------------+----------------------+
                    |
       +------------+------------+
       v                         v
+--------------+    +---------------------+
|  PubMed      |    |  Prompt Assembly    |
|  Evidence    |--->|  Source A: Notes     |
|  Search      |    |  Source B: Guidelines|
|  (NCBI API)  |    |  Source C: PubMed   |
+--------------+    +----------+----------+
                               |
                               v
                    +---------------------+
                    |  LLM Generation     |
                    |  Claude Haiku       |
                    |  (temp=0.15)        |
                    +----------+----------+
                               |
                               v
                    +---------------------+
                    |  Appeal Letter +    |
                    |  Citations +        |
                    |  PubMed References  |
                    +---------------------+
                               |
                    (optional)  v
                    +---------------------+
                    |  Accuracy           |
                    |  Verification       |
                    +---------------------+
```

## Cost

| Action | Cost |
|--------|------|
| Generate appeal (Claude Haiku) | ~$0.03 |
| Verify accuracy (optional) | ~$0.02 |
| PubMed search | Free |
| RAG retrieval | Free (keyword-based) |
| With Gemini/OpenRouter fallback | Free |

**~33 appeals per dollar** with Claude Haiku. Free with Gemini or OpenRouter (lower quality).

## Project Structure

```
src/
├── app/                        # Pages + API routes
│   ├── page.tsx                # Dashboard
│   ├── new-appeal/page.tsx     # 3-step appeal creation wizard
│   ├── appeals/                # Appeal history + detail views
│   └── api/
│       ├── generate-appeal/    # Main generation pipeline
│       ├── verify-appeal/      # On-demand accuracy check
│       ├── appeals/            # Appeal CRUD
│       └── codes/              # CPT/ICD-10 autocomplete
├── components/
│   └── Sidebar.tsx             # Navigation
└── lib/
    ├── gemini.ts               # Multi-model LLM abstraction
    ├── prompts.ts              # Prompt templates + anti-hallucination rules
    ├── guidelines.ts           # 11 medical guidelines with evidence
    ├── retrieval.ts            # Guideline source selection
    ├── rag.ts                  # Embedding + keyword fallback retrieval
    ├── web-evidence.ts         # PubMed search integration
    ├── db.ts                   # File-based persistence
    ├── medical-codes.ts        # ICD-10 + CPT lookup
    └── sample-data.ts          # 3 test cases
backend/
├── app/
│   ├── main.py                 # FastAPI app, middleware, routers
│   ├── routers/                # Appeal, code search, verification endpoints
│   ├── services/               # LLM, RAG, retrieval, PubMed, guideline logic
│   └── db/                     # SQLAlchemy async session + tables
├── alembic/                    # PostgreSQL migrations
├── eval/                       # 55-case evaluation harness
└── tests/                      # API, retrieval, service tests
```

## License

MIT
