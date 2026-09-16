"""
Juego de Damas 8x10 en Python con Kivy
---------------------------------------
8 columnas x 10 filas.

Rojo  = Jugador
Negro = IA

Casillas jugables  = café
Casillas no jugables = blanco apagado
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


# ============================================================
# CONFIGURACIÓN DEL TABLERO
# ============================================================

COLUMNAS = 8
FILAS = 10


# ============================================================
# COLORES
# ============================================================

COLOR_CAFE = (0.45, 0.29, 0.16, 1)
COLOR_BLANCO_APAGADO = (0.86, 0.85, 0.81, 1)

COLOR_ROJA = (0.78, 0.10, 0.08, 1)
COLOR_NEGRA = (0.08, 0.08, 0.08, 1)

COLOR_SELECCION = (0.95, 0.75, 0.05, 1)
COLOR_MOVIMIENTO = (0.15, 0.75, 0.35, 1)

COLOR_BORDE = (0.12, 0.12, 0.12, 1)


# ============================================================
# LÓGICA DEL JUEGO
# ============================================================

def tablero_inicial():

    tab = [
        ['.' for _ in range(COLUMNAS)]
        for _ in range(FILAS)
    ]

    # 4 filas superiores para la IA
    for fila in range(4):
        for col in range(COLUMNAS):
            if (fila + col) % 2 == 1:
                tab[fila][col] = 'n'

    # 4 filas inferiores para el jugador
    for fila in range(FILAS - 4, FILAS):
        for col in range(COLUMNAS):
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

    if jugador == 'r':
        return 'n'

    return 'r'


def dentro(fila, col):

    return (
        0 <= fila < FILAS
        and
        0 <= col < COLUMNAS
    )


def direcciones_pieza(pieza):

    # Rojo sube
    if pieza == 'r':
        return [
            (-1, -1),
            (-1, 1)
        ]

    # Negro baja
    if pieza == 'n':
        return [
            (1, -1),
            (1, 1)
        ]

    # Damas pueden ir en las cuatro direcciones
    return [
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1)
    ]


# ============================================================
# GENERAR MOVIMIENTOS
# ============================================================

def generar_movimientos(tab, jugador):

    capturas = []
    simples = []

    for fila in range(FILAS):

        for col in range(COLUMNAS):

            pieza = tab[fila][col]

            if pieza == '.':
                continue

            if not es_pieza_de(pieza, jugador):
                continue

            # Buscar capturas
            capturas += _buscar_capturas(
                tab,
                fila,
                col,
                pieza,
                jugador
            )

            # Buscar movimientos normales
            for df, dc in direcciones_pieza(pieza):

                nf = fila + df
                nc = col + dc

                if dentro(nf, nc):

                    if tab[nf][nc] == '.':

                        simples.append(
                            (
                                fila,
                                col,
                                nf,
                                nc,
                                False,
                                []
                            )
                        )

    # En damas, si existe una captura,
    # las capturas tienen prioridad.
    if capturas:
        return capturas

    return simples


def _buscar_capturas(
    tab,
    fila,
    col,
    pieza,
    jugador,
    capturadas_previas=None,
    camino_previo=None
):

    if capturadas_previas is None:
        capturadas_previas = []

    if camino_previo is None:
        camino_previo = (fila, col)

    resultados = []

    rival = oponente(jugador)

    for df, dc in direcciones_pieza(pieza):

        mf = fila + df
        mc = col + dc

        destino_fila = fila + (2 * df)
        destino_col = col + (2 * dc)

        if not dentro(mf, mc):
            continue

        if not dentro(destino_fila, destino_col):
            continue

        pieza_en_medio = tab[mf][mc]

        if pieza_en_medio == '.':
            continue

        if not es_pieza_de(pieza_en_medio, rival):
            continue

        if tab[destino_fila][destino_col] != '.':
            continue

        if (mf, mc) in capturadas_previas:
            continue

        tab_temp = copy.deepcopy(tab)

        tab_temp[fila][col] = '.'
        tab_temp[mf][mc] = '.'

        pieza_final = pieza

        # Promoción roja
        if pieza == 'r' and destino_fila == 0:
            pieza_final = 'R'

        # Promoción negra
        elif pieza == 'n' and destino_fila == FILAS - 1:
            pieza_final = 'N'

        tab_temp[destino_fila][destino_col] = pieza_final

        nueva_lista = capturadas_previas + [
            (mf, mc)
        ]

        siguientes = _buscar_capturas(
            tab_temp,
            destino_fila,
            destino_col,
            pieza_final,
            jugador,
            nueva_lista,
            camino_previo
        )

        if siguientes:

            resultados += siguientes

        else:

            resultados.append(
                (
                    camino_previo[0],
                    camino_previo[1],
                    destino_fila,
                    destino_col,
                    True,
                    nueva_lista
                )
            )

    return resultados


# ============================================================
# APLICAR MOVIMIENTO
# ============================================================

def aplicar_movimiento(tab, mov):

    fila_origen = mov[0]
    col_origen = mov[1]

    fila_destino = mov[2]
    col_destino = mov[3]

    capturadas = mov[5]

    nuevo = copy.deepcopy(tab)

    pieza = nuevo[fila_origen][col_origen]

    nuevo[fila_origen][col_origen] = '.'

    # Eliminar piezas capturadas
    for cf, cc in capturadas:
        nuevo[cf][cc] = '.'

    # Promoción
    if pieza == 'r' and fila_destino == 0:
        pieza = 'R'

    elif pieza == 'n' and fila_destino == FILAS - 1:
        pieza = 'N'

    nuevo[fila_destino][col_destino] = pieza

    return nuevo


# ============================================================
# CONTAR PIEZAS
# ============================================================

def contar_piezas(tab):

    rojas = 0
    negras = 0

    for fila in tab:

        for pieza in fila:

            if pieza in ('r', 'R'):
                rojas += 1

            elif pieza in ('n', 'N'):
                negras += 1

    return rojas, negras


# ============================================================
# EVALUACIÓN DE LA IA
# ============================================================

def evaluar(tab, jugador_ia):

    valor = 0

    for fila in range(FILAS):

        for col in range(COLUMNAS):

            pieza = tab[fila][col]

            if pieza == '.':
                continue

            if es_dama(pieza):
                base = 1.7
            else:
                base = 1.0

            if es_pieza_de(pieza, jugador_ia):
                signo = 1
            else:
                signo = -1

            centro_col = (
                3.5 - abs(3.5 - col)
            )

            centro_fila = (
                (FILAS - 1) / 2
                - abs(((FILAS - 1) / 2) - fila)
            )

            centro = (
                0.05
                * centro_col
                * centro_fila
                / 4
            )

            valor += signo * (
                base + centro
            )

    rojas, negras = contar_piezas(tab)

    if jugador_ia == 'r':

        if negras == 0:
            valor += 1000

        if rojas == 0:
            valor -= 1000

    else:

        if rojas == 0:
            valor += 1000

        if negras == 0:
            valor -= 1000

    return valor


# ============================================================
# MINIMAX
# ============================================================

def minimax(
    tab,
    profundidad,
    alfa,
    beta,
    maximizando,
    jugador_ia,
    jugador_actual
):

    movimientos = generar_movimientos(
        tab,
        jugador_actual
    )

    if profundidad == 0 or not movimientos:

        return (
            evaluar(tab, jugador_ia),
            None
        )

    mejor_mov = None

    if maximizando:

        mejor_valor = -math.inf

        for mov in movimientos:

            nuevo_tab = aplicar_movimiento(
                tab,
                mov
            )

            valor, _ = minimax(
                nuevo_tab,
                profundidad - 1,
                alfa,
                beta,
                False,
                jugador_ia,
                oponente(jugador_actual)
            )

            if valor > mejor_valor:

                mejor_valor = valor
                mejor_mov = mov

            alfa = max(
                alfa,
                mejor_valor
            )

            if beta <= alfa:
                break

        return (
            mejor_valor,
            mejor_mov
        )

    else:

        mejor_valor = math.inf

        for mov in movimientos:

            nuevo_tab = aplicar_movimiento(
                tab,
                mov
            )

            valor, _ = minimax(
                nuevo_tab,
                profundidad - 1,
                alfa,
                beta,
                True,
                jugador_ia,
                oponente(jugador_actual)
            )

            if valor < mejor_valor:

                mejor_valor = valor
                mejor_mov = mov

            beta = min(
                beta,
                mejor_valor
            )

            if beta <= alfa:
                break

        return (
            mejor_valor,
            mejor_mov
        )


def mejor_movimiento_ia(
    tab,
    jugador_ia,
    profundidad=5
):

    _, mov = minimax(
        tab,
        profundidad,
        -math.inf,
        math.inf,
        True,
        jugador_ia,
        jugador_ia
    )

    if mov is None:

        movimientos = generar_movimientos(
            tab,
            jugador_ia
        )

        if movimientos:
            mov = random.choice(
                movimientos
            )

    return mov


# ============================================================
# DIFICULTADES
# ============================================================

DIFICULTADES = {

    "Fácil": (
        2,
        0.35
    ),

    "Medio": (
        4,
        0.10
    ),

    "Difícil": (
        6,
        0.0
    )
}


def elegir_movimiento_ia(
    tab,
    jugador_ia,
    profundidad,
    prob_azar
):

    movimientos = generar_movimientos(
        tab,
        jugador_ia
    )

    if not movimientos:
        return None

    if (
        prob_azar > 0
        and random.random() < prob_azar
    ):

        return random.choice(
            movimientos
        )

    return mejor_movimiento_ia(
        tab,
        jugador_ia,
        profundidad
    )


# ============================================================
# TABLERO KIVY
# ============================================================

class TableroWidget(GridLayout):

    def __init__(
        self,
        app,
        **kwargs
    ):

        super().__init__(
            cols=COLUMNAS,
            rows=FILAS,
            spacing=0,
            padding=0,
            **kwargs
        )

        self.app = app

        self.casillas = []

        for fila in range(FILAS):

            fila_widgets = []

            for col in range(COLUMNAS):

                casilla = Button(
                    text='',
                    background_normal='',
                    background_down='',
                    border=(0, 0, 0, 0)
                )

                casilla.bind(
                    on_release=lambda inst,
                    f=fila,
                    c=col:
                    self.app.al_hacer_clic(
                        f,
                        c
                    )
                )

                self.add_widget(casilla)

                fila_widgets.append(
                    casilla
                )

            self.casillas.append(
                fila_widgets
            )

    def dibujar(
        self,
        tablero,
        seleccion,
        movimientos_validos
    ):

        for fila in range(FILAS):

            for col in range(COLUMNAS):

                casilla = self.casillas[fila][col]

                casilla.canvas.before.clear()

                # ------------------------------------------------
                # COLOR DEL CUADRO
                # ------------------------------------------------

                if (fila + col) % 2 == 0:

                    color_fondo = (
                        COLOR_BLANCO_APAGADO
                    )

                else:

                    color_fondo = COLOR_CAFE

                with casilla.canvas.before:

                    Color(
                        *color_fondo
                    )

                    Rectangle(
                        pos=casilla.pos,
                        size=casilla.size
                    )

                    # --------------------------------------------
                    # SELECCIÓN
                    # --------------------------------------------

                    if seleccion == (
                        fila,
                        col
                    ):

                        Color(
                            *COLOR_SELECCION
                        )

                        Line(
                            rectangle=(
                                casilla.x + 3,
                                casilla.y + 3,
                                casilla.width - 6,
                                casilla.height - 6
                            ),
                            width=3
                        )

                    # --------------------------------------------
                    # MOVIMIENTO POSIBLE
                    # --------------------------------------------

                    es_hint = False

                    if seleccion is not None:

                        for mov in movimientos_validos:

                            if (
                                mov[0] == seleccion[0]
                                and
                                mov[1] == seleccion[1]
                                and
                                mov[2] == fila
                                and
                                mov[3] == col
                            ):

                                es_hint = True
                                break

                    if es_hint:

                        Color(
                            *COLOR_MOVIMIENTO
                        )

                        Line(
                            circle=(
                                casilla.center_x,
                                casilla.center_y,
                                min(
                                    casilla.width,
                                    casilla.height
                                ) / 2 - 10
                            ),
                            width=3
                        )

                    # --------------------------------------------
                    # PIEZAS
                    # --------------------------------------------

                    pieza = tablero[fila][col]

                    if pieza != '.':

                        if pieza in ('r', 'R'):

                            color_pieza = COLOR_ROJA

                        else:

                            color_pieza = COLOR_NEGRA

                        Color(
                            *color_pieza
                        )

                        tam = min(
                            casilla.width,
                            casilla.height
                        )

                        pad = tam * 0.12

                        Ellipse(
                            pos=(
                                casilla.center_x - tam / 2 + pad,
                                casilla.center_y - tam / 2 + pad
                            ),
                            size=(
                                tam - 2 * pad,
                                tam - 2 * pad
                            )
                        )

                        # ----------------------------------------
                        # BORDE DE LA FICHA
                        # ----------------------------------------

                        Color(
                            *COLOR_BORDE
                        )

                        Line(
                            circle=(
                                casilla.center_x,
                                casilla.center_y,
                                tam / 2 - pad
                            ),
                            width=1.5
                        )

                        # ----------------------------------------
                        # MARCA DE DAMA
                        # ----------------------------------------

                        if es_dama(pieza):

                            Color(
                                1,
                                0.82,
                                0.15,
                                1
                            )

                            Line(
                                circle=(
                                    casilla.center_x,
                                    casilla.center_y,
                                    tam / 4
                                ),
                                width=3
                            )


# ============================================================
# APLICACIÓN
# ============================================================

class DamasApp(App):

    def build(self):

        # --------------------------------------------
        # CONFIGURACIÓN
        # --------------------------------------------

        self.jugador_humano = 'r'
        self.jugador_ia = 'n'

        self.dificultad_actual = "Medio"

        self.tablero = tablero_inicial()

        self.turno = 'r'

        self.seleccion = None

        self.movimientos_validos = generar_movimientos(
            self.tablero,
            self.turno
        )

        # --------------------------------------------
        # CONTENEDOR PRINCIPAL
        # --------------------------------------------

        raiz = BoxLayout(
            orientation='vertical',
            padding=8,
            spacing=6
        )

        # --------------------------------------------
        # TÍTULO
        # --------------------------------------------

        titulo = Label(
            text="DAMAS 8 × 10",
            size_hint_y=None,
            height=42,
            font_size=22,
            bold=True
        )

        raiz.add_widget(titulo)

        # --------------------------------------------
        # INFORMACIÓN DE JUGADORES
        # --------------------------------------------

        jugadores = BoxLayout(
            size_hint_y=None,
            height=35,
            spacing=8
        )

        jugador_rojo = Label(
            text="🔴 Tú",
            font_size=16
        )

        jugador_negro = Label(
            text="⚫ IA",
            font_size=16
        )

        jugadores.add_widget(
            jugador_rojo
        )

        jugadores.add_widget(
            jugador_negro
        )

        raiz.add_widget(
            jugadores
        )

        # --------------------------------------------
        # DIFICULTAD
        # --------------------------------------------

        fila_superior = BoxLayout(
            size_hint_y=None,
            height=45,
            spacing=8
        )

        fila_superior.add_widget(
            Label(
                text="Dificultad:",
                font_size=16
            )
        )

        self.spinner = Spinner(
            text=self.dificultad_actual,
            values=list(
                DIFICULTADES.keys()
            )
        )

        self.spinner.bind(
            text=self.cambiar_dificultad
        )

        fila_superior.add_widget(
            self.spinner
        )

        raiz.add_widget(
            fila_superior
        )

        # --------------------------------------------
        # ESTADO
        # --------------------------------------------

        self.status = Label(
            text="Tu turno (rojas)",
            size_hint_y=None,
            height=35,
            font_size=15
        )

        raiz.add_widget(
            self.status
        )

        # --------------------------------------------
        # TABLERO
        # --------------------------------------------

        self.tablero_widget = TableroWidget(
            self
        )

        raiz.add_widget(
            self.tablero_widget
        )

        # --------------------------------------------
        # BOTÓN REINICIAR
        # --------------------------------------------

        boton_reiniciar = Button(
            text="Reiniciar partida",
            size_hint_y=None,
            height=48,
            font_size=16
        )

        boton_reiniciar.bind(
            on_release=lambda inst:
            self.reiniciar()
        )

        raiz.add_widget(
            boton_reiniciar
        )

        # --------------------------------------------
        # PRIMER DIBUJO
        # --------------------------------------------

        Clock.schedule_once(
            lambda dt:
            self.tablero_widget.dibujar(
                self.tablero,
                self.seleccion,
                self.movimientos_validos
            ),
            0
        )

        return raiz

    # ========================================================
    # CAMBIAR DIFICULTAD
    # ========================================================

    def cambiar_dificultad(
        self,
        spinner,
        texto
    ):

        self.dificultad_actual = texto

    # ========================================================
    # REINICIAR
    # ========================================================

    def reiniciar(self):

        self.tablero = tablero_inicial()

        self.turno = 'r'

        self.seleccion = None

        self.movimientos_validos = generar_movimientos(
            self.tablero,
            self.turno
        )

        self.status.text = (
            "Tu turno (rojas)"
        )

        self.tablero_widget.dibujar(
            self.tablero,
            self.seleccion,
            self.movimientos_validos
        )

    # ========================================================
    # CLIC EN TABLERO
    # ========================================================

    def al_hacer_clic(
        self,
        fila,
        col
    ):

        # Si está jugando la IA,
        # ignorar clics.
        if self.turno != self.jugador_humano:
            return

        pieza = self.tablero[fila][col]

        # ----------------------------------------------------
        # INTENTAR MOVER LA PIEZA SELECCIONADA
        # ----------------------------------------------------

        if self.seleccion is not None:

            mov = next(
                (
                    m
                    for m in self.movimientos_validos
                    if (
                        m[0] == self.seleccion[0]
                        and
                        m[1] == self.seleccion[1]
                        and
                        m[2] == fila
                        and
                        m[3] == col
                    )
                ),
                None
            )

            if mov is not None:

                # Aplicar movimiento
                self.tablero = aplicar_movimiento(
                    self.tablero,
                    mov
                )

                self.seleccion = None

                # Cambiar turno
                self.turno = oponente(
                    self.turno
                )

                # IMPORTANTE:
                # actualizar movimientos inmediatamente
                self.movimientos_validos = generar_movimientos(
                    self.tablero,
                    self.turno
                )

                self.tablero_widget.dibujar(
                    self.tablero,
                    self.seleccion,
                    self.movimientos_validos
                )

                # Revisar si terminó
                if self.revisar_fin():
                    return

                # Turno IA
                Clock.schedule_once(
                    lambda dt:
                    self.turno_ia(),
                    0.35
                )

                return

        # ----------------------------------------------------
        # SELECCIONAR PIEZA
        # ----------------------------------------------------

        if (
            pieza != '.'
            and
            es_pieza_de(
                pieza,
                self.jugador_humano
            )
        ):

            disponibles = [
                m
                for m in self.movimientos_validos
                if (
                    m[0] == fila
                    and
                    m[1] == col
                )
            ]

            if disponibles:

                self.seleccion = (
                    fila,
                    col
                )

            else:

                self.seleccion = None

        else:

            self.seleccion = None

        self.tablero_widget.dibujar(
            self.tablero,
            self.seleccion,
            self.movimientos_validos
        )

    # ========================================================
    # TURNO DE LA IA
    # ========================================================

    def turno_ia(self):

        if self.turno != self.jugador_ia:
            return

        movimientos = generar_movimientos(
            self.tablero,
            self.jugador_ia
        )

        if not movimientos:

            self.revisar_fin()

            return

        self.status.text = (
            "La IA está pensando..."
        )

        # Evita que el jugador pueda seleccionar
        # mientras la IA está calculando.
        self.seleccion = None

        self.tablero_widget.dibujar(
            self.tablero,
            self.seleccion,
            self.movimientos_validos
        )

        def jugar(dt):

            profundidad, prob_azar = (
                DIFICULTADES[
                    self.dificultad_actual
                ]
            )

            mov = elegir_movimiento_ia(
                self.tablero,
                self.jugador_ia,
                profundidad,
                prob_azar
            )

            if mov is None:

                self.revisar_fin()

                return

            self.tablero = aplicar_movimiento(
                self.tablero,
                mov
            )

            # Cambiar turno
            self.turno = oponente(
                self.turno
            )

            # Actualizar movimientos
            self.movimientos_validos = generar_movimientos(
                self.tablero,
                self.turno
            )

            self.tablero_widget.dibujar(
                self.tablero,
                self.seleccion,
                self.movimientos_validos
            )

            self.status.text = (
                "Tu turno (rojas)"
            )

            self.revisar_fin()

        Clock.schedule_once(
            jugar,
            0.05
        )

    # ========================================================
    # REVISAR FINAL
    # ========================================================

    def revisar_fin(self):

        rojas, negras = contar_piezas(
            self.tablero
        )

        mensaje = None

        # --------------------------------------------
        # SIN FICHAS
        # --------------------------------------------

        if rojas == 0:

            mensaje = (
                "La IA gana.\n"
                "Te quedaste sin fichas."
            )

        elif negras == 0:

            mensaje = (
                "¡Ganaste!\n"
                "La IA se quedó sin fichas."
            )

        else:

            # Actualizar movimientos
            self.movimientos_validos = generar_movimientos(
                self.tablero,
                self.turno
            )

            # ----------------------------------------
            # SIN MOVIMIENTOS
            # ----------------------------------------

            if not self.movimientos_validos:

                if self.turno == self.jugador_humano:

                    mensaje = (
                        "No tienes movimientos disponibles.\n"
                        "La IA gana."
                    )

                else:

                    mensaje = (
                        "¡Ganaste!\n"
                        "La IA no tiene movimientos."
                    )

        # --------------------------------------------
        # MOSTRAR RESULTADO
        # --------------------------------------------

        if mensaje:

            self.status.text = mensaje

            popup = Popup(
                title="Fin de la partida",
                content=Label(
                    text=mensaje,
                    halign='center',
                    valign='middle'
                ),
                size_hint=(0.75, 0.30)
            )

            popup.open()

            return True

        return False


# ============================================================
# INICIAR
# ============================================================

if __name__ == "__main__":

    DamasApp().run()
