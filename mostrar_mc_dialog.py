from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from ui_mostrar_MC import Ui_mostrar_MC
from class_mostrar_tabla import VentanaMostrarTabla

# Compatibilidad PySide6 (qtagg) y fallback a qt5agg si hiciera falta
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
except Exception:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

import matplotlib.pyplot as plt
import numpy as np

class CustomToolbar(NavigationToolbar2QT):
    # Igual que tu ejemplo: Home, Back, Forward, Pan, Zoom, Save
    toolitems = [
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    ]

class VentanaMostrarMC(QDialog):

    def __init__(self, mc_series: dict, parent=None):
        super().__init__(parent)
        self.ui = Ui_mostrar_MC()
        self.ui.setupUi(self)

        # Datos
        self._series = mc_series or {}

        # Figura y Canvas
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = CustomToolbar(self.canvas, self)
        self.toolbar.setMaximumHeight(28)

        # Inserta en cuadricula_MC (limpiando si ya hubiera contenido)
        layout = self.ui.cuadricula_MC.layout()
        if not layout:
            layout = QVBoxLayout(self.ui.cuadricula_MC)
            self.ui.cuadricula_MC.setLayout(layout)
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Label de coordenadas
        self.lbl_coordenadas = QLabel("Desplaza el mouse sobre la curva para ver coordenadas.")
        self.lbl_coordenadas.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.lbl_coordenadas)

        # Estados iniciales: todos marcados
        self.ui.checkBox_2.setChecked(True)  # Hognestad
        self.ui.checkBox_3.setChecked(True)  # Mander

        # Conexiones (replot total al cambiar)
        self.ui.checkBox_2.stateChanged.connect(self.actualizar_grafica)
        self.ui.checkBox_3.stateChanged.connect(self.actualizar_grafica)

        # Variables para hover
        self.marker = None
        self.x_total = []
        self.y_total = []

        # Primer dibujo y hover
        self.actualizar_grafica()
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        self.ui.btn_mostrar_tablaMC.clicked.connect(self.mostrar_tabla)

    def mostrar_tabla(self):
        checks = {
            "hognestad": self.ui.checkBox_2,
            "mander_no_conf": self.ui.checkBox_3,
        }
        etiquetas = {
            "hognestad": "Hognestad",
            "mander_no_conf": "Mander",
        }
        VentanaMostrarTabla(self._series, checks, etiquetas,
            titulo="Tabla de resultados Momento–Curvatura",
            subheaders=("θ", "M"),
            parent=self
        ).exec()

    def _etiqueta(self, clave: str) -> str:
        return {
            "hognestad": "Hognestad",
            "mander_no_conf": "Mander",
        }.get(clave, clave)

    def actualizar_grafica(self):
        import matplotlib.ticker as mticker

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Configuración de ejes (formato científico y rejilla)
        ax.axhline(0, color='gray', linewidth=1.2, linestyle='-', alpha=0.8)
        ax.axvline(0, color='gray', linewidth=1.2, linestyle='-', alpha=0.8)
        ax.set_xlabel("Curvatura, θ (1/m)", fontsize=10)
        ax.xaxis.set_label_position('top')
        ax.set_ylabel("Momento, M (Tm)", fontsize=10)
        ax.yaxis.set_label_position('right')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='both', labelsize=8)
        ax.format_coord = lambda x, y: ""

        # Formateadores científicos (ajusta potencias si hace falta)
        x_formatter = mticker.ScalarFormatter(useMathText=True)
        y_formatter = mticker.ScalarFormatter(useMathText=True)
        x_formatter.set_scientific(True)
        y_formatter.set_scientific(False)
        ax.xaxis.set_major_formatter(x_formatter)
        ax.yaxis.set_major_formatter(y_formatter)
        ax.xaxis.get_offset_text().set_fontsize(8)
        ax.yaxis.get_offset_text().set_fontsize(8)

        # Limpia acumuladores para hover
        self.x_total = []
        self.y_total = []

        # Qué curvas ploteamos según checkboxes
        modelos = [
            ("hognestad",      self.ui.checkBox_2, 'magenta'),  
            ("mander_no_conf", self.ui.checkBox_3, 'blue'),  
        ]

        algo_dibujado = False
        for clave, checkbox, color in modelos:
            if checkbox.isChecked():
                datos = self._series.get(clave)
                if datos is None:
                    continue
                thetas, M = datos
                # Garantiza arrays
                x = np.asarray(thetas, dtype=float)
                y = np.asarray(M, dtype=float)
                # Plotea
                ax.plot(x, y, label=self._etiqueta(clave), color=color)
                algo_dibujado = True
                # Acumula para hover
                self.x_total.extend(x.tolist())
                self.y_total.extend(y.tolist())

        if algo_dibujado:
            ax.legend(fontsize=9, loc="best", frameon=True)

        self.figure.tight_layout()

        # (Re)crear marcador para hover
        self.marker, = ax.plot([], [], 'ro', markersize=5)

        self.ax = ax
        self.canvas.draw_idle()

    def on_mouse_move(self, event):
        # Limpiar si el mouse no está sobre el eje o no hay datos
        if not getattr(event, "inaxes", False) or not self.x_total:
            if self.marker:
                self.marker.set_data([], [])
            self.lbl_coordenadas.setText("Desplaza el mouse sobre la curva para ver coordenadas.")
            self.canvas.draw_idle()
            return

        if event.xdata is None or event.ydata is None:
            return

        # Transformar todos los puntos a pixeles (pantalla)
        pts = np.column_stack([self.x_total, self.y_total]).astype(float)
        pts_disp = self.ax.transData.transform(pts)

        # Mouse en pixeles
        xm, ym = self.ax.transData.transform((float(event.xdata), float(event.ydata)))

        # Distancia euclídea en pixeles; umbral para “enganchar”
        d2 = (pts_disp[:, 0] - xm) ** 2 + (pts_disp[:, 1] - ym) ** 2
        idx = int(np.argmin(d2))
        r_pix = 12.0

        if d2[idx] <= r_pix * r_pix:
            x_curve = float(self.x_total[idx])
            y_curve = float(self.y_total[idx])
            self.marker.set_data([x_curve], [y_curve])
            # Mantengo tu formato original en este archivo
            self.lbl_coordenadas.setText(f"θ = {x_curve:.3f}     M = {y_curve:.3f}")
        else:
            self.marker.set_data([], [])
            self.lbl_coordenadas.setText("Desplaza el mouse sobre la curva para ver coordenadas.")

        self.canvas.draw_idle()
