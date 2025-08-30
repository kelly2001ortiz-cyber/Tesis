# class_mostrar_fibras.py
from PySide6.QtWidgets import QWidget, QLayout, QVBoxLayout
from seccion_fibras import dibujar_fibras

class class_mostrar_fibras:
    """
    Muestra el gráfico de seccion_fibras en ui.cuadricula_seccion.
    No cambia de página; solo toma parámetros según el texto del combobox ui.seccion_analisis.
    """

    def __init__(self, ui, seccion_columna_data: dict, seccion_viga_data: dict, capas_fibras_data: dict):
        self.ui = ui
        self.seccion_columna_data = seccion_columna_data or {}
        self.seccion_viga_data = seccion_viga_data or {}
        self.capas_fibras_data = capas_fibras_data or {}
        self._fib_widget = None  # mantener referencia

    def mostrar(self):
        tipo = (self.ui.seccion_analisis.currentText() or "").strip().lower()
        if tipo == "columna":
            b   = float(self.seccion_columna_data.get("disenar_columna_base", 0))
            h   = float(self.seccion_columna_data.get("disenar_columna_altura", 0))
            r   = float(self.seccion_columna_data.get("disenar_columna_recubrimiento", 0))
            dest = float(self.seccion_columna_data.get("disenar_columna_diametro_transversal", 0))/10
        else:
            b   = float(self.seccion_viga_data.get("disenar_viga_base", 0))
            h   = float(self.seccion_viga_data.get("disenar_viga_altura", 0))
            r   = float(self.seccion_viga_data.get("disenar_viga_recubrimiento", 0))
            dest = float(self.seccion_viga_data.get("disenar_viga_diametro_transversal", 0))/10

        n_x = int(self.capas_fibras_data.get("fibras_x", 0))
        n_y = int(self.capas_fibras_data.get("fibras_y", 0))

        self._montar_fibras(b, h, r, dest, n_x, n_y)

    def _montar_fibras(self, b, h, r, dest, n_x, n_y):
        self._fib_widget = dibujar_fibras(b, h, r, dest, n_x, n_y)
        container = self.ui.cuadricula_seccion
        if isinstance(container, QLayout):
            self._clear_layout(container)
            container.addWidget(self._fib_widget)
        elif isinstance(container, QWidget):
            lay = container.layout()
            if lay is None:
                lay = QVBoxLayout(container)
                container.setLayout(lay)
            self._clear_layout(lay)
            lay.addWidget(self._fib_widget)
        else:
            raise TypeError("ui.cuadricula_seccion debe ser un QLayout o un QWidget con layout.")

    @staticmethod
    def _clear_layout(layout: QLayout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
