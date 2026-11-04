# Resume Analysis — Abdurahiman Thommangadan

**Date:** 24 Oct 2026
**Files analysed:** `00_Original_Resumes/Abdurahiman_T_AI_Engineer_Fullstack_Resume_India.docx` and `..._UAE.docx`
**Finding:** the two files are identical except for the location line and phone number. Right now there is **one resume** in two copies, not a resume tailored per market or per role.

**Target roles**
1. **Preferred:** Senior Full Stack / MERN Stack Engineer with Generative AI experience
2. AI Engineer / Generative AI Developer / AI Agent Engineer

**Target markets:** India and UAE, so 2 roles × 2 markets = **4 resumes**

---

## 1. Verdict in one paragraph

The **content is strong and in demand**. Production multi-agent LangGraph systems, human-in-the-loop gates, LoRA fine-tuning of a vision-language model, Langfuse observability and SSE streaming are senior-level Generative AI work, and the 7-year Node/MERN background includes brand names (Samsung SDS, Infosys). The layout is already mostly ATS-safe: one column, no tables, no text boxes, Arial, and contact details in the body rather than the header. The **problems are in how the content is presented**:
- there are almost no numbers
- the resume is about 3 pages long and repeats itself
- one generic title is used for two different jobs
- the evidence for the full-stack role (frontend work) is thin
- it uses a lot of jargon that recruiters don't search for
- several small ATS and parsing problems need fixing

All of these are fixable without inventing anything.

| Area | Score | Comment |
|---|---|---|
| ATS parseability (format) | 7/10 | Single column and standard fonts are good. Links hidden behind words, one role with no company name, Letter paper size |
| Keyword match: AI Engineer roles | 7/10 | Deep, but niche jargon. Missing common search terms (see §4) |
| Keyword match: Full Stack / MERN + AI | 5/10 | React, Next.js and TypeScript appear almost only in the skills lists. No frontend bullets |
| Impact / achievements | 2/10 | The whole resume has essentially one number ("millions of records") |
| Length and focus | 4/10 | About 1,570 words, roughly 3 pages. Target is 2 pages |
| Market fit: India | 5/10 | No notice period or preferred locations |
| Market fit: UAE | 4/10 | No visa status, nationality or notice period |

---

## 2. Critical issues (fix first)

### 2.1 No quantified impact — the biggest weakness
Every bullet says **what was built**, not **what changed because of it**. Recruiters skim for numbers, and ATS ranking and AI screeners favour bullets with outcomes.
Missing numbers to collect (see §8):
- quotation turnaround before and after Janal AI
- extraction or quote accuracy
- number of manufacturers or users onboarded
- size of the team you led
- latency or time to first token
- cost per run
- Samsung traffic or orders, VData record counts, test coverage %

### 2.2 One resume trying to be two jobs
The title reads *"AI Engineer & Fullstack Developer"*. An ATS and a recruiter compare your title against the requisition title. A "Senior Full Stack Engineer" job wants to see that title first, and an "AI Engineer" job wants to see that one. **Each role needs its own headline, summary, skill order and bullet emphasis.**

### 2.3 Experience is under-counted
Apr 2019 to Oct 2026 is **7 years 6 months**. The resume says **"6+ years"**. Change it to **7+ years** (Naukri and many ATS filters bucket candidates by years of experience).

### 2.4 Ambiguous role breaks parsing
`Senior Backend Engineer · SaaS Platforms (LMS, TV Apps, Voter Data) | Sep 2024 – Jan 2025` has **no company name**, and its date sits inline after a "|" instead of right-aligned like the other roles. The ATS will either attach it to the wrong employer or drop it.
**Fix (to be confirmed):** if this was at Voizzit, show **one employer with two roles**. That shows a **promotion in about 4 months**, which is a strong signal:
```
Voizzit Information Technology LLC — Dubai, UAE                Sep 2024 – Present
  Tech Lead — Generative AI & Agent Platform                   Jan 2025 – Present
  Senior Backend Engineer                                      Sep 2024 – Jan 2025
```
Also, the VData project is described as "Tech-Lead-owned", but the role is titled "Senior Backend". Pick one.

### 2.5 Too long and repetitive (~3 pages)
- **"Technical Problem Solving & Production Quality"** (7 bullets) restates the experience section as self-claims. **Delete it.** Move any real evidence into experience bullets.
- **"Featured Projects"** repeats Janal AI, EMTAB, TechBuddy, VData and Solargraf, which already appear under experience. **Delete it** from the Full Stack resumes. For the AI resumes, keep only **independent or GitHub AI projects**, if any exist.
- Target: **2 pages**, roughly 650–850 words.

### 2.6 Weak full-stack evidence (critical for your preferred role)
For a MERN / Full Stack + AI role, the experience bullets should prove frontend ownership. Right now React, Three.js and Konva appear only in "Stack:" lines, and the Voizzit bullets talk about *"coordinating"* and *"defining contracts"* for the frontend. Collect what you **personally built** in React/TypeScript, for example:
- the CAD canvas
- the streaming chat UI
- dashboards
- TV apps
- the Angular modules at Nucore

---

## 3. ATS and formatting fixes

| # | Issue | Fix |
|---|---|---|
| 1 | "LinkedIn" and "GitHub" are clickable words. Many ATS keep only the visible text, so the URL is lost | Write the URLs out in full: `linkedin.com/in/<custom-url>` and `github.com/abdurahmant7` |
| 2 | Name shown as **"ABDURAHIMAN T"** | Use **"Abdurahiman Thommangadan"** to match LinkedIn and your passport. This matters for UAE visa and background checks and for recruiter searches |
| 3 | Paper size is **US Letter** | Switch to **A4** (the standard in India and UAE) |
| 4 | Body text is 10 pt with 0.4" top/bottom margins | Use 10.5–11 pt body and 0.5–0.6" margins. More readable once trimmed to 2 pages |
| 5 | Heading "CORE COMPETENCIES" | Rename to **"TECHNICAL SKILLS"**, which ATS maps reliably |
| 6 | Special characters such as `→` inside bullets | Replace with words ("to"). Older ATS (Taleo, some Workday set-ups) garble them |
| 7 | Skills include 9 programming languages, plus Selenium, JMeter, PHP, Kotlin, Dart, UDP, Hapi.js… | Keep only what you would happily be interviewed on. A long tail reads as junior and dilutes keyword weight |
| 8 | Jargon recruiters never search for: "Reviewer-Decision Provenance", "Evaluator History", "Trace Stores", "BLPOP", "Foundational Agents" | Keep one plain-language mention in a bullet and take them out of the skills list |
| 9 | Certifications are padded: "self-directed practitioner program" and "applied to production at Voizzit" are not certifications | Remove them. Add real credentials (see §6) |
| 10 | File name contains "India" / "UAE" | Name the files you send `Abdurahiman_Thommangadan_Senior_AI_Engineer.pdf` and similar. The recruiter sees the file name |
| 11 | File format | Send a **text-based PDF** to most portals and LinkedIn. Keep a **DOCX** for Naukri and older ATS that ask for Word |

---

## 4. Keyword gaps (add **only if true**)

High-frequency terms in 2026 job descriptions that are **missing or weak** in your resume:

**AI Engineer / AI Agent roles**
- **Exact phrases:** "AI Agents", "Agentic AI", "LLM Applications", "Retrieval-Augmented Generation (RAG)", "Generative AI"
- **Model and provider names:** OpenAI API / GPT-4o, Anthropic Claude, Google Gemini, Llama, Qwen, Mistral, **and the base model you fine-tuned**
- **Platforms:** Azure OpenAI, AWS Bedrock, Vertex AI. **Azure is especially valued in the UAE** (enterprise and government)
- **Agent ecosystem:** MCP (Model Context Protocol), CrewAI / AutoGen / OpenAI Agents SDK, LlamaIndex, function calling
- **Vector / retrieval:** pgvector, Pinecone, Chroma, Elasticsearch, hybrid search, re-ranking, embeddings
- **Evaluation and guardrails:** RAGAS, DeepEval, LLM-as-judge, guardrails, red-teaming
- **Serving:** vLLM, Ollama, TGI, quantisation, inference optimisation
- **Python data/ML:** PyTorch, Transformers, pandas

**Full Stack / MERN + AI roles**
- **Core stack:** "MERN", Next.js, TypeScript (in experience bullets, not just the skills list), Express.js, MongoDB
- **Frontend:** REST/GraphQL API design, responsive UI, state management, Tailwind
- **AI-in-product:** AI chat UI, streaming UI, AI SDK (Vercel AI SDK), "LLM integration"
- **DevOps:** Docker, Kubernetes, CI/CD, AWS. Move these into bullets where you actually did them
- **Engineering practice:** system design, microservices, unit/integration testing

---

## 5. Section-by-section rewrite direction

### Header
```
ABDURAHIMAN THOMMANGADAN
Senior Full Stack Engineer — MERN + Generative AI          ← (or "Senior AI Engineer — Generative AI & AI Agents")
Dubai, UAE | +971 55 819 2397 | abdurahmant7@gmail.com | linkedin.com/in/<custom> | github.com/abdurahmant7
UAE: Indian national · <Visa status> · Notice: <X> days          ← UAE versions only
India: Notice period <X> days · Open to Bangalore / Kochi / Remote  ← India versions only
```

### Summary (3–4 lines, numbers included). Drafts with placeholders:

**Full Stack / MERN + AI**
> Senior Full Stack Engineer with 7+ years building MERN and Node.js/NestJS products, including Samsung.com global eCommerce and Infosys enterprise SaaS. Since 2025 I have been shipping production Generative AI features: LangGraph agents, RAG and real-time LLM streaming UIs. I deliver end to end across React/TypeScript frontends, Node.js and FastAPI APIs, MongoDB/PostgreSQL, AWS and CI/CD. As Tech Lead at Voizzit (Dubai), I took Janal AI from architecture to production, cutting quotation turnaround from [X] to [Y].

**AI Engineer / AI Agent Engineer**
> Senior AI Engineer with 7+ years in software engineering, leading production Generative AI since 2025. My work covers multi-agent systems on LangGraph (ReAct, Reflexion, Plan-and-Execute), agentic RAG on Qdrant, LoRA/PEFT fine-tuning of a vision-language model, and LLMOps with Langfuse. As Tech Lead for Janal AI at Voizzit (Dubai), I [quantified result]. I bring a strong Python/FastAPI and Node.js backend foundation from Samsung SDS and Infosys.

### Experience — before and after examples (fill in the [ ] numbers)

| Before | After |
|---|---|
| Owned the end-to-end AI architecture for an AI-powered CAD/ERP platform serving aluminium windows & doors manufacturers — multimodal model selection, fine-tuning pipeline… | Led a [N]-engineer team building **Janal AI**, a Generative AI CAD/ERP platform that turns customer drawings into priced quotations for [N] aluminium manufacturers. I own the architecture from model selection to the React frontend |
| Led the LLM fine-tuning program for a custom fine-tuned multimodal LLM using LoRA / PEFT on RunPod GPU infrastructure… | Fine-tuned **[base model, e.g. Qwen2.5-VL-7B]** with LoRA/PEFT on RunPod GPUs using a 3-stage curriculum ([N]K JSONL samples). This raised drawing-to-quote extraction accuracy from [X]% to [Y]% over the base model |
| Built real-time agent streaming infrastructure using FastAPI, SSE, and Redis Streams — delivering token-level model output… | Built real-time agent streaming with FastAPI, SSE and Redis Streams, bringing time-to-first-token in the UI under [1 s] and quotation turnaround from [2 days] down to [15 min] |
| Implemented a human-in-the-loop review gate as a hard graph suspension backed by Redis BLPOP… | Designed a human-in-the-loop approval gate (LangGraph interrupt + Redis), giving **zero unapproved data writes** across [N] agent runs |
| Led backend development of multiple SaaS products: TechBuddy LMS…, VData… | Built the NestJS + PostgreSQL backend for VData, serving [X]M voter records with p95 [Y] ms APIs, ELK analytics and CI/CD |
| Engineered backend services for the Samsung.com global eCommerce platform using Node.js microservices… | Built Node.js microservices for Samsung.com global eCommerce handling [X] events/day over Kafka and RabbitMQ across [N] country storefronts |

**How the bullets are split per variant**

| Role | Full Stack / MERN + AI resume | AI Engineer resume |
|---|---|---|
| Voizzit — Tech Lead | 5 bullets (product delivery, React UI, APIs, AI features) | 7 bullets (agents, fine-tuning, RAG, LLMOps, streaming) |
| Voizzit — Senior Backend | 2 | 1 |
| Samsung SDS | 3 | 1–2 |
| Infosys | 2–3 | 1–2 |
| Kimball (IoT + ML anomaly detection) | 2 | 2 (lead with the ML / anomaly detection work) |
| Nucore | 2 (MERN + Angular) | 1 |

### Skills (grouped and ordered per variant)
- **Full Stack + AI:** Frontend, Backend, Databases, Cloud & DevOps, **AI/LLM integration**, Testing
- **AI Engineer:** Generative AI & Agents, LLM Fine-Tuning, RAG & Vector DBs, LLMOps & Evaluation, Python/APIs, supporting stack

### Education
B.Sc. Computer Science, Farook College (University of Calicut), 2016–2019. Fine as it is.
**UAE note:** make sure the degree certificate is **attested** (MoFA / embassy) if you don't already have this done. Some visa and employer processes ask for it.

---

## 6. Credentials that would strengthen both markets (optional, quick wins)

- **DeepLearning.AI short courses** (free, 1–2 hours each): *AI Agents in LangGraph*, *Functions, Tools and Agents with LangChain*, *Evaluating AI Agents*, *MCP*. These are real, verifiable lines on the resume and LinkedIn
- **Microsoft Azure AI Engineer Associate (AI-102)**: high signal for **UAE** enterprise and government employers
- **AWS Certified AI Practitioner / ML Engineer Associate**: a good signal for **India** product companies

---

## 7. India vs UAE: what differs

| | India | UAE |
|---|---|---|
| Main channels | **Naukri** (most important), LinkedIn, Instahyre, Wellfound (startups), Cutshort, Indeed | **LinkedIn** (most important), Bayt, NaukriGulf, GulfTalent, Indeed UAE, recruitment agencies |
| Personal details on CV | None (no DOB, marital status or photo) | **Nationality, visa status, notice period**; driving licence if held. Photo optional. Skip it for ATS |
| Must-state | Notice period, current and preferred locations, total experience | Visa status / transferable visa, availability, current location |
| Keyword tilt | SaaS / product scale, startups, MERN, Next.js | Enterprise and government, **Azure**, Arabic NLP (if any), fintech, smart-city |
| Paper | A4 | A4 |
| Salary | Not on resume (Naukri profile field only) | Not on resume |

---

## 8. Facts needed from you before rewriting (nothing will be invented)

1. **Where are you physically based right now: Dubai or Bangalore? What is your UAE visa status?** (The India copy says Bangalore, the UAE copy says Dubai, and your current employer is in Dubai.)
2. **Was "Senior Backend Engineer, Sep 2024 – Jan 2025" at Voizzit?** (That would be a promotion to Tech Lead.)
3. **Janal AI numbers:** team size you lead, number of customers or manufacturers, quote turnaround before and after, extraction accuracy, latency, cost per run, number of agent runs.
4. **Which base model** did you fine-tune, and how many training samples?
5. **Frontend work you personally built** (React / Three.js / Konva CAD UI? TV apps? Angular at Nucore?).
6. **Older roles:** any numbers (Samsung traffic or events, VData record counts, test coverage, performance gains, team size).
7. **Which keywords in §4 you actually used:** OpenAI / Claude / Gemini APIs, Azure / Bedrock, MCP, Next.js, pgvector / Pinecone, CrewAI, vLLM, PyTorch…
8. **GitHub:** any public AI or full-stack repositories worth linking or pinning?
9. **Notice period**, and preferred cities in India.

---

## 9. Plan from here

| Phase | Output | Status |
|---|---|---|
| 1 | Resume audit (this file) | ✅ Done |
| 1 | Folder structure for India / UAE × 2 roles | ✅ Done |
| 1 | LinkedIn, Naukri and Indeed audits | ⏳ Planned in `02_Profile_Update_Plan.md`; needs your sign-in |
| 2 | Master resume → `02_Master_Resume/content.js` (single source; `node build.js` regenerates all 4) | ✅ Done (24 Oct 2026) |
| 3 | 4 tailored resumes (DOCX + PDF, A4, 2 pages) → `India/…` and `UAE/…` | ✅ Done. Metrics still to add (§8) |
| 4 | LinkedIn, Naukri and Indeed update drafts (headline, About, skills, settings) | ✅ Drafted in `02_Profile_Update_Plan.md`. Apply after the audits |
| 4 | New UAE portal profiles: Bayt, NaukriGulf, GulfTalent | After phase 3 |
| 5 | Application tracker, target company lists, job alerts | Final |
