from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidgetItem, QPushButton
from ui_esfuerzo_deformacion_acero import Ui_esfuerzo_deformacion_acero
from Park_acero import curva_acero_park
from PySide6.QtCore import Qt
from class_mostrar_tabla import VentanaMostrarTabla

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
import matplotlib.pyplot as plt
import numpy as np

class CustomToolbar(NavigationToolbar2QT):
    toolitems = [
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    ]

class VentanaEsfuerzoAcero(QDialog):
    def __init__(self, datos_acero):
        super().__init__()
        self.ui = Ui_esfuerzo_deformacion_acero()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())

        self.datos_acero = datos_acero

        self.ui.nombre_acero.setText(datos_acero.get("nombre_acero"))
        self.ui.esfuerzo_fy.setText(datos_acero.get("esfuerzo_fy"))
        self.ui.modulo_Es.setText(datos_acero.get("modulo_Es"))

        # ----------- TABLA DE PUNTOS CARACTERÍSTICOS CENTRADA -----------
        def_fluencia = float(datos_acero.get("def_fluencia_acero"))
        esfuerzo_fy = float(datos_acero.get("esfuerzo_fy"))
        def_inicio_endurecimiento = float(datos_acero.get("def_inicio_endurecimiento"))
        def_ultima = float(datos_acero.get("def_ultima_acero"))
        esfuerzo_ultimo = float(datos_acero.get("esfuerzo_ultimo_acero"))

        self.ui.tablePuntosControl.setRowCount(3)
        self.ui.tablePuntosControl.setColumnCount(2)

        # Fila 0
        item_00 = QTableWidgetItem(f"{def_fluencia:.5f}")
        item_00.setTextAlignment(Qt.AlignCenter)
        self.ui.tablePuntosControl.setItem(0, 0, item_00)
        item_01 = QTableWidgetItem(f"{esfuerzo_fy:.2f}")
        item_01.setTextAlignment(Qt.AlignCenter)
        self.ui.tablePuntosControl.setItem(0, 1, item_01)
        # Fila 1
        item_10 = QTableWidgetItem(f"{def_inicio_endurecimiento:.5f}")
        item_10.setTextAlignment(Qt.AlignCenter)
        self.ui.tablePuntosControl.setItem(1, 0, item_10)
        item_11 = QTableWidgetItem(f"{esfuerzo_fy:.2f}")
        item_11.setTextAlignment(Qt.AlignCenter)
        self.ui.tablePuntosControl.setItem(1, 1, item_11)
        # Fila 2
        item_20 = QTableWidgetItem(f"{def_ultima:.5f}")
        item_20.setTextAlignment(Qt.AlignCenter)
        self.ui.tablePuntosControl.setItem(2, 0, item_20)
        item_21 = QTableWidgetItem(f"{esfuerzo_ultimo:.2f}")
        item_21.setTextAlignment(Qt.AlignCenter)
        self.ui.tablePuntosControl.setItem(2, 1, item_21)
        # ---------------------------------------------------------------
        # Crear FigureCanvas y CustomToolbar
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = CustomToolbar(self.canvas, self)
        self.toolbar.setMaximumHeight(28)

        # Layout para la gráfica y la barra de herramientas
        layout = self.ui.cuadricula_ed_acero.layout()
        if not layout:
            layout = QVBoxLayout(self.ui.cuadricula_ed_acero)
            self.ui.cuadricula_ed_acero.setLayout(layout)
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Etiqueta para mostrar las coordenadas
        self.lbl_coordenadas = QLabel("Desplaza el mouse sobre la curva para ver coordenadas.")
        layout.addWidget(self.lbl_coordenadas)

        # Almacenar es y fs para el evento
        self.fs, self.es = curva_acero_park(self.datos_acero)
        self.mostrar_grafica_interactiva_acero()

        # Guardar referencias para marcador y ejes
        self.ax = self.figure.axes[0]
        self.marker, = self.ax.plot([], [], 'ro', markersize=5)

        # Evento para seguir el mouse sobre la curva
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        self.ui.btn_mostrar_tabla_ed_a.clicked.connect(self.mostrar_tabla)

    def mostrar_tabla(self):
        """
        Abre la tabla genérica con los datos de la curva esfuerzo–deformación del acero.
        """
        # Guardamos la serie como dict, igual que en hormigón
        series = {
            "acero": (self.es, self.fs)
        }

        # En este caso no hay checkboxes, así que inventamos uno “siempre activo”
        checks = {"acero": QLabel()}
        checks["acero"].setChecked = lambda *_: None   # dummy
        checks["acero"].isChecked = lambda: True       # siempre activo

        etiquetas = {"acero": "Thompson y Park"}

        VentanaMostrarTabla(
            series,
            checks,
            etiquetas,
            titulo="Tabla de resultados Esfuerzo–Deformación Acero",
            subheaders=("ε", "σ"),
            parent=self
        ).exec()

    def mostrar_grafica_interactiva_acero(self):
        import matplotlib.ticker as mticker
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.plot(self.es, self.fs, 'b-', picker=5)
        # Marcar el origen (sistema de referencia)
        self.ax.axhline(0, color='gray', linewidth=1.5, linestyle='-', alpha=0.8)
        self.ax.axvline(0, color='gray', linewidth=1.5, linestyle='-', alpha=0.8)
        # Títulos de los ejes en lado opuesto de los ticks
        self.ax.set_xlabel("Deformación, ε (cm/cm)", fontsize=10)
        self.ax.xaxis.set_label_position('top')
        self.ax.set_ylabel("Esfuerzo, σ (kg/cm²)", fontsize=10)
        self.ax.yaxis.set_label_position('right')
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.tick_params(axis='both', labelsize=8)
        self.ax.format_coord = lambda x, y: ""
        # 
        x_formatter = mticker.ScalarFormatter(useMathText=True)
        y_formatter = mticker.ScalarFormatter(useMathText=True)
        x_formatter.set_scientific(True)
        x_formatter.set_powerlimits((-3, -3))
        y_formatter.set_scientific(True)
        y_formatter.set_powerlimits((3, 3))
        self.ax.xaxis.set_major_formatter(x_formatter)
        self.ax.yaxis.set_major_formatter(y_formatter)
        self.ax.xaxis.get_offset_text().set_fontsize(8)  # O el tamaño que desees
        self.ax.yaxis.get_offset_text().set_fontsize(8)
        self.figure.tight_layout()

        # El marcador solo se crea una vez en __init__, aquí solo lo limpiamos
        self.marker, = self.ax.plot([], [], 'ro', markersize=5)
        self.canvas.draw_idle()

    def on_mouse_move(self, event):
        if not event.inaxes:
            self.marker.set_data([], [])
            self.lbl_coordenadas.setText("Desplaza el mouse sobre la curva para ver coordenadas.")
            self.canvas.draw_idle()
            return
        x_mouse = event.xdata
        idx = (np.abs(self.es - x_mouse)).argmin()
        x_curve = self.es[idx]
        y_curve = self.fs[idx]
        tolerancia_x = (self.es.max() - self.es.min()) * 0.02
        if abs(x_mouse - x_curve) > tolerancia_x:
            self.marker.set_data([], [])
            self.lbl_coordenadas.setText("Desplaza el mouse sobre la curva para ver coordenadas.")
        else:
            self.marker.set_data([x_curve], [y_curve])
            self.lbl_coordenadas.setText(f"ε = {x_curve:.5f}     σ = {y_curve:.2f}")
        self.canvas.draw_idle()

    def resizeEvent(self, event):
        size = self.ui.cuadricula_ed_acero.size()
        self.canvas.resize(size.width(), size.height())
        self.canvas.draw_idle()
        super().resizeEvent(event)
