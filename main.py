"""
Juego de Damas (Checkers) en Python con Kivy - listo para compilar a APK
--------------------------------------------------------------------------
Misma lógica de juego que la versión de Tkinter, pero con Kivy para que
pueda compilarse a Android usando Buildozer.

Requisitos para probarlo en PC (antes de compilar):
    pip install kivy

Para compilar a APK necesitas Linux (o WSL) con Buildozer instalado:
    pip install buildozer cython
    buildozer init          # genera buildozer.spec (o usa el incluido)
    buildozer -v android debug

El .apk queda en la carpeta bin/ al terminar.
"""

import copy
import math
import random

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock

TAM = 8

# ---------------------------------------------------------------------
# Lógica del juego (idéntica a la versión de escritorio)
# ---------------------------------------------------------------------

def tablero_inicial():
    tab = [['.' for _ in range(TAM)] for _ in range(TAM)]
    for fila in range(3):
        for col in range(TAM):
            if (fila + col) % 2 == 1:
                tab[fila][col] = 'n'
    for fila in range(5, 8):
        for col in range(TAM):
            if (fila + col) % 2 == 1:
                tab[fila][col] = 'r'
    return tab


def es_pieza_de(pieza, jugador):
    if jugador == 'r':
        return pieza in ('r', 'R')
    return pieza in ('n', 'N')


def es_dama(pieza):
    return pieza in ('R', 'N')


def oponente(jugador):
    return 'n' if jugador == 'r' else 'r'


def dentro(fila, col):
    return 0 <= fila < TAM and 0 <= col < TAM


def direcciones_pieza(pieza):
    if pieza == 'r':
        return [(-1, -1), (-1, 1)]
    if pieza == 'n':
        return [(1, -1), (1, 1)]
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def generar_movimientos(tab, jugador):
    capturas = []
    simples = []
    for fila in range(TAM):
        for col in range(TAM):
            pieza = tab[fila][col]
            if pieza == '.' or not es_pieza_de(pieza, jugador):
                continue
            capturas += _buscar_capturas(tab, fila, col, pieza, jugador)
            for df, dc in direcciones_pieza(pieza):
                nf, nc = fila + df, col + dc
                if dentro(nf, nc) and tab[nf][nc] == '.':
                    simples.append((fila, col, nf, nc, False, []))
    if capturas:
        return capturas
    return simples


def _buscar_capturas(tab, fila, col, pieza, jugador, capturadas_previas=None, camino_previo=None):
    if capturadas_previas is None:
        capturadas_previas = []
    if camino_previo is None:
        camino_previo = (fila, col)

    resultados = []
    rival = oponente(jugador)

    for df, dc in direcciones_pieza(pieza):
        mf, mc = fila + df, col + dc
        df2, dc2 = fila + 2 * df, col + 2 * dc

        if not dentro(df2, dc2):
            continue
        if tab[mf][mc] == '.' or not es_pieza_de(tab[mf][mc], rival):
            continue
        if tab[df2][dc2] != '.':
            continue
        if (mf, mc) in capturadas_previas:
            continue

        tab_temp = copy.deepcopy(tab)
        tab_temp[fila][col] = '.'
        tab_temp[mf][mc] = '.'
        pieza_final = pieza
        if pieza == 'r' and df2 == 0:
            pieza_final = 'R'
        elif pieza == 'n' and df2 == TAM - 1:
            pieza_final = 'N'
        tab_temp[df2][dc2] = pieza_final

        nueva_lista = capturadas_previas + [(mf, mc)]
        siguientes = _buscar_capturas(tab_temp, df2, dc2, pieza_final, jugador, nueva_lista, camino_previo)

        if siguientes:
            resultados += siguientes
        else:
            resultados.append((camino_previo[0], camino_previo[1], df2, dc2, True, nueva_lista))

    return resultados


def aplicar_movimiento(tab, mov):
    fo, co, fd, cd, es_captura, capturadas = mov
    nuevo = copy.deepcopy(tab)
    pieza = nuevo[fo][co]
    nuevo[fo][co] = '.'
    for (cf, cc) in capturadas:
        nuevo[cf][cc] = '.'
    if pieza == 'r' and fd == 0:
        pieza = 'R'
    elif pieza == 'n' and fd == TAM - 1:
        pieza = 'N'
    nuevo[fd][cd] = pieza
    return nuevo


def contar_piezas(tab):
    r = sum(fila.count('r') + fila.count('R') for fila in tab)
    n = sum(fila.count('n') + fila.count('N') for fila in tab)
    return r, n


def evaluar(tab, jugador_ia):
    valor = 0
    for fila in range(TAM):
        for col in range(TAM):
            pieza = tab[fila][col]
            if pieza == '.':
                continue
            base = 1.7 if es_dama(pieza) else 1
            signo = 1 if es_pieza_de(pieza, jugador_ia) else -1
            centro = 0.05 * (3.5 - abs(3.5 - col)) * (3.5 - abs(3.5 - fila)) / 3.5
            valor += signo * (base + centro)
    r, n = contar_piezas(tab)
    if jugador_ia == 'r' and n == 0:
        valor += 1000
    if jugador_ia == 'n' and r == 0:
        valor += 1000
    if jugador_ia == 'r' and r == 0:
        valor -= 1000
    if jugador_ia == 'n' and n == 0:
        valor -= 1000
    return valor


def minimax(tab, profundidad, alfa, beta, maximizando, jugador_ia, jugador_actual):
    movimientos = generar_movimientos(tab, jugador_actual)
    if profundidad == 0 or not movimientos:
        return evaluar(tab, jugador_ia), None

    mejor_mov = None
    if maximizando:
        mejor_valor = -math.inf
        for mov in movimientos:
            nuevo_tab = aplicar_movimiento(tab, mov)
            valor, _ = minimax(nuevo_tab, profundidad - 1, alfa, beta, False,
                                jugador_ia, oponente(jugador_actual))
            if valor > mejor_valor:
                mejor_valor = valor
                mejor_mov = mov
            alfa = max(alfa, mejor_valor)
            if beta <= alfa:
                break
        return mejor_valor, mejor_mov
    else:
        mejor_valor = math.inf
        for mov in movimientos:
            nuevo_tab = aplicar_movimiento(tab, mov)
            valor, _ = minimax(nuevo_tab, profundidad - 1, alfa, beta, True,
                                jugador_ia, oponente(jugador_actual))
            if valor < mejor_valor:
                mejor_valor = valor
                mejor_mov = mov
            beta = min(beta, mejor_valor)
            if beta <= alfa:
                break
        return mejor_valor, mejor_mov


def mejor_movimiento_ia(tab, jugador_ia, profundidad=5):
    _, mov = minimax(tab, profundidad, -math.inf, math.inf, True, jugador_ia, jugador_ia)
    if mov is None:
        movimientos = generar_movimientos(tab, jugador_ia)
        mov = random.choice(movimientos) if movimientos else None
    return mov


DIFICULTADES = {
    "Fácil": (2, 0.35),
    "Medio": (4, 0.10),
    "Difícil": (6, 0.0),
}


def elegir_movimiento_ia(tab, jugador_ia, profundidad, prob_azar):
    movimientos = generar_movimientos(tab, jugador_ia)
    if not movimientos:
        return None
    if prob_azar > 0 and random.random() < prob_azar:
        return random.choice(movimientos)
    return mejor_movimiento_ia(tab, jugador_ia, profundidad)


# ---------------------------------------------------------------------
# Interfaz gráfica con Kivy
# ---------------------------------------------------------------------

COLOR_CLARA = (0.91, 0.84, 0.72, 1)
COLOR_OSCURA = (0.42, 0.27, 0.14, 1)
COLOR_ROJA = (0.75, 0.22, 0.17, 1)
COLOR_NEGRA = (0.17, 0.17, 0.17, 1)
COLOR_SEL = (0.95, 0.77, 0.06, 1)
COLOR_HINT = (0.18, 0.8, 0.44, 1)


class TableroWidget(GridLayout):
    def __init__(self, app, **kwargs):
        super().__init__(cols=TAM, rows=TAM, **kwargs)
        self.app = app
        self.casillas = []
        for fila in range(TAM):
            fila_widgets = []
            for col in range(TAM):
                casilla = Button(background_normal='', background_down='',
                                  background_color=(0, 0, 0, 0), border=(0, 0, 0, 0))
                casilla.bind(on_release=lambda inst, f=fila, c=col: self.app.al_hacer_clic(f, c))
                self.add_widget(casilla)
                fila_widgets.append(casilla)
            self.casillas.append(fila_widgets)

    def dibujar(self, tablero, seleccion, movimientos_validos):
        for fila in range(TAM):
            for col in range(TAM):
                casilla = self.casillas[fila][col]
                casilla.canvas.before.clear()
                color_fondo = COLOR_CLARA if (fila + col) % 2 == 0 else COLOR_OSCURA
                with casilla.canvas.before:
                    Color(*color_fondo)
                    Rectangle(pos=casilla.pos, size=casilla.size)

                    if seleccion == (fila, col):
                        Color(*COLOR_SEL)
                        Line(rectangle=(casilla.x + 2, casilla.y + 2,
                                        casilla.width - 4, casilla.height - 4), width=2)

                    es_hint = seleccion and any(
                        m[0] == seleccion[0] and m[1] == seleccion[1] and m[2] == fila and m[3] == col
                        for m in movimientos_validos)
                    if es_hint:
                        Color(*COLOR_HINT)
                        Line(circle=(casilla.center_x, casilla.center_y, casilla.width / 2 - 14), width=3)

                    pieza = tablero[fila][col]
                    if pieza != '.':
                        color_pieza = COLOR_ROJA if pieza in ('r', 'R') else COLOR_NEGRA
                        Color(*color_pieza)
                        pad = 10
                        Ellipse(pos=(casilla.x + pad, casilla.y + pad),
                                size=(casilla.width - 2 * pad, casilla.height - 2 * pad))
                        if es_dama(pieza):
                            Color(1, 1, 1, 1)
                            Line(circle=(casilla.center_x, casilla.center_y, casilla.width / 4), width=2)


class DamasApp(App):
    def build(self):
        self.jugador_humano = 'r'
        self.jugador_ia = 'n'
        self.dificultad_actual = "Medio"

        self.tablero = tablero_inicial()
        self.turno = 'r'
        self.seleccion = None
        self.movimientos_validos = generar_movimientos(self.tablero, self.turno)

        raiz = BoxLayout(orientation='vertical', padding=10, spacing=10)

        fila_superior = BoxLayout(size_hint_y=None, height=50, spacing=10)
        fila_superior.add_widget(Label(text="Dificultad:"))
        self.spinner = Spinner(text=self.dificultad_actual, values=list(DIFICULTADES.keys()))
        self.spinner.bind(text=self.cambiar_dificultad)
        fila_superior.add_widget(self.spinner)
        raiz.add_widget(fila_superior)

        self.status = Label(text="Tu turno (rojas)", size_hint_y=None, height=40)
        raiz.add_widget(self.status)

        self.tablero_widget = TableroWidget(self)
        raiz.add_widget(self.tablero_widget)

        boton_reiniciar = Button(text="Reiniciar", size_hint_y=None, height=50)
        boton_reiniciar.bind(on_release=lambda inst: self.reiniciar())
        raiz.add_widget(boton_reiniciar)

        Clock.schedule_once(lambda dt: self.tablero_widget.dibujar(
            self.tablero, self.seleccion, self.movimientos_validos))

        return raiz

    def cambiar_dificultad(self, spinner, texto):
        self.dificultad_actual = texto

    def reiniciar(self):
        self.tablero = tablero_inicial()
        self.turno = 'r'
        self.seleccion = None
        self.movimientos_validos = generar_movimientos(self.tablero, self.turno)
        self.status.text = "Tu turno (rojas)"
        self.tablero_widget.dibujar(self.tablero, self.seleccion, self.movimientos_validos)

    def al_hacer_clic(self, fila, col):
        if self.turno != self.jugador_humano:
            return

        pieza = self.tablero[fila][col]

        if self.seleccion:
            mov = next((m for m in self.movimientos_validos
                        if m[0] == self.seleccion[0] and m[1] == self.seleccion[1]
                        and m[2] == fila and m[3] == col), None)
            if mov:
                self.tablero = aplicar_movimiento(self.tablero, mov)
                self.seleccion = None
                self.turno = oponente(self.turno)
                self.tablero_widget.dibujar(self.tablero, self.seleccion, self.movimientos_validos)
                if self.revisar_fin():
                    return
                Clock.schedule_once(lambda dt: self.turno_ia(), 0.4)
                return

        if pieza != '.' and es_pieza_de(pieza, self.jugador_humano):
            disponibles = [m for m in self.movimientos_validos if m[0] == fila and m[1] == col]
            self.seleccion = (fila, col) if disponibles else None
        else:
            self.seleccion = None

        self.tablero_widget.dibujar(self.tablero, self.seleccion, self.movimientos_validos)

    def turno_ia(self):
        movimientos = generar_movimientos(self.tablero, self.jugador_ia)
        if not movimientos:
            self.status.text = "¡Ganaste! La IA no tiene movimientos."
            return

        self.status.text = "La IA está pensando..."

        def jugar(dt):
            profundidad, prob_azar = DIFICULTADES[self.dificultad_actual]
            mov = elegir_movimiento_ia(self.tablero, self.jugador_ia, profundidad, prob_azar)
            self.tablero = aplicar_movimiento(self.tablero, mov)
            self.turno = oponente(self.turno)
            self.movimientos_validos = generar_movimientos(self.tablero, self.turno)
            self.tablero_widget.dibujar(self.tablero, self.seleccion, self.movimientos_validos)
            self.status.text = "Tu turno (rojas)"
            self.revisar_fin()

        Clock.schedule_once(jugar, 0.05)

    def revisar_fin(self):
        r, n = contar_piezas(self.tablero)
        mensaje = None
        if r == 0:
            mensaje = "La IA gana. Te quedaste sin fichas."
        elif n == 0:
            mensaje = "¡Ganaste! La IA se quedó sin fichas."
        else:
            self.movimientos_validos = generar_movimientos(self.tablero, self.turno)
            if not self.movimientos_validos:
                if self.turno == self.jugador_humano:
                    mensaje = "No tienes movimientos disponibles. Pierdes."
                else:
                    mensaje = "¡Ganaste! La IA no tiene movimientos."

        if mensaje:
            self.status.text = mensaje
            popup = Popup(title="Fin de la partida",
                           content=Label(text=mensaje),
                           size_hint=(0.7, 0.3))
            popup.open()
            return True
        return False


if __name__ == "__main__":
    DamasApp().run()
