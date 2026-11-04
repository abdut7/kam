# Brief: scenario-first questions for one track (read fully)

You are adding to an interview-prep study page for one candidate. Read `CONTENT_FORMAT.md` in this folder first, especially "Scenario-first rules", "Extra block types" and the overlay rules.

## The candidate
AI Full Stack Engineer, 7+ years, interviewing now for senior roles in India and the UAE. Strong in Node.js (Express, NestJS), React, MongoDB, PostgreSQL, Redis, Kafka/RabbitMQ, Python (FastAPI, 4 years), LangGraph agents, MCP, RAG on Qdrant, vLLM inference, LoRA fine-tuning, Langfuse LLMOps, AWS, Docker, Kubernetes, GitHub Actions. Real projects: CADBEATER (AI estimator: LangGraph multi-agent, fine-tuned vision-language model on vLLM, Qdrant RAG, Redis Streams, SSE to a React/Three.js frontend, RBAC, human approval gates, Langfuse evals), VData (NestJS, clean architecture, TypeORM/PostgreSQL, near-instant search over 30 million records on AWS), Samsung.com eCommerce (Node.js microservices, Kafka, RabbitMQ, autoscaling for sale events), Solargraf (microservices behind an API gateway with gRPC), EMTAB (IoT anomaly detection pipeline). Do not invent facts about his projects; you may use them as realistic settings ("in a system like CADBEATER...").

## What the user asked for
"Every module should have interview-level questions, that is, scenario-based questions: what you did when these things came up... include all kinds of error cases and what you do when this problem arises... No need for any basic-level questions like 'What is that?'... In the learning content, mention the purpose and what problem this technology or tool is resolving."

## What you write
One overlay file (path given in your task). No `# ` H1. It contains:

1. A `## <exact existing section title>` heading for EVERY existing section listed in your task, each followed by only a `### Why it exists` block: 3-5 plain sentences. Say what problem this technology, tool or idea solves, what breaks or what people did before it, and the cost or trade-off it introduces. No jargon without a short explanation. Titles must match exactly (they merge into the existing sections).

2. A new section `## <Track> Project Scenarios [Scenarios]` (exact title given in your task):
   - framing blockquote (how interviewers run project and design scenarios for this area and what a senior answer shows)
   - `### Concepts you must understand`: 5-8 bullets on how to attack design and project scenarios in this area (the questions to ask first, the decisions that matter, the numbers to estimate)
   - 6 `### Q. ` blocks: realistic project or design situations ("You are building...", "Your team must migrate...", "A client needs... with constraint ...", "You inherit..."). Each answer covers requirements you would clarify, the design or plan, key decisions with trade-offs, risks, and what you would measure.
   - `### Practice`

3. A new section `## <Track> Incidents & Error Cases [Scenarios]` (exact title given in your task):
   - framing blockquote (structure for incident answers: clarify impact, contain, diagnose, fix, prevent)
   - `### Concepts you must understand`: 3-5 bullets plus a GFM table with columns "Symptom or error", "First check", "Likely causes", "Fix", 10-14 rows of real errors and symptoms for this area (exact error messages where they exist)
   - 8 `### Q. ` blocks, each naming a concrete symptom or error in the title ("After a deploy, ...", "Logs show `...`", "Users report ..."). Each answer: first moves in the Short answer; then in Deeper explanation the diagnosis steps in order with real commands, queries, dashboards or log searches, likely causes ranked, the fix, and how you prevent a repeat (alert, test, guardrail, runbook).
   - `### Practice` (include one "break it on purpose" exercise)

## Rules
- Question titles are situations, never "What is / Explain / Define / What is the difference". Grep the track's existing files first (named in your task) and do not duplicate an existing question; where an existing question covers the theory, build the scenario on top of it.
- Each Q block 200-380 words, four bold labels in order, code fences tagged, no em or en dashes, no HTML, straight quotes.
- Be technically exact. Use real commands and error texts you are sure of; if unsure of an exact message, describe the symptom instead of inventing text. No invented statistics.
- Run `node build/validate.mjs <your file>` from the `07_Interview_Prep` folder and fix anything it flags. Create no other files. Do not browse.
- Report back only: path, number of Why-it-exists blocks, number of questions in each new section, anything left out.
