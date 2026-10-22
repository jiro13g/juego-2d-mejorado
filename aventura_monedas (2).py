import json
import math
import os
import random
import sys
from array import array

import pygame

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

# ---------------------------------------------------------------- Ajustes
ANCHO, ALTO = 900, 520
FPS = 60

VEL_JUGADOR = 5
GRAVEDAD = 0.65
FUERZA_SALTO = -13
VEL_CAIDA_MAX = 14
REBOTE = -9
FRAMES_COYOTE = 6
FRAMES_BUFFER = 6
FRAMES_INVULNERABLE = 90
FRAMES_ESTRELLA = 360
FRAMES_COMBO = 90
COMBO_MAX = 5
VIDAS_MAX = 3
INICIO = (55, 400)
SUELO_Y = 465

ARCHIVO_RECORDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.json")

# Colores
BLANCO = (255, 255, 255)
NEGRO = (25, 25, 30)
AMARILLO = (255, 210, 30)
AMARILLO_CLARO = (255, 245, 130)
ROJO = (220, 55, 55)
ROJO_CLARO = (255, 130, 130)
AZUL = (40, 80, 220)
NARANJA = (235, 130, 30)
MORADO = (140, 70, 200)
MARRON = (130, 80, 40)
MARRON_OSCURO = (90, 55, 30)
VERDE = (55, 160, 70)
VERDE_OSCURO = (35, 110, 50)
PIEL = (255, 205, 160)
ABISMO = (20, 28, 60)
GRIS = (90, 90, 100)
PANEL = (30, 60, 120)
CIAN = (90, 220, 255)
POLVO = (230, 215, 190)

# ---------------------------------------------------------------- Niveles
# suelos: (x, ancho)          -> los huecos entre ellos son precipicios
# plataformas: (x, y, ancho)
# monedas: (x, y)
# enemigos: (x_min, x_max, y_base, velocidad[, "volador"])
NIVELES = [
    {
        "nombre": "Pradera",
        "tiempo": 40,
        "suelos": [(0, 330), (430, 470)],
        "plataformas": [(140, 385, 150), (350, 320, 150), (570, 380, 150), (690, 270, 130)],
        "monedas": [(190, 350), (240, 350), (400, 285), (455, 285),
                    (620, 345), (735, 235), (810, 430), (500, 430)],
        "enemigos": [(120, 290, 465, 2.0), (480, 780, 465, 3.0)],
    },
    {
        "nombre": "Dos abismos",
        "tiempo": 55,
        "suelos": [(0, 240), (340, 220), (660, 240)],
        "plataformas": [(250, 390, 90), (450, 350, 110), (580, 390, 100),
                        (720, 330, 110), (570, 260, 100)],
        "monedas": [(100, 430), (180, 430), (285, 355), (400, 430), (495, 315),
                    (620, 355), (740, 430), (840, 430), (770, 295), (610, 225)],
        "enemigos": [(360, 525, 465, 2.5), (680, 865, 465, 2.5), (450, 525, 350, 1.5),
                     (260, 600, 250, 1.6, "volador")],
    },
    {
        "nombre": "La torre",
        "tiempo": 65,
        "suelos": [(0, 390), (510, 390)],
        "plataformas": [(30, 395, 100), (180, 335, 100), (30, 275, 100), (180, 215, 100),
                        (395, 395, 120), (400, 300, 110), (400, 200, 110),
                        (640, 395, 100), (790, 335, 100), (640, 275, 100), (790, 215, 100)],
        "monedas": [(60, 360), (210, 300), (60, 240), (210, 180), (445, 360), (445, 265), (445, 165),
                    (670, 360), (820, 300), (670, 240), (820, 180), (150, 430), (580, 430)],
        "enemigos": [(130, 355, 465, 2.5), (540, 865, 465, 3.0), (395, 480, 395, 1.5),
                     (200, 500, 250, 1.6, "volador")],
    },
    {
        "nombre": "Las islas",
        "tiempo": 70,
        "suelos": [(0, 200), (700, 200)],
        "plataformas": [(230, 410, 90), (360, 360, 90), (490, 410, 90), (620, 360, 80),
                        (300, 270, 100), (450, 220, 100), (600, 270, 100)],
        "monedas": [(265, 375), (395, 325), (525, 375), (650, 325), (335, 235),
                    (485, 185), (635, 235), (80, 430), (150, 430), (780, 430), (840, 430)],
        "enemigos": [(0, 165, 465, 3.0), (705, 865, 465, 3.5),
                     (490, 545, 410, 1.5), (450, 515, 220, 1.5),
                     (230, 700, 330, 2.0, "volador")],
    },
    {
        "nombre": "El castillo",
        "tiempo": 90,
        "suelos": [(0, 150), (250, 150), (500, 150), (750, 150)],
        "plataformas": [(155, 395, 90), (405, 395, 90), (655, 395, 90),
                        (60, 300, 100), (260, 290, 110), (460, 300, 100), (660, 290, 110),
                        (800, 200, 100), (350, 200, 120), (120, 200, 100)],
        "monedas": [(190, 360), (440, 360), (690, 360), (90, 265), (295, 255),
                    (495, 265), (695, 255), (835, 165), (390, 165), (150, 165),
                    (60, 430), (300, 430), (550, 430), (800, 430)],
        "enemigos": [(250, 365, 465, 3.0), (500, 615, 465, 3.0), (750, 865, 465, 3.5),
                     (350, 435, 200, 2.0), (660, 735, 290, 1.5),
                     (150, 750, 240, 2.2, "volador")],
    },
]

OPCIONES_JUGADORES = [
    ("Un jugador", "Recoge todas las monedas tú solo"),
    ("Dos jugadores", "J1: A / D / W     J2: flechas"),
    ("Jugador vs Computadora", "Compite contra la CPU por las monedas"),
]
OPCIONES_MODO = [
    ("Clásico", "3 vidas y sin límite de tiempo"),
    ("Contrarreloj", "Tiempo límite por nivel y bonus por rapidez"),
]


# Un tema visual por nivel: cielo, tres capas de paisaje (lejos -> cerca), astro, etc.
# astro: (tipo, color, radio, (x, y))
TEMAS = [
    {   # Pradera: día
        "cielo": ((70, 160, 255), (175, 225, 255)),
        "capas": ((150, 200, 215), (110, 175, 150), (70, 150, 90)),
        "nube": BLANCO, "astro": ("sol", (255, 240, 150), 30, (790, 95)),
        "estrellas": False, "pajaros": True, "ave": (50, 60, 80),
    },
    {   # Dos abismos: atardecer
        "cielo": ((95, 90, 175), (255, 175, 105)),
        "capas": ((190, 130, 150), (150, 100, 125), (95, 70, 100)),
        "nube": (255, 205, 190), "astro": ("sol", (255, 190, 110), 38, (230, 330)),
        "estrellas": False, "pajaros": True, "ave": (60, 40, 70),
    },
    {   # La torre: crepúsculo
        "cielo": ((35, 35, 105), (200, 120, 170)),
        "capas": ((120, 90, 150), (85, 65, 120), (55, 45, 90)),
        "nube": (175, 150, 205), "astro": ("luna", (240, 235, 250), 26, (710, 100)),
        "estrellas": True, "pajaros": False, "ave": (30, 30, 50),
    },
    {   # Las islas: tropical
        "cielo": ((40, 190, 230), (195, 248, 240)),
        "capas": ((120, 215, 210), (80, 185, 170), (50, 150, 130)),
        "nube": BLANCO, "astro": ("sol", (255, 250, 200), 32, (150, 90)),
        "estrellas": False, "pajaros": True, "ave": (30, 70, 80),
    },
    {   # El castillo: noche
        "cielo": ((8, 10, 38), (50, 45, 110)),
        "capas": ((45, 45, 95), (32, 32, 72), (20, 20, 50)),
        "nube": (70, 70, 125), "astro": ("luna", (235, 235, 255), 30, (150, 85)),
        "estrellas": True, "pajaros": False, "ave": (30, 30, 50),
    },
]


# ---------------------------------------------------------------- Utilidades
CLAVE = (255, 0, 255)


def crear_cielo(arriba, abajo):
    """Degradado vertical, se dibuja una sola vez."""
    cielo = pygame.Surface((ANCHO, ALTO))
    for y in range(ALTO):
        t = y / ALTO
        color = tuple(int(a + (b - a) * t) for a, b in zip(arriba, abajo))
        pygame.draw.line(cielo, color, (0, y), (ANCHO, y))
    return cielo


def crear_capa(color, base, amplitud, forma, k1, k2, fase, arboles=0, semilla=1):
    """Franja de montañas/colinas que se repite horizontalmente sin costuras.
    Devuelve (superficie, y_superior)."""
    def altura(x):
        if forma == "pico":
            h = (0.7 * (1 - abs(math.sin(math.pi * k1 * x / ANCHO + fase)))
                 + 0.3 * (1 - abs(math.sin(math.pi * k2 * x / ANCHO + fase * 2))))
        else:
            a = 2 * math.pi * x / ANCHO
            h = 0.5 + 0.35 * math.sin(k1 * a + fase) + 0.15 * math.sin(k2 * a + fase * 2)
        return base - amplitud * h

    top = max(0, int(base - amplitud) - (36 if arboles else 2))
    sup = pygame.Surface((ANCHO, ALTO - top))
    sup.fill(CLAVE)
    sup.set_colorkey(CLAVE)
    puntos = [(0, ALTO - top)]
    puntos += [(x, altura(x) - top) for x in range(0, ANCHO + 1, 6)]
    puntos.append((ANCHO, ALTO - top))
    pygame.draw.polygon(sup, color, puntos)

    if arboles:
        rng = random.Random(semilla)
        verde = tuple(int(c * 0.8) for c in color)
        for _ in range(arboles):
            x = rng.randint(30, ANCHO - 30)
            y = altura(x) - top + 3
            h = rng.randint(24, 34)
            pygame.draw.rect(sup, verde, (x - 1, y - 5, 3, 7))
            for j in range(3):
                w = 11 - j * 3
                ty = y - 6 - j * h / 3
                pygame.draw.polygon(sup, verde, [(x - w, ty), (x + w, ty), (x, ty - h / 2.2)])
    return sup, top


def crear_astro(tipo, color, radio):
    """Sol o luna con un halo suave."""
    tam = radio * 5
    sup = pygame.Surface((tam, tam), pygame.SRCALPHA)
    c = tam // 2
    for i in range(10, 0, -1):
        pygame.draw.circle(sup, (*color, 8 + (10 - i) * 6), (c, c), radio + i * radio // 5)
    pygame.draw.circle(sup, color, (c, c), radio)
    if tipo == "luna":
        crater = tuple(int(v * 0.85) for v in color)
        e = radio / 30
        for dx, dy, rr in ((-8, -6, 6), (7, 5, 5), (-3, 10, 3), (10, -9, 3)):
            pygame.draw.circle(sup, crater, (int(c + dx * e), int(c + dy * e)), max(1, int(rr * e)))
    return sup


def cargar_records():
    try:
        with open(ARCHIVO_RECORDS, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return {str(k): int(v) for k, v in datos.items()}
    except (OSError, ValueError, TypeError):
        return {}


def guardar_records(records):
    try:
        with open(ARCHIVO_RECORDS, "w", encoding="utf-8") as f:
            json.dump(records, f)
    except OSError:
        pass


# ---------------------------------------------------------------- Audio (sintetizado, sin archivos)
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
        self.sonidos = {
            "moneda": self._unir(o(988, 988, 0.05, 0.25, "cuadrada"), o(1319, 1319, 0.12, 0.25, "cuadrada")),
            "salto": self._unir(o(280, 620, 0.14, 0.25, "cuadrada")),
            "aplastar": self._unir(o(420, 120, 0.15, 0.35)),
            "dano": self._unir(o(300, 60, 0.25, 0.35, "cuadrada"), o(0, 0, 0.12, 0.3, "ruido")),
            "item": self._unir(o(523, 523, 0.07, 0.3), o(659, 659, 0.07, 0.3), o(784, 784, 0.12, 0.3)),
            "nivel": self._unir(o(523, 523, 0.1, 0.3), o(659, 659, 0.1, 0.3),
                                o(784, 784, 0.1, 0.3), o(1047, 1047, 0.25, 0.3)),
            "derrota": self._unir(o(392, 392, 0.2, 0.3), o(330, 330, 0.2, 0.3),
                                  o(262, 262, 0.2, 0.3), o(196, 196, 0.4, 0.3)),
            "tic": self._unir(o(1000, 1000, 0.05, 0.2, "cuadrada")),
            "menu": self._unir(o(660, 660, 0.04, 0.2, "cuadrada")),
        }

    def reproducir(self, nombre):
        if self.activo and not self.silencio:
            self.sonidos[nombre].play()

    def alternar(self):
        self.silencio = not self.silencio


# ---------------------------------------------------------------- Jugador
class Jugador:
    def __init__(self, nombre, color, controles=None, bot=False):
        self.nombre = nombre
        self.color = color
        self.controles = controles
        self.bot = bot
        self.rect = pygame.Rect(0, 0, 34, 45)

        self.puntos = 0
        self.vidas = VIDAS_MAX
        self.activo = True

        # Estado de la IA
        self.objetivo = None
        self.meta = None
        self.ia_timer = 0
        self.ia_dist = 9999

        self.inicio = INICIO
        self.reiniciar_posicion(*INICIO)

    def reiniciar_posicion(self, x=None, y=None):
        if x is not None:
            self.inicio = (x, y)
        self.x, self.y = float(self.inicio[0]), float(self.inicio[1])
        self.vx = 0.0
        self.vy = 0.0
        self.en_suelo = False
        self.coyote = 0
        self.buffer = 0
        self.salto_prev = False
        self.mirando = 1
        self.invulnerable = 0
        self.estrella = 0
        self.dolor = 0
        self.feliz = 0
        self.combo = 0
        self.combo_timer = 0
        self.evento_salto = False
        self.evento_aterrizar = 0.0
        self.prev_bottom = self.inicio[1] + self.rect.height
        self._sincronizar()

    def _sincronizar(self):
        self.rect.topleft = (round(self.x), round(self.y))

    # ---- Entrada humana
    def leer_teclas(self, teclas):
        c = self.controles
        izq = any(teclas[k] for k in c["izq"])
        der = any(teclas[k] for k in c["der"])
        salto = any(teclas[k] for k in c["salto"])
        return int(der) - int(izq), salto

    # ---- IA sencilla para el modo contra la computadora
    def hay_peligro(self, direccion, superficies):
        """True si delante no hay suelo (precipicio)."""
        r = self.rect
        px = r.centerx + direccion * (r.width // 2 + 22)
        for s in superficies:
            if s.left <= px <= s.right and s.top >= r.bottom - 4:
                return False
        return True

    def decidir_ia(self, monedas, enemigos, superficies):
        r = self.rect
        if not monedas:
            return 0, False

        if self.objetivo is None or self.objetivo not in monedas:
            self.objetivo = min(
                monedas,
                key=lambda m: abs(m.centerx - r.centerx) + 2 * abs(m.centery - r.centery),
            )
            self.ia_dist, self.ia_timer = 9999, 0
            self.meta = None
        obj = self.objetivo

        # La meta se decide en el suelo y se mantiene mientras está en el aire
        if self.en_suelo or self.meta is None:
            meta_x, meta_y = obj.centerx, obj.centery
            # Si la moneda está muy alta, usa una plataforma intermedia
            if meta_y < r.bottom - 125:
                mejor, mejor_valor = None, None
                for s in superficies:
                    subida = r.bottom - s.top
                    hueco = max(0, s.left - r.right, r.left - s.right)
                    if subida < 20 or subida > 110 or hueco > 110:
                        continue
                    valor = abs(s.centerx - obj.centerx) + 2 * abs(s.top - obj.centery)
                    if mejor_valor is None or valor < mejor_valor:
                        mejor, mejor_valor = s, valor
                if mejor is not None:
                    meta_x, meta_y = mejor.centerx, mejor.top - 30
            self.meta = (meta_x, meta_y)
        meta_x, meta_y = self.meta

        dx = meta_x - r.centerx
        dy = meta_y - r.centery
        direccion = 0 if abs(dx) < 8 else (1 if dx > 0 else -1)

        # Si no avanza hacia la moneda, prueba con otra
        self.ia_timer += 1
        if self.ia_timer >= 90:
            distancia = abs(obj.centerx - r.centerx) + abs(obj.centery - r.centery)
            if distancia > self.ia_dist - 20:
                self.objetivo = random.choice(monedas)
                distancia = 9999
            self.ia_dist, self.ia_timer = distancia, 0

        salto = False
        if self.en_suelo:
            if direccion and self.hay_peligro(direccion, superficies):
                salto = True
            for e in enemigos:
                if e.vivo and abs(e.rect.centery - r.centery) < 40:
                    dist = (e.rect.centerx - r.centerx) * (direccion or 1)
                    if 0 < dist < 90:
                        salto = True
            if dy < -25 and abs(dx) < 140:
                salto = True
        elif self.vy < 0:
            salto = True  # mantener pulsado mientras sube
        return direccion, salto

    # ---- Física
    def actualizar(self, direccion, salto_pulsado, superficies):
        self.evento_salto = False
        self.evento_aterrizar = 0.0

        objetivo = direccion * VEL_JUGADOR
        self.vx += (objetivo - self.vx) * (0.3 if direccion else 0.2)
        if direccion == 0 and abs(self.vx) < 0.1:
            self.vx = 0
        if direccion:
            self.mirando = direccion

        self.x += self.vx
        self.x = max(0, min(self.x, ANCHO - self.rect.width))

        # Salto con coyote time y buffer
        if salto_pulsado and not self.salto_prev:
            self.buffer = FRAMES_BUFFER
        self.salto_prev = salto_pulsado

        self.coyote = FRAMES_COYOTE if self.en_suelo else max(0, self.coyote - 1)
        self.buffer = max(0, self.buffer - 1)

        if self.buffer > 0 and self.coyote > 0:
            self.vy = FUERZA_SALTO
            self.buffer = 0
            self.coyote = 0
            self.evento_salto = True

        # Salto variable
        if self.vy < -4 and not salto_pulsado:
            self.vy *= 0.85

        # Gravedad y colisión con plataformas de un solo sentido
        self.prev_bottom = self.rect.bottom
        vy_antes = self.vy
        self.vy = min(self.vy + GRAVEDAD, VEL_CAIDA_MAX)
        self.y += self.vy
        self._sincronizar()

        estaba_en_suelo = self.en_suelo
        self.en_suelo = False
        if self.vy >= 0:
            for s in superficies:
                if self.rect.colliderect(s) and self.prev_bottom <= s.top:
                    self.y = s.top - self.rect.height
                    self.vy = 0
                    self.en_suelo = True
                    self._sincronizar()
                    break
        if self.en_suelo and not estaba_en_suelo:
            self.evento_aterrizar = vy_antes

        if self.invulnerable > 0:
            self.invulnerable -= 1
        if self.estrella > 0:
            self.estrella -= 1
        if self.dolor > 0:
            self.dolor -= 1
        if self.feliz > 0:
            self.feliz -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 0

    def dibujar(self, sup, frames, fuente_etiqueta=None):
        if self.invulnerable > 0 and self.estrella == 0 and (self.invulnerable // 4) % 2 == 0:
            return

        r = self.rect
        caminando = self.en_suelo and abs(self.vx) > 1

        # Aura de estrella (parpadea cuando va a terminar)
        if self.estrella > 0 and (self.estrella > 90 or (self.estrella // 5) % 2):
            tono = (frames * 6) % 360
            aura = pygame.Color(0)
            aura.hsva = (tono, 60, 100, 100)
            pygame.draw.ellipse(sup, aura, r.inflate(16, 14), width=4)

        self._dibujar_piernas(sup, frames, caminando)
        pygame.draw.rect(sup, self.color, (r.x, r.y, r.width, 30), border_radius=7)
        cinturon = tuple(int(c * 0.65) for c in self.color)
        pygame.draw.rect(sup, cinturon, (r.x + 1, r.y + 25, r.width - 2, 4))

        estado = self._expresion()
        paso = math.sin(frames * 0.35) if caminando else 0.0
        self._dibujar_brazos(sup, frames, estado, paso)
        self._dibujar_cabeza(sup, frames, estado)

        if fuente_etiqueta is not None:
            etiqueta = fuente_etiqueta.render(self.nombre, True, self.color)
            sup.blit(etiqueta, etiqueta.get_rect(center=(r.centerx, r.y - 14)))

    # ---- Piernas
    def _dibujar_piernas(self, sup, frames, caminando):
        r = self.rect
        m = self.mirando
        cadera = r.y + 27
        tobillo = r.bottom - 6
        pantalon = tuple(int(c * 0.55) for c in self.color)
        fase = frames * 0.35
        for lado in (-1, 1):
            hx = r.centerx + lado * 7
            if not self.en_suelo:
                if self.vy < 0:   # encogidas al subir
                    fx = hx + m * 3 + lado
                    fy = cadera + (7 if lado == m else 10)
                else:             # abiertas al caer
                    fx = hx + lado * 5
                    fy = cadera + 12
            elif caminando:       # paso alternado, la pierna se levanta al avanzar
                ang = fase + (math.pi if lado < 0 else 0)
                fx = hx + math.sin(ang) * 7
                fy = tobillo - max(0, math.cos(ang)) * 5
            else:
                fx, fy = hx, tobillo
            fx, fy = round(fx), round(fy)
            pygame.draw.line(sup, pantalon, (hx, cadera), (fx, fy), 7)
            pygame.draw.ellipse(sup, MARRON_OSCURO, (fx - 7 + m * 2, fy - 1, 14, 7))

    # ---- Expresiones y brazos
    def _expresion(self):
        if self.dolor > 0:
            return "dolor"
        if self.estrella > 0 or self.feliz > 0:
            return "feliz"
        if not self.en_suelo:
            if self.vy < -1:
                return "salto"
            if self.vy > 3:
                return "miedo"
        return "normal"

    def _dibujar_brazos(self, sup, frames, estado, paso):
        r = self.rect
        sy = r.y + 22
        largo = 15
        manga = tuple(int(c * 0.75) for c in self.color)
        for lado, sx in ((-1, r.x + 1), (1, r.right - 1)):
            if estado == "salto":
                ang = lado * 2.7
            elif estado == "miedo":
                ang = lado * (1.9 + 0.25 * math.sin(frames * 0.5 + (lado > 0)))
            elif estado == "feliz":
                ang = lado * (2.6 + 0.3 * math.sin(frames * 0.4))
            elif estado == "dolor":
                ang = lado * (1.5 + 0.4 * math.sin(frames * 0.8))
            elif paso:
                ang = lado * (0.15 - 0.9 * paso)
            else:
                ang = lado * (0.2 + 0.04 * math.sin(frames * 0.08))
            fin = (sx + largo * math.sin(ang), sy + largo * math.cos(ang))
            pygame.draw.line(sup, manga, (sx, sy), fin, 6)
            pygame.draw.circle(sup, manga, (round(sx), sy), 3)
            pygame.draw.circle(sup, PIEL, (round(fin[0]), round(fin[1])), 4)

    def _dibujar_cabeza(self, sup, frames, estado):
        r = self.rect
        cx, m = r.centerx, self.mirando
        pygame.draw.circle(sup, PIEL, (cx, r.y + 7), 12)

        # Gorra del color del jugador
        pygame.draw.circle(sup, self.color, (cx, r.y + 3), 12, draw_top_left=True, draw_top_right=True)
        pygame.draw.rect(sup, self.color, (cx if m > 0 else cx - 14, r.y + 1, 14, 4), border_radius=2)

        ey, my = r.y + 8, r.y + 14.5
        fx = cx + m * 2
        ojos = (fx - 4, fx + 4)
        parpadeo = estado == "normal" and frames % 160 < 6

        if estado == "feliz":
            for lado in (-1, 1):
                pygame.draw.circle(sup, (255, 160, 160), (fx + lado * 8, round(my) - 2), 2)

        for i, ex in enumerate(ojos):
            if estado == "dolor":
                pygame.draw.line(sup, NEGRO, (ex - 2, ey - 2), (ex + 2, ey + 2), 2)
                pygame.draw.line(sup, NEGRO, (ex - 2, ey + 2), (ex + 2, ey - 2), 2)
            elif estado == "feliz":
                pygame.draw.arc(sup, NEGRO, (ex - 3, ey - 2, 6, 6), 0, math.pi, 2)
            elif parpadeo:
                pygame.draw.line(sup, NEGRO, (ex - 3, ey), (ex + 3, ey), 2)
            else:
                grande = estado in ("salto", "miedo")
                pygame.draw.circle(sup, BLANCO, (ex, ey), 4 if grande else 3)
                pygame.draw.circle(sup, NEGRO, (ex + m, ey), 1 if estado == "miedo" else 2)
            if estado in ("miedo", "dolor"):  # cejas preocupadas
                a, b = (ey - 4, ey - 7) if i == 0 else (ey - 7, ey - 4)
                pygame.draw.line(sup, NEGRO, (ex - 3, a), (ex + 3, b), 2)

        my = round(my)
        if estado == "feliz":
            pygame.draw.ellipse(sup, NEGRO, (fx - 5, my - 3, 10, 8))
            pygame.draw.rect(sup, PIEL, (fx - 5, my - 3, 10, 3))
        elif estado == "salto":
            pygame.draw.ellipse(sup, NEGRO, (fx - 3, my - 3, 6, 7))
        elif estado == "dolor":
            pygame.draw.ellipse(sup, NEGRO, (fx - 4, my - 3, 8, 7))
        elif estado == "miedo":
            pygame.draw.arc(sup, NEGRO, (fx - 4, my - 1, 8, 6), 0, math.pi, 2)
        else:
            pygame.draw.arc(sup, NEGRO, (fx - 4, my - 4, 8, 6), math.pi, 2 * math.pi, 2)


# ---------------------------------------------------------------- Enemigo
class Enemigo:
    def __init__(self, x_min, x_max, y_base, velocidad, tipo="suelo"):
        self.x_min, self.x_max = x_min, x_max
        self.velocidad = velocidad
        self.tipo = tipo
        self.y_base = y_base
        self.rect = pygame.Rect(x_min, y_base - 35, 35, 35)
        self.reaparecer()

    def reaparecer(self):
        self.x = float(self.x_min)
        self.direccion = 1
        self.vivo = True
        self.espera = 0
        self.fase = 0.0
        self.rect.x = self.x_min
        self.rect.y = self.y_base - 35

    def derrotar(self):
        self.vivo = False
        self.espera = 300  # reaparece a los 5 segundos

    def actualizar(self):
        if not self.vivo:
            self.espera -= 1
            if self.espera <= 0:
                self.reaparecer()
            return

        self.x += self.velocidad * self.direccion
        if self.x <= self.x_min:
            self.x, self.direccion = self.x_min, 1
        elif self.x >= self.x_max:
            self.x, self.direccion = self.x_max, -1
        self.rect.x = round(self.x)

        if self.tipo == "volador":
            self.fase += 0.06
            self.rect.y = round(self.y_base - 35 + math.sin(self.fase) * 40)

    def dibujar(self, sup, frames=0):
        if not self.vivo:
            return
        r = self.rect
        if self.tipo == "volador":
            aleteo = math.sin(frames * 0.35) * 8
            for lado in (-1, 1):
                cx = r.centerx + lado * 14
                pygame.draw.polygon(sup, MORADO, [
                    (r.centerx + lado * 8, r.y + 14),
                    (cx + lado * 12, r.y + 4 + aleteo),
                    (cx + lado * 10, r.y + 22 + aleteo * 0.5)])
            pygame.draw.ellipse(sup, (95, 50, 160), r)
            for ox in (11, 24):
                pygame.draw.circle(sup, BLANCO, (r.x + ox, r.y + 15), 5)
                pygame.draw.circle(sup, NEGRO, (r.x + ox + 2 * self.direccion, r.y + 15), 2)
            pygame.draw.line(sup, NEGRO, (r.x + 7, r.y + 7), (r.x + 15, r.y + 11), 3)
            pygame.draw.line(sup, NEGRO, (r.x + 28, r.y + 7), (r.x + 20, r.y + 11), 3)
            cx = r.centerx
            pygame.draw.ellipse(sup, NEGRO, (cx - 6, r.y + 22, 12, 7))
            pygame.draw.polygon(sup, BLANCO, [(cx - 5, r.y + 23), (cx - 2, r.y + 23), (cx - 4, r.y + 28)])
            pygame.draw.polygon(sup, BLANCO, [(cx + 2, r.y + 23), (cx + 5, r.y + 23), (cx + 4, r.y + 28)])
            return

        pygame.draw.rect(sup, ROJO, (r.x, r.y, r.width, 28), border_radius=8)
        for ox in (10, 25):
            pygame.draw.circle(sup, BLANCO, (r.x + ox, r.y + 14), 5)
            pygame.draw.circle(sup, NEGRO, (r.x + ox + 2 * self.direccion, r.y + 14), 2)
        pygame.draw.line(sup, NEGRO, (r.x + 4, r.y + 6), (r.x + 14, r.y + 10), 3)
        pygame.draw.line(sup, NEGRO, (r.x + 31, r.y + 6), (r.x + 21, r.y + 10), 3)

        # Boca con dientes, pies y bracitos que se balancean
        cx = r.centerx
        pygame.draw.ellipse(sup, NEGRO, (cx - 8, r.y + 20, 16, 7))
        pygame.draw.polygon(sup, BLANCO, [(cx - 6, r.y + 21), (cx - 2, r.y + 21), (cx - 4, r.y + 25)])
        pygame.draw.polygon(sup, BLANCO, [(cx + 2, r.y + 21), (cx + 6, r.y + 21), (cx + 4, r.y + 25)])
        t = (int(self.x) // 8) % 2
        for lado in (-1, 1):
            subir = 3 if (t == 1) == (lado == 1) else 0
            hx = cx + lado * 8
            fy = r.bottom - 6 - subir
            pygame.draw.line(sup, (170, 35, 35), (hx, r.y + 24), (hx, fy), 5)
            pygame.draw.ellipse(sup, MARRON_OSCURO, (hx - 7 + self.direccion * 2, fy - 1, 14, 7))
        sw = 4 if t else -4
        for lado, sx in ((-1, r.x + 1), (1, r.right - 1)):
            fin = (sx + lado * 7, r.y + 24 + sw * lado)
            pygame.draw.line(sup, (170, 35, 35), (sx, r.y + 22), fin, 4)
            pygame.draw.circle(sup, (170, 35, 35), fin, 3)


# ---------------------------------------------------------------- Objeto (power-up)
class Objeto:
    def __init__(self, tipo, x, y):
        self.tipo = tipo            # "corazon" o "estrella"
        self.rect = pygame.Rect(0, 0, 26, 26)
        self.rect.center = (x, y)
        self.vida = 480
        self.edad = 0


# ---------------------------------------------------------------- Juego
class Juego:
    def __init__(self):
        flags = pygame.SCALED | pygame.RESIZABLE
        try:
            self.ventana = pygame.display.set_mode((ANCHO, ALTO), flags)
        except pygame.error:
            self.ventana = pygame.display.set_mode((ANCHO, ALTO))
        self.pantalla = pygame.Surface((ANCHO, ALTO))
        pygame.display.set_caption("La aventura de las monedas")
        self.reloj = pygame.time.Clock()
        self.audio = Audio()

        self.fuente = pygame.font.SysFont("Arial", 25, bold=True)
        self.fuente_media = pygame.font.SysFont("Arial", 21, bold=True)
        self.fuente_pequena = pygame.font.SysFont("Arial", 17)
        self.fuente_etiqueta = pygame.font.SysFont("Arial", 15, bold=True)
        self.fuente_grande = pygame.font.SysFont("Arial", 48, bold=True)

        # Fondo con parallax: cielo + capas por tema
        self.cielos = [crear_cielo(*t["cielo"]) for t in TEMAS]
        self.astros = [crear_astro(*t["astro"][:3]) for t in TEMAS]
        self.capas = []
        for i, t in enumerate(TEMAS):
            lejos, medio, cerca = t["capas"]
            lista = []
            for (sup, top), vel, k in (
                (crear_capa(lejos, 330, 120, "pico", 3, 7, 0.6), 0.08, 0.03),
                (crear_capa(medio, 400, 80, "colina", 2, 5, 1.3 + i), 0.20, 0.07),
                (crear_capa(cerca, 452, 45, "colina", 3, 7, 2.1 + i, arboles=14, semilla=i + 5), 0.45, 0.14),
            ):
                lista.append((sup, top, vel, k))
            self.capas.append(lista)
        rng = random.Random(3)
        self.estrellas_bg = [(rng.randint(0, ANCHO), rng.randint(0, 300), rng.choice((1, 1, 2)),
                              rng.uniform(0, 6.28)) for _ in range(70)]
        self.pajaros = [[random.randint(0, ANCHO), random.randint(60, 200),
                         random.uniform(0.6, 1.4), random.uniform(0, 6)] for _ in range(4)]
        self.t_fondo = 0
        self.cam_x = ANCHO / 2
        self.capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        self.capa.fill((0, 0, 0, 175))
        self.negro = pygame.Surface((ANCHO, ALTO))
        self.negro.fill((0, 0, 0))

        self.nubes = [[140, 75, 1.0, 0.15], [680, 105, 1.2, 0.10], [420, 45, 0.8, 0.20],
                      [830, 55, 0.9, 0.12], [20, 135, 0.7, 0.18]]
        self.records = cargar_records()

        self.modo_jug = 0      # 0 = solo, 1 = dos jugadores, 2 = vs CPU
        self.modo_juego = 0    # 0 = clásico, 1 = contrarreloj
        self.seleccion = 0
        self.estado = "menu_jugadores"

        self.jugadores = []
        self.nivel = 0
        self.particulas = []
        self.textos = []
        self.objetos = []
        self.frames = 0
        self.bloqueo = 0
        self.bonus = 0
        self.motivo = ""
        self.temblor = 0
        self.fade = 0
        self.ultimo_seg = None
        self.nuevo_record = False
        self.suelos, self.plataformas, self.superficies = [], [], []
        self.monedas, self.enemigos = [], []
        self.total_monedas = 0

    # ------------------------------------------------------------ Partida
    def clave(self):
        return f"{self.modo_jug}-{self.modo_juego}"

    def crear_jugadores(self):
        j1 = {"izq": (pygame.K_a, pygame.K_LEFT), "der": (pygame.K_d, pygame.K_RIGHT),
              "salto": (pygame.K_w, pygame.K_UP, pygame.K_SPACE)}
        if self.modo_jug == 0:
            return [Jugador("J1", AZUL, j1)]
        if self.modo_jug == 1:
            c1 = {"izq": (pygame.K_a,), "der": (pygame.K_d,),
                  "salto": (pygame.K_w, pygame.K_SPACE)}
            c2 = {"izq": (pygame.K_LEFT,), "der": (pygame.K_RIGHT,),
                  "salto": (pygame.K_UP,)}
            return [Jugador("J1", AZUL, c1), Jugador("J2", NARANJA, c2)]
        return [Jugador("J1", AZUL, j1), Jugador("CPU", MORADO, bot=True)]

    def nueva_partida(self):
        self.jugadores = self.crear_jugadores()
        self.nivel = 0
        self.bonus = 0
        self.motivo = ""
        self.nuevo_record = False
        self.cargar_nivel(0)
        self.estado = "jugando"

    def cargar_nivel(self, indice):
        datos = NIVELES[indice]
        self.nivel = indice
        self.suelos = [pygame.Rect(x, SUELO_Y, w, ALTO - SUELO_Y) for x, w in datos["suelos"]]
        self.plataformas = [pygame.Rect(x, y, w, 20) for x, y, w in datos["plataformas"]]
        self.superficies = self.suelos + self.plataformas
        self.monedas = [pygame.Rect(x, y, 22, 22) for x, y in datos["monedas"]]
        self.total_monedas = len(self.monedas)
        self.enemigos = [Enemigo(*e) for e in datos["enemigos"]]
        self.particulas = []
        self.textos = []
        self.objetos = []
        self.frames = 0
        self.fade = 40
        self.temblor = 0
        self.ultimo_seg = None

        for k, j in enumerate(self.jugadores):
            if j.activo:
                j.reiniciar_posicion(INICIO[0] + 45 * k, INICIO[1])
                j.invulnerable = FRAMES_INVULNERABLE
                j.objetivo = None
                j.meta = None

    def siguiente_nivel(self):
        self.cargar_nivel(self.nivel + 1)
        self.estado = "jugando"

    @property
    def limite_frames(self):
        return NIVELES[self.nivel]["tiempo"] * FPS

    def terminar(self, estado, motivo=""):
        self.estado = estado
        self.motivo = motivo
        humanos = [j.puntos for j in self.jugadores if not j.bot]
        mejor = max(humanos, default=0)
        clave = self.clave()
        anterior = self.records.get(clave, 0)
        self.nuevo_record = mejor > anterior
        if self.nuevo_record:
            self.records[clave] = mejor
            guardar_records(self.records)
        self.audio.reproducir("nivel" if estado == "ganaste" else "derrota")

    def completar_nivel(self):
        self.bonus = 0
        if self.modo_juego == 1:
            self.bonus = max(0, (self.limite_frames - self.frames) // FPS)
        for j in self.jugadores:
            if j.activo:
                j.puntos += self.bonus
                j.dolor = 0
                j.feliz = 9999
                j.vidas = min(VIDAS_MAX, j.vidas + 1)

        if self.nivel == len(NIVELES) - 1:
            self.terminar("ganaste")
        else:
            self.audio.reproducir("nivel")
            self.estado = "nivel_completo"
            self.bloqueo = 60

    # ------------------------------------------------------------ Lógica
    def crear_particulas(self, x, y, color, cantidad=10):
        for _ in range(cantidad):
            angulo = random.uniform(0, 2 * math.pi)
            vel = random.uniform(1, 4)
            self.particulas.append(
                [x, y, math.cos(angulo) * vel, math.sin(angulo) * vel - 1,
                 random.randint(20, 35), color]
            )

    def crear_polvo(self, x, y, cantidad=6):
        for _ in range(cantidad):
            self.particulas.append(
                [x + random.uniform(-8, 8), y, random.uniform(-1.5, 1.5), random.uniform(-1.2, -0.2),
                 random.randint(12, 22), POLVO]
            )

    def texto_flotante(self, x, y, txt, color=BLANCO):
        self.textos.append([x, y, txt, 40, color])

    def actualizar_particulas(self):
        for p in self.particulas:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.15
            p[4] -= 1
        self.particulas = [p for p in self.particulas if p[4] > 0]
        for t in self.textos:
            t[1] -= 0.7
            t[3] -= 1
        self.textos = [t for t in self.textos if t[3] > 0]

    def mover_nubes(self):
        self.t_fondo += 1
        for nube in self.nubes:
            nube[0] += nube[3]
            if nube[0] > ANCHO + 80:
                nube[0] = -100
        for p in self.pajaros:
            p[0] += p[2]
            if p[0] > ANCHO + 30:
                p[0] = -30
                p[1] = random.randint(60, 200)

        # La cámara de parallax sigue a los jugadores (suavizada)
        objetivo = ANCHO / 2
        if self.estado not in ("menu_jugadores", "menu_modo"):
            xs = [j.x + 17 for j in self.jugadores if j.activo]
            if xs:
                objetivo = sum(xs) / len(xs)
        self.cam_x += (objetivo - self.cam_x) * 0.05

    def perder_vida(self, j):
        j.vidas -= 1
        if j.vidas <= 0:
            j.activo = False
            self.crear_particulas(j.rect.centerx, j.rect.centery, j.color, 16)
            self.temblor = 18
            return False
        return True

    def derrotar_enemigo(self, j, enemigo, rebote=True):
        enemigo.derrotar()
        j.puntos += 50
        j.feliz = 45
        if rebote:
            j.vy = REBOTE
        cx, cy = enemigo.rect.center
        self.crear_particulas(cx, cy, ROJO if enemigo.tipo == "suelo" else MORADO, 14)
        self.texto_flotante(cx, cy - 10, "+50", ROJO_CLARO)
        self.audio.reproducir("aplastar")
        self.temblor = max(self.temblor, 4)

        # A veces suelta un objeto
        azar = random.random()
        if azar < 0.20 and any(p.activo and p.vidas < VIDAS_MAX for p in self.jugadores):
            self.objetos.append(Objeto("corazon", cx, cy))
        elif azar < 0.32:
            self.objetos.append(Objeto("estrella", cx, cy))

    def recoger_moneda(self, j, moneda):
        self.monedas.remove(moneda)
        j.combo = min(COMBO_MAX, j.combo + 1) if j.combo_timer > 0 else 1
        j.combo_timer = FRAMES_COMBO
        j.feliz = 25
        ganancia = 10 * j.combo
        j.puntos += ganancia
        self.crear_particulas(moneda.centerx, moneda.centery, AMARILLO)
        txt = f"+{ganancia}" + (f" x{j.combo}" if j.combo > 1 else "")
        self.texto_flotante(moneda.centerx, moneda.y - 6, txt, AMARILLO_CLARO)
        if not j.bot:
            self.audio.reproducir("moneda")

    def actualizar_objetos(self):
        for obj in self.objetos[:]:
            obj.vida -= 1
            obj.edad += 1
            if obj.vida <= 0:
                self.objetos.remove(obj)
                continue
            for j in self.jugadores:
                if j.activo and j.rect.colliderect(obj.rect):
                    if obj.tipo == "corazon":
                        j.vidas = min(VIDAS_MAX, j.vidas + 1)
                        self.texto_flotante(obj.rect.centerx, obj.rect.y, "+1 vida", ROJO_CLARO)
                        self.crear_particulas(obj.rect.centerx, obj.rect.centery, ROJO_CLARO, 12)
                    else:
                        j.estrella = FRAMES_ESTRELLA
                        self.texto_flotante(obj.rect.centerx, obj.rect.y, "¡Estrella!", AMARILLO)
                        self.crear_particulas(obj.rect.centerx, obj.rect.centery, AMARILLO, 16)
                    self.audio.reproducir("item")
                    self.objetos.remove(obj)
                    break

    def actualizar(self):
        self.mover_nubes()
        self.actualizar_particulas()
        if self.fade > 0:
            self.fade -= 1

        if self.estado == "nivel_completo":
            self.bloqueo = max(0, self.bloqueo - 1)
        if self.estado != "jugando":
            return

        self.frames += 1
        teclas = pygame.key.get_pressed()

        for enemigo in self.enemigos:
            enemigo.actualizar()
        self.actualizar_objetos()

        for j in self.jugadores:
            if not j.activo:
                continue

            if j.bot:
                direccion, salto = j.decidir_ia(self.monedas, self.enemigos, self.superficies)
            else:
                direccion, salto = j.leer_teclas(teclas)
            j.actualizar(direccion, salto, self.superficies)

            # Efectos de salto y aterrizaje
            if j.evento_salto:
                self.crear_polvo(j.rect.centerx, j.rect.bottom, 4)
                if not j.bot:
                    self.audio.reproducir("salto")
            if j.evento_aterrizar > 4:
                self.crear_polvo(j.rect.centerx, j.rect.bottom, 6)

            # Monedas
            for moneda in self.monedas[:]:
                if j.rect.colliderect(moneda):
                    self.recoger_moneda(j, moneda)

            # Enemigos: se aplastan saltando encima (o con la estrella)
            for enemigo in self.enemigos:
                if not enemigo.vivo or not j.rect.colliderect(enemigo.rect):
                    continue
                if j.estrella > 0:
                    self.derrotar_enemigo(j, enemigo, rebote=False)
                elif j.vy > 0 and j.prev_bottom <= enemigo.rect.top + 10:
                    self.derrotar_enemigo(j, enemigo)
                elif j.invulnerable == 0:
                    self.audio.reproducir("dano")
                    self.temblor = 10
                    j.combo, j.combo_timer = 0, 0
                    if self.perder_vida(j):
                        j.invulnerable = FRAMES_INVULNERABLE
                        j.dolor = 40
                        j.vy = -8
                        j.vx = 7 if j.rect.centerx >= enemigo.rect.centerx else -7
                    break

            # Precipicio
            if j.activo and j.rect.top > ALTO:
                self.audio.reproducir("dano")
                self.temblor = 10
                if self.perder_vida(j):
                    j.reiniciar_posicion()
                    j.invulnerable = FRAMES_INVULNERABLE
                    j.dolor = 40

        # Condiciones de fin
        if not any(j.activo for j in self.jugadores):
            self.terminar("perdiste", "FIN DEL JUEGO")
        elif self.modo_juego == 1 and self.frames >= self.limite_frames:
            self.terminar("perdiste", "¡SE ACABÓ EL TIEMPO!")
        elif not self.monedas:
            self.completar_nivel()

        # Pitido en los últimos 10 segundos
        if self.estado == "jugando" and self.modo_juego == 1:
            restante = math.ceil((self.limite_frames - self.frames) / FPS)
            if restante <= 10 and restante != self.ultimo_seg:
                self.audio.reproducir("tic")
            self.ultimo_seg = restante

    # ------------------------------------------------------------ Dibujo
    def texto(self, txt, fuente, color, pos, centrado=False):
        img = fuente.render(txt, True, color)
        sombra = fuente.render(txt, True, NEGRO)
        rect = img.get_rect(center=pos) if centrado else img.get_rect(topleft=pos)
        self.pantalla.blit(sombra, rect.move(2, 2))
        self.pantalla.blit(img, rect)

    def dibujar_corazon(self, x, y, color, e=1.0):
        s = self.pantalla
        radio, off = int(6 * e), int(5 * e)
        pygame.draw.circle(s, color, (x - off, y), radio)
        pygame.draw.circle(s, color, (x + off, y), radio)
        pygame.draw.polygon(s, color, [(x - int(11 * e), y + int(2 * e)),
                                       (x + int(11 * e), y + int(2 * e)),
                                       (x, y + int(16 * e))])

    def dibujar_estrella(self, cx, cy, radio, color):
        puntos = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = radio if i % 2 == 0 else radio * 0.45
            puntos.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        pygame.draw.polygon(self.pantalla, color, puntos)
        pygame.draw.polygon(self.pantalla, NEGRO, puntos, 2)

    def dibujar_fondo(self):
        s = self.pantalla
        i = 0 if self.estado in ("menu_jugadores", "menu_modo") else self.nivel
        tema = TEMAS[i]
        desv = self.cam_x - ANCHO / 2
        t = self.t_fondo

        s.blit(self.cielos[i], (0, 0))

        if tema["estrellas"]:
            for x, y, r, f in self.estrellas_bg:
                b = int(170 + 85 * math.sin(t * 0.04 + f))
                px = int((x - desv * 0.01) % ANCHO)
                pygame.draw.circle(s, (b, b, min(255, b + 20)), (px, y), r)

        astro = self.astros[i]
        ax, ay = tema["astro"][3]
        s.blit(astro, astro.get_rect(center=(int(ax - desv * 0.02), ay)))

        for nube in self.nubes:
            self.dibujar_nube(nube[0] - desv * 0.05 * nube[2], nube[1], nube[2], tema["nube"])

        for sup, top, vel, k in self.capas[i]:
            x0 = -((t * vel + desv * k) % ANCHO)
            s.blit(sup, (int(x0), top))
            s.blit(sup, (int(x0) + ANCHO, top))

        if tema["pajaros"]:
            for x, y, v, f in self.pajaros:
                a = math.sin(t * 0.25 + f) * 4
                yy = y + math.sin(t * 0.03 + f) * 6
                pygame.draw.lines(s, tema["ave"], False,
                                  [(x - 7, yy - a), (x, yy), (x + 7, yy - a)], 2)

    def dibujar_nube(self, x, y, escala, color=BLANCO):
        for dx, dy, radio in ((0, 0, 22), (25, -5, 28), (50, 3, 20)):
            pygame.draw.circle(self.pantalla, color,
                               (int(x + dx * escala), int(y + dy * escala)), int(radio * escala))

    def dibujar_moneda(self, moneda, indice):
        t = self.frames
        flotar = math.sin(t * 0.08 + indice) * 3
        ancho = 3 + 9 * abs(math.cos(t * 0.06 + indice))
        cx, cy = moneda.centerx, moneda.centery + flotar
        pygame.draw.ellipse(self.pantalla, AMARILLO, (cx - ancho, cy - 12, ancho * 2, 24))
        pygame.draw.ellipse(self.pantalla, AMARILLO_CLARO,
                            (cx - ancho * 0.55, cy - 7, ancho * 1.1, 14))

    def dibujar_objeto(self, obj):
        if obj.vida < 120 and (obj.vida // 6) % 2:
            return
        flotar = math.sin(obj.edad * 0.12) * 4
        cx, cy = obj.rect.centerx, int(obj.rect.centery + flotar)
        pygame.draw.circle(self.pantalla, (255, 255, 255), (cx, cy), 18, 2)
        if obj.tipo == "corazon":
            self.dibujar_corazon(cx, cy - 6, ROJO, 1.0)
        else:
            self.dibujar_estrella(cx, cy, 13, AMARILLO)

    def dibujar_mundo(self):
        s = self.pantalla
        self.dibujar_fondo()

        # Precipicios (todo lo que no es suelo)
        pygame.draw.rect(s, ABISMO, (0, SUELO_Y, ANCHO, ALTO - SUELO_Y))
        for suelo in self.suelos:
            pygame.draw.rect(s, MARRON, suelo)
            pygame.draw.rect(s, VERDE, (suelo.x, suelo.y, suelo.width, 14))
            pygame.draw.rect(s, VERDE_OSCURO, (suelo.x, suelo.y + 10, suelo.width, 4))

        for p in self.plataformas:
            pygame.draw.rect(s, MARRON, p, border_radius=3)
            pygame.draw.rect(s, VERDE, (p.x, p.y, p.width, 6), border_radius=3)

        for i, moneda in enumerate(self.monedas):
            self.dibujar_moneda(moneda, i)
        for obj in self.objetos:
            self.dibujar_objeto(obj)
        for enemigo in self.enemigos:
            enemigo.dibujar(s, self.frames)

        etiqueta = self.fuente_etiqueta if len(self.jugadores) > 1 else None
        for j in self.jugadores:
            if j.activo:
                j.dibujar(s, self.frames, etiqueta)

        for x, y, _, _, vida, color in self.particulas:
            pygame.draw.circle(s, color, (int(x), int(y)), max(1, vida // 8))
        for x, y, txt, vida, color in self.textos:
            img = self.fuente_etiqueta.render(txt, True, color)
            sombra = self.fuente_etiqueta.render(txt, True, NEGRO)
            rect = img.get_rect(center=(int(x), int(y)))
            s.blit(sombra, rect.move(1, 1))
            s.blit(img, rect)

    def dibujar_hud(self):
        datos = NIVELES[self.nivel]
        recogidas = self.total_monedas - len(self.monedas)

        if self.modo_juego == 1:
            restante = max(0, math.ceil((self.limite_frames - self.frames) / FPS))
            tiempo = f"Tiempo: {restante}s"
            color = ROJO_CLARO if restante <= 10 else BLANCO
        else:
            tiempo = f"Tiempo: {self.frames // FPS}s"
            color = BLANCO

        self.texto(
            f"Nivel {self.nivel + 1}/{len(NIVELES)}: {datos['nombre']}   -   "
            f"Monedas {recogidas}/{self.total_monedas}   -   {tiempo}",
            self.fuente_media, color, (ANCHO // 2, 20), centrado=True
        )

        for i, j in enumerate(self.jugadores):
            x0 = 20 if i == 0 else ANCHO - 210
            color_texto = BLANCO if j.activo else GRIS
            self.texto(f"{j.nombre}: {j.puntos}", self.fuente_media, color_texto, (x0, 40))
            for v in range(VIDAS_MAX):
                col = ROJO if v < j.vidas else GRIS
                self.dibujar_corazon(x0 + 125 + v * 26, 52, col, 0.8)
            if j.activo and j.combo > 1:
                self.texto(f"Combo x{j.combo}", self.fuente_etiqueta, AMARILLO, (x0, 68))
            if j.activo and j.estrella > 0:
                ancho = int(90 * j.estrella / FRAMES_ESTRELLA)
                pygame.draw.rect(self.pantalla, AMARILLO, (x0 + 90, 70, ancho, 6), border_radius=3)
                self.dibujar_estrella(x0 + 76, 73, 8, AMARILLO)

        if self.modo_jug == 1:
            ayuda = "J1: A/D + W     J2: flechas     P: pausa     M: sonido     ESC: menú"
        else:
            ayuda = "Mover: A/D o flechas  |  Saltar: W, arriba o ESPACIO  |  P: pausa  |  M: sonido  |  ESC: menú"
        self.texto(ayuda, self.fuente_pequena, BLANCO, (ANCHO // 2, 492), centrado=True)

        if self.audio.silencio:
            self.texto("SIN SONIDO", self.fuente_etiqueta, ROJO_CLARO, (ANCHO // 2, 470), centrado=True)

    def lineas_puntuacion(self):
        lineas = [f"{j.nombre}: {j.puntos} puntos" for j in self.jugadores]
        if len(self.jugadores) > 1:
            a, b = self.jugadores[0], self.jugadores[1]
            if a.puntos == b.puntos:
                lineas.append("¡Empate!")
            else:
                ganador = a if a.puntos > b.puntos else b
                lineas.append(f"¡Gana {ganador.nombre}!")
        return lineas

    def dibujar_overlay(self, titulo, color, lineas):
        self.pantalla.blit(self.capa, (0, 0))
        self.texto(titulo, self.fuente_grande, color, (ANCHO // 2, 140), centrado=True)
        for i, linea in enumerate(lineas):
            self.texto(linea, self.fuente, BLANCO, (ANCHO // 2, 205 + i * 38), centrado=True)

    def dibujar_menu(self):
        s = self.pantalla
        self.dibujar_fondo()
        pygame.draw.rect(s, MARRON, (0, SUELO_Y, ANCHO, ALTO - SUELO_Y))
        pygame.draw.rect(s, VERDE, (0, SUELO_Y, ANCHO, 14))

        self.texto("La aventura de las monedas", self.fuente_grande, AMARILLO,
                   (ANCHO // 2, 60), centrado=True)

        en_modo = self.estado == "menu_modo"
        if not en_modo:
            subtitulo, opciones = "¿Cuántos jugadores?", OPCIONES_JUGADORES
        else:
            subtitulo, opciones = "Elige el modo de juego", OPCIONES_MODO
        self.texto(subtitulo, self.fuente, BLANCO, (ANCHO // 2, 125), centrado=True)

        for i, (titulo, descripcion) in enumerate(opciones):
            y = 165 + i * 85
            marco = pygame.Rect(200, y, 500, 70)
            pygame.draw.rect(s, PANEL, marco, border_radius=12)
            if i == self.seleccion:
                pygame.draw.rect(s, AMARILLO, marco, width=4, border_radius=12)
            self.texto(f"{i + 1}. {titulo}", self.fuente, BLANCO, (ANCHO // 2, y + 24), centrado=True)
            self.texto(descripcion, self.fuente_pequena, AMARILLO_CLARO, (ANCHO // 2, y + 52), centrado=True)
            if en_modo:
                rec = self.records.get(f"{self.modo_jug}-{i}", 0)
                if rec:
                    self.texto(f"Récord: {rec}", self.fuente_etiqueta, AMARILLO,
                               (marco.right - 80, y + 10), centrado=True)

        pie = "Flechas arriba/abajo o números para elegir  -  ENTER para aceptar  -  ESC para "
        pie += "volver" if en_modo else "salir"
        self.texto(pie, self.fuente_pequena, BLANCO, (ANCHO // 2, 492), centrado=True)

    def dibujar(self):
        if self.estado in ("menu_jugadores", "menu_modo"):
            self.dibujar_menu()
            return

        self.dibujar_mundo()
        self.dibujar_hud()

        if self.estado == "pausa":
            self.dibujar_overlay("PAUSA", BLANCO, ["Pulsa P para continuar"])
        elif self.estado == "nivel_completo":
            lineas = self.lineas_puntuacion()
            if self.modo_juego == 1:
                lineas.insert(0, f"Bonus de tiempo: +{self.bonus}")
            lineas.append("Pulsa ENTER para continuar")
            self.dibujar_overlay(f"¡NIVEL {self.nivel + 1} COMPLETADO!", AMARILLO, lineas)
        elif self.estado in ("ganaste", "perdiste"):
            lineas = self.lineas_puntuacion()
            if self.nuevo_record:
                lineas.append("¡NUEVO RÉCORD!")
            else:
                lineas.append(f"Mejor puntuación: {self.records.get(self.clave(), 0)}")
            lineas.append("R: jugar de nuevo   |   ENTER: menú")
            if self.estado == "ganaste":
                self.dibujar_overlay("¡GANASTE EL JUEGO!", AMARILLO, lineas)
            else:
                self.dibujar_overlay(self.motivo or "FIN DEL JUEGO", ROJO, lineas)

        if self.fade > 0:
            self.negro.set_alpha(int(255 * self.fade / 40))
            self.pantalla.blit(self.negro, (0, 0))

    # ------------------------------------------------------------ Eventos
    def ir_menu(self):
        self.estado = "menu_jugadores"
        self.seleccion = self.modo_jug

    def aceptar_opcion(self):
        self.audio.reproducir("menu")
        if self.estado == "menu_jugadores":
            self.modo_jug = self.seleccion
            self.estado = "menu_modo"
            self.seleccion = self.modo_juego
        else:
            self.modo_juego = self.seleccion
            self.nueva_partida()

    def evento_menu(self, tecla):
        opciones = OPCIONES_JUGADORES if self.estado == "menu_jugadores" else OPCIONES_MODO
        n = len(opciones)

        if tecla == pygame.K_ESCAPE:
            if self.estado == "menu_modo":
                self.ir_menu()
            else:
                self.salir()
        elif tecla in (pygame.K_UP, pygame.K_w):
            self.seleccion = (self.seleccion - 1) % n
            self.audio.reproducir("menu")
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.seleccion = (self.seleccion + 1) % n
            self.audio.reproducir("menu")
        elif pygame.K_1 <= tecla <= pygame.K_9:
            indice = tecla - pygame.K_1
            if indice < n:
                self.seleccion = indice
                self.aceptar_opcion()
        elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.aceptar_opcion()

    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.salir()
            if evento.type != pygame.KEYDOWN:
                continue

            tecla = evento.key
            if tecla == pygame.K_m:
                self.audio.alternar()
                continue
            if tecla == pygame.K_F11:
                pygame.display.toggle_fullscreen()
                continue

            if self.estado in ("menu_jugadores", "menu_modo"):
                self.evento_menu(tecla)
                continue

            if tecla == pygame.K_ESCAPE:
                self.ir_menu()
            elif tecla == pygame.K_r:
                self.nueva_partida()
            elif tecla == pygame.K_p:
                if self.estado == "jugando":
                    self.estado = "pausa"
                elif self.estado == "pausa":
                    self.estado = "jugando"
            elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.estado == "nivel_completo" and self.bloqueo == 0:
                    self.siguiente_nivel()
                elif self.estado in ("ganaste", "perdiste"):
                    self.ir_menu()

    @staticmethod
    def salir():
        pygame.quit()
        sys.exit()

    def paso(self):
        self.reloj.tick(FPS)
        self.eventos()
        self.actualizar()
        self.dibujar()

        offset = (0, 0)
        if self.temblor > 0:
            intensidad = min(5, 1 + self.temblor // 3)
            offset = (random.randint(-intensidad, intensidad), random.randint(-intensidad, intensidad))
            self.ventana.fill(NEGRO)
            if self.estado != "pausa":
                self.temblor -= 1
        self.ventana.blit(self.pantalla, offset)
        pygame.display.flip()

    def ejecutar(self):
        while True:
            self.paso()


if __name__ == "__main__":
    Juego().ejecutar()
