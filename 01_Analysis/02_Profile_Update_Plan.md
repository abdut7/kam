# Profile Update Plan: LinkedIn, Naukri, Indeed and UAE Portals

**Status:** plan only. Nothing has been changed on any account yet. (Update 25 Oct 2026: Naukri and Indeed have since been changed; see `India/Naukri/Naukri_Audit_and_Changes.md`.)
**Title decision (25 Oct 2026):** the profile title everywhere is exactly **AI Full Stack Engineer** (no "Senior", no extra words in the title itself). Keep the existing AI Engineer resume as the second resume. The factual Voizzit job title ("Technical Lead — Full Stack & Generative AI") does not change. Use this wording on LinkedIn, Bayt, NaukriGulf, GulfTalent and HiringCafe too.
**Source of truth:** the new resumes in `India/` and `UAE/`. Every profile must match them exactly (titles, dates, company names, CADBEATER), because recruiters cross-check.

---

## 0. Order of work

| # | Platform | Market | Why this order |
|---|---|---|---|
| 1 | **LinkedIn** | Both | Recruiters in both markets check it, and it drives most UAE hiring |
| 2 | **Naukri** | India | Main recruiter search tool in India |
| 3 | **Indeed** | Both (one account, India + UAE sites) | Quick, mostly a resume upload and preferences |
| 4 | **Bayt, NaukriGulf, GulfTalent** (new) | UAE | Main UAE portals; create profiles with the UAE resumes |

For each platform: (a) audit what's there now, then (b) apply the drafts below, adjusted to what the audit finds.

---

## 1. LinkedIn (one profile for both markets and both roles)

### Audit checklist (when you sign in to the browser pane)
- [ ] Headline, About, location, open-to-work settings
- [ ] Experience entries vs. resume: titles, dates, Voizzit's two roles, "Janal AI" still mentioned?
- [ ] Skills (count, top skills pinned), endorsements
- [ ] Featured section, certifications, education
- [ ] Custom URL, profile photo, banner
- [ ] Recent activity (posts in the last 90 days)

### Planned changes (drafts)

**Custom URL:** change `…/abdurahiman-thommangadan-995314168` to `linkedin.com/in/abdurahiman-thommangadan` (or the nearest available). Then update `PERSON.linkedinUrl` in `02_Master_Resume/content.js` and run `node build.js` to refresh all 4 resumes.

**Headline** (max 220 characters; covers both roles):
> AI Full Stack Engineer | Tech Lead @ Voizzit | Node.js, React, Python | Generative AI, AI Agents, LangGraph, MCP, LLMOps | System Design

**About** (draft):
> I build products end to end, from the React frontend to the AI agents behind it.
>
> For 7+ years I've shipped web platforms on the MERN stack, NestJS and PostgreSQL, including enterprise SaaS at Infosys and Industry 4.0 IoT at Kimball Electronics. Since 2025 I've been Tech Lead at Voizzit, leading CADBEATER: a multi-agent AI estimation system for fenestration and facade projects that generates cost estimates and CAD drawings while reducing manual estimating work from 4 hours to 10 minutes. I also built VData voter search across 30 million records with near-instant lookup and Samsung.com microservices at Samsung SDS that autoscale for high-traffic sales events.
>
> What I work on at CADBEATER:
> • Multi-agent systems on LangGraph: ReAct, Reflexion and Plan-and-Execute agents
> • Building the React + Three.js CAD frontend with Redux Toolkit, TanStack Query and real-time SSE streaming
> • Agentic RAG on Qdrant with validated, structured outputs
> • Human-in-the-loop approval gates, so AI never changes business data unchecked
> • Real-time LLM streaming (FastAPI, SSE, Redis Streams) into a React + Three.js CAD interface
> • LLMOps and observability with Langfuse
>
> Stack: React, Node.js, Express, NestJS, Python, FastAPI, MongoDB, PostgreSQL, Redis, Kafka, LangGraph, LangChain, Hugging Face, AWS, Docker.
>
> abdurahmant7@gmail.com

(Optional last line: "Open to AI Full Stack Engineer (MERN + AI) and AI Engineer roles in the UAE and India." Skip it if your current employer shouldn't see it; use the recruiter-only setting below instead.)

**Experience:** mirror the resume.
- Voizzit as one company with two positions: *Senior Backend Engineer* (Sep 2024 – Jan 2025), then *Tech Lead — Generative AI & Agent Platform* (Jan 2025 – Present). LinkedIn shows this as a promotion.
- Replace every "Janal AI" with **CADBEATER**.
- Paste 3–5 bullets per role from the AI Engineer resume, and add skills to each position.

**Open to Work:** set to **recruiters only**, so it isn't public.
- Job titles: AI Full Stack Engineer, MERN Stack Developer, AI Engineer, Generative AI Engineer, Senior Software Engineer
- Locations: Dubai, Abu Dhabi, Bangalore, plus Remote
- Types: full-time; on-site / hybrid / remote

**Location:** Dubai, UAE (matches "UAE Resident"). Indian recruiters will still find you through the Open to Work locations.

**Skills:** pin as top skills **Generative AI, Node.js, React.js, LangGraph, MERN Stack**. Then add up to about 50 from the two resumes' skill lists.

**Featured:** a CADBEATER post or demo video (non-confidential), plus an architecture write-up of multi-agent + human-in-the-loop design.

**Certifications:** Machine Learning Specialization (DeepLearning.AI), Deep Learning (Codebasics), IoT (NPTEL), with credential links.

**Activity:** 1 post per week on agentic AI or full-stack lessons from CADBEATER. Recruiters favour active profiles.

---

## 2. Naukri (India)

### Audit checklist
- [ ] Resume headline, profile summary, key skills
- [ ] Employment entries and designations
- [ ] Notice period, current/expected CTC, preferred locations
- [ ] Attached resume (old version?), last-updated date, profile completeness %

### Planned changes (drafts)

**Resume headline** (max 250 characters):
> AI Full Stack Engineer | 7.5 Yrs | Technical Lead | Node.js, React, Python | Generative AI, AI Agents, LangGraph, MCP, OpenAI, Anthropic, LLMOps, Inference Engineering | System Design | Ex-Samsung SDS, Infosys

**Key skills** (most important first):
Generative AI, AI Agents, LangGraph, LangChain, MCP, OpenAI, Anthropic, RAG, LLM, LLMOps, vLLM, LLM Fine-Tuning, Node.js, NestJS, Express.js, Python, FastAPI, System Design, Clean Architecture, Distributed Systems, Microservices, MongoDB, React.js, MERN Stack, TypeScript, REST API, Kafka, RabbitMQ, Redis, PostgreSQL, AWS, Docker, Kubernetes, CI/CD, System Design, Team Leading

**Profile summary** (draft, under 1,000 characters):
> AI Full Stack Engineer with 7.5 years building MERN, NestJS and PostgreSQL platforms, including enterprise SaaS at Infosys and eCommerce microservices at Samsung SDS. Technical Lead at Voizzit since 2025, delivering CADBEATER across a React + Three.js frontend, FastAPI, MongoDB and LangGraph. Its AI estimator reduced manual estimating work from 4 hours to 10 minutes. I also built VData search across 30 million voter records with near-instant lookup and implemented autoscaling for Samsung.com microservices during sales events. Strong in React, Node.js, Python, RAG, agents, AWS, Kafka and CI/CD.

**Employment:** Voizzit with both designations. Company names and dates must match the resume.
**Projects section:** CADBEATER, VData, Solargraf, EMTAB (short descriptions from the resume).
**Resume to upload:** `India/Resume_FullStack_MERN_AI/…pdf`, your preferred role. The headline and key skills already cover the AI roles. For AI-only jobs, attach the AI Engineer resume when applying.
**Fields to set:** notice period **Immediate (15 days or less)**, current CTC **₹24 LPA**, expected CTC **₹28 LPA**, preferred locations (Bangalore + others? still to confirm).
**Habit:** make a small edit (headline or a skill) every 2–3 days. Naukri ranks recently updated profiles higher in recruiter searches.

---

## 3. Indeed (one account: indeed.co.in + ae.indeed.com)

### Audit checklist
- [ ] Profile resume (which file?), visibility (public/private)
- [ ] Job title preferences, locations, salary preference, "ready to work" status

### Planned changes
- **Profile resume:** Full Stack MERN + AI resume. When applying, upload the role- and market-specific file each time (Indeed allows this per application).
- **Desired titles:** AI Full Stack Engineer, MERN Stack Developer, AI Engineer, Generative AI Engineer
- **Locations:** Bangalore, Dubai, Abu Dhabi, Remote
- **Visibility:** searchable by employers
- **Job alerts:** set up on both country sites (see §5)

---

## 4. UAE portals (new profiles)

| Portal | Resume to upload | Fields to fill |
|---|---|---|
| **Bayt.com** | UAE Full Stack MERN + AI | Visa status (UAE Resident), nationality, notice period (Immediate), expected salary (AED), target titles |
| **NaukriGulf** | UAE Full Stack MERN + AI | Same headline and key skills as Naukri India, with location Dubai |
| **GulfTalent** | UAE AI Engineer | Same fields |

Use the AI Engineer resume for AI-only roles on any portal.

---

## 5. Job alerts (set up after profiles are updated)

| Search | India | UAE |
|---|---|---|
| "MERN stack" + "AI" / "LLM" | Naukri, LinkedIn, Indeed | LinkedIn, Bayt, Indeed UAE |
| "Full Stack Engineer" + "Generative AI" | Same | Same |
| "AI Engineer" / "Generative AI Engineer" / "AI Agent" / "LangGraph" | Same | Same + GulfTalent |

---

## 6. Open items from you (improve resumes and profiles)

1. **Numbers for CADBEATER** (the biggest upgrade): team size, customers, quote turnaround before/after, accuracy, latency, number of runs. Each one replaces a vaguer phrase in `content.js`.
2. **Base model fine-tuned** (e.g. Qwen2.5-VL / Llama Vision) and dataset size.
3. **GitHub:** the old link (`github.com/abdurahmant7`) is broken, so it was removed. Send the right username to add it back.
4. ~~Notice period~~ Immediate joiner. ~~CTC~~ current ₹24 LPA, expected ₹28 LPA. Still open: **nationality / visa details** for UAE portals, **UAE expected salary (AED)**, **preferred Indian cities**.
5. **Keywords you've genuinely used but aren't listed yet:** OpenAI / Claude / Gemini APIs, Azure OpenAI, AWS Bedrock, MCP, Next.js, pgvector, CrewAI, vLLM, PyTorch.
6. **CADBEATER:** confirm it's the renamed Janal AI (same project). If it's a different project, send a short description and it becomes its own entry.
