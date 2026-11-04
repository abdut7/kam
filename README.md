# Job Hunt 2026: India + UAE

**Target roles:** (1) AI Full Stack Engineer (MERN + Generative AI; preferred) · (2) AI Engineer / GenAI / AI Agent Engineer
**Profile title everywhere (since 25 Oct 2026):** exactly "AI Full Stack Engineer"; the Full Stack resume files are named `…_AI_Full_Stack_Engineer`

```
00_Original_Resumes/              Old resumes, kept for reference (do not send)
01_Analysis/                      Audits: resume, LinkedIn, Naukri, Indeed
02_Master_Resume/                 Single source of truth: every bullet and metric. All 4 resumes are cut from it
03_Shared_Profiles/
   LinkedIn/                      One profile serves both markets
   Indeed/                        One account, India + UAE country sites
04_Temp_Profile_Python/           TEMPORARY AI Full Stack variant with Python (4 years); India/ + UAE/ DOCX + PDF.
                                  Built by `node build.js --temp`; the four live resumes below are not touched
05_Full_History_Resume/           The "actual" AI Full Stack resume with EVERY employer (adds Digitide Solutions, Infogain;
                                  Samsung SDS shown with Intelliswift payroll). India/ + UAE/ DOCX + PDF.
                                  Built by `node build.js --full`; the four live resumes are not touched
06_Temp_Neutrinos_Node/           TEMPORARY "Node.js Backend Engineer" variant tailored to the Neutrinos JD (Bangalore, on-site); India/ only.
                                  Built by `node build.js --neutrinos`; the other resumes are not touched
India/
   Resume_FullStack_MERN_AI/      DOCX + PDF
   Resume_AI_Engineer/            DOCX + PDF
   Naukri/                        Profile update plan
   Applications/                  Tracker, target companies
UAE/
   Resume_FullStack_MERN_AI/      DOCX + PDF
   Resume_AI_Engineer/            DOCX + PDF
   Job_Portals_Bayt_NaukriGulf_GulfTalent/
   Applications/                  Tracker, target companies
```

Rule: edit facts in `02_Master_Resume/content.js` first, then regenerate the 4 resumes, so they never drift apart:

```bash
cd "02_Master_Resume" && npm install && node build.js
```

Which file to send:
- Full Stack / MERN + AI job in India: `India/Resume_FullStack_MERN_AI/*.pdf`
- AI / GenAI / AI Agent job in India: `India/Resume_AI_Engineer/*.pdf`
- Same choice for the UAE, from `UAE/…` (UAE phone number + "UAE Resident")
- Send the `.docx` only when a portal asks for Word

Plans: `01_Analysis/01_Resume_Analysis.md` (audit) · `01_Analysis/02_Profile_Update_Plan.md` (LinkedIn / Naukri / Indeed / UAE portals)
# kam
