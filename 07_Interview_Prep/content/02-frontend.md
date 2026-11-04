# Frontend & React at Scale

> This track covers the React knowledge that separates a senior frontend engineer from someone who can "make it work": how React actually renders, how hooks behave under the hood, how to manage state and data in large applications, how to keep a growing codebase fast and maintainable, and how to build the streaming, agent-driven UIs that AI products need. Interviewers for AI Full Stack roles use frontend rounds to check that you can own the product surface end to end: the model call is only half of the feature, the other half is a UI that stays responsive while tokens stream in, recovers from failures, and does not fall apart when ten engineers work on it.

## React Rendering Model

> Interviewers probe this to find out whether you understand React or merely use it. A weak answer talks about the "virtual DOM being fast". A strong answer separates render from commit, explains what triggers a re-render, knows why keys exist, and can say what concurrent rendering changes about the guarantees your code can rely on.

### Concepts you must understand
- Rendering is React calling your component functions to produce a tree of element objects; committing is applying the computed diff to the DOM. They are separate phases with different rules and different hooks.
- Reconciliation compares the new element tree with the previous one by element type and position (or key) and decides what to mount, update, or unmount; Fiber is the data structure and work loop that make this incremental and interruptible.
- A component re-renders when its own state changes, when its parent re-renders, or when a context it reads changes. Props "changing" is a consequence of the parent rendering, not an independent trigger.
- Keys give siblings an identity across renders; index keys break the moment a list is reordered, inserted into, or filtered, because state and DOM get attached to the wrong item.
- React 18 batches every state update in the same tick, including updates inside promises, timeouts, and native event listeners (automatic batching); `flushSync` opts a specific update out.
- Concurrent rendering lets React pause, discard, or restart a render in progress so urgent work (typing) is not blocked by slow work (filtering a large list). Transitions are how you mark work as non-urgent.
- Render functions must be pure: StrictMode calls them twice in development to expose impure code, and concurrent React may run a render that is never committed.
- The React Compiler automatically memoizes components and hook results when code follows the Rules of React, which removes most hand-written `useMemo` and `useCallback`.

### Q. Walk me through what happens between a setState call and the DOM changing.
**Short answer (45 seconds):** The setter does not render anything; it enqueues an update on that component's fiber with a priority and schedules work. React then runs the render phase: it calls the component function and its descendants, builds a work-in-progress fiber tree, and diffs it against the current tree to collect effects such as "update this attribute" or "insert this node". Finally the commit phase applies those mutations to the DOM in one synchronous pass, runs layout effects, lets the browser paint, and then runs passive effects (`useEffect`).

**Deeper explanation:** The separation matters because the two phases have different guarantees. The render phase is pure and interruptible: React can run it, throw the result away, and run it again, so anything you do there (your component body, `useMemo` callbacks) must have no side effects. The commit phase is synchronous and never interrupted, which is why `useLayoutEffect` and ref attachment happen there and why you can measure the DOM in a layout effect without seeing a half-applied UI.

```text
setCount(c => c + 1)
  -> update queued on the fiber, lane (priority) assigned, work scheduled
render phase (pure, interruptible)
  -> call component functions, build workInProgress tree, diff vs current
commit phase (sync, atomic)
  -> apply DOM mutations, attach refs, run useLayoutEffect, swap trees
browser paints
passive effects
  -> run useEffect cleanups, then useEffect callbacks
```

React reads the setter's argument lazily: functional updaters are applied in order during render, which is why `setCount(c => c + 1)` twice gives +2 while `setCount(count + 1)` twice gives +1.

**Follow-ups they will ask:**
- Why is state not updated right after calling the setter: the update is queued; the new value exists only in the next render's closure.
- Where do refs get attached: during commit, after DOM mutation, before layout effects run.
- Can the render phase be skipped for a subtree: yes, when a memoized component receives identical props or when React bails out because state did not change.

**Mistakes to avoid:**
- Saying "setState updates the DOM" or "the virtual DOM makes it fast". The win is batching and minimal mutation, not raw speed.
- Describing `useEffect` as part of rendering. It runs after commit and paint.

### Q. What is reconciliation, and why did React need Fiber to do it well?
**Short answer (45 seconds):** Reconciliation is the diffing step: given a new tree of elements and the previous one, React decides which DOM nodes to keep, update, or replace. It uses two heuristics: elements of different types produce entirely different subtrees, and siblings are matched by key. Fiber is the rewrite of the engine that turned this from one recursive, uninterruptible pass into a linked list of small units of work that can be paused and resumed.

**Deeper explanation:** Before Fiber, the reconciler walked the tree recursively on the call stack, and a large update blocked the main thread until it finished. Fiber gives every component instance and host node a fiber object with `child`, `sibling`, and `return` pointers, an update queue, and an effect tag. The work loop processes one fiber at a time and asks the scheduler whether to yield to the browser, which makes time slicing possible. React keeps two trees, `current` and `workInProgress`, and commit swaps the pointer, so a half-finished render is never visible.

The diffing rules to state: a `<div>` replaced by a `<span>` at the same position unmounts the whole subtree, state included; siblings are matched by key, otherwise by index; a component whose type is the same function updates in place. This is why defining a component inside another component is a bug: each render produces a new function identity, so React remounts the child every time.

**Follow-ups they will ask:**
- Is the diff O(n): yes, React trades a perfect tree diff for a linear heuristic based on type and key.
- What is a "lane": the priority bitmask attached to updates so React can process urgent updates before transitions.
- What triggers a remount rather than an update: a different element type at the same position, or a changed key.

**Mistakes to avoid:**
- Claiming Fiber made rendering "asynchronous by default". Rendering stays synchronous for urgent updates; concurrency is opt-in through transitions, Suspense, and deferred values.
- Describing reconciliation as comparing DOM nodes. It compares element objects; the DOM is touched only in commit.

### Q. Why does React insist on keys, and what actually goes wrong with index keys?
**Short answer (45 seconds):** Keys tell the reconciler which sibling in the new list corresponds to which sibling in the old list. Without them React matches by position, so when you prepend or remove an item every element after that point looks "changed", and more importantly component state and uncontrolled DOM state stay attached to the position rather than the data. Index keys recreate exactly that positional matching, so they are only safe for static lists that never reorder or filter.

**Deeper explanation:** The symptom people hit in production: a list of rows each containing an input; delete the second row and the third row's typed text appears in the second row. React kept the fiber at index 1, updated its props to the third item, and the input's uncontrolled value never moved. The same mechanism causes wrong animation targets and leaked `useState` values.

```ts
// Breaks on reorder/delete: state follows the position
{todos.map((t, i) => <TodoRow key={i} todo={t} />)}

// Correct: state follows the entity
{todos.map((t) => <TodoRow key={t.id} todo={t} />)}
```

Keys only need to be unique among siblings, not globally. Changing a key deliberately is a legitimate tool: giving a form `key={userId}` resets all its internal state when the user changes, which is cleaner than syncing state with an effect. Generating keys with `Math.random()` or `crypto.randomUUID()` during render is the opposite mistake: every render produces new keys, so every item unmounts and remounts.

**Follow-ups they will ask:**
- What if the API gives no id: build a stable composite from immutable fields, or assign an id once when the data enters the client, never during render.
- Do keys affect performance or only correctness: both; wrong keys cause remounts, which are far more expensive than updates.
- Can two different lists reuse the same key values: yes, uniqueness is per parent.

**Mistakes to avoid:**
- Saying index keys are "fine as long as there is no warning". The warning only fires for missing keys, not for wrong ones.
- Using the array index to silence the lint rule on a list that can be sorted or filtered.

### Q. What causes a component to re-render, and what does not?
**Short answer (45 seconds):** Three things: its own state changed (via `useState` or `useReducer`), its parent rendered, or a context it subscribes to changed value. That is the whole list. Props do not trigger renders on their own; they change because the parent rendered. Refs changing never trigger a render. A memoized component (`React.memo`) is the only case where a parent render can be skipped, and only if its props are shallow-equal.

**Deeper explanation:** The consequence most engineers miss: by default, when a component renders, all of its children render too, regardless of whether their props changed. Re-rendering is usually cheap, because reconciliation then finds nothing to commit, so the question is not "how do I stop re-renders" but "where is a re-render expensive enough to matter". Typical culprits are a large list, a heavy chart, or a provider at the top of the tree whose value object is recreated every render, which re-renders every consumer.

Two structural fixes beat memoization: push state down to the component that needs it so fewer components sit under the updating one, and lift expensive children up as `children` props so they are created by a parent that does not re-render.

```ts
// Expensive children are created by App and passed down; toggling `open`
// re-renders Layout but <HeavyTable /> is the same element object, so it bails out.
function Layout({ children }) {
  const [open, setOpen] = useState(false);
  return <div onClick={() => setOpen(!open)}>{open && <Sidebar />}{children}</div>;
}
```

React also bails out of a state update when the new value is `Object.is`-equal to the old one, which is why `setItems(items)` with the same array reference does nothing.

**Follow-ups they will ask:**
- Does a context change re-render components that only pass the provider through: no, only components that call `useContext` on it.
- How do you see which components rendered and why: React DevTools Profiler with "Record why each component rendered" enabled.
- Does changing a ref value re-render: never; refs are for values React should not react to.

**Mistakes to avoid:**
- Saying "props changed so it re-rendered". The parent rendered; props being different is incidental.
- Wrapping everything in `React.memo` as a first response. It costs a comparison on every render and is defeated by any inline object or function prop.

### Q. What is automatic batching in React 18, and when would you bypass it?
**Short answer (45 seconds):** Batching means several state updates in the same tick produce one render instead of one per setter call. Before React 18 that only happened inside React event handlers; updates inside a `setTimeout`, a resolved promise, or a native listener each caused a separate render. With `createRoot`, React 18 batches everywhere. You bypass it with `flushSync` from `react-dom` when you need the DOM updated synchronously, typically to measure or scroll right after a state change.

**Deeper explanation:** Batching is both a performance feature and a consistency feature: without it, an `await fetch()` followed by `setData(x); setLoading(false);` would render an intermediate frame where data is present but the spinner still shows. Automatic batching is tied to the new root API; apps still mounted with the legacy `ReactDOM.render` keep the old behaviour, which is one reason migrations to 18 occasionally change timing-dependent code.

```ts
import { flushSync } from "react-dom";

function addMessage(msg: Message) {
  flushSync(() => setMessages((prev) => [...prev, msg]));
  // DOM now contains the new row, so this scrolls to it
  listRef.current?.lastElementChild?.scrollIntoView({ block: "end" });
}
```

`flushSync` forces a synchronous render and commit, so it should be rare and never inside a render or an effect that could run on every update. For "run after the DOM updates" the normal tool is `useLayoutEffect`, which runs after commit but before paint and does not break batching.

**Follow-ups they will ask:**
- Does batching change the order of updaters: no, functional updaters are applied in call order during the next render.
- Is batching the same as debouncing: no; batching merges updates inside one tick, debouncing delays work across time.
- How do you log the "current" state right after a setter: you cannot; read it in the next render, an effect, or keep the value in a local variable.

**Mistakes to avoid:**
- Claiming `flushSync` is how you "fix" stale state. It forces a render; it does not change closure semantics.
- Forgetting that batching requires `createRoot`; the legacy root behaves like React 17.

### Q. Explain concurrent rendering. What does "interruptible" mean in practice?
**Short answer (45 seconds):** Concurrent rendering means React can start rendering an update, pause partway to handle a more urgent update, and either resume or throw the paused work away. Nothing runs in parallel; the main thread is still single-threaded. The practical result is that a transition-marked update, like filtering ten thousand rows, no longer freezes the input box the user is typing into, because keystrokes are high priority and the filtering render yields to them.

**Deeper explanation:** You opt in per update. `startTransition` (or `useTransition`, which adds an `isPending` flag) marks state updates as non-urgent; `useDeferredValue` gives you a lagging copy of a value that React updates in a low-priority render. Everything else stays synchronous and urgent. During a transition React keeps showing the old UI until the new tree is ready, so the user never sees a half-rendered state, and if a new transition arrives the stale one is abandoned instead of committed.

```ts
const [isPending, startTransition] = useTransition();

function onSearch(e: React.ChangeEvent<HTMLInputElement>) {
  setQuery(e.target.value);                       // urgent: keep the input live
  startTransition(() => setFilter(e.target.value)); // non-urgent: may be interrupted
}
```

Interruptibility imposes rules on your code: render must be pure, because a render might run and never commit; `useEffect` must not assume one effect per render; and reading mutable external stores during render needs `useSyncExternalStore`, otherwise different components can see different values in one frame (tearing). Suspense is the other half of the story: while a transition waits on suspended data, React keeps the old screen instead of flashing a fallback.

**Follow-ups they will ask:**
- Does this make long computations faster: no, it makes them yield; the total CPU time is the same or slightly higher.
- What happens to a transition when a new one starts: the in-progress render is discarded and work restarts with the latest state.
- Which API would you use for an expensive child receiving a prop: `useDeferredValue` on the prop, with `memo` on the child so the deferred render is cheap to skip.

**Mistakes to avoid:**
- Calling it "multi-threaded React" or confusing it with web workers.
- Wrapping every update in a transition. Transitions delay feedback, so controlled inputs must stay urgent.

### Q. My effect runs twice on mount in development. Is that a bug in React?
**Short answer (45 seconds):** No, it is StrictMode doing its job. In development, StrictMode double-invokes render functions to catch impure components, and since React 18 it also mounts, unmounts, and re-mounts each component once so you see whether your effect cleanups actually undo the setup. Production runs each effect once. If the double run breaks your app, the effect was missing a cleanup or was doing something that cannot be safely repeated.

**Deeper explanation:** The simulated unmount exists because React wants to be able to unmount a component and restore its state later (the mechanism behind preserving state in hidden tabs and back navigation). Any effect that survives that round trip, subscribe then unsubscribe then subscribe, is correct; one that leaks a socket, double-registers a listener, or fires an analytics event twice has a real bug that would also show up in production during fast navigations.

```ts
useEffect(() => {
  const controller = new AbortController();
  fetch(`/api/items?q=${q}`, { signal: controller.signal })
    .then((r) => r.json())
    .then(setItems)
    .catch((e) => { if (e.name !== "AbortError") setError(e); });
  return () => controller.abort(); // the second mount cancels the first request
}, [q]);
```

StrictMode also double-invokes `useMemo` and `useReducer` functions and the initializer passed to `useState`, which flushes out code that mutates state during render. Fixes are structural: make render pure, move one-time initialization into a module-level lazy or into the server, and never rely on "mount runs exactly once" for side effects like posting data.

**Follow-ups they will ask:**
- How do you run something exactly once per page load: not in an effect; use a module-level flag, a ref guard, or do it where the event originates.
- Does StrictMode affect production builds: no, all its checks are stripped.
- Why is double rendering safe: because render is supposed to be pure; if it is not, the duplication reveals the impurity.

**Mistakes to avoid:**
- Removing StrictMode to make the warning go away.
- Guarding effects with a `didRun` ref as a general pattern; it hides the missing cleanup instead of adding it.

### Q. What does the React Compiler do, and does it make memo and useMemo obsolete?
**Short answer (45 seconds):** The React Compiler is a build-time plugin that analyses components and hooks and inserts fine-grained memoization automatically: it caches JSX subtrees, computed values, and callbacks so a component only recomputes the parts whose inputs changed. It relies on the Rules of React, especially purity and not mutating props or state. For code that follows those rules it replaces most manual `useMemo`, `useCallback`, and `React.memo`; it does not remove the need to understand why re-renders happen, and it skips components it cannot prove safe.

**Deeper explanation:** Manual memoization fails in both directions: people forget it where it matters, sprinkle it where it costs more than it saves, and one unstable dependency defeats a chain. The compiler does the analysis mechanically at expression granularity, finer than a component boundary. It bails out of components it cannot reason about, such as conditional hook calls or mutation of a captured value, which is why adoption starts with the `react-compiler` ESLint rules.

What it does not do: change how state triggers renders, make expensive algorithms cheaper, memoize across a boundary it cannot see such as a prop object built by a third-party library, or help with a context value that changes constantly. The architectural advice stays: colocate state, split contexts, virtualize large lists. The compiler removes boilerplate and the "forgot a useCallback" class of regressions.

**Follow-ups they will ask:**
- Can you adopt it incrementally: yes, it can be scoped to directories or opted in per file, and existing manual memoization is left in place.
- Does it work with React 18: it targets React 19; older versions need a runtime shim and have fewer guarantees.
- How do you verify it is doing anything: React DevTools shows a "Memo" badge on compiled components, and the Profiler shows reduced render counts.

**Mistakes to avoid:**
- Saying the compiler "makes React fast" in general. It optimizes re-render skipping, nothing else.
- Assuming it fixes code that mutates props or state; such components are skipped.

### Practice
- Build a list of 50 rows with an uncontrolled input per row, keyed by index, delete a middle row, and watch the text shift. Fix it with stable ids and explain what moved.
- Add a search box over 20,000 generated rows; measure typing latency with the Performance panel, then wrap the filtering in `startTransition` and compare the long-task timeline.
- Mount a `WebSocket` in an effect without cleanup under StrictMode and observe the duplicate connection in the Network tab; add the cleanup and confirm one connection survives.
- Say it out loud: explain to a junior engineer the difference between the render phase and the commit phase, including where refs, layout effects, and passive effects run, in under two minutes.

## Hooks Deep Dive

> Hooks questions are where interviewers separate "has used React for years" from "understands React". Weak answers recite the docs: useEffect for side effects, useMemo for performance. Strong answers explain timing, closure semantics, and the cost model, and can point at a concrete bug each hook is designed to avoid. Expect at least one question that is really about JavaScript closures wearing a React costume.

### Concepts you must understand
- Every render creates a fresh closure; hooks are how React persists values across those closures, indexed by call order, which is why hooks cannot be called conditionally.
- `useEffect` runs after commit, normally after paint; the cleanup of the previous run executes before the next run and on unmount. Dependencies decide when "the next run" happens; they are not a cache key.
- A stale closure is an effect, timer, or event handler that captured an old render's variables; the fix is functional updates, moving the logic inside the effect, a latest-value ref, or `useEffectEvent`.
- `useMemo` and `useCallback` only pay off when the consumer relies on referential identity (a memoized child, another hook's dependency array) or the computation is measurably expensive; otherwise they cost memory and a comparison for nothing.
- `useRef` is a mutable box React does not watch: use it for DOM nodes, instance variables such as timers and sockets, "previous value" tracking, and the latest-callback pattern.
- `useReducer` centralizes state transitions as a pure function, gives you a stable `dispatch`, and is the natural home for state machines and multi-field state that changes together.
- `useLayoutEffect` runs synchronously after DOM mutation and before paint; it is for measurement that must not flicker, nothing else.
- `useSyncExternalStore` is the only safe way to read a mutable store outside React during concurrent rendering; it prevents tearing and supports server snapshots.
- `useId` produces ids that are stable between server and client for linking labels, descriptions, and ARIA attributes; it is never a key.
- A custom hook is an API: stable return identities, an options object, built-in cleanup, and SSR safety are what make it reusable across teams.

### Q. Explain the full lifecycle of a useEffect: when it runs, when cleanup runs, and how useLayoutEffect differs.
**Short answer (45 seconds):** After React commits a render, it runs layout effects synchronously before the browser paints, then paints, then runs passive effects (`useEffect`). On every subsequent render where any dependency changed, React first runs the previous effect's cleanup and then the new effect body, in that order, with the new render's values. On unmount, only the cleanup runs. `useLayoutEffect` has the same dependency semantics but runs in the pre-paint window, so you can measure the DOM and set state without the user seeing an intermediate frame.

**Deeper explanation:** The cleanup-then-effect ordering is the mental model that fixes most effect bugs: the cleanup always belongs to the render that created the effect and closes over that render's values, so unsubscribing from `oldRoomId` while subscribing to `newRoomId` works without extra bookkeeping.

```ts
useEffect(() => {
  const socket = connect(roomId);        // this render's roomId
  socket.on("message", onMessage);
  return () => socket.close();           // closes the socket for the same roomId
}, [roomId]);
```

React 18 added one timing nuance: effects caused by a discrete user input such as a click are flushed synchronously before the next event, so a click handler that sets state and an effect reading that state cannot interleave with another click. Layout effects block paint, so they must be cheap; a `setState` inside one triggers a synchronous re-render before paint, which is exactly the tool for "measure the tooltip, then position it" and exactly the wrong tool for data fetching.

**Follow-ups they will ask:**
- What happens with an empty dependency array: runs after mount, cleanup on unmount, plus the extra StrictMode cycle in development.
- Can the effect see state it just set: no, it sees the closure of the render that scheduled it; the updated value arrives in the next render's effect.
- Does `useLayoutEffect` run on the server: no, neither effect type runs during SSR; measurement code must tolerate a first client render without layout.

**Mistakes to avoid:**
- Calling effects "componentDidMount" and "componentDidUpdate"; the cleanup-first model is different and the deps array is not a lifecycle switch.
- Using `useLayoutEffect` for anything that is not a synchronous measurement; it delays paint.

### Q. What is a stale closure in React and how do you fix one without disabling the lint rule?
**Short answer (45 seconds):** Each render captures its own copy of props and state. If an effect, interval, or subscription callback was created in an earlier render and keeps running, it sees that earlier render's values, so a counter interval set up with `[]` deps keeps adding to the same stale `count`. The fixes are to use functional updates so you never read state, to include the value in the dependency array and let the effect re-subscribe, to keep the latest value in a ref, or to use `useEffectEvent` for the non-reactive part of an effect.

**Deeper explanation:** The exhaustive-deps lint rule is right far more often than it is wrong: a missing dependency is a stale closure waiting for the right timing to bite. The real question is which fix is appropriate.

```ts
// 1. Functional update: no state read, no dependency needed
useEffect(() => {
  const id = setInterval(() => setCount((c) => c + 1), 1000);
  return () => clearInterval(id);
}, []);

// 2. Latest-ref: the subscription stays, the handler stays fresh
const onMessageRef = useRef(onMessage);
useEffect(() => { onMessageRef.current = onMessage; });
useEffect(() => {
  const socket = connect(roomId);
  socket.on("message", (m) => onMessageRef.current(m));
  return () => socket.close();
}, [roomId]);
```

The latest-ref pattern is what `useEffectEvent` formalizes in recent React 19 releases: you declare the part of the effect that reads the newest props without being a dependency, and the effect itself re-runs only when `roomId` changes. The option to avoid is `// eslint-disable-next-line react-hooks/exhaustive-deps`, because it freezes a bug into the code and hides it from the next reader.

**Follow-ups they will ask:**
- Why not just add the function to the deps: if it is recreated every render the effect re-subscribes every render, which may be acceptable or may thrash a socket.
- Is this a React problem: no, it is plain JavaScript closure semantics; React just makes you create a new closure per render.
- How does `useCallback` help: it stabilizes the identity so the effect does not re-run, but it only moves the problem if the callback itself has stale deps.

**Mistakes to avoid:**
- Treating the dependency array as "when I want the effect to run"; it must list what the effect reads.
- Reading `ref.current` during render to avoid deps; refs are for effects and handlers.

### Q. When are useMemo and useCallback useless, and when are they harmful?
**Short answer (45 seconds):** They are useless when nothing downstream cares about referential identity: a `useCallback` passed to a plain, non-memoized child saves nothing because the child re-renders anyway, and a `useMemo` around a cheap expression costs more than it saves. They matter in two cases: the result is a dependency of another hook or a prop to a `React.memo` component, or the computation is measurably expensive. They are harmful when their dependency list is wrong, because then they return stale data and look like a React bug.

**Deeper explanation:** Memoization is a chain: one unstable input anywhere, an inline object prop, a context value, an anonymous callback, breaks every memoized consumer below it. So the audit is top-down. Start with the Profiler, find the expensive subtree, and then make the chain stable from the point where the state lives down to the component that is expensive. Memoizing leaf components while the parent passes `style={{ padding: 8 }}` is wasted effort.

```ts
const columns = useMemo(() => buildColumns(schema), [schema]);  // feeds a memoized DataGrid
const onRowClick = useCallback((id: string) => select(id), [select]); // select is stable (dispatch)
return <DataGrid columns={columns} onRowClick={onRowClick} rows={rows} />;
```

`useMemo` is also not a semantic guarantee: the React docs reserve the right to discard cached values, so it must never be used for correctness such as "create this object exactly once". For a one-time object use `useState(() => create())` or a ref. Finally, with the React Compiler enabled most of this becomes automatic, which is the strongest hint that manual memoization is plumbing, not architecture.

**Follow-ups they will ask:**
- How do you decide "expensive": measure with `performance.now()` or the Profiler; a rule of thumb is anything that shows up as a visible chunk of a 16 ms frame.
- Does `useCallback` prevent the function from being created: no, the inline function is created each render and then thrown away if the deps are unchanged.
- What about memoizing context values: that is one of the cases that matters, because every consumer re-renders when the value identity changes.

**Mistakes to avoid:**
- Wrapping every handler "for performance" with no memoized consumer; it adds code and misleads reviewers.
- Using `useMemo` with `[]` as a singleton; use state initializer or a ref.

### Q. What are the legitimate uses of useRef beyond grabbing a DOM node?
**Short answer (45 seconds):** `useRef` is a mutable container whose identity is stable across renders and whose mutation does not cause a render. That makes it the right place for anything React should not react to: timer and interval ids, a WebSocket or AbortController, the previous value of a prop, a "latest callback" so long-lived subscriptions see fresh handlers, and an `isMounted`-style guard for async work. It is also how imperative APIs cross component boundaries through `useImperativeHandle`.

**Deeper explanation:** The rule that keeps refs safe is: write and read them in effects and event handlers, not during render. Reading a ref during render makes output depend on something React does not track, which breaks under concurrent rendering because a discarded render may have mutated it.

```ts
function usePrevious<T>(value: T) {
  const ref = useRef<T | undefined>(undefined);
  useEffect(() => { ref.current = value; });   // updated after commit
  return ref.current;                           // during render: previous commit's value
}

function useDebouncedCallback<A extends unknown[]>(fn: (...a: A) => void, ms: number) {
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  return useCallback((...args: A) => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => fn(...args), ms);
  }, [fn, ms]);
}
```

Callback refs (`ref={(node) => ...}`) run when the node attaches and detaches, which is better than an effect for measuring a node that may mount conditionally. In React 19 `ref` is a regular prop on function components, so `forwardRef` is no longer required, and a ref callback can return a cleanup function.

**Follow-ups they will ask:**
- Why not store the timer in state: it would re-render on every change and the value would be stale inside the closure.
- How is a ref different from an instance variable in a class: it is the same idea; `useRef` is React's way to give a function component instance storage.
- Can refs be shared between a parent and a child: yes, by passing the ref as a prop or exposing a narrow API with `useImperativeHandle`.

**Mistakes to avoid:**
- Using a ref to hold state that drives the UI and then wondering why the screen does not update.
- Using `useRef` as a general "skip the lint rule" escape hatch for dependencies.

### Q. When would you pick useReducer over useState?
**Short answer (45 seconds):** When several pieces of state change together, when the next state depends on the previous one in non-trivial ways, or when the transitions are a finite set of events, a reducer makes those rules explicit and testable as a pure function. You also get a `dispatch` whose identity never changes, so passing it down avoids a layer of `useCallback`. For independent primitives such as an open flag or a text value, `useState` is clearer.

**Deeper explanation:** The classic case is an async request lifecycle. With separate `useState` calls for `data`, `error`, and `loading`, impossible combinations are representable, such as loading true with an error present, and every call site has to remember to reset the others. A reducer with a discriminated union makes impossible states unrepresentable and gives you a single place to look when a transition is wrong.

```ts
type State =
  | { status: "idle" }
  | { status: "loading"; controller: AbortController }
  | { status: "success"; data: Item[] }
  | { status: "error"; message: string };

type Action =
  | { type: "start"; controller: AbortController }
  | { type: "resolve"; data: Item[] }
  | { type: "reject"; message: string }
  | { type: "reset" };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "start": return { status: "loading", controller: action.controller };
    case "resolve": return state.status === "loading" ? { status: "success", data: action.data } : state;
    case "reject": return { status: "error", message: action.message };
    case "reset": return { status: "idle" };
  }
}
```

Reducers also scale a chat UI well: "append streaming token to the last assistant message" is one action with one implementation, instead of a `setMessages` with array surgery copied into three components. Because reducers must be pure, side effects such as the fetch itself live in the dispatching code or an effect, never inside the reducer.

**Follow-ups they will ask:**
- Is useReducer "Redux in a component": same reducer idea, but local, with no middleware, no devtools, and no cross-tree subscription.
- How do you test it: call `reducer(state, action)` in a unit test with no React involved.
- How do you combine it with Context: provide `state` and `dispatch` in two separate contexts so dispatch-only consumers do not re-render on state changes.

**Mistakes to avoid:**
- Putting the fetch inside the reducer; reducers must be pure and may be called twice in StrictMode.
- Reaching for a reducer for a single boolean; the ceremony costs readability.

### Q. How do you design a custom hook that other teams can adopt safely?
**Short answer (45 seconds):** Treat it as a public API. Give it one job and a `use` prefix, accept an options object so new parameters are additive, return values with stable identities so consumers can put them in dependency arrays, own your cleanup so a consumer cannot leak a subscription, and make it SSR-safe. Then write the three tests that matter: it cleans up on unmount, it re-subscribes when inputs change, and it behaves under StrictMode's double mount.

**Deeper explanation:** Most custom hooks are either "subscribe to something" or "derive and cache something". For subscriptions, reach for `useSyncExternalStore` rather than `useState` plus `useEffect`, because it handles server rendering and concurrent tearing for you. For derived data, return memoized values and stable callbacks, because a hook that returns a fresh object every render forces every consumer to either accept re-renders or re-memoize your output.

```ts
type Options = { interval?: number; enabled?: boolean };

export function useOnlineStatus({ enabled = true }: Options = {}) {
  return useSyncExternalStore(
    (notify) => {
      if (!enabled) return () => {};
      window.addEventListener("online", notify);
      window.addEventListener("offline", notify);
      return () => {
        window.removeEventListener("online", notify);
        window.removeEventListener("offline", notify);
      };
    },
    () => navigator.onLine,
    () => true // server snapshot: assume online during SSR
  );
}
```

Other API hygiene: return a tuple only when the order is obvious (`[value, setValue]`), otherwise an object; use `useId` inside form hooks so generated `aria-describedby` and `htmlFor` ids survive hydration; expose a way to disable the hook (`enabled`) because hooks cannot be called conditionally; and document which returned functions are stable so consumers do not wrap them again.

**Follow-ups they will ask:**
- Where does the hook's state live: in the component that calls it; two components calling the same hook do not share state unless the hook reads a shared store.
- How do you test a hook: with `renderHook` from Testing Library, asserting on behaviour and cleanup rather than internals.
- When should a hook become a component or a provider instead: when multiple components must share one instance of the state.

**Mistakes to avoid:**
- Returning new object or array literals every render from a hook that is meant to be a dependency somewhere.
- Hiding a `fetch` in a hook with no cancellation; every consumer inherits the race condition.

### Q. useTransition vs useDeferredValue: when do you reach for each?
**Short answer (45 seconds):** Both move work into a low-priority render that React can interrupt. `useTransition` is for when you own the state update: you wrap the setter call in `startTransition` and get an `isPending` flag. `useDeferredValue` is for when you only own a value, typically a prop or state you cannot wrap, and want a lagging copy of it for an expensive subtree. Same scheduler underneath, different ownership.

**Deeper explanation:** A search page is the canonical example. If the component holds `query` in state, you call `setQuery` urgently to keep the input responsive and `startTransition(() => setResultsQuery(q))` for the expensive list. If the expensive list is a child that receives `query` as a prop from somewhere you do not control, the child does `const deferred = useDeferredValue(query)` and renders with `deferred`, so React first commits the cheap update with the old list, then renders the new list in the background.

```ts
function Results({ query }: { query: string }) {
  const deferred = useDeferredValue(query);
  const stale = deferred !== query;
  return (
    <div style={{ opacity: stale ? 0.6 : 1 }}>
      <HeavyList query={deferred} />   // HeavyList is memoized so the stale render is cheap
    </div>
  );
}
```

Two details interviewers like: the deferred render is only skipped cheaply if the child is memoized, otherwise React still re-renders it with the old value; and transitions integrate with Suspense, so a navigation inside `startTransition` keeps the current screen visible instead of showing the fallback. React 19 added an optional second argument to `useDeferredValue` for the value to use during the initial render.

**Follow-ups they will ask:**
- Is this a replacement for debouncing: partly; debouncing delays work by a fixed time, deferral starts immediately and yields to urgent work, so for CPU-bound filtering deferral is better, for network calls debouncing still matters.
- Can `startTransition` wrap an async function: React 19 supports async actions in transitions, with `isPending` staying true until the promise settles.
- Why not put the input itself in a transition: the typed characters would lag, which users perceive as a broken input.

**Mistakes to avoid:**
- Using transitions for a controlled input's own value.
- Expecting a transition to make slow code fast; it only changes scheduling.

### Q. What problem does useSyncExternalStore solve, and when would you actually use it?
**Short answer (45 seconds):** It lets components subscribe to a store that lives outside React, such as a Redux or Zustand store, `window.matchMedia`, or `navigator.onLine`, in a way that stays consistent under concurrent rendering. The problem it solves is tearing: during an interruptible render, the store may change between two components reading it, so one frame shows two different values. The hook forces a synchronous re-render when a snapshot changes mid-render and also provides a server snapshot for SSR and hydration.

**Deeper explanation:** The signature is `useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot?)`. `subscribe` receives a callback and returns an unsubscribe function; React calls it once per store, not per render, as long as the function identity is stable, so define it outside the component or memoize it. `getSnapshot` must be cheap and must return the same reference while the store has not changed, otherwise React assumes the store changed on every render and loops; selecting a slice of a store therefore requires memoizing the selected value or returning primitives.

```ts
const store = createStore(); // { subscribe(cb), getState() }

function useCartCount() {
  return useSyncExternalStore(
    store.subscribe,
    () => store.getState().items.length,  // primitive: safe to return each time
    () => 0                               // server snapshot
  );
}
```

This is why library authors moved to it: react-redux and Zustand use it internally, so you rarely call it directly in application code. You do call it for browser APIs that are not React state (media queries, online status, `localStorage` with the `storage` event, scroll position when a global value is genuinely needed) and when wrapping a legacy event-emitter module during a migration.

**Follow-ups they will ask:**
- Why not `useState` plus `useEffect` subscription: it works for non-concurrent code but can tear during transitions and has no hydration-safe server value.
- What happens if `getSnapshot` returns a new object each time: an infinite update loop with a console error about the snapshot being unstable.
- Does it support selectors: not directly; select primitives or memoize the selected object yourself.

**Mistakes to avoid:**
- Returning `store.getState()` where the state is a new object on each call; you must return a stable reference.
- Omitting the server snapshot in an SSR app, which throws during hydration.

### Practice
- Implement `useInterval(callback, delay)` three ways (naive with stale closure, functional update, latest-ref) and write a test that proves the first one is wrong.
- Take a component with five `useCallback` wrappers, profile it, remove every wrapper whose consumer is not memoized, and confirm the render count is identical.
- Write `useMediaQuery` with `useSyncExternalStore`, render it in a Next.js page, and check there is no hydration warning and no flash of the wrong layout.
- Convert an async request managed by three `useState` calls into a `useReducer` with a discriminated union; list the impossible states you eliminated.
- Say it out loud: explain why an interval set up in `useEffect(..., [])` logs the same count forever, then describe the fix you would ship and why.

## State Management at Scale

> Senior frontend interviews almost always include "how would you manage state in a large app". The weak answer names a library. The strong answer first classifies the state (server cache, URL, form, UI, shared client) because each class has a different owner and a different tool, then explains the failure modes of Context, why server state is a caching problem, and how optimistic updates stay correct. Be ready to defend a choice against alternatives rather than list them.

### Concepts you must understand
- Most "global state" is server state: a cache of data the server owns. Treating it as client state (copying it into Redux and syncing by hand) is the root of most stale-data bugs.
- Client state splits into URL state (filters, pagination, selected tab), form state, ephemeral UI state (open menus), and genuinely shared client state (auth session, theme, cart draft). Each has a natural home.
- React Context is a dependency-injection mechanism, not a store: every consumer re-renders when the provider value identity changes, and there is no built-in selector.
- Redux Toolkit, Zustand, and Jotai differ in topology (one store with reducers, one store with hooks and selectors, many atoms composed bottom-up) more than in capability; choose on team size, debugging needs, and how much derived state you have.
- TanStack Query models a server cache: `staleTime` controls when data is considered old, `gcTime` controls when unused data is dropped, and invalidation marks keys stale and refetches the active ones.
- Optimistic updates write the expected result into the cache before the server confirms, keep a snapshot to roll back on error, and invalidate on settle so the server's truth wins.
- Normalize when the same entity appears in several places and can be edited; keep it denormalized when data is read-only and shaped per screen.
- Derived state is computed during render, never stored; storing it creates two sources of truth that drift.
- Form state belongs in a form library that uses uncontrolled inputs by default (react-hook-form) so typing does not re-render the whole form, with schema validation at the boundary.

### Q. How do you decide where a piece of state should live in a large React application?
**Short answer (45 seconds):** I classify it first. If the server owns it, it goes into a server-cache layer such as TanStack Query or RTK Query, never into hand-rolled Redux slices. If it should survive a refresh or be shareable, it goes in the URL. If it is a form in progress, it lives in the form library. If it is local UI, it stays in the component or the nearest common ancestor. Only what is left, cross-cutting client state such as the session, the theme, or a multi-step draft, deserves a shared store, and that is usually a small one.

**Deeper explanation:** This classification removes most of the "Redux vs Zustand" debate, because the store ends up holding a fraction of what teams used to put there. The benefits are concrete: server data gets caching, deduplication, background refetch, and retry for free; URL state gets back-button and deep-link behaviour; form state gets validation and dirty tracking without renders on each keystroke.

```text
Who owns the truth?            Where it lives            Tool
server                         query cache               TanStack Query / RTK Query
the address bar                URL search params         router, nuqs
a form being filled in         form store                react-hook-form
one component or subtree       useState / useReducer     React
the whole client session       small shared store        Zustand / Redux Toolkit / Context
```

The second rule is colocation: start local and lift only when a second consumer appears. State lifted too early is the main reason top-level providers end up re-rendering the whole app. The third rule is that "shared" means shared by components far apart in the tree; siblings share through their parent.

**Follow-ups they will ask:**
- What about a selected row id used by a table and a detail panel: the nearest common parent, or the URL if the selection should survive a refresh.
- Where do WebSocket updates go: into the query cache via `setQueryData`, so every consumer of that key updates.
- When would you put server data in Redux anyway: when you need complex client-side derivation across many entities with devtools time travel, and RTK Query does not fit.

**Mistakes to avoid:**
- Answering with a library name before asking what kind of state it is.
- Mirroring server data into a client store "so it is global"; it is already global in the query cache.

### Q. What are the pitfalls of using React Context for state, and how do you work around them?
**Short answer (45 seconds):** Context has no selector: when the provider's value changes identity, every component that calls `useContext` for it re-renders, even if it only cares about one field. A provider value built as an inline object re-renders all consumers on every render of the provider. The workarounds are to memoize the value, split one context into several by update frequency, separate state from the dispatch function, and move high-frequency state into an external store that supports selectors.

**Deeper explanation:** Context is excellent for things that rarely change and are needed everywhere: the current user, theme, locale, a feature-flag client, a query client. It is a poor fit for a mouse position, a form's live values, or a chat message list, because each change fans out to all consumers.

```ts
const StateCtx = createContext<State | null>(null);
const DispatchCtx = createContext<React.Dispatch<Action> | null>(null);

function Provider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initial);
  return (
    <StateCtx.Provider value={state}>
      <DispatchCtx.Provider value={dispatch}>{children}</DispatchCtx.Provider>
    </StateCtx.Provider>
  );
}
```

Buttons that only dispatch now never re-render on state changes. For large states, go further: one context per independent slice, so a theme toggle does not re-render the cart. When even that is not enough, a Zustand store with selectors or `useSyncExternalStore` gives per-field subscriptions. Two React 19 conveniences: `<Ctx value={...}>` works without `.Provider`, and `use(Ctx)` can be called inside conditions and loops, which simplifies optional providers.

**Follow-ups they will ask:**
- Does wrapping consumers in `React.memo` help: no, context updates bypass memo; the consumer re-renders regardless of props.
- How do you default a context safely: default to `null` and throw a clear error in a `useX` hook if the provider is missing, instead of shipping fake defaults.
- Is Context slow: propagation is cheap; the cost is the consumers' renders.

**Mistakes to avoid:**
- Calling Context "a built-in Redux". It is a transport for values, with no store, no selectors, and no middleware.
- Putting everything in one `AppContext` with a value object rebuilt each render.

### Q. Redux Toolkit, Zustand, or Jotai: how do you choose, and what would you say to a team that wants to standardize on one?
**Short answer (45 seconds):** Same problem, different topologies. Redux Toolkit is one store with slices and reducers, strict unidirectional flow, excellent devtools, middleware, and RTK Query built in; it fits large teams that value explicitness. Zustand is a minimal store exposed as a hook with selectors, no provider, usable outside React; it fits apps with a little shared client state, which is most of them. Jotai is bottom-up atoms with derived atoms, which fits editors and dashboards full of interdependent derived state. For a team standard I pick based on how much client state remains once server state lives in a query cache; often Zustand is enough.

**Deeper explanation:** The differences that matter in practice: Redux forces all updates through serializable actions, which gives you time-travel debugging, action logs for bug reports, and an easy place for cross-cutting logic (listener middleware), at the cost of ceremony. Zustand lets components subscribe to a slice with a selector, so re-renders are precise, and the store can be read and written from non-React code such as a WebSocket handler. Jotai inverts the model: each atom is independent, derived atoms recompute only when their inputs change, and Suspense integration is native, so async derivations read naturally.

```ts
// Zustand: selector-based subscription, no provider
const useSession = create<SessionState>()((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));
const name = useSession((s) => s.user?.name); // re-renders only when name changes
```

Whatever the pick, the same discipline applies: keep server data out of it, keep derived values computed not stored, and keep actions near the state they change.

**Follow-ups they will ask:**
- Where does Recoil fit: it introduced the atom model but is no longer actively maintained; Jotai is the usual replacement.
- Can Zustand scale to a large app: yes with slices and selectors, but you lose the enforced action log unless you add the devtools middleware and name your updates.
- What about MobX or signals: observable models with automatic fine-grained updates; good fit for complex object graphs, less idiomatic in the React ecosystem.

**Mistakes to avoid:**
- Dismissing Redux as "legacy". Redux Toolkit removed most of the boilerplate and RTK Query is a strong server-cache layer.
- Comparing libraries without first saying which state class they would hold.

### Q. How does TanStack Query cache data, and how do you invalidate it correctly after a mutation?
**Short answer (45 seconds):** Every query is identified by a serializable key such as `["todos", { status }]`. The cache stores the data per key with two timers: `staleTime` (default zero) says how long data counts as fresh, and `gcTime` (default five minutes) says how long unused data stays in memory after the last observer unmounts. Fresh data is served without a request; stale data is served immediately and refetched in the background on mount, window focus, or reconnect. After a mutation you call `invalidateQueries` with a key prefix, which marks matching queries stale and refetches the ones currently rendered.

**Deeper explanation:** The key design is hierarchical: `["todos"]` matches everything under it, so one invalidation after creating a todo refreshes the list, the filtered lists, and the counts. Keys with objects are hashed deterministically, so key order inside the object does not matter. Multiple components mounting the same key share one request (deduplication) and one cache entry.

```ts
const todos = useQuery({
  queryKey: ["todos", { status }],
  queryFn: ({ signal }) => api.todos.list({ status, signal }),
  staleTime: 30_000,
});

const create = useMutation({
  mutationFn: api.todos.create,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["todos"] }),
});
```

Passing the `signal` into the fetch lets the library cancel requests when the query unmounts or the key changes. `staleTime` is the main tuning knob: zero gives maximum freshness and more traffic; a long value suits reference data such as countries. `select` derives a slice without extra requests, and `placeholderData: keepPreviousData` keeps the old page visible while the next page loads.

**Follow-ups they will ask:**
- Difference between `invalidateQueries` and `refetchQueries`: invalidate marks stale and refetches only active queries; refetch forces matching queries regardless.
- How do you set data from a WebSocket message: `queryClient.setQueryData(key, updater)`, which updates every consumer without a request.
- What does `isPending` vs `isFetching` mean: pending means no data yet; fetching means a request is in flight, including background refetches.

**Mistakes to avoid:**
- Copying query results into local state with an effect; the cache is already the state.
- Using unstable keys such as a new object with a `Date` inside, which defeats caching.

### Q. Implement an optimistic update with TanStack Query and tell me what can go wrong.
**Short answer (45 seconds):** In `onMutate` I cancel in-flight refetches for the key, snapshot the current cache, and write the expected result with `setQueryData`. In `onError` I restore the snapshot. In `onSettled` I invalidate so the server's version replaces my guess. The things that go wrong are races: a background refetch landing after my optimistic write, two overlapping mutations rolling back each other's changes, and optimistic ids colliding with real ones.

**Deeper explanation:**

```ts
const toggle = useMutation({
  mutationFn: api.todos.toggle,
  onMutate: async (id: string) => {
    await queryClient.cancelQueries({ queryKey: ["todos"] });
    const previous = queryClient.getQueryData<Todo[]>(["todos"]);
    queryClient.setQueryData<Todo[]>(["todos"], (old) =>
      old?.map((t) => (t.id === id ? { ...t, done: !t.done } : t)));
    return { previous };
  },
  onError: (_err, _id, ctx) => {
    if (ctx?.previous) queryClient.setQueryData(["todos"], ctx.previous);
  },
  onSettled: () => queryClient.invalidateQueries({ queryKey: ["todos"] }),
});
```

`cancelQueries` matters: without it, a refetch that started before the mutation can resolve after `setQueryData` and overwrite the optimistic row with stale server data. For overlapping mutations, the snapshot rollback is too coarse (rolling back mutation A also removes B's change), so either disable the control while a mutation is pending, or roll back by reapplying the inverse change rather than restoring the snapshot. For creates, generate a temporary client id, render the row in a pending style, and replace it with the server id in `onSuccess`. A simpler option when the UI is local to the mutation: read `mutation.variables` while `isPending` and render the pending row from that, with no cache writes at all.

**Follow-ups they will ask:**
- When is optimism wrong: for operations where a failure is likely or costly to explain, such as payments, show pending state instead.
- How do you show the user a rollback: a toast with the error and the reverted item; silent reverts feel like data loss.
- How does this interact with invalidation on focus: `onSettled` invalidation and focus refetch converge on the server truth, which is the point.

**Mistakes to avoid:**
- Skipping `cancelQueries` and then "fixing" the flicker by removing invalidation, which leaves the cache wrong forever.
- Treating the optimistic write as the source of truth; the server response must always win.

### Q. What is normalized state, when is it worth it, and how does derived state fit in?
**Short answer (45 seconds):** Normalized state stores each entity once in a map keyed by id, with lists expressed as arrays of ids, like database tables. It pays off when the same entity appears in several views and can be edited, because one update changes every view and there is no risk of two copies disagreeing. It is not worth it for read-only, screen-shaped responses where a per-query cache already handles consistency. Derived state is the complementary rule: anything computable from existing state is computed during render, not stored.

**Deeper explanation:** Redux Toolkit's `createEntityAdapter` generates the `{ ids, entities }` shape with CRUD reducers and selectors. In GraphQL land, Apollo Client normalizes automatically by `__typename` and `id`. TanStack Query deliberately does not normalize: it caches per query key, and you get consistency by invalidating or by writing the mutated entity into each affected key. Both approaches work; what matters is naming the trade-off: normalization gives automatic consistency and update cost proportional to one entity, at the price of joining data back together for rendering and of handling "which lists does this new entity belong to".

```ts
type Normalized = {
  users: Record<string, User>;
  postIds: string[];
  posts: Record<string, Post & { authorId: string }>;
};
// Rendering joins: posts[id] and users[posts[id].authorId]
```

Derived state failures are quieter. Storing `fullName` next to `firstName` and `lastName`, or `selectedItem` next to `items` and `selectedId`, creates a second source of truth kept in sync with effects, and effects run a render late, so the UI shows a stale pair for a frame. Compute it: `const selected = items.find((i) => i.id === selectedId)`, with `useMemo` only if heavy.

**Follow-ups they will ask:**
- How do you keep a normalized store in sync after a server mutation: apply the returned entity to the map; the lists update automatically because they hold ids.
- What is the cost of normalization in a React app: more selectors and memoization to avoid re-joining on every render.
- Where does `select` in TanStack Query fit: it is derived state at the cache boundary, memoized per query.

**Mistakes to avoid:**
- Normalizing everything by default, including data shown once and never edited.
- Using an effect to copy one state into another "so they match".

### Q. Why would you put application state in the URL, and what are the rules for doing it well?
**Short answer (45 seconds):** Any state a user would expect to survive a refresh, share with a colleague, or step back through with the browser's back button belongs in the URL: filters, sort order, pagination, the open tab, the selected record. It also makes server rendering trivial, because the first request already carries the state. The rules are to keep it serializable and small, omit defaults, validate it on read because users edit URLs, and decide deliberately between pushing a new history entry and replacing the current one.

**Deeper explanation:** Routers expose this through `useSearchParams` (React Router and Next.js) and `useParams` for path segments. The pattern that scales is a small typed layer: a schema that parses the raw params into a typed object with defaults, and a setter that serializes back, so components never touch strings.

```ts
const filtersSchema = z.object({
  q: z.string().default(""),
  page: z.coerce.number().int().min(1).default(1),
  status: z.enum(["open", "closed", "all"]).default("open"),
});

function useFilters() {
  const [params, setParams] = useSearchParams();
  const filters = filtersSchema.parse(Object.fromEntries(params));
  const update = (patch: Partial<typeof filters>) =>
    setParams(serialize({ ...filters, ...patch }), { replace: true });
  return [filters, update] as const;
}
```

Typing into a search box should `replace` so the back button does not step through every keystroke; changing a page or a tab should `push` so back behaves as users expect. Reset `page` to 1 when a filter changes. Avoid encoding large or sensitive data: URLs end up in logs, referrers, and screenshots. In Next.js the `nuqs` library wraps this pattern with typed parsers and server-compatible defaults.

**Follow-ups they will ask:**
- Does URL state cause extra renders: changing search params re-renders the route; keep the parsing memoized and the consumers narrow.
- How do you keep URL state and a query cache aligned: use the parsed filters object directly in the query key.
- What about modal state: open/close for a lightweight modal is UI state; a modal that shows an entity should be a URL.

**Mistakes to avoid:**
- Keeping filters in a store and "syncing" them to the URL with an effect; the URL should be the only source.
- Trusting URL values without validation and crashing on a hand-edited `page=abc`.

### Q. How do you manage form state at scale, and why does react-hook-form use uncontrolled inputs?
**Short answer (45 seconds):** Controlled forms re-render the whole form component on every keystroke, which is fine for three fields and painful for forty with cross-field validation. react-hook-form registers native inputs through refs, so typing never triggers a React render; it reads values at submit or validation time and re-renders only the pieces that subscribe to a specific field or to `formState`. Validation runs against a schema (zod via `@hookform/resolvers`) so the same schema types the form, validates it, and can be reused on the server.

**Deeper explanation:**

```ts
const schema = z.object({
  email: z.string().email(),
  seats: z.coerce.number().int().min(1).max(500),
});
type FormValues = z.infer<typeof schema>;

const { register, handleSubmit, control, formState: { errors, isSubmitting } } =
  useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { email: "", seats: 1 } });

<input {...register("email")} aria-invalid={!!errors.email} />
<Controller name="seats" control={control}
  render={({ field }) => <NumberStepper value={field.value} onChange={field.onChange} />} />
```

`register` works for native elements; `Controller` adapts controlled design-system components. `watch` subscribes the whole component to changes, so prefer `useWatch` with a `name` inside the small component that needs the live value. `useFieldArray` manages dynamic rows and gives each a stable `id` to use as the key, which avoids the index-key problem. Submit handlers receive parsed, typed values, and server errors map back with `setError`. Resetting after a successful save uses `reset(values)` so `isDirty` reflects the new baseline.

**Follow-ups they will ask:**
- How do you handle multi-step forms: one `useForm` at the wizard level with `trigger(fields)` per step, or one form per step writing into a store.
- Where does async validation go: in the schema with `refine`, or in `validate` on the field, debounced, and only after the synchronous checks pass.
- How do server actions in Next.js fit: react-hook-form can hand the parsed values to an action, and `useActionState` covers simple forms without a library.

**Mistakes to avoid:**
- Storing every keystroke in a global store; forms are local until submit.
- Validating only on the client; the schema must run on the server too.

### Practice
- Take an existing screen that copies fetched data into Redux; replace it with TanStack Query, delete the slice, and count the lines removed and the bugs that no longer exist (stale list after create, duplicate fetch on remount).
- Build a filter bar whose state lives only in the URL with a zod parser; verify refresh, back button, and a shared link all restore the same view.
- Implement an optimistic toggle, then simulate a slow network in DevTools and click twice fast; observe the rollback bug and fix it with per-item pending state.
- Profile a 30-field controlled form, convert it to react-hook-form with `register`, and compare render counts while typing.
- Say it out loud: a teammate proposes "let us put everything in Zustand". Argue for classifying state first, and name what would stay in Zustand afterwards.

## Performance Engineering

> Performance questions test whether you measure before you optimize. The weak answer is a list of tricks (memo everything, lazy load everything). The strong answer starts with a diagnosis method, distinguishes load performance (bundle, LCP) from runtime performance (renders, INP), names the tool for each, and knows the cost of each fix. Have one real story where you found a bottleneck, what the profiler showed, and the before and after numbers you measured yourself.

### Concepts you must understand
- Load performance and runtime performance are different problems: the first is about bytes, requests, and render blocking; the second is about main-thread work per interaction. Different tools, different fixes.
- React DevTools Profiler shows which components rendered in each commit, how long they took, and why; the Chrome Performance panel shows long tasks, layout, and paint. Lighthouse and field data (CrUX, web-vitals library) show what users experience.
- Core Web Vitals: LCP (largest content paint, good under 2.5 s), INP (interaction to next paint, good under 200 ms), CLS (cumulative layout shift, good under 0.1), all measured at the 75th percentile of real users.
- A memo boundary only works when every prop crossing it is referentially stable; place few boundaries at the top of expensive subtrees rather than many at the leaves.
- Virtualization renders only the rows in and near the viewport; it trades find-in-page, accessibility, and simplicity for constant DOM size.
- Code splitting with dynamic `import()` and `React.lazy` moves code off the critical path; Suspense renders a fallback while the chunk loads, and chunk-load failures after deploys must be handled.
- Tree shaking requires ES modules and side-effect-free packages; barrel files and CommonJS dependencies are the usual reasons dead code ships.
- Images and fonts dominate LCP and CLS: size attributes, modern formats, priority hints, self-hosted fonts with a swap strategy.
- Layout thrashing is interleaving DOM reads and writes so the browser recalculates layout repeatedly; batch reads, then writes, and animate with transform and opacity.
- Web workers move CPU-bound work off the main thread; they cannot touch the DOM and pay a serialization cost per message.

### Q. A page feels slow. Walk me through how you find the cause before you change any code.
**Short answer (45 seconds):** First I decide whether it is slow to load or slow to interact with, because the tools differ. For load I run Lighthouse and look at the network waterfall: bundle size, render-blocking requests, the LCP element and what it waits on. For interaction I record in the Chrome Performance panel while reproducing the slowness and look for long tasks over 50 ms, then open the React Profiler for the same interaction to see which components rendered, how long, and why. Only after I have a number and a culprit do I change code, and I re-measure after.

**Deeper explanation:** The React Profiler flamegraph shows each commit; the ranked view sorts components by self time; enabling "Record why each component rendered" tells you whether it was props, state, context, or the parent. A common finding is a wide, shallow bar: hundreds of cheap components rendering because a provider value changed. Another is a single deep bar: one component doing heavy work in render, which the Performance panel confirms as scripting time inside a long task.

```text
Symptom                         Tool                         Typical culprit
slow first paint                Lighthouse, Network         huge bundle, blocking font, no SSR
slow after load, janky typing   Performance panel + Profiler  wide re-render, unmemoized provider
one click freezes UI            Performance panel            sync heavy computation, layout thrash
fine locally, slow for users    web-vitals field data        low-end devices, slow networks
```

Lab numbers lie about users: a developer laptop is several times faster than a mid-range Android phone, so the Performance panel's CPU throttling (4x or 6x) is the honest setting. Field data from the `web-vitals` library sent to analytics tells you which pages and which interactions actually hurt, and the attribution build tells you which element and which script was responsible.

**Follow-ups they will ask:**
- How do you profile in production: React's production profiling build or the `<Profiler onRender>` API, plus field vitals; DevTools profiling needs the profiling bundle.
- What is a long task: any main-thread task over 50 ms; it is what blocks input and raises INP.
- How do you make a performance regression visible in CI: Lighthouse CI with budgets on bundle size and LCP, and a size-limit check on the main chunk.

**Mistakes to avoid:**
- Jumping to `React.memo` before profiling; most slow pages are slow for one specific reason.
- Quoting Lighthouse scores from a fast laptop as proof.

### Q. Where do you place memo boundaries in a large component tree?
**Short answer (45 seconds):** At the top of expensive subtrees that receive few, stable props, not at every leaf. A boundary only helps if everything crossing it is referentially stable, so I start where the state lives, make the props crossing the boundary stable (memoized objects, stable callbacks, ids instead of entities), and verify in the Profiler that the subtree now bails out. Composition often removes the need: passing expensive content as `children` or lifting state down means the expensive subtree is not under the component that re-renders.

**Deeper explanation:** Consider a dashboard where a filter input and a heavy chart share a parent. Typing updates the parent's state, so the chart re-renders on every keystroke. Options in order of preference: move the input state into the input component and hand the committed value up on blur or debounce; keep the chart as a `children` element created by a non-re-rendering ancestor; wrap the chart in `memo` and ensure its `data`, `options`, and callbacks are stable.

```ts
const Chart = memo(function Chart({ series, onSelect }: ChartProps) { /* expensive */ });

function Dashboard({ series }: { series: Series[] }) {
  const [q, setQ] = useState("");
  const onSelect = useCallback((id: string) => router.push(`/points/${id}`), []);
  return (
    <>
      <input value={q} onChange={(e) => setQ(e.target.value)} />
      <Chart series={series} onSelect={onSelect} />   // bails out while typing
    </>
  );
}
```

Pass primitives where possible: `selectedId` instead of `selectedItem` means the boundary survives a new object identity from the store. For lists, memoize the row component and pass it the row's id plus a stable handler rather than inline closures per row. With the React Compiler enabled these boundaries are inserted for you, but the composition advice still applies because the compiler cannot change where state lives.

**Follow-ups they will ask:**
- Why not memo everything: each boundary costs a shallow compare per render and makes inline props a silent regression.
- How do you detect a broken boundary: the Profiler shows the memoized component rendering with "props changed" and names the prop.
- Does `memo` compare deeply: no, shallow `Object.is` per prop; a custom comparator is possible but rarely worth it.

**Mistakes to avoid:**
- Wrapping a component in `memo` while passing it `style={{}}` or an arrow function.
- Memoizing leaves while a provider at the root re-renders everything anyway.

### Q. How does list virtualization work, and when is it the wrong answer?
**Short answer (45 seconds):** A virtualized list renders only the items that intersect the viewport plus a small overscan, positions them absolutely or with a spacer inside a scroll container whose height equals the full list, and swaps items in and out as the user scrolls. DOM size becomes constant regardless of data size. It is the wrong answer when the list is short, when users need find-in-page or print, when rows have unpredictable heights you cannot measure cheaply, or when pagination would serve the user better anyway.

**Deeper explanation:** With fixed row heights the math is trivial: `startIndex = floor(scrollTop / rowHeight)`, render `ceil(viewportHeight / rowHeight) + overscan` rows, translate the container by `startIndex * rowHeight`. Variable heights need measurement: libraries such as `@tanstack/react-virtual` and `react-virtuoso` measure rendered rows with `ResizeObserver` and keep an estimate for unmeasured ones, which causes small scroll corrections when estimates are wrong.

```ts
const virtualizer = useVirtualizer({
  count: rows.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 48,
  overscan: 8,
});
// render virtualizer.getVirtualItems() with style={{ transform: `translateY(${item.start}px)` }}
```

Costs to name: screen readers lose the full list and need `aria-rowcount` and `aria-rowindex`; Ctrl+F only finds rendered rows; scroll restoration on navigation needs saved offsets; images inside rows re-load on remount unless cached; and a chat-style list anchored to the bottom needs reverse-order handling. The CSS property `content-visibility: auto` is a cheaper middle ground for long static pages: the browser skips rendering work for off-screen sections while keeping them in the DOM.

**Follow-ups they will ask:**
- How many rows before virtualizing: measure; a few hundred simple rows is often fine, a few thousand with complex cells is not.
- How do you virtualize a grid: two-dimensional windows, row and column virtualizers, which the same libraries support.
- What about infinite scroll: virtualization controls the DOM, infinite scroll controls fetching; combine them by fetching the next page when the last virtual item nears the end.

**Mistakes to avoid:**
- Virtualizing a 40-row list because "it might grow".
- Forgetting the accessibility attributes and shipping a list a screen reader sees as ten items.

### Q. How do you code-split a React application, and what are the pitfalls of React.lazy and Suspense?
**Short answer (45 seconds):** The bundler splits at every dynamic `import()`, so I split by route first, then by heavy feature inside a route: a chart library, a rich text editor, a PDF viewer, an admin panel most users never open. `React.lazy` wraps the dynamic import as a component, and a `Suspense` boundary above it shows a fallback while the chunk loads. The pitfalls are fallback flashes on fast networks, waterfalls when a lazy chunk itself fetches data, stale chunk hashes after a deploy causing load failures, and over-splitting into dozens of tiny requests.

**Deeper explanation:**

```ts
const Editor = lazy(() => import("./Editor"));          // default export required

function Page() {
  return (
    <Suspense fallback={<EditorSkeleton />}>
      <Editor />
    </Suspense>
  );
}
// preload on intent so the click feels instant
<button onMouseEnter={() => import("./Editor")} onClick={open}>Edit</button>
```

Place Suspense boundaries where a fallback makes visual sense, usually around a region rather than each component, so one skeleton replaces one region. Combine lazy loading with transitions: navigating inside `startTransition` keeps the current screen while the chunk and its data load instead of flashing the fallback. To avoid data waterfalls, start the data fetch when the route is matched, not inside the lazily loaded component; router loaders and prefetching exist for this.

Deploy failures are the production pitfall: a user with an old HTML shell clicks a route after a deploy, the browser requests `Editor.abc123.js`, and the CDN returns 404 because only the new hash exists. Handle it with an error boundary around the lazy region that retries once and then reloads the page, and keep old assets served for a while after a deploy.

**Follow-ups they will ask:**
- Why does `lazy` need a default export: the API resolves `module.default`; for named exports map it in the import callback.
- Does splitting always help: no, it adds a round trip per chunk; split what is large and rarely needed.
- How does this work with SSR: frameworks handle server-side chunk discovery; in plain React SSR lazy components need Suspense and streaming.

**Mistakes to avoid:**
- Splitting every component and shipping fifty tiny chunks that load in a chain.
- No error boundary around lazy regions, so a chunk 404 takes down the whole app.

### Q. How do you shrink a JavaScript bundle, and what breaks tree shaking?
**Short answer (45 seconds):** Measure first with a bundle analyzer so you know what is actually big; it is usually a few dependencies, not application code. Then: replace heavy libraries with lighter ones or native APIs, import deeply or from ES-module builds so unused exports can be dropped, split rarely used code into async chunks, and check that polyfills and locale data are not shipped wholesale. Tree shaking breaks when a package is CommonJS, when it is not marked side-effect free, or when a barrel file re-exports everything so the bundler cannot prove what is unused.

**Deeper explanation:** Tree shaking is dead-export elimination over ES module static imports. It needs `import`/`export` syntax (not `require`), a `"sideEffects": false` flag or list in the dependency's `package.json` so the bundler knows that dropping an unused module cannot change behaviour, and code that does not perform side effects at module scope. Barrel files (`index.ts` re-exporting a hundred components) are the common self-inflicted wound: importing one icon from a barrel can pull the module graph of all of them, and in development it also slows cold starts.

```bash
npx vite-bundle-visualizer                       # Vite: visualize what is in the bundle
ANALYZE=true next build                          # Next.js with @next/bundle-analyzer configured
npx source-map-explorer dist/assets/index-*.js   # any build: which source files make up a chunk
```

Typical wins: `date-fns` over moment, `lodash-es` per-function imports or native array methods, loading a charting library only on pages that chart, per-component imports instead of a UI kit's full CSS, and checking that `core-js` is not duplicated across packages. Set a size budget in CI (`size-limit`) so regressions fail the build rather than surface in a quarterly audit.

**Follow-ups they will ask:**
- How do you find duplicate dependencies: the analyzer shows two versions of the same package; fix with resolutions or by upgrading the dependant.
- Does minification do tree shaking: no, minifiers remove unreachable code within a module; tree shaking removes unused modules and exports across the graph.
- What about the CSS bundle: same idea; purge unused utility classes and avoid global imports of whole component libraries.

**Mistakes to avoid:**
- Importing a single function with `import _ from "lodash"` and assuming the bundler trims it.
- Optimizing application code while a 400 KB dependency sits untouched.

### Q. Explain LCP, INP, and CLS, and what moves each one in a React application.
**Short answer (45 seconds):** LCP measures when the largest visible element, usually a hero image or heading, finishes rendering; it is driven by server response time, render-blocking resources, and whether that element's resource is discovered early. INP measures the worst interaction latency across a visit, from input to the next frame painted; in React it is driven by long tasks in event handlers, large synchronous re-renders, and hydration work. CLS measures unexpected layout movement; it comes from images without dimensions, late-loading fonts, and content injected above the fold.

**Deeper explanation:** For LCP in a client-rendered SPA the chain is HTML, then the bundle, then an API call, then the image: three round trips before the hero appears. Server rendering puts the hero in the HTML; `fetchpriority="high"` and never lazy-loading the LCP image remove the discovery delay; less JS shortens blocking time.

For INP, a click that synchronously re-renders a 2,000-row table is a 300 ms task. Fixes: virtualize so the render is small, move the expensive update into `startTransition` so the first paint shows feedback, and avoid synchronous layout reads in handlers. Hydration counts too: a large page hydrating while the user taps gives a slow first interaction, which is why streaming and selective hydration matter.

For CLS, reserve space: `width` and `height` attributes or `aspect-ratio` on images and embeds, skeletons the same size as the content they replace, `font-display: optional` or metric-matched fallback fonts so text does not reflow, and never insert banners above existing content without user action.

**Follow-ups they will ask:**
- How do you measure INP locally: the Performance panel's interactions track, or the web-vitals library in the console with attribution.
- Which vital does a slow API hurt: LCP if the hero depends on it, otherwise none directly; perceived speed still suffers.
- What replaced FID: INP, which covers all interactions and the full duration, not only the first input's delay.

**Mistakes to avoid:**
- Quoting thresholds without knowing they apply at the 75th percentile of real users.
- Lazy-loading the hero image, which directly delays LCP.

### Q. What is your strategy for images and fonts on a performance-sensitive page?
**Short answer (45 seconds):** For images: always set intrinsic dimensions so layout is stable, serve modern formats (AVIF or WebP with fallbacks) at the sizes actually displayed via `srcset` and `sizes`, lazy-load everything below the fold and eagerly load the LCP image with a high fetch priority, and put them behind a CDN with caching. For fonts: self-host, subset to the characters you need, preload the one or two files used above the fold, use `font-display: swap` with a metric-matched fallback or `optional` for non-critical text, and limit weights.

**Deeper explanation:**

```ts
// Next.js: next/image handles srcset, lazy loading, and dimensions
<Image src={hero} alt="Dashboard overview" priority sizes="(max-width: 768px) 100vw, 50vw" />

// Plain HTML equivalent for the LCP image
<img src="/hero-1200.avif" srcset="/hero-600.avif 600w, /hero-1200.avif 1200w"
     sizes="(max-width: 768px) 100vw, 50vw" width="1200" height="600"
     fetchpriority="high" decoding="async" alt="Dashboard overview" />
```

`loading="lazy"` on below-fold images defers them until near the viewport; on the LCP image it is actively harmful. For user-generated images, an image CDN or a resizing endpoint prevents a 4 MB upload from being served to a phone. Prefer SVG for icons and illustrations, inlined for the few that are critical and sprite or component-based for the rest.

Fonts cause two problems: invisible text while loading and a layout shift when the real font swaps in. `next/font` self-hosts Google Fonts at build time and generates a fallback with `size-adjust` so the swap barely moves text; the manual equivalent is a `@font-face` with `font-display: swap` and a fallback tuned with `size-adjust`, `ascent-override`, and `descent-override`. Preload only the subset used above the fold; preloading six weights competes with the LCP image for bandwidth.

**Follow-ups they will ask:**
- Why not base64 images in CSS: they bloat the stylesheet, block rendering, and cannot be cached separately.
- What does `decoding="async"` do: lets the browser decode the image off the critical rendering path.
- Variable fonts: one file for many weights, usually smaller than three static weights.

**Mistakes to avoid:**
- Serving one 2000 px image to every device.
- Loading fonts from a third-party origin on the critical path, which adds a DNS and TLS round trip before any text renders.

### Q. What is layout thrashing, how do you avoid it, and when would you move work to a web worker?
**Short answer (45 seconds):** Layout thrashing is forcing the browser to recompute layout many times in one frame by interleaving DOM reads and writes: read an element's height, write a style, read the next element, and so on; each read after a write forces a synchronous reflow. You avoid it by batching all reads first, then all writes, by using `requestAnimationFrame` for visual updates, and by animating only `transform` and `opacity`. A web worker is for CPU-bound work that is not about the DOM at all, such as parsing a large file or running a diff, where even a well-scheduled main-thread loop would block input.

**Deeper explanation:**

```ts
// thrash: layout recomputed on every iteration
items.forEach((el) => { el.style.height = el.getBoundingClientRect().width / 2 + "px"; });

// batched: one layout for all reads, then writes
const widths = items.map((el) => el.getBoundingClientRect().width);
items.forEach((el, i) => { el.style.height = widths[i] / 2 + "px"; });
```

In React, the usual sources are measurement in `useLayoutEffect` across many siblings, scroll handlers that read `offsetTop` and set state, and animating `width`, `height`, `top`, or `left`. Use `ResizeObserver` and `IntersectionObserver` instead of polling, `transform` instead of `top`, and CSS transitions or the Web Animations API so the work stays out of JavaScript.

Workers run on a separate thread with no DOM access; messages are structure-cloned, so sending a 50 MB array every frame is itself expensive. Use transferable `ArrayBuffer`s for large payloads and a wrapper such as `comlink` so calls look like async functions. Good worker jobs: parsing a large CSV or JSON, client-side search indexing, highlighting large documents, resizing images before upload, hashing. Poor jobs: anything needing frequent round trips to the DOM or React state.

**Follow-ups they will ask:**
- How do you detect thrashing: the Performance panel marks forced synchronous layout with a warning on the layout events.
- Can a worker render React: not to the DOM; OffscreenCanvas can draw in a worker for canvas-heavy visualizations.
- Is `requestIdleCallback` an option: for low-priority background work, yes, but it is not supported everywhere and never for user-visible updates.

**Mistakes to avoid:**
- Moving a 10 ms job into a worker and paying 20 ms of serialization for it.
- Using `setTimeout(fn, 0)` loops as a scheduler instead of transitions or the browser's own scheduling APIs.

### Practice
- Record a Performance profile with 4x CPU throttling while typing in a search box over a large table; identify the long task, fix it with virtualization and a transition, and record the before and after INP.
- Run a bundle analyzer on an existing project, list the three largest dependencies, and replace or lazily load one of them; measure the main chunk size change.
- Take a page with a hero image and a web font; measure LCP and CLS in Lighthouse, add dimensions, priority hints, and a metric-matched fallback font, and re-measure.
- Write a thrashing loop that measures and resizes 500 elements, confirm the forced layout warnings, then batch reads and writes and compare frame times.
- Say it out loud: describe how you would diagnose "the dashboard feels sluggish" in the first fifteen minutes, naming the tool and the number you would look at in each step.

## Architecture for Scalable Frontends

> Architecture rounds ask how you keep a frontend healthy as the team and codebase grow by an order of magnitude. Weak answers describe a folder layout. Strong answers talk about boundaries: what one team can change without breaking another, how a component API stays stable, how failures are contained, how configuration and flags are managed, and when the heavyweight tools (monorepos, micro-frontends) earn their complexity. Interviewers are listening for trade-offs and for the phrase "it depends on the team, here is how I decide".

### Concepts you must understand
- Organize by feature, not by file type: a feature folder owns its components, hooks, API calls, and tests, exposes a small public surface, and is forbidden from reaching into another feature's internals. Boundaries are enforced with lint rules, not conventions.
- A design system is a contract: tokens, accessible primitives, and component APIs that favour composition over boolean prop explosions, with controlled and uncontrolled modes and a stable way to forward refs and extra props.
- Compound components share implicit state through context so consumers compose the parts in any layout; they trade discoverability for flexibility.
- Hooks replaced render props for sharing logic; render props still win when the consumer must control what is rendered inside the component's own structure, such as a row inside a virtualized list.
- Error boundaries catch render-phase errors in their subtree and show a fallback; they do not catch errors in event handlers, async code, or the server, so those need explicit handling.
- Routing is architecture: nested layouts, route-level code splitting, loaders that start data fetching on navigation, and route guards define how features plug into the app.
- Build-time environment variables are inlined and public; secrets never reach the client bundle. Runtime config exists for build-once, deploy-many setups.
- Feature flags decouple deploy from release; evaluate them close to the server, pass them to the client to avoid flicker, and delete them on a schedule.
- Monorepos with Turborepo or Nx give shared packages, atomic cross-package changes, and cached, affected-only CI; they need ownership rules to avoid becoming one giant ball.
- Micro-frontends solve an organizational problem (independent deploys by many teams) at a high technical cost; one product owned by a few teams almost never needs them.

### Q. How do you structure a large React codebase so that several teams can work in it without stepping on each other?
**Short answer (45 seconds):** By feature, with enforced boundaries. Each feature directory owns everything about that feature and exports a small public API from its index file; shared code lives in a separate layer for UI primitives, utilities, and API clients that features may import but that may never import from features. Routes are the composition layer that wires features into pages. A lint rule enforces the import direction so the boundary is a build failure, not a code-review comment. Teams then own features and the shared layer has a designated owner.

**Deeper explanation:**

```text
src/
  app/            routes, providers, layouts (composition only)
  features/
    billing/      components/ hooks/ api/ model/ index.ts  (public surface)
    chat/
    workspace/
  shared/
    ui/           design-system primitives
    lib/          http client, date utils, feature-flag client
    config/       env parsing, constants
```

Rules that make this work: `features/*` may import from `shared/*` and from another feature only through its `index.ts`; `shared` never imports from `features`; `app` imports from both. `eslint-plugin-boundaries` or `import/no-restricted-paths` encodes this; in an Nx monorepo `enforce-module-boundaries` does the same with tags. Co-locate tests and stories with the code they cover. Keep the public index small; a feature that exports forty symbols has no boundary.

Routing follows the same structure: each feature exposes its route segments, the app composes them into nested layouts, and route-level `lazy` imports give code splitting per feature for free. Loaders (React Router) or server components (Next.js) start data fetching at navigation time so a feature's components do not create request waterfalls.

**Follow-ups they will ask:**
- What goes in `shared` versus a feature: anything two features need with no feature-specific logic; if it has business rules it belongs to a feature.
- How do you handle a component two features both want to own: promote it to shared with a named owner, or make one feature the owner and the other a consumer through the public API.
- How do you migrate a type-based layout (components/, hooks/, utils/) to this: one feature at a time, with the lint rule in warn mode until the move is complete.

**Mistakes to avoid:**
- Presenting a folder tree as the architecture; the architecture is the import rules.
- Barrel files that re-export entire features, which erase the boundary and hurt tree shaking.

### Q. How do you design a component API for a design system that stays usable for years?
**Short answer (45 seconds):** Start from accessible, headless behaviour and layer styling on top with tokens, so visual redesigns do not change component APIs. Prefer composition to configuration: a `Card` with `Card.Header` and `Card.Body` ages better than a `Card` with twelve boolean props. Support both controlled and uncontrolled usage, forward refs and spread remaining props onto the root element so consumers can escape without forking, and express variants as a small typed set rather than free-form className overrides. Document every component with Storybook and lock behaviour with tests and visual regression.

**Deeper explanation:**

```ts
type ButtonProps = React.ComponentPropsWithoutRef<"button"> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
};

export function Button({ variant = "primary", size = "md", loading, children, ...rest }: ButtonProps) {
  return (
    <button className={buttonStyles({ variant, size })} aria-busy={loading || undefined}
      disabled={rest.disabled || loading} {...rest}>
      {loading ? <Spinner size="sm" /> : children}
    </button>
  );
}
```

Spreading `...rest` onto the root means `aria-*`, `data-testid`, and event handlers work without the design system anticipating them. A polymorphic `as` or `asChild` prop (as Radix does) lets a `Button` render as a link without duplicating styles. Controlled plus uncontrolled (`value`/`defaultValue`, `open`/`defaultOpen`) is the pattern native inputs use and consumers expect. Tokens (colour, spacing, typography) live in CSS variables so theming is a stylesheet change.

Governance matters as much as code: semantic versioning with a changelog, deprecation warnings that point at the replacement, codemods for breaking changes, and a rule that product teams propose additions through the system rather than forking locally.

**Follow-ups they will ask:**
- Build on a headless library or from scratch: build on React Aria, Radix, or Headless UI for behaviour and accessibility; write your own only when the primitive does not exist.
- How do you prevent `className` overrides from becoming the API: allow a `className` for layout concerns, document that internals are not stable, and offer variants for everything that recurs.
- How do you test it: unit tests for behaviour and keyboard interaction, axe for accessibility, Chromatic or Playwright screenshots for visual regressions.

**Mistakes to avoid:**
- Boolean prop explosions (`isPrimary`, `isLarge`, `isOutlined`) that create impossible combinations.
- A design system without an accessibility story; retrofitting it later is a rewrite.

### Q. What are compound components, and when do you use them instead of a props-driven component?
**Short answer (45 seconds):** A compound component is a parent that owns state and a set of sub-components that read it through context, so consumers compose the pieces in their own layout: `<Tabs>` with `<Tabs.List>`, `<Tabs.Trigger>`, and `<Tabs.Panel>`. You use the pattern when the component has multiple visual parts whose arrangement should be flexible, when consumers need to insert their own elements between parts, or when a prop-based API would need render props for every slot. A single-purpose component with one or two slots is better off with plain props.

**Deeper explanation:**

```ts
const TabsCtx = createContext<{ value: string; setValue: (v: string) => void } | null>(null);

export function Tabs({ defaultValue, children }: { defaultValue: string; children: React.ReactNode }) {
  const [value, setValue] = useState(defaultValue);
  const ctx = useMemo(() => ({ value, setValue }), [value]);
  return <TabsCtx.Provider value={ctx}>{children}</TabsCtx.Provider>;
}

Tabs.Trigger = function Trigger({ value, children }: { value: string; children: React.ReactNode }) {
  const ctx = useTabs();
  return (
    <button role="tab" aria-selected={ctx.value === value} onClick={() => ctx.setValue(value)}>
      {children}
    </button>
  );
};
```

The context is private to the component family, so the state is implicit for consumers but still controlled by the parent. Add a `value`/`onValueChange` pair to the root for controlled use. The downsides: sub-components only work inside the parent, so the `useTabs` hook must throw a clear message when the context is missing; the API is less discoverable than a props list; and each sub-component is a context consumer, so a frequently changing value re-renders all of them, which rarely matters for tabs but does for a high-frequency slider.

Headless libraries use this pattern everywhere (Radix `Select`, React Aria components), which is a strong signal for when it fits: components with roles, keyboard navigation, and several moving parts.

**Follow-ups they will ask:**
- Why not `React.Children.map` to inject props: it breaks when consumers wrap or reorder children; context does not care about tree position.
- How do you type the dot-notation sub-components: assign them as static properties with explicit prop types, or export them as named exports alongside the root.
- How do you keep styling flexible: expose data attributes such as `data-state="active"` for CSS and let consumers pass className per part.

**Mistakes to avoid:**
- Using compound components for a simple component with one content slot.
- Letting sub-components reach into the parent's DOM; communicate only through the shared context.

### Q. Render props versus custom hooks: when is each the right abstraction?
**Short answer (45 seconds):** Hooks are the default for sharing stateful logic: they compose, they do not nest the JSX tree, and TypeScript types them cleanly. Render props remain the right tool when the component owns the structure and the consumer only decides what to render inside it, such as the row of a virtualized list, the item of a combobox, or a slot in a layout that must exist at a specific DOM position. The test is: does the consumer need logic (use a hook) or a rendering slot (use a render prop)?

**Deeper explanation:** Before hooks, render props and higher-order components were the only ways to reuse behaviour, which produced the "wrapper hell" of nested providers and callbacks. Hooks removed that for logic. What hooks cannot do is render on behalf of a component: a list virtualizer must create the scroll container and position each row itself, so it asks you for a function from item to element.

```ts
// Render prop: the component controls where and when the row renders
<VirtualList items={rows} rowHeight={40}
  renderRow={(row, style) => <div style={style}>{row.name}</div>} />

// Hook: you control rendering, the hook provides logic
const { getInputProps, getItemProps, highlightedIndex } = useCombobox({ items });
```

Headless UI libraries often offer both: a hook for full control and a component with render props for convenience. Prop getters (`getInputProps()`) are the bridge: the hook hands back props objects that you spread onto your own elements, keeping behaviour and accessibility centralized while leaving markup to you. A `children` function is just a render prop by another name and should follow the same rule.

**Follow-ups they will ask:**
- Are higher-order components dead: mostly; they survive for cross-cutting wrappers such as `withErrorBoundary` where wrapping a component is the point.
- Performance difference: a render prop is a new function per render; it only matters if the receiving component is memoized on it.
- How do you type a render prop: as a function type on the props, `(item: T, style: CSSProperties) => ReactNode`, with the component generic over `T`.

**Mistakes to avoid:**
- Converting every render prop to a hook and losing the component's control of structure.
- Nesting three render-prop components for logic that a single custom hook could express.

### Q. How do error boundaries work, and how do you use them in a production React app?
**Short answer (45 seconds):** An error boundary is a class component that implements `getDerivedStateFromError` and `componentDidCatch`; when any component in its subtree throws during render, lifecycle, or constructor, React unmounts that subtree and renders the boundary's fallback. They do not catch errors from event handlers, async callbacks, server rendering, or the boundary itself. In production you place them at the route level so a crash shows an error page instead of a blank screen, and around independent widgets so one broken panel does not take down the dashboard, and you report the error with its component stack.

**Deeper explanation:** Most teams use the `react-error-boundary` package rather than writing the class. It provides a `FallbackComponent` with `resetErrorBoundary`, `resetKeys` to recover automatically when some input changes, and `useErrorBoundary` to forward errors from event handlers and effects into the nearest boundary.

```ts
<ErrorBoundary
  FallbackComponent={({ error, resetErrorBoundary }) => (
    <Panel title="Chart unavailable">
      <button onClick={resetErrorBoundary}>Retry</button>
    </Panel>
  )}
  resetKeys={[dashboardId]}
  onError={(error, info) => report(error, { componentStack: info.componentStack })}
>
  <RevenueChart id={dashboardId} />
</ErrorBoundary>
```

Boundary placement is a product decision: a failing comment widget should degrade, a failing checkout should show a full recovery page. Pair boundaries with Suspense: an async error thrown while a lazy chunk or a query fails lands in the nearest boundary, and TanStack Query's `throwOnError` turns data errors into boundary errors where that is the desired UX. React 19 adds root-level `onCaughtError` and `onUncaughtError` options to `createRoot` for centralized reporting, and it stopped re-throwing caught errors to the console twice.

**Follow-ups they will ask:**
- How do you handle an error in an `onClick`: try/catch there, or call `showBoundary(error)` from `useErrorBoundary`.
- Why not one boundary at the root: it works as a last resort but turns any widget bug into a full-page failure.
- How do you test a boundary: render a child that throws and assert the fallback; silence the expected console error in the test.

**Mistakes to avoid:**
- Saying boundaries catch all errors; the handler, async, and SSR gaps are the usual follow-up.
- A fallback with no retry and no reporting; the user is stuck and you never hear about it.

### Q. How do you manage environment configuration and feature flags in a frontend?
**Short answer (45 seconds):** Build-time variables (`VITE_*`, `NEXT_PUBLIC_*`) are string-replaced into the bundle, so they are public by definition and only hold things like API base URLs and public keys; secrets live on the server. I validate them at startup with a schema so a missing variable fails the build, not a user's session. When the same build must run in several environments, config is loaded at runtime from an endpoint or injected into the HTML. Feature flags come from a flag service, are evaluated as early as possible, ideally on the server, and are passed to the client so there is no flicker; each flag has an owner and a removal date.

**Deeper explanation:**

```ts
// shared/config/env.ts: fail fast on misconfiguration
const envSchema = z.object({
  VITE_API_URL: z.string().url(),
  VITE_SENTRY_DSN: z.string().optional(),
  MODE: z.enum(["development", "staging", "production"]),
});
export const env = envSchema.parse(import.meta.env);
```

Runtime config is the pattern for containers: the image is built once and a small `/config.json` or a server-generated `window.__CONFIG__` supplies per-environment values. Next.js server components and route handlers read `process.env` directly, keeping secrets server-side; anything prefixed `NEXT_PUBLIC_` is inlined into client code.

Flags come in three kinds: release toggles (ship dark, flip on, delete within weeks), experiments (randomized, measured, removed), and operational kill switches (long-lived, documented). The client reads them through a hook such as `useFlag("new-checkout")` backed by LaunchDarkly, Unleash, GrowthBook, Statsig, or PostHog; defaults are the safe state, usually off; and server-side evaluation sent in the initial payload avoids the flash of old UI that client-only evaluation causes.

**Follow-ups they will ask:**
- How do you keep flags from rotting: a registry with owner and expiry, a lint or CI check that fails on expired flags, and removal as part of the rollout ticket.
- Can a flag hide code from the bundle: not at runtime; only build-time constants let the bundler drop a branch.
- How do you test both flag states: tests inject the flag provider with fixed values; e2e runs the critical path in both states.

**Mistakes to avoid:**
- Putting a private API key in a `VITE_` variable because "it is only used by our frontend".
- Using flags as permanent configuration, which leaves dozens of dead branches nobody dares delete.

### Q. When do you reach for a monorepo with Turborepo or Nx, and how do you keep it from becoming slow?
**Short answer (45 seconds):** When several deployables share code that changes together: a web app, an admin app, a component library, shared types with the backend, and configuration packages for ESLint and TypeScript. A monorepo lets one pull request change a shared package and every consumer atomically, with one toolchain. The cost is CI time and coupling, which is why the tooling matters: Turborepo and Nx build a task graph, run only what changed, and cache task outputs locally and remotely so an unchanged package's tests never run twice.

**Deeper explanation:** With pnpm workspaces as the package manager, `packages/ui`, `packages/config-eslint`, `packages/tsconfig`, and `apps/web` reference each other with `workspace:*`. Turborepo's `turbo.json` declares each task's dependencies (`build` depends on `^build` of dependencies) and outputs, which is what makes caching correct. Nx adds a project graph, `affected` commands based on git diff, generators, and tag-based import boundaries.

```json
{
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**", ".next/**"] },
    "test":  { "dependsOn": ["build"], "outputs": ["coverage/**"] },
    "lint":  {}
  }
}
```

Keeping it fast: enable remote caching so CI and developers share results; keep internal packages small and side-effect free so changes invalidate little; choose between "just-in-time" packages consumed as TypeScript by the app's bundler and prebuilt packages with `dist` (slower locally, caches better); pin one React version across the repo; and use a changeset tool if packages are published.

The organizational part: ownership files per package, a shared `config` package so lint and TypeScript rules do not drift, and a rule that `apps` depend on `packages`, never the reverse.

**Follow-ups they will ask:**
- Monorepo or multi-repo for frontend and backend: a monorepo when they share types or an API contract that changes together; otherwise independent repos with a published contract.
- How do you avoid version drift of dependencies: a single lockfile, a tool such as `syncpack` or pnpm catalogs, and renovate updates across the workspace.
- Turborepo or Nx: Turborepo is smaller and simpler; Nx gives more structure (graph, generators, boundary enforcement) and suits larger organizations.

**Mistakes to avoid:**
- A monorepo for a single app with no shared packages.
- Running the whole test suite on every commit because the task graph was never declared.

### Q. Micro-frontends and module federation: when are they justified, and when are they a mistake?
**Short answer (45 seconds):** Micro-frontends split one application into independently built and deployed pieces, each owned by a team. They are justified when the organization is large enough that a single build and release train is the bottleneck, when teams genuinely need different release cadences, or when integrating acquired products with different stacks. They are a mistake for one product owned by a handful of teams: duplicated dependencies, inconsistent UX, cross-app state problems, and a harder debugging and performance story, in exchange for deployment independence those teams did not need.

**Deeper explanation:** Module Federation (webpack 5, also Rspack and Vite plugins) lets one bundle load modules from another at runtime and share dependencies as singletons, so `react` loads once. Alternatives: single-spa for routing between frameworks, iframes for strict isolation, web components for neutral embedding, and the simplest option, a monorepo with one build where teams own packages but deploy together.

```text
Shell app (routing, auth, layout)
  /checkout   -> remote "checkout"  built and deployed by Payments team
  /search     -> remote "search"    built and deployed by Discovery team
shared singletons: react, react-dom, design-system, router
```

Failure modes to name: version skew of shared singletons between remotes and shell; duplicated bundles when sharing is misconfigured; design drift as each team ships its own copy of the design system; shared state and auth passed through global events or the URL; and local development that needs several apps running. Needed maturity: contract tests between shell and remotes, a strictly versioned design system, errors tagged by remote, and a performance budget per remote.

**Follow-ups they will ask:**
- How do remotes share state: avoid it; where unavoidable use the URL, a tiny event bus, or a shared store exposed as a singleton with a versioned contract.
- Do Next.js multi-zones change this: they route path prefixes to separate apps, giving page-level deployment independence with less runtime coupling.
- How would you migrate away: collapse remotes into packages of a monorepo one at a time, keeping team ownership but unifying the build.

**Mistakes to avoid:**
- Proposing micro-frontends as a technical fix for a slow build; caching and splitting fix that with no new runtime.
- Claiming they are "just microservices for the frontend" without naming the shared-dependency and UX costs.

### Practice
- Add `eslint-plugin-boundaries` (or `import/no-restricted-paths`) to an existing project with a feature layout and fix every violation; note which cross-feature imports were real coupling.
- Build a `Tabs` compound component with controlled and uncontrolled modes, keyboard navigation, and `data-state` attributes; write tests for arrow-key behaviour.
- Wrap three dashboard widgets in individual error boundaries that report to the console with component stacks; throw inside one and verify the others survive and the retry works.
- Create a two-app Turborepo with a shared `ui` package, declare the task graph, and show that a change to one app does not re-run the other's tests.
- Say it out loud: a director asks whether the team of twelve should adopt micro-frontends. Give your recommendation, the two conditions that would change it, and the cheaper alternative.

## Data Fetching, Caching & Real-time

> This section is where full-stack experience shows. Interviewers want to hear that you treat the network as unreliable and slow by default: requests get cancelled, responses arrive out of order, connections drop, users go offline. A weak answer is "I use axios and useEffect". A strong answer describes a typed HTTP layer, explains caching semantics, picks a real-time transport for a reason, and knows how reconnection avoids duplicate or lost messages.

### Concepts you must understand
- A frontend needs one HTTP layer: base URL, auth headers, JSON parsing, error normalization, timeouts, and cancellation in one place; `fetch` needs a thin wrapper for this, `axios` gives interceptors out of the box.
- `fetch` only rejects on network failure; a 500 resolves successfully, so `response.ok` must be checked and turned into a typed error.
- Stale-while-revalidate serves cached data immediately and refreshes it in the background; it exists at the HTTP layer (`Cache-Control`) and in client caches (TanStack Query, SWR).
- Deduplication collapses concurrent identical requests into one in-flight promise; cancellation with `AbortController` stops requests whose result nobody will use.
- Out-of-order responses are a race, not a network bug: the fix is to cancel or ignore every response except the latest.
- Offset pagination is simple but unstable under inserts; cursor pagination is stable and cheap for deep pages but has no random access. Infinite scroll is cursor pagination driven by an intersection observer.
- WebSockets are bidirectional and need their own heartbeat and scaling story; SSE is server-to-client over plain HTTP with built-in reconnection and `Last-Event-ID`; polling is the boring option that is often enough.
- Reconnection needs exponential backoff with jitter, a way to resume from the last seen event, and idempotent handling so replayed messages are harmless.
- Retries belong only on idempotent or retryable failures (network errors, 5xx, 429 with `Retry-After`); mutations need idempotency keys to be retried safely.
- Offline support is a spectrum: from "show cached data and queue mutations" to a service worker with background sync.

### Q. How do you structure the HTTP layer of a frontend application?
**Short answer (45 seconds):** One module owns the transport. It sets the base URL and credentials, attaches the auth header, applies a timeout and the caller's abort signal, parses JSON, and converts every non-2xx response into a typed `ApiError` with status, code, and the server's message. On top of that sit resource functions (`todos.list`, `todos.create`) that return typed data, and the data layer (TanStack Query hooks) calls those. Components never see URLs or `fetch`. Whether the transport is `fetch` or `axios` matters less than the fact that there is exactly one.

**Deeper explanation:**

```ts
export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

export async function http<T>(path: string, init: RequestInit & { timeoutMs?: number } = {}): Promise<T> {
  const signal = init.signal
    ? AbortSignal.any([init.signal, AbortSignal.timeout(init.timeoutMs ?? 15_000)])
    : AbortSignal.timeout(init.timeoutMs ?? 15_000);
  const res = await fetch(`${env.VITE_API_URL}${path}`, {
    ...init, signal, credentials: "include",
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.code ?? "unknown", body.message ?? res.statusText);
  }
  return res.status === 204 ? (undefined as T) : (res.json() as Promise<T>);
}
```

`axios` gives you this shape with interceptors, automatic JSON, and rejection on non-2xx, plus upload progress events, which is why many teams still prefer it; `ky` and `ofetch` are smaller wrappers with the same ideas. Validate responses at the boundary with zod for endpoints you do not control, and log a schema mismatch instead of crashing. Keep the layer free of React so it can be used from a service worker, a WebSocket handler, or a test.

**Follow-ups they will ask:**
- Where does token refresh go: in this layer, as a single-flight refresh that queues concurrent 401s and replays them once.
- How do you add tracing: a request id header generated here and echoed by the server so frontend and backend logs correlate.
- How do you mock it in tests: with MSW at the network level, so the real layer runs and only the server is fake.

**Mistakes to avoid:**
- Calling `fetch` inside components, which scatters error handling and auth logic.
- Treating a resolved `fetch` as success without checking `response.ok`.

### Q. Explain stale-while-revalidate and where it appears in a frontend stack.
**Short answer (45 seconds):** Stale-while-revalidate means: if cached data exists, show it immediately even if it is past its freshness window, and fetch a new copy in the background to replace it. The user sees content instantly and gets the fresh version a moment later. At the HTTP layer it is a `Cache-Control` directive honoured by browsers and CDNs. In the client it is the default behaviour of TanStack Query and SWR: cached data renders, then a background refetch runs when the data is stale and a component mounts, the window regains focus, or the network reconnects.

**Deeper explanation:**

```text
Cache-Control: max-age=60, stale-while-revalidate=300
  0-60 s   : fresh, served from cache, no request
  60-360 s : stale, served from cache immediately, revalidated in background
  > 360 s  : must fetch before responding
```

The pattern trades a window of possible staleness for instant responses, so it fits data where a slightly old value is acceptable: lists, dashboards, profiles. It does not fit data where showing an old value is wrong, such as an account balance before a payment or a seat count during checkout; there you set `staleTime: 0` and show a pending state, or fetch on demand. In TanStack Query the knobs are `staleTime` (how long data is fresh) and the refetch triggers; `gcTime` is separate and controls memory. The UI should distinguish "stale, refreshing" from "loading": a subtle indicator or none at all for background refreshes, a skeleton only when there is nothing to show.

CDN-level SWR matters for API responses and server-rendered pages too: Next.js ISR is stale-while-revalidate for whole pages, serving the cached HTML and regenerating in the background after the revalidation window.

**Follow-ups they will ask:**
- How does the UI avoid flicker when fresh data arrives: structural sharing in TanStack Query keeps unchanged references, so unchanged rows do not re-render.
- What about `ETag` and `If-None-Match`: conditional requests make revalidation cheap (304 with no body) and complement SWR.
- How do you handle a user who edited data that is being revalidated: cancel the refetch in `onMutate` and write the result into the cache, then invalidate.

**Mistakes to avoid:**
- Describing SWR as "caching"; the defining part is the background revalidation and the instant stale response.
- Applying it to data where stale values have consequences.

### Q. How do you deduplicate requests and cancel the ones whose results are no longer needed?
**Short answer (45 seconds):** Deduplication keeps a map of in-flight promises keyed by the request identity and returns the same promise to every caller until it settles; TanStack Query does this per query key, so twenty components asking for the same user make one request. Cancellation uses `AbortController`: pass its `signal` to `fetch`, and call `abort()` when the component unmounts, the search term changes, or the user navigates away. Together they fix the two classic bugs: N identical requests on page load, and an old search response overwriting a newer one.

**Deeper explanation:**

```ts
// Latest-wins search: abort the previous request when the query changes
useEffect(() => {
  const controller = new AbortController();
  http<Result[]>(`/search?q=${encodeURIComponent(q)}`, { signal: controller.signal })
    .then(setResults)
    .catch((e) => { if (e.name !== "AbortError") setError(e); });
  return () => controller.abort();
}, [q]);
```

If you cannot abort (a third-party SDK, for example), the fallback is a sequence number or a "latest request" ref: each response checks whether it is still the latest before writing state. Aborting is better because it also frees the connection and stops the server work when the server supports it.

Dedup across components is a cache concern, which is one reason to use a query library rather than per-component effects. Within a single server render, Next.js memoizes identical `fetch` calls and React's `cache` function does the same for arbitrary functions in server components, so a layout and a page can both ask for the current user without two database calls. On the client, `useQuery` with the same key in parallel mounts shares the promise, and `queryClient.prefetchQuery` in a route loader or on hover warms the cache so the component mounts with data.

**Follow-ups they will ask:**
- Does aborting a POST undo it: no; the server may have processed it. Abort only reads, or design the write to be idempotent.
- How do you add a timeout: `AbortSignal.timeout(ms)`, combined with the caller's signal via `AbortSignal.any` in modern browsers.
- How does TanStack Query cancel: it passes a `signal` to the `queryFn`; forwarding it to `fetch` is what makes cancellation real.

**Mistakes to avoid:**
- Treating `AbortError` as a failure and showing an error toast for every cancelled search.
- Debouncing instead of cancelling and still writing an out-of-order response.

### Q. Offset versus cursor pagination, and how do you implement infinite scroll correctly?
**Short answer (45 seconds):** Offset pagination (`?page=3&limit=20`) is easy and supports jumping to a page, but inserts and deletes between requests shift items so users see duplicates or skip rows, and deep offsets are slow in SQL. Cursor pagination returns an opaque cursor pointing at the last item, usually encoding a sort key such as `(created_at, id)`, so the next page is stable and cheap; the cost is no random access. Infinite scroll is cursor pagination where a sentinel element near the bottom triggers the next fetch through `IntersectionObserver`, with the pages kept in a flat list.

**Deeper explanation:**

```ts
const query = useInfiniteQuery({
  queryKey: ["feed", filters],
  queryFn: ({ pageParam, signal }) => api.feed.list({ cursor: pageParam, ...filters, signal }),
  initialPageParam: undefined as string | undefined,
  getNextPageParam: (last) => last.nextCursor ?? undefined,
});

const sentinelRef = useIntersection(() => {
  if (query.hasNextPage && !query.isFetchingNextPage) query.fetchNextPage();
});
const items = query.data?.pages.flatMap((p) => p.items) ?? [];
```

Details that separate a working feed from a broken one: guard `fetchNextPage` with `isFetchingNextPage` so a fast scroll does not fire twice; disable the observer when `hasNextPage` is false; give the user a way out of infinite scroll (a footer that becomes reachable, or a "load more" button after a few pages) for accessibility and for finding the footer at all; restore scroll position on back navigation by caching the pages, which the query cache already does; and show new items that arrived at the top with a "new posts" affordance rather than silently shifting the list under the user's thumb.

On the server, keyset pagination (`WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT 20`) with a matching index is what makes cursors cheap; the cursor is just those two values encoded.

**Follow-ups they will ask:**
- How do you show total count with cursors: a separate, cached count query, or an approximate count; cursors do not give it for free.
- How do you handle an item deleted mid-scroll: cursors skip it naturally; with offsets you would duplicate the following row.
- Virtualize or not: once the list holds more than a few hundred rich rows, combine infinite scroll with a virtualizer.

**Mistakes to avoid:**
- Offset pagination on a feed that changes constantly.
- Infinite scroll with no stopping point, no footer access, and no keyboard way to load more.

### Q. WebSockets, Server-Sent Events, or polling: how do you choose?
**Short answer (45 seconds):** Polling first if updates are infrequent and a few seconds of delay is fine, because it needs no new infrastructure and caches well. SSE when the server pushes to the client but the client talks back over normal HTTP: notifications, live dashboards, LLM token streams. It runs over plain HTTP, reconnects automatically, resumes with `Last-Event-ID`, and passes through proxies and CDNs. WebSockets when traffic is genuinely bidirectional and frequent, such as collaborative editing, chat with typing indicators, or games, and you are prepared to own heartbeats, reconnection, and horizontal scaling with a pub/sub layer.

**Deeper explanation:**

```text
                 polling        SSE                       WebSocket
direction        client pull    server -> client          both
protocol         HTTP           HTTP, text/event-stream   ws:// upgrade
reconnect        n/a            built into EventSource    you implement
binary           no             no (text only)            yes
infra            none           keep-alive aware proxies  sticky or pub/sub (Redis)
```

SSE specifics worth knowing: the `EventSource` API cannot set custom headers, so auth is cookies or a token in the URL, or you use `fetch` with a streaming body reader and parse `text/event-stream` yourself (which is what the Vercel AI SDK does); over HTTP/1.1 browsers cap connections per origin, so several open SSE streams to one host can starve other requests, a problem HTTP/2 removes. WebSocket specifics: proxies and load balancers need idle timeouts raised; connections are stateful, so scaling to many servers requires a broker (Redis pub/sub, NATS) to fan out messages; and you must send ping frames or application heartbeats to detect dead connections, because TCP will not tell you promptly.

For an AI chat product the usual answer is SSE or a streamed `fetch` response for model output, plus normal POSTs for user messages; WebSockets only when the product also needs presence, typing indicators, or multiplayer.

**Follow-ups they will ask:**
- Can SSE work behind Nginx or a CDN: yes, with buffering disabled (`X-Accel-Buffering: no`) and a long read timeout.
- Why not WebSockets for everything: operational cost; every stateful connection complicates deploys, scaling, and auth rotation.
- What about WebTransport or HTTP/3: promising for low-latency bidirectional traffic, not yet the default choice in product code.

**Mistakes to avoid:**
- Choosing WebSockets for a one-directional notification feed.
- Forgetting that `EventSource` reconnects on its own and layering a second reconnect loop on top.

### Q. How do you handle reconnection for a long-lived connection without losing or duplicating messages?
**Short answer (45 seconds):** Three parts. Detect the drop quickly with heartbeats, because a half-open TCP connection can stay silent for minutes. Reconnect with exponential backoff plus jitter and a cap, and reset the delay after a successful connection. Resume rather than restart: every message carries a monotonic id or sequence, the client sends the last one it saw on reconnect, and the server replays from there, or the client refetches the current state and then subscribes. Consumers must be idempotent, keyed by message id, so a replayed message is a no-op.

**Deeper explanation:**

```ts
function connect(attempt = 0) {
  const ws = new WebSocket(`${url}?since=${lastSeq}`);
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data) as { seq: number; payload: unknown };
    if (msg.seq <= lastSeq) return;         // duplicate from replay
    lastSeq = msg.seq;
    handle(msg.payload);
  };
  ws.onclose = () => {
    const base = Math.min(30_000, 500 * 2 ** attempt);
    const delay = base / 2 + Math.random() * (base / 2);   // jitter
    setTimeout(() => connect(attempt + 1), delay);
  };
  ws.onopen = () => { attempt = 0; startHeartbeat(ws); };
}
```

Jitter matters when a server restarts: without it, every client reconnects at the same instant and the server falls over again. Also reconnect immediately on the browser's `online` event and when the tab becomes visible, and pause heartbeats in hidden tabs to save battery. If the gap is too large for the server's replay buffer, the server should say so and the client should do a full state resync, which is the "fetch state, then subscribe from the state's version" pattern used by collaborative editors.

With SSE much of this is built in: `EventSource` reconnects by itself, sends `Last-Event-ID`, and honours the server's `retry:` field. You still need idempotent handling on the client and a replay window on the server.

**Follow-ups they will ask:**
- What if messages are not idempotent: make them so by including an id and a version; a "balance += 10" message is unsafe to replay, "balance = 110 at version 7" is safe.
- How do you surface connection state to the user: a small "reconnecting" indicator after a grace period, and disable sending until reconnected.
- How does auth survive reconnects: re-read the current token at connect time rather than capturing it once.

**Mistakes to avoid:**
- Fixed-interval retries with no jitter and no cap.
- Reconnecting and re-subscribing without resuming, which silently drops everything sent during the gap.

### Q. How do you design retries and offline behaviour in a frontend?
**Short answer (45 seconds):** Retry only what is safe to retry: network failures, 5xx, 408, and 429 with the `Retry-After` header honoured, never 4xx validation or auth errors. Reads can retry freely with exponential backoff; writes need an idempotency key so a retried POST does not create two orders. When offline, show cached data with a clear indicator, queue mutations and replay them in order when connectivity returns, and tell the user what is pending. A service worker is the step after that: caching the app shell and API responses so the app loads offline at all.

**Deeper explanation:** TanStack Query retries failed queries three times by default with exponential backoff and pauses fetching while the browser reports offline, resuming on reconnect; configure `retry` to a function so 4xx errors fail fast. For mutations, retrying is off by default and should stay off unless the server accepts an `Idempotency-Key` header, in which case the key is generated once per user action and reused for every retry.

```ts
const create = useMutation({
  mutationFn: (input: NewOrder) =>
    http("/orders", { method: "POST", body: JSON.stringify(input),
      headers: { "Idempotency-Key": input.clientId } }),
  retry: (count, err) => count < 3 && (err instanceof ApiError ? err.status >= 500 : true),
});
```

Offline-first apps persist the query cache (TanStack's persister) and the mutation queue to IndexedDB so a reload does not lose pending work, and resolve conflicts when a queued write hits data that changed on the server: last write wins with a notice, or a merge for structured data. A service worker built with Workbox caches static assets with cache-first and API GETs with network-first or stale-while-revalidate, and background sync can replay queued requests even after the tab closes.

**Follow-ups they will ask:**
- How do you detect offline reliably: `navigator.onLine` is a hint; treat a failed request as the real signal and recover on the `online` event.
- How do you prevent retry storms: backoff with jitter, a retry budget, and honouring `Retry-After`.
- How do you test offline: Playwright's `context.setOffline(true)` and the Network panel's offline throttle.

**Mistakes to avoid:**
- Retrying a non-idempotent POST and double-charging a customer.
- Retrying 400 and 401 responses, which can lock accounts or hide validation errors.

### Q. How do you implement auth token refresh in the HTTP layer without a storm of failed requests?
**Short answer (45 seconds):** The layer intercepts a 401, triggers one refresh, and makes every other request that fails during that window wait on the same refresh promise instead of starting their own, then replays them with the new token. If the refresh itself fails, it clears the session once and redirects to login. Where possible the refresh token lives in an httpOnly cookie and the access token is short-lived and held in memory, so a page load starts with a silent refresh rather than reading a token from storage.

**Deeper explanation:**

```ts
let refreshing: Promise<string> | null = null;

async function withAuth<T>(path: string, init: RequestInit = {}, retried = false): Promise<T> {
  try {
    return await http<T>(path, { ...init, headers: { ...init.headers, Authorization: `Bearer ${accessToken}` } });
  } catch (e) {
    if (!(e instanceof ApiError) || e.status !== 401 || retried) throw e;
    refreshing ??= refreshAccessToken().finally(() => { refreshing = null; });
    accessToken = await refreshing;          // every concurrent 401 awaits this one promise
    return withAuth<T>(path, init, true);    // replay once
  }
}
```

The `retried` flag prevents an infinite loop when the replayed request also returns 401. The single-flight promise is the core: a dashboard that fires twelve requests on load must not fire twelve refreshes, which would rotate the refresh token twelve times and, with rotation enabled, invalidate the session. Proactive refresh (a timer that refreshes shortly before expiry) reduces the number of 401s users ever see, but the reactive path is still required because timers drift and tabs sleep. With multiple tabs, coordinate through the `BroadcastChannel` API or a storage event so one tab refreshes and the others pick up the new token.

**Follow-ups they will ask:**
- Where is the access token stored: in memory in the JS module; a refresh on page load restores it; never `localStorage` if XSS is a concern.
- What does the server need: short access token lifetime, rotating refresh tokens with reuse detection, and a refresh endpoint that reads the httpOnly cookie.
- How do WebSocket connections get a new token: reconnect with the current token when it changes, or use a short-lived ticket endpoint for the handshake.

**Mistakes to avoid:**
- Refreshing inside every component's error handler instead of once in the transport layer.
- Retrying on 401 without a guard, so an invalid session loops forever.

### Practice
- Write a `fetch` wrapper with timeout, abort merging, typed errors, and single-flight token refresh; unit test the refresh path with three concurrent 401s and assert one refresh call.
- Build a search box that fires on every keystroke with no cancellation, throttle the network in DevTools, type quickly, and capture the out-of-order bug; fix it with `AbortController` and verify.
- Implement a feed with `useInfiniteQuery`, a cursor API, and an intersection sentinel; verify no duplicate fetch on fast scroll and that back navigation restores position.
- Build a tiny SSE endpoint in Express that emits ids, kill the server mid-stream, and watch `EventSource` reconnect with `Last-Event-ID`; then implement the same resume logic over a WebSocket by hand.
- Say it out loud: a product manager wants "live updates" on an orders page. Ask the three questions that decide between polling, SSE, and WebSockets, and give the recommendation for a page that changes a few times a minute.

## Next.js & Rendering Strategies

> Next.js questions test whether you understand where code runs and when HTML is produced. Weak answers list acronyms. Strong answers pick a rendering strategy per page with a reason, explain what Server Components change about data access and bundle size, know the caching layers well enough to debug "why is my page stale", and can say when a plain SPA is the better tool. Interviewers hiring for AI products also care about streaming, because model responses are streamed.

### Concepts you must understand
- CSR ships an empty shell and renders in the browser; SSR renders HTML per request; SSG renders at build; ISR serves static HTML and regenerates it in the background after a revalidation window or on demand. The choice is per route, driven by freshness, personalization, and SEO.
- React Server Components run only on the server, add nothing to the client bundle, can read databases directly, and send a serialized tree (the RSC payload) that the client merges with client components; they are different from SSR, which renders client components to HTML.
- `"use client"` marks the boundary where the client bundle starts; server components can render client components and pass them serializable props or server-rendered children.
- Server actions are server functions callable from forms and client components; they are public HTTP endpoints and must validate input and check authorization like any API.
- Hydration attaches React to server-rendered HTML; a mismatch between server output and the client's first render is a hydration error, caused by non-deterministic values, browser-only branches, invalid HTML nesting, or extensions.
- Streaming SSR sends the shell immediately and fills Suspense boundaries as their data resolves; selective hydration lets the user interact with hydrated parts while others are still loading.
- The App Router has several caches: per-request fetch memoization, the data cache, the full route cache, and the client-side router cache; knowing which one holds stale data is the debugging skill.
- The Edge runtime is a lightweight V8 environment close to users with a Web API subset; the Node runtime has full Node APIs and TCP database drivers. Compute location should match data location.
- Metadata, sitemaps, robots, and Open Graph images are generated server-side per route; SSR or SSG exists partly so crawlers and link previews see real content.
- Next.js is the wrong tool for a purely authenticated SPA with no SEO needs, a static content site that another tool serves better, or a product whose backend is a long-lived stateful server.

### Q. Compare CSR, SSR, SSG, and ISR. How do you choose for a given page?
**Short answer (45 seconds):** I ask three questions per page: does it need to be indexed or previewed by crawlers, how fresh must it be, and is it personalized. A marketing page is SSG. A blog or product catalogue that changes hourly is ISR with a revalidation window or on-demand revalidation on publish. A personalized dashboard behind login is SSR for the shell with client fetching for live data, or pure CSR if SEO is irrelevant and the data is all user-specific. A real-time view such as a chat is CSR inside whatever shell the app already has.

**Deeper explanation:**

```text
Strategy  When HTML is made         Freshness        Cost per request   Good for
CSR       in the browser            live             static file        logged-in apps, tools
SSR       every request             live             server CPU         personalized, SEO-critical
SSG       at build                  build time       CDN hit            docs, marketing
ISR       at build, then on demand  revalidate window CDN hit mostly    catalogues, blogs, news
```

In the App Router a route is static unless something makes it dynamic: reading `cookies()`, `headers()`, or `searchParams`, or opting out with `export const dynamic = "force-dynamic"`. `export const revalidate = 60` turns a static route into ISR. On-demand revalidation (`revalidatePath`, `revalidateTag`) from a webhook or a server action gives you static speed with publish-time freshness, which is the strategy for most content-heavy pages.

The trade-offs to mention: SSR adds server cost and TTFB that depends on your slowest data source, so stream it; SSG and ISR need a build or regeneration pipeline and can serve a stale page for one request after the window; CSR gives the worst first paint and no crawler content but the simplest hosting. Most real apps mix these per route rather than picking one globally.

**Follow-ups they will ask:**
- How does ISR behave on the first request after the window: it serves the stale page and regenerates in the background; the next visitor sees the fresh one.
- Can a static page show user-specific data: yes, render the static shell and fetch the personalized bits on the client or in a streamed Suspense boundary.
- What about `generateStaticParams`: it pre-renders a known set of dynamic routes at build; unknown params fall back to on-demand rendering.

**Mistakes to avoid:**
- Choosing one strategy for the whole app.
- Making a page dynamic by accident (reading cookies in a layout) and losing CDN caching for everything under it.

### Q. What are React Server Components, and what problem do they solve that SSR did not?
**Short answer (45 seconds):** Server Components execute only on the server, at request or build time, and never ship their code to the browser. They can be `async`, read a database directly, import heavy libraries such as a markdown parser without affecting the client bundle, and output a serialized tree that React merges with interactive client components. SSR gave crawlers and users a fast first paint, but all the component code still shipped and re-ran in the browser; RSC removes that code and the data-fetching round trips for the non-interactive parts of the page.

**Deeper explanation:**

```ts
// app/invoices/page.tsx: server component, no "use client"
export default async function InvoicesPage({ searchParams }: Props) {
  const { status } = await searchParams;
  const invoices = await db.invoice.findMany({ where: { status } });   // direct DB access
  return (
    <section>
      <InvoiceFilters />                       // client component: needs state and events
      <InvoiceTable rows={invoices} />         // server component: markup only
    </section>
  );
}
```

`"use client"` marks a module as the entry point of a client bundle; everything it imports is client code. Client components cannot import server components but can receive them as `children` or props, which is how an interactive shell wraps server-rendered content. Props crossing the boundary must be serializable: no functions except server actions, no class instances.

What RSC is not: a replacement for client state or interactivity, or SSR. In the App Router both happen: server components produce the RSC payload, client components are server-rendered to HTML for the first paint and hydrated, and navigation fetches only the payload. Mental model: server components are a templating layer with React's composition, client components are the app.

**Follow-ups they will ask:**
- Does `useState` work in a server component: no; no hooks that need state, effects, or browser APIs.
- How do you share code between both: a directive-free module can be imported by either side if it has no server-only or client-only imports; the `server-only` and `client-only` packages enforce it.
- Does RSC remove the need for TanStack Query: for initial reads often yes; for client caching, polling, optimistic updates, and real-time it still earns its place.

**Mistakes to avoid:**
- Saying RSC "renders on the server like SSR". The difference is that no code ships and the output is a tree, not HTML.
- Adding `"use client"` at the top of a page to fix an error, which pushes the whole subtree into the client bundle.

### Q. What are server actions, and how do you use them safely?
**Short answer (45 seconds):** A server action is an async function marked with `"use server"` that the framework exposes as a POST endpoint; forms can call it directly through `action={fn}` and client components can call it like a function. It runs on the server with access to the database and secrets, can revalidate cached paths or tags, and can redirect. Because it is an endpoint, it must validate its arguments with a schema, check authentication and authorization inside the function, and never trust ids passed from the client to mean "this user owns the record".

**Deeper explanation:**

```ts
"use server";
const schema = z.object({ title: z.string().min(1).max(200) });

export async function createTodo(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const session = await auth();
  if (!session) return { error: "Not signed in" };
  const parsed = schema.safeParse({ title: formData.get("title") });
  if (!parsed.success) return { error: parsed.error.issues[0].message };
  await db.todo.create({ data: { ...parsed.data, userId: session.user.id } });
  revalidateTag("todos");
  return { error: null };
}

// client component
const [state, formAction, pending] = useActionState(createTodo, { error: null });
<form action={formAction}><input name="title" /><button disabled={pending}>Add</button></form>
```

`useActionState` gives you the last returned state and a pending flag; `useFormStatus` inside the form gives child components the pending state. Forms work before hydration (progressive enhancement) because the browser can submit them natively. For non-form calls from a client component you import the action and call it inside `startTransition`. Return serializable values and keep errors as data, not thrown exceptions, because thrown errors become generic 500s to the client.

Security points interviewers want: treat each action as a public API; use the framework's action ids rather than exposing your own routing; verify ownership in the query (`where: { id, userId }`), not after fetching; and rate-limit actions that send mail or call paid APIs.

**Follow-ups they will ask:**
- Server actions or route handlers: actions for mutations driven by your own UI; route handlers for public APIs, webhooks, and anything other clients call.
- How do you show optimistic UI with an action: `useOptimistic` holds the expected state until the action settles.
- Can actions be called in parallel: calls from one client are serialized by default; design them as independent units anyway.

**Mistakes to avoid:**
- Passing a `userId` from the client to the action and trusting it.
- Doing long-running work (minutes) inside an action; hand it to a queue and return a job id.

### Q. What causes hydration errors, and how do you fix them properly?
**Short answer (45 seconds):** Hydration requires the client's first render to produce the same tree as the server's HTML. Anything that differs breaks it: `Date.now()` or `Math.random()` in render, formatting dates in the user's time zone when the server used UTC, branching on `typeof window`, reading `localStorage` for a theme, invalid HTML nesting that the browser corrects (a `div` inside a `p`), and browser extensions that inject markup. The fix is to make the first render deterministic and move client-only values into a second render via an effect or `useSyncExternalStore` with a server snapshot.

**Deeper explanation:** React 18 recovers from a mismatch by discarding the server HTML up to the nearest Suspense boundary and rendering it on the client, so the page works but you lose the benefit and get a console error; React 19 prints a diff of the mismatch.

```ts
// Theme from localStorage: wrong on the server, so defer it
function useTheme() {
  return useSyncExternalStore(
    subscribeToStorage,
    () => (localStorage.getItem("theme") as Theme) ?? "light",
    () => "light"   // server snapshot: deterministic
  );
}

// Relative times: render a stable value first, upgrade on the client
<time dateTime={iso} suppressHydrationWarning>{formatInTimeZone(iso, "UTC")}</time>
```

Better than deferring a theme is reading it from a cookie in a server component so the right value is in the HTML with no flash. `suppressHydrationWarning` is for one text node that legitimately differs (a timestamp), not a blanket fix. Components that cannot run on the server (a map SDK touching `window` at import) load with `next/dynamic` and `ssr: false`, rendering nothing in the HTML.

Invalid nesting deserves a lint check: `p` cannot contain block elements, `a` cannot contain `a`; the browser rewrites such markup, so the DOM no longer matches React's tree.

**Follow-ups they will ask:**
- Why not check `typeof window` in render: the server and client branches differ, which is exactly a mismatch; use effects or external store hooks.
- How do extensions cause errors: they mutate the DOM before hydration; React 19 tolerates some of this, and the fix is to confirm in an incognito window.
- Does a mismatch affect server components: no, they do not hydrate; mismatches are a client component concern.

**Mistakes to avoid:**
- Spraying `suppressHydrationWarning` across a component tree.
- Wrapping half the app in `ssr: false` to make warnings disappear, which gives up server rendering entirely.

### Q. How does streaming SSR with Suspense work, and what does it change for users?
**Short answer (45 seconds):** Instead of waiting for every data source before sending any HTML, the server sends the page shell immediately with fallbacks in place of the slow parts, then streams each Suspense boundary's HTML as its data resolves, with a small inline script that swaps the fallback for the content. The browser starts painting and loading assets right away, and with selective hydration React hydrates the parts that are ready and prioritizes whichever part the user clicks. Users see the layout in the time of your fastest query rather than your slowest.

**Deeper explanation:**

```ts
export default function OrderPage({ params }: Props) {
  return (
    <>
      <OrderHeader id={params.id} />                     // fast, awaited first
      <Suspense fallback={<LineItemsSkeleton />}>
        <LineItems id={params.id} />                     // slow query, streams later
      </Suspense>
      <Suspense fallback={<RecommendationsSkeleton />}>
        <Recommendations id={params.id} />               // slowest, streams last
      </Suspense>
    </>
  );
}
```

A `loading.tsx` file in the App Router is a Suspense boundary for the whole route segment, the coarse version of this; the granular version above is better because the header and line items do not wait for recommendations. Under the hood this is `renderToPipeableStream`: the first chunk is the shell, later chunks arrive as hidden `template` elements plus a script that moves them into place.

Consequences to design around: status and headers go out with the first chunk, so a redirect or 404 must be decided before streaming starts (Next.js handles `redirect()` and `notFound()` inside boundaries with client-side fallbacks, but the status is already 200); errors inside a boundary after the shell is sent render the nearest error boundary, not a 500 page; and head content such as the title should come from metadata, not a slow component.

**Follow-ups they will ask:**
- What is selective hydration: hydrating Suspense boundaries independently and out of order, prioritizing the one the user interacts with.
- Does streaming help SEO: crawlers that execute the full response see the final content; the shell and metadata are in the first chunk either way.
- How does this relate to streamed LLM output: same transport idea (chunked HTTP), but model tokens are streamed to the client as data, not as server-rendered HTML.

**Mistakes to avoid:**
- One `loading.tsx` for the route and nothing else, so the whole page waits for the slowest query.
- Putting something that needs headers (authentication redirect) below a Suspense boundary.

### Q. Explain the caching layers in the Next.js App Router and how you control them when a page shows stale data.
**Short answer (45 seconds):** There are four. Request memoization dedupes identical `fetch` calls within one server render. The data cache persists fetch results across requests until revalidated by time or tag. The full route cache stores the HTML and RSC payload of static routes at build. The router cache in the browser holds RSC payloads of visited and prefetched routes. When a page is stale I ask which layer served it: a static route needs `revalidatePath` or a dynamic opt-out, a cached fetch needs `revalidateTag` or `cache: "no-store"`, and client staleness after a mutation needs `router.refresh()` or a server action.

**Deeper explanation:**

```ts
// Data cache: tag the fetch, revalidate on write
const res = await fetch(`${API}/products`, { next: { tags: ["products"], revalidate: 3600 } });

// In a server action after a mutation
revalidateTag("products");          // marks data cache entries stale
revalidatePath("/products");        // also purges the route cache for the path

// Make a route dynamic (bypasses the full route cache)
export const dynamic = "force-dynamic";
```

Defaults changed across versions, so "it depends on the version" is a legitimate answer: earlier App Router releases cached `fetch` by default and kept dynamic pages in the router cache briefly, while Next.js 15 made `fetch` and GET route handlers uncached by default and set router cache staleness for dynamic pages to zero. Newer releases move toward explicit opt-in caching with a `"use cache"` directive. Durable rule: know your version's defaults, prefer explicit `revalidate` and tags, and check the build output, which marks each route static or dynamic.

Anything that reads request-specific data (`cookies()`, `headers()`, `searchParams`, which are async in recent versions) makes the route dynamic, which disables the full route cache for it but not the data cache for its fetches.

**Follow-ups they will ask:**
- Why does navigating back show old data: the router cache; `router.refresh()`, a server action, or a `revalidatePath` call invalidates it.
- Can non-fetch data access (an ORM call) be cached: with `unstable_cache` or the newer `"use cache"` directive, with tags and revalidation like fetch.
- How do you debug which layer served a response: check the build output for the route type, add logging in the data function to see whether it runs, and inspect the `x-nextjs-cache` header where present.

**Mistakes to avoid:**
- Blaming the CDN when the stale data comes from the client router cache.
- Marking everything `force-dynamic` as a fix, which throws away all static benefits.

### Q. Edge runtime versus Node runtime: how do you decide where a route runs?
**Short answer (45 seconds):** The Edge runtime runs on lightweight V8 isolates close to users, starts almost instantly, and supports a Web API subset: `fetch`, `Request`, `Response`, Web Crypto, streams. It lacks Node built-ins such as `fs` and raw TCP sockets, so traditional database drivers do not work there. The Node runtime has everything Node has, with heavier cold starts in serverless deployments. I pick Edge for logic that needs no database: auth cookie checks, redirects, geolocation, A/B assignment, header rewriting. I pick Node for anything that talks to a database over TCP, uses Node-only libraries, or is CPU-heavy.

**Deeper explanation:** The trap is latency geometry: edge compute is only faster if the data is also nearby. A route at the edge in Mumbai calling Postgres in Virginia crosses the ocean on every query, so a page with three sequential queries ends up slower than the same page rendered next to the database. Edge suits routes that touch a globally distributed cache or no data; Node near the database suits data-heavy pages.

```ts
export const runtime = "edge";          // per route segment or route handler
export const preferredRegion = "bom1";  // keep compute near the data when supported by the host
```

Edge-compatible data access exists (HTTP drivers such as Neon serverless or Upstash Redis, proxies such as Prisma Accelerate), but the distance to the primary database still applies. Check library compatibility too: anything depending on Node's `crypto` or native addons fails at build time for Edge. Streaming works in both. Next.js middleware has historically run on the Edge runtime, which is why it is limited to header and cookie logic with lightweight fetches.

**Follow-ups they will ask:**
- Is Edge cheaper: often priced per request and CPU time with no idle, but extra network hops can offset it; measure.
- Can you use Edge for an LLM streaming proxy: yes, a good fit: `fetch` the model API and stream the response through, no database involved.
- How do you handle a library that needs Node only on one route: set `runtime = "nodejs"` on that segment and keep the others on Edge.

**Mistakes to avoid:**
- Saying "edge is always faster".
- Choosing Edge for a page that runs several queries against a single-region database.

### Q. How do you handle SEO and metadata in Next.js, and when is Next.js the wrong tool?
**Short answer (45 seconds):** Metadata is defined per route with a static `metadata` export or an async `generateMetadata` that can fetch data, and Next.js merges it down the layout tree: title templates, descriptions, canonical URLs, Open Graph and Twitter cards, alternates for languages. `sitemap.ts` and `robots.ts` generate those files, and `opengraph-image.tsx` renders social preview images on the server. Combined with server rendering, crawlers and link unfurlers receive real content. Next.js is the wrong tool when none of this matters: a fully authenticated SPA, a static content site that Astro or a static generator serves with less machinery, or a product whose backend is a long-lived stateful server rather than request-response functions.

**Deeper explanation:**

```ts
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const product = await getProduct(params.slug);
  return {
    title: product.name,                              // layout template: "%s | Shop"
    description: product.summary,
    alternates: { canonical: `https://shop.example/p/${product.slug}` },
    openGraph: { images: [`/p/${product.slug}/opengraph-image`] },
  };
}
```

Structured data (JSON-LD) is a `script` tag of type `application/ld+json` rendered in the page component, kept in sync with visible content. Canonicals matter when URL state produces many variants of one page; filtered or paginated URLs should be canonicalized or excluded in robots rules.

When to say no to Next.js: an internal tool behind SSO with no SEO need gets simpler builds, cheaper static hosting, and fewer caching surprises as a Vite SPA with a separate API. A docs or marketing site with little interactivity is often better served by Astro or a static generator that ships near-zero JavaScript. A product built around persistent WebSocket sessions needs a long-running server, so keep that service separate and let Next.js be the front door only.

**Follow-ups they will ask:**
- How do you test metadata: fetch the route with curl and inspect the head; use the social platforms' debuggers for OG previews.
- Can metadata be set from client components: no, it must come from the server-side exports.
- Does Next.js lock you into Vercel: it runs on any Node host or in Docker with `output: "standalone"`; some caching and image features need configuration elsewhere.

**Mistakes to avoid:**
- Setting `document.title` in an effect and expecting crawlers to see it.
- Choosing Next.js for an authenticated SPA "because it is standard" and then fighting server rendering on every page.

### Practice
- Build one small Next.js app with four routes, one per strategy (static, ISR with on-demand revalidation via a route handler, dynamic SSR, and a client-only page); read the build output and explain each route's marker.
- Create a page with three data sources of different speeds; first with a single `loading.tsx`, then with nested Suspense boundaries; measure TTFB and time to full content with the Network panel.
- Write a server action that creates a record, tag the fetch that lists records, and prove that `revalidateTag` updates the list while a page without the tag stays stale; then fix the stale page.
- Introduce a hydration error on purpose with a time-zone formatted date, read the React 19 diff, and fix it with a server snapshot.
- Say it out loud: explain to a backend engineer the difference between SSR and React Server Components in two minutes, including what ships to the browser in each case.

## TypeScript for React

> TypeScript questions in a React interview are rarely about syntax. They test whether you use the type system to make invalid UI states impossible, whether you can write a generic component without `any`, and whether types at the network boundary are checked at runtime or merely asserted. Weak answers reach for `as` and `!`. Strong answers model the domain with unions, infer types from schemas, and know which compiler flags change what the types promise.

### Concepts you must understand
- Type props as a plain `type` or `interface`, type `children` as `React.ReactNode`, and extend native element props with `React.ComponentPropsWithoutRef<"button">` so wrappers accept everything the element accepts.
- Event types are generic over the element: `React.ChangeEvent<HTMLInputElement>`, `React.MouseEvent<HTMLButtonElement>`, `React.FormEvent<HTMLFormElement>`; handler aliases such as `React.ChangeEventHandler<HTMLInputElement>` save typing.
- Generic components (`function Table<T>(props: TableProps<T>)`) infer `T` from the data prop and let column definitions reference `keyof T`; arrow functions in `.tsx` need `<T,>` to disambiguate from JSX.
- Discriminated unions with a literal `kind` or `status` field make impossible states unrepresentable for both state and props, and an exhaustive `switch` with a `never` check turns a missed case into a compile error.
- `satisfies` validates a value against a type while keeping the narrower inferred type, which annotations widen and `as` silently overrides.
- `Omit` and `Pick` do not distribute over unions; a union with a discriminant loses it under `Omit`, so you need a distributive helper or you pick per member.
- `strict` is the baseline; `noUncheckedIndexedAccess` makes array and record indexing return `T | undefined`, which catches a whole class of runtime crashes in list code.
- Types vanish at runtime: anything from the network must be parsed with a schema (zod) at the boundary, and the TypeScript type is inferred from that schema so the two cannot drift.
- `createContext<T | null>(null)` plus a hook that throws when the provider is missing is the pattern that avoids non-null assertions at every consumer.

### Q. How do you type component props, children, and event handlers idiomatically?
**Short answer (45 seconds):** Declare a props type and annotate the function parameter; avoid `React.FC` because it adds little and no longer implies `children`. Type `children` as `React.ReactNode`, which covers elements, strings, arrays, and `null`. For components that wrap a native element, extend `React.ComponentPropsWithoutRef<"button">` and spread the rest so consumers get every native attribute. Type events by the element that fires them: `React.ChangeEvent<HTMLInputElement>` for inputs, `React.MouseEvent<HTMLButtonElement>` for buttons, and let inline handlers infer from the JSX.

**Deeper explanation:**

```ts
type TextFieldProps = Omit<React.ComponentPropsWithoutRef<"input">, "onChange" | "value"> & {
  label: string;
  value: string;
  onChange: (value: string) => void;        // domain-level handler, not the raw event
  hint?: React.ReactNode;
};

export function TextField({ label, value, onChange, hint, id, ...rest }: TextFieldProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  return (
    <div>
      <label htmlFor={inputId}>{label}</label>
      <input id={inputId} value={value}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value)} {...rest} />
      {hint && <p id={`${inputId}-hint`}>{hint}</p>}
    </div>
  );
}
```

Omitting the native `onChange` and `value` before redefining them avoids a type conflict and documents the component's opinion: consumers get the value, not the event. Use `React.ComponentProps<typeof Button>` to derive props from another component instead of exporting every props type. For `ref`, React 19 lets function components accept `ref` as a normal prop typed `React.Ref<HTMLInputElement>`; before that, `forwardRef<HTMLInputElement, Props>` was required. Render-prop and callback props are typed as function types, and `children` as a function (`(state: S) => React.ReactNode`) when the component controls rendering.

**Follow-ups they will ask:**
- `interface` or `type` for props: either; `type` handles unions and intersections more naturally, `interface` gives slightly better error messages for extension; pick one per codebase.
- Why not `JSX.Element` for children: it excludes strings, arrays, and `null`; `ReactNode` is what React accepts.
- How do you type a polymorphic `as` prop: with a generic over `React.ElementType` and `React.ComponentPropsWithoutRef<T>`; it gets complex quickly, so lean on a library implementation.

**Mistakes to avoid:**
- Typing every handler as `(e: any) => void` or `Function`.
- `React.FC<Props>` with implicit children assumptions from older type definitions.

### Q. How do you write a generic component such as a typed data table, and what pitfalls appear?
**Short answer (45 seconds):** Make the component a generic function over the row type: `function Table<T>({ rows, columns }: TableProps<T>)`, where columns reference `keyof T` and render functions receive `T`. TypeScript infers `T` from the `rows` argument at the call site, so consumers get autocomplete on column keys and type errors on typos. The pitfalls: arrow components in `.tsx` need the `<T,>` syntax, `memo` and `forwardRef` erase generics unless you re-cast, and constraints such as `T extends { id: string }` are needed for keys.

**Deeper explanation:**

```ts
type Column<T> = { key: keyof T & string; header: string; render?: (row: T) => React.ReactNode };
type TableProps<T extends { id: string }> = {
  rows: T[];
  columns: Column<T>[];
  onRowClick?: (row: T) => void;
};

export function Table<T extends { id: string }>({ rows, columns, onRowClick }: TableProps<T>) {
  return (
    <table>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id} onClick={() => onRowClick?.(row)}>
            {columns.map((c) => <td key={c.key}>{c.render ? c.render(row) : String(row[c.key])}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

<Table rows={users} columns={[{ key: "email", header: "Email" }]} />   // key must be a User field
```

`React.memo(Table)` returns a non-generic component type, so the usual workaround is `memo(Table) as typeof Table`. Generic hooks follow the same idea: `function useLocalStorage<T>(key: string, initial: T): [T, (v: T) => void]`, with `as const` on the returned tuple so callers get a tuple rather than an array of a union. Default type parameters (`<T = unknown>`) keep call sites clean when inference has nothing to work with. When the generic gets hard to read, a discriminated union of concrete column types often expresses the intent more clearly than deeper generics.

**Follow-ups they will ask:**
- Why `keyof T & string`: `keyof` includes `number` and `symbol`; intersecting with `string` keeps keys usable as React keys and object paths.
- How do you type a `Select<T>` with `value: T` and `options: T[]`: the same generic pattern, plus a `getLabel: (o: T) => string` function instead of assuming a `label` field.
- Can TypeScript infer `T` from `columns` alone: yes if `rows` is absent, but inference prefers the simplest source; pass `rows` first.

**Mistakes to avoid:**
- `rows: any[]` with `columns: { key: string }[]`, which gives up the whole point.
- Trying to make one generic handle every table variant instead of composing simpler components.

### Q. How do discriminated unions improve state and props modelling in React?
**Short answer (45 seconds):** A discriminated union is a set of object types that share a literal tag such as `status` or `kind`. Narrowing on the tag gives you exactly the fields valid for that case, so a `success` state has `data` and no `error`, and a `link` button has `href` while a `button` variant has `onClick`. This removes optional fields that are "sometimes required", deletes defensive checks, and lets an exhaustive `switch` fail compilation when a new case is added but not handled.

**Deeper explanation:**

```ts
type Request<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error };

function assertNever(x: never): never { throw new Error(`Unhandled: ${JSON.stringify(x)}`); }

function View({ req }: { req: Request<User[]> }) {
  switch (req.status) {
    case "idle": return null;
    case "loading": return <Spinner />;
    case "success": return <UserList users={req.data} />;   // data is defined here
    case "error": return <ErrorPanel error={req.error} />;
    default: return assertNever(req);                        // compile error if a case is missing
  }
}

type ActionProps =
  | { kind: "link"; href: string; external?: boolean }
  | { kind: "button"; onClick: () => void; type?: "button" | "submit" };
```

Compare with `{ data?: T; error?: Error; loading: boolean }`: nothing stops `loading: true` with `error` set, every consumer checks `data` for undefined even after `loading` is false, and adding a `cancelled` state is invisible to the compiler. With unions, the reducer's return type documents every reachable state and TanStack Query exposes exactly this shape through `status` and the `isSuccess`/`isError` narrowing guards.

**Follow-ups they will ask:**
- How does `Omit` interact with unions: it collapses them to the shared properties and loses the discriminant; use a distributive `type DistributiveOmit<T, K extends keyof any> = T extends unknown ? Omit<T, K> : never`.
- When is a union overkill: two optional fields that are genuinely independent; unions model mutually exclusive cases.
- How do you share the tag type with the backend: generate it from a zod schema with `z.discriminatedUnion("status", [...])` or from the OpenAPI spec.

**Mistakes to avoid:**
- Boolean flag soup (`isLoading`, `isError`, `hasData`) that can represent impossible combinations.
- Skipping the `never` default, which makes the exhaustive check silent.

### Q. Which TypeScript utility types do you use most in React code, and where do they bite?
**Short answer (45 seconds):** `Pick` and `Omit` to derive a component's props from another's or from a native element; `Partial` for update payloads and `Required` for post-validation data; `Record<K, V>` for lookup maps keyed by a union; `ReturnType` and `Parameters` to type around functions I do not own; `Awaited<ReturnType<typeof fetchUser>>` to name an async result; `Extract` and `Exclude` to slice a union; `NonNullable` after filtering; and `React.ComponentProps<typeof X>` to borrow another component's props. The places they bite are `Omit` on unions, `Partial` hiding missing required data, and `Record<string, T>` indexing that lies without `noUncheckedIndexedAccess`.

**Deeper explanation:**

```ts
type Status = "draft" | "published" | "archived";
const labels: Record<Status, string> = { draft: "Draft", published: "Live", archived: "Archived" };
// Adding a Status member without a label is now a compile error

type UserResponse = Awaited<ReturnType<typeof api.users.get>>;      // follow the function, no duplicate type
type EditableUser = Pick<UserResponse, "name" | "email">;             // the form's fields
type ButtonVariant = React.ComponentProps<typeof Button>["variant"];  // derive, do not re-declare
type ActiveStatus = Exclude<Status, "archived">;
```

Template literal types combine with these for design tokens (`` `${Size}-${Weight}` ``) and event names. `as const` on arrays of options gives you literal element types to derive unions from (`(typeof OPTIONS)[number]`), which keeps the runtime list and the type in one place. Mapped types with `keyof` generate form error shapes from the form value type (`Partial<Record<keyof FormValues, string>>`).

Where to stop: deeply conditional types for component props slow the compiler and produce unreadable errors. If a type needs a comment to explain what it computes, a plainer union or a second component is usually better. For library-level code (a design system) complex types are justified; for product code, readability wins.

**Follow-ups they will ask:**
- Why derive types from functions rather than declare them: one source of truth; when the API client changes, every consumer updates or fails to compile.
- `Record<string, T>` or `Map`: `Record` for static key sets and JSON data; `Map` for dynamic keys, non-string keys, and frequent insert and delete.
- What does `Partial` hide: that a value may be incomplete; use it for patch payloads, not for state you render.

**Mistakes to avoid:**
- Re-declaring response types by hand next to the fetch function and letting them drift.
- `Omit<UnionType, "k">` and wondering where the discriminant went.

### Q. What does `satisfies` do that `as` and type annotations do not?
**Short answer (45 seconds):** `satisfies` checks that a value conforms to a type without changing the value's inferred type. An annotation (`const x: T = ...`) widens the value to `T`, so you lose literal keys and narrower types. A cast (`as T`) does not check at all beyond basic overlap; it tells the compiler to trust you, and it is how wrong types enter a codebase. `satisfies` gives you the check and keeps the precise inferred type, which is exactly what config objects, route tables, and theme tokens need.

**Deeper explanation:**

```ts
type Route = { path: string; component: React.ComponentType; auth?: boolean };

const routes = {
  home: { path: "/", component: Home },
  settings: { path: "/settings", component: Settings, auth: true },
} satisfies Record<string, Route>;

routes.settings.auth;          // boolean: still known
routes.billing;                // compile error: key does not exist (an annotation would allow it)

const palette = {
  primary: "#2563eb",
  surface: "#ffffff",
} satisfies Record<string, `#${string}`>;   // every value must be a hex string; keys stay literal
```

With `const routes: Record<string, Route>` the type of `routes.billing` would be `Route`, not an error, and `routes.settings.auth` would be `boolean | undefined`. With `as Record<string, Route>` a typo in a property would compile. `satisfies` is also the clean way to validate an object against a discriminated union while keeping the specific member for later use, and to check that an exhaustive map covers a union (`satisfies Record<Status, ...>`) without widening the values.

In React code the practical uses are route and navigation configs, design tokens, feature flag registries, i18n message maps, and column definitions where you want the compiler to check the shape but keep autocompletion on the keys.

**Follow-ups they will ask:**
- When is `as` legitimate: narrowing a `unknown` after a runtime check you performed, `as const`, and interop with badly typed libraries, each with a comment.
- Does `satisfies` exist at runtime: no, like all types it is erased; it is a compile-time check only.
- Version requirement: TypeScript 4.9 introduced it.

**Mistakes to avoid:**
- Using `as` to silence errors in props objects; it hides the mismatch until runtime.
- Annotating config objects and then sprinkling non-null assertions when the widened type loses information.

### Q. Which TypeScript strictness settings matter most, and what do they catch in React code?
**Short answer (45 seconds):** `strict: true` is non-negotiable; it turns on `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, and `useUnknownInCatchVariables`, which together catch most null and shape errors. On top of that I enable `noUncheckedIndexedAccess`, because `items[0]` and `map[key]` returning `T | undefined` is what prevents "cannot read properties of undefined" in list and lookup code. `exactOptionalPropertyTypes` distinguishes "missing" from "explicitly undefined", which matters for props spread into components with defaults. `verbatimModuleSyntax` and `isolatedModules` keep imports compatible with esbuild and SWC, which transpile file by file.

**Deeper explanation:**

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "skipLibCheck": true
  }
}
```

`noUncheckedIndexedAccess` is the one that changes daily code: `const first = rows[0]` becomes `Row | undefined`, so you write `rows.at(0)` with a guard or `rows[0]?.name`. Teams adopting it on an existing codebase get many errors; migrate directory by directory using a second tsconfig or a lint rule. `useUnknownInCatchVariables` makes `catch (e)` give `unknown`, so error handling checks `e instanceof ApiError` instead of reading `e.message` blindly.

Pair the compiler with typescript-eslint's type-aware rules: `no-floating-promises` catches un-awaited async calls in handlers, `switch-exhaustiveness-check` enforces the `never` pattern, `no-explicit-any` and `no-unsafe-*` keep `any` out, and `consistent-type-imports` complements `verbatimModuleSyntax`. In CI, run `tsc --noEmit` separately from the bundler, because Vite and Next.js builds transpile without type checking.

**Follow-ups they will ask:**
- Why `skipLibCheck`: it skips checking `.d.ts` files of dependencies, which speeds builds and avoids failures from third-party type conflicts; your own code is still checked.
- What does `strictFunctionTypes` do for props: it checks callback parameters contravariantly, so a handler typed for a subtype cannot be passed where a supertype handler is expected.
- How do you handle a legacy codebase with hundreds of errors: enable flags incrementally, use `// @ts-expect-error` with a reason rather than `@ts-ignore`, and track the count.

**Mistakes to avoid:**
- Treating a successful `next build` as proof of type safety; it does not type check in all configurations.
- Turning off `strictNullChecks` to make a migration easier and never turning it back on.

### Q. How do you type API responses safely, and how do you keep frontend types in sync with the backend?
**Short answer (45 seconds):** Types do not exist at runtime, so a response typed as `User` is a promise the compiler cannot keep. I define a zod schema for each response at the HTTP boundary, parse with `safeParse`, and infer the TypeScript type from the schema with `z.infer`, so the type and the validation can never disagree. Failures are logged with the path that mismatched and handled as errors, not as silent `undefined`s deep in a component. For sync with the backend, the schema is generated from the OpenAPI spec or shared from a package in the monorepo, or the whole contract is end-to-end typed with tRPC.

**Deeper explanation:**

```ts
const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(["admin", "member"]),
  createdAt: z.string().datetime().transform((s) => new Date(s)),
  plan: z.object({ name: z.string(), seats: z.number().int() }).nullable(),
});
export type User = z.infer<typeof UserSchema>;     // Date for createdAt, after transform

export async function getUser(id: string, signal?: AbortSignal): Promise<User> {
  const json = await http<unknown>(`/users/${id}`, { signal });
  const parsed = UserSchema.safeParse(json);
  if (!parsed.success) {
    report("schema_mismatch", { path: "/users/:id", issues: parsed.error.issues });
    throw new ApiError(502, "bad_response", "Unexpected response shape");
  }
  return parsed.data;
}
```

Parsing at the boundary is also where you normalize: coerce numeric strings, convert ISO strings to `Date`, default optional fields, and strip unknown keys so the rest of the app sees one clean shape. Be deliberate about strictness: `z.object` strips unknown keys by default, which tolerates additive backend changes; `.strict()` fails on them, which is right for security-sensitive payloads.

Keeping in sync: `openapi-typescript` generates types from the spec, and tools such as `orval` or `openapi-zod-client` generate zod schemas and typed clients; a shared `packages/contracts` in a monorepo lets the Node backend validate requests with the same schemas the frontend uses for responses; tRPC gives inferred end-to-end types when frontend and backend are TypeScript in one repo. Whichever you pick, run contract validation in CI so a backend change breaks the build, not production.

**Follow-ups they will ask:**
- Is parsing every response slow: it is microseconds for typical payloads; for very large lists parse a sample or validate on the server and trust the contract tests.
- zod or a type-only approach: type-only is fine for internal APIs with generated types and contract tests; zod when you need runtime guarantees or transforms.
- How do you type form input versus API output: two schemas or `z.input` and `z.output` of one schema with transforms.

**Mistakes to avoid:**
- `const data = (await res.json()) as User`, which is a cast with no checking.
- Hand-maintaining response interfaces that silently drift from the backend.

### Practice
- Write a generic `Table<T>` with typed columns and a `memo` wrapper that keeps the generic; verify that a misspelled column key is a compile error.
- Convert a component with `isLoading`, `isError`, and optional `data` props into a discriminated union and add an exhaustive switch; add a new state and watch the compiler find every switch.
- Enable `noUncheckedIndexedAccess` on a small project, fix the errors, and note which ones were real bugs.
- Add zod parsing to an existing API client, point it at a mocked server that returns a wrong field type, and verify the error surfaces at the boundary with a clear path.
- Say it out loud: explain to a reviewer why `satisfies` is the right tool for a route config and what you would lose with an annotation or a cast.

## Testing & Quality

> Testing questions check whether you know what to test and at which layer, not whether you can spell `expect`. Weak answers chase coverage numbers and snapshot everything. Strong answers test behaviour through the user's interface, mock at the network boundary rather than inside the app, put the expensive confidence in a few end-to-end flows, and treat a flaky test as a bug with a root cause. Be ready to describe the test pyramid you would set up on day one of a new React codebase.

### Concepts you must understand
- Testing Library's principle: tests should resemble how users interact with the app, so you find elements by role, label, and text, interact with `userEvent`, and assert on what the user sees, never on component internals or state.
- Query priority: `getByRole` first, then `getByLabelText` and `getByText`; `getByTestId` is the last resort. `findBy*` awaits appearance; `queryBy*` asserts absence.
- Vitest runs on the Vite pipeline with a Jest-compatible API and a jsdom or happy-dom environment; Jest remains common in Next.js projects through `next/jest`. The assertions and Testing Library code are the same.
- MSW intercepts requests at the network layer in Node and in the browser, so the real HTTP layer runs in tests and the same handlers serve unit tests, Storybook, and local development.
- `renderHook` tests a hook through a tiny host component; wrap it with the providers it needs and drive it with `act`.
- Unit and integration tests in jsdom cover components and flows cheaply; Playwright covers the few critical paths in a real browser with auto-waiting locators, traces, and cross-browser runs.
- Automated accessibility checks (axe) catch structural issues such as missing labels and contrast; keyboard, focus order, and screen reader experience need a manual pass.
- Flaky tests come from un-awaited async work, shared mutable state between tests, real time and real network, and animations; the fix is determinism, not retries.
- Type checking, lint with type-aware rules, and a bundle size check belong in the same CI stage as tests; they catch different classes of bugs.

### Q. What is the React Testing Library philosophy, and how does it change what you assert?
**Short answer (45 seconds):** Test the component the way a user or a screen reader experiences it. You render it, find elements by their accessible role and name, interact with `userEvent` the way a person would, and assert on the visible outcome. You never reach into state, call instance methods, or assert on class names, because those are implementation details that change in a refactor while behaviour stays the same. The payoff is tests that survive refactors and fail when the user experience breaks, plus an accessibility check for free, since inaccessible elements are hard to query.

**Deeper explanation:**

```ts
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

test("adds a todo and clears the input", async () => {
  const user = userEvent.setup();
  render(<TodoForm onAdd={vi.fn()} />);

  const input = screen.getByRole("textbox", { name: /new todo/i });
  await user.type(input, "Write tests");
  await user.click(screen.getByRole("button", { name: /add/i }));

  expect(await screen.findByText("Write tests")).toBeInTheDocument();
  expect(input).toHaveValue("");
});
```

`getByRole("button", { name: /add/i })` fails if the button has no accessible name, which is the accessibility check in disguise. `userEvent` dispatches the full sequence of events a real interaction produces (pointer, focus, keydown, input) where `fireEvent` fires one synthetic event, so `userEvent` catches bugs in handlers that depend on focus or keyboard order. `findBy*` returns a promise that resolves when the element appears, which replaces manual `waitFor` loops for most async UI.

What not to test at this layer: exact markup via snapshots (they fail on any change and nobody reads the diff), styling, and third-party library internals. Snapshot tests have a narrow place for serialized output such as generated markdown or a config object.

**Follow-ups they will ask:**
- When is `getByTestId` acceptable: when there is no semantic handle, such as a decorative container you need to scope queries within, and it should prompt a question about the markup.
- How do you test a component that reads context: render it inside the real provider with test values, or a small `renderWithProviders` helper.
- Why `screen` rather than destructuring from `render`: one consistent query surface and better error messages listing the current DOM.

**Mistakes to avoid:**
- Asserting on state or props through hooks or wrapper instances.
- Snapshotting whole components and approving diffs without reading them.

### Q. How do you set up a fast unit test suite for a React application, and Vitest or Jest?
**Short answer (45 seconds):** For a Vite app I use Vitest: it reuses the Vite config and transforms, understands ESM and TypeScript natively, runs tests in parallel workers, and offers a Jest-compatible API, so Testing Library and `jest-dom` matchers work unchanged. For a Next.js app Jest with `next/jest` is still the path of least resistance, although Vitest works with a small config. The speed levers are the same either way: a light DOM environment (happy-dom or jsdom), no real network, fake timers where time matters, and running only affected tests in watch mode.

**Deeper explanation:**

```ts
// vitest.config.ts
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],   // jest-dom matchers, MSW server lifecycle, cleanup
    css: false,
    coverage: { provider: "v8", reporter: ["text", "lcov"] },
  },
});

// src/test/setup.ts
import "@testing-library/jest-dom/vitest";
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

`onUnhandledRequest: "error"` makes any un-mocked request fail loudly, which is how you discover a component quietly fetching in a test. `vi.mock` replaces modules when you must (analytics, a heavy chart), but prefer dependency injection through props or context so the mock is explicit. Fake timers (`vi.useFakeTimers()` and `vi.setSystemTime()`) make debounce and relative-time tests deterministic; remember `userEvent.setup({ advanceTimers: vi.advanceTimersByTime })` so typing still works with fake timers.

Coverage is a diagnostic, not a goal: look for untested branches in business logic, not a percentage. Typical CI split: type check, lint, unit and integration tests, then Playwright on the built app.

**Follow-ups they will ask:**
- Why not test in a real browser for everything: speed; jsdom tests run in milliseconds, browser tests in seconds; Vitest's browser mode exists for component tests that need real layout.
- How do you keep tests fast as the suite grows: shard across CI workers, run only affected files in pre-commit, and avoid rendering the whole app for a unit test.
- What about Jest's ESM problems: they come from transforming `node_modules`; `transformIgnorePatterns` or moving to Vitest fixes them.

**Mistakes to avoid:**
- Mocking `fetch` globally in setup so every test passes with fake data and nobody notices real request bugs.
- Chasing 100 percent coverage on presentational components while business logic hooks go untested.

### Q. How do you mock the network in frontend tests, and why MSW rather than mocking fetch or axios?
**Short answer (45 seconds):** Mock Service Worker intercepts requests at the network boundary: in Node tests through request interception, in the browser through a service worker. The application code runs unchanged, including the HTTP layer, interceptors, retries, and error mapping, and the test only decides what the server returns. Mocking `fetch` or `axios` tests a fake, couples tests to the transport library, and skips the code that most often has bugs: status handling, parsing, and auth refresh. The same MSW handlers also power Storybook stories and a mock mode for local development, so one set of fixtures serves three uses.

**Deeper explanation:**

```ts
// src/test/handlers.ts (MSW 2 API)
export const handlers = [
  http.get("/api/todos", () => HttpResponse.json([{ id: "1", title: "Write tests", done: false }])),
  http.post("/api/todos", async ({ request }) => {
    const body = (await request.json()) as { title: string };
    return HttpResponse.json({ id: "2", ...body, done: false }, { status: 201 });
  }),
];

// in a test: override for one scenario
server.use(http.get("/api/todos", () => HttpResponse.json({ message: "boom" }, { status: 500 })));
render(<Todos />);
expect(await screen.findByRole("alert")).toHaveTextContent(/could not load/i);
```

Because `server.resetHandlers()` runs after each test, per-test overrides do not leak. Handlers can simulate latency with `delay()`, network errors with `HttpResponse.error()`, and streaming responses with a `ReadableStream` body, which is how you test an SSE or token-streaming UI without a model API. For TanStack Query tests, create a fresh `QueryClient` per test with `retry: false` so error paths do not wait for retries.

Playwright can reuse the same handlers through `page.route` or by running the app in mock mode with the service worker, which keeps e2e fixtures consistent with unit fixtures. The one thing MSW does not test is the real backend contract; that is what schema validation at the boundary and contract tests cover.

**Follow-ups they will ask:**
- How do you assert that a request was made with the right body: capture it in the handler and assert on the captured value; avoid asserting on `fetch` call counts.
- How do you mock GraphQL: MSW has `graphql.query` and `graphql.mutation` handlers matching by operation name.
- What about WebSockets: recent MSW versions add WebSocket interception; otherwise inject a fake socket through a provider.

**Mistakes to avoid:**
- `vi.spyOn(global, "fetch")` returning hand-built objects that do not behave like `Response`.
- Forgetting `onUnhandledRequest: "error"`, so unmocked requests fail silently and tests pass by accident.

### Q. How do you test a custom hook?
**Short answer (45 seconds):** With `renderHook` from Testing Library, which mounts the hook inside a minimal component and exposes `result.current`, `rerender` for new arguments, and `unmount` for cleanup checks. State changes are wrapped in `act`, and async hooks are awaited with `waitFor`. Hooks that need providers get a `wrapper` option. For hooks that subscribe to something, the tests that matter are: it reflects the source, it re-subscribes when inputs change, and it unsubscribes on unmount. If a hook is mostly rendering logic, test the component that uses it instead.

**Deeper explanation:**

```ts
test("useDebouncedValue trails the input", () => {
  vi.useFakeTimers();
  const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 300), {
    initialProps: { v: "a" },
  });
  rerender({ v: "ab" });
  expect(result.current).toBe("a");                 // not yet
  act(() => { vi.advanceTimersByTime(300); });
  expect(result.current).toBe("ab");
  vi.useRealTimers();
});

test("useTodos loads from the API", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: React.ReactNode }) =>
    <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  const { result } = renderHook(() => useTodos(), { wrapper });
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data).toHaveLength(1);
});
```

For subscription hooks, assert cleanup explicitly: spy on `removeEventListener` or on a fake store's `unsubscribe`, call `unmount()`, and check it was called. Test StrictMode behaviour by rendering with `reactStrictMode: true` in the render options (supported in recent Testing Library versions) or by wrapping in `StrictMode` yourself, which flushes out missing cleanups. Reducers inside hooks are best tested directly as pure functions.

**Follow-ups they will ask:**
- Why `act`: it flushes React's updates and effects so assertions see the committed state; Testing Library wraps its own helpers in it.
- How do you test a hook that uses `useSyncExternalStore`: drive the external store directly and assert `result.current` follows, no `act` needed for the store mutation itself beyond the notify.
- Hooks or components, which do you test: components by default; hooks directly when they hold real logic reused across components.

**Mistakes to avoid:**
- Testing a hook's internal state shape instead of what consumers observe.
- Forgetting `retry: false` in test query clients and waiting through exponential backoff.

### Q. Where do you draw the line between unit, integration, and end-to-end tests in a React codebase?
**Short answer (45 seconds):** Pure logic (reducers, formatters, schema parsing) gets unit tests with no DOM. Components and feature flows get integration tests in jsdom with Testing Library and MSW: render the feature, drive it like a user, assert outcomes. A small set of business-critical journeys, sign in, checkout, the core workflow, get Playwright tests against the built app in a real browser. The ratio is many cheap jsdom tests, few expensive browser tests, because browser tests are slower, flakier, and harder to debug, but they are the only ones that catch bundling, routing, CSS, and real browser behaviour.

**Deeper explanation:**

```ts
// playwright: critical path, real browser, auto-waiting locators
test("user can create and complete a todo", async ({ page }) => {
  await page.goto("/todos");
  await page.getByRole("textbox", { name: /new todo/i }).fill("Ship it");
  await page.getByRole("button", { name: /add/i }).click();
  const row = page.getByRole("listitem").filter({ hasText: "Ship it" });
  await expect(row).toBeVisible();
  await row.getByRole("checkbox").check();
  await expect(row).toHaveAttribute("data-done", "true");
});
```

Playwright's locators auto-wait and retry assertions, which removes the `sleep` calls that made older e2e suites flaky. Use the same role-based locators as Testing Library so the two layers share vocabulary. Reuse authentication through `storageState` so each test does not log in through the UI. Run against a production build with a seeded database or MSW mock mode; decide deliberately, because a real backend tests the contract while mocks test the frontend alone. Record traces on failure and keep retries at one in CI as a signal, not a fix.

Visual regression (`toHaveScreenshot`, Chromatic for Storybook) covers the "did the layout break" class that functional tests miss, and belongs on design-system components more than on whole pages.

**Follow-ups they will ask:**
- How many e2e tests: enough to cover the flows whose failure would page someone, often ten to thirty, each under a minute.
- How do you keep e2e tests independent: each test creates its own data with unique identifiers and cleans up or runs against a fresh seed.
- How do you test across browsers: Playwright projects for Chromium, Firefox, and WebKit, with the full matrix nightly and Chromium on every pull request.

**Mistakes to avoid:**
- Hundreds of e2e tests covering what jsdom tests cover faster.
- e2e tests that depend on a shared staging database and each other's data.

### Q. How do you test accessibility automatically, and what can automation not catch?
**Short answer (45 seconds):** Three automated layers: `eslint-plugin-jsx-a11y` catches static mistakes in JSX such as images without alt text or click handlers on divs; axe-core via `vitest-axe` or `jest-axe` runs the rules engine against rendered components in unit tests; and `@axe-core/playwright` scans whole pages in e2e. Together they catch missing labels, bad contrast, invalid ARIA, and duplicate ids. They cannot judge whether the focus order makes sense, whether a screen reader announcement is understandable, whether a custom widget's keyboard model matches expectations, or whether an alt text is meaningful. Those need a keyboard-only pass and a screen reader session.

**Deeper explanation:**

```ts
// unit level
import { axe } from "vitest-axe";
test("dialog has no detectable a11y violations", async () => {
  const { container } = render(<ConfirmDialog open title="Delete item?" />);
  expect(await axe(container)).toHaveNoViolations();
});

// page level
test("todos page is accessible", async ({ page }) => {
  await page.goto("/todos");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(results.violations).toEqual([]);
});
```

Testing Library adds behavioural accessibility checks almost for free: role-based queries fail when roles or names are missing, `user.tab()` lets you assert focus order, `user.keyboard("{Escape}")` tests dismissal, and `toHaveFocus()` asserts focus management after a dialog opens or closes. Storybook's a11y addon runs axe per story during development so issues appear before review.

The manual checklist to mention: navigate the feature with keyboard only and confirm nothing is unreachable or trapped; use VoiceOver or NVDA through the main flow and listen for unlabelled controls and missing live announcements; zoom to 200 percent and check nothing is clipped; enable reduced motion and confirm animations respect it; test with a high-contrast mode. Automation finds a minority of real-world issues; the manual pass finds the rest.

**Follow-ups they will ask:**
- When does axe run too slowly: on every unit test; scope it to component library tests and a few page-level e2e scans.
- How do you prevent regressions in focus management: explicit tests that open a dialog and assert focus moves in and returns on close.
- Contrast with dynamic themes: run axe per theme in Storybook, since contrast depends on the token values.

**Mistakes to avoid:**
- Treating a green axe run as "accessible".
- Fixing lint errors by adding `role="button"` to a div instead of using a button.

### Q. What makes frontend tests flaky, and how do you fix them for good?
**Short answer (45 seconds):** Almost always one of four things: asynchronous work that the test did not wait for correctly, shared mutable state leaking between tests, dependence on real time or real network, or, in browser tests, animations and layout timing. The fix is determinism: await the UI with `findBy` and web-first assertions rather than sleeps, isolate state per test with fresh clients and handler resets, control time with fake timers, mock the network, and disable animations in e2e. Retries are a diagnostic signal, not a fix, and a flaky test gets quarantined with a ticket rather than ignored.

**Deeper explanation:**

```text
Symptom                             Cause                               Fix
passes alone, fails in suite        shared module singleton, MSW leak   fresh instances per test, resetHandlers
fails only in CI                    slower machine exposes missing await findBy / waitFor, no fixed sleeps
"not wrapped in act" warning        state update after test finished    await the async work, unmount cleanly
wrong relative time text            real Date.now()                     vi.setSystemTime
e2e click misses                    element animating or re-rendering   disable animations, locator auto-wait
random order failures               test data collisions                unique ids per test, no shared fixtures
```

In jsdom, the "not wrapped in act" warning is a flake predictor: it means a promise resolved after the assertion, so the test passed by luck. In Playwright, `await page.waitForTimeout(1000)` is a flake generator; replace it with `await expect(locator).toBeVisible()` or waiting for a specific response with `page.waitForResponse`. Query clients, Zustand stores, and MSW handlers must be created or reset per test; a module-level store that survives between tests is the most common leak in React suites.

Process matters: track flaky tests, make retries visible in reports so they are not silently masking failures, and set a rule that a test retried in CI twice in a week gets fixed or deleted.

**Follow-ups they will ask:**
- How do you debug an e2e flake: Playwright traces with screenshots, network, and console per step, recorded on first retry.
- Do fake timers break `userEvent`: they can; pass `advanceTimers` to `userEvent.setup` so it advances the fake clock between events.
- Is test parallelism a source of flakes: only when tests share state (a database, a port, a file); isolate or serialize those.

**Mistakes to avoid:**
- Adding `retries: 3` and calling the suite stable.
- Fixing a flake with a longer sleep.

### Practice
- Take an existing component test that uses `fireEvent` and class-name assertions, rewrite it with `userEvent` and role queries, then break the accessible name and watch the test catch it.
- Set up Vitest with MSW and `onUnhandledRequest: "error"`; write a test for a list that loads, errors, and retries, with per-test handler overrides.
- Write a Playwright test for your most important flow with role locators and `storageState` login; run it ten times in a loop and fix any flake you find at the root.
- Add `vitest-axe` to a dialog component and `@axe-core/playwright` to one page; fix the first violation and add a focus-management test for the dialog.
- Say it out loud: describe the test pyramid you would set up for a new React product, what each layer is responsible for, and the one rule you would enforce about flaky tests.

## Security & Accessibility

> Frontend security questions check whether you know where React's protection ends: output escaping does nothing for raw HTML, URLs, tokens in storage, or third-party scripts. Accessibility questions check whether you build for keyboards and screen readers by default or bolt it on. Weak answers say "React prevents XSS" and "we add aria-labels". Strong answers describe a defense in depth (sanitization, CSP, cookie flags, CSRF protection, dependency hygiene) and an accessibility practice built on semantic HTML, with ARIA as the exception and focus management as a designed behaviour.

### Concepts you must understand
- React escapes text children and attribute values, so classic injection fails, but `dangerouslySetInnerHTML`, user-controlled `href` and `src` values, raw HTML from markdown, and third-party scripts are all outside that protection.
- A Content Security Policy tells the browser which script and resource origins are allowed; a strict policy uses per-request nonces or hashes with `strict-dynamic`, rolled out first in report-only mode.
- Tokens in `localStorage` are readable by any script that runs on the page; httpOnly cookies are not readable by scripts but are sent automatically, which means CSRF must be handled.
- CSRF defenses stack: `SameSite` cookies, origin header checks, and anti-CSRF tokens for state-changing requests. Clickjacking is blocked with `frame-ancestors`.
- Dependencies are code you ship: lockfiles, automated vulnerability updates, minimal dependency count, install-script caution, and integrity attributes for CDN scripts reduce supply-chain risk.
- WCAG organizes requirements as perceivable, operable, understandable, robust; the usual target is level AA, which includes 4.5:1 text contrast, keyboard operability, visible focus, and content that reflows at narrow widths.
- Semantic HTML gives you roles, names, and keyboard behaviour for free; a `button` is accessible by default, a `div` with `onClick` is not.
- The first rule of ARIA is not to use it when a native element exists; ARIA only changes what assistive technology is told, never behaviour, so every ARIA widget needs hand-built keyboard support.
- Focus is a managed resource: dialogs trap and return it, composite widgets use arrow keys with a roving tabindex, and route changes move it to the new content.

### Q. React escapes output, so how does XSS still happen in a React application?
**Short answer (45 seconds):** React escapes strings rendered as children or attribute values, which stops the classic `<script>` injection. XSS still happens through everything React does not escape: `dangerouslySetInnerHTML` with untrusted HTML, rendered markdown that allows raw HTML, user-controlled `href` or `src` values such as `javascript:` URLs, server-rendered JSON embedded in a script tag without escaping, SVG uploads containing scripts, and third-party scripts or browser extensions. The defenses are to sanitize any HTML you must render with DOMPurify, validate URL schemes, escape embedded JSON, and back all of it with a strict Content Security Policy so a slip does not become an exploit.

**Deeper explanation:**

```ts
import DOMPurify from "dompurify";

function RichText({ html }: { html: string }) {
  const clean = useMemo(
    () => DOMPurify.sanitize(html, { USE_PROFILES: { html: true }, FORBID_TAGS: ["style", "form"] }),
    [html]
  );
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}

function SafeLink({ href, children }: { href: string; children: React.ReactNode }) {
  const ok = /^(https?:|mailto:|\/(?!\/))/i.test(href);   // allow http(s), mailto, same-origin paths
  return <a href={ok ? href : "#"} rel="noopener noreferrer">{children}</a>;
}
```

Markdown is the common AI-product vector: model output or user content is rendered as markdown, and the renderer allows HTML by default in some configurations. Use a renderer with HTML disabled (react-markdown does not render raw HTML unless you add a plugin) and sanitize if you must allow it. For server rendering, data placed into a `script` tag must have `<` escaped as `<`, which frameworks do for their own payloads but not for yours. Trusted Types, enforced through CSP, makes the browser refuse string-to-DOM sinks unless a policy produced the value, which turns a whole class of bugs into runtime errors in development.

**Follow-ups they will ask:**
- Does React block `javascript:` URLs: it warns on them in development; treat the validation as your responsibility.
- Is `dangerouslySetInnerHTML` ever fine: yes for HTML you generated and control, such as highlighted code from a trusted library, and after sanitization for anything user-supplied.
- How do you handle user-uploaded SVGs: serve them as `img` from a separate origin, never inline them, or sanitize and strip scripts and event handlers.

**Mistakes to avoid:**
- "React handles XSS" as the complete answer.
- Sanitizing on the client only; sanitize or validate on the server where the content is stored, and again where it is rendered.

### Q. How would you roll out a Content Security Policy for a React or Next.js application?
**Short answer (45 seconds):** Start in report-only mode so nothing breaks: ship a `Content-Security-Policy-Report-Only` header with a strict policy and a reporting endpoint, collect violations for a week or two, fix or allow-list what is legitimate, then switch to enforcing. The target policy uses a per-request nonce on every script tag with `'strict-dynamic'` so scripts loaded by allowed scripts are trusted, `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'none'`, and `connect-src` limited to your API and WebSocket origins. Nonces require server rendering, which Next.js supports through middleware that generates the nonce and the framework picks up for its own scripts.

**Deeper explanation:**

```text
Content-Security-Policy:
  default-src 'self';
  script-src 'nonce-{random}' 'strict-dynamic';
  style-src 'self' 'nonce-{random}';
  img-src 'self' data: https://cdn.example.com;
  font-src 'self';
  connect-src 'self' https://api.example.com wss://rt.example.com;
  frame-ancestors 'none';
  object-src 'none';
  base-uri 'self';
  report-to csp-endpoint
```

Pure client-rendered apps cannot use per-request nonces because the HTML is static; they use hashes of their inline scripts or avoid inline scripts entirely and rely on `'self'`. `'unsafe-inline'` for scripts defeats the policy and is what analytics vendors will ask you for; the answer is to load their script from an allowed origin with a nonce. Styles are the usual pain: CSS-in-JS that injects style elements at runtime and server-rendered inline `style` attributes are blocked by a strict `style-src`; setting styles through the CSSOM (which React's `style` prop does on the client) is allowed, and most modern libraries support a nonce.

Treat the report stream as a monitoring signal after rollout: a sudden spike of blocked scripts from an unknown origin is either a broken deploy or an injection attempt.

**Follow-ups they will ask:**
- How does CSP help if you already sanitize: defense in depth; a sanitizer bug or a forgotten sink is contained because injected inline scripts have no nonce.
- Does CSP stop data exfiltration: `connect-src`, `img-src`, and `form-action` limit where scripts can send data, which blocks the common exfiltration channels.
- What about browser extensions causing reports: filter known extension origins and `moz-extension`/`chrome-extension` schemes out of the report pipeline.

**Mistakes to avoid:**
- Shipping an enforcing policy on day one and breaking checkout.
- Allowing `'unsafe-inline'` and `'unsafe-eval'` to make a vendor script work, which turns the policy into decoration.

### Q. Where do you store authentication tokens in a browser app: httpOnly cookies or localStorage?
**Short answer (45 seconds):** In httpOnly, Secure, SameSite cookies when the API is same-site, because no script on the page can read them, so an XSS bug cannot exfiltrate the session. `localStorage` is readable by any JavaScript running on the origin, including a compromised dependency, and tokens there walk out the door. Cookies trade that for CSRF exposure, which is manageable with `SameSite` and origin checks. The pattern I prefer is a short-lived access token kept only in memory plus a refresh token in an httpOnly cookie, or a backend-for-frontend that holds the tokens server-side and gives the browser only a session cookie.

**Deeper explanation:**

```text
Set-Cookie: __Host-session=...; Path=/; Secure; HttpOnly; SameSite=Lax
```

The `__Host-` prefix forces `Secure`, no `Domain`, and `Path=/`, which prevents subdomain cookie injection. `SameSite=Lax` sends the cookie on top-level navigations and same-site requests but not on cross-site POSTs, which blocks most CSRF by default; `Strict` also blocks following a link from an email into a logged-in page, so it suits a second, high-privilege cookie rather than the main session.

Cross-domain setups (`app.example.com` calling `api.other.com`) need `SameSite=None; Secure` and CORS with credentials, which reopens CSRF and hits third-party cookie restrictions; put the API behind the same site with a proxy or a BFF. With the in-memory access token pattern, the page starts with no token and silently refreshes using the cookie; a reload costs one request. XSS can still use the session while the page is compromised, which is why token storage is one layer and CSP and sanitization are the others.

**Follow-ups they will ask:**
- What about `sessionStorage`: same exposure to scripts as `localStorage`, just per tab.
- How does a mobile app or a third-party client fit: they use the bearer-token flow with secure device storage; cookies are the browser answer.
- How do you log out everywhere: revoke the refresh token server-side and keep access tokens short enough that revocation takes effect within minutes.

**Mistakes to avoid:**
- Storing a long-lived JWT in `localStorage` and calling it "stateless auth".
- Setting cookies without `Secure` and `HttpOnly` or with a broad `Domain`.

### Q. If sessions live in cookies, how do you prevent CSRF, and how do you stop clickjacking?
**Short answer (45 seconds):** CSRF is a cross-site page making the browser send a state-changing request with your cookies attached. Three layers stop it: `SameSite=Lax` or `Strict` cookies so cross-site requests do not carry the cookie, server-side verification that the `Origin` or `Sec-Fetch-Site` header matches your site, and an anti-CSRF token for state-changing requests, either a synchronizer token tied to the session or a double-submit cookie echoed in a header. Requiring a custom header on JSON APIs also helps, because cross-origin requests with custom headers trigger a CORS preflight the attacker's origin fails. Clickjacking is a different attack, framing your page invisibly; `Content-Security-Policy: frame-ancestors 'none'` blocks it.

**Deeper explanation:**

```ts
// Express: reject state-changing requests from other origins, then require the CSRF header
app.use((req, res, next) => {
  if (["POST", "PUT", "PATCH", "DELETE"].includes(req.method)) {
    const origin = req.get("Origin") ?? "";
    const site = req.get("Sec-Fetch-Site");                  // "same-origin" | "same-site" | "cross-site" | "none"
    if (site === "cross-site" || (origin && !allowedOrigins.has(origin))) return res.sendStatus(403);
    if (req.get("X-CSRF-Token") !== req.cookies["csrf"]) return res.sendStatus(403);  // double submit
  }
  next();
});
```

The double-submit cookie is readable by your JavaScript (not httpOnly) and must be echoed in a header; an attacker's page cannot read your cookie, so it cannot set the header. Next.js server actions compare `Origin` to `Host` for you, which covers the origin check but not a token. Forms that must work without JavaScript need a hidden token field rendered on the server.

GET requests must never change state, otherwise a simple image tag triggers the change with the cookie attached and none of these defenses apply. For clickjacking, `frame-ancestors` supersedes the older `X-Frame-Options` header; send both for old browsers, and if your page must be embeddable by partners, list their origins explicitly.

**Follow-ups they will ask:**
- Is `SameSite=Lax` enough on its own: it covers most cases, but browser differences and subdomain takeover mean the header check and token are worth keeping.
- Does CSRF apply to bearer tokens in headers: no, the attacker cannot set the `Authorization` header cross-site; that is the one security advantage of header tokens.
- How does CORS relate: CORS controls whether a cross-origin page can read a response; it does not stop a simple request from being sent, so it is not a CSRF defense by itself.

**Mistakes to avoid:**
- Treating CORS as CSRF protection.
- State changes on GET endpoints "for convenience".

### Q. How do you manage dependency and supply-chain risk in a frontend codebase?
**Short answer (45 seconds):** Every dependency is code that runs with the user's session, so I keep the count low and the sources trustworthy. Concretely: a committed lockfile and `npm ci` for reproducible builds; automated updates through Renovate or Dependabot gated by tests; `npm audit` or Snyk in CI with a severity policy; install scripts disabled where possible; `overrides` for vulnerable transitive versions; integrity attributes on CDN scripts; and a review for new dependencies that asks who maintains it, what it pulls in, and whether the platform already does the job.

**Deeper explanation:** The incidents that shaped this practice are public: `event-stream` was handed to a new maintainer who shipped a credential stealer; `ua-parser-js` was hijacked through a compromised npm account; and the polyfill.io CDN was bought and began serving malicious code to every site that still loaded it. The lesson is the same each time: a frontend dependency or CDN script executes in your users' browsers with full access to your page.

```bash
npm ci --ignore-scripts                 # reproducible install, no arbitrary postinstall code
npm audit --audit-level=high            # fail CI on high and critical
npx depcheck                            # find dependencies nobody imports
```

```json
{ "overrides": { "semver": "^7.5.4" } }  // pin a vulnerable transitive package until upstream updates
```

For third-party scripts (analytics, chat widgets, A/B tools), governance matters more than tooling: inventory them, load them with a nonce under CSP so a vendor compromise is limited by `connect-src`, sandbox what you can in iframes, and remove the ones nobody owns. Pin versions and add `integrity` hashes for anything loaded from a CDN, or bundle it yourself. Produce build artifacts in CI from the lockfile so a developer laptop is never the source of a production bundle.

**Follow-ups they will ask:**
- How do you evaluate a new package: maintenance activity, download trend, dependency tree size, whether it has install scripts, and whether a 50-line in-house utility would do.
- Lockfile or caret ranges: both; ranges in `package.json` for update flexibility, the lockfile for reproducibility.
- What about `npx` and dev tooling: the same risk applies to anything executed at build time; pin versions and run in CI containers.

**Mistakes to avoid:**
- Ignoring audit output because "it is only dev dependencies"; build-time compromise ships to users too.
- Loading a script from a third-party CDN with no integrity attribute and no version pin.

### Q. What does WCAG require in practice, and how does semantic HTML get you most of the way there?
**Short answer (45 seconds):** WCAG groups requirements into four principles: perceivable, operable, understandable, robust. Most products target level AA, which in daily terms means text contrast of at least 4.5:1 (3:1 for large text and UI components), everything operable with a keyboard with visible focus, no content that depends on colour alone, labels on every control, headings that describe structure, content that reflows at narrow widths without horizontal scrolling, and no keyboard traps. Semantic HTML delivers a large share of this automatically: native buttons, links, inputs with labels, lists, and landmarks have roles, names, and keyboard behaviour built in.

**Deeper explanation:**

```ts
<header>
  <nav aria-label="Primary">...</nav>
</header>
<main id="main">
  <h1>Invoices</h1>
  <section aria-labelledby="overdue-heading">
    <h2 id="overdue-heading">Overdue</h2>
    <table>
      <thead><tr><th scope="col">Customer</th><th scope="col">Amount</th></tr></thead>
      <tbody>...</tbody>
    </table>
    <button type="button" onClick={remind}>Send reminders</button>
  </section>
</main>
```

Landmarks (`header`, `nav`, `main`, `aside`, `footer`) let screen reader users jump between regions; a single `h1` and a non-skipping heading hierarchy give them a table of contents; `label` associated with an input through `htmlFor` gives the field a name and a bigger click target; `th scope` gives table cells context when read aloud. A `button` is focusable, activates on Enter and Space, exposes its role, and is disabled correctly; a `div onClick` is none of these until you reimplement each one.

WCAG 2.2 added practical criteria worth knowing: a minimum target size for interactive elements, focus that must not be hidden behind sticky headers, and a non-dragging alternative for drag actions. Also honour `prefers-reduced-motion` and `prefers-color-scheme`.

**Follow-ups they will ask:**
- Why does accessibility matter commercially: legal exposure in many markets, public-sector procurement requirements, and the overlap with SEO and usability for everyone.
- How do you check contrast with design tokens: compute it in the design system tests for every text and background pair, not by eye.
- What is "robust": content works with current and future assistive technology, which in practice means valid HTML and correct ARIA.

**Mistakes to avoid:**
- Divs and spans with click handlers everywhere, fixed later with `role` and `tabIndex`.
- Removing focus outlines for aesthetics without providing a visible replacement.

### Q. When should you use ARIA, and what are the rules that keep it from making things worse?
**Short answer (45 seconds):** Only when no native element expresses what you are building: tabs, comboboxes, tree views, custom sliders, live regions. The rules: do not add ARIA when a native element exists (`button` over `role="button"`); do not change a native element's semantics; every interactive ARIA role must be fully keyboard operable, because ARIA only changes what assistive technology is told, never behaviour; never hide focusable elements with `aria-hidden`; and every interactive element needs an accessible name. The ARIA Authoring Practices Guide defines the expected keyboard model for each widget, and headless component libraries implement those models so you do not have to.

**Deeper explanation:**

```ts
// Tabs following the APG pattern: roving tabindex, arrow keys move selection
<div role="tablist" aria-label="Settings sections">
  {tabs.map((t, i) => (
    <button key={t.id} role="tab" id={`tab-${t.id}`} aria-selected={i === active}
      aria-controls={`panel-${t.id}`} tabIndex={i === active ? 0 : -1}
      onKeyDown={onArrowKeys} onClick={() => setActive(i)}>
      {t.label}
    </button>
  ))}
</div>
<div role="tabpanel" id={`panel-${tabs[active].id}`} aria-labelledby={`tab-${tabs[active].id}`}>...</div>
```

Naming and describing: `aria-labelledby` points at visible text and is preferred over `aria-label`, which is invisible and often goes stale or untranslated; `aria-describedby` attaches hints and error messages to inputs. State: `aria-expanded` on disclosure triggers, `aria-selected` on tabs and options, `aria-pressed` on toggle buttons, `aria-invalid` on fields with errors, `aria-busy` while a region loads. Live regions announce changes that happen away from focus: `role="status"` (polite) for "saved" messages and `role="alert"` (assertive) for errors; the element must exist before the text changes, or the announcement is missed.

The most damaging ARIA mistakes are additive: a `role="menu"` on a plain navigation list makes screen readers expect menu keyboard behaviour that is not there, and `aria-hidden="true"` on a container that still has focusable children creates ghost focus stops.

**Follow-ups they will ask:**
- How do you test whether ARIA is right: Testing Library role queries confirm the role and name; a screen reader pass confirms the experience.
- `aria-label` on a `div`: ignored unless the element has a role; generic elements cannot be named.
- Why prefer headless libraries: they implement the APG keyboard and ARIA patterns and are tested across screen readers, which is weeks of work to replicate.

**Mistakes to avoid:**
- "Sprinkle aria-labels" as the accessibility plan.
- Giving an element a role without implementing the keyboard behaviour that role promises.

### Q. How do you handle keyboard navigation and focus management for dialogs, menus, and route changes?
**Short answer (45 seconds):** Tab order follows DOM order, so structure the markup in reading order and avoid positive `tabIndex`. Dialogs move focus inside when they open, trap it while open, close on Escape, and return focus to the element that opened them; the native `dialog` element with `showModal()` gives you the trap, Escape, and the top layer for free. Composite widgets such as menus and tabs are one Tab stop with arrow keys moving inside (roving tabindex). On client-side route changes nothing moves by default, so I move focus to the new page's heading or main region and update the document title so screen reader users know the page changed.

**Deeper explanation:**

```ts
function ConfirmDialog({ open, onClose, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();     // focus moves in, background is inert, Escape closes
    if (!open && dialog.open) dialog.close();         // focus returns to the previously focused element
  }, [open]);
  return (
    <dialog ref={ref} onClose={onClose} aria-labelledby="confirm-title">
      <h2 id="confirm-title">Delete item?</h2>
      {children}
    </dialog>
  );
}
```

If you cannot use `dialog`, a headless library (Radix, React Aria) implements the trap, the inert background, and focus return. Menus follow the APG pattern: Enter or Space opens, arrows move, Home and End jump, Escape closes and returns focus. A native `select` needs none of this.

For route changes, an effect on the page component focuses a heading with `tabIndex={-1}` after navigation and sets `document.title`; a visually hidden live region announcing the new page is the backup. Add a "skip to main content" link as the first focusable element, style focus with `:focus-visible`, and never remove outlines globally.

**Follow-ups they will ask:**
- What about focus when a list item is deleted: move focus to the next item, or to the list heading if the list is now empty; losing focus to `body` strands keyboard users.
- How do you handle focus for streaming or loading content: do not steal focus when content arrives; announce it through a live region instead.
- How do you test focus management: assert `toHaveFocus()` after open and after close, and run `user.tab()` through the dialog to confirm the trap.

**Mistakes to avoid:**
- `tabIndex` values above zero to "fix" order instead of fixing the DOM.
- A custom modal that opens without moving focus, so keyboard users are still on the page behind it.

### Practice
- Render model-generated markdown through react-markdown with and without raw HTML enabled, feed it an `img onerror` payload, and confirm which configuration executes it; add DOMPurify where needed.
- Add a report-only CSP to a Next.js app with nonces via middleware, collect violations for a day of local use, and tighten until the enforcing policy loads the app cleanly.
- Build a login flow with an in-memory access token and an httpOnly refresh cookie against an Express API; add the `Sec-Fetch-Site` and double-submit CSRF checks and verify a cross-origin POST from a test page is rejected.
- Run your main feature with keyboard only and VoiceOver or NVDA; write down every unlabelled control and every place focus is lost, then fix the dialog focus return and the route-change focus.
- Say it out loud: a security reviewer asks why you store the refresh token in a cookie instead of localStorage. Give the reasoning, name the attack each choice exposes, and state the mitigations you ship.

## Building AI Product UIs

> This is the section that makes you an AI Full Stack Engineer rather than a frontend engineer who has used an LLM API. Interviewers want to see that you have shipped a streaming UI and hit its problems: tokens arriving faster than React should render, markdown that flickers, a stop button that does not actually stop the model, tool calls that need to be shown and sometimes approved, JSON that is invalid until the last byte. Weak answers describe a chat box. Strong answers describe the state machine, the transport, and the trade-offs you made for perceived speed.

### Concepts you must understand
- Model output arrives as a stream of small chunks over SSE or a chunked `fetch` response; the client reads it with a `ReadableStream` reader, decodes with a streaming `TextDecoder`, and buffers across chunk boundaries because events can be split anywhere.
- Rendering on every token is too many renders; batch appends per animation frame or per few tens of milliseconds, and keep the message list structure stable so only the streaming message re-renders.
- A chat is a state machine over messages with ids and statuses (sending, streaming, complete, error, stopped); the user message is appended optimistically and the assistant message is a placeholder updated in place.
- Markdown from a model is untrusted content: no raw HTML, validated link schemes, no automatic loading of images from arbitrary origins, and memoized rendering of completed blocks so the whole message is not re-parsed per token.
- Tool calls and agent steps are first-class message parts with their own status; users need to see what the agent is doing, and some tools need a human approval step that pauses the stream.
- Cancellation must propagate end to end: client abort, server detects the closed request, upstream model call aborted, partial output preserved and marked as stopped.
- Perceived latency is about time to first visible change, not total time: stream immediately, acknowledge within a hundred milliseconds, show stage text during long tool calls, and never show a bare spinner for long.
- Streaming structured output means the JSON is invalid until it is complete; use an incremental partial-JSON parser or a schema designed to be useful while partial, and validate the final object.
- The `useChat` pattern: a hook that owns messages, input, status, and a stop function, talking to a server route that streams a typed protocol of parts; the shape is worth knowing even if you build your own.
- Accessibility for streaming: announce that a response is in progress and announce the completed message, not every token; keep focus where the user left it; make stop reachable from the keyboard.

### Q. How do you stream model tokens from your server to a React UI, and how do you render them efficiently?
**Short answer (45 seconds):** The server proxies the model's stream and forwards it as Server-Sent Events or a chunked response; the client calls `fetch`, reads `response.body` with a reader, decodes with a `TextDecoder` in streaming mode, and parses events from a buffer because a chunk can end mid-event or mid-character. Each parsed delta is appended to the current assistant message. I do not call `setState` per token; I accumulate into a buffer and flush to React once per animation frame, so the UI renders at most about sixty times a second regardless of token rate, and the message list is keyed so only the streaming message re-renders.

**Deeper explanation:**

```ts
async function readSse(res: Response, onDelta: (text: string) => void, signal: AbortSignal) {
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done || signal.aborted) break;
    buffer += decoder.decode(value, { stream: true });   // keeps split multi-byte characters intact
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";                          // last piece may be incomplete
    for (const evt of events) {
      const data = evt.split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trim()).join("\n");
      if (data && data !== "[DONE]") onDelta(JSON.parse(data).delta);
    }
  }
}
```

On the rendering side, `onDelta` appends to a `pendingRef` string and a `requestAnimationFrame` loop dispatches one `append` action per frame with the batch. The reducer updates the streaming message immutably; every other message keeps its identity, and a memoized `MessageRow` lets the rest of the list skip. Why not `EventSource`: it only does GET and cannot carry an `Authorization` header or a POST body, so most chat UIs use `fetch` and parse SSE by hand, as the popular SDKs do. The server must disable proxy buffering (`X-Accel-Buffering: no` behind Nginx) and flush headers immediately.

**Follow-ups they will ask:**
- What about the server side in Node: pipe the model SDK's async iterator into `res.write` with `text/event-stream`, flush per chunk, and listen for the client closing the request.
- Why batch per frame rather than per token: rendering sixty times a second is invisible to the user; rendering three hundred times a second wastes CPU and can stutter on low-end devices.
- How do you handle a dropped connection mid-stream: show the partial text, mark the message as interrupted, and offer "continue" or "retry", resuming from the server-side partial if you persisted it.

**Mistakes to avoid:**
- Decoding chunks without `{ stream: true }`, which corrupts non-ASCII text when a character spans two chunks.
- `setMessages` on every token for a long response, which creates thousands of renders and visible lag.

### Q. How do you structure chat state so that optimistic user messages and streaming assistant messages behave correctly?
**Short answer (45 seconds):** The conversation is an array of messages with stable ids and an explicit status per message. Sending appends the user message immediately with status `sending` and an assistant placeholder with status `streaming`, then starts the request. Deltas update the placeholder in place by id; completion flips it to `complete`; an error flips it to `error` with the partial text kept and a retry action; stop flips it to `stopped`. All transitions go through one reducer so every component sees the same rules, and the server returns ids that replace client-generated ones when the message is persisted.

**Deeper explanation:**

```ts
type Message = {
  id: string; role: "user" | "assistant"; content: string;
  status: "sending" | "streaming" | "complete" | "error" | "stopped"; error?: string;
};
type Action =
  | { type: "send"; user: Message; assistant: Message }
  | { type: "append"; id: string; delta: string }
  | { type: "finish"; id: string; status: Message["status"]; error?: string }
  | { type: "confirmIds"; map: Record<string, string> };

function reducer(state: Message[], a: Action): Message[] {
  switch (a.type) {
    case "send": return [...state, a.user, a.assistant];
    case "append": return state.map((m) => (m.id === a.id ? { ...m, content: m.content + a.delta } : m));
    case "finish": return state.map((m) => (m.id === a.id ? { ...m, status: a.status, error: a.error } : m));
    case "confirmIds": return state.map((m) => (a.map[m.id] ? { ...m, id: a.map[m.id] } : m));
  }
}
```

Behaviours the state must support: retry that reuses the user message and creates a new assistant placeholder; "edit and resend" that truncates everything after the edited message (or branches, if you keep a tree); regenerate; and an idempotency key per send so a double click or network retry does not create two server-side turns. Scrolling is part of the contract: auto-scroll while the user is at the bottom, stop the moment they scroll up, and show a "jump to latest" button.

Persist to the server as you go (the server already has the full stream) so a refresh restores the conversation, and store the conversation id in the URL so it is shareable and survives reloads.

**Follow-ups they will ask:**
- Where does this state live: in the chat feature's reducer or a small store, with the server as source of truth for history loaded via a query on open.
- How do you keep the input responsive during a stream: the input is separate state; streaming updates touch only the message list.
- Multi-turn with tool calls: the assistant message becomes a list of parts rather than one string, each part with its own status.

**Mistakes to avoid:**
- Treating the assistant message as "the last element" and appending to it by index, which breaks when a second send starts.
- Dropping the partial response on error, which throws away the text the user was reading.

### Q. How do you render streaming markdown safely and without flicker?
**Short answer (45 seconds):** Three concerns. Safety: the markdown is untrusted, so the renderer must not emit raw HTML, links need validated schemes and `rel="noopener noreferrer"`, and images from arbitrary origins should not load automatically, because a prompt injection can embed an image URL that exfiltrates data in its query string. Performance: parsing the whole message on every batch gets slower as the message grows, so split the content into completed blocks and the trailing in-progress block, memoize the completed blocks by content, and re-parse only the tail. Flicker: incomplete syntax such as an unclosed code fence or bold marker makes the tail jump between styles, so either auto-close open constructs for rendering or render the tail more conservatively until a block boundary arrives.

**Deeper explanation:**

```ts
const Block = memo(function Block({ md }: { md: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]}
      components={{ a: SafeLink, img: BlockedImage, code: CodeBlock }}
      urlTransform={(url) => (/^(https?:|mailto:)/i.test(url) ? url : "")}>
      {md}
    </ReactMarkdown>
  );
});

function StreamingMarkdown({ content, streaming }: { content: string; streaming: boolean }) {
  const blocks = useMemo(() => splitIntoBlocks(content), [content]);   // split on blank lines outside code fences
  return (
    <>
      {blocks.slice(0, -1).map((b, i) => <Block key={i} md={b} />)}      // memoized, unchanged content skips
      <Block md={closeOpenConstructs(blocks.at(-1) ?? "", streaming)} />  // only the tail re-parses
    </>
  );
}
```

`splitIntoBlocks` must respect code fences, otherwise a fence that spans several paragraphs is split and rendered as text. Syntax highlighting is expensive; highlight only completed code blocks and render the streaming one as plain preformatted text. For images, render a placeholder with the alt text and a "load image" affordance, or proxy allowed hosts through your own origin. Treat links the same way you would in user-generated content: show the destination on hover and open in a new tab with `noopener`.

**Follow-ups they will ask:**
- Why not sanitize with DOMPurify and allow HTML: you can, but a markdown renderer with HTML disabled removes the attack surface instead of filtering it.
- How do you handle tables and math: GFM tables through `remark-gfm`; math through a KaTeX plugin on completed blocks only, since partial formulas throw.
- What about copying code: a copy button per completed code block, reading from the raw source, not the highlighted DOM.

**Mistakes to avoid:**
- `dangerouslySetInnerHTML` with model output run through a permissive markdown-to-HTML library.
- Re-rendering the entire message markdown on every token for a two-thousand-token answer.

### Q. How do you show tool calls and agent progress in the UI, including steps that need approval?
**Short answer (45 seconds):** Make tool calls first-class parts of the assistant message rather than hiding them. Each call renders as a step with a status (pending, running, done, failed), a human-readable summary of what it is doing ("Searching knowledge base for refund policy"), and an expandable section with the arguments and result for users who want detail. The stream carries typed events for call start, result, and text, so the UI can interleave text and steps in order. For tools with side effects, the server pauses before executing and emits an approval request; the UI renders approve and reject buttons, and the user's decision is sent back to resume the run.

**Deeper explanation:**

```ts
type Part =
  | { type: "text"; text: string }
  | { type: "tool"; id: string; name: string; args: unknown; status: "pending" | "running" | "done" | "failed";
      result?: unknown; summary: string; needsApproval?: boolean }
  | { type: "reasoning"; text: string };          // optional, collapsed by default

function ToolStep({ part, onDecision }: { part: Extract<Part, { type: "tool" }>; onDecision?: (ok: boolean) => void }) {
  return (
    <details aria-busy={part.status === "running"}>
      <summary><StatusIcon status={part.status} /> {part.summary}</summary>
      <pre>{JSON.stringify(part.args, null, 2)}</pre>
      {part.result !== undefined && <ResultView value={part.result} />}
      {part.needsApproval && part.status === "pending" && onDecision && (
        <div><button onClick={() => onDecision(true)}>Approve</button><button onClick={() => onDecision(false)}>Reject</button></div>
      )}
    </details>
  );
}
```

The summary string should come from code, not the model, so it is predictable: map each tool name and its arguments to a sentence. Long-running tools need progress, either intermediate status events from the server or elapsed time with a stage label, because "running" for forty seconds with no change looks frozen. Multi-step agents benefit from a compact timeline above the answer that collapses when the run completes.

Approval is a protocol decision: the run is suspended server-side with its state persisted, the request has an id, and the client posts the decision to resume. Disable the input while a decision is pending and say plainly what approving will do.

**Follow-ups they will ask:**
- Do you show raw tool results to end users: summarized by default, raw behind a toggle; raw JSON is for operators and debugging.
- How do you handle a tool that fails: show the failure as a step with the error summary and let the model's follow-up text explain or retry; never a blank step.
- Should "reasoning" be shown: collapsed and optional if the provider exposes it; most users want the answer, some want the trace.

**Mistakes to avoid:**
- Hiding tool activity behind a spinner, so a twenty-second search looks like a hang.
- Letting the model write the UI status text, which produces inconsistent and sometimes misleading labels.

### Q. How do you implement cancellation of a streaming response end to end?
**Short answer (45 seconds):** The stop button calls `abort()` on the `AbortController` whose signal was passed to `fetch`. The browser closes the request; on the server the request's close or abort event fires, and the handler aborts the upstream model call by passing a signal to the SDK, so you stop paying for tokens nobody will see. The client keeps the partial text, marks the message as `stopped`, and offers "continue". The server persists the partial output with the stopped flag so a refresh shows the same thing. Pressing Escape should do what the button does, and the stop control takes the place of send while streaming.

**Deeper explanation:**

```ts
// client
const controllerRef = useRef<AbortController | null>(null);
async function send(text: string) {
  controllerRef.current?.abort();                      // one stream at a time
  const controller = new AbortController();
  controllerRef.current = controller;
  try {
    const res = await fetch("/api/chat", { method: "POST", body: JSON.stringify({ text, conversationId }), signal: controller.signal });
    await readSse(res, (d) => queueDelta(assistantId, d), controller.signal);
    dispatch({ type: "finish", id: assistantId, status: "complete" });
  } catch (e) {
    dispatch({ type: "finish", id: assistantId, status: (e as Error).name === "AbortError" ? "stopped" : "error" });
  }
}

// server (Express)
app.post("/api/chat", async (req, res) => {
  const upstream = new AbortController();
  req.on("close", () => upstream.abort());             // client went away: stop the model
  const stream = await client.messages.stream({ ...params }, { signal: upstream.signal });
  // forward events to res; on abort, persist the partial text as stopped
});
```

Details that matter: `AbortError` is a normal outcome, not an error toast; the request may already be complete when the user clicks stop, so `finish` must be idempotent; in serverless environments the function may be frozen when the client disconnects, so persist progress as you stream rather than at the end; and if a tool is mid-execution when the user stops, decide whether tools are cancellable or whether the stop takes effect at the next boundary, and show which.

**Follow-ups they will ask:**
- How do you cancel in Next.js route handlers: the `Request` has a `signal`; pass it to the model SDK, and persist incrementally because the handler may be terminated.
- Does the model API stop billing on abort: providers stop generating when the connection closes, so you pay for what was generated so far.
- How do you handle "regenerate" during a stream: abort the current stream first, then start the new one with a fresh assistant id.

**Mistakes to avoid:**
- A stop button that only stops rendering while the server keeps generating and billing.
- Wiring stop to the fetch but not to the upstream model call.

### Q. Which techniques improve perceived latency in an AI interface when the model itself is slow?
**Short answer (45 seconds):** Users judge speed by how fast something changes on screen, so I optimize time to first visible change rather than total time. The user message appears instantly, a thinking indicator shows within a hundred milliseconds, and the first streamed token replaces it. During long tool calls I show stage text that changes ("Searching...", "Reading three documents...") instead of a static spinner, and I keep the input usable. On the backend I stream from the model, start the stream before any non-essential work, and prefetch context on focus so the request leaves earlier.

**Deeper explanation:** Time to first token is dominated by things you control: how quickly the request leaves, what runs before the model call (retrieval, auth, logging), and whether the first token is flushed immediately or buffered by a proxy. Run retrieval in parallel with request setup, stream an acknowledgement event before the model responds so the UI can switch from "sending" to "thinking", and send a stage event per step so the UI has something truthful to show.

```text
0 ms      user message rendered optimistically, input cleared
< 100 ms  indicator appears; status "Thinking"
~300 ms   server ack event: status "Searching your documents"
~1.2 s    first text token: indicator replaced by streaming text
end       status cleared; actions (copy, regenerate, feedback) fade in
```

Two cautions. Do not fake progress: a bar that reaches 90 percent and waits destroys trust; stage labels tied to real events are better. And if a provider bursts large chunks, smoothing them over a few frames reads better than text jumping in paragraphs, as long as the stream never lags reality by more than a moment.

**Follow-ups they will ask:**
- Does a faster model for the first sentence help: it can, but inconsistency between the two outputs is a real risk; measure.
- What about caching: cache retrieval results, use provider prompt caching, and serve identical questions from an answer cache with a visible "cached" label.
- How do you measure perceived latency: log time to first token and time to first visible change on the client, and track them as product metrics next to total latency.

**Mistakes to avoid:**
- A bare spinner for five seconds and then a wall of text.
- Delaying the first token with work that could run in parallel or after the stream starts.

### Q. How do you handle partial or malformed JSON when a model streams structured output?
**Short answer (45 seconds):** A JSON document is syntactically invalid until its last brace, so a naive `JSON.parse` on the accumulated text fails until the end. The options are an incremental parser that returns a best-effort object from a prefix (libraries such as `partial-json` do this, as does the AI SDK's object streaming), a schema designed so partial output is meaningful (top-level fields first, arrays of self-contained items), or streaming newline-delimited JSON where each line is a complete object. In every case the final payload is validated with zod and the UI treats fields as optional until completion.

**Deeper explanation:**

```ts
import { parse as parsePartial } from "partial-json";

const ItineraryDay = z.object({ day: z.number(), title: z.string(), activities: z.array(z.string()) });
const Itinerary = z.object({ destination: z.string(), days: z.array(ItineraryDay) });
type PartialItinerary = DeepPartial<z.infer<typeof Itinerary>>;   // every field optional while streaming

function onDelta(delta: string) {
  buffer += delta;
  const partial = parsePartial(buffer) as PartialItinerary;   // closes open brackets and quotes for you
  setDraft(partial);                                          // render destination as soon as it exists, days as they appear
}

function onDone() {
  const result = Itinerary.safeParse(JSON.parse(buffer));
  if (!result.success) return requestRepair(buffer, result.error);   // ask the model to fix, or fall back
  setFinal(result.data);
}
```

Design the schema for streaming: put the fields the UI needs first in the object so they arrive first (models generally emit keys in schema order when using structured output modes), prefer arrays of complete items over one giant nested object, and keep strings that the user reads near the top. Rendering partial objects needs care: a half-written string looks like a typo, so show strings in a streaming style until the next field begins, and render list items only when they parse completely. Malformed final output (trailing commas, prose before the JSON, markdown fences) is common with weaker models; strip fences and leading prose before parsing, use the provider's JSON mode or tool calling to constrain output, and keep a repair step that re-prompts with the validation error.

**Follow-ups they will ask:**
- Why not ask for NDJSON: it is the simplest robust option for lists; it does not work when the result is one nested object.
- How does tool calling help: tool-call arguments are constrained to the schema by the provider, which removes most syntax errors; streaming tool arguments still arrive as partial JSON.
- How do you type `DeepPartial`: a recursive mapped type, or use the AI SDK's `DeepPartial` export when using its object streaming.

**Mistakes to avoid:**
- `JSON.parse` in a try/catch on every delta and showing nothing until the end, which is just non-streaming with extra CPU.
- Trusting the final object without schema validation because "the model was told the schema".

### Q. Describe the Vercel AI SDK useChat pattern conceptually, and how you keep streaming content accessible.
**Short answer (45 seconds):** `useChat` is a hook that owns the chat state machine: the messages, a status (ready, submitted, streaming, error), a send function, a `stop` wired to an abort controller, and regenerate. It talks to a server route that streams a typed protocol of parts (text deltas, tool calls and results, custom data, finish) rather than raw text, and client messages carry a `parts` array so text and tool steps render in order. That shape (typed parts, explicit status, built-in abort) is worth copying even without the SDK. Accessibility follows: announce status transitions, not tokens.

**Deeper explanation:** The protocol is the valuable idea: raw text cannot express "a tool call started" or "here is data for a card", so the SDK multiplexes typed events over one connection and the hook reduces them into message parts. Client-side tools run through a callback when the model requests a tool the browser owns; human-in-the-loop approval is the same mechanism with a click in between.

```ts
// Accessible status region: announces transitions, never individual tokens
<div role="status" aria-live="polite" className="sr-only">
  {status === "submitted" && "Assistant is thinking"}
  {status === "streaming" && "Assistant is responding"}
  {status === "ready" && lastAssistant && `Assistant replied: ${plainText(lastAssistant).slice(0, 200)}`}
  {status === "error" && "The response failed. Press retry to try again."}
</div>
<article aria-busy={status === "streaming"} aria-label="Assistant message">...</article>
<button type="button" onClick={stop} aria-keyshortcuts="Escape" disabled={status !== "streaming"}>Stop generating</button>
```

Streaming text inside a live region would announce every batch, so the live region carries state changes and a summary of the completed message, and the message itself is normal content read at the user's pace. Keep focus where the user left it; never move it to the streaming message. Honour `prefers-reduced-motion` for typing animations, keep the stop button keyboard-reachable and labelled, and treat "stop auto-scrolling when the user scrolls up" as an accessibility feature.

**Follow-ups they will ask:**
- Why use the SDK instead of hand-rolling: the parts protocol, abort handling, and tool plumbing are weeks of edge cases; hand-roll only for a custom protocol.
- How do you persist: the server's finish callback writes the final message; the client loads history as initial messages.
- How does a screen reader user know a tool ran: the step's summary and status are text, not only an icon.

**Mistakes to avoid:**
- `aria-live="assertive"` on the streaming message.
- Moving focus to the assistant message when the response starts, pulling the user away from the input.

### Practice
- Build a streaming endpoint in Express that forwards a model stream as SSE, and a React client that parses it with a buffered reader and batches renders per frame; measure render count with the Profiler for a 1,500-token answer before and after batching.
- Implement the chat reducer with optimistic send, stop, retry, and regenerate; write unit tests for every transition and for a stop that arrives after completion.
- Render a long model answer with react-markdown naively, then with memoized completed blocks and a conservatively rendered tail; compare CPU time per token and check an unclosed code fence no longer flickers.
- Wire cancellation end to end: client abort, server `close` handler, upstream SDK signal; confirm in the provider dashboard or logs that generation stops within a second of clicking stop.
- Say it out loud: walk an interviewer through what happens from the moment a user presses Enter in your chat UI to the moment the first token renders, naming every component, event, and state transition on the way.
