"""
ROCKBOT - La fortaleza del Dr. Malvex
Juego de acción y plataformas de desplazamiento lateral inspirado en los clásicos
de robots: elige un nivel, derrota al jefe, copia su arma y úsala contra el siguiente.

Requisitos:  pip install pygame
Ejecutar:    python rockbot.py

Controles
  Mover ........ flechas o A / D
  Saltar ....... ESPACIO, W, flecha arriba o K
  Disparar ..... X, J o Z   (mantén pulsado con el Buster para cargar el disparo)
  Cambiar arma . Q / E  o  teclas 1-7
  Pausa ........ P        Sonido ... M        Pantalla completa ... F11

Novedades de esta versión
  - Los jefes se muestran en la pantalla de título, en la selección de misión
    (retrato animado, arma, nivel y punto débil), en el aviso previo al combate,
    en el HUD y en la pantalla de victoria.
  - Brillos aditivos en disparos, explosiones y jefes, viñeta, paneles de HUD,
    fondos temáticos en las tarjetas y baldosas con más relieve.
"""
import math
import random
import sys
from array import array

import pygame

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

# ---------------------------------------------------------------- Ajustes
TS = 32                                # tamaño de cada baldosa
ANCHO, ALTO = 960, 544
FILAS = ALTO // TS                     # 17
COLS_PANTALLA = ANCHO // TS            # 30
FPS = 60

VEL = 3.4
GRAV = 0.6
SALTO = -12.2
CAIDA_MAX = 13
HP_MAX = 28
FRAMES_COYOTE = 6
FRAMES_BUFFER = 6
MAX_BALAS = 3

K_IZQ = (pygame.K_LEFT, pygame.K_a)
K_DER = (pygame.K_RIGHT, pygame.K_d)
K_SALTO = (pygame.K_SPACE, pygame.K_UP, pygame.K_w, pygame.K_k)
K_DISP = (pygame.K_x, pygame.K_j, pygame.K_z)

BLANCO = (255, 255, 255)
NEGRO = (20, 20, 28)
ROJO = (225, 60, 60)
AMARILLO = (255, 215, 40)
PIEL = (255, 208, 165)
GRIS = (90, 92, 105)
AZUL = (60, 140, 255)
VERDE = (70, 210, 100)
CLAVE = (255, 0, 255)

# Tamaño de las tarjetas de la selección de misión
TARJ_W, TARJ_H = 270, 150

# ---------------------------------------------------------------- Datos
IDS = ["fuego", "hielo", "rayo", "viento", "tierra", "bomba"]
JEFES = [
    {"id": "fuego", "nombre": "PIRO", "arma": "LLAMARADA", "color": (240, 120, 30), "oscuro": (150, 60, 20)},
    {"id": "hielo", "nombre": "GLACIO", "arma": "RAYO GÉLIDO", "color": (130, 210, 245), "oscuro": (60, 120, 175)},
    {"id": "rayo", "nombre": "VOLTIO", "arma": "CHISPA", "color": (250, 220, 50), "oscuro": (150, 120, 20)},
    {"id": "viento", "nombre": "AEROS", "arma": "CUCHILLA", "color": (110, 220, 130), "oscuro": (50, 130, 70)},
    {"id": "tierra", "nombre": "TERRÓN", "arma": "ROCA", "color": (190, 140, 80), "oscuro": (110, 75, 40)},
    {"id": "bomba", "nombre": "BOMBARDO", "arma": "BOMBA", "color": (225, 60, 75), "oscuro": (120, 30, 40)},
]
# Cada jefe es débil al arma del siguiente (en círculo)
for _i, _d in enumerate(JEFES):
    _d["debil"] = IDS[(_i + 1) % len(IDS)]

COSTE = {"fuego": 1, "hielo": 1, "rayo": 2, "viento": 1, "tierra": 2, "bomba": 2}
ARMAS = {"buster": {"nombre": "BUSTER", "color": AZUL, "coste": 0}}
for _d in JEFES:
    ARMAS[_d["id"]] = {"nombre": _d["arma"], "color": _d["color"], "coste": COSTE[_d["id"]]}

# Un tema visual por nivel (los 6 jefes + la fortaleza)
TEMAS = [
    {"nombre": "Volcán", "cielo": ((60, 15, 15), (230, 110, 40)), "capas": ((110, 35, 30), (80, 25, 25)),
     "tile": ((210, 100, 45), (115, 52, 36), (62, 26, 22)), "amb": "brasas"},
    {"nombre": "Glaciar", "cielo": ((120, 180, 235), (225, 245, 255)), "capas": ((170, 210, 235), (130, 180, 215)),
     "tile": ((235, 250, 255), (140, 190, 225), (80, 130, 175)), "amb": "nieve"},
    {"nombre": "Central Eléctrica", "cielo": ((20, 15, 50), (90, 60, 140)), "capas": ((50, 40, 90), (35, 28, 70)),
     "tile": ((250, 220, 70), (70, 65, 100), (35, 30, 60)), "amb": None},
    {"nombre": "Cielo Alto", "cielo": ((70, 150, 255), (200, 235, 255)), "capas": ((170, 215, 240), (130, 195, 220)),
     "tile": ((255, 255, 255), (150, 200, 230), (100, 150, 190)), "amb": None},
    {"nombre": "Cantera", "cielo": ((120, 90, 60), (220, 180, 120)), "capas": ((150, 110, 75), (115, 80, 55)),
     "tile": ((175, 135, 85), (120, 85, 55), (70, 50, 35)), "amb": None},
    {"nombre": "Fábrica Explosiva", "cielo": ((50, 40, 40), (140, 90, 60)), "capas": ((90, 70, 65), (65, 50, 50)),
     "tile": ((205, 75, 65), (90, 80, 80), (45, 40, 45)), "amb": "brasas"},
    {"nombre": "Fortaleza del Dr. Malvex", "cielo": ((15, 10, 30), (60, 30, 80)),
     "capas": ((40, 25, 60), (28, 18, 45)), "tile": ((150, 150, 190), (75, 70, 105), (35, 30, 55)), "amb": None},
]


# ---------------------------------------------------------------- Utilidades
def R(x, y, w, h):
    return pygame.Rect(int(x), int(y), int(w), int(h))


def mezclar(color, f):
    return tuple(max(0, min(255, int(v * f))) for v in color)


_BRILLOS = {}


def brillo(sup, pos, radio, color, fuerza=0.4):
    """Halo de luz aditivo (se cachea por radio/color)."""
    radio = max(4, int(radio))
    clave = (radio, tuple(color), fuerza)
    s = _BRILLOS.get(clave)
    if s is None:
        s = pygame.Surface((radio * 2, radio * 2))
        for k in range(radio, 0, -2):
            f = fuerza * (1 - k / radio) ** 2
            pygame.draw.circle(s, tuple(int(v * f) for v in color), (radio, radio), k)
        _BRILLOS[clave] = s
    sup.blit(s, (int(pos[0]) - radio, int(pos[1]) - radio), special_flags=pygame.BLEND_RGB_ADD)


def crear_cielo(arriba, abajo):
    cielo = pygame.Surface((ANCHO, ALTO))
    for y in range(ALTO):
        t = y / ALTO
        color = tuple(int(a + (b - a) * t) for a, b in zip(arriba, abajo))
        pygame.draw.line(cielo, color, (0, y), (ANCHO, y))
    return cielo


def crear_capa(color, base, amplitud, forma, k1, k2, fase):
    """Franja de montañas/colinas que se repite sin costuras. Devuelve (superficie, y_superior)."""
    def altura(x):
        if forma == "pico":
            h = (0.7 * (1 - abs(math.sin(math.pi * k1 * x / ANCHO + fase)))
                 + 0.3 * (1 - abs(math.sin(math.pi * k2 * x / ANCHO + fase * 2))))
        else:
            a = 2 * math.pi * x / ANCHO
            h = 0.5 + 0.35 * math.sin(k1 * a + fase) + 0.15 * math.sin(k2 * a + fase * 2)
        return base - amplitud * h

    top = max(0, int(base - amplitud) - 2)
    sup = pygame.Surface((ANCHO, ALTO - top))
    sup.fill(CLAVE)
    sup.set_colorkey(CLAVE)
    puntos = [(0, ALTO - top)] + [(x, altura(x) - top) for x in range(0, ANCHO + 1, 8)] + [(ANCHO, ALTO - top)]
    pygame.draw.polygon(sup, color, puntos)
    return sup, top


def crear_tiles(colores):
    claro, medio, oscuro = colores
    top = pygame.Surface((TS, TS))
    top.fill(medio)
    pygame.draw.rect(top, claro, (0, 0, TS, 9))
    pygame.draw.line(top, mezclar(claro, 1.18), (1, 1), (TS - 2, 1), 1)      # brillo superior
    pygame.draw.line(top, oscuro, (0, 9), (TS, 9), 2)
    pygame.draw.rect(top, oscuro, (0, 0, TS, TS), 1)
    for x in (6, 18, 26):
        pygame.draw.rect(top, oscuro, (x, 20 + (x % 5), 3, 3))
    cuerpo = pygame.Surface((TS, TS))
    for y in range(TS):                                                       # degradado vertical
        pygame.draw.line(cuerpo, mezclar(medio, 1.08 - 0.28 * y / TS), (0, y), (TS, y))
    pygame.draw.line(cuerpo, oscuro, (0, TS // 2), (TS, TS // 2), 1)
    pygame.draw.line(cuerpo, oscuro, (TS // 2, 0), (TS // 2, TS // 2), 1)
    pygame.draw.line(cuerpo, oscuro, (TS // 4, TS // 2), (TS // 4, TS), 1)
    pygame.draw.rect(cuerpo, oscuro, (0, 0, TS, TS), 1)
    puerta = pygame.Surface((TS, TS))
    puerta.fill((120, 125, 140))
    for y in range(0, TS, 8):
        pygame.draw.rect(puerta, (70, 72, 88), (0, y, TS, 4))
    pygame.draw.rect(puerta, (40, 40, 50), (0, 0, TS, TS), 2)
    pinchos = pygame.Surface((TS, TS), pygame.SRCALPHA)
    for i in range(4):
        pts = [(i * 8, TS), (i * 8 + 4, TS - 15), (i * 8 + 8, TS)]
        pygame.draw.polygon(pinchos, (205, 210, 225), pts)
        pygame.draw.polygon(pinchos, (70, 70, 90), pts, 1)
    return {"top": top, "cuerpo": cuerpo, "puerta": puerta, "pinchos": pinchos}


def crear_vineta():
    v = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    pasos = 36
    for k in range(pasos):
        alpha = int(120 * (1 - k / pasos) ** 2.2)
        pygame.draw.rect(v, (0, 0, 0, alpha), (k * 4, k * 3, ANCHO - k * 8, ALTO - k * 6), 4)
    return v


# ---------------------------------------------------------------- Audio sintetizado
class Audio:
    TASA = 22050

    def __init__(self):
        self.activo = False
        self.silencio = False
        self.sonidos = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(self.TASA, -16, 1, 512)
            if pygame.mixer.get_init()[:3] != (self.TASA, -16, 1):
                return
            self._crear_sonidos()
            self.activo = True
        except pygame.error:
            self.activo = False

    def _onda(self, f0, f1, dur, vol=0.3, forma="seno"):
        n = int(self.TASA * dur)
        datos = array("h")
        fase = 0.0
        for i in range(n):
            t = i / max(1, n)
            fase += 2 * math.pi * (f0 + (f1 - f0) * t) / self.TASA
            if forma == "ruido":
                v = random.uniform(-1, 1)
            elif forma == "cuadrada":
                v = 1.0 if math.sin(fase) >= 0 else -1.0
            else:
                v = math.sin(fase)
            datos.append(int(32767 * vol * (1 - t) * v))
        return datos

    def _unir(self, *partes):
        total = array("h")
        for p in partes:
            total.extend(p)
        return pygame.mixer.Sound(buffer=total.tobytes())

    def _crear_sonidos(self):
        o = self._onda
        nota = lambda f, d=0.1, v=0.28: o(f, f, d, v, "cuadrada")
        self.sonidos = {
            "disparo": self._unir(o(1100, 350, 0.07, 0.18, "cuadrada")),
            "disparo_fuerte": self._unir(o(700, 120, 0.18, 0.28, "cuadrada")),
            "carga": self._unir(o(300, 900, 0.25, 0.15)),
            "golpe": self._unir(o(260, 120, 0.06, 0.3, "cuadrada")),
            "explosion": self._unir(o(0, 0, 0.22, 0.35, "ruido"), o(120, 40, 0.15, 0.3)),
            "dano": self._unir(o(450, 110, 0.22, 0.3, "cuadrada")),
            "item": self._unir(nota(700, 0.05), nota(1050, 0.1)),
            "vida": self._unir(nota(523, 0.08), nota(659, 0.08), nota(784, 0.08), nota(1047, 0.2)),
            "salto": self._unir(o(250, 520, 0.09, 0.18, "cuadrada")),
            "puerta": self._unir(o(110, 110, 0.3, 0.35, "cuadrada")),
            "tic": self._unir(nota(1200, 0.03, 0.15)),
            "arma": self._unir(nota(523, 0.1), nota(659, 0.1), nota(784, 0.1), nota(659, 0.1), nota(1047, 0.3)),
            "menu": self._unir(nota(660, 0.04, 0.2)),
            "muerte": self._unir(o(600, 40, 0.7, 0.3)),
            "victoria": self._unir(nota(523, 0.15), nota(659, 0.15), nota(784, 0.15),
                                   nota(1047, 0.3), nota(784, 0.15), nota(1047, 0.5)),
        }

    def reproducir(self, nombre):
        if self.activo and not self.silencio and nombre in self.sonidos:
            self.sonidos[nombre].play()

    def alternar(self):
        self.silencio = not self.silencio


# ---------------------------------------------------------------- Nivel
class Nivel:
    def __init__(self, datos):
        self.g = datos["g"]
        self.cols = len(self.g[0])
        self.ancho = self.cols * TS
        self.sala_ini = datos["sala_ini"]
        self.sala_x = self.sala_ini * TS
        self.check = datos["check"]
        self.spawn = datos["spawn"]
        self.enemigos = datos["enemigos"]
        self.items = datos["items"]

    def tile(self, c, r):
        if c < 0 or c >= self.cols:
            return "#"
        if r < 0 or r >= FILAS:
            return "."
        return self.g[r][c]

    def solidos_en(self, rect):
        out = []
        for c in range(rect.left // TS, (rect.right - 1) // TS + 1):
            for r in range(rect.top // TS, (rect.bottom - 1) // TS + 1):
                if self.tile(c, r) in "#|":
                    out.append(pygame.Rect(c * TS, r * TS, TS, TS))
        return out

    def pinchos(self, rect):
        for c in range(rect.left // TS, (rect.right - 1) // TS + 1):
            for r in range(rect.top // TS, (rect.bottom - 1) // TS + 1):
                if self.tile(c, r) == "^" and rect.colliderect(pygame.Rect(c * TS, r * TS + 14, TS, TS - 14)):
                    return True
        return False

    def cerrar_puerta(self):
        for r in range(10, 14):
            self.g[r][self.sala_ini - 1] = "|"


def generar_nivel(semilla, largo, dif):
    """Crea un nivel por segmentos (planos, huecos, pinchos, escalones, plataformas, muros)
    asegurando que todo sea salvable, y termina en una sala de jefe del tamaño de la pantalla."""
    rng = random.Random(semilla)
    N = largo + 40 + COLS_PANTALLA
    g = [["."] * N for _ in range(FILAS)]
    enem, items = [], []

    def suelo(c0, c1, h):
        for c in range(c0, min(c1, N)):
            for r in range(h, FILAS):
                g[r][c] = "#"

    def poblar(c0, n, h):
        for _ in range(rng.randint(0, 1 + dif)):
            if n < 5:
                break
            c = rng.randint(c0 + 2, c0 + n - 2)
            tipo = rng.choice(["caminante", "caminante", "torreta", "saltarin"])
            enem.append((tipo, c * TS + TS // 2, h * TS))
        if rng.random() < 0.3:
            tipo = rng.choice(["vida_p", "ammo_p", "vida_p", "ammo_p", "vida_g", "ammo_g"])
            items.append((tipo, (c0 + n // 2) * TS + TS // 2, h * TS - 40))
        elif rng.random() < 0.04:
            items.append(("extra", (c0 + n // 2) * TS + TS // 2, h * TS - 40))

    def volar(c, h):
        enem.append(("volador", c * TS, (h - 4) * TS))

    h = 13
    suelo(0, 14, h)
    col = 14
    mitad = largo // 2
    check = None
    while col < largo:
        if check is None and col >= mitad:
            suelo(col, col + 8, h)
            check = ((col + 3) * TS, h * TS - Jugador.H)
            g[h - 1][col + 3] = "C"
            col += 8
            continue
        seg = rng.choices(["plano", "hueco", "pinchos", "escalones", "plataformas", "muro"],
                          weights=[3, 3, 2, 2, 2, 2])[0]
        if seg == "plano":
            n = rng.randint(6, 11)
            suelo(col, col + n, h)
            poblar(col, n, h)
            col += n
        elif seg == "hueco":
            gp = rng.randint(2, 3)
            suelo(col + gp, col + gp + 5, h)
            if rng.random() < 0.3 * dif:
                volar(col + gp, h)
            col += gp + 5
        elif seg == "pinchos":
            n = rng.randint(8, 11)
            suelo(col, col + n, h)
            k = rng.randint(1, 3)
            c0 = col + rng.randint(2, n - k - 3)
            for c in range(c0, c0 + k):
                g[h - 1][c] = "^"
            col += n
        elif seg == "escalones":
            for _ in range(rng.randint(2, 3)):
                paso = rng.randint(1, 2)
                if h - paso < 8:
                    paso = -rng.randint(1, 2)
                h = min(14, h - paso)
                suelo(col, col + 3, h)
                col += 3
            suelo(col, col + 3, h)
            col += 3
        elif seg == "plataformas":
            gp = rng.randint(6, 9)
            fin = col + gp
            c, pr, ultimo = col + 1, h - 2, col
            while True:
                w = rng.randint(2, 3)
                if c + w > fin - 1:
                    break
                for cc in range(c, c + w):
                    g[pr][cc] = "#"
                ultimo = c + w
                c = ultimo + rng.randint(2, 3)
                pr = max(h - 4, min(h - 2, pr + rng.choice([-1, 0, 1])))
            while fin - ultimo > 3:       # el último salto hasta el suelo nunca supera 3 baldosas
                for cc in range(ultimo + 2, ultimo + 4):
                    g[pr][cc] = "#"
                ultimo += 4
            suelo(fin, fin + 5, h)
            if rng.random() < 0.5 * dif:
                volar(col + gp // 2, h)
            col = fin + 5
        else:  # muro
            n = rng.randint(8, 11)
            suelo(col, col + n, h)
            alto = rng.randint(2, 3)
            c0 = col + rng.randint(3, 4)
            for c in range(c0, c0 + 2):
                for r in range(h - alto, h):
                    g[r][c] = "#"
            poblar(col, n, h) if rng.random() < 0.3 else None
            col += n

    # Pasillo y sala del jefe
    suelo(col, N, 13)
    items.append(("vida_g", (col + 3) * TS, 13 * TS - 40))
    items.append(("ammo_g", (col + 5) * TS, 13 * TS - 40))
    sala_ini = col + 8
    cols = sala_ini + COLS_PANTALLA
    for c in range(sala_ini, cols):
        g[0][c] = g[1][c] = "#"
    for r in range(0, 14):
        g[r][cols - 1] = "#"
    for r in range(0, 10):
        g[r][sala_ini - 1] = "#"
    g = [fila[:cols] for fila in g]
    return {"g": g, "sala_ini": sala_ini, "check": check, "enemigos": enem, "items": items,
            "spawn": (2 * TS, 13 * TS - Jugador.H)}


def mover(e, nivel):
    """Mueve e (con rect, x, y, vx, vy) y resuelve colisiones con las baldosas sólidas.
    Devuelve (toca_pared, en_suelo, toca_techo)."""
    e.x += e.vx
    e.rect.x = round(e.x)
    toco_x = False
    for r in nivel.solidos_en(e.rect):
        if e.rect.colliderect(r):
            if e.vx > 0:
                e.rect.right = r.left
            elif e.vx < 0:
                e.rect.left = r.right
            e.x = float(e.rect.x)
            toco_x = True
    e.y += e.vy
    e.rect.y = round(e.y)
    suelo = techo = False
    for r in nivel.solidos_en(e.rect):
        if e.rect.colliderect(r):
            if e.vy > 0:
                e.rect.bottom = r.top
                suelo = True
            elif e.vy < 0:
                e.rect.top = r.bottom
                techo = True
            e.y = float(e.rect.y)
            e.vy = 0
    if not suelo and e.vy >= 0:
        sonda = e.rect.move(0, 1)
        if any(sonda.colliderect(r) for r in nivel.solidos_en(sonda)):
            suelo = True
    return toco_x, suelo, techo


# ---------------------------------------------------------------- Dibujo de personajes
def dibujar_robot(sup, r, color, m, estado, t, dispara=False, carga=0):
    """Robot del jugador (rect de 26x40). estado: quieto / correr / salto / dano."""
    osc, cl = mezclar(color, 0.55), mezclar(color, 1.35)
    cx, pie, y0 = r.centerx, r.bottom, r.y
    s = math.sin(t * 0.4)

    # Bufanda ondeando detrás
    vuelo = 0 if estado == "quieto" else 10
    onda = math.sin(t * 0.25)
    cola = 12 + vuelo
    pts = [(cx - m * 6, y0 + 17), (cx - m * (6 + cola * 0.5), y0 + 15 + onda * 2),
           (cx - m * (6 + cola), y0 + 18 + onda * 4), (cx - m * (6 + cola * 0.6), y0 + 23 + onda * 2),
           (cx - m * 6, y0 + 22)]
    pygame.draw.polygon(sup, (235, 70, 70), pts)
    pygame.draw.polygon(sup, (150, 30, 40), pts, 1)

    # Brazo trasero
    pygame.draw.line(sup, osc, (cx - m * 10, y0 + 20), (cx - m * 13, y0 + 28), 6)
    pygame.draw.circle(sup, cl, (cx - m * 13, y0 + 29), 3)

    # Piernas
    if estado == "salto":
        piernas = [(cx - 10, pie - 16, 9, 11), (cx + 1, pie - 20, 9, 11)]
    elif estado == "correr":
        piernas = [(cx - 10 + s * 5, pie - 14 - max(0, s) * 4, 9, 14),
                   (cx + 1 - s * 5, pie - 14 - max(0, -s) * 4, 9, 14)]
    else:
        piernas = [(cx - 10, pie - 14, 9, 14), (cx + 1, pie - 14, 9, 14)]
    for q in piernas:
        pygame.draw.rect(sup, osc, R(*q), border_radius=3)
        pygame.draw.line(sup, mezclar(osc, 0.6), (q[0] + 1, q[1] + 4), (q[0] + q[2] - 2, q[1] + 4), 2)
        pygame.draw.rect(sup, cl, R(q[0] - 1, q[1] + q[3] - 6, q[2] + 3, 6), border_radius=3)

    # Torso con placa, cinturón y núcleo
    pygame.draw.rect(sup, color, R(cx - 11, y0 + 16, 22, 14), border_radius=4)
    pygame.draw.rect(sup, cl, R(cx - 11, y0 + 16, 22, 4), border_radius=3)
    pygame.draw.rect(sup, osc, R(cx - 11, y0 + 28, 22, 3))
    pygame.draw.circle(sup, osc, (cx, y0 + 23), 5, 1)
    pygame.draw.circle(sup, BLANCO if (t // 12) % 2 else cl, (cx, y0 + 23), 3)
    for lado in (-1, 1):                                                                  # hombreras
        pygame.draw.circle(sup, cl, (cx + lado * 12, y0 + 19), 5)
        pygame.draw.circle(sup, osc, (cx + lado * 12, y0 + 19), 5, 1)

    # Cabeza: casco, cresta, antena, cara
    pygame.draw.polygon(sup, cl, [(cx - m * 2, y0 + 2), (cx - m * 12, y0 - 7), (cx - m * 8, y0 + 7)])
    pygame.draw.rect(sup, color, R(cx - 12, y0 + 1, 24, 17), border_radius=7)
    pygame.draw.rect(sup, cl, R(cx - 10, y0 + 1, 20, 4), border_radius=3)
    ant = math.sin(t * 0.2) * 2
    pygame.draw.line(sup, osc, (cx + m * 3, y0 + 1), (cx + m * 5 + ant, y0 - 6), 2)
    pygame.draw.circle(sup, AMARILLO if (t // 10) % 2 else ROJO, (int(cx + m * 5 + ant), y0 - 7), 2)
    pygame.draw.circle(sup, osc, (cx - m * 10, y0 + 10), 3)                               # orejera
    pygame.draw.rect(sup, PIEL, R(cx - 7 + m * 3, y0 + 6, 14, 9), border_radius=3)
    ex = cx + m * 3
    if estado == "dano":
        for ox in (-3, 3):
            pygame.draw.line(sup, NEGRO, (ex + ox - 2, y0 + 8), (ex + ox + 2, y0 + 12), 2)
            pygame.draw.line(sup, NEGRO, (ex + ox - 2, y0 + 12), (ex + ox + 2, y0 + 8), 2)
    else:
        pygame.draw.rect(sup, NEGRO, R(ex - 4, y0 + 8, 2, 4))
        pygame.draw.rect(sup, NEGRO, R(ex + 2, y0 + 8, 2, 4))

    # Cañón del brazo delantero
    if dispara or carga > 0:
        x0, x1 = cx + m * 8, cx + m * 24
        pygame.draw.rect(sup, osc, R(min(x0, x1), y0 + 19, abs(x1 - x0), 8), border_radius=3)
        pygame.draw.circle(sup, cl, (x1, y0 + 23), 5)
        if carga >= 25:
            rad = 5 + int(2 * math.sin(t * 0.6)) + (3 if carga >= 50 else 0)
            pygame.draw.circle(sup, BLANCO if (t // 3) % 2 else color, (x1 + m * 4, y0 + 23), rad)
    else:
        pygame.draw.line(sup, osc, (cx + m * 10, y0 + 20), (cx + m * 15, y0 + 29), 7)
        pygame.draw.circle(sup, cl, (cx + m * 15, y0 + 29), 5)
        pygame.draw.circle(sup, osc, (cx + m * 15, y0 + 29), 2)


def dibujar_jefe(sup, d, r, m, t, golpe=False):
    """Jefe de nivel (rect de 56x68), con diseño propio según su elemento."""
    col = BLANCO if golpe and t % 2 else d["color"]
    osc, cl, i = d["oscuro"], mezclar(d["color"], 1.3), d["id"]
    otro = mezclar(osc, 0.6)
    cx, b, y0 = r.centerx, r.bottom, r.y
    pulso = math.sin(t * 0.3)

    # Accesorios traseros
    if i == "viento":
        for lado in (-1, 1):
            pygame.draw.polygon(sup, mezclar(col, 0.8), [(cx + lado * 14, y0 + 28), (cx + lado * 40, y0 + 14 + pulso * 3),
                                                         (cx + lado * 32, y0 + 46)])
            pygame.draw.polygon(sup, BLANCO, [(cx + lado * 14, y0 + 28), (cx + lado * 40, y0 + 14 + pulso * 3),
                                              (cx + lado * 32, y0 + 46)], 1)
    elif i == "rayo" and t % 8 < 4:
        for lado in (-1, 1):
            pygame.draw.lines(sup, AMARILLO, False, [(cx + lado * 34, y0 + 18), (cx + lado * 42, y0 + 26),
                                                     (cx + lado * 36, y0 + 32), (cx + lado * 44, y0 + 42)], 2)

    # Piernas
    for lado in (-1, 1):
        pygame.draw.rect(sup, osc, R(cx + lado * 10 - 8, b - 22, 16, 22), border_radius=4)
        pygame.draw.line(sup, otro, (cx + lado * 10 - 7, b - 14), (cx + lado * 10 + 7, b - 14), 2)
        pygame.draw.rect(sup, cl, R(cx + lado * 10 - 10, b - 9, 20, 9), border_radius=3)

    # Torso
    pygame.draw.rect(sup, col, R(r.x + 4, y0 + 26, r.w - 8, 30), border_radius=9)
    pygame.draw.rect(sup, cl, R(r.x + 4, y0 + 26, r.w - 8, 6), border_radius=4)
    pygame.draw.rect(sup, osc, R(r.x + 4, y0 + 50, r.w - 8, 6), border_radius=3)
    pygame.draw.circle(sup, osc, (cx, y0 + 40), 8)
    if i == "fuego":
        pygame.draw.polygon(sup, (255, 200, 60), [(cx - 6, y0 + 46), (cx, y0 + 31 + pulso * 3), (cx + 6, y0 + 46)])
        pygame.draw.polygon(sup, BLANCO, [(cx - 3, y0 + 46), (cx, y0 + 38), (cx + 3, y0 + 46)])
    elif i == "hielo":
        for a in (0, math.pi / 3, 2 * math.pi / 3):
            pygame.draw.line(sup, (230, 250, 255), (cx - math.cos(a) * 9, y0 + 40 - math.sin(a) * 9),
                             (cx + math.cos(a) * 9, y0 + 40 + math.sin(a) * 9), 2)
    elif i == "rayo":
        pygame.draw.lines(sup, AMARILLO, False, [(r.x + 8, y0 + 34), (cx - 8, y0 + 44), (cx + 2, y0 + 32),
                                                 (r.right - 8, y0 + 44)], 3)
    elif i == "viento":
        pygame.draw.ellipse(sup, (230, 255, 235), R(cx - 13, y0 + 33, 26, 14), 2)
        pygame.draw.circle(sup, BLANCO, (cx, y0 + 40), 3)
    elif i == "tierra":
        pygame.draw.lines(sup, otro, False, [(cx - 14, y0 + 28), (cx - 6, y0 + 38), (cx - 12, y0 + 52)], 2)
        pygame.draw.lines(sup, otro, False, [(cx + 10, y0 + 28), (cx + 4, y0 + 40), (cx + 8, y0 + 52)], 2)
        pygame.draw.circle(sup, (250, 190, 90), (cx, y0 + 40), 4)
    else:  # bomba
        pygame.draw.line(sup, (35, 35, 45), (r.x + 6, y0 + 30), (r.right - 6, y0 + 52), 7)
        for k in range(4):
            px, py = r.x + 12 + k * 11, y0 + 33 + k * 5
            pygame.draw.circle(sup, AMARILLO if (t // 6 + k) % 3 else BLANCO, (px, py), 3)
        pygame.draw.circle(sup, (35, 35, 45), (cx, y0 + 40), 6)
    if i in ("fuego", "hielo", "viento"):
        pygame.draw.circle(sup, cl, (cx, y0 + 40), 8, 1)

    # Brazo trasero
    pygame.draw.line(sup, osc, (cx - m * 24, y0 + 34), (cx - m * 28, y0 + 52), 9)
    pygame.draw.circle(sup, cl, (cx - m * 28, y0 + 54), 7)

    # Hombreras (una por elemento)
    for lado in (-1, 1):
        sx, sy = cx + lado * 27, y0 + 33
        if i == "tierra":
            radios = (13, 10, 14, 11, 13, 10)
            pts = [(sx + radios[k] * math.cos(k * 1.05), sy + radios[k] * 0.9 * math.sin(k * 1.05)) for k in range(6)]
            pygame.draw.polygon(sup, otro if not (golpe and t % 2) else BLANCO, pts)
            pygame.draw.polygon(sup, osc, pts, 2)
        else:
            if i == "fuego":
                for k in (-1, 0, 1):
                    al = 12 + pulso * 3 + (3 if k == 0 else 0)
                    pygame.draw.polygon(sup, (255, 150, 40), [(sx + k * 7 - 4, sy - 6), (sx + k * 7, sy - 6 - al), (sx + k * 7 + 4, sy - 6)])
            elif i == "hielo":
                for k, al in ((-1, 10), (0, 15), (1, 10)):
                    pygame.draw.polygon(sup, (225, 250, 255), [(sx + k * 7 - 4, sy - 6), (sx + k * 7, sy - 6 - al), (sx + k * 7 + 4, sy - 6)])
            pygame.draw.circle(sup, cl if i != "bomba" else (45, 45, 58), (sx, sy), 11)
            pygame.draw.circle(sup, osc, (sx, sy), 11, 2)
            if i == "bomba":
                pygame.draw.circle(sup, (120, 120, 140), (sx - 3, sy - 3), 3)
            elif i == "rayo":
                pygame.draw.lines(sup, AMARILLO, False, [(sx - 4, sy - 6), (sx + 1, sy - 1), (sx - 2, sy + 1), (sx + 4, sy + 7)], 2)

    # Cañón del brazo delantero
    x0, x1 = cx + m * 14, cx + m * 40
    pygame.draw.rect(sup, osc, R(min(x0, x1), y0 + 36, abs(x1 - x0), 12), border_radius=5)
    pygame.draw.rect(sup, cl, R(min(x0, x1), y0 + 36, abs(x1 - x0), 3), border_radius=2)
    pygame.draw.circle(sup, cl, (x1, y0 + 42), 7)
    pygame.draw.circle(sup, BLANCO, (x1, y0 + 42), 3)

    # Cresta (detrás de la cabeza)
    if i == "fuego":
        for k in range(5):
            ox = (k - 2) * 8
            alto = (18 + (6 if k % 2 == 0 else 0)) * (1 + 0.25 * math.sin(t * 0.3 + k))
            pygame.draw.polygon(sup, (255, 150, 40), [(cx + ox - 6, y0 + 8), (cx + ox, y0 + 8 - alto), (cx + ox + 6, y0 + 8)])
            if k in (1, 2, 3):
                pygame.draw.polygon(sup, AMARILLO, [(cx + ox - 3, y0 + 8), (cx + ox, y0 + 8 - alto * 0.6), (cx + ox + 3, y0 + 8)])
    elif i == "hielo":
        for ox, al in ((-16, 14), (-8, 22), (0, 30), (8, 22), (16, 14)):
            pts = [(cx + ox - 4, y0 + 8), (cx + ox, y0 + 8 - al), (cx + ox + 4, y0 + 8)]
            pygame.draw.polygon(sup, (225, 250, 255), pts)
            pygame.draw.polygon(sup, (120, 190, 230), pts, 1)
    elif i == "rayo":
        for lado in (-1, 1):
            pts = [(cx + lado * 14, y0 + 8), (cx + lado * 10, y0 - 2), (cx + lado * 19, y0 - 6), (cx + lado * 13, y0 - 18)]
            pygame.draw.lines(sup, AMARILLO, False, pts, 3)
            pygame.draw.circle(sup, BLANCO if t % 6 < 3 else AMARILLO, pts[-1], 3)
    elif i == "viento":
        a = t * 0.5
        pygame.draw.rect(sup, osc, R(cx - 3, y0 - 4, 6, 12))
        pygame.draw.line(sup, (230, 255, 235), (cx - math.cos(a) * 26, y0 - 3), (cx + math.cos(a) * 26, y0 - 3), 5)
        pygame.draw.line(sup, BLANCO, (cx - math.sin(a) * 22, y0 - 3), (cx + math.sin(a) * 22, y0 - 3), 3)
    elif i == "tierra":
        for pts in ([(cx - 20, y0 + 10), (cx - 28, y0 - 8), (cx - 10, y0 + 2)],
                    [(cx + 20, y0 + 10), (cx + 28, y0 - 8), (cx + 10, y0 + 2)],
                    [(cx - 8, y0 + 4), (cx, y0 - 10), (cx + 8, y0 + 4)]):
            pygame.draw.polygon(sup, otro, pts)
            pygame.draw.polygon(sup, osc, pts, 2)
    else:  # bomba
        pygame.draw.circle(sup, (35, 35, 45), (cx, y0 + 2), 15)
        pygame.draw.circle(sup, (120, 120, 140), (cx - 5, y0 - 3), 4)
        pygame.draw.lines(sup, (200, 170, 90), False, [(cx + 5, y0 - 12), (cx + 10, y0 - 18), (cx + 16, y0 - 20)], 2)
        if t % 6 < 3:
            pygame.draw.circle(sup, AMARILLO, (cx + 16, y0 - 21), 4)
            pygame.draw.circle(sup, BLANCO, (cx + 16, y0 - 21), 2)

    # Cabeza y cara
    pygame.draw.rect(sup, col, R(cx - 19, y0 + 2, 38, 30), border_radius=12)
    pygame.draw.rect(sup, cl, R(cx - 15, y0 + 2, 30, 5), border_radius=3)
    pygame.draw.rect(sup, NEGRO, R(cx - 15 + m * 2, y0 + 13, 30, 12), border_radius=5)
    for ox in (-11, 2):
        pygame.draw.rect(sup, AMARILLO, R(cx + ox + m * 2, y0 + 16, 9, 5), border_radius=2)
        pygame.draw.rect(sup, BLANCO, R(cx + ox + m * 2 + 3 + m, y0 + 17, 3, 3))
    pygame.draw.line(sup, NEGRO, (cx - 16 + m * 2, y0 + 9), (cx - 3 + m * 2, y0 + 14), 4)
    pygame.draw.line(sup, NEGRO, (cx + 16 + m * 2, y0 + 9), (cx + 3 + m * 2, y0 + 14), 4)
    pygame.draw.rect(sup, osc, R(cx - 8, y0 + 26, 16, 4), border_radius=2)
    for k in range(-2, 3):
        pygame.draw.line(sup, cl, (cx + k * 3, y0 + 26), (cx + k * 3, y0 + 29), 1)


def dibujar_malvex(sup, r, t, golpe=False, furioso=False):
    """El Dr. Malvex en su platillo volador (rect de 100x64)."""
    cx, y0 = r.centerx, r.y
    base = BLANCO if golpe and t % 2 else (150, 150, 175)
    osc, cl = mezclar(base, 0.6), mezclar(base, 1.2)
    luz = ROJO if furioso else AMARILLO

    for lado in (-1, 1):                                                           # propulsores
        fl = 8 + 5 * math.sin(t * 0.6 + lado)
        pygame.draw.rect(sup, osc, R(cx + lado * 24 - 9, y0 + 46, 18, 10), border_radius=3)
        pygame.draw.polygon(sup, (255, 160, 50), [(cx + lado * 24 - 8, y0 + 55), (cx + lado * 24, y0 + 55 + fl * 2), (cx + lado * 24 + 8, y0 + 55)])
        pygame.draw.polygon(sup, AMARILLO, [(cx + lado * 24 - 4, y0 + 55), (cx + lado * 24, y0 + 55 + fl), (cx + lado * 24 + 4, y0 + 55)])
    for lado in (-1, 1):                                                           # brazos con pinzas
        bal = math.sin(t * 0.1 + lado) * 4
        mano = (cx + lado * 54, y0 + 44 + bal)
        pygame.draw.line(sup, osc, (cx + lado * 40, y0 + 36), mano, 6)
        pygame.draw.circle(sup, cl, mano, 6)
        for dy in (-6, 6):
            pygame.draw.line(sup, cl, mano, (mano[0] + lado * 8, mano[1] + dy + 4), 3)

    pygame.draw.ellipse(sup, (170, 220, 245), R(cx - 26, y0 - 4, 52, 46))          # cúpula
    pygame.draw.circle(sup, PIEL, (cx, y0 + 16), 12)                               # cabeza
    pygame.draw.circle(sup, BLANCO, (cx, y0 + 10), 12, draw_top_left=True, draw_top_right=True)
    for lado in (-1, 1):
        pygame.draw.circle(sup, BLANCO, (cx + lado * 12, y0 + 15), 4)
        pygame.draw.line(sup, NEGRO, (cx + lado * 9, y0 + 12), (cx + lado * 2, y0 + 16), 3)
        pygame.draw.circle(sup, ROJO if furioso else NEGRO, (cx + lado * 5, y0 + 17), 2)
    pygame.draw.rect(sup, BLANCO, R(cx - 12, y0 + 21, 24, 5), border_radius=3)     # bigote
    pygame.draw.circle(sup, BLANCO, (cx - 13, y0 + 24), 3)
    pygame.draw.circle(sup, BLANCO, (cx + 13, y0 + 24), 3)
    pygame.draw.arc(sup, (225, 247, 255), R(cx - 26, y0 - 4, 52, 46), 0, math.pi, 3)
    pygame.draw.line(sup, osc, (cx, y0 - 4), (cx, y0 - 14), 3)                     # antena
    pygame.draw.circle(sup, luz if (t // 8) % 2 else osc, (cx, y0 - 15), 3)

    pygame.draw.ellipse(sup, osc, R(r.x, y0 + 26, r.w, 30))                        # plato
    pygame.draw.ellipse(sup, base, R(r.x + 4, y0 + 24, r.w - 8, 24))
    pygame.draw.ellipse(sup, cl, R(r.x + 12, y0 + 26, r.w - 24, 6))
    for k in range(7):                                                             # luces del borde
        x = r.x + 10 + k * (r.w - 20) / 6
        pygame.draw.circle(sup, luz if (t // 6 + k) % 2 else mezclar(luz, 0.4), (int(x), y0 + 42 + int(4 * math.sin(k * 0.5))), 3)
    pygame.draw.circle(sup, osc, (cx, y0 + 38), 7)
    pygame.draw.circle(sup, luz, (cx, y0 + 38), 4)


def barra_vertical(sup, x, y, valor, maximo, color, segs=28):
    pygame.draw.rect(sup, NEGRO, (x - 3, y - 3, 20, segs * 4 + 6), border_radius=3)
    pygame.draw.rect(sup, BLANCO, (x - 3, y - 3, 20, segs * 4 + 6), 2, border_radius=3)
    lleno = int(round(max(0, valor) / maximo * segs))
    for i in range(segs):
        pygame.draw.rect(sup, color if i < lleno else (45, 45, 58), (x, y + (segs - 1 - i) * 4, 14, 3))


# ---------------------------------------------------------------- Proyectiles
class Proyectil:
    def __init__(self, x, y, vx, vy, w, h, dmg, color, hostil=False, grav=0.0, vida=120, pierce=False,
                 explota=0, congela=False, boomerang=False, forma="bala", arma="buster"):
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (round(x), round(y))
        self.cx, self.cy = float(x), float(y)
        self.vx, self.vy, self.v0 = vx, vy, vx
        self.dmg, self.color, self.hostil, self.grav = dmg, color, hostil, grav
        self.vida = self.vida_max = vida
        self.pierce, self.explota, self.congela = pierce, explota, congela
        self.boomerang, self.forma, self.arma = boomerang, forma, arma
        self.edad = 0
        self.vivo = True
        self.detonar = False
        self.golpeados = set()

    def actualizar(self, nivel):
        self.edad += 1
        self.vida -= 1
        if self.boomerang:
            self.vx = self.v0 * math.cos(math.pi * self.edad / self.vida_max)
        self.vy += self.grav
        self.cx += self.vx
        self.cy += self.vy
        self.rect.center = (round(self.cx), round(self.cy))
        if self.forma != "explosion" and nivel.tile(int(self.cx) // TS, int(self.cy) // TS) in "#|":
            self.vivo = False
            if self.explota:
                self.detonar = True
        if self.vida <= 0:
            self.vivo = False
            if self.explota:
                self.detonar = True
        if self.cx < -100 or self.cx > nivel.ancho + 100 or self.cy > ALTO + 100:
            self.vivo = False

    def dibujar(self, sup, cam):
        r = self.rect.move(-cam, 0)
        if r.right < -40 or r.left > ANCHO + 40:
            return
        f, c, (cx, cy) = self.forma, self.color, r.center
        if f != "explosion":
            brillo(sup, (cx, cy), min(40, max(r.w, r.h) * 0.9 + 6), c, 0.5 if self.hostil else 0.42)
        if f == "bala":
            pygame.draw.ellipse(sup, c, r)
            pygame.draw.ellipse(sup, BLANCO, r.inflate(-r.w // 2, -r.h // 2))
        elif f == "carga":
            pygame.draw.circle(sup, c, (cx, cy), r.w // 2)
            pygame.draw.circle(sup, BLANCO, (cx, cy), r.w // 3)
        elif f == "fuego":
            pygame.draw.circle(sup, c, (cx, cy), r.w // 2)
            pygame.draw.circle(sup, AMARILLO, (cx - int(self.vx > 0) * 2 + 1, cy), r.w // 4 + self.edad % 3)
        elif f == "hielo":
            pygame.draw.polygon(sup, c, [(r.left, cy), (cx, r.top), (r.right, cy), (cx, r.bottom)])
            pygame.draw.polygon(sup, BLANCO, [(cx - 5, cy), (cx, cy - 3), (cx + 5, cy), (cx, cy + 3)])
        elif f == "rayo":
            pts = [(r.left, cy), (cx - 5, cy - 5), (cx + 3, cy + 5), (r.right, cy)]
            pygame.draw.lines(sup, c, False, pts, 4)
            pygame.draw.lines(sup, BLANCO, False, pts, 1)
        elif f == "cuchilla":
            a, pts = self.edad * 0.5, []
            for k in range(8):
                rad = r.w / 2 if k % 2 == 0 else r.w / 5
                ang = a + k * math.pi / 4
                pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
            pygame.draw.polygon(sup, c, pts)
            pygame.draw.polygon(sup, BLANCO, pts, 1)
        elif f == "roca":
            pts = [(r.left + 3, r.top), (r.right - 2, r.top + 4), (r.right, r.bottom - 5),
                   (r.left + 6, r.bottom), (r.left, r.centery)]
            pygame.draw.polygon(sup, c, pts)
            pygame.draw.polygon(sup, mezclar(c, 0.55), pts, 2)
        elif f == "bomba":
            pygame.draw.circle(sup, (40, 40, 50), (cx, cy), r.w // 2)
            pygame.draw.circle(sup, c, (cx - 2, cy - 2), 3)
            if self.edad % 8 < 4:
                pygame.draw.circle(sup, AMARILLO, (cx + 4, cy - r.w // 2), 3)
        elif f == "explosion":
            p = 1 - self.vida / self.vida_max
            rad = int(r.w / 2 * (0.5 + 0.5 * p))
            brillo(sup, (cx, cy), rad * 1.7 + 6, (255, 170, 60), 0.6)
            pygame.draw.circle(sup, (255, 190, 70), (cx, cy), rad)
            pygame.draw.circle(sup, BLANCO, (cx, cy), max(2, rad // 2))
        elif f == "tornado":
            for k in range(5):
                ancho = 14 + k * 5 + int(4 * math.sin(self.edad * 0.4 + k))
                pygame.draw.ellipse(sup, c if k % 2 == 0 else BLANCO, (cx - ancho // 2, r.top + k * (r.h // 5), ancho, r.h // 5 + 2))
        else:  # bala enemiga
            pygame.draw.circle(sup, c, (cx, cy), r.w // 2 + 1)
            pygame.draw.circle(sup, BLANCO, (cx, cy), max(2, r.w // 4))


# ---------------------------------------------------------------- Objetos
class Item:
    def __init__(self, tipo, x, y, temporal=False):
        self.tipo = tipo
        tam = 22 if tipo == "extra" else (18 if tipo.endswith("_g") else 12)
        self.rect = pygame.Rect(0, 0, tam, tam)
        self.rect.midbottom = (round(x), round(y))
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        self.vx = self.vy = 0.0
        self.temporal = temporal
        self.vida = 600

    def actualizar(self, nivel):
        self.vy = min(self.vy + GRAV * 0.6, 8)
        mover(self, nivel)
        if self.temporal:
            self.vida -= 1

    def dibujar(self, sup, cam, t):
        if self.temporal and self.vida < 120 and (self.vida // 5) % 2:
            return
        r = self.rect.move(-cam, 0)
        if r.right < 0 or r.left > ANCHO:
            return
        if self.tipo.startswith("vida"):
            brillo(sup, r.center, r.w + 6, (255, 80, 80), 0.35)
            pygame.draw.rect(sup, BLANCO, r, border_radius=4)
            pygame.draw.rect(sup, ROJO, r.inflate(-4, -4), border_radius=3)
            pygame.draw.line(sup, BLANCO, (r.centerx, r.top + 3), (r.centerx, r.bottom - 3), 3)
            pygame.draw.line(sup, BLANCO, (r.left + 3, r.centery), (r.right - 3, r.centery), 3)
        elif self.tipo.startswith("ammo"):
            brillo(sup, r.center, r.w + 6, (80, 150, 255), 0.35)
            pygame.draw.rect(sup, BLANCO, r, border_radius=4)
            pygame.draw.rect(sup, (60, 120, 230), r.inflate(-4, -4), border_radius=3)
            pygame.draw.polygon(sup, AMARILLO, [(r.centerx + 2, r.top + 2), (r.left + 4, r.centery + 1),
                                                (r.centerx, r.centery + 1), (r.centerx - 2, r.bottom - 2),
                                                (r.right - 4, r.centery - 1), (r.centerx, r.centery - 1)])
        else:
            brillo(sup, r.center, 26, AZUL, 0.5)
            dibujar_robot(sup, pygame.Rect(r.centerx - 13, r.bottom - 40, 26, 40), AZUL, 1, "quieto", t)


# ---------------------------------------------------------------- Enemigos
class Enemigo:
    DATOS = {"caminante": (40, 34, 2), "torreta": (40, 40, 3), "saltarin": (36, 36, 2), "volador": (42, 30, 1)}

    def __init__(self, tipo, x, y, color):
        w, h, hp = self.DATOS[tipo]
        self.tipo, self.hp, self.color = tipo, hp, color
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.midbottom = (round(x), round(y))
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        self.y0 = self.y
        self.vx = self.vy = 0.0
        self.dir = -1
        self.t = random.randint(30, 90)
        self.congelado = 0
        self.flash = 0
        self.activo = False
        self.en_suelo = False
        self.muerto = False
        self.fuera = False
        self.ang = 0.0

    def actualizar(self, juego):
        j, nivel = juego.jugador, juego.nivel
        if not self.activo:
            if abs(self.rect.centerx - (juego.cam + ANCHO / 2)) < ANCHO * 0.7 + 20:
                self.activo = True
                self.dir = 1 if j.rect.centerx > self.rect.centerx else -1
            else:
                return
        if self.flash > 0:
            self.flash -= 1
        if self.congelado > 0:
            self.congelado -= 1
            if self.tipo != "volador":
                self.vy = min(self.vy + GRAV, CAIDA_MAX)
                self.vx = 0
                mover(self, nivel)
            return

        if self.tipo == "caminante":
            self.vy = min(self.vy + GRAV, CAIDA_MAX)
            self.vx = self.dir * 1.0
            c = (self.rect.centerx + self.dir * (self.rect.w // 2 + 2)) // TS
            r = (self.rect.bottom + 2) // TS
            if self.en_suelo and nivel.tile(c, r) not in "#|":
                self.dir = -self.dir
                self.vx = -self.vx
            toco, self.en_suelo, _ = mover(self, nivel)
            if toco:
                self.dir = -self.dir
        elif self.tipo == "saltarin":
            self.vy = min(self.vy + GRAV, CAIDA_MAX)
            if self.en_suelo:
                self.vx = 0
                self.t -= 1
                if self.t <= 0:
                    self.vy = -9.5
                    self.vx = 2.2 * (1 if j.rect.centerx > self.rect.centerx else -1)
                    self.t = random.randint(60, 100)
            _, self.en_suelo, _ = mover(self, nivel)
        elif self.tipo == "torreta":
            dx, dy = j.rect.centerx - self.rect.centerx, j.rect.centery - self.rect.centery
            self.ang = math.atan2(dy, dx)
            self.t -= 1
            if self.t <= 0 and abs(dx) < 420:
                self.t = 110
                ca, sa = math.cos(self.ang), math.sin(self.ang)
                juego.proyectiles.append(Proyectil(self.rect.centerx + ca * 24, self.rect.centery + sa * 24,
                                                   ca * 3.8, sa * 3.8, 9, 9, 2, (255, 130, 60), hostil=True,
                                                   vida=150, forma="bala_e"))
                juego.audio.reproducir("disparo")
        else:  # volador
            self.t += 1
            self.x += self.dir * 1.5
            self.y = self.y0 + math.sin(self.t * 0.08) * 45
            self.rect.topleft = (round(self.x), round(self.y))
            if abs(self.rect.centerx - (juego.cam + ANCHO / 2)) > ANCHO:
                self.fuera = True

    def dibujar(self, sup, cam, t):
        if self.hp <= 0:
            return
        r = self.rect.move(-cam, 0)
        if r.right < -20 or r.left > ANCHO + 20:
            return
        col, osc = self.color, mezclar(self.color, 0.6)
        if self.congelado > 0:
            col, osc = (170, 225, 255), (100, 170, 215)
        if self.flash > 0 and t % 2:
            col = BLANCO
        cl = mezclar(col, 1.3)
        cx, b, d = r.centerx, r.bottom, self.dir
        if self.tipo == "caminante":
            paso = (t // 8) % 2
            pygame.draw.ellipse(sup, NEGRO, R(r.x + 3 + paso * 4, b - 7, 15, 7))
            pygame.draw.ellipse(sup, NEGRO, R(r.right - 18 - paso * 4, b - 7, 15, 7))
            pygame.draw.rect(sup, osc, R(r.x + 3, b - 17, r.w - 6, 12), border_radius=4)
            pygame.draw.line(sup, mezclar(osc, 0.6), (r.x + 8, b - 11), (r.right - 8, b - 11), 2)
            centro = (cx, b - 15)
            for ox in (-10, 0, 10):
                yd = b - 15 - int(math.sqrt(400 - ox * ox))
                pygame.draw.polygon(sup, (215, 220, 230), [(cx + ox - 3, yd + 2), (cx + ox, yd - 6), (cx + ox + 3, yd + 2)])
            pygame.draw.circle(sup, col, centro, 20, draw_top_left=True, draw_top_right=True)
            pygame.draw.circle(sup, osc, centro, 20, 2, draw_top_left=True, draw_top_right=True)
            pygame.draw.ellipse(sup, cl, R(cx - 12, b - 31, 10, 5))
            pygame.draw.rect(sup, osc, R(cx - 23, b - 17, 46, 5), border_radius=2)
            for ox in (-6, 6):
                pygame.draw.circle(sup, BLANCO, (cx + ox + d * 2, b - 9), 4)
                pygame.draw.circle(sup, NEGRO, (cx + ox + d * 4, b - 9), 2)
        elif self.tipo == "torreta":
            base = [(r.x, b), (r.x + 5, b - 13), (r.right - 5, b - 13), (r.right, b)]
            pygame.draw.polygon(sup, osc, base)
            pygame.draw.polygon(sup, mezclar(osc, 0.6), base, 2)
            for ox in (-13, 13):
                pygame.draw.circle(sup, cl, (cx + ox, b - 5), 2)
            pygame.draw.circle(sup, col, (cx, b - 13), 16, draw_top_left=True, draw_top_right=True)
            pygame.draw.circle(sup, osc, (cx, b - 13), 16, 2, draw_top_left=True, draw_top_right=True)
            pygame.draw.ellipse(sup, cl, R(cx - 9, b - 27, 10, 5))
            ox, oy = cx, b - 20
            fin = (ox + math.cos(self.ang) * 24, oy + math.sin(self.ang) * 24)
            pygame.draw.line(sup, osc, (ox, oy), fin, 10)
            pygame.draw.line(sup, NEGRO, (ox, oy), fin, 6)
            pygame.draw.circle(sup, GRIS, fin, 5)
            pygame.draw.circle(sup, NEGRO, fin, 3)
            pygame.draw.circle(sup, ROJO, (ox, oy), 6)
            pygame.draw.circle(sup, BLANCO, (ox - 2, oy - 2), 2)
        elif self.tipo == "saltarin":
            sq = 3 if self.en_suelo else 0
            cy = r.centery - 6 + sq
            alto = (b - 4) - (cy + 10)
            for lado in (-8, 8):
                pts = [(cx + lado, cy + 10)]
                for k in range(1, 5):
                    pts.append((cx + lado + (5 if k % 2 else -5), cy + 10 + alto * k / 4))
                pygame.draw.lines(sup, osc, False, pts, 3)
            pygame.draw.ellipse(sup, NEGRO, R(cx - 14, b - 6, 12, 6))
            pygame.draw.ellipse(sup, NEGRO, R(cx + 2, b - 6, 12, 6))
            pygame.draw.circle(sup, col, (cx, cy), 15)
            pygame.draw.ellipse(sup, cl, R(cx - 9, cy + 1, 18, 11))
            pygame.draw.circle(sup, cl, (cx - 5, cy - 6), 4)
            for ox in (-7, 7):
                pygame.draw.circle(sup, BLANCO, (cx + ox, cy - 11), 6)
                pygame.draw.circle(sup, NEGRO, (cx + ox + d * 2, cy - 11), 3)
            pygame.draw.line(sup, NEGRO, (cx - 7, cy + 4), (cx + 7, cy + 4), 2)
        else:
            cy = r.centery
            ale = math.sin(t * 0.5) * 10
            for lado in (-1, 1):
                pts = [(cx + lado * 8, cy - 2), (cx + lado * 26, cy - 12 + ale), (cx + lado * 30, cy - 4 + ale * 0.6),
                       (cx + lado * 22, cy + 6)]
                pygame.draw.polygon(sup, osc, pts)
                pygame.draw.polygon(sup, mezclar(osc, 0.6), pts, 1)
                pygame.draw.line(sup, mezclar(osc, 0.6), (cx + lado * 8, cy - 2), (cx + lado * 27, cy - 6 + ale * 0.8), 1)
            pygame.draw.ellipse(sup, col, r)
            pygame.draw.ellipse(sup, cl, R(r.x + 6, r.y + 3, r.w - 18, 8))
            a = t * 0.9
            pygame.draw.line(sup, NEGRO, (cx, r.y - 3), (cx, r.y + 2), 3)
            pygame.draw.line(sup, (220, 225, 235), (cx - math.cos(a) * 14, r.y - 4), (cx + math.cos(a) * 14, r.y - 4), 3)
            brillo(sup, (cx + d * 5, cy), 14, ROJO, 0.5)
            pygame.draw.circle(sup, BLANCO, (cx + d * 5, cy), 6)
            pygame.draw.circle(sup, ROJO, (cx + d * 6, cy), 3)
            pygame.draw.circle(sup, NEGRO, (cx + d * 6, cy), 1)
            for ox in (-4, 2):
                pygame.draw.polygon(sup, BLANCO, [(cx + ox, r.bottom - 5), (cx + ox + 2, r.bottom + 2), (cx + ox + 4, r.bottom - 5)])


# ---------------------------------------------------------------- Jefes
class Jefe:
    W, H = 56, 68

    def __init__(self, idx, x, y):
        self.idx = idx
        self.d = JEFES[idx]
        self.rect = pygame.Rect(0, 0, self.W, self.H)
        self.rect.midbottom = (round(x), round(y))
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        self.vx = self.vy = 0.0
        self.hp = self.hp_max = 28
        self.mira = -1
        self.t = 40
        self.accion = "espera"
        self.flash = 0
        self.frame = 0
        self.en_suelo = False
        self.disparado = False

    def intro(self, juego):
        self.vy = min(self.vy + GRAV, CAIDA_MAX)
        _, self.en_suelo, _ = mover(self, juego.nivel)
        return self.en_suelo

    def recibir(self, dano, arma):
        if self.flash > 0:
            return False
        if arma == self.d["id"]:
            dano = 1
        elif arma == self.d["debil"]:
            dano *= 3
        self.hp -= dano
        self.flash = 8
        return True

    def elegir(self, juego):
        self.mira = 1 if juego.jugador.rect.centerx > self.rect.centerx else -1
        r = random.random()
        if r < 0.4:
            self.accion, self.vy, self.vx, self.t, self.disparado = "salto", -11.0, self.mira * 2.8, 90, False
        elif r < 0.75:
            self.accion, self.t, self.vx = "ataque", 50, 0
        else:
            self.accion, self.vx, self.t = "carga", self.mira * 4.2, 40

    def disparar(self, juego):
        x, y, m, i, col = self.rect.centerx + self.mira * 32, self.rect.centery - 4, self.mira, self.d["id"], self.d["color"]
        P, j = juego.proyectiles, juego.jugador
        juego.audio.reproducir("disparo_fuerte")
        if i == "fuego":
            for vy in (-3.0, -1.0, 1.0):
                P.append(Proyectil(x, y, m * 4.2, vy, 16, 16, 3, col, hostil=True, grav=0.12, vida=140, forma="fuego"))
        elif i == "hielo":
            P.append(Proyectil(x, y, m * 6.5, 0, 24, 12, 3, col, hostil=True, vida=130, forma="hielo"))
            P.append(Proyectil(x, y + 22, m * 5.0, 0, 24, 12, 3, col, hostil=True, vida=130, forma="hielo"))
        elif i == "rayo":
            for dy in (-30, 0, 30):
                P.append(Proyectil(x, y + dy, m * 7, 0, 26, 8, 3, col, hostil=True, vida=110, forma="rayo"))
        elif i == "viento":
            P.append(Proyectil(x, self.rect.bottom - 34, m * 3.2, 0, 34, 56, 3, col, hostil=True, vida=220, forma="tornado"))
        elif i == "tierra":
            for _ in range(3):
                P.append(Proyectil(j.rect.centerx + random.randint(-130, 130), 2 * TS + 8, 0, 3.5, 22, 22, 3, col,
                                   hostil=True, grav=0.2, vida=200, forma="roca"))
        else:
            P.append(Proyectil(x, y, m * 3.6, -6.5, 18, 18, 4, col, hostil=True, grav=0.35, vida=200,
                               explota=60, forma="bomba"))

    def actualizar(self, juego):
        self.frame += 1
        if self.flash > 0:
            self.flash -= 1
        self.vy = min(self.vy + GRAV, CAIDA_MAX)
        self.t -= 1
        if self.accion == "espera":
            self.vx = 0
            if self.t <= 0:
                self.elegir(juego)
        elif self.accion == "ataque":
            if self.t == 25:
                self.disparar(juego)
            if self.t <= 0:
                self.accion, self.t = "espera", random.randint(25, 45)
        elif self.accion == "salto":
            if not self.disparado and self.vy > 0:
                self.disparar(juego)
                self.disparado = True
            if self.en_suelo and self.t < 85:
                self.vx = 0
                self.accion, self.t = "espera", 30
                if self.d["id"] == "tierra":
                    juego.temblor = 14
                    juego.audio.reproducir("explosion")
        elif self.accion == "carga":
            if self.t <= 0:
                self.vx = 0
                self.accion, self.t = "espera", 35
        toco, self.en_suelo, _ = mover(self, juego.nivel)
        if toco and self.accion == "carga":
            self.vx = 0
            self.accion, self.t = "espera", 35

    def dibujar(self, sup, cam, t):
        r = self.rect.move(-cam, 0)
        brillo(sup, (r.centerx, r.centery), 64, self.d["color"], 0.32)
        dibujar_jefe(sup, self.d, r, self.mira, t, self.flash > 0)


class Malvex(Jefe):
    def __init__(self, x, y):
        self.idx = -1
        self.d = {"id": "malvex", "nombre": "DR. MALVEX", "color": (180, 180, 200), "oscuro": (90, 90, 110), "debil": None}
        self.rect = pygame.Rect(0, 0, 100, 64)
        self.rect.center = (round(x), -40)
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        self.vx = self.vy = 0.0
        self.hp = self.hp_max = 40
        self.mira, self.t, self.frame, self.flash = -1, 0, 0, 0
        self.en_suelo = False
        self.dir = -1
        self.limites = (x - 560, x - 10)

    def intro(self, juego):
        self.y = min(self.y + 3, 170)
        self.rect.y = round(self.y)
        return self.y >= 170

    def recibir(self, dano, arma):
        if self.flash > 0:
            return False
        self.hp -= dano
        self.flash = 8
        return True

    def actualizar(self, juego):
        self.frame += 1
        self.t += 1
        if self.flash > 0:
            self.flash -= 1
        furioso = self.hp <= 20
        vel = 2.6 if furioso else 1.6
        self.x += self.dir * vel
        if self.x < self.limites[0]:
            self.dir = 1
        elif self.x > self.limites[1]:
            self.dir = -1
        self.y = 170 + math.sin(self.frame * (0.06 if furioso else 0.04)) * (60 if furioso else 40)
        self.rect.topleft = (round(self.x), round(self.y))
        self.mira = 1 if juego.jugador.rect.centerx > self.rect.centerx else -1
        if self.t % (55 if furioso else 90) == 0:
            j = juego.jugador
            base = math.atan2(j.rect.centery - self.rect.centery, j.rect.centerx - self.rect.centerx)
            n = 5 if furioso else 3
            for k in range(n):
                a = base + (k - n // 2) * 0.22
                juego.proyectiles.append(Proyectil(self.rect.centerx, self.rect.centery + 10, math.cos(a) * 4.5,
                                                   math.sin(a) * 4.5, 12, 12, 3, (255, 90, 90), hostil=True,
                                                   vida=160, forma="bala_e"))
            juego.audio.reproducir("disparo_fuerte")
            if furioso and (self.t // 55) % 2 == 0:       # lluvia de proyectiles desde arriba
                for _ in range(2):
                    juego.proyectiles.append(Proyectil(j.rect.centerx + random.randint(-150, 150), 2 * TS + 8, 0, 3,
                                                       14, 14, 3, (255, 150, 60), hostil=True, grav=0.15,
                                                       vida=200, forma="bala_e"))

    def dibujar(self, sup, cam, t):
        r = self.rect.move(-cam, 0)
        furioso = self.hp <= 20
        brillo(sup, r.center, 80, (255, 90, 90) if furioso else (120, 120, 210), 0.35)
        dibujar_malvex(sup, r, t, self.flash > 0, furioso)


# ---------------------------------------------------------------- Jugador
class Jugador:
    W, H = 26, 40

    def __init__(self):
        self.rect = pygame.Rect(0, 0, self.W, self.H)
        self.armas = ["buster"]
        self.ammo = {i: 28 for i in IDS}
        self.arma = "buster"
        self.reiniciar(0, 0)

    def reiniciar(self, x, y):
        self.x, self.y = float(x), float(y)
        self.rect.topleft = (round(x), round(y))
        self.vx = self.vy = 0.0
        self.en_suelo = False
        self.mirando = 1
        self.hp = HP_MAX
        self.inv = self.aturdido = 0
        self.coyote = self.buffer = 0
        self.salto_prev = self.disp_prev = False
        self.carga = self.disp_anim = self.cd = self.frame = 0
        self.vivo = True

    def obtener(self, arma_id):
        if arma_id not in self.armas:
            self.armas.append(arma_id)
            self.armas.sort(key=lambda a: -1 if a == "buster" else IDS.index(a))

    def cambiar_arma(self, d):
        i = self.armas.index(self.arma)
        self.arma = self.armas[(i + d) % len(self.armas)]
        self.carga = 0

    def elegir_arma(self, n):
        if 0 <= n < len(self.armas):
            self.arma = self.armas[n]
            self.carga = 0

    def herir(self, juego, dano, direccion):
        if self.inv > 0 or not self.vivo:
            return False
        self.hp = max(0, self.hp - dano)
        self.inv, self.aturdido, self.vy, self.vx, self.carga = 80, 18, -4.0, direccion * 2.6, 0
        juego.audio.reproducir("dano")
        juego.temblor = 8
        return True

    def disparar(self, juego, cargado=False):
        a, m = self.arma, self.mirando
        x, y = self.rect.centerx + m * 16, self.rect.centery - 3
        P, au = juego.proyectiles, juego.audio
        propios = [p for p in P if not p.hostil]
        if a == "buster":
            if cargado:
                P.append(Proyectil(x, y, m * 8.5, 0, 30, 30, 4, (150, 220, 255), vida=70, pierce=True, forma="carga"))
                au.reproducir("disparo_fuerte")
            elif sum(1 for p in propios if p.arma == "buster" and p.forma == "bala") < MAX_BALAS:
                P.append(Proyectil(x, y, m * 9, 0, 12, 8, 2, (255, 240, 120), vida=55, forma="bala"))
                au.reproducir("disparo")
            else:
                return
            self.disp_anim = 14
            return
        if self.cd > 0 or self.ammo[a] <= 0:
            return
        col = ARMAS[a]["color"]
        if a == "fuego":
            P.append(Proyectil(x, y, m * 6, 0, 20, 20, 2, col, vida=45, forma="fuego", arma=a))
            self.cd = 14
        elif a == "hielo":
            P.append(Proyectil(x, y, m * 9, 0, 24, 12, 2, col, vida=50, congela=True, forma="hielo", arma=a))
            self.cd = 12
        elif a == "rayo":
            for vy in (-2.6, 0, 2.6):
                P.append(Proyectil(x, y, m * 8, vy, 22, 10, 2, col, vida=40, pierce=True, forma="rayo", arma=a))
            self.cd = 20
        elif a == "viento":
            if any(p.arma == "viento" for p in propios):
                return
            P.append(Proyectil(x, y, m * 7, 0, 28, 28, 2, col, vida=60, pierce=True, boomerang=True, forma="cuchilla", arma=a))
            self.cd = 10
        elif a == "tierra":
            P.append(Proyectil(x, y, m * 4.6, -3.5, 24, 24, 3, col, grav=0.28, vida=110, forma="roca", arma=a))
            self.cd = 24
        elif a == "bomba":
            P.append(Proyectil(x, y, m * 4.5, -5, 16, 16, 4, col, grav=0.3, vida=100, explota=60, forma="bomba", arma=a))
            self.cd = 26
        self.ammo[a] -= ARMAS[a]["coste"]
        self.disp_anim = 14
        au.reproducir("disparo_fuerte")

    def actualizar(self, juego, teclas):
        self.frame += 1
        izq = any(teclas[k] for k in K_IZQ)
        der = any(teclas[k] for k in K_DER)
        salto = any(teclas[k] for k in K_SALTO)
        disp = any(teclas[k] for k in K_DISP)
        if self.aturdido > 0:
            self.aturdido -= 1
            izq = der = salto = False
            self.vx *= 0.92
        else:
            d = int(der) - int(izq)
            self.vx = d * VEL
            if d:
                self.mirando = d

        if salto and not self.salto_prev:
            self.buffer = FRAMES_BUFFER
        self.salto_prev = salto
        self.coyote = FRAMES_COYOTE if self.en_suelo else max(0, self.coyote - 1)
        self.buffer = max(0, self.buffer - 1)
        if self.buffer and self.coyote:
            self.vy, self.buffer, self.coyote = SALTO, 0, 0
            juego.audio.reproducir("salto")
        if self.vy < -3 and not salto and self.aturdido == 0:
            self.vy *= 0.6
        self.vy = min(self.vy + GRAV, CAIDA_MAX)
        _, self.en_suelo, _ = mover(self, juego.nivel)

        # Disparo y carga
        if self.cd > 0:
            self.cd -= 1
        if self.aturdido == 0:
            if disp and not self.disp_prev:
                self.disparar(juego)
            if disp and self.arma == "buster":
                self.carga = min(self.carga + 1, 90)
                if self.carga == 25:
                    juego.audio.reproducir("carga")
            if not disp:
                if self.disp_prev and self.arma == "buster" and self.carga >= 50:
                    self.disparar(juego, cargado=True)
                self.carga = 0
        self.disp_prev = disp
        if self.disp_anim > 0:
            self.disp_anim -= 1
        if self.inv > 0:
            self.inv -= 1

    def dibujar(self, sup, cam, t):
        r = self.rect.move(-cam, 0)
        if self.aturdido > 0:
            estado = "dano"
        elif not self.en_suelo:
            estado = "salto"
        elif abs(self.vx) > 0.5:
            estado = "correr"
        else:
            estado = "quieto"
        if self.carga >= 25:
            brillo(sup, (r.centerx + self.mirando * 28, r.y + 23), 22 + (10 if self.carga >= 50 else 0),
                   (150, 220, 255), 0.55)
        dibujar_robot(sup, r, ARMAS[self.arma]["color"], self.mirando, estado, t, self.disp_anim > 0, self.carga)


# ---------------------------------------------------------------- Juego
class Juego:
    def __init__(self):
        try:
            self.ventana = pygame.display.set_mode((ANCHO, ALTO), pygame.SCALED | pygame.RESIZABLE)
        except pygame.error:
            self.ventana = pygame.display.set_mode((ANCHO, ALTO))
        self.pantalla = pygame.Surface((ANCHO, ALTO))
        pygame.display.set_caption("ROCKBOT - La fortaleza del Dr. Malvex")
        self.reloj = pygame.time.Clock()
        self.audio = Audio()

        self.f_grande = pygame.font.SysFont("Arial", 56, bold=True)
        self.f_titulo = pygame.font.SysFont("Arial", 34, bold=True)
        self.f_media = pygame.font.SysFont("Arial", 22, bold=True)
        self.f_peq = pygame.font.SysFont("Arial", 16, bold=True)
        self.f_mini = pygame.font.SysFont("Arial", 13, bold=True)

        self.cielos = [crear_cielo(*t["cielo"]) for t in TEMAS]
        self.capas = []
        for i, t in enumerate(TEMAS):
            lejos, cerca = t["capas"]
            self.capas.append([(*crear_capa(lejos, 380, 140, "pico", 3, 7, 0.6 + i), 0.15),
                               (*crear_capa(cerca, 470, 80, "colina", 2, 5, 1.3 + i), 0.35)])
        self.tiles = [crear_tiles(t["tile"]) for t in TEMAS]
        self.vineta = crear_vineta()

        # Retratos pequeños de los jefes (HUD, panel de selección, intro de nivel)
        self.minis = [self.retrato_jefe(i, 0.52, 0) for i in range(len(JEFES))]
        # Fondos temáticos de las tarjetas de selección
        self.fondos = [self.crear_fondo_tarjeta(i) for i in range(len(JEFES))]

        self.estado = "titulo"
        self.sel = 0
        self.vencidos = set()
        self.jugador = Jugador()
        self.vidas = 3
        self.t = 0
        self.t_menu = 0
        self.fin_t = 0
        self.intro_t = 0
        self.temblor = 0
        self.fade = 0
        self.nivel = None
        self.idx = 0
        self.tema = 0
        self.cam = 0.0
        self.ambiente = []
        self.enemigos, self.items, self.proyectiles, self.particulas = [], [], [], []
        self.sala = 0
        self.sala_t = 0
        self.jefe = None
        self.cola_jefes = []
        self.barra = 0.0
        self.check_ok = self.sala_vista = False
        self.muerte_t = 0

    # ------------------------------------------------------------ Retratos de jefes
    def retrato_jefe(self, i, escala, t, m=1, golpe=False):
        """Dibuja al jefe i en una superficie transparente y la escala."""
        tmp = pygame.Surface((80, 104), pygame.SRCALPHA)
        dibujar_jefe(tmp, JEFES[i], pygame.Rect(12, 32, 56, 68), m, t, golpe)
        return pygame.transform.scale(tmp, (int(80 * escala), int(104 * escala)))

    def crear_fondo_tarjeta(self, i):
        w, h, t = TARJ_W, TARJ_H, TEMAS[i]
        sup = pygame.transform.smoothscale(self.cielos[i], (w, h))
        pts = [(0, h)] + [(x, h - 54 - int(20 * math.sin(x * 0.05 + i) + 10 * math.sin(x * 0.13 + i * 2)))
                          for x in range(0, w + 1, 6)] + [(w, h)]
        pygame.draw.polygon(sup, t["capas"][0], pts)
        pts2 = [(0, h)] + [(x, h - 30 - int(12 * math.sin(x * 0.08 + i * 3))) for x in range(0, w + 1, 6)] + [(w, h)]
        pygame.draw.polygon(sup, t["capas"][1], pts2)
        pygame.draw.rect(sup, t["tile"][1], (0, h - 14, w, 14))
        pygame.draw.rect(sup, t["tile"][0], (0, h - 14, w, 5))
        pygame.draw.line(sup, t["tile"][2], (0, h - 9), (w, h - 9), 2)
        sombra = pygame.Surface((w, h), pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 45))
        sup.blit(sombra, (0, 0))
        sup = sup.convert_alpha()
        mascara = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, w, h), border_radius=12)
        sup.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return sup

    # ------------------------------------------------------------ Niveles
    def empezar_nivel(self, idx):
        for i in IDS:
            self.jugador.ammo[i] = 28
        self.check_ok = self.sala_vista = False
        self.iniciar_nivel(idx)
        self.estado = "intro"
        self.intro_t = 170
        self.fade = 30

    def iniciar_nivel(self, idx, reaparecer=False):
        self.idx, self.tema = idx, idx
        castillo = idx == 6
        datos = generar_nivel(100 + idx * 31, 190 if castillo else 110 + 8 * idx, 3 if castillo else 1 + idx // 3)
        self.nivel = Nivel(datos)
        color = (150, 150, 190) if castillo else JEFES[idx]["color"]
        self.enemigos = [Enemigo(t, x, y, color) for t, x, y in datos["enemigos"]]
        self.items = [Item(t, x, y) for t, x, y in datos["items"]]
        self.proyectiles, self.particulas = [], []
        self.sala, self.jefe, self.cola_jefes, self.barra, self.muerte_t = 0, None, [], 0.0, 0
        self.temblor = 0
        if reaparecer and self.sala_vista:
            sx, sy = self.nivel.sala_x - 7 * TS, 13 * TS - Jugador.H
        elif reaparecer and self.check_ok:
            sx, sy = self.nivel.check
        else:
            sx, sy = self.nivel.spawn
            self.check_ok = self.sala_vista = False
        self.jugador.reiniciar(sx, sy)
        self.cam = max(0, min(sx - ANCHO / 2, self.nivel.ancho - ANCHO))
        amb = TEMAS[idx]["amb"]
        self.ambiente = []
        if amb:
            for _ in range(45):
                self.ambiente.append([random.uniform(0, ANCHO), random.uniform(0, ALTO), random.uniform(0.4, 1.6),
                                      random.uniform(-0.4, 0.4), random.randint(1, 3)])

    def reaparecer(self):
        if self.vidas < 0:
            self.estado = "gameover"
            self.fin_t = 0
            return
        self.iniciar_nivel(self.idx, reaparecer=True)
        self.fade = 25

    # ------------------------------------------------------------ Efectos
    def explosion(self, x, y, color, n=14):
        for _ in range(n):
            a, v = random.uniform(0, 2 * math.pi), random.uniform(1, 5)
            self.particulas.append([x, y, math.cos(a) * v, math.sin(a) * v, random.randint(20, 40), color, random.randint(2, 4)])

    def actualizar_particulas(self):
        for p in self.particulas:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.12
            p[4] -= 1
        self.particulas = [p for p in self.particulas if p[4] > 0]
        amb = TEMAS[self.tema]["amb"]
        for a in self.ambiente:
            if amb == "brasas":
                a[1] -= a[2]
                a[0] += a[3] + math.sin(self.t * 0.05 + a[4])
                if a[1] < -5:
                    a[0], a[1] = random.uniform(0, ANCHO), ALTO + 5
            else:
                a[1] += a[2]
                a[0] += a[3]
                if a[1] > ALTO + 5:
                    a[0], a[1] = random.uniform(0, ANCHO), -5

    def soltar(self, x, y):
        r = random.random()
        tipo = "vida_p" if r < 0.16 else "ammo_p" if r < 0.28 else "vida_g" if r < 0.32 else None
        if tipo:
            self.items.append(Item(tipo, x, y, temporal=True))

    # ------------------------------------------------------------ Lógica del juego
    def actualizar_camara(self):
        n = self.nivel
        obj = n.sala_x if self.sala >= 1 else self.jugador.rect.centerx - ANCHO / 2
        obj = max(0, min(obj, n.ancho - ANCHO))
        self.cam += (obj - self.cam) * 0.2
        if abs(obj - self.cam) < 0.5:
            self.cam = obj

    def entrar_sala(self):
        self.sala = 1
        self.sala_vista = True
        self.nivel.cerrar_puerta()
        self.audio.reproducir("puerta")
        self.temblor = 12
        self.proyectiles = []
        if self.idx == 6:
            self.cola_jefes = list(range(6)) + ["malvex"]
            self.siguiente_jefe()
        else:
            self.crear_jefe(self.idx)

    def siguiente_jefe(self):
        self.crear_jefe(self.cola_jefes.pop(0))

    def crear_jefe(self, i):
        x, y = self.nivel.sala_x + ANCHO - 140, 5 * TS
        self.jefe = Malvex(x, y) if i == "malvex" else Jefe(i, x, y)
        self.sala, self.barra = 1, 0.0

    def terminar_jefe(self):
        self.jefe = None
        if self.idx == 6:
            if self.cola_jefes:
                self.jugador.hp = min(HP_MAX, self.jugador.hp + 10)
                self.siguiente_jefe()
            else:
                self.estado, self.fin_t = "victoria", 0
                self.audio.reproducir("victoria")
        else:
            self.vencidos.add(self.idx)
            self.jugador.obtener(IDS[self.idx])
            self.estado, self.fin_t = "arma", 0
            self.audio.reproducir("arma")

    def matar_jugador(self):
        j = self.jugador
        j.vivo = False
        self.explosion(j.rect.centerx, j.rect.centery, AZUL, 20)
        self.explosion(j.rect.centerx, j.rect.centery, BLANCO, 12)
        self.audio.reproducir("muerte")
        self.muerte_t = 100
        self.vidas -= 1

    def golpear(self, o, p):
        if isinstance(o, Jefe):
            if o.recibir(p.dmg, p.arma):
                self.audio.reproducir("golpe")
                self.explosion(p.rect.centerx, p.rect.centery, BLANCO, 5)
        else:
            o.hp -= p.dmg
            o.flash = 6
            if p.congela:
                o.congelado = 150
            self.audio.reproducir("golpe")
            self.explosion(p.rect.centerx, p.rect.centery, BLANCO, 4)

    def resolver_colisiones(self):
        j, nivel = self.jugador, self.nivel
        nuevas = []
        objetivos = [e for e in self.enemigos if e.hp > 0 and e.activo]
        if self.jefe and self.sala == 2:
            objetivos.append(self.jefe)
        for p in self.proyectiles:
            p.actualizar(nivel)
            if not p.hostil:
                for o in objetivos:
                    if id(o) in p.golpeados or not p.rect.colliderect(o.rect):
                        continue
                    p.golpeados.add(id(o))
                    if p.explota:
                        p.detonar, p.vivo = True, False
                        break
                    self.golpear(o, p)
                    if not p.pierce:
                        p.vivo = False
                        break
            elif j.vivo and p.rect.colliderect(j.rect):
                if p.forma == "explosion":
                    if id(j) not in p.golpeados:
                        p.golpeados.add(id(j))
                        j.herir(self, p.dmg, 1 if j.rect.centerx >= p.rect.centerx else -1)
                elif p.explota:
                    p.detonar, p.vivo = True, False
                elif j.herir(self, p.dmg, 1 if p.vx >= 0 else -1) and not p.pierce:
                    p.vivo = False
            if p.detonar:
                p.detonar = False
                nuevas.append(Proyectil(p.cx, p.cy, 0, 0, p.explota * 2, p.explota * 2, p.dmg, (255, 190, 70),
                                        hostil=p.hostil, vida=12, pierce=True, forma="explosion", arma=p.arma))
                self.audio.reproducir("explosion")
                self.temblor = max(self.temblor, 6)
                self.explosion(p.cx, p.cy, (255, 160, 50), 12)
        self.proyectiles = [p for p in self.proyectiles if p.vivo] + nuevas

        # Contacto con enemigos y jefe
        for e in self.enemigos:
            if e.hp > 0 and e.activo and e.rect.colliderect(j.rect):
                j.herir(self, 3, 1 if j.rect.centerx >= e.rect.centerx else -1)
        if self.jefe and self.sala == 2 and self.jefe.rect.colliderect(j.rect):
            j.herir(self, 4, 1 if j.rect.centerx >= self.jefe.rect.centerx else -1)
        if nivel.pinchos(j.rect):
            j.herir(self, 8, -j.mirando)

        for e in self.enemigos:
            if e.hp <= 0 and not e.muerto:
                e.muerto = True
                self.explosion(e.rect.centerx, e.rect.centery, e.color, 12)
                self.audio.reproducir("explosion")
                self.soltar(e.rect.centerx, e.rect.bottom)
        self.enemigos = [e for e in self.enemigos if not e.muerto and not e.fuera]

    def actualizar_juego(self):
        j, nivel = self.jugador, self.nivel
        self.t += 1
        self.actualizar_particulas()
        if self.temblor > 0:
            self.temblor -= 1
        if self.muerte_t > 0:
            self.muerte_t -= 1
            if self.muerte_t == 0:
                self.reaparecer()
            return

        if self.sala == 3:                                   # el jefe explota
            self.sala_t -= 1
            if self.sala_t % 6 == 0 and self.jefe:
                self.explosion(self.jefe.rect.centerx + random.randint(-24, 24),
                               self.jefe.rect.centery + random.randint(-28, 28), self.jefe.d["color"], 8)
                self.audio.reproducir("explosion")
            if self.sala_t <= 0:
                self.terminar_jefe()
            self.actualizar_camara()
            return

        if self.sala == 1:                                   # intro del jefe: aviso + barra de vida que se llena
            if self.jefe.intro(self):
                ant = int(self.barra)
                self.barra += 0.4
                if int(self.barra) != ant and int(self.barra) % 2 == 0:
                    self.audio.reproducir("tic")
            if self.barra >= self.jefe.hp_max:
                self.barra, self.sala = self.jefe.hp_max, 2
                self.jefe.t = 45
            self.actualizar_camara()
            return

        j.actualizar(self, pygame.key.get_pressed())
        if j.rect.left < self.cam:                           # no se puede retroceder fuera de la pantalla
            j.x = float(round(self.cam))
            j.rect.x = round(self.cam)
        for e in self.enemigos:
            e.actualizar(self)
        for it in self.items[:]:
            it.actualizar(nivel)
            if it.vida <= 0 or it.rect.top > ALTO + 60:
                self.items.remove(it)
            elif it.rect.colliderect(j.rect):
                self.recoger(it)
                self.items.remove(it)
        if self.jefe and self.sala == 2:
            self.jefe.actualizar(self)
        self.resolver_colisiones()

        if self.jefe and self.sala == 2 and self.jefe.hp <= 0:
            self.sala, self.sala_t = 3, 110
            self.proyectiles = [p for p in self.proyectiles if not p.hostil]
        if self.sala == 0 and j.rect.centerx > nivel.sala_x + 48:
            self.entrar_sala()
        if not self.check_ok and j.rect.centerx > nivel.check[0]:
            self.check_ok = True
            self.audio.reproducir("item")
        if j.vivo and (j.hp <= 0 or j.rect.top > ALTO + 40):
            j.hp = 0
            self.matar_jugador()
        self.actualizar_camara()

    def recoger(self, it):
        j = self.jugador
        if it.tipo.startswith("vida"):
            j.hp = min(HP_MAX, j.hp + (14 if it.tipo.endswith("_g") else 5))
            self.audio.reproducir("item")
        elif it.tipo.startswith("ammo"):
            cant = 18 if it.tipo.endswith("_g") else 7
            a = j.arma if j.arma != "buster" else min((x for x in j.armas if x != "buster"),
                                                      key=lambda x: j.ammo[x], default=None)
            if a:
                j.ammo[a] = min(28, j.ammo[a] + cant)
            self.audio.reproducir("item")
        else:
            self.vidas = min(9, self.vidas + 1)
            self.audio.reproducir("vida")

    # ------------------------------------------------------------ Dibujo
    def texto(self, txt, fuente, color, pos, centrado=True):
        img = fuente.render(txt, True, color)
        sombra = fuente.render(txt, True, NEGRO)
        rect = img.get_rect(center=pos) if centrado else img.get_rect(topleft=pos)
        self.pantalla.blit(sombra, rect.move(2, 2))
        self.pantalla.blit(img, rect)

    def texto_logo(self, txt, fuente, color, pos):
        """Título grande con contorno grueso y sombra de color."""
        s = self.pantalla
        contorno = fuente.render(txt, True, NEGRO)
        base = fuente.render(txt, True, mezclar(color, 0.5))
        img = fuente.render(txt, True, color)
        rect = img.get_rect(center=pos)
        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (3, 3), (-3, 3), (3, -3), (-3, -3), (0, 6), (3, 6), (-3, 6)):
            s.blit(contorno, rect.move(ox, oy))
        s.blit(base, rect.move(0, 4))
        s.blit(img, rect)

    def dibujar_fondo(self, tema, cam):
        s = self.pantalla
        s.blit(self.cielos[tema], (0, 0))
        for sup, top, f in self.capas[tema]:
            x0 = -int((cam * f) % ANCHO)
            s.blit(sup, (x0, top))
            s.blit(sup, (x0 + ANCHO, top))
        col = (255, 170, 60) if TEMAS[tema]["amb"] == "brasas" else BLANCO
        for x, y, _, _, r in self.ambiente:
            pygame.draw.circle(s, col, (int(x), int(y)), r)

    def dibujar_tiles(self):
        n, cam, s, ts = self.nivel, int(self.cam), self.pantalla, self.tiles[self.tema]
        for c in range(max(0, cam // TS), min(n.cols, (cam + ANCHO) // TS + 2)):
            x = c * TS - cam
            for r in range(FILAS):
                t = n.g[r][c]
                if t == ".":
                    continue
                y = r * TS
                if t == "#":
                    s.blit(ts["top"] if n.tile(c, r - 1) not in "#|" else ts["cuerpo"], (x, y))
                elif t == "|":
                    s.blit(ts["puerta"], (x, y))
                elif t == "^":
                    s.blit(ts["pinchos"], (x, y))
                elif t == "C":
                    color = VERDE if self.check_ok else ROJO
                    pygame.draw.rect(s, (200, 200, 210), (x + 14, y - 6, 4, TS + 6))
                    pygame.draw.polygon(s, color, [(x + 18, y - 6), (x + 32, y + 2), (x + 18, y + 10)])
                    brillo(s, (x + 24, y + 2), 20, color, 0.45)

    def dibujar_mundo(self):
        s, cam, j = self.pantalla, int(self.cam), self.jugador
        self.dibujar_fondo(self.tema, cam)
        self.dibujar_tiles()
        for it in self.items:
            it.dibujar(s, cam, self.t)
        for e in self.enemigos:
            e.dibujar(s, cam, self.t)
        if self.jefe:
            if self.sala != 3 or self.t % 4 < 2:
                self.jefe.dibujar(s, cam, self.t)
        for p in self.proyectiles:
            p.dibujar(s, cam)
        if j.vivo and not (j.inv > 0 and (j.inv // 3) % 2):
            j.dibujar(s, cam, self.t)
        for x, y, _, _, vida, color, r in self.particulas:
            pygame.draw.circle(s, color, (int(x - cam), int(y)), max(1, min(r, vida // 6 + 1)))
        s.blit(self.vineta, (0, 0))

    def dibujar_hud(self):
        s, j = self.pantalla, self.jugador
        # Panel izquierdo (vida, munición, arma, vidas)
        panel = pygame.Surface((128, 214), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 120), panel.get_rect(), border_radius=10)
        pygame.draw.rect(panel, (255, 255, 255, 60), panel.get_rect(), 2, border_radius=10)
        s.blit(panel, (8, 8))
        barra_vertical(s, 20, 20, j.hp, HP_MAX, (240, 240, 240) if j.hp > 8 else ROJO)
        if j.arma != "buster":
            barra_vertical(s, 46, 20, j.ammo[j.arma], 28, ARMAS[j.arma]["color"])
        self.texto(ARMAS[j.arma]["nombre"], self.f_peq, ARMAS[j.arma]["color"], (20, 146), centrado=False)
        dibujar_robot(s, pygame.Rect(20, 168, 26, 40), AZUL, 1, "quieto", 0)
        self.texto(f"x{max(0, self.vidas)}", self.f_media, BLANCO, (52, 180), centrado=False)

        # Panel del jefe (barra + retrato)
        if self.jefe and self.sala >= 1:
            d = self.jefe.d
            pj = pygame.Surface((110, 214), pygame.SRCALPHA)
            pygame.draw.rect(pj, (0, 0, 0, 120), pj.get_rect(), border_radius=10)
            pygame.draw.rect(pj, (255, 255, 255, 60), pj.get_rect(), 2, border_radius=10)
            s.blit(pj, (ANCHO - 118, 8))
            valor = self.barra if self.sala == 1 else self.jefe.hp
            barra_vertical(s, ANCHO - 34, 20, valor, self.jefe.hp_max, d["color"])
            self.texto(d["nombre"], self.f_peq, d["color"], (ANCHO - 63, 146))
            if self.jefe.idx >= 0:
                self.minis[self.jefe.idx].set_alpha(255)
                s.blit(self.minis[self.jefe.idx], (ANCHO - 63 - 21, 156))

        # Barra de armas
        n = len(j.armas)
        x0 = ANCHO // 2 - n * 15
        for i, a in enumerate(j.armas):
            r = pygame.Rect(x0 + i * 30, ALTO - 30 - (4 if a == j.arma else 0), 24, 22)
            pygame.draw.rect(s, ARMAS[a]["color"], r, border_radius=4)
            pygame.draw.rect(s, BLANCO if a == j.arma else NEGRO, r, 2, border_radius=4)
        if n > 1:
            self.texto("Q / E: cambiar arma", self.f_peq, BLANCO, (ANCHO // 2, ALTO - 46))

        # Fortaleza: progreso de la ronda de jefes
        if self.idx == 6 and self.jefe:
            x0 = ANCHO // 2 - 3 * 46
            for i in range(6):
                if self.jefe.idx == i:
                    alpha = 255
                    pygame.draw.rect(s, AMARILLO, (x0 + i * 46 - 2, 6, 46, 58), 2, border_radius=6)
                elif i in self.cola_jefes:
                    alpha = 150
                else:
                    alpha = 45
                self.minis[i].set_alpha(alpha)
                s.blit(self.minis[i], (x0 + i * 46, 8))
            for m in self.minis:
                m.set_alpha(255)

        if self.jefe and self.sala == 1:
            self.dibujar_aviso_jefe()

    def dibujar_aviso_jefe(self):
        """Banner de presentación del jefe mientras se llena su barra de vida."""
        s, d = self.pantalla, self.jefe.d
        veil = pygame.Surface((ANCHO, 92), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 175))
        s.blit(veil, (0, 150))
        pygame.draw.line(s, d["color"], (0, 150), (ANCHO, 150), 3)
        pygame.draw.line(s, d["color"], (0, 241), (ANCHO, 241), 3)
        if (self.t // 8) % 2 == 0:
            self.texto("¡ADVERTENCIA!", self.f_peq, ROJO, (ANCHO // 2, 166))
        self.texto(d["nombre"], self.f_titulo, d["color"], (ANCHO // 2, 197))
        deb = d.get("debil")
        if deb:
            self.texto(f"Punto débil: {ARMAS[deb]['nombre']}", self.f_peq, ARMAS[deb]["color"], (ANCHO // 2, 226))
        else:
            self.texto("El genio detrás de todo", self.f_peq, (200, 200, 230), (ANCHO // 2, 226))
        if self.jefe.idx >= 0:
            for m, x in ((1, ANCHO // 2 - 230), (-1, ANCHO // 2 + 230)):
                img = self.retrato_jefe(self.jefe.idx, 0.8, self.t, m)
                s.blit(img, (x - 32, 158))

    def dibujar_titulo(self):
        s = self.pantalla
        self.ambiente = []
        self.dibujar_fondo(6, self.t_menu * 0.8)
        suelo_y = ALTO - 90
        pygame.draw.rect(s, (35, 30, 55), (0, suelo_y, ANCHO, 90))
        pygame.draw.rect(s, (150, 150, 190), (0, suelo_y, ANCHO, 8))

        # Galería de jefes en fila: tres a cada lado, mirando al héroe
        posiciones = [(75, 0, 1), (170, 1, 1), (265, 2, 1), (695, 3, -1), (790, 4, -1), (885, 5, -1)]
        for k, (x, i, m) in enumerate(posiciones):
            bob = int(math.sin(self.t_menu * 0.08 + k) * 3)
            pygame.draw.ellipse(s, (15, 12, 28), (x - 32, suelo_y - 4, 64, 12))
            brillo(s, (x, suelo_y - 50), 70, JEFES[i]["color"], 0.3)
            img = self.retrato_jefe(i, 1.1, self.t_menu // 2, m)
            s.blit(img, (x - img.get_width() // 2, suelo_y + 4 - 110 + bob))

        self.texto_logo("ROCKBOT", self.f_grande, AMARILLO, (ANCHO // 2, 100))
        self.texto("La fortaleza del Dr. Malvex", self.f_titulo, BLANCO, (ANCHO // 2, 160))
        tmp = pygame.Surface((70, 64), pygame.SRCALPHA)
        dibujar_robot(tmp, pygame.Rect(22, 14, 26, 40), AZUL, 1, "correr", self.t_menu, dispara=self.t_menu % 90 < 20)
        brillo(s, (ANCHO // 2, 270), 110, AZUL, 0.3)
        s.blit(pygame.transform.scale(tmp, (175, 160)), (ANCHO // 2 - 87, 190))
        if (self.t_menu // 30) % 2 == 0:
            self.texto("PRESIONA ENTER", self.f_titulo, AMARILLO, (ANCHO // 2, 400))
        self.texto("Flechas/A-D: mover   Espacio/W: saltar   X/J: disparar (mantén para cargar)",
                   self.f_peq, BLANCO, (ANCHO // 2, 450))
        self.texto("Q/E: cambiar arma   P: pausa   M: sonido   F11: pantalla completa",
                   self.f_peq, BLANCO, (ANCHO // 2, 475))
        self.texto("Vence a los 6 jefes, copia sus armas y entra a la fortaleza.",
                   self.f_peq, (200, 200, 230), (ANCHO // 2, 510))
        s.blit(self.vineta, (0, 0))

    def castillo_abierto(self):
        return len(self.vencidos) == 6

    def dibujar_seleccion(self):
        s = self.pantalla
        s.fill((12, 16, 52))
        off = self.t_menu % 40
        for x in range(-40, ANCHO + 40, 40):
            pygame.draw.line(s, (22, 32, 88), (x + off, 0), (x + off, ALTO))
        for y in range(-40, ALTO + 40, 40):
            pygame.draw.line(s, (22, 32, 88), (0, y + off), (ANCHO, y + off))
        self.texto("ELIGE TU MISIÓN", self.f_titulo, AMARILLO, (ANCHO // 2, 28))
        parpadeo = (self.t_menu // 15) % 2 == 0

        for i, d in enumerate(JEFES):
            col, fila = i % 3, i // 3
            r = pygame.Rect(60 + col * 285, 56 + fila * 164, TARJ_W, TARJ_H)
            sel = i == self.sel
            vencido = i in self.vencidos
            s.blit(self.fondos[i], r.topleft)

            # Retrato animado del jefe (salta cuando está seleccionado)
            salto = int(abs(math.sin(self.t_menu * 0.12)) * 9) if sel and not vencido else 0
            img = self.retrato_jefe(i, 1.2, self.t_menu // 2 if sel else 0, 1)
            pygame.draw.ellipse(s, (0, 0, 0), (r.x + 14, r.bottom - 18, 90, 10))
            if sel:
                brillo(s, (r.x + 58, r.bottom - 70), 70, d["color"], 0.4)
            s.blit(img, (r.x + 8, r.bottom - 14 - 120 - salto))

            # Datos del jefe
            xt = r.x + 122
            self.texto(d["nombre"], self.f_media, BLANCO, (xt, r.y + 12), centrado=False)
            self.texto(TEMAS[i]["nombre"], self.f_mini, (210, 225, 255), (xt, r.y + 40), centrado=False)
            self.texto("ARMA", self.f_mini, (160, 170, 200), (xt, r.y + 62), centrado=False)
            self.texto(d["arma"], self.f_peq, d["color"], (xt, r.y + 77), centrado=False)
            self.texto("DÉBIL A", self.f_mini, (160, 170, 200), (xt, r.y + 100), centrado=False)
            deb = ARMAS[d["debil"]]
            pygame.draw.rect(s, deb["color"], (xt, r.y + 118, 12, 12), border_radius=3)
            pygame.draw.rect(s, BLANCO, (xt, r.y + 118, 12, 12), 1, border_radius=3)
            self.texto(deb["nombre"], self.f_mini, BLANCO, (xt + 17, r.y + 117), centrado=False)

            if vencido:
                veil = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(veil, (0, 0, 0, 150), veil.get_rect(), border_radius=12)
                s.blit(veil, r)
                self.texto("VENCIDO", self.f_media, d["color"], (r.centerx, r.centery - 10))
            if sel:
                pygame.draw.rect(s, AMARILLO if parpadeo else BLANCO, r, 4, border_radius=12)
            else:
                pygame.draw.rect(s, (70, 90, 170), r, 2, border_radius=12)

        # Botón de la fortaleza
        r = pygame.Rect(280, 378, 400, 52)
        abierto = self.castillo_abierto()
        pygame.draw.rect(s, (90, 30, 110) if abierto else (35, 35, 55), r, border_radius=10)
        tmp = pygame.Surface((130, 100), pygame.SRCALPHA)
        dibujar_malvex(tmp, pygame.Rect(15, 22, 100, 64), self.t_menu)
        icono = pygame.transform.scale(tmp, (65, 50))
        if not abierto:
            icono.fill((70, 70, 85, 255), special_flags=pygame.BLEND_RGBA_MULT)
        s.blit(icono, (r.x + 10, r.centery - 25))
        self.texto("FORTALEZA DEL DR. MALVEX" if abierto else "FORTALEZA (bloqueada)", self.f_media,
                   BLANCO if abierto else GRIS, (r.centerx + 36, r.centery))
        if self.sel == 6:
            pygame.draw.rect(s, AMARILLO if parpadeo else BLANCO, r, 4, border_radius=10)

        # Panel de información del elemento seleccionado
        p = pygame.Rect(120, 438, 720, 60)
        panel = pygame.Surface(p.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 130), panel.get_rect(), border_radius=10)
        s.blit(panel, p.topleft)
        pygame.draw.rect(s, (70, 90, 170), p, 2, border_radius=10)
        if self.sel < 6:
            d = JEFES[self.sel]
            arma_deb = d["debil"]
            dador = IDS.index(arma_deb)
            s.blit(self.minis[dador], (p.x + 10, p.y + 3))
            ya = dador in self.vencidos
            self.texto(f"{d['nombre']} es débil a {ARMAS[arma_deb]['nombre']}, el arma de {JEFES[dador]['nombre']}.",
                       self.f_peq, BLANCO, (p.x + 70, p.y + 12), centrado=False)
            if ya:
                self.texto("¡Ya tienes esa arma! Úsala contra él.", self.f_peq, VERDE, (p.x + 70, p.y + 34), centrado=False)
            else:
                self.texto(f"Derrota antes a {JEFES[dador]['nombre']} ({TEMAS[dador]['nombre']}) para conseguirla.",
                           self.f_peq, (200, 215, 255), (p.x + 70, p.y + 34), centrado=False)
        else:
            if abierto:
                msg = ["Enfréntate otra vez a los 6 jefes y al Dr. Malvex.", "¡Todas tus armas estarán a tu disposición!"]
            else:
                msg = [f"Derrota a los 6 jefes para abrirla ({len(self.vencidos)}/6).",
                       "Allí te espera el Dr. Malvex."]
            self.texto(msg[0], self.f_peq, BLANCO, (p.centerx, p.y + 17))
            self.texto(msg[1], self.f_peq, (200, 215, 255), (p.centerx, p.y + 40))
        self.texto("Flechas: elegir   ENTER: comenzar   ESC: volver", self.f_peq, (170, 180, 220), (ANCHO // 2, 523))

    def dibujar_pausa(self):
        s, j = self.pantalla, self.jugador
        veil = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 175))
        s.blit(veil, (0, 0))
        self.texto("PAUSA", self.f_grande, BLANCO, (ANCHO // 2, 90))
        for i, a in enumerate(j.armas):
            y = 170 + i * 42
            if a == j.arma:
                pygame.draw.rect(s, (255, 255, 255), (ANCHO // 2 - 230, y - 17, 460, 34), 2, border_radius=6)
            self.texto(f"{i + 1}. {ARMAS[a]['nombre']}", self.f_media, ARMAS[a]["color"], (ANCHO // 2 - 210, y - 11), centrado=False)
            if a != "buster":
                pygame.draw.rect(s, (45, 45, 58), (ANCHO // 2 + 20, y - 7, 180, 14))
                pygame.draw.rect(s, ARMAS[a]["color"], (ANCHO // 2 + 20, y - 7, int(180 * j.ammo[a] / 28), 14))
        self.texto("P: continuar   ESC: salir al menú   Q/E o 1-7: cambiar arma", self.f_peq, BLANCO, (ANCHO // 2, ALTO - 50))

    def dibujar_intro(self):
        s = self.pantalla
        veil = pygame.Surface((ANCHO, 130), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 170))
        s.blit(veil, (0, ALTO // 2 - 90))
        nombre = TEMAS[self.idx]["nombre"]
        self.texto(f"NIVEL: {nombre.upper()}", self.f_titulo, AMARILLO, (ANCHO // 2, ALTO // 2 - 55))
        if self.idx < 6:
            d = JEFES[self.idx]
            self.texto(f"Jefe: {d['nombre']}", self.f_media, d["color"], (ANCHO // 2, ALTO // 2 - 15))
            for m, x in ((1, ANCHO // 2 - 300), (-1, ANCHO // 2 + 300)):
                brillo(s, (x, ALTO // 2 - 25), 60, d["color"], 0.35)
                img = self.retrato_jefe(self.idx, 0.9, self.t, m)
                s.blit(img, (x - img.get_width() // 2, ALTO // 2 - 82))
        else:
            self.texto("Jefe final: DR. MALVEX", self.f_media, (200, 200, 230), (ANCHO // 2, ALTO // 2 - 15))
            x0 = ANCHO // 2 - 3 * 50
            for i in range(6):
                self.minis[i].set_alpha(255)
                s.blit(self.minis[i], (x0 + i * 50 + 4, ALTO // 2 + 50))
        if (self.intro_t // 12) % 2 == 0:
            self.texto("¡LISTO!", self.f_titulo, BLANCO, (ANCHO // 2, ALTO // 2 + 25))

    def dibujar_arma(self):
        s = self.pantalla
        d = JEFES[self.idx]
        s.fill((10, 10, 30))
        for k in range(12):
            a = self.t_menu * 0.03 + k * math.pi / 6
            pygame.draw.line(s, mezclar(d["color"], 0.35), (ANCHO // 2, 250),
                             (ANCHO // 2 + math.cos(a) * 700, 250 + math.sin(a) * 700), 24)
        self.texto(f"¡{d['nombre']} DERROTADO!", self.f_titulo, AMARILLO, (ANCHO // 2, 80))
        # El jefe vencido, a los lados
        for m, x in ((1, 170), (-1, ANCHO - 170)):
            brillo(s, (x, 230), 100, d["color"], 0.4)
            img = self.retrato_jefe(self.idx, 1.5, self.t_menu // 2, m)
            s.blit(img, (x - img.get_width() // 2, 150 + int(math.sin(self.t_menu * 0.06 + m) * 5)))
        tmp = pygame.Surface((70, 64), pygame.SRCALPHA)
        dibujar_robot(tmp, pygame.Rect(22, 14, 26, 40), d["color"], 1, "quieto", self.t_menu)
        brillo(s, (ANCHO // 2, 245), 110, d["color"], 0.45)
        s.blit(pygame.transform.scale(tmp, (175, 160)), (ANCHO // 2 - 87, 165))
        self.texto("ARMA OBTENIDA", self.f_media, BLANCO, (ANCHO // 2, 360))
        self.texto(d["arma"], self.f_grande, d["color"], (ANCHO // 2, 415))
        if len(self.vencidos) == 6:
            self.texto("¡La fortaleza del Dr. Malvex se ha abierto!", self.f_media, AMARILLO, (ANCHO // 2, 470))
        if self.fin_t > 60 and (self.fin_t // 20) % 2 == 0:
            self.texto("ENTER para continuar", self.f_peq, BLANCO, (ANCHO // 2, 515))

    def dibujar_final(self, titulo, color, lineas, galeria=False):
        s = self.pantalla
        s.fill((10, 8, 22))
        self.texto_logo(titulo, self.f_grande, color, (ANCHO // 2, 150))
        for i, l in enumerate(lineas):
            self.texto(l, self.f_media, BLANCO, (ANCHO // 2, 245 + i * 38))
        if galeria:
            # Los seis jefes derrotados, en fila
            for i in range(6):
                x = ANCHO // 2 - 3 * 90 + i * 90 + 17
                brillo(s, (x + 28, 390), 50, JEFES[i]["color"], 0.25)
                img = self.retrato_jefe(i, 0.7, self.t_menu // 2, 1 if i < 3 else -1)
                s.blit(img, (x, 345 + int(math.sin(self.t_menu * 0.07 + i) * 4)))
            self.texto("Todos los jefes han sido derrotados", self.f_peq, (200, 200, 230), (ANCHO // 2, 440))
        if self.fin_t > 60 and (self.fin_t // 20) % 2 == 0:
            self.texto("ENTER para continuar", self.f_peq, AMARILLO, (ANCHO // 2, 495))

    def dibujar(self):
        e = self.estado
        if e == "titulo":
            self.dibujar_titulo()
        elif e == "seleccion":
            self.dibujar_seleccion()
        elif e in ("jugando", "pausa", "intro"):
            self.dibujar_mundo()
            self.dibujar_hud()
            if e == "pausa":
                self.dibujar_pausa()
            elif e == "intro":
                self.dibujar_intro()
        elif e == "arma":
            self.dibujar_arma()
        elif e == "gameover":
            self.dibujar_final("FIN DEL JUEGO", ROJO, ["Te quedaste sin vidas.", "Vuelves a la selección de misión."])
        else:
            self.dibujar_final("¡VICTORIA!", AMARILLO, ["Derrotaste al Dr. Malvex y salvaste al mundo.",
                                                       "¡Gracias por jugar ROCKBOT!"], galeria=True)
        if self.fade > 0:
            veil = pygame.Surface((ANCHO, ALTO))
            veil.set_alpha(int(255 * self.fade / 30))
            self.pantalla.blit(veil, (0, 0))
            self.fade -= 1

    # ------------------------------------------------------------ Eventos
    def tecla_titulo(self, k):
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.audio.reproducir("menu")
            self.estado, self.sel = "seleccion", 0
        elif k == pygame.K_ESCAPE:
            self.salir()

    def tecla_seleccion(self, k):
        s = self.sel
        if k in (pygame.K_LEFT, pygame.K_a) and s < 6:
            s = (s // 3) * 3 + (s % 3 - 1) % 3
        elif k in (pygame.K_RIGHT, pygame.K_d) and s < 6:
            s = (s // 3) * 3 + (s % 3 + 1) % 3
        elif k in (pygame.K_UP, pygame.K_w):
            s = 4 if s == 6 else s - 3 if s >= 3 else (6 if (s == 1 and self.castillo_abierto()) else s + 3)
        elif k in (pygame.K_DOWN, pygame.K_s):
            s = 1 if s == 6 else (s + 3 if s < 3 else (6 if (s == 4 and self.castillo_abierto()) else s - 3))
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if s < 6 and s not in self.vencidos:
                self.audio.reproducir("menu")
                self.vidas = max(self.vidas, 3)
                self.empezar_nivel(s)
            elif s == 6 and self.castillo_abierto():
                self.audio.reproducir("menu")
                self.empezar_nivel(6)
            return
        elif k == pygame.K_ESCAPE:
            self.estado = "titulo"
            return
        if s != self.sel:
            self.audio.reproducir("menu")
        self.sel = s

    def tecla_intro(self, k):
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.intro_t = 1

    def tecla_jugando(self, k):
        j = self.jugador
        if k == pygame.K_p:
            self.estado = "pausa"
        elif k == pygame.K_ESCAPE:
            self.estado = "seleccion"
        elif k == pygame.K_q:
            j.cambiar_arma(-1)
        elif k == pygame.K_e:
            j.cambiar_arma(1)
        elif pygame.K_1 <= k <= pygame.K_7:
            j.elegir_arma(k - pygame.K_1)

    def tecla_pausa(self, k):
        if k == pygame.K_p:
            self.estado = "jugando"
        elif k == pygame.K_ESCAPE:
            self.estado = "seleccion"
        elif k == pygame.K_q:
            self.jugador.cambiar_arma(-1)
        elif k == pygame.K_e:
            self.jugador.cambiar_arma(1)
        elif pygame.K_1 <= k <= pygame.K_7:
            self.jugador.elegir_arma(k - pygame.K_1)

    def tecla_arma(self, k):
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.fin_t > 60:
            self.estado, self.sel = "seleccion", min(self.sel, 5) if not self.castillo_abierto() else 6

    def tecla_gameover(self, k):
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.fin_t > 60:
            self.vidas, self.estado = 3, "seleccion"

    def tecla_victoria(self, k):
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.fin_t > 60:
            self.vencidos = set()
            self.jugador = Jugador()
            self.vidas, self.estado, self.sel = 3, "titulo", 0

    def eventos(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.salir()
            if ev.type != pygame.KEYDOWN:
                continue
            if ev.key == pygame.K_m:
                self.audio.alternar()
            elif ev.key == pygame.K_F11:
                try:
                    pygame.display.toggle_fullscreen()
                except pygame.error:
                    pass
            else:
                getattr(self, "tecla_" + self.estado)(ev.key)

    @staticmethod
    def salir():
        pygame.quit()
        sys.exit()

    def paso(self):
        self.reloj.tick(FPS)
        self.eventos()
        self.t_menu += 1
        if self.estado == "jugando":
            self.actualizar_juego()
        elif self.estado == "intro":
            self.t += 1
            self.actualizar_particulas()
            self.intro_t -= 1
            if self.intro_t <= 0:
                self.estado = "jugando"
        elif self.estado in ("arma", "gameover", "victoria"):
            self.fin_t += 1
        self.dibujar()

        offset = (0, 0)
        if self.temblor > 0 and self.estado == "jugando":
            k = min(5, 1 + self.temblor // 3)
            offset = (random.randint(-k, k), random.randint(-k, k))
            self.ventana.fill(NEGRO)
        self.ventana.blit(self.pantalla, offset)
        pygame.display.flip()

    def ejecutar(self):
        while True:
            self.paso()


if __name__ == "__main__":
    Juego().ejecutar()