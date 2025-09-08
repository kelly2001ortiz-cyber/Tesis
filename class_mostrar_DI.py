# class_mostrar_DI.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidgetItem, QSizePolicy
from PySide6.QtCore import Qt, QSignalBlocker, QEvent
from ui_mostrar_DI import Ui_mostrar_DI
from vista_dinamica_seccion_columna import SeccionColumnaGrafico
from class_mostrar_tabla import VentanaMostrarTabla

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
except Exception:
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


class VentanaMostrarDI(QDialog):
    """
    Ventana para mostrar el Diagrama de Interacción y llenar la tabla de puntos característicos.
    Requiere:
        - di_matriz: ndarray con columnas [c, φM, φP, M, P]
        - di_series: dict con series {'con_phi': (φM, φP), 'sin_phi': (M, P)}
    """
    def __init__(self, seccion_columna_data: dict,
                 di_matriz=None, di_series=None,
                 parent=None):
        super().__init__(parent)
        self.ui = Ui_mostrar_DI()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())
       
        # ===== Datos de entrada =====
        self._di_matriz = None if di_matriz is None else np.asarray(di_matriz, dtype=float)
        self._series = di_series or {}

        # --------- Dibuja la sección ----------
        SeccionColumnaGrafico(
            self.ui.cuadricula_seccionDI,
            (seccion_columna_data or {}).copy(),
            ui=None,
            mostrar_toolbar=False,
            mostrar_coords=False
        )

        # --- Hacer que la sección se vea grande y llene el frame ---
        cont = self.ui.cuadricula_seccionDI

        # Quitar márgenes/espaciado del layout del contenedor (si existe)
        lay_sec = cont.layout()
        if lay_sec:
            lay_sec.setContentsMargins(0, 0, 0, 0)
            lay_sec.setSpacing(0)

        # Intentar encontrar el canvas de matplotlib que crea SeccionColumnaGrafico
        sec_canvas = cont.findChild(FigureCanvas)
        if sec_canvas:
            sec_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            sec_canvas.updateGeometry()
            # Usar el espacio disponible (cuando sea posible)
            try:
                sec_canvas.figure.set_constrained_layout(True)
            except Exception:
                pass

        # Redimensionar la figura cuando cambie el tamaño del frame
        cont.installEventFilter(self)

        # ====== Canvas para el DI ======
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = CustomToolbar(self.canvas, self)
        self.toolbar.setMaximumHeight(28)

        layout = self.ui.cuadricula_DI.layout()
        if not layout:
            layout = QVBoxLayout(self.ui.cuadricula_DI)
            self.ui.cuadricula_DI.setLayout(layout)
        # limpiar contenedores previos
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # etiqueta coordenadas para el hover
        self.lbl_coordenadas = QLabel("Desplaza el mouse sobre la curva para ver coordenadas.")
        self.lbl_coordenadas.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.lbl_coordenadas)

        # Variables para hover
        self.marker = None
        self.x_total = []
        self.y_total = []
        self._xy_disp = None  # coordenadas de pantalla (pixeles)

        # ====== Estado inicial: solo uno marcado ======
        with QSignalBlocker(self.ui.checkBox_conphi), QSignalBlocker(self.ui.checkBox_sinphi):
            self.ui.checkBox_conphi.setChecked(True)
            self.ui.checkBox_sinphi.setChecked(False)

        # ====== Conexiones ======
        self.ui.checkBox_conphi.toggled.connect(self._on_conphi_toggled)
        self.ui.checkBox_sinphi.toggled.connect(self._on_sinphi_toggled)
        # si usas el botón para refrescar/llenar tabla manualmente
        self.ui.btn_mostrar_tablaDI.clicked.connect(self.mostrar_tabla)

        # Ajustar encabezados según modo inicial
        self._ajustar_encabezados_tabla()

        # Primer llenado de tabla y dibujo del DI
        self._llenar_tabla_puntos_caracteristicos()
        self._dibujar_di()

        # Conectar hover y actualización de coords en cada dibujado (zoom/pan)
        self._hover_cid = self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self._draw_cid = self.canvas.mpl_connect("draw_event", self._recalc_disp_coords)

    # ---------- Event filter para la sección (agrandar canvas) ----------
    def eventFilter(self, obj, event):
        if obj is self.ui.cuadricula_seccionDI and event.type() == QEvent.Resize:
            sec_canvas = obj.findChild(FigureCanvas)
            if sec_canvas and hasattr(sec_canvas, "figure"):
                dpi = sec_canvas.figure.dpi or 100.0
                width_in = max(obj.width() / dpi, 1.0)
                height_in = max(obj.height() / dpi, 1.0)
                sec_canvas.figure.set_size_inches(width_in, height_in, forward=True)
                sec_canvas.draw_idle()
        return super().eventFilter(obj, event)

    # ---------- Exclusión mutua y refresco ----------
    def _on_conphi_toggled(self, checked: bool):
        if checked:
            with QSignalBlocker(self.ui.checkBox_sinphi):
                self.ui.checkBox_sinphi.setChecked(False)
        else:
            if not self.ui.checkBox_sinphi.isChecked():
                with QSignalBlocker(self.ui.checkBox_conphi):
                    self.ui.checkBox_conphi.setChecked(True)
        self._ajustar_encabezados_tabla()
        self._llenar_tabla_puntos_caracteristicos()
        self._dibujar_di()

    def _on_sinphi_toggled(self, checked: bool):
        if checked:
            with QSignalBlocker(self.ui.checkBox_conphi):
                self.ui.checkBox_conphi.setChecked(False)
        else:
            if not self.ui.checkBox_conphi.isChecked():
                with QSignalBlocker(self.ui.checkBox_sinphi):
                    self.ui.checkBox_sinphi.setChecked(True)
        self._ajustar_encabezados_tabla()
        self._llenar_tabla_puntos_caracteristicos()
        self._dibujar_di()

    # ---------- Encabezados dinámicos ----------
    def _ajustar_encabezados_tabla(self):
        """
        Cambia los títulos de columnas según el modo (con φ o sin φ).
        Horizontal:
            - Con φ: ['φPn (T)', 'φMn (T-m)']
            - Sin φ: ['Pn (T)',  'Mn (T-m)']
        (Las dimensiones/tamaños de la tabla se respetan como en el .ui)
        """
        tabla = self.ui.tablePuntosControl
        # asegurar 3 filas x 2 columnas
        if tabla.rowCount() < 3:
            tabla.setRowCount(3)
        if tabla.columnCount() < 2:
            tabla.setColumnCount(2)

        if self.ui.checkBox_conphi.isChecked():
            tabla.setHorizontalHeaderItem(0, QTableWidgetItem("φPn (T)"))
            tabla.setHorizontalHeaderItem(1, QTableWidgetItem("φMn (T-m)"))
        else:
            tabla.setHorizontalHeaderItem(0, QTableWidgetItem("Pn (T)"))
            tabla.setHorizontalHeaderItem(1, QTableWidgetItem("Mn (T-m)"))

        # Importante: no ajustamos widths/heights para mantener lo del .ui

    # ---------- Llenado de tabla ----------
    def _llenar_tabla_puntos_caracteristicos(self):
        """
        Llena la tabla con:
            - Fila 0: primer punto
            - Fila 1: punto con momento máximo (por magnitud |M|)
            - Fila 2: último punto
        Usando (φPn, φMn) o (Pn, Mn) según el checkbox activo.
        """
        tabla = self.ui.tablePuntosControl
        tabla.setRowCount(3)
        tabla.setColumnCount(2)

        if self._di_matriz is None or self._di_matriz.size == 0:
            # Limpiar si no hay datos
            for r in range(3):
                for c in range(2):
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignCenter)
                    tabla.setItem(r, c, item)
            return

        # di_matriz: columnas [c, φM, φP, M, P]
        con_phi = self.ui.checkBox_conphi.isChecked()
        if con_phi:
            col_M = 1  # φM
            col_P = 2  # φP
        else:
            col_M = 3  # M
            col_P = 4  # P

        M_arr = np.asarray(self._di_matriz[:, col_M], dtype=float)
        P_arr = np.asarray(self._di_matriz[:, col_P], dtype=float)

        n = len(M_arr)
        if n == 0:
            for r in range(3):
                for c in range(2):
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignCenter)
                    tabla.setItem(r, c, item)
            return

        # Índices característicos
        idx_first = 0
        idx_last = n - 1
        idx_mmax = int(np.nanargmax(np.abs(M_arr)))  # máximo por magnitud

        # Helper para colocar valores formateados y centrados
        def _set_row(r, p_val, m_val):
            p_item = QTableWidgetItem(f"{p_val:.3f}")
            m_item = QTableWidgetItem(f"{m_val:.3f}")
            p_item.setTextAlignment(Qt.AlignCenter)
            m_item.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(r, 0, p_item)
            tabla.setItem(r, 1, m_item)

        _set_row(0, P_arr[idx_first], M_arr[idx_first])
        _set_row(1, P_arr[idx_mmax], M_arr[idx_mmax])
        _set_row(2, P_arr[idx_last], M_arr[idx_last])

    # ---------- Dibujo del DI + preparación del hover ----------
    def _dibujar_di(self):
        """
        Dibuja el diagrama seleccionado (con φ o sin φ) si di_series está disponible
        y prepara el marcador y arrays para el hover.
        """
        if not self._series:
            # Sin datos de series: limpiar figura
            self.figure.clear()
            self.canvas.draw_idle()
            return

        import matplotlib.ticker as mticker

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Ejes y formato
        ax.axhline(0, color='gray', linewidth=1.2, linestyle='-', alpha=0.8)
        ax.axvline(0, color='gray', linewidth=1.2, linestyle='-', alpha=0.8)
        ax.set_xlabel("Momento, M (T-m)", fontsize=10)
        ax.xaxis.set_label_position('top')
        ax.set_ylabel("Carga Axial, P (T)", fontsize=10)
        ax.yaxis.set_label_position('right')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='both', labelsize=8)
        ax.format_coord = lambda x, y: ""  # desactiva tooltip por defecto

        # Notación científica compacta
        x_formatter = mticker.ScalarFormatter(useMathText=True)
        y_formatter = mticker.ScalarFormatter(useMathText=True)
        x_formatter.set_scientific(True)
        y_formatter.set_scientific(True)
        ax.xaxis.set_major_formatter(x_formatter)
        ax.yaxis.set_major_formatter(y_formatter)
        ax.xaxis.get_offset_text().set_fontsize(8)
        ax.yaxis.get_offset_text().set_fontsize(8)

        # Decide serie según checkbox
        if self.ui.checkBox_conphi.isChecked():
            datos = self._series.get("con_phi")
            etiqueta = "Diagrama con φ"
            color = "magenta"
        else:
            datos = self._series.get("sin_phi")
            etiqueta = "Diagrama sin φ"
            color = "blue"

        self.x_total, self.y_total = [], []
        if datos is not None:
            # En tu UI: M horizontal, P vertical
            x = np.asarray(datos[0], dtype=float)  # M
            y = np.asarray(datos[1], dtype=float)  # P
            ax.plot(x, y, label=etiqueta, color=color)
            ax.legend(fontsize=9, loc="best", frameon=True)

            # Guarda todos los puntos para el hover
            self.x_total = x.tolist()
            self.y_total = y.tolist()

        self.figure.tight_layout()

        # (Re)crear el marcador rojo para el hover
        (self.marker,) = ax.plot([], [], 'ro', markersize=5)
        self.ax = ax

        # Precalcular coords en pixeles para hover robusto
        self._recalc_disp_coords()
        self.canvas.draw_idle()

    def _recalc_disp_coords(self, *_args, **_kwargs):
        """Recalcula las coordenadas transformadas a pixeles (tras zoom/pan/draw)."""
        if self.x_total and self.y_total and hasattr(self, "ax"):
            pts = np.column_stack([self.x_total, self.y_total])
            self._xy_disp = self.ax.transData.transform(pts)
        else:
            self._xy_disp = None

    # ---------- Hover ----------
    def on_mouse_move(self, event):
        # Si no estamos sobre el eje o no hay datos, limpia y sale
        if not getattr(event, "inaxes", False) or not self.x_total:
            if self.marker:
                self.marker.set_data([], [])
            self.lbl_coordenadas.setText("Desplaza el mouse sobre la curva para ver coordenadas.")
            self.canvas.draw_idle()
            return

        if event.xdata is None or event.ydata is None:
            return

        # Asegurar coordenadas en pixeles
        if self._xy_disp is None:
            self._recalc_disp_coords()
            if self._xy_disp is None:
                return

        # Convertir el mouse a pixeles
        xm, ym = self.ax.transData.transform((float(event.xdata), float(event.ydata)))

        # Distancia euclídea en pixeles a todos los puntos de la curva
        d2 = (self._xy_disp[:, 0] - xm) ** 2 + (self._xy_disp[:, 1] - ym) ** 2
        idx = int(np.argmin(d2))

        # Umbral en pixeles para “enganchar” la curva
        r_pix = 12.0
        if d2[idx] <= r_pix * r_pix:
            x_curve = self.x_total[idx]
            y_curve = self.y_total[idx]
            self.marker.set_data([x_curve], [y_curve])
            self.lbl_coordenadas.setText(f"M = {x_curve:.3f}   P = {y_curve:.3f}")
        else:
            self.marker.set_data([], [])
            self.lbl_coordenadas.setText("Desplaza el mouse sobre la curva para ver coordenadas.")

        self.canvas.draw_idle()

    def mostrar_tabla(self):
        """
        Abre la tabla genérica con las curvas seleccionadas.
        """
        checks = {
            "con_phi": self.ui.checkBox_conphi,
            "sin_phi": self.ui.checkBox_sinphi,
        }
        etiquetas = {
            "con_phi": "Diagrama con φ",
            "sin_phi": "Diagrama sin φ",
        }

        VentanaMostrarTabla(
            self._series, checks, etiquetas,
            titulo="Tabla de resultados Diagrama de Interacción",
            subheaders=("M", "P"),   # eje horizontal: Momento, eje vertical: Carga
            parent=self
        ).exec()
