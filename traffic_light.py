"""
Traffic Light Simulation (4-way junction) - Python + PyOpenGL
Keys: SPACE pause | R reset | D Lissajous demo | ESC quit
Lab 1: primitives | Lab 2: Bresenham circle | Lab 3: transformations | Lab 4: sin/cos
"""
import math, sys
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

W, H, WORLD = 1000, 800, 500.0
PHASES = [("H_GREEN", 8.0), ("H_YELLOW", 3.0), ("V_GREEN", 8.0), ("V_YELLOW", 3.0)]
STOP, CAR_HALF, GAP = 132.0, 25.0, 60.0     # stop-line distance, half car length, min gap
COLORS = [(0.2, 0.7, 1), (1, 0.65, 0.2), (0.35, 0.9, 0.45), (0.95, 0.35, 0.4),
          (0.95, 0.8, 0.25), (0.75, 0.5, 1), (0.25, 0.9, 0.8), (1, 0.45, 0.7)]

paused, demo = False, False
phase_i, phase_t, lis_t, last_ms = 0, 0.0, 0.0, 0
cars = []

def reset():                      # 8 cars: 2 per direction (h = horizontal, v = vertical)
    global cars, phase_i, phase_t, lis_t
    phase_i, phase_t, lis_t, cars = 0, 0.0, 0.0, []
    for axis in "hv":
        for d in (1, -1):
            for start in (440.0, 240.0):
                k = len(cars)
                cars.append({"axis": axis, "dir": d, "pos": -d * start,
                             "speed": 85 + 4 * k, "color": COLORS[k]})

# ---------- Lab 1 and Lab 2: primitives and Bresenham circle ----------
def rect(x, y, w, h, c):
    glColor3f(*c)
    glBegin(GL_QUADS)                                   # filled rectangle
    for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h)):
        glVertex2f(px, py)
    glEnd()

def circle(cx, cy, r, c):
    """Bresenham (midpoint) circle, filled with horizontal lines."""
    glColor3f(*c)
    x, y, d = 0, int(r), 3 - 2 * int(r)
    glBegin(GL_LINES)
    while x <= y:
        for a, b in ((x, y), (y, x)):                   # 8-way symmetry
            for sy in (b, -b):
                glVertex2f(cx - a, cy + sy)
                glVertex2f(cx + a, cy + sy)
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1
    glEnd()

def text(x, y, s, c=(1, 1, 1), font=GLUT_BITMAP_8_BY_13):
    glColor3f(*c)
    glRasterPos2f(x, y)
    for ch in s:
        glutBitmapCharacter(font, ord(ch))

def light(axis):                                         # 2 = green, 1 = yellow, 0 = red
    name = PHASES[phase_i][0]
    return (2 if "GREEN" in name else 1) if name.startswith(axis.upper()) else 0

def update_cars(dt):
    for c in cars:
        d = c["dir"]
        s = c["pos"] * d                                 # distance along travel direction
        # stop before the line when the light is not green
        at_line = light(c["axis"]) != 2 and -STOP - CAR_HALF <= s < -STOP
        # stop when the car in front is too close (queue)
        blocked = any(o is not c and o["axis"] == c["axis"] and o["dir"] == d
                      and 0 < o["pos"] * d - s < GAP for o in cars)
        if not (at_line or blocked):
            c["pos"] += d * c["speed"] * dt
        if c["pos"] * d > WORLD + 45:                    # re-enter from the other side
            c["pos"] = -d * (WORLD + 45)

def draw_road():
    rect(-WORLD, -WORLD, 2 * WORLD, 2 * WORLD, (0.12, 0.34, 0.18))      # grass
    rect(-WORLD, -115, 2 * WORLD, 230, (0.2, 0.21, 0.23))               # roads
    rect(-115, -WORLD, 230, 2 * WORLD, (0.2, 0.21, 0.23))
    for p in range(-480, 481, 60):                                      # dashed lines
        if abs(p) > 130:
            rect(p, -3, 30, 6, (0.92, 0.9, 0.7))
            rect(-3, p, 6, 30, (0.92, 0.9, 0.7))
    for x, y, w, h in [(-145, -86, 18, 82), (127, 4, 18, 82),           # stop lines
                       (4, -145, 82, 18), (-86, 127, 82, 18)]:
        rect(x, y, w, h, (0.95, 0.95, 0.95))
    for i in range(7):                                                  # zebra crossings
        o = -110 + i * 32
        for x, y, w, h in [(o, 118, 18, 10), (o, -128, 18, 10), (118, o, 10, 18), (-128, o, 10, 18)]:
            rect(x, y, w, h, (0.88, 0.88, 0.88))

def draw_signal(cx, cy, state):
    rect(cx - 23, cy - 55, 46, 110, (0.08, 0.08, 0.09))                 # housing
    for i, col in enumerate([(1, 0.08, 0.06), (1, 0.72, 0.05), (0.05, 0.95, 0.18)]):
        y = cy + 32 - 32 * i                                            # red, yellow, green
        circle(cx, y, 17, (0.05, 0.05, 0.06))
        on = state == i                                                 # lamp ON / OFF
        circle(cx, y, 12 if on else 10, col if on else tuple(0.25 * v for v in col))

def draw_car(c):
    # Lab 3: translate + rotate each car with its own matrix
    glPushMatrix()
    lane = (-45 if c["axis"] == "h" else 45) * c["dir"]
    if c["axis"] == "h":
        glTranslatef(c["pos"], lane, 0)
        glRotatef(0 if c["dir"] > 0 else 180, 0, 0, 1)
    else:
        glTranslatef(lane, c["pos"], 0)
        glRotatef(90 * c["dir"], 0, 0, 1)
    rect(-25, -12, 50, 24, c["color"])                                  # body
    rect(-3, -9, 15, 18, (0.65, 0.88, 0.98))                            # windshield
    for wx in (-15, 15):
        for wy in (-13, 13):
            circle(wx, wy, 5, (0.03, 0.03, 0.03))                       # wheels
    rect(21, -9, 4, 18, (1, 0.95, 0.55))                                # headlights
    glPopMatrix()

def draw_lissajous():
    rect(-WORLD, -WORLD, 2 * WORLD, 2 * WORLD, (0.03, 0.035, 0.09))
    glColor3f(0.3, 0.35, 0.48)
    glBegin(GL_LINES)                                                   # axes
    for v in ((-430, 0), (430, 0), (0, -350), (0, 350)):
        glVertex2f(*v)
    glEnd()
    glColor3f(0.15, 0.85, 1.0)
    glBegin(GL_LINE_STRIP)                                              # the curve
    for i in range(1800):
        t = i * 0.012
        glVertex2f(300 * math.sin(3 * t + math.pi / 2), 230 * math.sin(2 * t))
    glEnd()
    px = 300 * math.sin(3 * lis_t + math.pi / 2)                        # moving point
    py = 230 * math.sin(2 * lis_t)
    circle(px, py, 9, (1, 0.35, 0.25))
    text(-460, 455, "LISSAJOUS: x = A sin(3t + pi/2), y = B sin(2t)  (D = back)", font=GLUT_BITMAP_HELVETICA_18)

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    if demo:
        draw_lissajous()
    else:
        draw_road()
        for x, y, ax in ((-185, 165, "h"), (185, -165, "h"), (165, 185, "v"), (-165, -185, "v")):
            draw_signal(x, y, light(ax))
        for c in cars:
            draw_car(c)
        name = PHASES[phase_i][0]
        col = (0.2, 1, 0.3) if "GREEN" in name else ((1, 0.8, 0.1) if "YELLOW" in name else (1, 0.2, 0.2))
        left = max(0, math.ceil(PHASES[phase_i][1] - phase_t))
        text(-480, 465, "TRAFFIC LIGHT SIMULATION", font=GLUT_BITMAP_HELVETICA_18)
        text(-480, 435, "PHASE: %s | NEXT CHANGE IN: %d s" % (name.replace("_", " "), left), col)
        text(-480, -465, "SPACE: Pause  R: Reset  D: Lissajous  ESC: Quit" + ("  [PAUSED]" if paused else ""))
    glutSwapBuffers()

# ---------- GLUT callbacks ----------
def timer(_):
    global phase_i, phase_t, lis_t, last_ms
    now = glutGet(GLUT_ELAPSED_TIME)
    dt = min((now - (last_ms or now)) / 1000.0, 0.05)
    last_ms = now
    if not paused:
        lis_t += dt * 1.3
        if not demo:
            phase_t += dt
            if phase_t >= PHASES[phase_i][1]:                 # next signal phase
                phase_t, phase_i = 0.0, (phase_i + 1) % len(PHASES)
            update_cars(dt)
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

def keyboard(key, x, y):
    global paused, demo
    if key == b"\x1b":
        sys.exit(0)
    paused = not paused if key == b" " else paused
    demo = not demo if key in (b"d", b"D") else demo
    if key in (b"r", b"R"):
        reset()

def main():
    reset()
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(W, H)
    glutCreateWindow(b"Traffic Light Simulation - PyOpenGL")
    glMatrixMode(GL_PROJECTION)
    gluOrtho2D(-WORLD * 1.25, WORLD * 1.25, -WORLD, WORLD)   # 2D view
    glMatrixMode(GL_MODELVIEW)
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutTimerFunc(16, timer, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()