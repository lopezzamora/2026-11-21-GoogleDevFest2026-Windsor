# Google DevFest Windsor 2026 🍁

## “It Worked in the Demo”: Evaluating Agents Before Your User Does

Presented by **[Sandra Lopez-Zamora](https://www.linkedin.com/in/slopezza/)** (Senior AI/ML Engineer, [Pythian](https://www.pythian.com/))  
📅 **Date:** November 21st, 2026  
📍 **Event:** [Google DevFest Windsor 2026](https://gdg.community.dev/)  
📊 **Presentation Deck:** [Presentation PDF](<./2026-11-21 - DevFest Windsor 2026 - It worked in the demo v2.pdf>) | [Google Slides](https://docs.google.com/presentation/d/1382v1KW7VUqCbN9vlHQRwLlZtxFC2shSTR3gMOF6yeY/edit?usp=sharing)  
🏕️ **Companion Demo Agent:** [`campseeker/`](campseeker/README.md)

---

## 🎯 Talk Abstract

> **Your agent nailed the demo, but then real users showed up with vague questions, unexpected paths, and edge cases, and it gave confident answers that were quietly wrong.**
>
> Agents fail differently from traditional software: they’re non-deterministic, they make multi-step decisions, and they’ll happily report a task as done when it isn’t.
> 
> This session shows a practical way to evaluate agents before your users end up doing the testing for you. Using Gemini Enterprise Agent Platform, we will go beyond checking the final answer to evaluate tool choices, trajectories, and safety behaviour. We will also generate realistic test scenarios, so you aren’t limited to the cases you thought of, and use the results to find and fix what’s breaking.
> 
> You will leave with a clear model for agent evaluation that you can apply to your own agents, whether you’re shipping your first prototype or running agents in production.

---

## 💡 Key Concepts & Objectives

This repository contains the slides and complete companion codebase designed to take attendees from high-level evaluation principles to hands-on implementation:

1. **Answer Quality vs. Observable Trajectories**
   - Fluent, plausible text alone cannot distinguish grounded agent behavior from a lucky guess.
   - Real evaluation requires inspecting observable intermediate steps: tool choices, arguments passed, ordering, and retrieved API evidence.
2. **Prompts are Not Permission Boundaries**
   - Public failures (Air Canada, Chevrolet/Fullpath, Replit) show why safety and permissions must be enforced at the architectural layer (e.g. read-only clients, explicit scopes), not just in system prompts.
3. **The 5-Step Evaluation Loop**
   - A repeatable, scientific cycle for building reliable agents:
     - `1. Define`: Establish clear metrics and rubrics (e.g., *Valid Trip Plan Rate*).
     - `2. Build`: Curate fixed benchmark scenarios and edge cases.
     - `3. Run`: Execute agents and capture full tool traces.
     - `4. Score`: Grade traces using deterministic rules and LLM-as-judge AutoRaters.
     - `5. Improve`: Apply targeted fixes only from verified failures (**"No failure, no fix"**), then rerun the identical suite.
4. **Pre-Deployment vs. Post-Deployment Rigor**
   - Rapid offline local inner loop (`agents-cli eval run`) during development.
   - Batch managed cloud evaluations (`agents-cli eval submit`) and continuous Online Monitoring on production traces in Google Cloud.

---

## 🏕️ Reference Implementation: CampSeeker

This repository includes **[CampSeeker](campseeker/README.md)**, an evidence-grounded campground discovery agent built with **Google ADK** (Agent Development Kit), **Gemini 2.5 Flash**, and the official **US National Park Service (NPS) API**.

```text
2026-11-21-GoogleDevFest2026-Windsor/
├── README.md                      # Main event overview & talk abstract
└── campseeker/                    # Companion agent reference project
    ├── campseeker/                # ADK Agent, tools, and FastAPI server
    ├── tests/
    │   ├── unit/                  # Offline unit tests
    │   ├── integration/           # Server and streaming integration tests
    │   └── eval/                  # 5-step evaluation suite & LLM-as-judge
    │       ├── datasets/          # Curated benchmark cases (basic-dataset.json)
    │       ├── eval_config.yaml   # Metric configuration & pass thresholds
    │       ├── valid_trip_plan_rate.py # Slide 9 binary metric implementation
    │       └── response_quality.py     # 1-5 rubric judge
    └── README.md                  # Comprehensive agent setup & eval guide
```

### Quick Replication (Local DevFest Lab)

```bash
# 1. Navigate to the agent workspace
cd campseeker

# 2. Install dependencies via uv and agents-cli
agents-cli install

# 3. Configure your API keys (.env)
cp .env.example .env

# 4. Run the interactive local playground
agents-cli playground

# 5. Run the full 5-step evaluation suite
agents-cli eval run
```

👉 **See [`campseeker/README.md`](campseeker/README.md) for the full walkthrough, evaluation datasets, and cloud deployment instructions.**

---

## 👩‍💻 About the Speaker

**Sandra Lopez-Zamora** is a **Senior Machine Learning Engineer** at **[Pythian](https://www.pythian.com/)** as part of the AI Services team. Prior to this role, she worked in various roles at Scotiabank, where she delivered impactful solutions within cloud migration and data-driven decision-making initiatives, and built credit risk models across a \$12B portfolio. Her expertise spans retail credit risk modelling, Python, GCP, MLOps, and data strategy. Recently, she has been experimenting with Generative AI to explore new ways of delivering insights and enhancing decision-making.

Sandra is also a passionate community builder. As City Lead for **Women in AI Canada (London & Southwestern Ontario)**, she creates spaces where ambition and belonging thrive.

Additionally, she holds a **PhD in Chemical Engineering** from **Western University** with a strong focus on Mathematical Modelling and Machine Learning applications.

- 🔗 **LinkedIn:** [linkedin.com/in/slopezza](https://www.linkedin.com/in/slopezza/)

---

## 🏢 About Pythian

**[Pythian Services Inc.](https://www.pythian.com/about)** is a leading global data, cloud, and AI consultancy with nearly three decades of engineering experience helping enterprises transform and stay competitive in the digital economy.

Founded in 1997, Pythian’s mission is to **help organizations unlock the full power and potential of their data** by turning complexity into a distinct business advantage:
- **Artificial Intelligence & Machine Learning:** Designing and deploying production-grade AI solutions, custom ML models, agentic workflows, RAG architectures, and automated MLOps pipelines.
- **Data Engineering & Analytics:** Modernizing legacy data platforms, building robust data lakes/warehouses, eliminating technical debt, and delivering actionable business intelligence.
- **Cloud & Database Managed Services:** Delivering proactive 24/7 database administration (DBA), cloud migrations, Site Reliability Engineering (SRE), and continuous operational support across multi-cloud environments.
- **Strategic Hyperscaler Partnerships:** As a **Premier Google Cloud Partner** (and multi-year Google Cloud Partner of the Year award winner in Data Analytics & Cloud Migration), Pythian maintains tier-one certified alliances across Google Cloud, AWS, Microsoft Azure, Oracle, and Snowflake.

Learn more at **[pythian.com/about](https://www.pythian.com/about)**.

---

## 📚 Links & Additional Resources

- 📊 **Presentation Slides:** [“It Worked in the Demo”: Evaluating Agents Before Your User Does (PDF)](<./2026-11-21 - DevFest Windsor 2026 - It worked in the demo v2.pdf>) 
- 🛠️ **Google Agent Development Kit (ADK):** [adk.dev](https://adk.dev/)
- 📦 **Google Agents CLI (`agents-cli`):** [cloud.google.com/products/agent-builder](https://cloud.google.com/products/agent-builder)
- 🌲 **National Park Service (NPS) API:** [nps.gov/subjects/developer](https://www.nps.gov/subjects/developer/get-started.htm)
