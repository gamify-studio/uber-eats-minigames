# Delivery Moped Game — 3D Version Design Spec

**Date:** 2026-06-02
**Status:** Approved (design), pre-implementation
**Builds on:** [2026-06-02-delivery-moped-game-design.md](2026-06-02-delivery-moped-game-design.md)

## Concept

3D third-person version of the delivery moped game, matching the original
reference screenshots (chase camera behind the moped, low-poly city). The
**core loop is unchanged** from the 2D v1 — accept order → ride to restaurant →
deliver to customer → earn cash, beat the timer. Only the rendering and camera
change from top-down 2D canvas to 3D WebGL.

## Locked scope decisions

- **File:** New `delivery3d.html` at repo root. The 2D `delivery.html` stays.
- **Engine:** Three.js r160, loaded as an ES module from the jsdelivr CDN
  (`https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js`).
  Accepts one external request + internet at runtime (chosen over vendoring).
- **Camera:** Third-person chase only (no first-person toggle).
- **Reuse:** All HTML/CSS overlays (start, popup, HUD, banner, touch buttons,
  minimap canvas) and the order FSM logic are reused from the 2D version.

## Coordinate mapping

The 2D world used `(x, y)` on a `TILE=120`, `COLS=14`, `ROWS=14` grid
(`WORLD = 1680 × 1680`). In 3D the same grid maps to the **XZ plane**: world
`x → scene x`, world `y → scene z`. Height is `+y` (up). All grid/restaurant/
customer/collision math is preserved; only the axis name changes.

## Systems

### 1. Scene + ground (baked texture)
- `THREE.Scene` with sky-blue background and exponential fog for depth.
- Lights: `HemisphereLight` (sky/ground fill) + one `DirectionalLight` (sun).
- **Ground:** a single `PlaneGeometry` sized to the world, rotated flat, with a
  `CanvasTexture` baked once at load: paint grass base, gray road bands along
  every gridline, and dashed yellow lane lines (reusing the 2D road-drawing
  approach). One draw call for the whole street grid — efficient and readable.

### 2. Buildings
- For each interior block of the grid, an extruded box (`BoxGeometry`) with a
  randomized height (e.g. 40–160) and a color from the building palette, placed
  on the block center. Merged into as few meshes as practical (≤ ~196 boxes is
  fine as individual meshes; merge if perf requires).
- **Restaurants:** the 8 picked blocks get a distinct building plus a floating
  emoji **billboard** (`Sprite` from a per-emoji CanvasTexture) hovering above,
  always facing the camera, with a name label.

### 3. Moped (player)
- Low-poly model assembled from primitives under a parent `Group`: body box,
  seat, two wheel cylinders, handlebar, red delivery box (with a "D"/emoji
  texture), and a simple rider (capsule/sphere stack).
- **Physics (XZ plane), identical arcade model to 2D:** `speed` integrates along
  `heading` (yaw); gas accelerates, brake/friction decelerate, steer rotates yaw
  with speed-scaled authority. Per-axis AABB **soft collision** against building
  footprints (reuse `blockAt(x, z, pad)`); clamp inside world bounds.
- The `Group` is positioned at `(x, ~0, z)` and rotated `rotation.y = -heading`
  (sign chosen so visual facing matches travel direction).

### 4. Chase camera
- Each frame compute a desired camera position behind + above the moped:
  `desired = mopedPos − forward * DIST + up * HEIGHT`, then `camera.position`
  lerps toward `desired` for smooth follow. `camera.lookAt` a point slightly
  ahead of the moped. Tuned so the moped sits lower-center like the reference.

### 5. Order FSM
- Reused verbatim from 2D (`idle → offered → accepted → carrying →
  delivered/failed`), operating on `(x, z)`. `offer()`, `accept()`, `decline()`,
  `deliver()` (payout + `timeBonus`), `fail()`, `target()` unchanged in spirit.

### 6. Nav markers (3D)
- **Target beam:** a tall, semi-transparent colored cylinder rising from the
  target point so it's visible over buildings; gently pulsing scale/opacity.
  Orange while heading to pickup, green while carrying to dropoff. A pin/emoji
  sprite sits at its base.
- **Direction arrow:** a floating arrow sprite/mesh above the moped that yaws to
  point toward the active target (helps when the beam is off-screen).

### 7. HUD / popup / start / touch / minimap
- DOM overlays reused unchanged. The **minimap** is the same 2D `<canvas>`
  overlay, drawn each frame from world `(x, z)` → minimap pixels, showing
  restaurants, target, and player.

### 8. Loop
- `requestAnimationFrame`; `update(dt)` (clamped dt): read input → moped physics
  + collision → camera follow → `orders.update` → sync DOM/minimap. `render()`:
  `renderer.render(scene, camera)` then draw minimap canvas.
- `WebGLRenderer` resizes with the viewport; `pixelRatio` capped at 2.

## Out of scope (v1 of 3D)

First-person view, dynamic shadows beyond a basic setup, traffic/AI cars,
fuel/upgrades, sound, persistence.

## Success criteria

- `delivery3d.html` loads Three.js from CDN, renders a 3D city with no console
  errors.
- Chase camera follows the moped smoothly; moped drives via touch + keyboard and
  cannot pass through buildings or leave the world.
- Order popup → accept routes to the restaurant (beam/arrow), pickup flips to the
  customer, delivery pays out and money increments; decline + timeout recover.
- Minimap + direction arrow track the active target; playable continuously.
