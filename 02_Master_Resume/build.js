// Builds 4 ATS-friendly resumes (India/UAE × Full Stack/AI Engineer) as DOCX + PDF from content.js.
// Usage: npm install && node build.js
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const {
  Document, Packer, Paragraph, TextRun, Tab, ExternalHyperlink, AlignmentType,
  BorderStyle, LevelFormat, TabStopType,
} = require('docx');
const { PERSON, MARKETS, ROLES, TEMP_ROLES, FULL_ROLES, NEUTRINOS_ROLES, EDUCATION } = require('./content');

const ROOT = path.resolve(__dirname, '..');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

// A4, single column. Twips: 1440 = 1 inch.
const PAGE = { width: 11906, height: 16838 };
const MARGIN = { top: 680, bottom: 680, left: 850, right: 850 };
const TEXT_WIDTH = PAGE.width - MARGIN.left - MARGIN.right;
const FONT = 'Arial';
const ACCENT = '1F3A5F';
// Half-points
const SZ = { name: 34, headline: 21, contact: 19, heading: 22, body: 21 };

// ---------------------------------------------------------------------------
// DOCX
// ---------------------------------------------------------------------------
const run = (text, opts = {}) => new TextRun({ text, font: FONT, size: SZ.body, ...opts });

function heading(text) {
  return new Paragraph({
    keepNext: true,
    spacing: { before: 150, after: 70 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 1 } },
    children: [run(text.toUpperCase(), { bold: true, size: SZ.heading, color: ACCENT })],
  });
}

function leftRight(leftRuns, right, { before = 0, after = 0, keepNext = true } = {}) {
  return new Paragraph({
    keepNext,
    spacing: { before, after },
    tabStops: [{ type: TabStopType.RIGHT, position: TEXT_WIDTH - 15 }],
    children: [...leftRuns, new TextRun({ children: [new Tab(), right], font: FONT, size: SZ.body })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { after: 35, line: 252 },
    children: [run(text)],
  });
}

function buildDocx(role, market) {
  const children = [];

  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 30 },
    children: [run(PERSON.name, { bold: true, size: SZ.name, color: ACCENT })],
  }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [run(role.headline, { bold: true, size: SZ.headline })],
  }));
  const contact = [market.location, market.residency, market.phone, PERSON.email].filter(Boolean).join('  |  ');
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [
      run(`${contact}  |  `, { size: SZ.contact }),
      new ExternalHyperlink({
        link: PERSON.linkedinUrl,
        children: [run(PERSON.linkedinLabel, { size: SZ.contact, bold: true, color: ACCENT, underline: {} })],
      }),
    ],
  }));

  children.push(heading('Professional Summary'));
  children.push(new Paragraph({ spacing: { after: 20, line: 250 }, children: [run(role.summary(market))] }));

  children.push(heading('Technical Skills'));
  for (const [label, items] of role.skills) {
    children.push(new Paragraph({
      spacing: { after: 30, line: 252 },
      children: [run(`${label}: `, { bold: true }), run(items)],
    }));
  }

  children.push(heading('Professional Experience'));
  role.experience.forEach((job, i) => {
    children.push(leftRight(
      [run(job.company, { bold: true }), ...(job.location ? [run(`, ${job.location}`)] : [])],
      job.dates,
      { before: i === 0 ? 20 : 110, after: 10 },
    ));
    job.roles.forEach((r, j) => {
      const titleRuns = [run(r.title, { bold: true, italics: true })];
      const p = r.dates
        ? leftRight(titleRuns, r.dates, { before: j === 0 ? 0 : 60, after: 30 })
        : new Paragraph({ keepNext: true, spacing: { before: j === 0 ? 0 : 60, after: 30 }, children: titleRuns });
      children.push(p);
      if (r.project) {
        children.push(new Paragraph({
          keepNext: true,
          spacing: { after: 30, line: 252 },
          children: [
            run(`Flagship project: ${r.project.name}`, { bold: true, color: ACCENT }),
            ...(r.project.description ? [run(` — ${r.project.description}`)] : []),
          ],
        }));
      }
      r.bullets.forEach((b) => children.push(bullet(b)));
      if (r.stack) {
        children.push(new Paragraph({
          spacing: { after: 30, line: 252 },
          indent: { left: 300 },
          children: [run('Tech stack: ', { bold: true }), run(r.stack)],
        }));
      }
    });
    // Optional employer-level stack line (used by the --neutrinos variant).
    if (job.stack) {
      children.push(new Paragraph({
        spacing: { before: 40, after: 30, line: 252 },
        children: [run(`${job.stackLabel || 'Tech stack'}: `, { bold: true }), run(job.stack)],
      }));
    }
  });

  if (role.projects.length) {
    children.push(heading('Additional Projects'));
    for (const [name, desc] of role.projects) {
      children.push(new Paragraph({
        spacing: { after: 30, line: 252 },
        children: [run(`${name}: `, { bold: true }), run(desc)],
      }));
    }
  }

  children.push(heading('Education'));
  for (const e of EDUCATION) {
    children.push(leftRight([run(e.degree, { bold: true }), run(`, ${e.school}`)], e.dates, { after: 20, keepNext: false }));
  }

  children.push(heading('Certifications'));
  role.certifications.forEach((c) => children.push(bullet(c)));

  return new Document({
    creator: 'Abdurahiman Thommangadan',
    title: `Abdurahiman Thommangadan — ${role.docTitle}`,
    description: 'Resume',
    styles: { default: { document: { run: { font: FONT, size: SZ.body } } } },
    numbering: {
      config: [{
        reference: 'bullets',
        levels: [{
          level: 0,
          format: LevelFormat.BULLET,
          text: '•',
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 300, hanging: 220 } } },
        }],
      }],
    },
    sections: [{ properties: { page: { size: PAGE, margin: MARGIN } }, children }],
  });
}

// ---------------------------------------------------------------------------
// HTML -> PDF (same content and layout, text-based PDF via headless Chrome)
// ---------------------------------------------------------------------------
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function buildHtml(role, market) {
  const contact1 = [market.location, market.residency, market.phone, PERSON.email].filter(Boolean).map(esc).join('&nbsp;&nbsp;|&nbsp;&nbsp;');
  const exp = role.experience.map((job) => `
    <div class="job">
      <div class="lr"><span><b>${esc(job.company)}</b>${job.location ? `, ${esc(job.location)}` : ''}</span><span>${esc(job.dates)}</span></div>
      ${job.roles.map((r) => `
        <div class="lr role"><span><b><i>${esc(r.title)}</i></b></span><span>${r.dates ? esc(r.dates) : ''}</span></div>
        ${r.project ? `<p class="project"><b>Flagship project: ${esc(r.project.name)}</b>${r.project.description ? ` — ${esc(r.project.description)}` : ''}</p>` : ''}
        <ul>${r.bullets.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>
        ${r.stack ? `<p class="stack"><b>Tech stack:</b> ${esc(r.stack)}</p>` : ''}`).join('')}
      ${job.stack ? `<p class="job-stack"><b>${esc(job.stackLabel || 'Tech stack')}:</b> ${esc(job.stack)}</p>` : ''}
    </div>`).join('');
  const projects = role.projects.length
    ? `<h2>Additional Projects</h2>${role.projects.map(([n, d]) => `<p class="line"><b>${esc(n)}:</b> ${esc(d)}</p>`).join('')}`
    : '';
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Abdurahiman Thommangadan — ${esc(role.docTitle)}</title>
<style>
  @page { size: A4; margin: ${MARGIN.top / 1440}in ${MARGIN.right / 1440}in ${MARGIN.bottom / 1440}in ${MARGIN.left / 1440}in; }
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: ${SZ.body / 2}pt; line-height: 1.25; color: #111; margin: 0; }
  .name { text-align: center; font-size: ${SZ.name / 2}pt; font-weight: bold; color: #${ACCENT}; margin: 0 0 1.5pt; }
  .headline { text-align: center; font-size: ${SZ.headline / 2}pt; font-weight: bold; margin: 0 0 2pt; }
  .contact { text-align: center; font-size: ${SZ.contact / 2}pt; margin: 0; }
  .contact a { color: #${ACCENT}; font-weight: bold; text-decoration: underline; }
  h2 { font-size: ${SZ.heading / 2}pt; color: #${ACCENT}; text-transform: uppercase; border-bottom: 0.75pt solid #${ACCENT};
       margin: 7.5pt 0 3.5pt; padding-bottom: 1pt; break-after: avoid; }
  p { margin: 0 0 1.5pt; }
  .line { margin: 0 0 1.25pt; }
  .lr { display: flex; justify-content: space-between; gap: 12pt; break-after: avoid; }
  .job { margin-top: 5.5pt; }
  .job:first-of-type { margin-top: 1pt; }
  .role { margin: 0.5pt 0 1.5pt; }
  .role + ul + .role { margin-top: 3pt; }
  .project { margin: 0 0 1.5pt; }
  .project b { color: #${ACCENT}; }
  .stack { margin: 0 0 1.5pt 15pt; }
  .job-stack { margin: 2pt 0 1.5pt; }
  ul { margin: 0; padding-left: 15pt; }
  li { margin: 0 0 1.5pt; padding-left: 1pt; }
</style></head><body>
<p class="name">${esc(PERSON.name)}</p>
<p class="headline">${esc(role.headline)}</p>
<p class="contact">${contact1}&nbsp;&nbsp;|&nbsp;&nbsp;<a href="${PERSON.linkedinUrl}">${esc(PERSON.linkedinLabel)}</a></p>
<h2>Professional Summary</h2>
<p>${esc(role.summary(market))}</p>
<h2>Technical Skills</h2>
${role.skills.map(([l, s]) => `<p class="line"><b>${esc(l)}:</b> ${esc(s)}</p>`).join('')}
<h2>Professional Experience</h2>
${exp}
${projects}
<h2>Education</h2>
${EDUCATION.map((e) => `<div class="lr"><span><b>${esc(e.degree)}</b>, ${esc(e.school)}</span><span>${esc(e.dates)}</span></div>`).join('')}
<h2>Certifications</h2>
<ul>${role.certifications.map((c) => `<li>${esc(c)}</li>`).join('')}</ul>
</body></html>`;
}

function htmlToPdf(html, pdfPath) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'resume-'));
  const htmlPath = path.join(tmp, 'resume.html');
  fs.writeFileSync(htmlPath, html);
  execFileSync(CHROME, [
    '--headless', '--disable-gpu', '--no-pdf-header-footer', '--print-to-pdf-no-header',
    `--user-data-dir=${path.join(tmp, 'profile')}`, `--print-to-pdf=${pdfPath}`, `file://${htmlPath}`,
  ], { stdio: 'ignore' });
  fs.rmSync(tmp, { recursive: true, force: true });
}

async function main() {
  // `node build.js --temp` builds only the temporary variants into 04_Temp_Profile_Python/<market>/,
  // leaving the four live resumes (and their file hashes) untouched.
  // `node build.js --full` likewise builds only the full-employment-history variant into 05_Full_History_Resume/<market>/.
  // `node build.js --neutrinos` builds only the Neutrinos Node.js Backend Engineer variant (India market only: Bangalore on-site role)
  // into 06_Temp_Neutrinos_Node/India/.
  const temp = process.argv.includes('--temp');
  const full = process.argv.includes('--full');
  const neutrinos = process.argv.includes('--neutrinos');
  // The full-history variant has two more employers, so body text drops from 10.5pt to 10pt to keep it at two pages.
  if (full) SZ.body = 20;
  const markets = neutrinos ? [MARKETS.india] : Object.values(MARKETS);
  for (const market of markets) {
    for (const role of full ? FULL_ROLES : temp ? TEMP_ROLES : neutrinos ? NEUTRINOS_ROLES : ROLES) {
      const outDir = full
        ? path.join(ROOT, '05_Full_History_Resume', market.folder)
        : temp
          ? path.join(ROOT, '04_Temp_Profile_Python', market.folder)
          : neutrinos
            ? path.join(ROOT, '06_Temp_Neutrinos_Node', market.folder)
            : path.join(ROOT, market.folder, role.folder);
      fs.mkdirSync(outDir, { recursive: true });
      const base = path.join(outDir, role.fileBase);
      fs.writeFileSync(`${base}.docx`, await Packer.toBuffer(buildDocx(role, market)));
      htmlToPdf(buildHtml(role, market), `${base}.pdf`);
      console.log(`built ${path.relative(ROOT, base)}.{docx,pdf}`);
    }
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
