# Design language

Generated games look cheap when typography, spacing and colour are ad hoc. A small token
system fixes 80% of that for a fixed cost of ~40 lines of CSS.

## Tokens

Define once on `:root`, consume everywhere — including from JS so canvas and DOM agree.

```css
:root{
  /* palette: two surfaces, one ink, one line, one accent, four semantics */
  --paper:#f7f4e9; --paper-2:#eae5d3; --ink:#20332c; --ink-2:#3a5449;
  --line:#2f4b3f; --accent:#efa63f; --accent-d:#7a5a18;
  --ok:#5ba368; --warn:#e2b93f; --bad:#d85f4d; --info:#4f91c9;

  /* type: one display face, one UI face, one mono for numbers */
  --f-ui: system-ui, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  --f-num: ui-monospace, "SFMono-Regular", Menlo, monospace;

  /* rhythm: 4px base, 8px steps */
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:24px; --s6:32px; --s7:48px;

  /* depth: hard offset shadows, not blur-only */
  --shadow: 0 4px 0 rgba(24,48,38,.25), 0 14px 34px rgba(20,40,32,.22);
  --r-btn: 12px; --r-card: 18px; --r-pill: 999px;

  /* safe areas for notched devices */
  --sat: env(safe-area-inset-top, 0px); --sab: env(safe-area-inset-bottom, 0px);
  --sal: env(safe-area-inset-left, 0px); --sar: env(safe-area-inset-right, 0px);
}
```

Rules: **two surfaces maximum**, one accent, semantic colours only for meaning. If everything
is colourful, nothing reads as important.

## Type scale

Three sizes per role, no more. Use `clamp()` so phones and desktops share one rule.

```css
.t-display { font-size: clamp(38px, 9vw, 92px); font-weight: 900; letter-spacing: .06em; line-height: 1.06; }
.t-title   { font-size: clamp(20px, 3.4vw, 30px); font-weight: 800; }
.t-body    { font-size: 15px; line-height: 1.75; color: var(--ink-2); }
.t-label   { font-size: 11px; font-weight: 700; letter-spacing: .24em; text-transform: uppercase; color: var(--ink-2); }
.t-num     { font-family: var(--f-num); font-variant-numeric: tabular-nums; }
```

`tabular-nums` matters: a counter that shifts horizontally while counting looks broken.

## Buttons

Physical, pressable, obvious. The 3 px travel on `:active` is the whole trick.

```css
.btn{
  padding: 11px 22px; border-radius: var(--r-btn);
  background: var(--paper); color: var(--ink);
  border: 2px solid var(--line); font: 600 15px/1 var(--f-ui);
  box-shadow: 0 4px 0 rgba(24,48,38,.25);
  transition: transform .08s, box-shadow .08s, background .15s;
  min-height: 44px;                       /* touch target */
}
.btn:hover{ background:#fff; transform: translateY(-1px); box-shadow: 0 5px 0 rgba(24,48,38,.25); }
.btn:active{ transform: translateY(3px); box-shadow: 0 1px 0 rgba(24,48,38,.25); }
.btn.primary{ background: var(--accent); color:#2b2410; border-color: var(--accent-d); }
.btn[disabled]{ opacity:.42; pointer-events:none; }
```

One primary action per screen. If two buttons look equally important, the screen has no
answer for the player.

## Screens

A screen is a card on a scrim, centred, with a maximum width. That is it — no routing, no
transitions longer than 200 ms.

```css
.screen{ position:absolute; inset:0; z-index:30; display:grid; place-items:center; padding: var(--s5);
         background: linear-gradient(180deg, rgba(21,52,39,.42), rgba(12,32,24,.72)); }
.screen .card{ width:min(560px, 94vw); background:var(--paper); border:3px solid var(--line);
               border-radius:var(--r-card); padding: clamp(20px,4vw,40px); box-shadow: var(--shadow); }
```

Hierarchy inside a card, top to bottom: eyebrow label → display title → one-line premise →
actions → fine print. The fine print is where version, credits and "progress is saved locally"
belong.

## HUD composition

Corners for status, centre for the crosshair and transient messages, edges for prompts.

```
top-left      vitals (health, stamina, ammo)     top-right   score / objective
top-centre    timer, compass, zone name          bottom      contextual prompt
centre        reticle, hit marker                bottom-edge touch controls
```

Rules:

- No more than six persistent HUD elements. Everything else is transient.
- Numerals in mono, aligned to a fixed width.
- Health uses both a bar and a colour: bar length carries the information, colour reinforces.
- Every prompt is a verb ("Press E to interact"), not a noun.
- HUD never overlaps itself at 320 px width — test that explicitly.

## Motion

- UI transitions: 120–200 ms, `ease-out` in, `ease-in` out.
- Never animate more than two properties; prefer `transform` and `opacity`.
- Screen shake amplitude ≤ 6 px, duration ≤ 200 ms, and decays — anything more is nausea.
- Idle animation on everything alive: 1–2 px bob, 2–3 s period.
- Respect `prefers-reduced-motion` (see `resilience-and-a11y.md`).

## Colour in-game vs in-UI

Keep gameplay signals out of the UI palette: damage flash is a saturated red overlay, not the
`--bad` chip colour. Otherwise the HUD and the world fight for the same meaning.

## The 30-minute polish checklist

Cheap changes that make a generated game look authored:

1. Hard offset shadow under cards and buttons (not a soft blur).
2. A vignette overlay on gameplay.
3. One accent colour used consistently for "the thing you should press".
4. Letter-spaced uppercase micro-labels above titles.
5. A boot screen with a determinate bar and the game's name.
6. A one-line premise under the title.
7. Tabular numerals in every counter.
8. Press-down travel on every button.
