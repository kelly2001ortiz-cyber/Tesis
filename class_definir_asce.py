# class_definir_asce.py
from typing import Optional

from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import QEvent

from ui_definir_asce import Ui_definir_asce
from validation_utils2 import (
    ErrorFloatingLabel,
    validar_en_tiempo_real,
    mostrar_mensaje_error_flotante,
    corregir_y_normalizar,
)

# ========= Estilo de gráfico/toolbar =========
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
except Exception:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mticker


class CustomToolbar(NavigationToolbar2QT):
    """Toolbar compacta."""
    toolitems = [
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    ]


class VentanaDefinirASCE(QDialog):
    """
    Ventana para configurar parámetros ASCE y dibujar:
      - Momento–Rotación (btn_calcular_rotacion)
      - Momento–Curvatura (btn_calcular_curvatura)

    Inyecciones esperadas (desde main antes de exec()):
      _calc_asce: instancia de CalculadoraASCE
      _tipo_seccion: "Viga" | "Columna"
      _direccion:   combobox o texto ("Dirección X" | "Dirección Y") — solo columnas
      _datos_hormigon, _datos_acero, _datos_seccion: dicts
      datos_iniciales: dict con claves para cargar/editar (asce_data compartido)
    """

    def __init__(self, seccion_actual: str, datos_iniciales: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.ui = Ui_definir_asce()
        self.ui.setupUi(self)

        # === Estado inicial requerido ===
        # Checkbox de curvatura desmarcado y groupBox_3 deshabilitado
        try:
            self.ui.checkBox_curvatura.setChecked(False)
            self.ui.groupBox_3.setEnabled(False)
            # Habilitar/Deshabilitar groupBox_3 según el checkbox
            self.ui.checkBox_curvatura.toggled.connect(self.ui.groupBox_3.setEnabled)
        except Exception:
            pass

        # ----------------- Estado general -----------------
        self.cambios_pendientes = False
        self.error_label = ErrorFloatingLabel(self)

        # Referencia al diccionario que se actualizará en tiempo real
        # Si no viene, creamos uno nuevo y lo mantenemos como _asce_data.
        self._asce_data: dict = datos_iniciales if datos_iniciales is not None else {}

        # Campos a validar/escuchar (ajusta según tu UI)
        self.campos_a_validar = [
            # Viga
            self.ui.long_viga_asce,
            self.ui.coef_viga_asce,
            self.ui.cortante_viga_asce,
            # Columna
            self.ui.axial_columna_asce,
        ]
        self.campos_invalidos = {c: False for c in self.campos_a_validar}

        # Conexiones de validación + actualización en tiempo real
        for campo in self.campos_a_validar:
            campo.textChanged.connect(lambda _, le=campo: self.on_modificacion(le))
            campo.editingFinished.connect(lambda le=campo: self._normalizar_y_actualizar(le))
            campo.installEventFilter(self)

        # Si hay combo para condición de viga, también lo conectamos a actualizaciones
        if hasattr(self.ui, "condicion_viga_asce"):
            self.ui.condicion_viga_asce.currentIndexChanged.connect(
                lambda _=None: self._actualizar_asce_data()
            )

        # ---- Precarga visual desde _asce_data ----
        self._cargar_datos(self._asce_data)

        # Habilitar/inhabilitar axial según el tipo
        if seccion_actual == "Viga":
            self.ui.axial_columna_asce.setEnabled(False)
        else:
            self.ui.axial_columna_asce.setEnabled(True)

        # ====== Canvas Matplotlib en cuadricula_ASCE ======
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = CustomToolbar(self.canvas, self)
        self.toolbar.setMaximumHeight(28)

        cont = self.ui.cuadricula_ASCE
        layout = cont.layout()
        if not layout:
            layout = QVBoxLayout(cont)
            cont.setLayout(layout)
        # limpiar contenedores previos
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Canvas expansible
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        try:
            self.figure.set_constrained_layout(True)
        except Exception:
            pass
        cont.installEventFilter(self)

        # etiqueta de coordenadas (hover)
        self.lbl_coordenadas_asce = QLabel("Desplaza el mouse sobre la curva para ver coordenadas.")
        self.lbl_coordenadas_asce.setStyleSheet("font-size: 14px; padding: 4px 0;")
        layout.addWidget(self.lbl_coordenadas_asce)

        # Variables para hover
        self.marker_asce = None
        self._xy_disp_asce = None
        self.x_total_asce = []
        self.y_total_asce = []
        self.ax_asce = None

        # Conectar hover/redibujado
        self._hover_cid_asce = self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move_asce)
        self._draw_cid_asce = self.canvas.mpl_connect("draw_event", self._recalc_disp_coords_asce)

        # Conectar botones del UI (ya existen en tu .ui)
        if hasattr(self.ui, "btn_calcular_rotacion"):
            self.ui.btn_calcular_rotacion.clicked.connect(self._calc_y_plot_rotacion)
        if hasattr(self.ui, "btn_calcular_curvatura"):
            self.ui.btn_calcular_curvatura.clicked.connect(self._calc_y_plot_curvatura)

        # Series calculadas (por si quieres leerlas desde fuera)
        self.series_asce = None

    # ----------------- Precarga utilitaria -----------------
    def _cargar_datos(self, d: dict):
        # Solo-lectura
        if "def_max_asce" in d:
            self.ui.def_max_asce.setText(str(d.get("def_max_asce", "")))
        if "def_ultima_asce" in d:
            self.ui.def_ultima_asce.setText(str(d.get("def_ultima_asce", "")))
        if "def_fluencia_asce" in d:
            self.ui.def_fluencia_asce.setText(str(d.get("def_fluencia_asce", "")))

        # Rotación (viga/columna)
        if "cortante_viga_asce" in d:
            self.ui.cortante_viga_asce.setText(str(d.get("cortante_viga_asce", "")))
        if "axial_columna_asce" in d:
            self.ui.axial_columna_asce.setText(str(d.get("axial_columna_asce", "")))

        # Condición: prioriza texto; si no hay, usa índice (compat)
        if hasattr(self.ui, "condicion_viga_asce"):
            if "condicion_viga_asce_text" in d:
                txt = str(d.get("condicion_viga_asce_text", "")).strip()
                idx = self.ui.condicion_viga_asce.findText(txt)
                if idx >= 0:
                    self.ui.condicion_viga_asce.setCurrentIndex(idx)
            elif "condicion_viga_asce" in d:
                try:
                    self.ui.condicion_viga_asce.setCurrentIndex(int(d.get("condicion_viga_asce", 0)))
                except Exception:
                    pass

        # Curvatura (viga)
        if "long_viga_asce" in d:
            self.ui.long_viga_asce.setText(str(d.get("long_viga_asce", "")))
        if "coef_viga_asce" in d:
            self.ui.coef_viga_asce.setText(str(d.get("coef_viga_asce", "")))

    # ----------------- Recolección utilitaria -----------------
    def _obtener_datos(self) -> dict:
        # Lectura de campos y empaquetado
        datos = {
            "def_max_asce": self.ui.def_max_asce.text().strip(),
            "def_ultima_asce": self.ui.def_ultima_asce.text().strip(),
            "def_fluencia_asce": self.ui.def_fluencia_asce.text().strip(),
            "cortante_viga_asce": self.ui.cortante_viga_asce.text().strip(),
            "axial_columna_asce": self.ui.axial_columna_asce.text().strip(),
            "long_viga_asce": self.ui.long_viga_asce.text().strip(),
            "coef_viga_asce": self.ui.coef_viga_asce.text().strip(),
        }
        if hasattr(self.ui, "condicion_viga_asce"):
            # Guardamos AMBOS: index (compat) y texto (lo que usa el cálculo)
            datos["condicion_viga_asce_index"] = self.ui.condicion_viga_asce.currentIndex()
            datos["condicion_viga_asce_text"] = self.ui.condicion_viga_asce.currentText().strip()
            # (Compat con código viejo que leía 'condicion_viga_asce' como índice)
            datos["condicion_viga_asce"] = datos["condicion_viga_asce_index"]
        return datos

    def _actualizar_asce_data(self):
        """Vuelca al dict externo los valores vigentes del diálogo (en tiempo real)."""
        self._asce_data.update(self._obtener_datos())

    # ----------------- Validación en tiempo real -----------------
    def on_modificacion(self, line_edit):
        validar_en_tiempo_real(line_edit, self.campos_invalidos, self.error_label)
        self.cambios_pendientes = True
        # Actualizar el dict en tiempo real mientras se escribe
        self._actualizar_asce_data()
        # Deshabilitar la grilla hasta recalcular
        try:
            self.ui.cuadricula_ASCE.setEnabled(False)
        except Exception:
            pass
        try:
            self.lbl_coordenadas_asce.setText("Par\u00e1metros modificados. Presiona 'Calcular' para actualizar la curva.")
        except Exception:
            pass

    def _normalizar_y_actualizar(self, line_edit):
        corregir_y_normalizar(line_edit)   # normaliza formato
        validar_en_tiempo_real(line_edit, self.campos_invalidos, self.error_label)
        self._actualizar_asce_data()
        self.cambios_pendientes = True
        # Deshabilitar la grilla hasta recalcular
        try:
            self.ui.cuadricula_ASCE.setEnabled(False)
        except Exception:
            pass
        try:
            self.lbl_coordenadas_asce.setText("Par\u00e1metros modificados. Presiona 'Calcular' para actualizar la curva.")
        except Exception:
            pass

    def validar_campos(self) -> bool:
        """Validación integral (si necesitas llamarla antes de calcular)."""
        for campo in self.campos_a_validar:
            corregir_y_normalizar(campo)
            validar_en_tiempo_real(campo, self.campos_invalidos, self.error_label)
            if self.campos_invalidos.get(campo, False):
                campo.setFocus()
                QMessageBox.warning(
                    self, "Revisar el formato",
                    "Formato incorrecto\nPor favor, revisar los campos resaltados en rojo"
                )
                return False
        return True

    # ----------------- Eventos globales (para limpiar errores) -----------------
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.error_label.hide()
        return super().eventFilter(obj, event)

    # ----------------- Tooltips de error -----------------
    def _mostrar_error(self, line_edit, mensaje: str):
        mostrar_mensaje_error_flotante(line_edit, self.error_label, mensaje)

    # ----------------- Paquete de datos para el calculador -----------------
    def _paquete_datos(self):
        tipo = getattr(self, "_tipo_seccion", "Viga")

        direccion = ""
        if tipo == "Columna":
            # si hay combobox de dirección, leerlo; si no, deja string vacío
            try:
                direccion = self._direccion.currentText()
            except Exception:
                try:
                    direccion = str(self._direccion)
                except Exception:
                    direccion = ""

        # *** TEXTO, no índice ***
        condicion = "Flexión"
        if hasattr(self.ui, "condicion_viga_asce"):
            cond_txt = self.ui.condicion_viga_asce.currentText().strip()
            alias = {
                "Flexion": "Flexión", "flexion": "Flexión", "flexión": "Flexión",
                "0": "Flexión", "1": "Corte",
                "Corte": "Corte", "corte": "Corte"
            }
            condicion = alias.get(cond_txt, cond_txt)

        datos_hormigon = getattr(self, "_datos_hormigon", {})
        datos_acero = getattr(self, "_datos_acero", {})
        datos_seccion = getattr(self, "_datos_seccion", {})
        datos_asce = self._obtener_datos()

        return tipo, direccion, condicion, datos_hormigon, datos_acero, datos_seccion, datos_asce

    # ----------------- Cálculo -----------------
    def _calcular_series(self):
        """
        Llama a CalculadoraASCE.calcular(.) y retorna:
            {'rotacion': (rots, Mr), 'curvatura': (thetas, M)}
        """
        # Asegura sincronía con el dict compartido
        self._actualizar_asce_data()

        calc = getattr(self, "_calc_asce", None)
        if calc is None:
            QMessageBox.warning(self, "ASCE", "No se ha inicializado el calculador ASCE.")
            return None

        tipo, direccion, condicion, dh, da, ds, dasce = self._paquete_datos()
        try:
            return calc.calcular(tipo, direccion, condicion, dh, da, ds, dasce)
        except Exception as e:
            # Muestra mensajes como "No se permitirá.", "Falta información", etc.
            QMessageBox.warning(self, "ASCE", f"Error de cálculo: {e}")
            return None

    # --- Dibujo con formato consistente ---
    def _dibujar_asce(self, x, y, etiqueta_x: str, etiqueta_serie: str, color="blue"):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Ejes y formato
        ax.axhline(0, color='gray', linewidth=1.2, linestyle='-', alpha=0.8)
        ax.axvline(0, color='gray', linewidth=1.2, linestyle='-', alpha=0.8)
        ax.set_xlabel(etiqueta_x, fontsize=10)               # X con unidades pedidas
        ax.xaxis.set_label_position('top')                   # etiqueta superior
        ax.set_ylabel("Momento, M (T\u00B7m)", fontsize=10) # Y con T·m
        ax.yaxis.set_label_position('right')                 # etiqueta derecha
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='both', labelsize=8)
        ax.format_coord = lambda _x, _y: ""                  # sin tooltip por defecto

        # Notación científica compacta
        x_formatter = mticker.ScalarFormatter(useMathText=True)
        y_formatter = mticker.ScalarFormatter(useMathText=True)
        x_formatter.set_scientific(True)
        y_formatter.set_scientific(True)
        ax.xaxis.set_major_formatter(x_formatter)
        ax.yaxis.set_major_formatter(y_formatter)

        # Dibujo
        ax.plot(x, y, '-', lw=2.0, color=color, label=etiqueta_serie)
        ax.legend(loc='best', fontsize=9, frameon=True)

        # Marker hover
        self.marker_asce = ax.plot([], [], 'o', ms=6, color='red', zorder=10)[0]

        self.canvas.draw_idle()
        self.ax_asce = ax
        self._recalc_disp_coords_asce(None)

    # --- Recalcular coordenadas de visualización para hover ---
    def _recalc_disp_coords_asce(self, _event):
        if self.ax_asce is None:
            return
        # Crea matriz de coords para distancia más corta a cursor
        self.x_total_asce = getattr(self, "x_total_asce", [])
        self.y_total_asce = getattr(self, "y_total_asce", [])
        if not len(self.x_total_asce) or not len(self.y_total_asce):
            # intentar obtener desde última línea de ax
            lines = self.ax_asce.get_lines()
            if lines:
                xs = lines[0].get_xdata()
                ys = lines[0].get_ydata()
                self.x_total_asce = np.array(xs)
                self.y_total_asce = np.array(ys)
            else:
                return
        self._xy_disp_asce = np.column_stack(
            self.ax_asce.transData.transform(np.column_stack([self.x_total_asce, self.y_total_asce]))
        )

    # --- Hover handler ---
    def _on_mouse_move_asce(self, event):
        if event.inaxes != self.ax_asce or self._xy_disp_asce is None:
            return
        if event.xdata is None or event.ydata is None:
            return
        if self.marker_asce is None:
            return

        xm, ym = self.ax_asce.transData.transform((float(event.xdata), float(event.ydata)))
        d2 = (self._xy_disp_asce[:, 0] - xm) ** 2 + (self._xy_disp_asce[:, 1] - ym) ** 2
        idx = int(np.argmin(d2))
        r_pix = 12.0
        if d2[idx] <= r_pix * r_pix:
            x_curve = self.x_total_asce[idx]
            y_curve = self.y_total_asce[idx]
            self.marker_asce.set_data([x_curve], [y_curve])
            etiqueta_x = self.ax_asce.get_xlabel()
            # Y siempre en T·m, X se muestra con su unidad actual (rad o 1/m)
            self.lbl_coordenadas_asce.setText(f"{etiqueta_x} = {x_curve:.3e}    M = {y_curve:.3e} T·m")
        else:
            self.marker_asce.set_data([], [])
            self.lbl_coordenadas_asce.setText("Desplaza el mouse sobre la curva para ver coordenadas.")
        self.canvas.draw_idle()

    # --- Callbacks de botones ---
    def _calc_y_plot_rotacion(self):
        # (opcional) validar antes de calcular
        if not self.validar_campos():
            return
        series = self._calcular_series()
        if not series:
            return
        self.series_asce = series
        x, y = series["rotacion"]  # x = rots (rad), y = Mr (T·m)
        self._dibujar_asce(x, y, "Rotación, \u03B8 (rad)", "Momento–Rotación", color="magenta")
        self.cambios_pendientes = False
        try:
            self.ui.cuadricula_ASCE.setEnabled(True)
        except Exception:
            pass

    def _calc_y_plot_curvatura(self):
        if not self.validar_campos():
            return
        series = self._calcular_series()
        if not series:
            return
        self.series_asce = series
        x, y = series["curvatura"]  # x = thetas (1/m), y = M (T·m)
        self._dibujar_asce(x, y, "Curvatura, \u03BA (1/m)", "Momento–Curvatura", color="blue")
        self.cambios_pendientes = False
        try:
            self.ui.cuadricula_ASCE.setEnabled(True)
        except Exception:
            pass
