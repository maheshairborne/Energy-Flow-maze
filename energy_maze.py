import pygame, random, sys
from collections import deque

pygame.init()
clock = pygame.time.Clock()
FPS = 60

# Screen setup
SW, SH = 1280, 720
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Gryffindor Star Rebirth - Energy Flow Maze")

# Grid config
ROWS, COLS = 6, 6
PANEL_W = 400
CELL = min((SW - PANEL_W - 80) // COLS, (SH - 120) // ROWS)
GRID_W = CELL * COLS
GRID_H = CELL * ROWS
GRID_X = 40
GRID_Y = (SH - GRID_H) // 2

# Colors
BG = (18, 22, 30)
TILE_BG = (245, 245, 245)
LINE = (40, 40, 40)
ENERGY = (255, 210, 50)
PANEL_BG = (28, 30, 36)
TEXT = (230, 230, 230)
SW_ON = (50, 200, 50)
SW_OFF = (200, 70, 70)
RES_COLOR = (200, 140, 60)
CAP_COLOR = (80, 150, 220)
SRC_COLOR = (60, 140, 255)
LED_OFF = (120, 60, 160)
LED_ON = (255, 200, 80)
PROGRESS_BG = (60, 60, 60)
PROGRESS_FG = (255, 255, 150)


# Fonts
FONT = pygame.font.SysFont("consolas", 18)
SMALL_FONT = pygame.font.SysFont("consolas", 14)
BIG = pygame.font.SysFont("consolas", 26, bold=True)

# Directions bits (for tile masks)
N, E, S, W = 1, 2, 4, 8
# DIRS entries: (dr, dc, BIT_FROM_NEIGHBOR_TO_THIS, BIT_FROM_THIS_TO_NEIGHBOR)
DIRS = [(-1, 0, N, S), (0, 1, E, W), (1, 0, S, N), (0, -1, W, E)]

# Tile base masks (two tile shapes: straight and corner)
TILE_BASE = {
    'straight': N | S,
    'corner'  : N | E
}

# Components
COMP_NONE = None
COMP_SWITCH = 'switch'
COMP_RES = 'resistor'
COMP_CAP = 'capacitor'
COMP_POOL = [COMP_NONE, COMP_NONE, COMP_SWITCH, COMP_RES, COMP_CAP]

# Board state
grid_type = [[None]*COLS for _ in range(ROWS)]
grid_rot = [[0]*COLS for _ in range(ROWS)]
grid_comp = [[COMP_NONE]*COLS for _ in range(ROWS)]
switch_state = {}

# Source and LED positions
SRC = (0, 0)
LED = (ROWS-1, COLS-1)

# UI
PANEL_X = GRID_X + GRID_W + 20
BUTTON_RECT = pygame.Rect(PANEL_X + PANEL_W - 140, GRID_Y + 12, 120, 42)

# Flow state
flow_active = False
flow_path = []
flow_index = 0
flow_timer = 0.0
led_lit = False

# Energized tiles (map (r,c) -> bool). Only set True when tile has been passed (or source pre-energized).
energized_state = {}

# Messages
message = ""
msg_timer = 0.0

# Flow constants
BASE_FLOW_SPEED = 0.15
RESISTOR_DELAY_MULTIPLIER = 3.0
CAPACITOR_CHARGE_TIME = 1.2  # seconds

# Sparks for LED effect
sparks = []

# ----------------- Utility helpers -----------------
def rotated_mask(mask, rot):
    rot %= 4
    m = mask
    for _ in range(rot):
        m = ((m << 1) & 0b1111) | ((m >> 3) & 1)
    return m

def tile_mask(rtype, rot):
    return rotated_mask(TILE_BASE[rtype], rot)

def carve_path():
    """Generate a random path from SRC to LED (biased to target)."""
    sx, sy = SRC
    tx, ty = LED
    path = [(sx, sy)]
    visited = set(path)
    x, y = sx, sy
    while (x, y) != (tx, ty):
        options = []
        # bias towards target
        if x < tx: options.append((x+1, y))
        if x > tx: options.append((x-1, y))
        if y < ty: options.append((x, y+1))
        if y > ty: options.append((x, y-1))
        # add other neighbors for randomness
        for nx, ny in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
            if 0 <= nx < ROWS and 0 <= ny < COLS and (nx, ny) not in visited:
                options.append((nx, ny))
        if not options:
            break
        nx, ny = random.choice(options)
        path.append((nx, ny))
        visited.add((nx, ny))
        x, y = nx, ny
    return path

def mask_to_tile(mask):
    for t, base in TILE_BASE.items():
        for r in range(4):
            if rotated_mask(base, r) == mask:
                return t, r
    return 'straight', 0

def new_puzzle():
    global grid_type, grid_rot, grid_comp, switch_state, flow_active, flow_path, flow_index, flow_timer, led_lit, message, msg_timer, energized_state
    flow_active = False
    flow_path = []
    flow_index = 0
    flow_timer = 0.0
    led_lit = False
    message = ""
    msg_timer = 0.0
    switch_state.clear()
    energized_state.clear()

    grid_type = [[None]*COLS for _ in range(ROWS)]
    grid_rot  = [[0]*COLS for _ in range(ROWS)]
    grid_comp = [[COMP_NONE]*COLS for _ in range(ROWS)]

    path = carve_path()
    path_set = set(path)

    for i, (r, c) in enumerate(path):
        prev = path[i-1] if i>0 else None
        nxt  = path[i+1] if i < len(path)-1 else None
        mask = 0
        if prev:
            pr, pc = prev
            if pr == r-1: mask |= N
            if pr == r+1: mask |= S
            if pc == c-1: mask |= W
            if pc == c+1: mask |= E
        if nxt:
            nr, nc = nxt
            if nr == r-1: mask |= N
            if nr == r+1: mask |= S
            if nc == c-1: mask |= W
            if nc == c+1: mask |= E
        ttype, trot = mask_to_tile(mask)
        grid_type[r][c] = ttype
        grid_rot[r][c] = trot
        if (r,c) not in (SRC, LED):
            comp = random.choice(COMP_POOL)
            # ensure we don't accidentally leave None on-path
            while comp is None:
                comp = random.choice(COMP_POOL)
            grid_comp[r][c] = comp
            if comp == COMP_SWITCH:
                switch_state[(r,c)] = random.choice([True, False])

    # fill the rest with random wires (no components)
    for r in range(ROWS):
        for c in range(COLS):
            if (r,c) in path_set:
                continue
            attempts = 0
            while True:
                ttype = random.choice(list(TILE_BASE.keys()))
                trot = random.randrange(4)
                m = tile_mask(ttype, trot)
                collides = False
                # reduce chance of accidental connection into path
                for dr, dc, out_bit, _ in DIRS:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and (nr,nc) in path_set:
                        if m & out_bit:
                            collides = True
                            break
                attempts += 1
                if not collides or attempts > 10:
                    break
            grid_type[r][c] = ttype
            grid_rot[r][c] = trot
            grid_comp[r][c] = COMP_NONE

    # scramble rotations
    for r in range(ROWS):
        for c in range(COLS):
            grid_rot[r][c] = (grid_rot[r][c] + random.randrange(4)) % 4

def cells_connected(r1, c1, r2, c2):
    if not (0 <= r2 < ROWS and 0 <= c2 < COLS): return False
    t1 = grid_type[r1][c1]; t2 = grid_type[r2][c2]
    if t1 is None or t2 is None: return False
    m1 = tile_mask(t1, grid_rot[r1][c1])
    m2 = tile_mask(t2, grid_rot[r2][c2])
    dr = r2 - r1; dc = c2 - c1
    if dr == -1 and dc == 0: return (m1 & N) and (m2 & S)
    if dr == 1 and dc == 0:  return (m1 & S) and (m2 & N)
    if dr == 0 and dc == -1: return (m1 & W) and (m2 & E)
    if dr == 0 and dc == 1:  return (m1 & E) and (m2 & W)
    return False

def find_connected_path():
    sr, sc = SRC
    tr, tc = LED
    q = deque()
    q.append((sr, sc))
    parent = {(sr, sc): None}
    while q:
        r, c = q.popleft()
        if (r, c) == (tr, tc):
            path = []
            cur = (tr, tc)
            while cur:
                path.append(cur)
                cur = parent[cur]
            path.reverse()
            return path
        for dr, dc, _, _ in DIRS:
            nr, nc = r+dr, c+dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in parent:
                if cells_connected(r, c, nr, nc):
                    parent[(nr, nc)] = (r, c)
                    q.append((nr, nc))
    return None

# ---------------- Drawing ----------------
def draw_progress_bar(r, c, progress):
    x = GRID_X + c*CELL
    y = GRID_Y + r*CELL
    bar_w = CELL - 16
    bar_h = 8
    bar_x = x + 8
    bar_y = y + 8
    pygame.draw.rect(screen, PROGRESS_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    fg_w = int(bar_w * progress)
    pygame.draw.rect(screen, PROGRESS_FG, (bar_x, bar_y, fg_w, bar_h), border_radius=4)

def draw_tile(r, c, energized=False, flow_progress=0):
    x = GRID_X + c*CELL
    y = GRID_Y + r*CELL
    rect = pygame.Rect(x, y, CELL, CELL)
    pygame.draw.rect(screen, TILE_BG, rect)
    pygame.draw.rect(screen, LINE, rect, 2)
    ttype = grid_type[r][c]
    if ttype is None:
        return
    rot = grid_rot[r][c]
    mask = tile_mask(ttype, rot)
    center = (x + CELL//2, y + CELL//2)
    thick = max(4, CELL//12)
    col = ENERGY if energized else LINE

    # connectors
    if mask & N:
        pygame.draw.rect(screen, col, (center[0]-thick//2, y+6, thick, CELL//2 - 10))
    if mask & S:
        pygame.draw.rect(screen, col, (center[0]-thick//2, center[1], thick, CELL//2 - 10))
    if mask & E:
        pygame.draw.rect(screen, col, (center[0], center[1]-thick//2, CELL//2 - 10, thick))
    if mask & W:
        pygame.draw.rect(screen, col, (x+6, center[1]-thick//2, CELL//2 - 10, thick))
    pygame.draw.circle(screen, col, center, thick+2)

    if energized:
        glow = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        pygame.draw.rect(glow, (255, 240, 120, 30), (0,0,CELL,CELL))
        screen.blit(glow, (x,y))

    comp = grid_comp[r][c]
    if comp == COMP_SWITCH:
        sw = switch_state.get((r,c), False)
        pygame.draw.circle(screen, SW_ON if sw else SW_OFF, (center[0], center[1] - CELL//6), CELL//12)
        label = SMALL_FONT.render("Switch", True, LINE)
        screen.blit(label, (x + (CELL - label.get_width())//2, y + CELL - 22))
    elif comp == COMP_RES:
        points = []
        left = x + CELL//4
        right = x + 3*CELL//4
        mid_y = y + CELL//2
        step = max(1, (right - left) // 6)
        for i in range(7):
            px = left + i*step
            py = mid_y + (CELL//8 if i % 2 == 0 else -CELL//8)
            points.append((px, py))
        pygame.draw.lines(screen, RES_COLOR, False, points, 3)
        draw_progress_bar(r, c, flow_progress)
        label = SMALL_FONT.render("Resistor", True, LINE)
        screen.blit(label, (x + (CELL - label.get_width())//2, y + CELL - 22))
    elif comp == COMP_CAP:
        cx = x + CELL//2
        cy = y + CELL//2
        pygame.draw.line(screen, CAP_COLOR, (cx-10, cy-12), (cx-10, cy+12), 4)
        pygame.draw.line(screen, CAP_COLOR, (cx+10, cy-12), (cx+10, cy+12), 4)
        draw_progress_bar(r, c, flow_progress)
        label = SMALL_FONT.render("Capacitor", True, LINE)
        screen.blit(label, (x + (CELL - label.get_width())//2, y + CELL - 22))


def draw_source_and_led(led_on):
    sr, sc = SRC
    cx = GRID_X + sc*CELL + CELL//2
    cy = GRID_Y + sr*CELL + CELL//2
    pygame.draw.circle(screen, SRC_COLOR, (cx, cy), CELL//4)
    stxt = FONT.render("Battery", True, LINE)
    screen.blit(stxt, (cx - stxt.get_width()//2, cy + CELL//4))

    lr, lc = LED
    cx2 = GRID_X + lc*CELL + CELL//2
    cy2 = GRID_Y + lr*CELL + CELL//2
    pygame.draw.circle(screen, LED_ON if led_on else LED_OFF, (cx2, cy2), CELL//4)
    ltxt = FONT.render("LED", True, LINE)
    screen.blit(ltxt, (cx2 - ltxt.get_width()//2, cy2 + CELL//4))

def draw_panel():
    pygame.draw.rect(screen, PANEL_BG, (PANEL_X, GRID_Y, PANEL_W, GRID_H))
    title = BIG.render("Legend & Controls", True, TEXT)
    screen.blit(title, (PANEL_X + 12, GRID_Y + 12))

    pygame.draw.rect(screen, (40, 100, 200), BUTTON_RECT, border_radius=8)
    btxt = BIG.render("START", True, (240, 240, 240))
    screen.blit(btxt, (BUTTON_RECT.centerx - btxt.get_width()//2, BUTTON_RECT.centery - btxt.get_height()//2))

    y = GRID_Y + 60
    items = [
        ("Battery", SRC_COLOR, "Source of energy"),
        ("LED (goal)", LED_OFF, "Lights when powered"),
        ("Switch", SW_ON, "Toggle ON/OFF to allow flow"),
        ("Resistor", RES_COLOR, "Slows energy flow"),
        ("Capacitor", CAP_COLOR, "Charges before passing"),
        ("Wires", LINE, "Rotate to connect"),
    ]
    for name, col, desc in items:
        pygame.draw.rect(screen, col, (PANEL_X + 18, y, 22, 18), border_radius=4)
        n = FONT.render(name, True, TEXT)
        d = SMALL_FONT.render(desc, True, TEXT)
        screen.blit(n, (PANEL_X + 48, y))
        screen.blit(d, (PANEL_X + 48, y + 20))
        y += 48

    if message:
        mcol = (50, 220, 120) if "Success" in message else (240, 100, 100)
        msg_surf = BIG.render(message, True, mcol)
        screen.blit(msg_surf, (PANEL_X + 12, GRID_Y + GRID_H - 250))

    ctitle = BIG.render("Instructions", True, TEXT)
    screen.blit(ctitle, (PANEL_X + 12, GRID_Y + GRID_H - 210))

    controls = [
        "Left Click: Rotate tile CW",
        "Right Click on Switch: Toggle ON/OFF",
        "Right Click on Wire: Rotate CCW",
        "Start Button: Test circuit flow",
        "R Key: Restart puzzle",
        "ESC: Quit game"
    ]
    y2 = GRID_Y + GRID_H - 180
    for line in controls:
        ctl_surf = SMALL_FONT.render(line, True, TEXT)
        screen.blit(ctl_surf, (PANEL_X + 18, y2))
        y2 += 26

def pos_to_cell(mx, my):
    if mx < GRID_X or my < GRID_Y:
        return None
    rx, ry = mx - GRID_X, my - GRID_Y
    c = rx // CELL
    r = ry // CELL
    if 0 <= r < ROWS and 0 <= c < COLS:
        return (r, c)
    return None

def start_flow():
    global message, msg_timer
    path = find_connected_path()
    if not path:
        message = "Circuit incomplete! No full connection."
        msg_timer = 2.5
        return False, None
    # check switches
    for (r,c) in path:
        if grid_comp[r][c] == COMP_SWITCH and not switch_state.get((r,c), False):
            message = "Switch is OFF! Open the circuit."
            msg_timer = 2.5
            return False, None
    return True, path

def begin_flow(path):
    global flow_active, flow_path, flow_index, flow_timer, led_lit, message, msg_timer, energized_state
    flow_active = True
    flow_path = path
    flow_index = 0
    flow_timer = 0.0
    led_lit = False
    message = "Energy flowing..."
    msg_timer = 2.0
    energized_state.clear()
    # mark source energized immediately so first gate sees input
    energized_state[SRC] = True

def toggle_switch(r, c):
    if (r,c) in switch_state:
        switch_state[(r,c)] = not switch_state[(r,c)]

def flow_update(dt):
    global flow_index, flow_timer, flow_active, led_lit, message, msg_timer

    if not flow_active:
        return

    # If finished
    if flow_index >= len(flow_path):
        flow_active = False
        led_lit = True
        message = "Success! Star vitality restored!"
        msg_timer = 3.0
        sparks.append([GRID_X + LED[1]*CELL + CELL//2, GRID_Y + LED[0]*CELL + CELL//2, 15])
        return

    r, c = flow_path[flow_index]
    comp = grid_comp[r][c]

    # Normal components
    base_delay = BASE_FLOW_SPEED
    delay = base_delay
    charging = False

    if comp == COMP_RES:
        delay = base_delay * RESISTOR_DELAY_MULTIPLIER
    elif comp == COMP_CAP:
        if flow_timer < CAPACITOR_CHARGE_TIME:
            charging = True
            flow_timer += dt
            return
        else:
            delay = base_delay

    flow_timer += dt
    if flow_timer >= delay and not charging:
        energized_state[(r, c)] = True
        flow_timer = 0
        flow_index += 1

def draw_energy_flow():
    if not flow_active and not led_lit and not energized_state:
        return
    for (r, c), val in list(energized_state.items()):
        if val:
            x = GRID_X + c*CELL + CELL//2
            y = GRID_Y + r*CELL + CELL//2
            pygame.draw.circle(screen, ENERGY, (x, y), CELL//7)
    if flow_active:
        for i in range(flow_index):
            if i < len(flow_path):
                r, c = flow_path[i]
                x = GRID_X + c*CELL + CELL//2
                y = GRID_Y + r*CELL + CELL//2
                pygame.draw.circle(screen, ENERGY, (x, y), CELL//7)

def draw_sparks():
    for s in sparks[:]:
        x, y, timer = s
        alpha = max(0, int(255 * (timer / 15)))
        size = max(3, int(timer))
        surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 150, alpha), (size, size), size)
        screen.blit(surf, (x - size, y - size))
        s[2] -= 1
        if s[2] <= 0:
            sparks.remove(s)

def reset_flow():
    global flow_active, flow_path, flow_index, flow_timer, led_lit, energized_state
    flow_active = False
    flow_path = []
    flow_index = 0
    flow_timer = 0
    led_lit = False
    energized_state.clear()

def main():
    global message, msg_timer

    new_puzzle()

    running = True
    while running:
        dt = clock.tick(FPS)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    new_puzzle()
                    reset_flow()
                    message = "Game restarted!"
                    msg_timer = 2.0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pos_to_cell(*event.pos)
                if BUTTON_RECT.collidepoint(event.pos) and not flow_active:
                    ok, path = start_flow()
                    if ok:
                        begin_flow(path)
                elif pos and not flow_active:
                    r, c = pos
                    comp = grid_comp[r][c]
                    if event.button == 1:
                        grid_rot[r][c] = (grid_rot[r][c] + 1) % 4
                    elif event.button == 3:
                        if comp == COMP_SWITCH:
                            toggle_switch(r, c)
                        else:
                            grid_rot[r][c] = (grid_rot[r][c] - 1) % 4

        if msg_timer > 0:
            msg_timer -= dt
            if msg_timer <= 0:
                message = ""

        flow_update(dt)

        screen.fill(BG)
        for r in range(ROWS):
            for c in range(COLS):
                energized = False
                if energized_state.get((r, c), False):
                    energized = True
                elif flow_active and flow_index > 0 and (r, c) in flow_path[:flow_index]:
                    energized = True

                progress = 0.0
                if flow_active and flow_index < len(flow_path):
                    cur = flow_path[flow_index]
                    if (r, c) == cur:
                        comp = grid_comp[r][c]
                        if comp == COMP_RES:
                            progress = min(1.0, flow_timer / (BASE_FLOW_SPEED * RESISTOR_DELAY_MULTIPLIER))
                        elif comp == COMP_CAP:
                            progress = min(1.0, flow_timer / CAPACITOR_CHARGE_TIME)
                        else:
                            progress = min(1.0, flow_timer / BASE_FLOW_SPEED)

                draw_tile(r, c, energized, progress)

        draw_energy_flow()
        draw_source_and_led(led_lit)
        draw_panel()
        draw_sparks()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
