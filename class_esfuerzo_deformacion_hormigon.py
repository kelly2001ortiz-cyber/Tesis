# Archivo: class_esfuerzo_deformacion_hormigon.py (corregido)

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QMessageBox
from PySide6.QtCore import Qt
from ui_esfuerzo_deformacion_hormigon import Ui_esfuerzo_deformacion_hormigon
from Hognestad02 import curva_hognestad
from Mander_HnoConfinado01 import curva_mander_no_confinado
from Mander_HConfinado04 import mander_confinado
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

class VentanaEsfuerzoHormigon(QDialog):
    def __init__(self, datos_hormigon, datos_acero, datos_seccion):
        super().__init__()
        self.ui = Ui_esfuerzo_deformacion_hormigon()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())

        self.datos_hormigon = datos_hormigon
        self.datos_acero = datos_acero
        self.datos_seccion = datos_seccion

        self.ui.nombre_hormigon.setText(datos_hormigon.get("nombre_hormigon", ""))
        self.ui.esfuerzo_fc.setText(datos_hormigon.get("esfuerzo_fc", ""))
        self.ui.modulo_Ec.setText(datos_hormigon.get("modulo_Ec", ""))

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = CustomToolbar(self.canvas, self)
        self.toolbar.setMaximumHeight(28)

        layout = self.ui.cuadricula_ed_hormigon.layout()
        if not layout:
            layout = QVBoxLayout(self.ui.cuadricula_ed_hormigon)
            self.ui.cuadricula_ed_hormigon.setLayout(layout)
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.lbl_coordenadas = QLabel("Desplaza el mouse sobre la curva para ver coordenadas.")
        self.lbl_coordenadas.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.lbl_coordenadas)

        self.ui.checkBox_2.setChecked(True)
        self.ui.checkBox_3.setChecked(True)
        self.ui.checkBox_4.setChecked(True)

        self.ui.checkBox_2.stateChanged.connect(self.actualizar_grafica)
        self.ui.checkBox_3.stateChanged.connect(self.actualizar_grafica)
        self.ui.checkBox_4.stateChanged.connect(self.actualizar_grafica)

        self.actualizar_grafica()
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.marker, = self.figure.gca().plot([], [], 'ro', markersize=5)
        self.x_total = []
        self.y_total = []
    
        self.ui.btn_mostrar_tabla_ed_h.clicked.connect(self.mostrar_tabla)

    def mostrar_tabla(self):
        checks = {
            "Hognestad": self.ui.checkBox_2,
            "Mander No Confinado": self.ui.checkBox_3,
            "Mander Confinado": self.ui.checkBox_4,
        }
        etiquetas = {
            "Hognestad": "Hognestad",
            "Mander No Confinado": "Mander No Confinado",
            "Mander Confinado": "Mander Confinado",
        }
        VentanaMostrarTabla(self._series, checks, etiquetas,
            titulo="Tabla de resultados Esfuerzo–Deformación",
            subheaders=("ε", "σ"),
            parent=self
        ).exec()

    def actualizar_grafica(self):
        import matplotlib.ticker as mticker
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        try:
            fc = float(self.datos_hormigon.get("esfuerzo_fc", 0))
            Ec = float(self.datos_hormigon.get("modulo_Ec", 0))
            def_max_sc = float(self.datos_hormigon.get("def_max_sin_confinar", 0))
            def_ult_sc = float(self.datos_hormigon.get("def_ultima_sin_confinar", 0))
            def_max_c = float(self.datos_hormigon.get("def_max_confinada", 0))
            def_ult_c = float(self.datos_hormigon.get("def_ultima_confinada", 0))
        except (ValueError, TypeError):
            QMessageBox.critical(self, "Error de datos", "Algunos parámetros no son válidos numéricamente.")
            return

        datos = {
            "esfuerzo_fc": fc,
            "modulo_Ec": Ec,
            "def_max_sin_confinar": def_max_sc,
            "def_ultima_sin_confinar": def_ult_sc,
            "def_max_confinada": def_max_c,
            "def_ultima_confinada": def_ult_c,
        }

        modelos = [
            ("Hognestad", self.ui.checkBox_2, 'magenta', lambda d: curva_hognestad(d)),
            ("Mander No Confinado", self.ui.checkBox_3, 'blue', lambda d: curva_mander_no_confinado(d)),
            ("Mander Confinado", self.ui.checkBox_4, 'green',
             lambda _: mander_confinado(self.datos_hormigon, self.datos_acero, self.datos_seccion)),
        ]

        self._series = {}   # 👈 guardar series aquí
        self.x_total = []
        self.y_total = []

        for nombre, checkbox, color, funcion in modelos:
            if checkbox.isChecked():
                x, y = funcion(datos)
                ax.plot(x, y, color=color, label=nombre)
                self._series[nombre] = (x, y)   # 👈 guardar la serie
                self.x_total.extend(x)
                self.y_total.extend(y)

        ax.axhline(0, color='gray', linewidth=1.5, linestyle='-', alpha=0.8)
        ax.axvline(0, color='gray', linewidth=1.5, linestyle='-', alpha=0.8)
        ax.set_xlabel("Deformación, ε (cm/cm)", fontsize=10)
        ax.xaxis.set_label_position('top')
        ax.set_ylabel("Esfuerzo, σ (kg/cm²)", fontsize=10)
        ax.yaxis.set_label_position('right')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='both', labelsize=8)
        ax.format_coord = lambda x, y: ""
        ax.legend(fontsize=9)

        x_formatter = mticker.ScalarFormatter(useMathText=True)
        y_formatter = mticker.ScalarFormatter(useMathText=True)
        x_formatter.set_scientific(True)
        x_formatter.set_powerlimits((-3, -3))
        y_formatter.set_scientific(True)
        y_formatter.set_powerlimits((3, 3))
        ax.xaxis.set_major_formatter(x_formatter)
        ax.yaxis.set_major_formatter(y_formatter)
        ax.xaxis.get_offset_text().set_fontsize(8)
        ax.yaxis.get_offset_text().set_fontsize(8)
        self.figure.tight_layout()

        self.marker, = ax.plot([], [], 'ro', markersize=5)
        self.ax = ax
        self.canvas.draw_idle()

    def on_mouse_move(self, event):
        if not event.inaxes or not self.x_total:
            self.marker.set_data([], [])
            self.lbl_coordenadas.setText("Desplaza el mouse sobre la curva para ver coordenadas.")
            self.canvas.draw_idle()
            return
        x_mouse = event.xdata
        x_all = np.array(self.x_total)
        y_all = np.array(self.y_total)
        idx = (np.abs(x_all - x_mouse)).argmin()
        x_curve = x_all[idx]
        y_curve = y_all[idx]
        tolerancia_x = (x_all.max() - x_all.min()) * 0.02
        if abs(x_mouse - x_curve) > tolerancia_x:
            self.marker.set_data([], [])
            self.lbl_coordenadas.setText("Desplaza el mouse sobre la curva para ver coordenadas.")
        else:
            self.marker.set_data([x_curve], [y_curve])
            self.lbl_coordenadas.setText(f"ε = {x_curve:.5f}     σ = {y_curve:.2f}")
        self.canvas.draw_idle()
