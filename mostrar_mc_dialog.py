from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from ui_mostrar_MC import Ui_mostrar_MC
from class_mostrar_tabla import VentanaMostrarTabla
from vista_dinamica_seccion_columna import SeccionColumnaGrafico
from vista_dinamica_seccion_viga import SeccionVigaGrafico

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton)

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

class VentanaMostrarParametrosMC(QDialog):
    def __init__(self, parametros, checks, etiquetas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parámetros Característicos")
        self.resize(820, 320)

        layout = QVBoxLayout(self)

        # Modelos activos
        modelos_visibles = [k for k, chk in checks.items() if chk.isChecked() and k in parametros]

        tabla = QTableWidget(self)
        tabla.setRowCount(8)
        tabla.setColumnCount(1 + len(modelos_visibles))

        headers = ["Parámetro"] + [etiquetas[k] for k in modelos_visibles]
        tabla.setHorizontalHeaderLabels(headers)

        filas = [
            ("Rigidez inicial, Ki (T-m/(1/m))", "rigidez_inicial"),
            ("Curvatura de fluencia, φy (1/m)", ("punto_fluencia", "phi")),
            ("Momento de fluencia, My (T-m)", ("punto_fluencia", "M")),
            ("Curvatura máxima, φmax (1/m)", ("punto_maximo", "phi")),
            ("Momento máximo, Mmax (T-m)", ("punto_maximo", "M")),
            ("Curvatura de falla, φf (1/m)", ("punto_falla", "phi")),
            ("Momento de falla, Mf (T-m)", ("punto_falla", "M")),
            ("Ductilidad, μφ (-)", "ductilidad_curvatura"),
        ]

        for i, (titulo, clave) in enumerate(filas):
            tabla.setItem(i, 0, QTableWidgetItem(titulo))

            for j, modelo in enumerate(modelos_visibles, start=1):
                datos = parametros.get(modelo, {})

                if isinstance(clave, tuple):
                    valor = datos.get(clave[0], {}).get(clave[1], None)
                else:
                    valor = datos.get(clave, None)

                if valor is None:
                    txt = "-"
                else:
                    txt = f"{float(valor):.6g}"

                tabla.setItem(i, j, QTableWidgetItem(txt))

        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(tabla)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)

class VentanaMostrarMC(QDialog):

    def __init__(self, seccion_columna_data: dict, seccion_viga_data: dict, mc_series: dict, mc_parametros: dict, tipo_seccion, parent=None):
        super().__init__(parent)
        self.ui = Ui_mostrar_MC()
        self.ui.setupUi(self)

        # Datos
        self._series = mc_series or {}
        self._parametros = mc_parametros or {}
        self._tipo_seccion = (tipo_seccion or "").strip().lower()

        # --------- Dibuja la sección ----------
        if self._tipo_seccion == "columna":
            SeccionColumnaGrafico(
                self.ui.cuadricula_seccionMC,
                (seccion_columna_data or {}).copy(),
                ui=None,
                mostrar_toolbar=False,
                mostrar_coords=False,
                show_highlight=False,
            )
        else:
            SeccionVigaGrafico(
                self.ui.cuadricula_seccionMC,
                (seccion_viga_data or {}).copy(),
                ui=None,
                mostrar_toolbar=False,
                mostrar_coords=False,
                show_highlight=False,
            )

        # Figura y Canvas
        self.figure = Figure()
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

        # ----- Configuración de checkboxes según tipo de sección -----
        # Siempre visibles para ambos
        self.ui.checkBox_2.setChecked(True)  # Hognestad
        self.ui.checkBox_4.setChecked(True)  # Mander No Confinado

        if self._tipo_seccion == "columna":
            # Columna: sí existe Mander Confinado
            self.ui.checkBox_3.show()
            self.ui.checkBox_3.setChecked(True)
        else:
            # Viga: no existe Mander Confinado
            self.ui.checkBox_3.setChecked(False)
            self.ui.checkBox_3.hide()

        # Conexiones (replot total al cambiar)
        self.ui.checkBox_2.stateChanged.connect(self.actualizar_grafica)
        self.ui.checkBox_3.stateChanged.connect(self.actualizar_grafica)
        self.ui.checkBox_4.stateChanged.connect(self.actualizar_grafica)

        # Variables para hover
        self.marker = None
        self.x_total = []
        self.y_total = []

        # Primer dibujo y hover
        self.actualizar_grafica()
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        self.ui.btn_mostrar_tablaMC.clicked.connect(self.mostrar_tabla)
        self.ui.btn_mostrar_parmetros.clicked.connect(self.mostrar_parametros)

    def mostrar_tabla(self):
        checks, etiquetas = self._checks_y_etiquetas()

        VentanaMostrarTabla(
            self._series,
            checks,
            etiquetas,
            titulo="Tabla de resultados Momento–Curvatura",
            subheaders=("θ", "M"),
            parent=self
        ).exec()

    def _checks_y_etiquetas(self):
        if self._tipo_seccion == "viga":
            checks = {
                "hognestad": self.ui.checkBox_2,
                "mander_no_conf": self.ui.checkBox_4,
            }
            etiquetas = {
                "hognestad": "Hognestad",
                "mander_no_conf": "Mander No Confinado",
            }
        else:
            checks = {
                "hognestad": self.ui.checkBox_2,
                "mander_conf": self.ui.checkBox_3,
                "mander_no_conf": self.ui.checkBox_4,
            }
            etiquetas = {
                "hognestad": "Hognestad",
                "mander_conf": "Mander Confinado",
                "mander_no_conf": "Mander No Confinado",
            }
        return checks, etiquetas


    def mostrar_parametros(self):
        checks, etiquetas = self._checks_y_etiquetas()

        if not self._parametros:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Parámetros Característicos", "No existen parámetros calculados para mostrar.")
            return

        dlg = VentanaMostrarParametrosMC(
            parametros=self._parametros,
            checks=checks,
            etiquetas=etiquetas,
            parent=self
        )
        dlg.exec()
    
    def _etiqueta(self, clave: str) -> str:
        return {
            "hognestad": "Hognestad",
            "mander_conf": "Mander Confinado",
            "mander_no_conf": "Mander No Confinado",
        }.get(clave, clave)

    def actualizar_grafica(self):
        import matplotlib.ticker as mticker

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Configuración de ejes
        ax.axhline(0, color='gray', linewidth=1.2, linestyle='-', alpha=0.8)
        ax.axvline(0, color='gray', linewidth=1.2, linestyle='-', alpha=0.8)
        ax.set_xlabel("Curvatura, θ (1/m)", fontsize=10)
        ax.xaxis.set_label_position('top')
        ax.set_ylabel("Momento, M (T-m)", fontsize=10)
        ax.yaxis.set_label_position('right')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='both', labelsize=8)
        ax.format_coord = lambda x, y: ""

        # Formateadores
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

        # Modelos según tipo de sección
        if self._tipo_seccion == "viga":
            modelos = [
                ("hognestad", self.ui.checkBox_2, 'magenta'),
                ("mander_no_conf", self.ui.checkBox_4, 'green'),
            ]
        else:
            modelos = [
                ("hognestad", self.ui.checkBox_2, 'magenta'),
                ("mander_conf", self.ui.checkBox_3, 'blue'),
                ("mander_no_conf", self.ui.checkBox_4, 'green'),
            ]

        algo_dibujado = False
        for clave, checkbox, color in modelos:
            if checkbox.isChecked():
                datos = self._series.get(clave)
                if datos is None:
                    continue

                thetas, M = datos
                x = np.asarray(thetas, dtype=float)
                y = np.asarray(M, dtype=float)

                ax.plot(x, y, label=self._etiqueta(clave), color=color)
                algo_dibujado = True

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
            self.lbl_coordenadas.setText(f"θ = {x_curve:.3f}     M = {y_curve:.3f}")
        else:
            self.marker.set_data([], [])
            self.lbl_coordenadas.setText("Desplaza el mouse sobre la curva para ver coordenadas.")

        self.canvas.draw_idle()