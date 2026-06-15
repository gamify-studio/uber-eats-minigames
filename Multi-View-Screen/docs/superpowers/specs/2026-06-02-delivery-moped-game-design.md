# Delivery Moped Game — Design Spec

**Date:** 2026-06-02
**Status:** Approved (design), pre-implementation

## Concept

Top-down 2D food-delivery game. Player rides a moped around a city, accepts
order offers, drives to the restaurant to pick up, then to the customer pin to
drop off — beating a countdown timer to earn cash. Mobile-first, themed on food
delivery (burgers, hotdogs, etc.), inspired by the reference mobile sims but
rebuilt as a lightweight 2D arcade game.

## Locked scope decisions

- **Look & tech:** Top-down 2D city, HTML5 `<canvas>`, vanilla JS, no deps.
- **Controls:** Mobile touch primary (on-screen steer + gas), keyboard fallback.
- **V1:** Core loop only — order → pickup → dropoff → earn → repeat. No fuel,
  upgrades, stacked orders, 3D, or sound.

## File layout

- New self-contained file: `delivery.html` at repo root.
- Existing `index.html` (branching video game) is untouched.
- Single file: inline `<style>` + `<script>`. No build step.

## Systems (isolated units)

### 1. World / Map
- City rendered top-down: gray road grid over a darker ground, colored
  building blocks between roads.
- A fixed set of **restaurant** spots (e.g. 5–8), each a building with a food
  emoji sign and a name.
- **Customer** pins generated dynamically at road-adjacent points.
- World is larger than the screen; a **camera** follows the moped (centered),
  clamped to world bounds.
- **Interface:** `world.draw(ctx, camera)`, `world.restaurants`,
  `world.randomCustomerPoint()`, `world.blocks` (for collision).

### 2. Moped (player)
- State: `{x, y, heading, speed}`.
- Arcade physics per frame (dt-scaled): gas → accelerate along `heading` up to
  max speed; steer left/right → rotate `heading` (steer authority scales with
  speed so you don't spin in place); friction decays speed when off-gas.
- **Soft collision:** if next position overlaps a building block, cancel that
  axis / bounce speed down — keeps player on roads without hard stops.
- **Interface:** `moped.update(dt, input)`, `moped.draw(ctx, camera)`.

### 3. Order state machine
- States: `idle → offered → accepted → carrying → delivered`, plus `failed`.
- An **order**: `{restaurant, item, emoji, customerPoint, payout, timeLimit,
  timeLeft}`.
- Transitions:
  - `idle`: after a short gap, generate an order → `offered`.
  - `offered`: popup shown (item, price, ACCEPT/DECLINE). Decline → back to
    `idle` (new offer soon). Accept → `accepted`, target = restaurant, timer
    starts.
  - `accepted`: target is the restaurant; entering its radius → `carrying`,
    banner flips to "Deliver the order", target = customer pin.
  - `carrying`: entering customer radius → `delivered`; award
    `payout + timeBonus(timeLeft)`; brief celebratory beat → `idle`.
  - Timer reaches 0 in `accepted`/`carrying` → `failed`: no/low pay, short
    beat → `idle`.
- **Interface:** `orders.update(dt, moped)`, `orders.current`,
  `orders.accept()`, `orders.decline()`.

### 4. Navigation / markers
- **Route arrow:** a green chevron/line from moped pointing toward the active
  target (restaurant while `accepted`, customer while `carrying`).
- **Target marker:** pulsing pin drawn at the target world position.
- **Minimap:** fixed corner panel showing simplified world bounds, player dot,
  and target dot.

### 5. HUD
- Top: money `$NNN`, and current-order strip with item name + countdown timer.
- Center/top banner: contextual prompt — "New order!", "Pick up the order",
  "Deliver the order", "Delivered! +$NN", "Order failed".
- Order **popup** card (offered state): food emoji, item name, price, timer,
  ACCEPT / DECLINE buttons. Pauses generation pressure until answered.

### 6. Controls
- **Touch:** bottom-left = left/right steer buttons; bottom-right = gas pedal
  (matches reference layout). Multi-touch so you can steer + gas together.
- **Keyboard:** Arrow keys / WASD (Up/W = gas, Left-Right/A-D = steer).
- Normalized into a single `input = {gas, steer}` consumed by `moped.update`.

### 7. Game loop
- `requestAnimationFrame` loop with dt clamp.
- `update(dt)`: read input → `moped.update` → camera follow → `orders.update`
  (arrival checks, timer).
- `render()`: world → target marker + route arrow → moped → HUD → minimap →
  popup (if offered).
- Canvas resizes to viewport; DPR-aware for crisp mobile rendering.

## One-delivery flow

```
idle → (offer) → offered → [ACCEPT] → accepted (drive to restaurant)
   → enter restaurant radius → carrying (drive to customer)
   → enter customer radius → delivered (+$payout +timeBonus) → idle
[DECLINE] → idle ;  [timer 0] → failed → idle
```

## Art direction

- Vector shapes + emoji drawn on canvas. Moped = simple sprite (body + rider
  blob) or 🛵; restaurants = colored rounded blocks with food emoji sign +
  label; customer = 📍 pin. Roads gray with dashed center lines; ground a muted
  green/asphalt. Bright, readable, arcadey.

## Out of scope (YAGNI for v1)

Fuel/gas stations, tips system beyond a simple time bonus, multiple stacked
orders, moped upgrades, real 3D, sound/music, persistence/high-scores.

## Success criteria

- Loads `delivery.html` with no console errors, no external requests.
- Moped drives smoothly via touch on mobile and keyboard on desktop; camera
  follows; can't drive through buildings.
- Order popup appears; ACCEPT routes to restaurant, pickup routes to customer,
  delivery pays out and money increments; DECLINE and timeout both recover to a
  new offer.
- Route arrow + minimap correctly point at the active target throughout.
- Playable continuously (loop never soft-locks across many deliveries).
