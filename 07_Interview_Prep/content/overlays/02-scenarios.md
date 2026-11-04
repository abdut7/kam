## React Rendering Model

### Why it exists
Before React, UI code changed the DOM by hand on every event, and keeping a dozen widgets in sync with changing data produced screens where one part showed new values and another still showed old ones. React lets you describe what the screen should look like for the current state and works out the smallest set of DOM changes itself, a step called reconciliation. Fiber and concurrent rendering were added because a large update used to block the main thread until it finished, which froze typing and scrolling. The cost is that React calls your component functions far more often than you expect, so wasted renders, unstable keys and object identity become problems you own.

## Hooks Deep Dive

### Why it exists
Before hooks, state and lifecycle logic lived in class components, and sharing that logic meant higher-order components or render props that wrapped components in layers nobody could read. Related code was also split apart: subscribe in `componentDidMount`, update in `componentDidUpdate`, unsubscribe in `componentWillUnmount`. Hooks let a function component hold state and side effects, and let you package that logic as a custom hook any component can call. The trade-off is closures: every render captures its own values, so dependency arrays, stale closures and missing cleanups become the most common bugs.

## State Management at Scale

### Why it exists
In a large app the same data, such as the current user, a cart or a list of orders, is needed by components far apart in the tree, and passing it through every level (prop drilling) breaks whenever the tree changes. Teams that solved this by copying server data into one global store then spent their time keeping those copies in sync with the server. Modern practice splits state by kind: server data in a cache such as TanStack Query, shared UI state in a small store, shareable view state in the URL, and everything else local to a component. The cost is another abstraction to learn and the discipline to decide, for each piece of state, where it lives.

## Performance Engineering

### Why it exists
Developers test on fast laptops while many users are on mid-range phones and slow networks, so an app that feels instant at the desk can feel broken in the field, and slow pages lose users and search ranking. Without measurement, teams wrap everything in `memo` or rewrite components and often make things worse. Performance engineering gives you shared metrics (Core Web Vitals: LCP for loading, INP for responsiveness, CLS for visual stability) and tools such as the React Profiler and a bundle analyzer to find the real bottleneck. Every fix, from virtualization to code splitting, adds code and new failure modes, so you apply it only where a measurement justifies it.

## Architecture for Scalable Frontends

### Why it exists
When several teams work in one frontend without boundaries, they collide: merge conflicts, circular imports, five copies of the same button, and one team's change breaking another team's page. Architecture choices such as feature folders with public entry points, a shared design system, monorepo tooling, error boundaries and feature flags give each team an area it owns and a contract with the others. Without them, apps grow into a tangle where nobody dares delete code. The cost is upfront structure and governance, which slows a small team down if adopted too early.

## Data Fetching, Caching & Real-time

### Why it exists
The network is slow and unreliable: requests fail, responses arrive out of order, and data changes on the server while the user is looking at it. Hand-written `fetch` calls inside `useEffect` led to race conditions, duplicate requests, missing loading and error states, and screens that never refreshed. Caching libraries, request cancellation and real-time transports such as SSE and WebSockets handle these problems in one place instead of in every component. The trade-off is that you now manage cache freshness and invalidation, which is where many subtle bugs live.

## Next.js & Rendering Strategies

### Why it exists
A purely client-rendered SPA sends an almost empty HTML page, so users see a blank screen until the JavaScript downloads and runs, and crawlers and link previews may see nothing at all. Server rendering, static generation and React Server Components put real content in the HTML and keep heavy code and secrets on the server. Before frameworks like Next.js, teams wired this up by hand with Express and custom bundler configs. The cost is a split mental model of code that runs on the server versus in the browser, plus hydration mismatches and caching layers that serve stale data when misunderstood.

## TypeScript for React

### Why it exists
Plain JavaScript lets you pass the wrong prop, misspell a field from an API response or forget a case in a status switch, and you find out only when a user hits it. TypeScript checks these at compile time, documents component APIs in the editor, and makes large refactors safe because the compiler lists every place a change breaks. The cost is build setup, a learning curve for generics, and a false sense of safety: types are erased at runtime, so data from the network still needs runtime validation with a tool such as zod.

## Testing & Quality

### Why it exists
Frontend code breaks in ways a code reviewer cannot see: a refactor removes a button's label, a hook stops cleaning up, a backend change breaks a form. Older tests checked component internals such as state values and method calls, so they broke on every refactor while missing real bugs. Modern testing renders components the way users use them (React Testing Library), mocks the network at its boundary (MSW) and runs critical journeys in a real browser (Playwright). The trade-off is time and maintenance: a slow or flaky suite gets ignored, so it must be fast and deterministic to be trusted.

## Security & Accessibility

### Why it exists
The browser runs your code next to untrusted input such as user content, model output and third-party scripts, so one careless line can lead to cross-site scripting, stolen sessions or forged requests. Accessibility exists because many people use a keyboard, a screen reader or heavy zoom, and an interface built only for a mouse and good eyesight shuts them out; in many markets it is also a legal requirement. Standards such as Content Security Policy, SameSite cookies and WCAG replaced ad hoc, per-team protections. The cost is discipline: a security header rolled out carelessly breaks third-party scripts, and accessibility needs checks with real assistive tools, not only linters.

## Building AI Product UIs

### Why it exists
Language model answers take seconds to tens of seconds, so a normal request with a spinner feels broken. Streaming shows text as it is generated, and agent interfaces show tool calls, progress and approval steps so users can see and trust what the system is doing. Earlier chat UIs either waited for the whole answer or hid what the agent did behind a spinner. The trade-off is that the UI becomes a state machine over a long-lived stream that must be cancellable and resumable, while rendering untrusted markdown and half-finished JSON safely.

## Frontend Project Scenarios [Scenarios]

> Interviewers run frontend design rounds as a conversation: they describe a product situation, stay quiet while you ask questions, then add constraints ("now it must work offline", "now it is 50,000 rows"). A weak answer jumps straight to a list of libraries. A senior answer pins down the numbers and the users first, says where each kind of state lives and how data flows, keeps hot paths out of React's render cycle, plans the rollout and the failure modes, and names the metrics that would prove the design works.

### Concepts you must understand
- Get the numbers first: rows on screen, updates per second, payload sizes, session length, target devices (a mid-range Android phone is the honest baseline) and network quality; they decide most of the design.
- Classify every piece of state: server cache, shared client UI state, URL state, local component state, and durable local data in IndexedDB; most frontend design mistakes are state in the wrong place.
- Keep high-frequency work out of React's render path: batch updates per animation frame, use external stores with selectors, mutate refs inside canvas or WebGL loops, and move heavy computation to a web worker.
- Model the network as an ordered log of events with ids, so the client can resume after a drop, ignore duplicates and detect gaps.
- Set budgets before building: INP under 200 ms and LCP under 2.5 s at the 75th percentile, a JavaScript budget per route, and real-user monitoring to check them in production.
- Prefer incremental, reversible delivery: strangler migrations, feature flags and percentage rollouts instead of a big-bang rewrite with a feature freeze.
- List the hostile conditions explicitly: offline, reconnects, a deploy mid-session, several tabs open, expired auth, low memory and slow CPUs.
- Shared frontend platforms such as a design system are products: they need versioning, a contribution model, migration tooling and adoption metrics.

### Q. You are building a real-time operations dashboard: about 5,000 shipments in a filterable table, with status updates arriving several times a second. How do you design it so it stays responsive?
**Short answer (45 seconds):** First I clarify the update rate, whether users need every intermediate state or only the latest, and whether filtering and sorting can stay on the client. Then I keep live data in a normalized store outside React, merge deltas as they arrive but notify React at most once per animation frame, virtualize the table so only visible rows render, and let each row subscribe to its own record. The filter input stays urgent while the filtered list renders as deferred work.

**Deeper explanation:** The feed is SSE because data flows one way: a snapshot with a sequence number, then versioned deltas keyed by shipment id; a sequence gap triggers a snapshot refetch.

```ts
const rows = new Map<string, Shipment>();
const listeners = new Set<() => void>();
let scheduled = false;

export function applyDelta(d: Shipment) {
  const cur = rows.get(d.id);
  if (cur && cur.version >= d.version) return;          // stale or duplicate
  rows.set(d.id, d);
  if (!scheduled) {
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; listeners.forEach((l) => l()); });
  }
}
const subscribe = (l: () => void) => { listeners.add(l); return () => { listeners.delete(l); }; };
export const useShipment = (id: string) => useSyncExternalStore(subscribe, () => rows.get(id));
```

`requestAnimationFrame` pauses in hidden tabs, so a background tab keeps merging and repaints once on return. TanStack Virtual renders around 50 memoized rows keyed by id, and a changed-cell flash is a CSS animation, not React state. At 5,000 rows client-side filtering is fine; at hundreds of thousands it moves to the server or a web worker.

Measure p75 INP with web-vitals attribution, long animation frames, Profiler render counts, and feed lag from server timestamp to paint.

**Follow-ups they will ask:**
- Users sort by a field that keeps changing: freeze row order while the pointer is over the table or re-sort on an interval, otherwise rows jump under the cursor.
- Updates reach a thousand per second: coalesce per id on the server; nobody can read that many changes anyway.

**Mistakes to avoid:**
- Calling `setState` per message, which turns a busy feed into a render storm.
- Ignoring reconnect gaps, so the table silently drifts away from the truth.

### Q. Your team must move a large Vite React SPA using React Router to the Next.js App Router, and product refuses a feature freeze. How do you plan it?
**Short answer (45 seconds):** I first clarify why we are migrating, usually SEO, first-load speed or a server layer for data and secrets, because that decides which routes move first. Then I migrate incrementally: run the whole SPA inside Next.js as a client-only catch-all route so we switch build and hosting without rewriting anything, then move routes one at a time to real App Router pages, highest value first. Feature work continues in whichever side owns the route.

**Deeper explanation:** Phase one follows the pattern in the Next.js migration guide: an optional catch-all route renders the existing app with server rendering off.

```ts
// app/[[...slug]]/page.tsx
import { ClientOnly } from "./client";
export default function Page() { return <ClientOnly />; }

// app/[[...slug]]/client.tsx
"use client";
import dynamic from "next/dynamic";
const App = dynamic(() => import("../../src/App"), { ssr: false });
export function ClientOnly() { return <App />; }
```

Mechanical work: `VITE_` variables become `NEXT_PUBLIC_` read from `process.env`, module-scope `window` access gets guarded, and static assets move to `public`.

Phase two moves one route at a time. A new `app/pricing/page.tsx` takes precedence over the catch-all, so Next serves that path while React Router still handles the rest. Crossing the boundary is a full page load, acceptable at first. Public SEO pages move first as server components; authenticated dashboards come later and may stay client components using TanStack Query, prefetched on the server via `HydrationBoundary`.

Key decisions: auth moves to cookies, because server components cannot see a token in `localStorage`. Runtime CSS-in-JS needs a style registry and client components, so plan a move to CSS Modules or a zero-runtime library.

Risks: hydration errors on newly server-rendered pages, bundle regressions, duplicate analytics page views and broken deep links. Measure LCP, INP and error rate per route before and after each move, plus the share of traffic on migrated routes.

**Follow-ups they will ask:**
- How do you roll back one route: revert its page so the catch-all serves the path again.
- When would you not migrate: an internal tool behind login with no SEO need gains little.

**Mistakes to avoid:**
- A parallel rewrite in a new repo that never catches up with the product.
- Marking every file `"use client"` and calling the migration done.

### Q. Four product teams have each built their own buttons, modals and tables. You are asked to lead a shared design system they will actually adopt. How do you plan and build it?
**Short answer (45 seconds):** I start by auditing what exists and asking what the teams share: React versions, server rendering, brands or themes, and how they release. I build on design tokens and accessible headless primitives, ship a versioned package with Storybook docs and visual tests, and migrate one team's busiest screens first to prove it. Adoption is the real goal, so contribution rules, codemods and adoption metrics matter as much as the components.

**Deeper explanation:**

```text
1. Audit: inventory screens, count variants per component
2. Tokens: color, spacing, type, radius, motion as CSS variables; themes swap values
3. Primitives: wrap Radix or React Aria for focus, keyboard and ARIA behavior
4. Components: Button, Field, Dialog, Menu, DataTable, Toast
5. Pilot with one team, then a migration guide and codemods for the rest
```

Styling: runtime CSS-in-JS conflicts with React Server Components and costs render time, so CSS variables with CSS Modules, Tailwind or a zero-runtime library suit Next.js teams. Packaging: one tree-shakeable ESM package with `sideEffects` set correctly, so a button import does not pull in the date picker. Versioning: semver with Changesets, deprecation warnings in development that name the replacement, and codemods for renames. API openness: a closed props API keeps consistency, compound components and a `className` escape hatch reduce forks; I keep core controls closed and layout open.

Quality gates: Storybook stories double as tests, with axe checks, visual regression screenshots and token contrast checks in CI.

Risks: the platform team becomes a bottleneck, so other teams contribute through a reviewed process; big breaking releases stall adoption, so changes ship small and often. Measure adoption by scanning repositories for local versus system component imports, plus style overrides, accessibility violations and time to build a new screen.

**Follow-ups they will ask:**
- One team uses Angular: share tokens and CSS, not React components.
- A team needs a variant this sprint: let them extend locally with a ticket to upstream it, and track the override.
- Dark mode and several brands: semantic tokens such as `--color-surface` mapped to palette values per theme.

**Mistakes to avoid:**
- Building forty components before a single team ships with five.
- Treating the system as a component dump with no owner, roadmap or migration support.

### Q. You are building an AI assistant chat that streams answers, shows each tool call, supports stop, and must continue the answer if the user refreshes mid-stream. How do you design it?
**Short answer (45 seconds):** The key decision is to decouple generation from the browser request. The server starts a run with an id, a worker writes every token, tool event and status change to a durable ordered log, and the browser only subscribes to that log from a cursor. A refresh reloads the conversation, sees the run still streaming, and resubscribes. Stop becomes an explicit cancel call, because closing the tab no longer means stop.

**Deeper explanation:**

```text
POST /runs                    -> { runId }; a worker calls the model and tools
worker                        -> XADD run:{id} * type delta text "..."
GET  /runs/{id}/events?after= -> SSE: XREAD from the cursor, then block
POST /runs/{id}/cancel        -> set flag; worker aborts the model call
on finish                     -> save message to Postgres, EXPIRE run:{id}
```

In a system like CADBEATER, which already pairs Redis Streams with SSE, the stream entry id doubles as the SSE `id:`, so `EventSource` sends `Last-Event-ID` on its own reconnects. A refresh creates a new `EventSource` without that id, so the page passes a cursor: `0` to replay and rebuild the partial message, or the last id kept in `sessionStorage`.

A reducer folds events into message parts and ignores ids it has applied, so replays are harmless. Tool events (`tool_started`, `tool_result`, `approval_required`) share the log, so a pending approval survives a refresh; the decision is a POST the worker waits on.

Decisions: cancel on disconnect is simpler but kills resume, so cancel is explicit, and runs with no subscriber for a few minutes are aborted to cap token cost. Streams are trimmed with `MAXLEN` and expire after completion.

Risks: orphaned runs when a worker dies (heartbeat plus a timeout that fails the run) and duplicate runs from a double submit (idempotency key on the POST). Measure time to first token, resume success rate, cancel-to-stop latency and orphaned runs.

**Follow-ups they will ask:**
- Why not WebSockets: the client mostly listens; SSE plus plain POSTs stays simple and proxy-friendly.
- Serverless hosting: generation must run in a worker or queue, not inside the request function.

**Mistakes to avoid:**
- Tying the model call to the HTTP request, so a refresh kills the answer.
- Buffering events in memory on one pod, so a reconnect that lands on another pod finds nothing.

### Q. You are adding a browser 3D viewer for large CAD assemblies to a React app, with side panels for part properties and selection. It must stay smooth on office laptops. How do you design it?
**Short answer (45 seconds):** I clarify model sizes, target GPUs and the interactions that matter: orbit, select, measure, annotate. Then I keep the render loop out of React state: React Three Fiber with refs and `useFrame` renders on demand while React owns the panels. Geometry is compressed on the server, decoded off the main thread, and drawn with instancing and merged meshes to keep draw calls low. Selection lives in a small store both sides share.

**Deeper explanation:**

```ts
const useViewer = create<{ selectedId?: string; select: (id?: string) => void }>()((set) => ({
  select: (selectedId) => set({ selectedId }),
}));

function Assembly({ url }: { url: string }) {
  const { scene } = useGLTF(url);                  // Draco-compressed glTF
  return (
    <primitive object={scene} onPointerDown={(e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      useViewer.getState().select(e.object.userData.partId);   // no re-render here
    }} />
  );
}
```

Server side, CAD files become glTF with Draco or meshopt compression, because parsing native CAD in the browser is slow; the Draco decoder runs in web workers. Repeated parts such as bolts become `InstancedMesh`, static parts are merged by material, and huge assemblies load by visible subassembly or level of detail. Picking on million-triangle meshes uses a bounding volume hierarchy (three-mesh-bvh) instead of brute-force raycasts.

React rules: `frameloop="demand"` on the `Canvas` draws only after changes; never `setState` per frame; camera moves and animations mutate refs inside `useFrame`; the property panel subscribes with a selector, and a small highlighter component changes materials imperatively and calls `invalidate()`. Three.js does not free GPU memory when objects are garbage collected, so switching models calls `dispose()` on geometries, materials and textures; R3F disposes what it created declaratively, not a loaded scene passed through `primitive`. Handle `webglcontextlost` with a reload prompt.

Measure frame time during orbit, draw calls and resident geometries and textures from `renderer.info`, time to first rendered model, and INP for panel clicks.

**Follow-ups they will ask:**
- The model does not fit in GPU memory: stream subassemblies on demand and show bounding boxes until detail loads.
- Can rendering leave the main thread: yes, `OffscreenCanvas` in a worker, at the cost of forwarding input events.

**Mistakes to avoid:**
- Keeping camera position or hover state in React state, so every mouse move re-renders the panels.
- Loading raw meshes that produce thousands of separate draw calls.

### Q. Field inspectors fill long forms with photos on tablets, often with no signal for hours, and the client demands zero lost submissions. How do you design the offline-first frontend?
**Short answer (45 seconds):** I clarify how long devices stay offline, photo sizes, whether two inspectors can edit the same asset, and what happens when the login expires offline. The design: an installable PWA whose service worker caches the app shell, IndexedDB as the source of truth for drafts, autosave on every change, and an outbox of submissions with client-generated ids that a sync engine replays when connectivity returns. The server treats those ids as idempotency keys, so a retried sync never creates duplicates.

**Deeper explanation:**

```ts
const db = new Dexie("inspections");
db.version(1).stores({ drafts: "id, assetId, updatedAt", outbox: "id, createdAt, status" });

async function submit(draft: Draft) {
  await db.transaction("rw", db.drafts, db.outbox, async () => {
    await db.outbox.add({ id: draft.id, payload: draft, schemaVersion: 3, status: "queued" });
    await db.drafts.delete(draft.id);
  });
  void syncOutbox();          // also on app start, "online" and a timer
}
```

Sync sends one item at a time with the item id as `Idempotency-Key`, marks it sent only after a 2xx, and backs off on failure. The Background Sync API helps on Chromium browsers but Safari does not support it, so the app also syncs on open and on `online`. Photos are compressed on the device, stored as Blobs and uploaded in resumable chunks. `navigator.storage.persist()` lowers eviction risk.

Decisions: append-only inspection records avoid most conflicts; where edits can collide, a version number lets the server return a conflict the UI shows as a field-level diff. Expired auth never blocks saving; the outbox waits for sign-in before syncing. Drafts carry a schema version so a new release migrates old drafts on load.

Risks: Safari can evict script-written storage for sites not visited recently unless installed to the home screen, and users clear site data. Measure outbox age, sync failures by reason, storage used, and daily device-versus-server record counts.

**Follow-ups they will ask:**
- How does the user know data is safe: a visible status per form (saved on device, queued, synced) and an outbox screen.
- A sync fails halfway: items are independent and idempotent, so retrying the whole queue is safe.

**Mistakes to avoid:**
- Keeping drafts in React state or `localStorage`, which loses photos and hits size limits.
- Retrying POSTs without idempotency keys, which turns a flaky network into duplicate inspections.

### Practice
- Build the dashboard store: a fake SSE feed emitting 200 updates a second across 5,000 rows; compare `setState` per message with the frame-batched store plus a virtualized table, and record INP and render counts under 4x CPU throttling.
- Implement resume after refresh with Express, Redis Streams and SSE: refresh mid-answer and confirm the message rebuilds with no duplicated or missing text, then cancel the run from a second tab.
- Build the offline outbox with Dexie; use Playwright's `context.setOffline(true)` to submit three forms offline, reload, go online, and assert exactly three server records even when you force one sync request to fail.
- Say it out loud: give a five-minute plan for the first two weeks of moving a Vite SPA to the Next.js App Router, including what ships to users at the end of week one.

## Frontend Incidents & Error Cases [Scenarios]

> Frontend incidents are hard because the failure happens on thousands of machines you cannot log into. Use one structure every time: clarify impact (which release, routes, browsers and how many users, from error tracking and real-user monitoring), contain (roll back, flip a flag, restore assets, purge a cache), diagnose by reproducing with a production build under the user's conditions, fix the cause, then prevent a repeat with a test, an alert or a runbook entry. Interviewers listen for whether you contain before you debug and whether you name exact tools and errors.

### Concepts you must understand
- Tag every error and RUM event with release version, route and browser, and upload source maps privately to the error tracker, so production stacks are readable and old sessions are distinguishable from new ones.
- Reproduce with a production build (`vite build && vite preview`, `next build && next start`), because dev mode adds checks, StrictMode double effects and a dev proxy that hide or create bugs.
- Long-lived tabs run old code: after any deploy some users stay on the previous version for hours, so assets, APIs and caches must tolerate two versions at once.
- Many "frontend" errors are infrastructure: CDN caching, proxy buffering, gateway error pages without CORS headers, and variables fixed at build time.
- Every fix ends with a guardrail: a lint rule, a test, an alert threshold or a runbook step.

| Symptom or error | First check | Likely causes | Fix |
|---|---|---|---|
| `ChunkLoadError: Loading chunk 412 failed` or `Failed to fetch dynamically imported module` after a deploy | Request the chunk URL: 404, HTML or JS | Old hashed assets deleted while tabs are open; `index.html` cached | Keep old assets, `no-cache` on HTML, reload once on chunk failure |
| `Expected a JavaScript module script but the server responded with a MIME type of "text/html"` | `curl -I` the asset URL | SPA fallback rewrites missing `/assets/*` to `index.html`; wrong `base` path | Exclude assets from the fallback so misses return 404; fix `base` |
| White screen with an uncaught error in the console | Is there a root error boundary; did it throw before `createRoot` | Uncaught render error unmounts the whole root; a module-scope throw | Route and root boundaries, `onUncaughtError` reporting, inline fallback message |
| Requests go to `undefined/api/...` or a staging host in production | Search the deployed bundle for the API host | Variable missing at build time; image built once with staging values | Validate env before the build; runtime config for promoted images |
| `Hydration failed because the initial UI does not match what was rendered on the server` | Reproduce with the user's time zone, locale and flag variant | Date or number formatting, client-only flags, cached personalized HTML, invalid nesting | Deterministic first render, server-evaluated flags, no shared cache for personalized HTML |
| `Maximum update depth exceeded` | Component in the stack and its effect dependencies | `setState` in an effect whose dependency is a new object every render | Derive during render, stabilize dependencies, remount with `key` |
| `Too many re-renders. React limits the number of renders to prevent an infinite loop.` | Handlers invoked during render | `onClick={setOpen(true)}` or unconditional `setState` in the component body | Pass a function; move the update to an event or effect |
| `The result of getSnapshot should be cached to avoid an infinite loop` | Store selectors used through `useSyncExternalStore` | Selector returns a new array or object on every call | Return stable references; `useShallow` in Zustand |
| Tab memory and DOM node count grow for hours | Performance monitor, then heap snapshot comparison filtered for "Detached" | Unbounded arrays, listeners or intervals without cleanup, undisposed chart or WebGL objects | Cap buffers, clean up effects, call `destroy` or `dispose`; memlab in CI |
| Typing in a table filter lags; INP poor on one route | web-vitals INP attribution: input delay, processing, presentation | Whole list re-renders per keystroke; synchronous filtering; formatters created per cell | `useDeferredValue`, virtualization, memoized rows, hoisted formatters |
| Mutation returns 200 but the list shows old data | Query Devtools: invalidated keys versus keys on screen; did a refetch fire | Key mismatch, HTTP or server cache, in-place cache mutation, two QueryClients | Key factory, `Cache-Control: no-store`, immutable `setQueryData`, one client |
| `No 'Access-Control-Allow-Origin' header is present on the requested resource` only in production | Preflight status and headers; the real status of the failed request | Gateway error without CORS headers, OPTIONS blocked by auth, origin not allowlisted | CORS before auth, explicit allowlist, headers on error responses, or same-origin proxy |
| Streamed answer appears all at once, or stops after about a minute | `curl -N` the origin directly and through the public URL | Proxy buffering, compression on the stream, idle timeouts | `proxy_buffering off`, no gzip on SSE, heartbeats, longer read timeout |
| `ResizeObserver loop completed with undelivered notifications` in error reports | Which component resizes itself inside its observer callback | A layout change in the callback triggers another resize in the same frame | Usually benign; defer the update with `requestAnimationFrame` or filter it from alerts |

### Q. Right after a deploy, Sentry shows a spike of `TypeError: Failed to fetch dynamically imported module`, and some users get a blank screen when they open a report page. What do you do?
**Short answer (45 seconds):** My first check is whether the failing sessions loaded the previous release: if old tabs are requesting chunk hashes that no longer exist, the deploy deleted the old assets. I contain by restoring the previous build's assets to the bucket and purging `index.html` from the CDN, then fix the cause so two versions can coexist.

**Deeper explanation:** Diagnosis in order:

```bash
# 1. Does the failing chunk exist? 404, HTML or JS?
curl -sI https://app.example.com/assets/Reports-3f9a1c.js | head -5
# 2. Is index.html cached?
curl -sI https://app.example.com/ | grep -iE 'cache-control|age'
# 3. Does the deploy delete old files?
grep -n -- '--delete' .github/workflows/deploy.yml
```

In Sentry, filter by release tag: if the failing events carry the old release, this is version skew. Ranked causes: `aws s3 sync --delete` or a fresh container removed old chunks while old tabs were open; `index.html` cached at the CDN, so new visitors get old HTML pointing at deleted files; the SPA fallback answers missing `/assets/*` with `index.html`, which shows up as a MIME type error; and a small background rate from ad blockers and flaky networks, which is normal. The blank screen happens because the lazy route throws during render and no error boundary sits around it, so React unmounts the whole root. Webpack apps report the same problem as `ChunkLoadError`.

```ts
window.addEventListener("vite:preloadError", (event) => {
  if (sessionStorage.getItem("chunk-reload")) return;   // tried once: let the boundary show
  sessionStorage.setItem("chunk-reload", "1");
  event.preventDefault();
  window.location.reload();                             // fetch the new index.html
});
```

Prevent: hashed assets get `Cache-Control: public, max-age=31536000, immutable` and `index.html` gets `no-cache`; deploys upload new assets before switching HTML and prune only files older than a few releases; an error boundary with a reload button wraps every lazy route; and an alert fires on chunk-error rate per release.

**Follow-ups they will ask:**
- Why not reload on every chunk error: a genuinely missing file would loop forever; the guard allows one try.
- How do you nudge long-lived tabs: poll a `version.json` and show "New version available" so users reload at a safe moment.

**Mistakes to avoid:**
- Blaming user networks because the message says "fetch".
- Rolling back with the same deleting deploy script, which strands users on the new version the same way.

### Q. Production shows a white screen while staging, built from the same commit, works. The console shows `TypeError: Failed to construct 'URL': Invalid URL`, and nothing reaches Sentry. Walk me through it.
**Short answer (45 seconds):** A white screen with nothing reported means the app died before React or the error tracker started, usually in module-scope code. With an invalid URL error, my first suspect is a build-time variable: `import.meta.env.VITE_API_URL` is replaced with its value during the build, so if the production build ran without it, `undefined` is baked into the bundle. I contain by redeploying the last good artifact, then make the build fail when a required variable is missing.

**Deeper explanation:** Steps:

```bash
# Which API host is baked into the deployed bundle?
curl -s https://app.example.com/ | grep -o 'assets/index-[^"]*\.js'
curl -s https://app.example.com/assets/index-8c1d2e.js | grep -oE 'https://api[^"]*' | sort -u
# Is it defined for the production job?
grep -n 'VITE_' .github/workflows/deploy.yml
```

Ranked causes: the variable is defined for the staging environment in CI but not for production; the Docker image is built once with staging values and promoted, but `VITE_*`, `NEXT_PUBLIC_*` and `REACT_APP_*` values are fixed at build time, so setting them on the container changes nothing; or a typo or missing `VITE_` prefix, since Vite exposes only prefixed variables to client code.

Why a white screen with no report: `new URL(import.meta.env.VITE_API_URL)` ran at import time, before `createRoot` and before Sentry initialized. Error boundaries only catch errors thrown while rendering inside the tree, so no boundary could help.

```ts
// scripts/check-env.ts: runs before `vite build`; CI provides these as environment variables
import { z } from "zod";
z.object({ VITE_API_URL: z.string().url(), VITE_SENTRY_DSN: z.string().min(1) }).parse(process.env);
```

Prevent the rest: initialize Sentry in its own first-imported module, report through React 19's `createRoot(el, { onUncaughtError })` plus a root error boundary, and add a small inline `window.onerror` script in `index.html` that shows a reload message if the app never mounts.

**Follow-ups they will ask:**
- How do you build once and deploy everywhere: runtime config from `/config.json` or a server-injected `window.__APP_CONFIG__`; build-time variables only for values that never differ.
- Can secrets go in that runtime config: no, everything the browser downloads is public.
- In Next.js: `NEXT_PUBLIC_*` is inlined at `next build`; server-only variables are read at runtime on the server.

**Mistakes to avoid:**
- Setting the variable on the running container and expecting the static bundle to change.
- Adding more error boundaries, which cannot catch module-scope errors.

### Q. After a release, Sentry shows `Hydration failed because the initial UI does not match what was rendered on the server` on the order details page, only for some users, and you cannot reproduce it. How do you track it down?
**Short answer (45 seconds):** I segment the events first: release, browser, and what the affected users share, such as time zone, locale, logged-in state, a flag variant or an extension. Then I reproduce with a production build under those conditions, read the diff React prints in development, and check what the release changed in that page's first render. The page usually still works, but React re-renders that part on the client, costing speed and causing flashes.

**Deeper explanation:** Steps in order:

1. Group Sentry events by release, browser and custom `timezone` and `locale` tags; React 18 production builds report this as minified errors #418 and #425.
2. Reproduce under the user's conditions:

```ts
const context = await browser.newContext({ timezoneId: "Asia/Dubai", locale: "ar-AE" });
const page = await context.newPage();
page.on("console", (m) => { if (m.type() === "error") console.log(m.text()); });
await page.goto("https://staging.example.com/orders/123");
```

3. Diff the release for render-time code: `toLocaleString` or `Intl.DateTimeFormat` without a fixed time zone, `Date.now()`, client-side flag evaluation, `localStorage`, `typeof window` branches.
4. Request the HTML with two users' cookies; if A's markup comes back for B, a cache is storing personalized pages.

Ranked causes for "only some users": time zone or locale formatting (server renders UTC, browser renders Dubai time); a flag variant evaluated differently on server and client; personalized HTML from a shared cache; CMS rich text with invalid nesting such as `p` inside `p`; and DOM-editing extensions, which an incognito retry confirms.

Fix the cause, not the warning: format dates with an explicit time zone from a cookie or profile, evaluate flags once on the server and pass them down, mark personalized responses `private, no-store`, and sanitize CMS markup.

Prevent: a Playwright smoke test that loads key pages in a non-UTC time zone and fails on any hydration console error, and an alert when hydration errors per release rise above baseline.

**Follow-ups they will ask:**
- Why not `suppressHydrationWarning`: it covers one element's text only and hides real bugs.
- It turns out to be an extension: React 19 skips unexpected tags extensions insert in `head` and `body`; filter confirmed cases out of alerts.

**Mistakes to avoid:**
- Wrapping the page in `ssr: false` to make the error go away.
- Testing only in your own time zone and declaring it fixed.

### Q. A filter panel crashes with `Maximum update depth exceeded`, but only when the page is opened from a URL that already contains filters. How do you debug and fix it?
**Short answer (45 seconds):** The error means updates are scheduling each other in a cycle, almost always an effect that sets state and depends on a value that is new every render, or two pieces of state syncing each other. I read the component stack, inspect that component's effects and dependencies, and look for state that mirrors props, the URL or a store. The fix is usually to stop syncing: derive during render or stabilize the dependency.

**Deeper explanation:** Steps: reproduce with the exact URL; in React DevTools turn on "Highlight updates when components render" and the Profiler's "Record why each component rendered" to see what changes each pass. The usual shape:

```ts
// Bug: a new object every render when the URL has filters
const filters = parseFilters(searchParams);
useEffect(() => {
  setDraft(filters);          // update -> render -> new filters -> effect again
}, [filters]);

// Fix 1: no copy; the URL is the state
const filters = parseFilters(searchParams);
// Fix 2: a local draft that resets when the URL changes: remount with a key
<FilterForm key={searchParams.toString()} initial={parseFilters(searchParams)} />
```

Why only with filters in the URL: with an empty query string, `parseFilters` returned a shared default constant, so the dependency was stable and the loop never started.

Other causes: one effect writes state into the URL with `router.replace` while another copies the URL back into state, and a Zustand v5 selector returning a new object, such as `useStore((s) => ({ a: s.a, b: s.b }))`, which loops and logs the "getSnapshot should be cached" warning; wrap it in `useShallow`.

Prevent: keep `react-hooks/exhaustive-deps` on and fix warnings rather than suppress them, prefer derived values over effects that copy state, and add a component test that renders with a populated URL and asserts the form appears.

**Follow-ups they will ask:**
- An equality check before `setState`: fine as a stopgap, but it hides the cycle.
- The loop runs through a parent and child, a child effect calling `onChange`: lift the state up or make the child fully controlled, so there is one owner.

**Mistakes to avoid:**
- Removing the dependency from the array to stop the loop, which swaps it for a stale closure bug.
- Adding a ref flag to skip "the second run" without understanding the cycle.

### Q. Operators keep the dispatch console open for a whole shift. After a few hours it gets sluggish and Chrome eventually kills the tab for running out of memory. How do you find and fix the leak?
**Short answer (45 seconds):** First I confirm it is a leak: memory that climbs with each repeated action and never drops after garbage collection. I reproduce with a scripted session, watch heap size, DOM nodes and listener counts in the Performance monitor, then compare heap snapshots before and after repeating one action to see what is retained and by whom. Containment is capping the obvious buffers; the real fix is the cleanup the retainer path points to.

**Deeper explanation:** Steps:

1. Reproduce on a production build with a script that repeats one workflow fifty times, watching the Performance monitor: if DOM Nodes and JS event listeners climb each cycle, something holds old screens.
2. Memory panel: take a heap snapshot, repeat the cycle ten times, force garbage collection, take another, and use the Comparison view. Filter for "Detached" to find DOM trees removed from the page but still referenced, and follow the Retainers panel to the closure, listener or array holding them.
3. Automate with memlab, which reports leaked objects with retainer traces:

```js
// scenario.js, run with: npx memlab run --scenario scenario.js
module.exports = {
  url: () => "http://localhost:4173/dispatch",
  action: async (page) => { await page.click("[data-testid=open-order]"); },
  back: async (page) => { await page.click("[data-testid=close-order]"); },
};
```

Ranked causes: an unbounded feed or log array in a store; subscriptions, intervals or `window` listeners without cleanup; chart or map instances never destroyed; Three.js geometries and textures never disposed; unbounded hand-rolled caches; and large objects passed to `console.log`, retained while DevTools is open.

Fix: ring buffers that keep the last N items, effects that return cleanups (`unsubscribe`, `clearInterval`, `removeEventListener`, `chart.destroy()`, `dispose()`), and LRU limits on caches. TanStack Query already drops inactive queries after `gcTime`, so do not set it to `Infinity` for per-record keys.

Prevent: memlab in CI for the main workflows and a soak test that fails if the heap after a hundred cycles exceeds a threshold.

**Follow-ups they will ask:**
- How do you tell a leak from a cache: a cache levels off; a leak grows with every repetition.
- High GPU process memory: check Chrome's task manager and `renderer.info.memory`.

**Mistakes to avoid:**
- Concluding from one snapshot instead of comparing across repeated actions.
- Shipping a forced periodic reload as the fix rather than as a stopgap.

### Q. A user edits an order, the API returns 200, but the orders list keeps showing the old status until a hard refresh. The app uses TanStack Query. What do you check?
**Short answer (45 seconds):** I split the problem with the Network tab and React Query Devtools: did a refetch of the list happen after the mutation, and if so, did the server return fresh data? No refetch points at the client cache: wrong keys, invalidation that never ran, or a cache mutated in place. A refetch with old data points at a cache below: HTTP, CDN, server-side or a read replica.

**Deeper explanation:** No refetch, ranked:
- Key mismatch: the list lives under `["orders", "list", { status: "open" }]` but the code invalidates `["order", id]`. Invalidation matches by prefix, so a key factory with one root covers every list variant.
- Callbacks that never fired: callbacks passed to `mutate(vars, { onSuccess })` do not run if the component unmounted first. Put invalidation in `useMutation`'s own `onSuccess` or `onSettled`.
- In-place mutation in `setQueryData`: pushing into the cached array keeps the same reference, so nothing re-renders.
- Two `QueryClient` instances, for example `new QueryClient()` inside a component body.

```ts
export const orderKeys = {
  all: ["orders"] as const,
  lists: () => [...orderKeys.all, "list"] as const,
  list: (f: Filters) => [...orderKeys.lists(), f] as const,
  detail: (id: string) => [...orderKeys.all, "detail", id] as const,
};
useMutation({
  mutationFn: updateOrder,
  onSuccess: (order) => {
    queryClient.setQueryData(orderKeys.detail(order.id), order);
    return queryClient.invalidateQueries({ queryKey: orderKeys.lists() });
  },
});
```

Refetch with old data, ranked: the GET carries `Cache-Control: max-age`, so the browser answers from its cache (Size column: "(disk cache)"); a CDN caches the API; a stale Redis cache or lagging replica on the backend; or in Next.js the list is rendered by a server component, so the write also needs `revalidatePath("/orders")` or `router.refresh()`.

Prevent: an MSW integration test that edits an order and asserts the list changes, `@tanstack/eslint-plugin-query`, and `no-store` on personalized API responses.

**Follow-ups they will ask:**
- Update the cache directly or invalidate: set the detail from the response, invalidate lists, because filtering and sorting rules live on the server.
- Another user changes the order: invalidation covers only your writes; use focus refetch, polling or a push event.

**Mistakes to avoid:**
- Setting `staleTime: 0` and `refetchOnMount: "always"` everywhere as a blanket fix.
- Calling `refetch()` on one hard-coded query instead of invalidating by key prefix.

### Q. The frontend works locally, but in production every POST to the API fails with "No 'Access-Control-Allow-Origin' header is present on the requested resource" while GETs work. What do you do?
**Short answer (45 seconds):** Locally the Vite dev server proxies `/api`, so the browser never made a cross-origin request and CORS was never tested. In production, GETs working and POSTs failing points at the preflight: a JSON body or an `Authorization` header makes the browser send `OPTIONS` first. I reproduce the preflight with `curl`, read its status and headers, and fix the server or gateway.

**Deeper explanation:**

```bash
curl -si -X OPTIONS https://api.example.com/orders \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,authorization" | head -20
```

Ranked causes:
1. The preflight reaches auth middleware and gets a 401 without CORS headers, or the gateway has no `OPTIONS` route.
2. The real response is an error, such as a 502 from the load balancer, a 413 from Nginx or a WAF block, whose error page carries no CORS headers, so the browser reports CORS instead. Check the status and server logs first.
3. The production origin is missing from the allowlist: `www` versus the apex domain, a new domain, or `http` versus `https`.
4. Credentials with a wildcard: with `credentials: "include"` the browser rejects `Access-Control-Allow-Origin: *` and needs the exact origin plus `Access-Control-Allow-Credentials: true`.
5. Both the app and the gateway add the header, and the browser rejects multiple values.
6. A CDN caches a response carrying one origin's header without `Vary: Origin`.

```js
app.use(cors({ origin: ["https://app.example.com"], credentials: true, maxAge: 600 }));
app.use(authMiddleware);         // after cors, so preflights never reach auth
```

The `cors` middleware answers `OPTIONS` itself when mounted before the routes; on API Gateway, also add the headers to the default 4XX and 5XX gateway responses. Often the cleanest fix is no CORS at all: route `app.example.com/api` to the backend through the CDN or reverse proxy, so the browser sees one origin.

Prevent: a post-deploy smoke test that runs this preflight against production domains, an allowlist validated at startup, and staging with production's domain layout.

**Follow-ups they will ask:**
- Why does Postman work: CORS is enforced by browsers; other clients are never blocked.
- Can the frontend use `mode: "no-cors"`: no, it returns an opaque response the code cannot read.

**Mistakes to avoid:**
- Setting `Access-Control-Allow-Origin: *` everywhere, which breaks cookies and widens exposure.
- Editing CORS config when the real response was a 502.

### Q. The AI chat streams token by token locally, but in production the answer arrives all at once after a long pause, and long answers stop at about the one-minute mark. Where do you look?
**Short answer (45 seconds):** Both symptoms point at something between the browser and the Node server, not at React. "All at once" means a layer is buffering the response: a reverse proxy, a CDN or compression middleware. "Stops near a minute" matches an idle or read timeout on a proxy or load balancer. I compare the stream from the origin directly with the stream through the public URL using `curl -N`, then fix buffering and timeouts on the streaming route and add heartbeats.

**Deeper explanation:**

```bash
# Through the public URL: do lines arrive spread out or in one burst?
curl -N -s -H "Accept: text/event-stream" -H "Cookie: $COOKIE" \
  "https://app.example.com/api/chat/stream?runId=abc" | while read -r line; do echo "$(date +%T) $line"; done
# Same request to the pod, bypassing the proxy chain
kubectl port-forward deploy/chat-api 3000:3000 &
curl -N -s "http://localhost:3000/api/chat/stream?runId=abc" | head
```

In the public response headers, `Content-Encoding: gzip` means something is compressing, and so buffering, the stream.

Ranked causes: Nginx buffers proxied responses by default (`proxy_buffering on`); Express `compression()` or a CDN holds bytes until a block fills; and idle timeouts, since Nginx `proxy_read_timeout` and the AWS ALB idle timeout both default to 60 seconds, which closes a stream that goes quiet during a long tool call.

```nginx
location /api/chat/ {
  proxy_pass http://chat_api;
  proxy_http_version 1.1;
  proxy_set_header Connection "";
  proxy_buffering off;
  proxy_cache off;
  gzip off;
  proxy_read_timeout 1h;
}
```

On the Node side, send `X-Accel-Buffering: no`, call `res.flushHeaders()`, exclude `text/event-stream` from compression, and write a comment line (`: ping`) every 15 seconds so no idle timer fires; raise the load balancer idle timeout too.

Prevent: a synthetic check through the public URL that fails if the first event is slow or the stream ends early, and a staging environment with the same proxy chain.

**Follow-ups they will ask:**
- Why heartbeats if you raised the timeout: corporate proxies and other layers you do not control have their own idle timers.
- The stream drops anyway: the client reconnects with the last event id and resumes, which is why events carry ids.

**Mistakes to avoid:**
- Rewriting the React rendering code when `curl` already shows the burst.
- Raising every timeout to an hour across the whole proxy instead of scoping it to the streaming route.

### Practice
- Break it on purpose: build a Vite app with a lazy route, serve it with `vite preview`, open it in a tab, rebuild so the old assets are deleted, then click the lazy route in the old tab; record the exact error in Chrome and Firefox, then add asset retention and the `vite:preloadError` reload guard and repeat.
- Put Nginx with default proxy settings in front of an Express SSE endpoint using Docker Compose, watch `curl -N` show the burst, then apply the streaming location block and a heartbeat and confirm events arrive spread out.
- Leak on purpose: add a `setInterval` and a `window` listener without cleanup to a modal, open and close it twenty times, find both in a heap snapshot comparison, then prove the fix with memlab.
- Format a date with `toLocaleString()` in a server-rendered component, run Playwright with `timezoneId: "Asia/Kolkata"`, make the test fail on the hydration console error, then fix the component and watch it pass.
- Say it out loud: "Users say the app shows a white screen since this morning." Give your first ten minutes: the questions you ask, the dashboards you open, your containment decision, and who you tell.
