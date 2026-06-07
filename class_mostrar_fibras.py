# class_mostrar_fibras.py
from PySide6.QtWidgets import QWidget, QLayout, QVBoxLayout
from seccion_fibras import dibujar_fibras


class class_mostrar_fibras:
    """
    Dibuja la malla de fibras en ui.cuadricula_seccion.

    El estado confinado/no confinado viene de:
        capas_fibras_data["confinado"]

    True  -> fibras confinadas
    False -> fibras no confinadas
    """

    def __init__(
        self,
        ui,
        seccion_columna_data: dict,
        seccion_viga_data: dict,
        capas_fibras_data: dict,
        datos_seccion: dict = None,  # se conserva para no cambiar main_app.py
    ):
        self.ui = ui
        self.seccion_columna_data = seccion_columna_data or {}
        self.seccion_viga_data = seccion_viga_data or {}
        self.capas_fibras_data = capas_fibras_data or {}
        self._fib_widget = None

    # ---------------------------------------------------------
    # Conversiones simples
    # ---------------------------------------------------------
    def _float(self, data, key, default=0.0):
        try:
            return float(data.get(key, default))
        except (TypeError, ValueError):
            return float(default)

    def _int(self, data, key, default=0):
        try:
            return int(float(data.get(key, default)))
        except (TypeError, ValueError):
            return int(default)

    def _bool(self, value, default=False):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "si", "sí", "yes", "on")
        return default

    # ---------------------------------------------------------
    # Armar datos para seccion_fibras.py
    # ---------------------------------------------------------
    def _data_columna(self, nf_x, nf_y, conf):
        d = self.seccion_columna_data

        b = self._float(d, "disenar_columna_base")
        h = self._float(d, "disenar_columna_altura")
        r = self._float(d, "disenar_columna_recubrimiento")
        de = self._float(d, "disenar_columna_diametro_transversal") / 10.0

        d_edge = self._float(d, "disenar_columna_diametro_longitudinal_2") / 10.0
        d_corner = self._float(d, "disenar_columna_diametro_longitudinal_esq") / 10.0

        nb_x = self._int(d, "disenar_columna_varillasX_2")
        nb_y = self._int(d, "disenar_columna_varillasY_2")

        return [b, h, r, de, d_edge, d_corner, nb_x, nb_y, nf_x, nf_y, conf]

    def _data_viga(self, nf_x, nf_y, conf):
        d = self.seccion_viga_data

        b = self._float(d, "disenar_viga_base")
        h = self._float(d, "disenar_viga_altura")
        r = self._float(d, "disenar_viga_recubrimiento")
        de = self._float(d, "disenar_viga_diametro_transversal") / 10.0

        d_sup = self._float(d, "disenar_viga_diametro_superior") / 10.0
        d_inf = self._float(d, "disenar_viga_diametro_inferior") / 10.0

        nb_sup = self._int(d, "disenar_viga_varillas_superior")
        nb_inf = self._int(d, "disenar_viga_varillas_inferior")

        return [b, h, r, de, d_sup, d_inf, nb_sup, nb_inf, nf_x, nf_y, conf]

    # ---------------------------------------------------------
    # Mostrar
    # ---------------------------------------------------------
    def mostrar(self):
        tipo = (self.ui.seccion_analisis.currentText() or "").strip().lower()

        nf_x = self._int(self.capas_fibras_data, "fibras_x")
        nf_y = self._int(self.capas_fibras_data, "fibras_y")
        conf = self._bool(self.capas_fibras_data.get("confinado", False))

        if tipo == "columna":
            data = self._data_columna(nf_x, nf_y, conf)
        elif tipo == "viga":
            data = self._data_viga(nf_x, nf_y, conf)
        else:
            raise ValueError(f"Tipo de seccion no valido: {tipo}")

        self._montar_fibras(data, tipo)

    # ---------------------------------------------------------
    # Montaje del widget
    # ---------------------------------------------------------
    def _montar_fibras(self, data, tipo):
        self._fib_widget = dibujar_fibras(data, tipo)
        contenedor = self.ui.cuadricula_seccion

        if isinstance(contenedor, QLayout):
            layout = contenedor
        elif isinstance(contenedor, QWidget):
            layout = contenedor.layout()
            if layout is None:
                layout = QVBoxLayout(contenedor)
                contenedor.setLayout(layout)
        else:
            raise TypeError("ui.cuadricula_seccion debe ser QLayout o QWidget.")

        self._limpiar_layout(layout)
        layout.addWidget(self._fib_widget)

    def _limpiar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
