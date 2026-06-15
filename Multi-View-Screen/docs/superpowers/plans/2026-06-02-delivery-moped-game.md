# Delivery Moped Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a top-down 2D food-delivery moped game as a single self-contained `delivery.html` — accept orders, drive to the restaurant, deliver to the customer, earn cash, repeat.

**Architecture:** One HTML file with inline `<style>` + `<script>`. An IIFE holds module-like objects (`World`, `moped`, `orders`, `hud`, `input`, `camera`) wired by a single `requestAnimationFrame` loop (`update(dt)` → `render()`). Canvas is DPR-aware and resizes to viewport. No external requests, no deps.

**Tech Stack:** HTML5 Canvas 2D, vanilla ES6 JS. No build step, no libraries.

**Testing note:** Repo has no JS test harness; adding one for a single-file canvas game is out of scope (YAGNI). Verification is via concrete browser checks listed per task. Pure-logic helpers (`timeBonus`, FSM transitions) include inline `console.assert` sanity checks during dev, removed in the final polish task.

---

## File Structure

- **Create:** `delivery.html` (repo root) — the entire game. One file by design: it is a self-contained arcade game with tightly-coupled render/update code; splitting into modules would need a build step this repo doesn't have. Internally organized into clearly-bounded objects (below).
- **Untouched:** `index.html` (existing branching video game), `videos/`.

Internal units inside the `<script>`:
- `canvas`/`ctx` + resize — rendering surface.
- `input` — normalizes keyboard + touch into `{gas:0..1, steer:-1..0..1}`.
- `camera` — `{x,y}` top-left in world space, follows moped, clamped to world.
- `World` — road grid, building blocks, restaurants; `draw`, `blockAt`, `randomCustomerPoint`.
- `moped` — `{x,y,heading,speed}`; `update`, `draw`.
- `orders` — FSM `{state,current}`; `update`, `accept`, `decline`.
- `hud` — DOM overlay (money, timer, banner) + canvas popup + minimap.
- loop — `update(dt)`, `render()`, `frame(t)`.

World constants: `TILE=120`, `COLS=14`, `ROWS=14` → world `1680×1680`. Roads run along tile gridlines; building blocks fill tile interiors.

---

## Task 1: Scaffold — canvas, DPR resize, ground, game loop

**Files:**
- Create: `delivery.html`

- [ ] **Step 1: Create `delivery.html` with canvas + loop skeleton**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<title>Moped Delivery</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html,body { width:100%; height:100%; overflow:hidden; background:#1f6f3a;
    font-family:-apple-system, system-ui, sans-serif; user-select:none; touch-action:none; }
  #game { position:fixed; inset:0; display:block; }
</style>
</head>
<body>
<canvas id="game"></canvas>
<script>
(function(){
  "use strict";
  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");
  let VW = 0, VH = 0, DPR = 1;

  function resize(){
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    VW = window.innerWidth; VH = window.innerHeight;
    canvas.width = Math.floor(VW * DPR);
    canvas.height = Math.floor(VH * DPR);
    canvas.style.width = VW + "px";
    canvas.style.height = VH + "px";
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  window.addEventListener("resize", resize);
  resize();

  function update(dt){ /* filled in later tasks */ }
  function render(){
    ctx.fillStyle = "#2a8f4c"; // grass ground
    ctx.fillRect(0, 0, VW, VH);
  }

  let last = 0;
  function frame(t){
    const dt = last ? Math.min((t - last) / 1000, 0.05) : 0; // clamp to 50ms
    last = t;
    update(dt);
    render();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
</script>
</body>
</html>
```

- [ ] **Step 2: Verify in browser**

Run: `open delivery.html` (or load via local server).
Expected: full-viewport green canvas, no console errors. Resizing window keeps canvas full-bleed and crisp (DPR).

- [ ] **Step 3: Commit**

```bash
git add delivery.html
git commit -m "feat(delivery): scaffold canvas + DPR resize + game loop"
```

---

## Task 2: Moped + camera + keyboard driving

Get a controllable moped moving on the ground with a chase camera, using keyboard first (fast desktop iteration). Touch comes in Task 4.

**Files:**
- Modify: `delivery.html`

- [ ] **Step 1: Add `input` (keyboard), `camera`, `moped` objects**

Insert before `update`:

```javascript
  // ----- input -----
  const keys = Object.create(null);
  window.addEventListener("keydown", e => { keys[e.key.toLowerCase()] = true; });
  window.addEventListener("keyup",   e => { keys[e.key.toLowerCase()] = false; });
  const input = { gas:0, steer:0, brake:0 };
  function readInput(){
    const up = keys["arrowup"]||keys["w"], down = keys["arrowdown"]||keys["s"];
    const left = keys["arrowleft"]||keys["a"], right = keys["arrowright"]||keys["d"];
    input.gas   = up ? 1 : 0;
    input.brake = down ? 1 : 0;
    input.steer = (right?1:0) - (left?1:0);
  }

  // ----- camera -----
  const camera = { x:0, y:0 };

  // ----- moped -----
  const moped = {
    x: 200, y: 200, heading: 0, speed: 0,
    MAX: 300, ACCEL: 420, FRICTION: 260, BRAKE: 600, TURN: 2.8,
    update(dt){
      // accelerate / brake / friction
      this.speed += input.gas * this.ACCEL * dt;
      this.speed -= input.brake * this.BRAKE * dt;
      if (input.gas === 0 && input.brake === 0){
        const f = this.FRICTION * dt;
        this.speed = this.speed > 0 ? Math.max(0, this.speed - f) : Math.min(0, this.speed + f);
      }
      this.speed = Math.max(-this.MAX*0.4, Math.min(this.MAX, this.speed));
      // steering authority scales with how fast you're going
      const grip = Math.min(1, Math.abs(this.speed) / 80);
      this.heading += input.steer * this.TURN * dt * grip * Math.sign(this.speed || 1);
      // integrate
      this.x += Math.cos(this.heading) * this.speed * dt;
      this.y += Math.sin(this.heading) * this.speed * dt;
    },
    draw(ctx){
      const sx = this.x - camera.x, sy = this.y - camera.y;
      ctx.save();
      ctx.translate(sx, sy);
      ctx.rotate(this.heading);
      // shadow
      ctx.fillStyle = "rgba(0,0,0,.25)"; ctx.beginPath();
      ctx.ellipse(0, 8, 18, 9, 0, 0, Math.PI*2); ctx.fill();
      // body (placeholder rounded rect, replaced with sprite in polish)
      ctx.fillStyle = "#e23b3b";
      roundRect(ctx, -16, -9, 32, 18, 6); ctx.fill();
      // nose marker so heading is visible
      ctx.fillStyle = "#fff"; roundRect(ctx, 8, -4, 8, 8, 2); ctx.fill();
      ctx.restore();
    }
  };

  function roundRect(ctx,x,y,w,h,r){
    ctx.beginPath();
    ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r);
    ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath();
  }

  function updateCamera(){
    camera.x = moped.x - VW/2;
    camera.y = moped.y - VH/2;
  }
```

- [ ] **Step 2: Wire into loop**

Replace `update`/`render` bodies:

```javascript
  function update(dt){
    readInput();
    moped.update(dt);
    updateCamera();
  }
  function render(){
    ctx.fillStyle = "#2a8f4c";
    ctx.fillRect(0, 0, VW, VH);
    moped.draw(ctx);
  }
```

- [ ] **Step 3: Verify in browser**

Open `delivery.html`. Hold Up/W → red moped accelerates; Left/Right rotate heading; releasing keys coasts to a stop via friction; Down/S brakes/reverses slightly. Moped stays screen-centered (camera follows). White nose shows facing direction.

- [ ] **Step 4: Commit**

```bash
git add delivery.html
git commit -m "feat(delivery): moped arcade physics + chase camera + keyboard input"
```

---

## Task 3: World — roads, buildings, collision, restaurants

**Files:**
- Modify: `delivery.html`

- [ ] **Step 1: Add `World` object (insert before `moped`)**

```javascript
  // ----- world -----
  const TILE = 120, COLS = 14, ROWS = 14;
  const WORLD_W = TILE*COLS, WORLD_H = TILE*ROWS;
  const ROAD = 46; // half road-width band along each gridline

  const FOODS = [
    {name:"Cheese Burger", emoji:"🍔"}, {name:"Hot Dog", emoji:"🌭"},
    {name:"Pizza Slice", emoji:"🍕"}, {name:"Sushi Roll", emoji:"🍣"},
    {name:"Tacos", emoji:"🌮"}, {name:"Fried Chicken", emoji:"🍗"},
    {name:"Ramen", emoji:"🍜"}, {name:"Donut", emoji:"🍩"},
  ];

  const World = {
    blocks: [],       // {x,y,w,h,color} building rects (tile interiors)
    restaurants: [],  // {x,y,name,emoji} center points
    build(){
      const palette = ["#c9b18c","#b58f6a","#9fb0c2","#caa6a0","#a8bba0","#d0c3a3"];
      let pi = 0;
      for (let r=0; r<ROWS; r++){
        for (let c=0; c<COLS; c++){
          // building fills interior of tile, leaving ROAD margin to gridlines
          const x = c*TILE + ROAD, y = r*TILE + ROAD;
          const w = TILE - ROAD*2, h = TILE - ROAD*2;
          if (w<=0||h<=0) continue;
          this.blocks.push({x,y,w,h,color:palette[(pi++)%palette.length]});
        }
      }
      // pick 8 spread-out blocks as restaurants
      const picks = [[1,1],[5,2],[10,1],[2,6],[8,7],[12,5],[4,11],[10,11]];
      picks.forEach((p,i)=>{
        const [c,r] = p;
        this.restaurants.push({
          x: c*TILE + TILE/2, y: r*TILE + TILE/2,
          name: ["Burger Barn","Dog House","Pizza Plaza","Sushi Spot",
                 "Taco Time","Cluck Hut","Ramen Bar","Sweet Stop"][i],
          emoji: ["🍔","🌭","🍕","🍣","🌮","🍗","🍜","🍩"][i],
        });
      });
    },
    // axis-aligned: is point inside any building block (with radius pad)?
    blockAt(px, py, pad){
      pad = pad||0;
      for (const b of this.blocks){
        if (px > b.x-pad && px < b.x+b.w+pad && py > b.y-pad && py < b.y+b.h+pad) return b;
      }
      return null;
    },
    // a road point not inside a building (for customer pins)
    randomCustomerPoint(){
      for (let i=0;i<200;i++){
        const onVertical = Math.random()<0.5;
        const c = 1 + Math.floor(Math.random()*(COLS-1));
        const r = 1 + Math.floor(Math.random()*(ROWS-1));
        const x = onVertical ? c*TILE : c*TILE + TILE/2;
        const y = onVertical ? r*TILE + TILE/2 : r*TILE;
        if (!this.blockAt(x,y,6) && x>40 && y>40 && x<WORLD_W-40 && y<WORLD_H-40) return {x,y};
      }
      return {x:TILE, y:TILE};
    },
    draw(ctx){
      // asphalt base
      ctx.fillStyle = "#5a5f66"; ctx.fillRect(-camera.x, -camera.y, WORLD_W, WORLD_H);
      // dashed center lines along road gridlines (only near viewport)
      ctx.strokeStyle = "rgba(255,235,120,.7)"; ctx.lineWidth = 3; ctx.setLineDash([18,16]);
      ctx.beginPath();
      for (let c=0;c<=COLS;c++){ const X=c*TILE-camera.x; if(X<-50||X>VW+50)continue; ctx.moveTo(X,-camera.y); ctx.lineTo(X,WORLD_H-camera.y); }
      for (let r=0;r<=ROWS;r++){ const Y=r*TILE-camera.y; if(Y<-50||Y>VH+50)continue; ctx.moveTo(-camera.x,Y); ctx.lineTo(WORLD_W-camera.x,Y); }
      ctx.stroke(); ctx.setLineDash([]);
      // buildings (cull to viewport)
      for (const b of this.blocks){
        const sx=b.x-camera.x, sy=b.y-camera.y;
        if (sx>VW||sy>VH||sx+b.w<0||sy+b.h<0) continue;
        ctx.fillStyle = "rgba(0,0,0,.18)"; roundRect(ctx,sx+3,sy+5,b.w,b.h,8); ctx.fill();
        ctx.fillStyle = b.color; roundRect(ctx,sx,sy,b.w,b.h,8); ctx.fill();
        ctx.fillStyle = "rgba(255,255,255,.12)"; roundRect(ctx,sx,sy,b.w,10,6); ctx.fill();
      }
      // restaurant signs
      for (const s of this.restaurants){
        const sx=s.x-camera.x, sy=s.y-camera.y;
        if (sx<-60||sy<-60||sx>VW+60||sy>VH+60) continue;
        ctx.font = "30px serif"; ctx.textAlign="center"; ctx.textBaseline="middle";
        ctx.fillText(s.emoji, sx, sy-4);
        ctx.font = "bold 11px system-ui"; ctx.fillStyle="#fff";
        ctx.strokeStyle="rgba(0,0,0,.6)"; ctx.lineWidth=3;
        ctx.strokeText(s.name, sx, sy+20); ctx.fillText(s.name, sx, sy+20);
      }
    }
  };
  World.build();
```

- [ ] **Step 2: Add soft collision to `moped.update`**

In `moped.update`, replace the `// integrate` block with axis-separated collision:

```javascript
      // integrate with per-axis soft collision against buildings
      const nx = this.x + Math.cos(this.heading) * this.speed * dt;
      const ny = this.y + Math.sin(this.heading) * this.speed * dt;
      if (!World.blockAt(nx, this.y, 10)) this.x = nx; else this.speed *= 0.4;
      if (!World.blockAt(this.x, ny, 10)) this.y = ny; else this.speed *= 0.4;
      // keep inside world bounds
      this.x = Math.max(12, Math.min(WORLD_W-12, this.x));
      this.y = Math.max(12, Math.min(WORLD_H-12, this.y));
```

- [ ] **Step 3: Draw world before moped; spawn moped on a road**

In `render`, add `World.draw(ctx);` between the grass fill and `moped.draw(ctx);`. Change moped spawn to a road gridline: `x: TILE, y: TILE` in the `moped` literal.

- [ ] **Step 4: Verify in browser**

Open `delivery.html`. City of colored buildings on gray roads with dashed yellow center lines; 8 labeled restaurant emojis spread around. Moped drives on roads and is blocked from driving through buildings (slows/stops at edges, no tunneling). Camera reveals more city as you drive; can't leave world bounds.

- [ ] **Step 5: Commit**

```bash
git add delivery.html
git commit -m "feat(delivery): top-down city grid, buildings, collision, restaurants"
```

---

## Task 4: Touch controls (steer buttons + gas pedal)

**Files:**
- Modify: `delivery.html`

- [ ] **Step 1: Add touch control DOM + CSS**

Add inside `<body>` after the canvas:

```html
<div id="touch">
  <div class="pad left">
    <button class="btn" id="steerL">◄</button>
    <button class="btn" id="steerR">►</button>
  </div>
  <div class="pad right">
    <button class="btn gas" id="gas">GAS</button>
    <button class="btn brake" id="brake">BRK</button>
  </div>
</div>
```

Add to `<style>`:

```css
  #touch { position:fixed; inset:auto 0 0 0; pointer-events:none; }
  .pad { position:fixed; bottom:22px; display:flex; gap:16px; pointer-events:none; }
  .pad.left { left:22px; } .pad.right { right:22px; }
  .btn {
    pointer-events:auto; width:84px; height:84px; border-radius:50%;
    border:none; font:700 18px system-ui; color:#fff;
    background:rgba(20,20,30,.42); backdrop-filter:blur(3px);
    box-shadow:0 6px 16px rgba(0,0,0,.35), inset 0 0 0 2px rgba(255,255,255,.25);
    touch-action:none;
  }
  .btn:active { transform:scale(.94); background:rgba(20,20,30,.6); }
  .btn.gas { background:rgba(40,170,80,.6); width:96px; height:96px; }
  .btn.brake { background:rgba(190,60,60,.55); }
  @media (hover:hover) and (pointer:fine){ #touch{ opacity:.5; } } /* dim on desktop */
```

- [ ] **Step 2: Wire pointer events into `input`**

Add after `readInput` definition. Touch sets flags OR'd with keyboard:

```javascript
  const touch = { gas:false, brake:false, steer:0 };
  function hold(id, on, off){
    const el = document.getElementById(id);
    const set = v => e => { e.preventDefault(); v(); };
    el.addEventListener("pointerdown", set(on));
    el.addEventListener("pointerup",   set(off));
    el.addEventListener("pointercancel", set(off));
    el.addEventListener("pointerleave", set(off));
  }
  hold("gas",   ()=>touch.gas=true,  ()=>touch.gas=false);
  hold("brake", ()=>touch.brake=true,()=>touch.brake=false);
  hold("steerL",()=>touch.steer=-1,  ()=>{ if(touch.steer===-1) touch.steer=0; });
  hold("steerR",()=>touch.steer=1,   ()=>{ if(touch.steer===1)  touch.steer=0; });
```

Then extend `readInput` to merge touch:

```javascript
    if (touch.gas)   input.gas = 1;
    if (touch.brake) input.brake = 1;
    if (touch.steer) input.steer = touch.steer;
```

- [ ] **Step 3: Verify**

Desktop: buttons appear dimmed bottom corners; clicking GAS drives, ◄ ► steer, BRK brakes — works alongside keyboard. Mobile (or devtools device mode): multi-touch GAS + steer simultaneously drives and turns. No page scroll/zoom on tap.

- [ ] **Step 4: Commit**

```bash
git add delivery.html
git commit -m "feat(delivery): mobile touch controls (steer + gas/brake)"
```

---

## Task 5: Order state machine + popup

**Files:**
- Modify: `delivery.html`

- [ ] **Step 1: Add `orders` FSM + `timeBonus` helper**

Insert before `update`:

```javascript
  // ----- orders FSM: idle -> offered -> accepted -> carrying -> delivered/failed -> idle
  function timeBonus(timeLeft){ return Math.round(Math.max(0, timeLeft) * 2); } // $2 per sec left

  const PICKUP_R = 46, DROP_R = 40;
  const orders = {
    state: "idle", current: null, gap: 1.0, // seconds until first offer
    money: 0, lastMsg: "", msgT: 0,
    update(dt){
      if (this.state === "idle"){
        this.gap -= dt;
        if (this.gap <= 0) this.offer();
      } else if (this.state === "accepted" || this.state === "carrying"){
        const o = this.current;
        o.timeLeft -= dt;
        if (o.timeLeft <= 0){ this.fail(); return; }
        const tgt = this.state === "accepted" ? o.restaurant : o.customer;
        const r = this.state === "accepted" ? PICKUP_R : DROP_R;
        if (Math.hypot(moped.x - tgt.x, moped.y - tgt.y) < r){
          if (this.state === "accepted"){ this.state = "carrying"; this.flash("Order picked up — deliver it!"); }
          else { this.deliver(); }
        }
      }
      if (this.msgT > 0) this.msgT -= dt;
    },
    offer(){
      const rest = World.restaurants[Math.floor(Math.random()*World.restaurants.length)];
      const food = FOODS[Math.floor(Math.random()*FOODS.length)];
      const customer = World.randomCustomerPoint();
      const dist = Math.hypot(customer.x-rest.x, customer.y-rest.y);
      const payout = Math.round(30 + dist/12);
      const timeLimit = Math.round(35 + dist/60);
      this.current = { restaurant:rest, customer, name:food.name, emoji:food.emoji,
                       payout, timeLimit, timeLeft: timeLimit };
      this.state = "offered";
    },
    accept(){ if(this.state==="offered"){ this.state="accepted"; this.flash("Head to "+this.current.restaurant.name); } },
    decline(){ if(this.state==="offered"){ this.state="idle"; this.gap=0.8; this.current=null; } },
    deliver(){ this.money += this.current.payout + timeBonus(this.current.timeLeft);
               this.flash("Delivered! +$"+(this.current.payout+timeBonus(this.current.timeLeft)));
               this.current=null; this.state="idle"; this.gap=1.6; },
    fail(){ this.flash("Too slow — order lost"); this.current=null; this.state="idle"; this.gap=1.6; },
    flash(msg){ this.lastMsg=msg; this.msgT=2.2; },
    target(){ if(this.state==="accepted")return this.current.restaurant;
              if(this.state==="carrying")return this.current.customer; return null; }
  };
  // dev sanity checks (removed in polish task)
  console.assert(timeBonus(10)===20 && timeBonus(-5)===0, "timeBonus");
```

- [ ] **Step 2: Build the popup as a DOM overlay (shown only when `state==='offered'`)**

Add to `<body>`:

```html
<div id="popup" class="hidden">
  <div class="card">
    <div class="emoji" id="pEmoji">🍔</div>
    <div class="pname" id="pName">Cheese Burger</div>
    <div class="price" id="pPrice">$10.00</div>
    <div class="ptimer">⏱ <span id="pTimer">00:23</span></div>
    <div class="row">
      <button id="decline" class="dec">DECLINE</button>
      <button id="accept" class="acc">ACCEPT</button>
    </div>
  </div>
</div>
```

Add to `<style>`:

```css
  #popup { position:fixed; inset:0; display:flex; align-items:center; justify-content:center;
    background:rgba(0,0,0,.35); z-index:30; }
  #popup.hidden { display:none; }
  .card { width:min(86vw,320px); background:#fff; border-radius:22px; padding:22px;
    text-align:center; box-shadow:0 20px 50px rgba(0,0,0,.5); }
  .card .emoji { font-size:64px; }
  .card .pname { font-weight:800; font-size:24px; margin-top:6px; }
  .card .price { color:#888; font-weight:700; margin-top:4px; }
  .card .ptimer { margin:12px 0; font-weight:700; color:#444; }
  .card .row { display:flex; gap:12px; }
  .card button { flex:1; padding:14px 0; border:none; border-radius:12px;
    font:800 16px system-ui; color:#fff; }
  .card .dec { background:#e8607a; } .card .acc { background:#2faf5a; }
```

- [ ] **Step 3: Wire popup buttons + show/hide each frame**

Add near other listeners:

```javascript
  const popup = document.getElementById("popup");
  document.getElementById("accept").addEventListener("click", ()=>orders.accept());
  document.getElementById("decline").addEventListener("click", ()=>orders.decline());
  function syncPopup(){
    if (orders.state === "offered"){
      const o = orders.current;
      document.getElementById("pEmoji").textContent = o.emoji;
      document.getElementById("pName").textContent = o.name;
      document.getElementById("pPrice").textContent = "$"+o.payout;
      const s = Math.max(0,Math.ceil(o.timeLeft));
      document.getElementById("pTimer").textContent = "00:"+String(s).padStart(2,"0");
      popup.classList.remove("hidden");
    } else {
      popup.classList.add("hidden");
    }
  }
```

Call `orders.update(dt);` in `update()` (after `updateCamera`) and `syncPopup();` at end of `update()`.

- [ ] **Step 4: Verify**

Open game. ~1s in, popup appears with food emoji/name/price/timer. DECLINE → popup closes, new offer shortly. ACCEPT → popup closes (driving resumes). Console shows no assert failures. (Targets/markers not visible yet — next task.)

- [ ] **Step 5: Commit**

```bash
git add delivery.html
git commit -m "feat(delivery): order state machine + accept/decline popup"
```

---

## Task 6: Navigation — target marker + route arrow + arrival

Markers make the accepted/carrying targets visible and confirm arrival logic from Task 5.

**Files:**
- Modify: `delivery.html`

- [ ] **Step 1: Add `drawTarget()` (marker + pulsing ring + route arrow)**

```javascript
  let pulse = 0;
  function drawTarget(dt){
    pulse += dt*3;
    const tgt = orders.target();
    if (!tgt) return;
    const sx = tgt.x - camera.x, sy = tgt.y - camera.y;
    const carrying = orders.state === "carrying";
    const col = carrying ? "#2faf5a" : "#ff9d2e";
    // pulsing ground ring
    const r = 26 + Math.sin(pulse)*5;
    ctx.strokeStyle = col; ctx.lineWidth = 4; ctx.globalAlpha = .9;
    ctx.beginPath(); ctx.arc(sx, sy, r, 0, Math.PI*2); ctx.stroke();
    ctx.globalAlpha = 1;
    // pin
    ctx.font = "34px serif"; ctx.textAlign="center"; ctx.textBaseline="alphabetic";
    ctx.fillText(carrying ? "📍" : "🏪", sx, sy-6);
    // route arrow from moped toward target (clamped to screen edge if off-screen)
    const dx = tgt.x - moped.x, dy = tgt.y - moped.y;
    const ang = Math.atan2(dy, dx);
    const mx = moped.x - camera.x, my = moped.y - camera.y;
    const ax = mx + Math.cos(ang)*70, ay = my + Math.sin(ang)*70;
    ctx.save(); ctx.translate(ax, ay); ctx.rotate(ang);
    ctx.fillStyle = col;
    ctx.beginPath(); ctx.moveTo(16,0); ctx.lineTo(-8,-10); ctx.lineTo(-8,10); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
```

- [ ] **Step 2: Call it in `render` (after world, before/after moped)**

In `render`, after `World.draw(ctx);` add `drawTarget(lastDt);` then `moped.draw(ctx);`. Store dt: in `update`, set a module var `lastDt = dt;` (declare `let lastDt = 0;` near top) so render can use it for the pulse.

- [ ] **Step 3: Verify**

Accept an order → orange 🏪 ring marker at the restaurant + orange arrow orbiting the moped points toward it. Drive into the ring → banner flips to "deliver" and marker turns green 📍 at the customer. Drive into customer ring → "Delivered! +$NN". Arrow always points at the active target.

- [ ] **Step 4: Commit**

```bash
git add delivery.html
git commit -m "feat(delivery): target marker, pulsing ring, route arrow"
```

---

## Task 7: HUD — money, timer, banner; payout already wired

**Files:**
- Modify: `delivery.html`

- [ ] **Step 1: Add HUD DOM**

Add to `<body>`:

```html
<div id="hud">
  <div id="banner"></div>
  <div id="topbar">
    <div id="orderInfo" class="chip hidden"><span id="oiEmoji">🍔</span> <span id="oiName">—</span> · <span id="oiTimer">00:00</span></div>
    <div id="money" class="chip">💵 $0</div>
  </div>
</div>
```

Add to `<style>`:

```css
  #hud { position:fixed; inset:0; pointer-events:none; z-index:20; color:#fff; }
  #topbar { position:fixed; top:14px; left:0; right:0; display:flex; justify-content:space-between;
    padding:0 16px; font:800 16px system-ui; text-shadow:0 2px 6px rgba(0,0,0,.6); }
  .chip { background:rgba(20,20,30,.5); padding:8px 14px; border-radius:20px; }
  .chip.hidden { display:none; }
  #banner { position:fixed; top:64px; left:0; right:0; text-align:center;
    font:800 20px system-ui; text-shadow:0 2px 8px rgba(0,0,0,.7); transition:opacity .3s; opacity:0; }
```

- [ ] **Step 2: Add `syncHud()`**

```javascript
  const elMoney = document.getElementById("money");
  const elBanner = document.getElementById("banner");
  const elOrder = document.getElementById("orderInfo");
  function syncHud(){
    elMoney.textContent = "💵 $" + orders.money;
    if (orders.state === "accepted" || orders.state === "carrying"){
      const o = orders.current, s = Math.max(0, Math.ceil(o.timeLeft));
      document.getElementById("oiEmoji").textContent = o.emoji;
      document.getElementById("oiName").textContent = o.name;
      document.getElementById("oiTimer").textContent = "00:"+String(s).padStart(2,"0");
      elOrder.classList.remove("hidden");
    } else {
      elOrder.classList.add("hidden");
    }
    if (orders.msgT > 0){ elBanner.textContent = orders.lastMsg; elBanner.style.opacity = 1; }
    else { elBanner.style.opacity = 0; }
  }
```

Call `syncHud();` at end of `update()`.

- [ ] **Step 3: Verify**

Money chip top-right shows `$0`, increments on delivery. While carrying/heading to pickup, order chip top-left shows emoji + name + live countdown. Banner fades in for "picked up", "Delivered! +$NN", "Too slow". Let a timer expire → "Too slow — order lost", money unchanged, new offer follows.

- [ ] **Step 4: Commit**

```bash
git add delivery.html
git commit -m "feat(delivery): HUD money/timer/banner"
```

---

## Task 8: Minimap

**Files:**
- Modify: `delivery.html`

- [ ] **Step 1: Add `drawMinimap()` (canvas, top-left under chips)**

```javascript
  function drawMinimap(){
    const W = 120, H = 120, pad = 14, top = 52;
    const x0 = pad, y0 = top;
    ctx.save();
    ctx.globalAlpha = .85;
    ctx.fillStyle = "#2b2f36"; roundRect(ctx, x0, y0, W, H, 10); ctx.fill();
    const sx = W/WORLD_W, sy = H/WORLD_H;
    // restaurants
    ctx.fillStyle = "#caa24a";
    for (const r of World.restaurants){ ctx.fillRect(x0+r.x*sx-1, y0+r.y*sy-1, 3, 3); }
    // target
    const tgt = orders.target();
    if (tgt){ ctx.fillStyle = orders.state==="carrying"?"#2faf5a":"#ff9d2e";
      ctx.beginPath(); ctx.arc(x0+tgt.x*sx, y0+tgt.y*sy, 3.5, 0, Math.PI*2); ctx.fill(); }
    // player
    ctx.fillStyle = "#e23b3b";
    ctx.beginPath(); ctx.arc(x0+moped.x*sx, y0+moped.y*sy, 3.5, 0, Math.PI*2); ctx.fill();
    ctx.restore();
  }
```

- [ ] **Step 2: Call in `render` last (HUD layer on top of world)**

Add `drawMinimap();` at the end of `render()`.

- [ ] **Step 3: Verify**

Minimap panel top-left shows gold restaurant dots, a red player dot that moves as you drive, and a colored target dot (orange pickup / green dropoff) matching the active order.

- [ ] **Step 4: Commit**

```bash
git add delivery.html
git commit -m "feat(delivery): corner minimap"
```

---

## Task 9: Polish — art, start overlay, cleanup, full playthrough

**Files:**
- Modify: `delivery.html`

- [ ] **Step 1: Improve moped sprite**

Replace the placeholder body block in `moped.draw` with a clearer scooter: red body, darker seat, two dark wheels, small headlight, and a rider dot. Keep it drawn in local (rotated) space:

```javascript
      // wheels
      ctx.fillStyle = "#222";
      ctx.beginPath(); ctx.ellipse(-12,0,5,5,0,0,Math.PI*2); ctx.ellipse(12,0,5,5,0,0,Math.PI*2); ctx.fill();
      // body
      ctx.fillStyle = "#e23b3b"; roundRect(ctx,-15,-7,30,14,7); ctx.fill();
      // delivery box
      ctx.fillStyle = "#d23"; roundRect(ctx,-15,-9,12,18,3); ctx.fill();
      ctx.fillStyle = "#fff"; ctx.font="8px system-ui"; ctx.textAlign="center"; ctx.fillText("🍔",-9,3);
      // rider
      ctx.fillStyle = "#3a4a8c"; ctx.beginPath(); ctx.arc(2,0,5,0,Math.PI*2); ctx.fill();
      // headlight
      ctx.fillStyle = "#ffe9a8"; roundRect(ctx,13,-3,4,6,2); ctx.fill();
```

- [ ] **Step 2: Add a start overlay (tap to begin) + brief how-to**

```html
<div id="start">
  <div class="scard">
    <h1>🛵 Moped Delivery</h1>
    <p>Accept orders, ride to the restaurant, then deliver to the customer before the timer runs out. Earn cash for fast drops!</p>
    <p class="hint">Drive: GAS + ◄ ► (or arrow keys / WASD)</p>
    <button id="startBtn">START</button>
  </div>
</div>
```

```css
  #start { position:fixed; inset:0; z-index:40; display:flex; align-items:center; justify-content:center;
    background:linear-gradient(160deg,#1b5e34,#0f3d22); color:#fff; text-align:center; }
  #start.hidden { display:none; }
  .scard { width:min(88vw,360px); padding:10px; }
  .scard h1 { font-size:34px; margin-bottom:14px; }
  .scard p { opacity:.9; line-height:1.5; margin-bottom:10px; }
  .scard .hint { font-size:13px; opacity:.7; }
  #startBtn { margin-top:18px; padding:16px 44px; border:none; border-radius:14px;
    background:#2faf5a; color:#fff; font:800 18px system-ui; }
```

Gate the order FSM until start: add `let started = false;` ; in `update`, only call `orders.update(dt)` / `syncPopup()` when `started`. Wire:

```javascript
  document.getElementById("startBtn").addEventListener("click", ()=>{
    started = true; document.getElementById("start").classList.add("hidden");
  });
```

- [ ] **Step 2: Remove dev asserts**

Delete the `console.assert(... "timeBonus")` line added in Task 5.

- [ ] **Step 3: Full playthrough verification**

Open `delivery.html`. Checklist:
- Start overlay → START hides it; no console errors/network requests.
- Drive smoothly via touch (devtools device mode) and keyboard; can't tunnel buildings; can't leave world.
- Popup offers; ACCEPT routes to restaurant (orange), pickup flips to customer (green), delivery pays out, money rises; time bonus larger for fast drops.
- DECLINE and timeout both recover to a new offer.
- Route arrow + minimap dots track the active target throughout.
- Play ~6 deliveries continuously with no soft-lock.

- [ ] **Step 4: Commit**

```bash
git add delivery.html
git commit -m "feat(delivery): art pass, start overlay, cleanup, v1 complete"
```

---

## Self-Review (completed during planning)

- **Spec coverage:** World/Map (T3), Moped (T2), Order FSM (T5), Nav/markers (T6), HUD (T7), Controls keyboard (T2)+touch (T4), Game loop (T1), minimap (T8), art/flow (T9). All spec systems mapped.
- **Placeholders:** none — every code step has concrete code; verification steps are concrete browser checks.
- **Type/name consistency:** `orders.target()`, `orders.state` values (`idle/offered/accepted/carrying`), `World.blockAt(px,py,pad)`, `World.randomCustomerPoint()`, `timeBonus()`, `roundRect()`, `camera.x/y`, `lastDt` used consistently across tasks. `roundRect` defined in T2 before all later uses.
- **Note:** Task 9 has two "Step 2"s in source ordering (art/start vs remove asserts) — execute top-to-bottom regardless of label.
```
