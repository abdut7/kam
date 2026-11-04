// MASTER RESUME CONTENT — single source of truth for all 4 resumes.
// Edit facts here, then run `node build.js` to regenerate India + UAE × Full Stack + AI Engineer (DOCX + PDF).
// Rule: no invented numbers. Add metrics here only once they are confirmed.
// Skills order (user preference): Generative AI / agents first, then backend, databases, frontend last.
// Voizzit title must match Naukri: "Technical Lead — Full Stack & Generative AI".

const PERSON = {
  name: 'ABDURAHIMAN THOMMANGADAN',
  email: 'abdurahmant7@gmail.com',
  linkedinUrl: 'https://www.linkedin.com/in/abdurahiman-thommangadan-995314168',
  linkedinLabel: 'LinkedIn',
};

const MARKETS = {
  india: {
    folder: 'India',
    location: 'Bangalore, India',
    phone: '+91 79073 82644',
    residency: null,
    summaryLead: '',
  },
  uae: {
    folder: 'UAE',
    location: 'Dubai, UAE',
    phone: '+971 55 819 2397',
    residency: 'UAE Resident',
    summaryLead: 'UAE-based ',
  },
};

// CADBEATER — one-line description reused across summaries and bullets.
const CADBEATER = 'an AI estimator system for fenestration and facade projects that generates cost estimates, bills of quantities (BOQ), bills of materials (BOM) and CAD drawings from requirements, joinery details or floor plans';
const CADBEATER_PROJECT = { name: 'CADBEATER' };
const VOIZZIT_LEAD_TITLE = 'Technical Lead — Full Stack & Generative AI';

const ARCHITECTURE_SKILLS = 'Solution Architecture, System Design, Clean (Onion) Architecture, SOLID & Design Patterns, Test-Driven Development (TDD), Behavior-Driven Development (BDD), Microservices, Event-Driven Architecture (Kafka, RabbitMQ), Distributed Systems (MongoDB, PostgreSQL), Horizontal & Vertical Scaling, Caching (Redis), API Gateway, Asynchronous Workers & Queues, High Availability';
const SECURITY_SKILLS = 'Role-Based Access Control (RBAC), JWT & OAuth 2.0 Authentication, OWASP Top 10, Secure API Design, Rate Limiting, Encryption in Transit & at Rest, Audit Logging';
const ORM_ODM = 'ORM / ODM (Sequelize, TypeORM, Mongoose)';

// ---------------------------------------------------------------------------
// ROLE 1 (preferred): AI Full Stack Engineer (user-chosen title since 2026-10-25, used everywhere)
// ---------------------------------------------------------------------------
const fullstack = {
  key: 'fullstack',
  folder: 'Resume_FullStack_MERN_AI',
  fileBase: 'Abdurahiman_Thommangadan_AI_Full_Stack_Engineer',
  docTitle: 'AI Full Stack Engineer',
  headline: 'AI Full Stack Engineer  |  Node.js, React, Generative AI & AI Agents',
  summary: (m) =>
    `${m.summaryLead}AI Full Stack Engineer and solution architect with 7+ years in Node.js and React, building highly ` +
    'scalable, secure products from scratch on MERN, NestJS, MongoDB and PostgreSQL, including Samsung.com global eCommerce ' +
    '(Samsung SDS) and enterprise SaaS (Infosys). Technical Lead for full stack and Generative AI at Voizzit since 2024, ' +
    'delivering CADBEATER, an AI estimator system for fenestration and facade projects, end to end: LangGraph agents, OpenAI, ' +
    'Anthropic and OpenRouter LLMs, vLLM inference, LLMOps, FastAPI and React. Strong in system design, Clean (Onion) ' +
    'Architecture, distributed and event-driven systems, scaling, RBAC security, AWS, CI/CD and AI-driven SDLC team leadership.',
  skills: [
    ['Generative AI & Agents', 'LangGraph, LangChain, Multi-Agent Systems, AI Agent Development, Model Context Protocol (MCP), Retrieval-Augmented Generation (RAG), Context & Memory Management, Prompt Engineering, Large Language Models (LLMs), LLM Inference Engineering'],
    ['LLMs, Inference & LLMOps', 'OpenAI, Anthropic (Claude), OpenRouter, Hugging Face, Structured Outputs (Constrained Decoding), vLLM, Quantization, Model Routing, Response Caching, Langfuse, Evaluation Pipelines, Cost & Latency Monitoring'],
    ['Backend', `Node.js, Express.js, NestJS, Python, FastAPI, Django, REST APIs, gRPC, WebSocket, Server-Sent Events (SSE), ${ORM_ODM}`],
    ['Architecture & System Design', ARCHITECTURE_SKILLS],
    ['Security', SECURITY_SKILLS],
    ['Databases & Messaging', 'MongoDB, PostgreSQL, MySQL, Redis, Qdrant (vector database), Apache Kafka, RabbitMQ'],
    ['Frontend & Mobile', 'React.js, Redux Toolkit, TanStack Query, JavaScript (ES6+), TypeScript, HTML5, CSS3, Tailwind CSS, Three.js, Angular, Flutter (Android, iOS, Web), React Native'],
    ['Cloud & DevOps', 'AWS (EC2, S3, SQS), Docker, Kubernetes, GitHub Actions, CI/CD, ELK Stack, RunPod (GPU)'],
    ['AI-Driven SDLC & Testing', 'Agentic Coding (Claude Code), Custom Module-Level & Project-Level Agent Skills, AI-Assisted Code Review, AI Development Lifecycle, Jest, Supertest, Playwright'],
    ['Languages', 'JavaScript, TypeScript, Python, Dart, SQL'],
  ],
  experience: [
    {
      company: 'Voizzit Information Technology LLC',
      location: 'Dubai, UAE',
      dates: 'Sep 2024 – Present',
      roles: [
        {
          title: VOIZZIT_LEAD_TITLE,
          project: CADBEATER_PROJECT,
          bullets: [
            'Led CADBEATER from requirements through production across the multi-agent AI backend, FastAPI services, MongoDB data layer and React frontend. Its estimator generates cost estimates, bills of quantities (BOQ), bills of materials (BOM) and CAD drawings from requirements, joinery details or floor plans, reducing manual estimating effort from four hours to ten minutes (about 96% less time).',
            'Built the multi-agent AI layer: LangGraph agents (ReAct, Reflexion, Plan-and-Execute), RAG over Qdrant, Model Context Protocol (MCP) tool integration, and short- and long-term agent memory with context compression.',
            'Integrated LLMs from OpenAI, Anthropic (Claude) and OpenRouter alongside a self-hosted vision-language model served with vLLM, with task-based model routing, caching and structured outputs through constrained decoding.',
            'Engineered for scale and reliability: event-driven FastAPI services on Redis Streams, GPU-isolated inference workers, and real-time SSE streaming to the React CAD frontend (Redux Toolkit, TanStack Query, Three.js).',
            'Secured the platform with role-based access control (RBAC), role- and team-scoped data access, audit logging and human-in-the-loop approval gates.',
            'Owned quality and LLMOps: Langfuse tracing, prompt versioning, evaluation pipelines, cost and latency monitoring, code reviews and an AI-driven SDLC (agentic coding with Claude Code, custom module- and project-level agent skills), and authored the architecture reference adopted across engineering and product.',
          ],
        },
        {
          title: 'Senior Backend Engineer — SaaS Platforms',
          bullets: [
            'Architected VData, a distributed voter-data platform, on NestJS with Clean (Onion) Architecture, separating domain, application and infrastructure layers, with TypeORM over PostgreSQL.',
            'Scaled VData horizontally and vertically on AWS to enable fast, near-instant search across 30 million voter records; supported the platform with ELK analytics, CI/CD and automated API test suites.',
            'Built TechBuddy LMS (admin CMS, student web, React Native TV apps) on NestJS and PostgreSQL, with AI-generated quizzes, offline content export, secure authentication and rate limiting.',
          ],
        },
        {
          title: 'Project: AutoFleet — Car Rental Booking & ERP Platform',
          bullets: [
            'Built a car rental booking and ERP platform covering the end-to-end booking flow, fleet management, reservations, CRM and HRM modules.',
            'Delivered a cross-platform Flutter mobile app for Android, iOS and web, and handled release management and ongoing maintenance on the Google Play Store and Apple App Store.',
            'Built the Node.js and React.js web platform on MongoDB and AWS, with Playwright-based automation for third-party integrations.',
          ],
          stack: 'Node.js, React.js, Flutter (Dart), MongoDB, AWS, Playwright',
        },
      ],
    },
    {
      company: 'Samsung SDS India',
      location: 'Chennai, India',
      dates: 'Feb 2024 – Sep 2024',
      roles: [
        {
          title: 'Backend Engineer — Samsung.com Global eCommerce',
          bullets: [
            'Built and operated independently deployable Node.js microservices for Samsung.com global eCommerce, supporting autoscaling during high-traffic sales events; used Kafka and RabbitMQ for event processing and PostgreSQL for transactional data.',
            'Built secure logistics and user-interaction APIs with Elasticsearch logging and monitoring for end-to-end traceability.',
          ],
        },
      ],
    },
    {
      company: 'Infosys Limited',
      location: 'Bangalore, India',
      dates: 'Jun 2022 – Feb 2024',
      roles: [
        {
          title: 'Associate Consultant — Enterprise SaaS',
          bullets: [
            'Delivered full-stack features and high-availability microservices for Solargraf, a solar-design SaaS with 3D design and financial modules (Node.js, Express.js, React.js, Sequelize, PostgreSQL).',
            'Built and tested microservices behind an API Gateway with gRPC, and took part in architecture reviews with cross-functional product teams.',
          ],
        },
      ],
    },
    {
      company: 'Kimball Electronics India Pvt. Ltd.',
      location: 'Trivandrum, India',
      dates: 'Nov 2020 – Jun 2022',
      roles: [
        {
          title: 'Software Engineer — Industrial IoT',
          bullets: [
            'Built the Alerting, Visualization and Data Acquisition modules of EMTAB, an Industry 4.0 IoT predictive-maintenance platform (Node.js, React.js, Express.js, Sequelize, MongoDB, MySQL).',
            'Integrated machine-learning anomaly detection into real-time shop-floor sensor pipelines, and wrote Playwright test automation.',
          ],
        },
      ],
    },
    {
      company: 'Nucore Software Solutions',
      location: 'Calicut, India',
      dates: 'Apr 2019 – Nov 2020',
      roles: [
        {
          title: 'Backend Developer — Travel Accounting SaaS',
          bullets: [
            'Designed and built the ERP accounting engine, microservice APIs and business logic for TRAACS, a back-office SaaS for travel agencies (Node.js, Express.js, Angular, PostgreSQL, MongoDB).',
          ],
        },
      ],
    },
  ],
  projects: [],
  certifications: [
    'Machine Learning Specialization — DeepLearning.AI (Andrew Ng)',
    'Deep Learning — Codebasics',
  ],
};

// ---------------------------------------------------------------------------
// ROLE 2: AI Engineer / Generative AI / AI Agent Engineer
// ---------------------------------------------------------------------------
const ai = {
  key: 'ai',
  folder: 'Resume_AI_Engineer',
  fileBase: 'Abdurahiman_Thommangadan_Senior_AI_Engineer',
  docTitle: 'Senior AI Engineer (Generative AI & AI Agents)',
  headline: 'Senior AI Engineer  |  Generative AI, Multi-Agent Systems, LLMOps, Inference Engineering, RAG',
  summary: (m) =>
    `${m.summaryLead}Senior AI Engineer with 7+ years of software engineering experience, leading production Generative AI since 2025. ` +
    `Technical Lead at Voizzit, where I architected CADBEATER from scratch: ${CADBEATER}. Hands-on across the modern AI stack: ` +
    'LangGraph multi-agent systems with MCP, OpenAI, Anthropic and OpenRouter LLMs, agent memory, agentic RAG, LoRA/PEFT ' +
    'fine-tuning, vLLM inference with quantization and constrained decoding, and Langfuse LLMOps, backed by strong system design ' +
    'and distributed-systems experience (Clean (Onion) Architecture, horizontal and vertical scaling, RBAC security).',
  skills: [
    ['Generative AI & Agents', 'LangGraph, LangChain, Multi-Agent Systems, AI Agent Development, Agentic AI, Retrieval-Augmented Generation (RAG), Model Context Protocol (MCP), Tool Calling, ReAct, Reflexion, Plan-and-Execute, Human-in-the-Loop, Prompt Engineering, Agentic RAG, Qdrant, Vector Embeddings, Semantic Search'],
    ['LLMs & Structured Decoding', 'OpenAI (GPT), Anthropic (Claude), OpenRouter, Open-Weight Models (Hugging Face), Structured Outputs, Constrained / Guided Decoding (JSON Schema)'],
    ['Context & Memory', 'Context Engineering, Agent Memory (short-term and long-term), LangGraph Checkpointing, Context Compression, Token Budgeting'],
    ['Inference Engineering', 'vLLM, Model Serving, Continuous Batching, KV Cache, Quantization (4-bit / 8-bit), Model Routing, Prompt & Response Caching, GPU Inference (RunPod), Token Streaming (SSE)'],
    ['LLMOps & Evaluation', 'Langfuse, LLM Tracing, Prompt Versioning, Evaluation Pipelines, Regression Testing, Model Registry (Hugging Face), Model Versioning & Rollback, Cost & Latency Monitoring, Guardrails'],
    ['Fine-Tuning & ML', 'LoRA, QLoRA, PEFT, Hugging Face Transformers, Vision-Language Models (VLM), Multimodal LLMs, Curriculum Learning, Dataset Curation, Deep Learning, Anomaly Detection'],
    ['AI-Driven SDLC', 'Agentic Coding (Claude Code), Custom Module-Level & Project-Level Agent Skills, AI-Assisted Code Review, AI Development Lifecycle (data, fine-tuning, evaluation, deployment, monitoring)'],
    ['Backend', `Python, FastAPI, Django, Node.js, NestJS, Express.js, REST APIs, WebSocket, gRPC, ${ORM_ODM}`],
    ['Architecture & System Design', ARCHITECTURE_SKILLS],
    ['Security', SECURITY_SKILLS],
    ['Databases & Messaging', 'MongoDB, PostgreSQL, Redis, Qdrant, Apache Kafka, RabbitMQ'],
    ['Cloud & DevOps', 'AWS (EC2, S3, SQS), Docker, Kubernetes, GitHub Actions, CI/CD, ELK Stack'],
    ['Frontend & Mobile', 'React.js, TypeScript, Three.js, Flutter'],
  ],
  experience: [
    {
      company: 'Voizzit Information Technology LLC',
      location: 'Dubai, UAE',
      dates: 'Sep 2024 – Present',
      roles: [
        {
          title: VOIZZIT_LEAD_TITLE,
          project: CADBEATER_PROJECT,
          bullets: [
            `Architected CADBEATER from requirements through production with a modular, horizontally scalable and secure design: ${CADBEATER}. The estimator reduced manual estimating effort from four hours to ten minutes (about 96% less time).`,
            'Architected the LangGraph multi-agent system: a ReAct agent for contextual Q&A, a Reflexion agent with self-critique loops for vision-heavy requirement extraction, and a Plan-and-Execute agent for estimate generation behind mandatory human review, with tools and data sources integrated through Model Context Protocol (MCP).',
            'Integrated LLMs from OpenAI, Anthropic (Claude) and OpenRouter, routing each task between these APIs, the self-hosted fine-tuned model and deterministic code, with prompt and response caching.',
            'Engineered the inference layer: served the fine-tuned vision-language model with vLLM (continuous batching, KV cache) on RunPod GPUs, with 4-bit/8-bit quantization and structured outputs enforced through constrained (guided) decoding against JSON schemas.',
            'Fine-tuned a custom multimodal vision-language model with LoRA/PEFT on a three-stage curriculum (vision extraction, then pricing logic, then end-to-end drawing-to-estimate), with checkpoints versioned in a Hugging Face model registry for rollout and rollback.',
            'Built LLMOps on Langfuse: end-to-end tracing, prompt versioning, automated evaluation pipelines (test datasets, scoring, regression checks) gating every prompt and model release, and token-cost and latency monitoring per estimate.',
            'Designed agent context and memory management: short-term state persisted with LangGraph checkpointers so runs resume after human review, long-term memory of past projects and estimates, and context compression with per-node token budgets.',
            'Built agentic RAG on Qdrant and real-time token streaming (FastAPI, SSE, Redis Streams), and secured the platform with role-based access control (RBAC), role- and team-scoped retrieval, audit logging and human-in-the-loop approval gates.',
            'Drove an AI-driven SDLC for the team: agentic coding with Claude Code, custom agent skills for each project module plus shared project-level skills, and AI-assisted code review; authored the system architecture reference.',
          ],
        },
        {
          title: 'Senior Backend Engineer — SaaS Platforms',
          bullets: [
            'Architected VData, a distributed voter-data platform on NestJS with Clean (Onion) Architecture and TypeORM, then scaled AWS search horizontally and vertically for fast, near-instant lookup across 30 million voter records.',
            'Built TechBuddy LMS (NestJS, PostgreSQL, React Native TV apps) with AI-generated quiz delivery.',
          ],
        },
        {
          title: 'Project: AutoFleet — Car Rental Booking & ERP Platform',
          bullets: [
            'Built a car rental booking and ERP platform (booking flow, fleet, CRM and HRM modules) with a Flutter mobile app for Android, iOS and web, released and maintained on the Play Store and App Store.',
          ],
          stack: 'Node.js, React.js, Flutter (Dart), MongoDB, AWS',
        },
      ],
    },
    {
      company: 'Samsung SDS India',
      location: 'Chennai, India',
      dates: 'Feb 2024 – Sep 2024',
      roles: [
        {
          title: 'Backend Engineer — Samsung.com Global eCommerce',
          bullets: [
            'Built and operated independently deployable Node.js microservices for Samsung.com global eCommerce, supporting autoscaling during high-traffic sales events; used Kafka and RabbitMQ for event processing and PostgreSQL for transactional data.',
            'Built secure logistics and user-interaction APIs with Elasticsearch logging and monitoring.',
          ],
        },
      ],
    },
    {
      company: 'Infosys Limited',
      location: 'Bangalore, India',
      dates: 'Jun 2022 – Feb 2024',
      roles: [
        {
          title: 'Associate Consultant — Enterprise SaaS',
          bullets: [
            'Delivered high-availability microservices for Solargraf, a solar-design SaaS with 3D design and financial-calculation modules, behind an API Gateway with gRPC.',
          ],
        },
      ],
    },
    {
      company: 'Kimball Electronics India Pvt. Ltd.',
      location: 'Trivandrum, India',
      dates: 'Nov 2020 – Jun 2022',
      roles: [
        {
          title: 'Software Engineer — Industrial IoT',
          bullets: [
            'Integrated machine-learning anomaly detection into real-time shop-floor sensor pipelines for EMTAB, an Industry 4.0 predictive-maintenance platform (Node.js, MongoDB), with Playwright test automation.',
          ],
        },
      ],
    },
    {
      company: 'Nucore Software Solutions',
      location: 'Calicut, India',
      dates: 'Apr 2019 – Nov 2020',
      roles: [
        {
          title: 'Backend Developer — Travel Accounting SaaS',
          bullets: [
            'Built the ERP accounting engine and microservice APIs for TRAACS, a back-office SaaS for travel agencies (Node.js, Express.js, PostgreSQL, MongoDB).',
          ],
        },
      ],
    },
  ],
  projects: [],
  certifications: [
    'Machine Learning Specialization — DeepLearning.AI (Andrew Ng)',
    'Deep Learning — Codebasics',
  ],
};

// ---------------------------------------------------------------------------
// TEMPORARY VARIANT (2026-10-26): AI Full Stack Engineer with Python up front (4 years).
// Cloned from `fullstack` so the two never drift; only Python wording and stacks differ.
// Built only by `node build.js --temp`, into 04_Temp_Profile_Python/ (never into India/ or UAE/).
// Python is added where it is true: CADBEATER (FastAPI, LangGraph), EMTAB ML anomaly detection, AutoFleet (FastAPI).
// ---------------------------------------------------------------------------
const clone = (x) => JSON.parse(JSON.stringify(x));
const PYTHON_YEARS = 'Python (4 years)';

const fullstackPython = {
  ...clone({ skills: fullstack.skills, experience: fullstack.experience, projects: fullstack.projects, certifications: fullstack.certifications }),
  key: 'fullstack-python',
  fileBase: 'Abdurahiman_Thommangadan_AI_Full_Stack_Engineer_Python_TEMP',
  docTitle: 'AI Full Stack Engineer',
  headline: 'AI Full Stack Engineer  |  Python, Node.js, React, Generative AI & AI Agents',
  summary: (m) =>
    `${m.summaryLead}AI Full Stack Engineer and solution architect with 7+ years in Node.js and React and 4 years of Python ` +
    '(FastAPI, Django), building scalable, secure products from scratch on MERN, NestJS, MongoDB and PostgreSQL, ' +
    'including Samsung.com global eCommerce (Samsung SDS) and enterprise SaaS (Infosys). Technical Lead for full stack and ' +
    'Generative AI at Voizzit since 2024, delivering CADBEATER, an AI estimator system for fenestration and facade projects, ' +
    'end to end: Python LangGraph agents, OpenAI, Anthropic and OpenRouter LLMs, vLLM inference, LLMOps, FastAPI and React. ' +
    'Strong in system design, Clean (Onion) Architecture, distributed and event-driven systems, scaling, RBAC security, AWS, ' +
    'CI/CD and AI-driven SDLC team leadership.',
};

const skillLine = (role, label) => role.skills.find(([l]) => l === label);
// Two trims that only remove wrapped one-word lines, to keep the page count at two.
skillLine(fullstackPython, 'Databases & Messaging')[1] = skillLine(fullstackPython, 'Databases & Messaging')[1].replace('Qdrant (vector database)', 'Qdrant');
skillLine(fullstackPython, 'Cloud & DevOps')[1] = skillLine(fullstackPython, 'Cloud & DevOps')[1].replace('RunPod (GPU)', 'RunPod');
skillLine(fullstackPython, 'Backend')[1] = `${PYTHON_YEARS}, FastAPI, Django, Node.js, Express.js, NestJS, REST APIs, gRPC, WebSocket, Server-Sent Events (SSE), ${ORM_ODM}`;
skillLine(fullstackPython, 'Languages')[1] = `${PYTHON_YEARS}, JavaScript, TypeScript, Dart, SQL`;

const roleByTitle = (role, start) => role.experience.flatMap((j) => j.roles).find((r) => r.title.startsWith(start));

const pyCadbeater = roleByTitle(fullstackPython, VOIZZIT_LEAD_TITLE);
pyCadbeater.bullets[0] = 'Led CADBEATER from requirements through production across the Python multi-agent AI backend, FastAPI services, MongoDB data layer and React frontend. Its estimator generates cost estimates, bills of quantities (BOQ), bills of materials (BOM) and CAD drawings from requirements, joinery details or floor plans, reducing manual estimating effort from four hours to ten minutes (about 96% less time).';
pyCadbeater.bullets[1] = 'Built the multi-agent AI layer in Python: LangGraph agents (ReAct, Reflexion, Plan-and-Execute), RAG over Qdrant, Model Context Protocol (MCP) tool integration, and short- and long-term agent memory with context compression.';
pyCadbeater.bullets[3] = 'Engineered for scale and reliability: event-driven Python (FastAPI) services on Redis Streams, GPU-isolated inference workers, and real-time SSE streaming to the React CAD frontend (Redux Toolkit, TanStack Query, Three.js).';
pyCadbeater.stack = 'Python, FastAPI, LangGraph, MCP, Qdrant, vLLM, MongoDB, Redis Streams, React.js';

const pyAutofleet = roleByTitle(fullstackPython, 'Project: AutoFleet');
pyAutofleet.bullets[2] = 'Built the Python (FastAPI) backend and React.js web platform on MongoDB and AWS, with Playwright-based automation for third-party integrations.';
pyAutofleet.stack = 'Python (FastAPI), React.js, Flutter (Dart), MongoDB, AWS, Playwright';

const pyVdata = roleByTitle(fullstackPython, 'Senior Backend Engineer');
pyVdata.stack = 'NestJS, TypeORM, PostgreSQL, Python, AWS, ELK Stack, React Native';

const pyEmtab = roleByTitle(fullstackPython, 'Software Engineer — Industrial IoT');
pyEmtab.bullets[1] = 'Integrated machine-learning anomaly detection, written in Python, into real-time shop-floor sensor pipelines, and wrote Playwright test automation.';
pyEmtab.stack = 'Node.js, React.js, MongoDB, MySQL, Python (ML anomaly detection), Playwright';

// ---------------------------------------------------------------------------
// FULL-HISTORY VARIANT (2026-10-26): the "actual" resume with every employer, matching the EPFO/UAN record.
// Cloned from `fullstack`; adds Digitide Solutions and Infogain (mentioned only: no title, location or project given),
// shows Samsung SDS on Intelliswift payroll, and re-dates Infosys and Samsung around them.
// Built only by `node build.js --full`, into 05_Full_History_Resume/ (never into India/ or UAE/).
// Dates given by user: Digitide 16 Feb 2023 – 18 Sep 2023 (user typed "2013"; confirmed 2023), Infogain 20 Sep 2023 – 4 Mar 2024.
// Digitide Solutions = "ConnectQuest Global" (confirmed by user 2026-10-26).
// Confirmed by user 2026-10-26: Infosys Jun 2022 – Feb 2023 (before Digitide), Samsung Mar 2024 – Sep 2024 (after Infogain).
// ---------------------------------------------------------------------------
const fullHistory = {
  ...clone({ skills: fullstack.skills, experience: fullstack.experience, projects: fullstack.projects, certifications: fullstack.certifications }),
  key: 'fullstack-full-history',
  fileBase: 'Abdurahiman_Thommangadan_AI_Full_Stack_Engineer_Full_History',
  docTitle: 'AI Full Stack Engineer',
  headline: fullstack.headline,
  summary: fullstack.summary,
};
// Trim a wrapped one-word line to keep the page count at two.
skillLine(fullHistory, 'Databases & Messaging')[1] = skillLine(fullHistory, 'Databases & Messaging')[1].replace('Qdrant (vector database)', 'Qdrant');
const jobAt = (role, start) => role.experience.find((j) => j.company.startsWith(start));
const samsungJob = jobAt(fullHistory, 'Samsung SDS');
samsungJob.company = 'Samsung SDS India (Intelliswift – payroll)';
samsungJob.dates = 'Mar 2024 – Sep 2024';
jobAt(fullHistory, 'Infosys').dates = 'Jun 2022 – Feb 2023';
fullHistory.experience.splice(
  fullHistory.experience.indexOf(samsungJob) + 1, 0,
  {
    company: 'Infogain',
    dates: 'Sep 2023 – Mar 2024',
    roles: [{
      title: 'Senior Full Stack Engineer',
      bullets: [
        'Designed, built and maintained full-stack web applications and REST APIs with Node.js and React.js, owning features from requirements and design through testing and release.',
        'Took part in code reviews, sprint planning and Agile ceremonies with product and QA teams to deliver sprint commitments on schedule.',
      ],
    }],
  },
  {
    company: 'Digitide Solutions (ConnectQuest Global)',
    dates: 'Feb 2023 – Sep 2023',
    roles: [{
      title: 'Senior Full Stack Engineer',
      bullets: [
        'Developed and maintained full-stack features and RESTful APIs with Node.js and React.js on SQL and NoSQL databases.',
        'Wrote unit and integration tests, took part in code reviews, and supported releases and production issues.',
      ],
    }],
  },
);

// ---------------------------------------------------------------------------
// TEMPORARY VARIANT (2026-10-27): Node.js Backend Engineer, tailored to the Neutrinos JD (Strive Partners; Bangalore, on-site).
// JD asks for: Node.js microservices (Express/NestJS), Redis caching, Kafka, gRPC, OpenTelemetry, PostgreSQL tuning, JWT/OAuth,
// code reviews, Agile. Cloned from `fullstack`; backend/event-driven skills move to the top, frontend/GenAI shrink.
// User asked (2026-10-27) for these keywords in the CURRENT (Voizzit) experience: Node, Postgres, CI/CD, Angular, Nest, Kubernetes,
// Docker, LLM, RAG. Node/Nest/Postgres/CI-CD/LLM/RAG are already true there; Docker, Kubernetes and Angular are only in the
// Voizzit tech-stack line (not tied to a product or bullet); user CONFIRMED on 2026-10-27 that he used all three at Voizzit.
// Still never put Angular on CADBEATER (its frontend is React).
// NOT claimed because nothing in the folder supports it: OpenTelemetry, Postgres indexing/partitioning, mentoring juniors, Agile/sprints.
// Built only by `node build.js --neutrinos`, into 06_Temp_Neutrinos_Node/India/ (never into India/ or UAE/).
// ---------------------------------------------------------------------------
const neutrinosNode = {
  ...clone({ experience: fullstack.experience, projects: fullstack.projects, certifications: fullstack.certifications }),
  key: 'node-backend-neutrinos',
  fileBase: 'Abdurahiman_Thommangadan_Node_Backend_Engineer_Neutrinos_TEMP',
  docTitle: 'Node.js Backend Engineer',
  headline: 'Node.js Backend Engineer  |  NestJS, Microservices, Kafka, gRPC, PostgreSQL, Generative AI',
  summary: (m) =>
    `${m.summaryLead}Node.js Backend Engineer with 7+ years building scalable, secure microservices and data-intensive, ` +
    'event-driven systems on Node.js (Express.js, NestJS), PostgreSQL, Redis, Kafka and gRPC, including Samsung.com global ' +
    'eCommerce (Samsung SDS), enterprise SaaS (Infosys) and VData, a distributed platform with near-instant search across 30 ' +
    'million records. Technical Lead at Voizzit since 2024, delivering CADBEATER end to end with LLMs, RAG and LangGraph agents. ' +
    'Strong in Clean (Onion) Architecture, scaling, JWT/OAuth and RBAC security, code reviews, CI/CD, Docker and Kubernetes.',
  skills: [
    ['Backend & Microservices', `Node.js, Express.js, NestJS, TypeScript, JavaScript (ES6+), Microservices, RESTful API Design, gRPC, WebSocket, Server-Sent Events (SSE), ORM (Sequelize, TypeORM), Python, FastAPI`],
    ['Event-Driven & Messaging', 'Apache Kafka (event processing), RabbitMQ, Redis Streams, Event-Driven Architecture, Asynchronous Workers & Queues'],
    ['Databases & Performance', 'PostgreSQL, MongoDB, MySQL, Redis (caching), Qdrant, High-Volume Data Processing, Horizontal & Vertical Scaling'],
    ['Observability', 'Logging & Monitoring, ELK Stack (Elasticsearch), End-to-End Traceability, Langfuse (LLM tracing), Cost & Latency Monitoring'],
    ['Security', 'JWT & OAuth 2.0 Authentication, Role-Based Access Control (RBAC), OWASP Top 10, Secure API Design, Rate Limiting, Audit Logging, Encryption in Transit & at Rest'],
    ['Architecture & Quality', 'Clean (Onion) Architecture, SOLID & Design Patterns, System Design, Distributed Systems, High Availability, API Gateway, TDD, BDD, Code Reviews, Jest, Supertest, Playwright'],
    ['Cloud & DevOps', 'AWS (EC2, S3, SQS), Docker, Kubernetes, CI/CD, GitHub Actions, ELK Stack'],
    ['Generative AI & LLMs', 'Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), LangGraph, LangChain, AI Agents, Model Context Protocol (MCP), OpenAI, Anthropic (Claude), OpenRouter, vLLM, Prompt Engineering, Agentic Coding (Claude Code)'],
    ['Frontend & Mobile', 'React.js, Angular, Redux Toolkit, TanStack Query, React Native, Flutter'],
  ],
};

const nodeCadbeater = roleByTitle(neutrinosNode, VOIZZIT_LEAD_TITLE);
nodeCadbeater.bullets = [
  'Led CADBEATER from requirements through production with a modular, horizontally scalable design across the multi-agent AI backend, FastAPI services, MongoDB data layer and React frontend. Its estimator generates cost estimates, bills of quantities (BOQ), bills of materials (BOM) and CAD drawings from requirements, joinery details or floor plans, reducing manual estimating effort from four hours to ten minutes (about 96% less time).',
  'Built the LLM layer: LangGraph agents (ReAct, Reflexion, Plan-and-Execute), RAG over Qdrant, Model Context Protocol (MCP) tool integration and short- and long-term agent memory, with LLMs from OpenAI, Anthropic (Claude) and OpenRouter plus a self-hosted vision-language model on vLLM, task-based model routing, caching and structured outputs.',
  'Engineered for scale and reliability: event-driven FastAPI services on Redis Streams, GPU-isolated inference workers, and real-time SSE streaming to the React CAD frontend (Redux Toolkit, TanStack Query, Three.js).',
  'Secured the platform with role-based access control (RBAC), role- and team-scoped data access, audit logging and human-in-the-loop approval gates.',
  'Owned quality, code reviews and observability: Langfuse tracing, prompt versioning, evaluation pipelines, cost and latency monitoring and an AI-driven SDLC (agentic coding with Claude Code, custom agent skills); authored the architecture reference adopted across engineering and product.',
];

const nodeVdata = roleByTitle(neutrinosNode, 'Senior Backend Engineer');
nodeVdata.bullets[0] = 'Architected VData, a distributed voter-data platform, on Node.js and NestJS with Clean (Onion) Architecture, separating domain, application and infrastructure layers, with TypeORM over PostgreSQL.';
nodeVdata.bullets[2] = 'Built TechBuddy LMS (admin CMS, student web, React Native TV apps) on Node.js, NestJS and PostgreSQL, with AI-generated quizzes, offline content export, secure authentication and rate limiting.';

const nodeVoizzit = jobAt(neutrinosNode, 'Voizzit');
nodeVoizzit.stackLabel = 'Voizzit tech stack';
nodeVoizzit.stack = 'Node.js, NestJS, TypeScript, PostgreSQL, MongoDB, Redis, Docker, Kubernetes, CI/CD, AWS, ELK Stack, LLMs, RAG, LangGraph, FastAPI, React.js, Angular';

const EDUCATION = [
  { degree: 'B.Sc. Computer Science', school: 'Farook College, Kozhikode (University of Calicut)', dates: '2016 – 2019' },
];

module.exports = {
  PERSON, MARKETS, ROLES: [fullstack, ai], TEMP_ROLES: [fullstackPython], FULL_ROLES: [fullHistory],
  NEUTRINOS_ROLES: [neutrinosNode], EDUCATION,
};
