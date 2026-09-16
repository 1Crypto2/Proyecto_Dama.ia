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
