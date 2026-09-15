# Slope — no JavaScript

The same game as `../slope.html`, rebuilt with **zero JavaScript**. One file,
no dependencies, no network. Open `slope.html` in any browser.

Verified by loading it in Chromium with `javaScriptEnabled: false` — it renders,
steers, collides and restarts with the engine's script support switched off.

## How it works

HTML alone has no computation — no arithmetic, no loops, no state. All of the
behaviour here comes from CSS:

| Concern | Mechanism |
|---|---|
| 3D track | `perspective` + a `rotateX(72deg)` plane; props are children that counter-rotate to stand upright, so the browser does the projection |
| Motion | `@keyframes` translating each prop from the horizon to the camera |
| Steering | a 5-radio group — arrow keys move between radios natively, which is real keyboard control with no script |
| Ball position | one rule per lane, `#lnN:checked ~ .game .ball { transform: ... }`, with a CSS transition to glide |
| Collision | a conjunction: the **lane gate** (`#lnN:checked`) supplies *where*, and a keyframe with a pulse at each arrival time supplies *when*. Both must hold for a wipeout sheet to be visible |
| Odometer | four digit strips scrolled by `steps(10)` animations at 1s / 10s / 100s / 1000s, so the tens carry when the units wrap |
| Pause | `animation-play-state: paused` driven by a checkbox |
| Retry | two interchangeable play states (`gsA`/`gsB`) with identical keyframes under different names — switching states re-applies the animations, which restarts them |

The course is generated at build time by `tools/generate.py`, which emits the
obstacle elements and the per-lane collision keyframes.

## What could not be carried over

These need runtime computation, so no CSS version of them exists:

- **Procedural infinite track.** The course is authored and fixed (~83s, 132 obstacles), identical every run. No curves, hills or holes — those were per-frame maths.
- **Sound.** The original synthesised audio through the Web Audio API.
- **Saved best score.** No `localStorage`, so `BEST` shows a dash.
- **Physics.** Steering snaps between 5 lanes instead of accelerating freely.
- **A latching game over.** CSS cannot store "you were hit". A wipeout shows for 2 seconds; click **Retry** to restart. Ignore it and the run continues.
- **A/D keys.** A radio group responds to arrow keys natively, but nothing can bind letter keys without script.
