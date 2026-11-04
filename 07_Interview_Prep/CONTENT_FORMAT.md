# Content format spec for the Interview Prep Atlas (read fully before writing)

## Who this is for
A software engineer with ~5 years of experience: MERN stack (Node.js/Express, React, MongoDB), ~4 years of Python, Postgres/Redis exposure, has shipped LLM/agent features (tool calling, MCP, RAG) in production, some GCP exposure, little formal AWS/Kubernetes depth. Target role: **AI Full Stack Engineer / AI Engineer** (senior / SDE-3 level) in India and the UAE. Interviews are happening NOW, so every topic must be written to help them (a) understand the concept properly and (b) answer confidently in an interview, including follow-ups.

Tone: a sharp senior engineer tutoring a peer. Plain English, concrete, no fluff, no motivational filler. Explain the "why" and the failure modes, not just definitions. Prefer real production examples (Node.js/Express, Postgres, MongoDB, Redis, Kafka, Python/FastAPI, OpenAI/Anthropic APIs) over abstract ones.

## File format (strict, a renderer depends on it)
Write GitHub-flavored Markdown. Structure:

```
# <Track title>

> One short paragraph: what this track covers and why it matters for an AI Full Stack Engineer interview.

## <Section title>

> Optional one-paragraph framing: how interviewers probe this section, what a weak vs strong answer looks like.

### Concepts you must understand
- Bullet list of the 5-10 core ideas, each one line, each a complete thought (not just a keyword).

### Q. <Interview question, written as the interviewer would say it>
**Short answer (45 seconds):** 2-4 sentences you could say out loud.

**Deeper explanation:** 1-3 short paragraphs. Use a code block (with a language tag) or a small table or an ASCII diagram inside a ```text fence when it makes the mechanism clearer. Name real tools/commands (EXPLAIN ANALYZE, SET TRANSACTION ISOLATION LEVEL, redis SET NX PX, kubectl rollout, etc.).

**Follow-ups they will ask:**
- 2-4 likely follow-up questions, each with a one-line answer after a colon.

**Mistakes to avoid:**
- 1-3 bullets: the wrong/weak answers and why they fail.

### Q. <next question> ...

### Practice
- 2-4 concrete hands-on exercises (what to build/run/measure) that make this section stick, plus one "say it out loud" rehearsal prompt.
```

Rules:
- `#` exactly once (the track title). `##` for sections. `###` only for: `Concepts you must understand`, `Q. ...` question blocks, and `Practice`. Nothing else at H3. No H4+.
- Every question heading MUST start with `### Q. ` (capital Q, period, space).
- The bold labels inside a question block must be exactly: `**Short answer (45 seconds):**`, `**Deeper explanation:**`, `**Follow-ups they will ask:**`, `**Mistakes to avoid:**`. Keep that order. All four are required in every question block.
- Length per question: 180-350 words total. Concepts list: 5-10 bullets. Aim for depth over breadth: a senior answer, not a glossary.
- Code blocks always carry a language tag: ```sql, ```js, ```ts, ```python, ```bash, ```yaml, ```text, ```json, ```dockerfile. Keep code short (3-25 lines) and correct.
- Allowed Markdown: headings, paragraphs, bold, italics, inline code, fenced code, bullet and numbered lists, GFM tables, blockquotes, links. NOT allowed: raw HTML, images, mermaid, footnotes, emoji, horizontal rules.
- Punctuation: no em dashes or en dashes anywhere (use a comma, a colon, or a new sentence). Use straight quotes.
- Facts: be precise. If you are not sure of a number, version, or default, leave it out rather than guess. Do not invent benchmark figures. Note vendor differences where they matter (Postgres vs MySQL, Kafka vs RabbitMQ).
- Do not write "as an AI" or refer to this document, the reader's resume, or interview dates. Do not include a closing summary section.
- Write the complete file in one go to the exact output path you were given. Do not create other files. Do not stop early; the file must contain every section and every question listed in your brief.

## Extra block types (added 2026-10-30, for simple explainers and overlays)

- `### In plain words` : a short, very simple explanation (3-6 sentences, no jargon or jargon explained inline) placed at the top of a section. Use an everyday analogy.
- `### From your saved posts` : a short bullet list naming which saved Instagram posts (creator handle + one-line topic) informed the section, plus any verified external links.
- `### C. <Concept name>` : a concept card, the simple counterpart of a question block. Required bold labels, in order:
  - `**In one line:**` one plain sentence a non-expert understands.
  - `**Think of it like:**` an everyday analogy in 1-2 sentences.
  - `**Example:**` one concrete, real example (a tool, a number, a scenario) in 1-3 sentences.
  - `**Say it in an interview:**` 2-3 sentences that sound senior and precise.
  - `**Go deeper:**` optional, names the track and section to read next, e.g. `Inference track, section "Inference Fundamentals".`
  Length: 70-140 words per card. Concept-card sections do not need Concepts/Practice blocks.
- Section level tags: append ` [Basics]`, ` [Core]`, ` [Advanced]`, ` [Start here]` or ` [New]` to a `## ` heading. `[Start here]` sections placed through an overlay are moved to the start of the track.
- Overlay files live in `content/overlays/NN-<name>.md` (same NN prefix as the track). A `## ` section whose title exactly matches an existing section is merged into it (In plain words and From your saved posts blocks go to the top, everything else goes before Practice). A section with a new title becomes a new section. Overlay files have no `# ` H1.

## Architecture blocks (added 2026-11-01)

- `### Walkthrough: <title>` : a numbered list (6-10 steps) that follows one request or one token through the system, step by step, using the same component names as the diagram. One or two short sentences per step.
- `### Diagram: <title>` : contains one fenced ```svg block (hand-written inline SVG, no <style> or <script>, colored only with the page classes bx, bx2, bxa, bxo, bxw, zone, t, tb, tm, ta, to, tmono, ln, lnm, lna, lno, dash, mk, mkm, mka, mko) followed by a 1-3 sentence markdown caption stating what the picture shows. Diagram blocks are placed at the top of the section after In plain words. Diagrams are authored by the editor, not by section writers.

## Scenario-first rules (added 2026-11-02, user requirement)

The user does not want basic "What is X?" interview questions. Interview questions must be scenario-based, project-based or failure-case-based: what you would do, decide, build, debug or fix in a concrete situation.
- Write every `### Q. ` title as a situation an interviewer would pose, for example "Checkout latency doubled right after a deploy. Walk me through the first 30 minutes.", "You are building X for Y with constraint Z. How do you design it?", "Users report duplicate charges. What do you check and how do you stop it?". Never "What is...", "Explain...", "Define...", "What is the difference between...".
- Answer with the same four labels, used this way: **Short answer (45 seconds):** your first moves and the direction you would take; **Deeper explanation:** the steps in order (clarify, contain, diagnose with real commands, metrics and logs, likely causes ranked, fix, prevent; or for design: requirements, decisions, trade-offs, what you would measure); **Follow-ups they will ask:** the twists an interviewer adds ("what if it is only one region?"); **Mistakes to avoid:** what weak candidates do.
- Failure-case questions must name the concrete error or symptom (an error message, a metric shape, a user report) and walk through diagnosis and the fix.
- `### Why it exists` : 3-5 plain sentences at the top of a section: the problem this technology, tool or idea solves, what people did before or what breaks without it, and the cost or trade-off it brings. Definitions belong here and in Learn first, never in interview questions.
- Section tag `[Scenarios]` marks sections made only of scenario questions.
