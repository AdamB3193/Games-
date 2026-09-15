# -*- coding: utf-8 -*-
"""Slope, with no JavaScript. Motion is CSS animation, state is radio/checkbox,
and a collision is a (lane x time) conjunction resolved by the cascade:
the lane gate supplies "which lane", the keyframe supplies "when"."""
import io, random

LANES, LANE_W = 5, 240
Y_FAR, Y_NEAR, Y_BALL = 0, 3100, 2450     # plane y: 0 is the horizon, +y is toward you
TILT  = 72
HIT_F = (Y_BALL - Y_FAR) / float(Y_NEAR - Y_FAR)
PULSE = 2.0                                # how long a wipeout sheet stays up

def lane_x(i): return (i - (LANES - 1) / 2.0) * LANE_W

# ------------------------------------------------------------------ course --
random.seed(7)
course, orbs = [], []
t, i = 4.0, 0
while t < 78.0:
    prog = min(1.0, t / 70.0)
    dur  = 4.2 - 2.0 * prog
    if i % 9 == 8:                                     # wall with one doorway
        gap = random.randrange(LANES)
        for L in range(LANES):
            if L != gap: course.append((t, L, dur))
        orbs.append((t + 0.9, gap, dur))
    else:
        n = 1 if prog < 0.35 else (2 if prog < 0.75 else 3)
        picked = random.sample(range(LANES), n)
        for L in picked: course.append((t, L, dur))
        free = [L for L in range(LANES) if L not in picked]
        if free and random.random() < 0.45:
            orbs.append((t, random.choice(free), dur))
    t += max(0.85, 2.3 - 1.4 * prog)
    i += 1

COURSE_LEN = max(ts + HIT_F * dur for ts, L, dur in course) + 4.0

def merged_hits(L):
    """Crash windows for one lane, overlaps merged so keyframe stops stay ordered."""
    hits = sorted(ts + HIT_F * dur for ts, lane, dur in course if lane == L)
    out = []
    for h in hits:
        if out and h <= out[-1][1] + 0.05: out[-1][1] = max(out[-1][1], h + PULSE)
        else: out.append([h, h + PULSE])
    return out

# --------------------------------------------------------------- css parts --
def keyframes(sfx):
    o = []
    for L in range(LANES):
        x = lane_x(L)
        o.append("@keyframes run%d%s{0%%{transform:translate3d(%.1fpx,%dpx,0) rotateX(-%ddeg);opacity:0}"
                 "7%%{opacity:1}100%%{transform:translate3d(%.1fpx,%dpx,0) rotateX(-%ddeg);opacity:1}}"
                 % (L, sfx, x, Y_FAR, TILT, x, Y_NEAR, TILT))
        stops = ["0%{opacity:0;pointer-events:none}"]
        for a, b in merged_hits(L):
            pa, pb = a / COURSE_LEN * 100.0, min(100.0, b / COURSE_LEN * 100.0)
            stops += ["%.4f%%{opacity:0;pointer-events:none}" % max(0.001, pa - 0.03),
                      "%.4f%%{opacity:1;pointer-events:auto}" % pa,
                      "%.4f%%{opacity:1;pointer-events:auto}" % pb,
                      "%.4f%%{opacity:0;pointer-events:none}" % min(99.999, pb + 0.03)]
        stops.append("100%{opacity:0;pointer-events:none}")
        o.append("@keyframes hit%d%s{%s}" % (L, sfx, "".join(stops)))
    o.append("@keyframes deck%s{from{background-position-y:0}to{background-position-y:240px}}" % sfx)
    for nm, _ in (("d0",1),("d1",1),("d2",1),("d3",1),("sr",1)):
        o.append("@keyframes %s%s{from{transform:translateY(0)}to{transform:translateY(-100%%)}}" % (nm, sfx))
    o.append("@keyframes spd%s{from{width:4%%}to{width:100%%}}" % sfx)
    return "\n".join(o)

def state_rules(gs, sfx):
    r = ["#%s:checked~.game .deck{animation:deck%s 1.15s linear infinite}" % (gs, sfx),
         "#%s:checked~.game .menu{display:none}" % gs,
         "#%s:checked~.game #spdfill{animation:spd%s 80s linear forwards}" % (gs, sfx),
         "#%s:checked~.game .sreel .strip{animation:sr%s 26s steps(10) infinite}" % (gs, sfx)]
    for k, secs in ((0, 1), (1, 10), (2, 100), (3, 1000)):
        r.append("#%s:checked~.game .reel%d .strip{animation:d%d%s %ds steps(10) infinite}"
                 % (gs, k, k, sfx, secs))
    for L in range(LANES):
        r.append("#%s:checked~.game #h%d{animation:hit%d%s %.3fs linear 1 forwards}"
                 % (gs, L, L, sfx, COURSE_LEN))
    for n, (ts, L, dur) in enumerate(course):
        r.append("#%s:checked~.game #o%d{animation:run%d%s %.3fs linear %.3fs 1 forwards}"
                 % (gs, n, L, sfx, dur, ts))
    for n, (ts, L, dur) in enumerate(orbs):
        r.append("#%s:checked~.game #q%d{animation:run%d%s %.3fs linear %.3fs 1 forwards}"
                 % (gs, n, L, sfx, dur, ts))
    return "\n".join(r)

obs_html = "\n".join('<div class="obs" id="o%d"></div>' % n for n in range(len(course)))
orb_html = "\n".join('<div class="orb" id="q%d"></div>' % n for n in range(len(orbs)))
gate_html = "\n".join(
    '<div class="gate g%d"><div class="boom" id="h%d">'
    '<span class="bt">WIPEOUT</span><span class="bs">You hit a block</span>'
    '<span class="brow"><label class="btn retryB" for="gsB">Retry</label>'
    '<label class="btn retryA" for="gsA">Retry</label>'
    '<label class="btn ghost" for="gsM">Menu</label></span></div></div>' % (L, L)
    for L in range(LANES))
lane_rules = "\n".join(
    "#ln%d:checked~.game .ball{transform:translate3d(%.1fpx,%dpx,0) rotateX(-%ddeg)}\n"
    "#ln%d:checked~.game .g%d{opacity:1}" % (L, lane_x(L), Y_BALL, TILT, L, L)
    for L in range(LANES))
radios = "\n".join('<input type="radio" name="lane" id="ln%d" class="lane"%s>'
                   % (L, ' checked' if L == 2 else '') for L in range(LANES))
pad_html = "\n".join(
    '<div class="padrow from%d"><label class="pad" for="ln%d">&#9664;</label>'
    '<label class="pad" for="ln%d">&#9654;</label></div>'
    % (L, max(0, L-1), min(LANES-1, L+1)) for L in range(LANES))
pad_rules = "\n".join("#ln%d:checked~.game .from%d{display:flex}" % (L, L) for L in range(LANES))
digits = "".join("<b>%d</b>" % d for d in range(10))

TPL = u"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#05060d">
<title>Slope &mdash; No JavaScript</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#05060d;color:#e8f6ff;
  font-family:"Segoe UI",system-ui,-apple-system,Roboto,Helvetica,Arial,sans-serif;
  -webkit-user-select:none;user-select:none}
input{position:absolute;opacity:0;width:1px;height:1px}
.game{position:fixed;inset:0;overflow:hidden}

.sky{position:absolute;inset:0;background:linear-gradient(180deg,#030610 0%,#0a1634 42%,#1a3668 100%)}
.stars{position:absolute;inset:0 0 55% 0;opacity:.85;
  background-image:radial-gradient(1.4px 1.4px at 12% 24%,#cfefff,transparent),
   radial-gradient(1.2px 1.2px at 32% 12%,#cfefff,transparent),
   radial-gradient(1.6px 1.6px at 51% 32%,#dff3ff,transparent),
   radial-gradient(1.1px 1.1px at 68% 16%,#cfefff,transparent),
   radial-gradient(1.5px 1.5px at 84% 28%,#cfefff,transparent),
   radial-gradient(1.2px 1.2px at 22% 40%,#bfe8ff,transparent),
   radial-gradient(1.3px 1.3px at 44% 6%,#cfefff,transparent),
   radial-gradient(1.1px 1.1px at 76% 44%,#cfefff,transparent),
   radial-gradient(1.5px 1.5px at 92% 10%,#dff3ff,transparent),
   radial-gradient(1.2px 1.2px at 6% 8%,#cfefff,transparent)}
.glow{position:absolute;left:50%;top:50%;width:150vmax;height:150vmax;transform:translate(-50%,-50%);
  background:radial-gradient(closest-side,rgba(90,200,255,.38),rgba(50,130,220,.14) 36%,rgba(0,0,0,0) 72%)}
.haze{position:absolute;left:-25%;right:-25%;top:calc(50% - 11vh);height:22vh;
  background:linear-gradient(180deg,rgba(20,60,120,0),rgba(9,17,38,.85) 55%,rgba(10,20,44,0))}

.stage{position:absolute;inset:0;perspective:520px;perspective-origin:50% 50%;overflow:hidden}
.world{position:absolute;left:50%;bottom:-140px;width:1200px;height:2800px;margin-left:-600px;
  transform-origin:50% 100%;transform:rotateX(@TILT@deg);transform-style:preserve-3d}
.deck{position:absolute;inset:0;
  background:repeating-linear-gradient(to bottom,#1e305c 0 120px,#16254a 120px 240px)}
.rail{position:absolute;top:0;bottom:0;width:7px;background:#68eeff;
  box-shadow:0 0 22px 5px rgba(104,238,255,.55)}
.rail.l{left:-4px}.rail.r{right:-4px}

.obs,.orb,.ball{position:absolute;top:0;transform-style:preserve-3d}
.obs{left:calc(50% - 58px);width:116px;height:116px;transform-origin:50% 100%;opacity:0;
  background:linear-gradient(180deg,#ff8098,#ff3e60 45%,#a81c3a);
  border-top:6px solid #ff96aa;border-radius:4px;
  box-shadow:0 0 26px rgba(255,62,96,.55),inset 0 -14px 26px rgba(0,0,0,.35)}
.orb{left:calc(50% - 24px);width:48px;height:48px;border-radius:50%;transform-origin:50% 100%;opacity:0;
  background:radial-gradient(circle at 38% 34%,#fffbe6,#ffd166 58%,rgba(255,209,102,0) 75%);
  box-shadow:0 0 26px 8px rgba(255,209,102,.45)}
.ball{left:calc(50% - 58px);width:116px;height:116px;border-radius:50%;transform-origin:50% 100%;
  transform:translate3d(0,@YBALL@px,0) rotateX(-@TILT@deg);
  transition:transform .17s cubic-bezier(.3,.9,.4,1);
  background:radial-gradient(circle at 34% 30%,#fff 4%,#7cfad7 28%,#1aa78f 74%,#07403c 100%);
  box-shadow:0 0 34px 10px rgba(124,250,215,.32),inset -8px -12px 22px rgba(0,0,0,.4);
  border:1px solid rgba(180,255,240,.5)}
.vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse at 50% 50%,rgba(0,0,0,0) 34%,rgba(0,0,0,.55) 100%)}

.hud{position:absolute;inset:0;pointer-events:none;
  padding:calc(env(safe-area-inset-top,0px) + 14px) 18px 0 18px;
  display:flex;justify-content:space-between;align-items:flex-start}
.panel{background:rgba(8,14,28,.42);border:1px solid rgba(90,230,255,.18);border-radius:12px;
  padding:8px 14px;backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px)}
.lbl{font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#7ea6c4;font-weight:700}
.val{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:700;line-height:1;
  display:flex;align-items:flex-end}
#score .val{font-size:34px;color:#7df9ff;text-shadow:0 0 18px rgba(80,240,255,.55)}
.hr{display:flex;flex-direction:column;gap:8px;align-items:flex-end}
#best .val,#spd .val{font-size:17px;color:#b8ecff}
.reel,.sreel{display:inline-block;height:1em;width:.62em;min-width:.62em;flex:0 0 auto;
  overflow:hidden;text-align:center}
.reel .strip,.sreel .strip{display:block}
.reel b,.sreel b{display:block;height:1em;line-height:1em;font-weight:700}
.unit{font-size:15px;color:#5d8ba6;margin-left:5px}
#spdbar{width:118px;height:5px;border-radius:3px;background:rgba(120,200,255,.16);
  overflow:hidden;margin-top:6px}
#spdfill{height:100%;width:4%;border-radius:3px;
  background:linear-gradient(90deg,#39e0ff,#8affc1 55%,#ffd166)}

.screen{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
  justify-content:flex-start;overflow-y:auto;gap:18px;text-align:center;padding:26px;
  background:radial-gradient(ellipse at 50% 42%,rgba(10,22,48,.55),rgba(3,5,12,.92));
  backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px);z-index:8}
.screen::before,.screen::after{content:'';flex:0 0 auto}
.screen::before{margin-top:auto}.screen::after{margin-bottom:auto}
.screen>*{flex:0 0 auto;max-width:100%}
h1{font-size:clamp(46px,13vw,104px);font-weight:900;letter-spacing:.06em;line-height:.92;
  background:linear-gradient(180deg,#eafcff 12%,#49e2ff 52%,#1b6bff 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 0 26px rgba(60,200,255,.45))}
.sub{font-size:13px;letter-spacing:.32em;text-transform:uppercase;color:#6f96b4;font-weight:700}
.btn{cursor:pointer;font-weight:800;letter-spacing:.14em;text-transform:uppercase;font-size:14px;
  color:#061019;background:linear-gradient(180deg,#8ff4ff,#25c7f0);border-radius:999px;
  padding:15px 46px;display:inline-block;
  box-shadow:0 0 30px rgba(50,200,255,.42),0 6px 20px rgba(0,0,0,.45)}
.btn:hover{filter:brightness(1.08)}
.btn.ghost{background:none;color:#9fe6ff;border:1px solid rgba(110,225,255,.42);
  box-shadow:none;padding:12px 30px;font-size:12px}
.tip{font-size:11px;color:#5d7f9b;letter-spacing:.08em;max-width:470px;line-height:1.8}
kbd{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:30px;
  padding:0 8px;border-radius:7px;background:rgba(18,32,58,.85);
  border:1px solid rgba(120,200,255,.3);border-bottom-width:3px;
  font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;font-weight:700;color:#cfefff}
.keys{display:flex;gap:26px;flex-wrap:wrap;justify-content:center}
.key{display:flex;flex-direction:column;align-items:center;gap:7px}
.key span{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#6d93b0;font-weight:700}
@media (max-height:560px){h1{font-size:clamp(30px,8vh,52px)}.screen{gap:10px;padding:16px}.keys{display:none}}

.gate{position:absolute;inset:0;opacity:0;z-index:9;pointer-events:none}
.boom{position:absolute;inset:0;opacity:0;pointer-events:none;text-decoration:none;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;
  background:radial-gradient(ellipse at 50% 42%,rgba(70,6,22,.93),rgba(3,5,12,.985))}
.boom .bt{font-size:clamp(28px,8vw,52px);font-weight:900;letter-spacing:.08em;color:#ff5e7a;
  text-shadow:0 0 26px rgba(255,70,110,.5)}
.boom .bs{font-size:13px;letter-spacing:.32em;text-transform:uppercase;color:#6f96b4;font-weight:700}
.boom .brow{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-top:6px}

.pads{position:absolute;left:0;right:0;bottom:0;height:42%;z-index:7;pointer-events:none}
.padrow{display:none;position:absolute;inset:0;justify-content:space-between;align-items:flex-end;
  padding:0 22px calc(env(safe-area-inset-bottom,0px) + 74px)}
.pad{width:92px;height:92px;border-radius:50%;background:rgba(10,24,48,.4);
  border:1px solid rgba(110,225,255,.28);color:#9fe6ff;font-size:30px;cursor:pointer;
  display:flex;align-items:center;justify-content:center;pointer-events:auto}
.pad:hover{background:rgba(60,200,255,.3)}
.lane:focus-visible~.game .pad{border-color:rgba(160,245,255,.8);box-shadow:0 0 18px rgba(110,225,255,.45)}

#pz:checked~.game *{animation-play-state:paused!important}
#pz:checked~.game .pausescreen{display:flex}
.pausescreen{display:none}
.corner{position:absolute;left:50%;transform:translateX(-50%);
  bottom:calc(env(safe-area-inset-bottom,0px) + 16px);z-index:10}

@KF_A@
@KF_B@
@ST_A@
@ST_B@
@LANE_RULES@
@PAD_RULES@
#gsA:checked~.game .retryA{display:none}
#gsB:checked~.game .retryB{display:none}
#gsM:checked~.game .corner{display:none}
</style>
</head>
<body>
@RADIOS@
<input type="radio" name="gs" id="gsM" checked>
<input type="radio" name="gs" id="gsA">
<input type="radio" name="gs" id="gsB">
<input type="checkbox" id="pz">

<div class="game">
  <div class="sky"><div class="stars"></div><div class="glow"></div><div class="haze"></div></div>
  <div class="stage">
    <div class="world">
      <div class="deck"></div>
      <div class="rail l"></div><div class="rail r"></div>
@ORBS@
@OBSTACLES@
      <div class="ball"></div>
    </div>
  </div>
  <div class="vig"></div>

  <div class="hud">
    <div class="panel" id="score"><div class="lbl">Distance</div>
      <div class="val"><span class="reel reel3"><span class="strip">@DIGITS@</span></span><span
        class="reel reel2"><span class="strip">@DIGITS@</span></span><span
        class="reel reel1"><span class="strip">@DIGITS@</span></span><span
        class="reel reel0"><span class="strip">@DIGITS@</span></span><span class="unit">m</span></div>
    </div>
    <div class="hr">
      <div class="panel" id="best"><div class="lbl">Best</div><div class="val">&mdash;</div></div>
      <div class="panel" id="spd"><div class="lbl">Speed</div>
        <div class="val"><span class="sreel"><span class="strip">@DIGITS@</span></span></div>
        <div id="spdbar"><div id="spdfill"></div></div></div>
    </div>
  </div>

  <div class="pads">
@PADS@
  </div>
@GATES@

  <div class="screen menu">
    <div class="sub">Endless Downhill Runner</div>
    <h1>SLOPE</h1>
    <p class="tip">No JavaScript anywhere. Every pixel of motion is a CSS animation and
      steering is a radio group &mdash; dodge the blocks, chase the orbs.</p>
    <label class="btn" for="gsA">Play</label>
    <div class="keys">
      <div class="key"><div style="display:flex;gap:5px"><kbd>&#8592;</kbd><kbd>&#8594;</kbd></div><span>Steer</span></div>
      <div class="key"><div style="display:flex;gap:5px"><kbd>Tab</kbd></div><span>Focus track</span></div>
    </div>
    <p class="tip">Click <b>Play</b>, then press <kbd>Tab</kbd> once &mdash; the arrow keys steer
      from then on. The round pads work with mouse or touch at any time.</p>
  </div>

  <div class="screen pausescreen">
    <div class="sub">Paused</div><h1 style="font-size:clamp(34px,9vw,64px)">HOLD UP</h1>
    <label class="btn" for="pz">Resume</label>
  </div>

  <label class="btn ghost corner" for="pz">Pause</label>
</div>
</body>
</html>
"""

out = TPL
for k, v in [("@TILT@", str(TILT)), ("@YBALL@", str(Y_BALL)), ("@DIGITS@", digits),
             ("@KF_A@", keyframes("a")), ("@KF_B@", keyframes("b")),
             ("@ST_A@", state_rules("gsA", "a")), ("@ST_B@", state_rules("gsB", "b")),
             ("@LANE_RULES@", lane_rules), ("@PAD_RULES@", pad_rules), ("@RADIOS@", radios),
             ("@OBSTACLES@", obs_html), ("@ORBS@", orb_html), ("@GATES@", gate_html),
             ("@PADS@", pad_html)]:
    out = out.replace(k, v)

low = out.lower()
assert "@" not in out.replace("@media", "").replace("@keyframes", ""), "token left unsubstituted"
for bad in ("<script", "javascript:", "onclick", "onload", "onerror", "<applet", "<object"):
    assert bad not in low, "found %s" % bad
io.open("/home/user/Games-/slope-no-js/slope.html", "w", encoding="utf-8").write(out)
print("wrote slope-no-js/slope.html  (%d bytes, %d obstacles, %d gates)"
      % (len(out), len(course), LANES))
