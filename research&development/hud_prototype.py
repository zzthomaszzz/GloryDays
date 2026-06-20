"""
HUD Prototype Sandbox
─────────────────────────────────────────────────────────────────────────────
Draw your UI layout here using pygame.draw.rect() / blit() calls.
When you're happy, tell Claude — it will translate the rects into client/hud.py.

HOW TO USE
  1. Run:  python "research&development/hud_prototype.py"
  2. Add rects in the section marked ══ DRAW YOUR RECTS HERE ══
  3. Save → the window auto-updates each loop (keep it open, edit, save, re-run)
  4. ESC or close window to quit

HELPER COLOURS (copy-paste as needed)
  Dark panel bg   : (10, 11, 20)
  Panel border    : (24, 26, 42)
  Ability slot    : (16, 17, 28)
  Gold text       : (188, 158, 48)
  HP green        : (38, 168, 58)
  Mana blue       : (32, 98, 215)
  Team blue       : (60, 100, 220)
  Team red        : (220, 60, 60)
  White text      : (210, 210, 222)
  Minimap ground  : (30, 35, 40)

REFERENCE SIZES FROM THE REAL GAME
  SW, SH              = 1920, 1080   — screen
  MINI_W, MINI_H      = 240, 150     — minimap
  ABILITY_SLOT_SZ     = 72           — ability slot (Q/E/R)
  INVENTORY_SLOT_SZ   = 32           — item slot
  RECALL_SLOT_SZ      = 18           — recall mini-slot (B)
  SHOP_BTN_W/H        = 42 × 32      — shop button

CURRENT PANEL GEOMETRY (ghost shapes drawn automatically below)
  panel_w ≈ 536, panel_h = 100
  panel_x = SW//2 - 268 = 692,  panel_y = SH - 100 = 980
  minimap  at (8, 922)
  HP bar   at (692, 953, 536, 12)
  Mana bar at (692, 968, 536, 7)
"""

import pygame
import sys
import os

#──────────────────────────────────────────────────────────────── constants ──
SW, SH = 1920, 1080

MINI_W, MINI_H      = 240, 150
ABILITY_SLOT_SZ     = 72
INVENTORY_SLOT_SZ   = 32
RECALL_SLOT_SZ      = 18
SHOP_BTN_W, SHOP_BTN_H = 42, 32

TEAM_BLUE = (60, 100, 220)
TEAM_RED  = (220, 60, 60)

ASSET_DIR = os.path.join(os.path.dirname(__file__), '..', 'asset')

#──────────────────────────────────────────────────────────────── ghost rects (current layout, dimmed) ──
# These match the real game's current positions.
# They render as dim outlines so you have a reference baseline.
# You do NOT need to keep them — they're read-only context.

_PANEL_W = 536
_PANEL_H = 100
_PANEL_X = SW // 2 - _PANEL_W // 2   # 692
_PANEL_Y = SH - _PANEL_H             # 980
_BARS_H  = 27                         # HP + gap + mana + bot

_GHOST = [
    # label              rect                                            colour
    ("minimap",          pygame.Rect(8, SH - MINI_H - 8, MINI_W, MINI_H),              (40, 44, 60)),
    ("panel bg",         pygame.Rect(_PANEL_X, _PANEL_Y, _PANEL_W, _PANEL_H),          (28, 30, 44)),
    ("HP+mana bars",     pygame.Rect(_PANEL_X, _PANEL_Y - _BARS_H, _PANEL_W, _BARS_H), (28, 30, 44)),
    ("gold section",     pygame.Rect(_PANEL_X + 14, _PANEL_Y + 10, 76, ABILITY_SLOT_SZ), (38, 36, 22)),
    ("ability Q",        pygame.Rect(_PANEL_X + 14 + 76 + 12,           _PANEL_Y + 10, ABILITY_SLOT_SZ, ABILITY_SLOT_SZ), (28, 26, 18)),
    ("ability E",        pygame.Rect(_PANEL_X + 14 + 76 + 12 + 78,      _PANEL_Y + 10, ABILITY_SLOT_SZ, ABILITY_SLOT_SZ), (28, 26, 18)),
    ("ability R",        pygame.Rect(_PANEL_X + 14 + 76 + 12 + 156,     _PANEL_Y + 10, ABILITY_SLOT_SZ, ABILITY_SLOT_SZ), (28, 26, 18)),
    ("inv 3×2 grid",     pygame.Rect(_PANEL_X + 14 + 76 + 12 + 216 + 14 + 14, _PANEL_Y + 10 + (ABILITY_SLOT_SZ - (2*INVENTORY_SLOT_SZ+4))//2, 3*INVENTORY_SLOT_SZ + 2*4, 2*INVENTORY_SLOT_SZ + 4), (22, 28, 22)),
    ("shop btn",         pygame.Rect(_PANEL_X + _PANEL_W - 14 - 18 - 8 - SHOP_BTN_W - 14, _PANEL_Y + 10 + ABILITY_SLOT_SZ - SHOP_BTN_H, SHOP_BTN_W, SHOP_BTN_H), (22, 24, 34)),
    ("recall slot",      pygame.Rect(_PANEL_X + _PANEL_W - 14 - RECALL_SLOT_SZ, _PANEL_Y + 10 + (ABILITY_SLOT_SZ - RECALL_SLOT_SZ)//2, RECALL_SLOT_SZ, RECALL_SLOT_SZ), (16, 22, 34)),
]


#──────────────────────────────────────────────────────────────── setup ──────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SW, SH))
    pygame.display.set_caption("HUD Prototype  |  ESC to quit")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("consolas", 11)

    # Load map background
    try:
        raw = pygame.image.load(os.path.join(ASSET_DIR, "map.png")).convert()
        map_bg = pygame.transform.scale(raw, (SW, SH))
    except Exception:
        map_bg = pygame.Surface((SW, SH))
        map_bg.fill((24, 32, 18))   # fallback dark green

    # Darken map so UI stands out
    dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 110))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        # ── Background: map ──────────────────────────────────────────────────
        screen.blit(map_bg, (0, 0))
        screen.blit(dim, (0, 0))

        # ── UI overlay (transparent) ─────────────────────────────────────────
        ui = pygame.Surface((SW, SH), pygame.SRCALPHA)

        # Ghost shapes — current layout reference (dim outlines)
        for label, rect, col in _GHOST:
            pygame.draw.rect(ui, col, rect)
            pygame.draw.rect(ui, (60, 65, 90), rect, 1)
            lbl = font.render(label, True, (60, 65, 90))
            ui.blit(lbl, (rect.x + 2, rect.y + 2))

        # ════════════════════════════════════════════════════════════════════
        #  DRAW YOUR RECTS BELOW  ↓ ↓ ↓
        #
        #  Example:
        #    pygame.draw.rect(ui, (10, 11, 20, 200), pygame.Rect(x, y, w, h))
        #    pygame.draw.rect(ui, (55, 65, 98),       pygame.Rect(x, y, w, h), 1)
        #
        #  Tips:
        #   - 4-tuple colours include alpha:   (R, G, B, A)  where A=0 transparent, 255 opaque
        #   - 3-tuple colours are fully opaque: (R, G, B)
        #   - Use SW, SH, MINI_W, MINI_H, ABILITY_SLOT_SZ, etc. instead of raw numbers
        #     so your rects scale correctly if the resolution ever changes
        # ════════════════════════════════════════════════════════════════════



        # ════════════════════════════════════════════════════════════════════

        screen.blit(ui, (0, 0))

        # Tiny helper overlay: mouse coords
        mx, my = pygame.mouse.get_pos()
        coord_s = font.render(f"({mx}, {my})", True, (120, 120, 140))
        screen.blit(coord_s, (SW - coord_s.get_width() - 8, 4))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
