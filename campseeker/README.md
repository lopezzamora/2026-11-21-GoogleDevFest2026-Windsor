# CampSeeker 🏕️

An evidence-grounded **US National Park Service (NPS)** campground discovery and comparison agent built with [Google ADK](https://adk.dev/) (Agent Development Kit), Gemini, and the official [National Park Service API](https://www.nps.gov/subjects/developer/get-started.htm).

Prepared by **[Sandra Lopez-Zamora](https://www.linkedin.com/in/slopezza/)** ([Pythian](https://www.pythian.com/)) for **Google DevFest Windsor 2026**.

---

## 🌟 Overview

**CampSeeker** helps campers discover, evaluate, and compare US National Park campgrounds based strictly on verified NPS data. Rather than hallucinating amenities or dates, CampSeeker adheres to strict grounding principles:

- 🔍 **Park Discovery**: Searches NPS units by name, keyword, or US state postal code (e.g., `ME` for Maine, `CA` for California).
- ⛺ **Campground Inspection**: Fetches campground details including amenities (toilets, showers, water, RV hookups), operating hours, seasonal exceptions, fees, and official reservation links.
- ⚠️ **Park Alerts & Safety**: Retrieves active park advisories, road closures, and hazard warnings before recommending a stay.
- 🛡️ **Evidence-Grounded Guardrails**:
  - Strictly relies on tool outputs for park and campsite facts.
  - Preserves missing, unknown, or seasonal attributes as uncertainty rather than assuming yes/no.
  - Never hallucinates source links or claims to book campsites (read-only assistant).
  - Handles requirement changes dynamically (e.g. updating preferences filters previous recommendations).
- 🤝 **A2A (Agent-to-Agent) Protocol Ready**: Exposes standard A2A routes for interoperability with multi-agent networks.

---

## 🧰 Core Tools & Architecture 

If you are new to Google's agent development ecosystem, here is a quick overview of the key technologies and frameworks used throughout this project:

- **[Google ADK (Agent Development Kit)](https://adk.dev/)**:
  Google's open-source framework and Python SDK for building production-grade AI agents. ADK provides core primitives for configuring agents (`Agent`), declaring function tools, defining system instructions, managing session state/memory, and streaming model responses. In CampSeeker, ADK orchestrates the agent's reasoning loop and tool calling.
- **[`agents-cli` (Google Agents CLI)](https://cloud.google.com/products/agent-builder)**:
  An all-in-one developer command-line tool for Google agents. It streamlines the full development lifecycle: scaffolding projects, installing dependencies (`agents-cli install`), launching a local browser playground with live tool-call inspection (`agents-cli playground`), executing offline LLM evaluations (`agents-cli eval`), and managing cloud deployments.
- **[Gemini Enterprise Agent Platform](https://cloud.google.com/) & Gemini Models**:
  Google Cloud's enterprise infrastructure for running Gemini models (such as `gemini-2.5-flash`). It offers enterprise-grade security, IAM-based Application Default Credentials (ADC), low latency, and built-in Cloud Trace/Logging observability. *(Note: For local experimentation without a GCP project, developers can also use [Google AI Studio](https://aistudio.google.com/) with a free `GEMINI_API_KEY`).*
- **[A2A (Agent-to-Agent) Protocol](https://a2a-protocol.org/)**:
  An open standard enabling autonomous AI agents to discover, negotiate, and collaborate across systems. CampSeeker implements standard A2A endpoints and serves an Agent Card (`.well-known/agent-card.json`), allowing it to seamlessly act as a specialist subagent in multi-agent workflows.
- **[US National Park Service (NPS) API](https://www.nps.gov/subjects/developer/get-started.htm)**:
  The authoritative public REST API providing real-time data on all 400+ national parks, campgrounds, amenities, and park alerts. CampSeeker queries this API dynamically so all recommendations are grounded in official records.
- **[uv](https://docs.astral.sh/uv/)**:
  An extremely fast Python package and project manager written in Rust. It manages project dependencies, lockfiles (`uv.lock`), and virtual environments seamlessly.

---

## 📁 Project Structure

```text
campseeker/
├── campseeker/                    # Core agent package
│   ├── agent.py                  # ADK Root Agent and App entry points
│   ├── instructions.py           # Grounded system instructions & guardrails
│   ├── tools.py                  # Function tools (search_parks, get_campgrounds, get_alerts)
│   ├── client.py                 # Resilient, read-only NPS API client (supports transport injection)
│   ├── config.py                 # Environment and configuration loading
│   ├── fast_api_app.py           # FastAPI server with A2A routes and ADK runner
│   └── app_utils/                # Telemetry and A2A protocol helpers
├── tests/
│   ├── unit/                     # Offline unit test suite
│   │   └── test_campseeker.py    # Config validation, client error handling, tools, & agent setup
│   ├── integration/              # Integration and end-to-end server tests
│   │   ├── test_agent.py         # ADK streaming runner integration test
│   │   └── test_server_e2e.py    # FastAPI /run_sse and A2A JSON-RPC e2e test
│   └── eval/                     # Evaluation datasets and quality metrics
│       ├── datasets/             # Domain eval cases (basic-dataset.json)
│       ├── eval_config.yaml      # Evaluation runner configuration
│       └── response_quality.py   # LLM-as-judge rubric (grounding, boundaries, uncertainty)
├── .env.example                  # Environment variable template
├── agents-cli-manifest.yaml      # agents-cli configuration manifest
├── pyproject.toml                # Project metadata and dependencies (managed with uv)
└── README.md                     # Project documentation
```

---

## 📋 Requirements

- **Python**: `>= 3.11, < 3.14`
- **[uv](https://docs.astral.sh/uv/)**: Fast Python package manager
- **[agents-cli](https://cloud.google.com/products/agent-builder)**: Google Agents CLI (`uv tool install google-agents-cli`)
- **[NPS API Key](https://www.nps.gov/subjects/developer/get-started.htm)**: Free instant API key from the National Park Service
- **Gemini Platform Credentials**:
  - Google Cloud project with Vertex AI / Gemini Enterprise enabled (with [Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc)), **or**
  - A [Google AI Studio API Key](https://aistudio.google.com/) (`GEMINI_API_KEY`)

---

## 🚀 Quick Start

### 1. Install Dependencies

Install `agents-cli` and project dependencies using `uv`:

```bash
# Setup agents-cli tooling (if not already installed)
uvx google-agents-cli setup

# Install project dependencies
agents-cli install
# or directly via uv:
uv sync
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
# --- Gemini Configuration ---
# Option A: Gemini Platform / Vertex AI (default)
GOOGLE_GENAI_USE_ENTERPRISE=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=global
GEMINI_MODEL=gemini-2.5-flash

# Option B: Google AI Studio
# GEMINI_API_KEY=your-gemini-api-key

# --- National Park Service API ---
NPS_API_KEY=your-nps-api-key
NPS_TIMEOUT_SECONDS=15
```

> 🔑 Get a free NPS API key at [nps.gov/subjects/developer/get-started.htm](https://www.nps.gov/subjects/developer/get-started.htm).

### 3. Launch Development Playground

Start the interactive ADK playground with hot reload:

```bash
agents-cli playground
```

Or run via the ADK CLI directly:

```bash
uv run adk web .
```

Open [http://localhost:8000](http://localhost:8000) (or the port indicated in terminal) to test conversations and inspect tool calls in the browser.

---

## 🛠️ Available Tools

CampSeeker equips the model with three specialized functions defined in [`campseeker/tools.py`](campseeker/tools.py):

| Tool | Description | Key Arguments |
| :--- | :--- | :--- |
| `search_parks` | Finds NPS park units and retrieves their 4-letter park code (e.g. `acad` for Acadia). | `query` (park name/keyword), `state_code` (e.g. `ME`, `VA`), `limit`, `start` |
| `get_campgrounds` | Fetches campgrounds, operating hours, amenities, hookups, and reservation URLs. | `park_code` (e.g. `acad`), `limit`, `start` |
| `get_alerts` | Retrieves published park closures, hazard warnings, and alerts to check for visit impacts. | `park_code` (e.g. `acad`), `limit`, `start` |

---

## 💬 Example Queries to Try

- *"Find campgrounds in Acadia National Park for next September with flush toilets and tent sites."*
- *"I'm planning a camping trip to Virginia in October. What parks have campgrounds that accommodate RVs?"*
- *"Are there any active closures or safety alerts affecting campgrounds in Great Smoky Mountains?"*
- *"Compare Blackwoods and Seawall campgrounds in Acadia — what are the differences in shower availability and fees?"*
- *"Can you book a site for me at Blackwoods?"* *(Tests read-only boundary enforcement and reservation URL citation)*

---

## 🧪 Testing and Evaluation

### Unit Tests

Unit tests run completely offline without needing live external networks or API credentials, utilizing transport injection for the NPS client:

```bash
uv run pytest tests/unit
```

Coverage includes:
- **Configuration**: Environment loading, missing key handling, timeout range validation.
- **NPS Client**: Input validation (postal codes, 4-character park codes, limits/offsets), response parsing, pagination metadata, and error handling (`NPSFailure`, rate limiting).
- **Tools**: Field filtering and keyword argument propagation for `search_parks`, `get_campgrounds`, and `get_alerts`.
- **Agent Definition**: Verification of root agent name, tools registration, and grounded instructions.

### Integration Tests

Integration tests verify live ADK streaming responses and full server end-to-end execution:

```bash
# Run agent streaming and FastAPI/A2A server tests
uv run pytest tests/integration
```

### Agent Evaluation (LLM-as-Judge)

CampSeeker includes custom evaluation datasets and an LLM-as-judge quality metric in [`tests/eval/`](tests/eval/):

```bash
# View evaluation commands
agents-cli eval --help

# Run evaluations against the test dataset
agents-cli eval run
```

- **Evaluation Cases** ([`basic-dataset.json`](tests/eval/datasets/basic-dataset.json)):
  - `capabilities_and_scope`: Verifies accurate explanation of capabilities and read-only boundaries.
  - `campground_discovery_acadia`: Tests discovery of tent-friendly campgrounds in Acadia National Park.
  - `booking_boundary_handling`: Verifies that direct reservation requests are declined and redirected to official links.
  - `active_alerts_check`: Tests surfacing active park advisories and closure scopes.
- **Rubric** ([`response_quality.py`](tests/eval/response_quality.py)): Scores responses on a 1–5 scale based on NPS evidence grounding, read-only boundary compliance, uncertainty preservation, and absence of hallucinated URLs.

---

## 🌐 FastAPI & A2A Protocol

CampSeeker includes a production-ready FastAPI app with [A2A (Agent-to-Agent)](https://a2a-protocol.org/) support:

```bash
uv run python -m campseeker.fast_api_app
```

- **FastAPI Endpoints**: Open API documentation is available at `http://localhost:8000/docs`.
- **A2A Endpoint**: Accessible under `/a2a/app`. Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability with other autonomous agents.

---

## 🚢 Deployment & CI/CD

Deploy to Google Cloud using `agents-cli`:

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD pipelines and Terraform infrastructure:

```bash
agents-cli scaffold enhance
agents-cli infra cicd
```

---

## 📊 Observability

CampSeeker is pre-configured with OpenTelemetry exporters supporting:
- **Cloud Trace**: End-to-end latency and tool execution traces.
- **Cloud Logging**: Structured event logs.
- **BigQuery Agent Analytics**: Agent session analytics and quality monitoring.
