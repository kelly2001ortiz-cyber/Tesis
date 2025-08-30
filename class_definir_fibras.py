from PySide6.QtWidgets import QDialog
from ui_definir_fibras import Ui_definir_fibras
from validation_utils2 import (
    ErrorFloatingLabel,
    mostrar_mensaje_error_flotante,
    parsear_numero,
    mostrar_numero,
)

class VentanaDefinirFibras(QDialog):
    def __init__(self, fibras_data, callback_actualizar=None, parent=None):  # <<< nuevo: parent
        super().__init__(parent)  # <<< nuevo: mantener referencia al padre
        self.ui = Ui_definir_fibras()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())

        # Referencia (NO se modifica hasta presionar OK)
        self.fibras_data = fibras_data
        self.callback_actualizar = callback_actualizar

        # Cargar valores actuales a los campos
        self.ui.fibras_x.setText(self.fibras_data.get("fibras_x", ""))
        self.ui.fibras_y.setText(self.fibras_data.get("fibras_y", ""))

        # --- Validación en tiempo real + tooltip de error ---
        self._error_label = ErrorFloatingLabel(self)  # etiqueta flotante reutilizable
        self._campos_invalidos = {}

        for le in (self.ui.fibras_x, self.ui.fibras_y):
            # Validación reactiva mientras escribe
            le.textChanged.connect(lambda _=None, le=le: self._validar_campo(le))
            # Normaliza/ajusta al salir del campo
            le.editingFinished.connect(lambda le=le: self._normalizar_minimo_entero(le, minimo=3))
            # Tooltip de error al entrar/salir
            self._instalar_eventos_tooltip(le)

        # Botones
        self.ui.btn_ok_fibras.clicked.connect(self.guardar_datos)   # guarda y cierra + ahora dibuja fibras
        self.ui.btn_cancelar_fibras.clicked.connect(self.reject)    # NO guarda, solo cierra

    # ---------- Utilidades UI ----------
    def _instalar_eventos_tooltip(self, line_edit):
        old_enter = getattr(line_edit, "enterEvent", None)
        old_leave = getattr(line_edit, "leaveEvent", None)

        def enterEvent(e):
            if self._campos_invalidos.get(line_edit, False):
                mostrar_mensaje_error_flotante(line_edit, self._error_label)
            else:
                self._error_label.hide()
            if callable(old_enter):
                old_enter(e)

        def leaveEvent(e):
            if self._error_label.isVisible() and self._error_label.campo_actual is line_edit:
                self._error_label.hide()
            if callable(old_leave):
                old_leave(e)

        line_edit.enterEvent = enterEvent
        line_edit.leaveEvent = leaveEvent

    # ---------- Validación / Normalización ----------
    def _validar_campo(self, line_edit):
        """Exige: número entero >= 3."""
        texto = line_edit.text()
        valor = parsear_numero(texto)
        valido = valor is not None and valor >= 3 and float(valor).is_integer()

        if not valido:
            line_edit.setStyleSheet("border: 1.5px solid #FF3333;")
            self._campos_invalidos[line_edit] = True
        else:
            line_edit.setStyleSheet("")
            self._campos_invalidos[line_edit] = False
            if self._error_label.isVisible() and self._error_label.campo_actual is line_edit:
                self._error_label.hide()

    def _normalizar_minimo_entero(self, line_edit, minimo=3):
        """
        Reutiliza tu parseo/formato, pero aplica regla local:
        - Redondea a entero
        - Fuerza mínimo = 3 para fibras_x y fibras_y
        (No toca el diccionario hasta guardar.)
        """
        texto_original = line_edit.text()
        valor = parsear_numero(texto_original)

        if valor is None:
            return

        # Redondear y forzar mínimo
        valor = int(round(valor))
        if valor < minimo:
            valor = minimo

        texto_formateado = mostrar_numero(valor)
        if texto_original != texto_formateado:
            line_edit.setText(texto_formateado)

    # ---------- Guardar ----------
    def guardar_datos(self):
        # Validar y mostrar tooltip si hay error
        for le in (self.ui.fibras_x, self.ui.fibras_y):
            self._validar_campo(le)
            if self._campos_invalidos.get(le, False):
                mostrar_mensaje_error_flotante(le, self._error_label)

        # Si hay inválidos, no cerrar ni guardar
        if any(self._campos_invalidos.get(le, False) for le in (self.ui.fibras_x, self.ui.fibras_y)):
            return

        # Normaliza definitivamente (por si el usuario no salió del campo)
        self._normalizar_minimo_entero(self.ui.fibras_x, minimo=3)
        self._normalizar_minimo_entero(self.ui.fibras_y, minimo=3)

        # >>> AQUÍ recién se escriben los cambios en el diccionario <<<
        self.fibras_data["fibras_x"] = self.ui.fibras_x.text()
        self.fibras_data["fibras_y"] = self.ui.fibras_y.text()

        # Avisar a la ventana principal (opcional)
        if self.callback_actualizar:
            self.callback_actualizar(self.fibras_data)

        # <<< NUEVO: dibujar inmediatamente las fibras en el frame de la ventana principal
        padre = self.parent()
        if padre is not None and hasattr(padre, "mostrar_fibras"):
            # Tu mostrar_fibras solo dibuja si la acción "Capas de Fibras" está marcada:contentReference[oaicite:1]{index=1},
            # así que nos aseguramos de activarla antes:
            try:
                accion = getattr(padre.ui, "actionCapas_de_Fibras_2", None)
                if accion is not None and hasattr(accion, "setChecked"):
                    accion.setChecked(True)
                padre.mostrar_fibras()
            except Exception:
                # No interrumpimos el cierre del diálogo por un error de dibujo
                pass

        self.accept()
