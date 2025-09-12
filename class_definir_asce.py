# class_definir_asce.py  (versión optimizada)
from __future__ import annotations
from typing import Optional, Tuple, List, Dict, Any

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import QEvent

from ui_definir_asce import Ui_definir_asce
from validation_utils2 import (
    ErrorFloatingLabel,
    validar_en_tiempo_real,
    mostrar_mensaje_error_flotante,
    corregir_y_normalizar,
)

# ========= Matplotlib embebido (Qt5/Qt6) =========
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
except Exception:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# ---------------- Toolbar compacta ----------------
class CustomToolbar(NavigationToolbar2QT):
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
    Ventana para configurar parámetros ASCE y graficar:
      - Momento–Rotación (btn_calcular_rotacion)
      - Momento–Curvatura (btn_calcular_curvatura)
    """

    # ------- Claves internas para persistencia -------
    _K_PLOT_KIND   = "_asce_plot_kind"       # "rotacion" | "curvatura" | None
    _K_PLOT_X      = "_asce_plot_x"
    _K_PLOT_Y      = "_asce_plot_y"
    _K_PLOT_XLABEL = "_asce_plot_xlabel"
    _K_PLOT_YLABEL = "_asce_plot_ylabel"
    _K_MAT_SIG     = "_asce_mat_signature"   # firma materiales

    # Colores fijos por tipo de curva
    _COLOR_ROT  = "magenta"
    _COLOR_CURV = "blue"

    # Campos editables (para validar, snapshot y reglas de limpieza)
    _CAMPOS_EDITABLES = (
        "def_max_asce", "def_ultima_asce", "def_fluencia_asce",
        "cortante_viga_asce", "axial_columna_asce",
        "long_viga_asce", "coef_viga_asce",
    )

    # Alias robustos para la condición de viga
    _ALIAS_CONDICION = {
        "Flexion": "Flexión", "flexion": "Flexión", "flexión": "Flexión",
        "0": "Flexión", 0: "Flexión",
        "1": "Corte",   1: "Corte",
        "Corte": "Corte", "corte": "Corte"
    }

    def __init__(self, seccion_actual: str, datos_iniciales: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.ui = Ui_definir_asce()
        self.ui.setupUi(self)

        # ----------------- Estado base -----------------
        self.cambios_pendientes = False
        self.error_label = ErrorFloatingLabel(self)

        # Diccionario vivo que recibimos por referencia (se actualiza en tiempo real)
        self._asce_data: Dict[str, Any] = datos_iniciales if isinstance(datos_iniciales, dict) else {}
        self._tipo_seccion: str = getattr(self, "_tipo_seccion", seccion_actual)  # compat con inyección
        self._grafica_actual: Optional[str] = None  # "rotacion" | "curvatura" | None

        # Buffers para curva y hover
        self.series_asce = None
        self.ax_asce = None
        self.marker_asce = None
        self._xy_disp_asce = None
        self.x_total_asce: List[float] = []
        self.y_total_asce: List[float] = []
        self._x_pick: np.ndarray | List[float] = []
        self._y_pick: np.ndarray | List[float] = []

        # Guard / snapshot
        self._hidratando: bool = False
        self._snapshot_ui: Dict[str, str] = {}

        # Campos a validar/escuchar y mapa widget->clave
        self.campos_a_validar = [getattr(self.ui, n) for n in self._CAMPOS_EDITABLES if hasattr(self.ui, n)]
        self._map_le_to_key = {getattr(self.ui, n): n for n in self._CAMPOS_EDITABLES if hasattr(self.ui, n)}

        # ------------ Conexiones de eventos de edición ------------
        for campo in self.campos_a_validar:
            campo.textChanged.connect(lambda _, le=campo: self.on_modificacion(le))
            campo.editingFinished.connect(lambda le=campo: self._normalizar_y_actualizar(le))
            campo.installEventFilter(self)

        # Combo Flexión/Corte (si existe)
        if hasattr(self.ui, "condicion_viga_asce"):
            self.ui.condicion_viga_asce.currentIndexChanged.connect(self._on_condicion_cambiada)

        # Botones de calcular
        self.ui.btn_calcular_rotacion.clicked.connect(self._calc_y_plot_rotacion)
        self.ui.btn_calcular_curvatura.clicked.connect(self._calc_y_plot_curvatura)

        # Axial solo para columnas
        self.ui.axial_columna_asce.setEnabled(self._tipo_seccion != "Viga")

        # ====== Canvas Matplotlib ======
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = CustomToolbar(self.canvas, self)
        self.toolbar.setMaximumHeight(28)
        # Silenciar coordenadas en la toolbar si es posible
        try:
            self.toolbar.coordinates = False
        except Exception:
            pass

        cont = self.ui.cuadricula_ASCE
        layout = cont.layout() or QVBoxLayout(cont)
        cont.setLayout(layout)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Label inferior para coordenadas
        if hasattr(self.ui, "lbl_coordenadas_asce"):
            self.lbl_coordenadas_asce: QLabel = self.ui.lbl_coordenadas_asce
        else:
            self.lbl_coordenadas_asce = QLabel("")
            self.lbl_coordenadas_asce.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            layout.addWidget(self.lbl_coordenadas_asce)

        # Eventos de mouse para hover
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move_asce)
        self.canvas.mpl_connect("draw_event", self._recalc_disp_coords_asce)

        # ===== Hidratación inicial =====
        self._hidratando = True
        self._refrescar_campos_materiales_desde_dicts()  # 1) material -> _asce_data
        self._cargar_datos(self._asce_data)              # 2) _asce_data -> UI
        self._snapshot_ui = self._obtener_datos()        # 3) snapshot
        if hasattr(self.ui, "condicion_viga_asce"):
            self._snapshot_ui["condicion_viga_asce_text"] = self.ui.condicion_viga_asce.currentText().strip()

        # 4) checkBox_curvatura gobierna groupBox_3
        if hasattr(self.ui, "checkBox_curvatura") and hasattr(self.ui, "groupBox_3"):
            self.ui.groupBox_3.setEnabled(self.ui.checkBox_curvatura.isChecked())
            self.ui.checkBox_curvatura.stateChanged.connect(self._on_toggle_curvatura)

        # ======= Restauración / Primera apertura =======
        try:
            firma_guardada = self._asce_data.get(self._K_MAT_SIG)
            if firma_guardada is not None and firma_guardada != self._firma_materiales_actual():
                self._borrar_persistencia_grafica()
        except Exception:
            pass

        restaurada = False
        try:
            restaurada = self._restaurar_grafica_si_hay()
        except Exception:
            restaurada = False

        if not restaurada:
            self._grafica_actual = None
            self._limpiar_cuadricula(etiqueta_x="")

        self._hidratando = False  # fin hidratación

    # ----------------- Helpers UI/estado -----------------
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            try:
                getattr(self.error_label, "hide_label", self.error_label.hide)()
            except Exception:
                pass
        return super().eventFilter(obj, event)

    def _set_status(self, texto: str):
        try:
            self.lbl_coordenadas_asce.setText(texto)
        except Exception:
            pass

    def _valor_lineedit(self, line_edit) -> str:
        try:
            return line_edit.text().strip()
        except Exception:
            return ""

    def _silenciar_coords(self, ax):
        try:
            ax.format_coord = lambda x, y: ""
        except Exception:
            pass

    # ----------------- Carga / snapshot -----------------
    def _cargar_datos(self, d: dict):
        if not isinstance(d, dict):
            return
        for key in self._CAMPOS_EDITABLES:
            if key in d and hasattr(self.ui, key):
                getattr(self.ui, key).setText(str(d.get(key, "")))
        if hasattr(self.ui, "condicion_viga_asce") and "condicion_viga_asce_text" in d:
            txt = str(d.get("condicion_viga_asce_text", "")).strip()
            idx = self.ui.condicion_viga_asce.findText(txt)
            if idx >= 0:
                self.ui.condicion_viga_asce.setCurrentIndex(idx)

    def _obtener_datos(self) -> dict:
        datos = {k: getattr(self.ui, k).text().strip() for k in self._CAMPOS_EDITABLES if hasattr(self.ui, k)}
        if hasattr(self.ui, "condicion_viga_asce"):
            datos["condicion_viga_asce_index"] = self.ui.condicion_viga_asce.currentIndex()
            datos["condicion_viga_asce_text"] = self.ui.condicion_viga_asce.currentText().strip()
        return datos

    def _actualizar_asce_data(self):
        self._asce_data.update(self._obtener_datos())

    # ----------------- Materiales -> _asce_data -----------------
    def _refrescar_campos_materiales_desde_dicts(self):
        try:
            if hasattr(self, "_datos_hormigon") and isinstance(self._datos_hormigon, dict):
                self._asce_data["def_max_asce"] = str(
                    self._datos_hormigon.get("def_max_sin_confinar", self._asce_data.get("def_max_asce", "")))
                self._asce_data["def_ultima_asce"] = str(
                    self._datos_hormigon.get("def_ultima_sin_confinar", self._asce_data.get("def_ultima_asce", "")))
            if hasattr(self, "_datos_acero") and isinstance(self._datos_acero, dict):
                self._asce_data["def_fluencia_asce"] = str(
                    self._datos_acero.get("def_fluencia_acero", self._asce_data.get("def_fluencia_asce", "")))
        except Exception:
            pass

    # ----------------- Edición / validación -----------------
    def on_modificacion(self, line_edit):
        if self._hidratando:
            return

        key = self._map_le_to_key.get(line_edit)
        if key:
            nuevo = self._valor_lineedit(line_edit)
            if nuevo == self._snapshot_ui.get(key, ""):
                return

        validar_en_tiempo_real(line_edit, {}, self.error_label)
        self.cambios_pendientes = True
        self._actualizar_asce_data()
        self._post_edicion_lineedit(line_edit)

        if key:
            self._snapshot_ui[key] = self._valor_lineedit(line_edit)

    def _normalizar_y_actualizar(self, line_edit):
        if self._hidratando:
            return
        corregir_y_normalizar(line_edit)
        validar_en_tiempo_real(line_edit, {}, self.error_label)

        key = self._map_le_to_key.get(line_edit)
        if key and self._valor_lineedit(line_edit) == self._snapshot_ui.get(key, ""):
            self._actualizar_asce_data()
            return

        self._actualizar_asce_data()
        self.cambios_pendientes = True
        self._post_edicion_lineedit(line_edit)
        if key:
            self._snapshot_ui[key] = self._valor_lineedit(line_edit)

    def _on_condicion_cambiada(self, _=None):
        if self._hidratando or not hasattr(self.ui, "condicion_viga_asce"):
            return
        nuevo_txt = self.ui.condicion_viga_asce.currentText().strip()
        if nuevo_txt == self._snapshot_ui.get("condicion_viga_asce_text", ""):
            return
        self._actualizar_asce_data()
        self._snapshot_ui["condicion_viga_asce_text"] = nuevo_txt
        etiqueta_x = {"rotacion": "Rotación, \u03B8 (rad)", "curvatura": "Curvatura, \u03BA (1/m)"}\
            .get(self._grafica_actual, "")
        self._limpiar_cuadricula(etiqueta_x)
        self._borrar_persistencia_grafica()

    def _on_toggle_curvatura(self, _state):
        try:
            if hasattr(self.ui, "groupBox_3"):
                self.ui.groupBox_3.setEnabled(self.ui.checkBox_curvatura.isChecked())
        except Exception:
            pass

    # ----------------- Reglas de limpieza tras edición -----------------
    def _post_edicion_lineedit(self, line_edit):
        solo_curvatura = {self.ui.long_viga_asce, self.ui.coef_viga_asce}
        etiqueta_x = {"rotacion": "Rotación, \u03B8 (rad)", "curvatura": "Curvatura, \u03BA (1/m)"}\
            .get(self._grafica_actual, "")
        if line_edit in solo_curvatura:
            if self._grafica_actual == "curvatura":
                self._limpiar_cuadricula(etiqueta_x)
                self._borrar_persistencia_grafica()
        else:
            self._limpiar_cuadricula(etiqueta_x)
            self._borrar_persistencia_grafica()

    # ----------------- Empaquetado de datos para cálculo -----------------
    def _paquete_datos(self) -> dict:
        tipo = getattr(self, "_tipo_seccion", "Viga")
        direccion = ""
        if tipo == "Columna":
            try:
                direccion = self._direccion.currentText()
            except Exception:
                direccion = str(getattr(self, "_direccion", "")) or ""

        condicion = "Flexión"
        if hasattr(self.ui, "condicion_viga_asce"):
            cond_txt = self.ui.condicion_viga_asce.currentText().strip()
            condicion = self._ALIAS_CONDICION.get(cond_txt, cond_txt or "Flexión")

        datos = {
            "tipo_seccion": tipo,
            "direccion": direccion,
            "condicion_viga": condicion,
        }
        datos.update(self._obtener_datos())
        for k in ("_datos_hormigon", "_datos_acero", "_datos_seccion"):
            if hasattr(self, k):
                datos[k[1:]] = getattr(self, k)
        return datos

    # ----------------- Dibujo / hover -----------------
    def _setup_axes(self, etiqueta_x: str, etiqueta_y: str = "Momento, M (T·m)", titulo: str | None = None):
        self.figure.clear()
        if self.marker_asce is not None:
            try:
                self.marker_asce.remove()
            except Exception:
                pass
            self.marker_asce = None

        ax = self.figure.add_subplot(111)
        self._silenciar_coords(ax)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='both', labelsize=8)
        if etiqueta_x:
            ax.set_xlabel(etiqueta_x, fontsize=10); ax.xaxis.set_label_position('top')
        if etiqueta_y:
            ax.set_ylabel(etiqueta_y, fontsize=10); ax.yaxis.set_label_position('right')
        if titulo:
            ax.set_title(titulo, fontsize=11)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=6))
        ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6))
        self.ax_asce = ax
        return ax

    def _limpiar_cuadricula(self, etiqueta_x: str = "", etiqueta_y: str = "Momento, M (T·m)"):
        self._setup_axes(etiqueta_x, etiqueta_y)
        self._reset_buffers()
        self.canvas.draw_idle()
        self._set_status("Parámetros modificados. Presiona 'Calcular' para actualizar la curva.")

    def _reset_buffers(self):
        self._xy_disp_asce = None
        self.x_total_asce = []
        self.y_total_asce = []
        self._x_pick = []
        self._y_pick = []
        self.series_asce = None

    def _ensure_marker(self):
        if self.ax_asce is None:
            return
        mk = getattr(self, "marker_asce", None)
        if mk is None or mk.axes is not self.ax_asce:
            try:
                if mk is not None:
                    mk.remove()
            except Exception:
                pass
            (self.marker_asce,) = self.ax_asce.plot([], [], 'o', ms=5, mfc='red', mec='white', mew=1.5,
                                                    zorder=10, visible=False)

    def _dibujar_asce(self, x, y, etiqueta_x: str, titulo: str, color: str = "C0"):
        ax = self._setup_axes(etiqueta_x, "Momento, M (T·m)", titulo)
        ax.plot(x, y, lw=1.8, color=color)

        self.canvas.draw_idle()
        self._recalc_disp_coords_asce(None)
        self._ensure_marker()

        self.x_total_asce = list(map(float, x))
        self.y_total_asce = list(map(float, y))
        self._set_status("Curva calculada. Desplaza el mouse para ver coordenadas.")

    def _recalc_disp_coords_asce(self, _event):
        if self.ax_asce is None:
            return
        if not self.x_total_asce or not self.y_total_asce:
            lines = self.ax_asce.get_lines()
            if not lines:
                return
            self.x_total_asce = list(lines[0].get_xdata())
            self.y_total_asce = list(lines[0].get_ydata())

        xs = np.asarray(self.x_total_asce, dtype=float)
        ys = np.asarray(self.y_total_asce, dtype=float)
        mask = np.isfinite(xs) & np.isfinite(ys)
        if not np.any(mask):
            self._xy_disp_asce = None
            self._x_pick = []
            self._y_pick = []
            return

        self._x_pick = xs[mask]
        self._y_pick = ys[mask]
        pts = np.column_stack([self._x_pick, self._y_pick])
        self._xy_disp_asce = self.ax_asce.transData.transform(pts)

    def _on_mouse_move_asce(self, event):
        if event.inaxes != self.ax_asce:
            if self.marker_asce is not None and self.marker_asce.get_visible():
                self.marker_asce.set_visible(False)
                self.canvas.draw_idle()
            return
        if self._xy_disp_asce is None or self.ax_asce is None:
            return
        try:
            diffs = self._xy_disp_asce - np.array([event.x, event.y])
            idx = int(np.argmin(np.einsum('ij,ij->i', diffs, diffs)))
            x_val = float(self._x_pick[idx]); y_val = float(self._y_pick[idx])
            self._set_status(f"x = {x_val:.6g} ; M = {y_val:.6g}")
            self._ensure_marker()
            self.marker_asce.set_data([x_val], [y_val])
            if not self.marker_asce.get_visible():
                self.marker_asce.set_visible(True)
            self.canvas.draw_idle()
        except Exception:
            pass

    # ----------------- Persistencia -----------------
    def _persistir_grafica(self, kind: str, x: list, y: list, xlabel: str, ylabel: str = "Momento, M (T·m)"):
        self._asce_data.update({
            self._K_PLOT_KIND:   kind,
            self._K_PLOT_X:      list(map(float, x)) if x is not None else None,
            self._K_PLOT_Y:      list(map(float, y)) if y is not None else None,
            self._K_PLOT_XLABEL: xlabel,
            self._K_PLOT_YLABEL: ylabel,
            self._K_MAT_SIG:     self._firma_materiales_actual(),
        })

    def _borrar_persistencia_grafica(self):
        self._asce_data[self._K_PLOT_KIND] = None
        self._asce_data[self._K_PLOT_X] = None
        self._asce_data[self._K_PLOT_Y] = None

    def _restaurar_grafica_si_hay(self) -> bool:
        kind   = self._asce_data.get(self._K_PLOT_KIND)
        x      = self._asce_data.get(self._K_PLOT_X)
        y      = self._asce_data.get(self._K_PLOT_Y)
        xlabel = self._asce_data.get(self._K_PLOT_XLABEL) or ""
        ylabel = self._asce_data.get(self._K_PLOT_YLABEL) or "Momento, M (T·m)"

        if kind and x and y and len(x) == len(y) and len(x) > 1:
            color = self._COLOR_ROT if kind == "rotacion" else self._COLOR_CURV
            self._dibujar_asce(x, y, xlabel, "Momento–Rotación" if kind == "rotacion" else "Momento–Curvatura", color)
            self._grafica_actual = kind
            return True
        return False

    def _firma_materiales_actual(self) -> Tuple[str, str, str]:
        d = self._asce_data
        return (
            str(d.get("def_max_asce", "")),
            str(d.get("def_ultima_asce", "")),
            str(d.get("def_fluencia_asce", "")),
        )

    # ----------------- Errores y validación previa -----------------
    def _mostrar_error(self, line_edit, mensaje: str):
        mostrar_mensaje_error_flotante(line_edit, self.error_label, mensaje)

    def validar_campos(self) -> bool:
        # Aquí puedes añadir validaciones si aplican; por ahora conserva el True del código original.
        return True

    # ----------------- Cálculo y dibujo -----------------
    def _calcular_series(self):
        """
        Invoca a self._calc_asce.calcular(...) con los argumentos correctos.
        Debe retornar:
            {"rotacion": (x_rot, y_Mr), "curvatura": (x_kappa, y_M)}
        """
        self._actualizar_asce_data()

        calc = getattr(self, "_calc_asce", None)
        if calc is None:
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "ASCE", "No se ha inicializado el calculador ASCE.")
            except Exception:
                pass
            return None

        p = self._paquete_datos()
        tipo_seccion = p.get("tipo_seccion", "Viga")
        direccion    = p.get("direccion", "")
        condicion    = p.get("condicion_viga", "Flexión")

        datos_hormigon = p.get("datos_hormigon", {}) or {}
        datos_acero    = p.get("datos_acero", {}) or {}
        datos_seccion  = p.get("datos_seccion", {}) or {}

        keys_asce = [
            "def_max_asce", "def_ultima_asce", "def_fluencia_asce",
            "cortante_viga_asce", "axial_columna_asce",
            "long_viga_asce", "coef_viga_asce",
            "condicion_viga_asce_text", "condicion_viga_asce_index",
        ]
        datos_asce = {k: p.get(k) for k in keys_asce if k in p}

        try:
            if hasattr(calc, "calcular"):
                return calc.calcular(tipo_seccion, direccion, condicion,
                                     datos_hormigon, datos_acero, datos_seccion, datos_asce)
            if hasattr(calc, "calcular_series"):
                payload = {
                    "tipo_seccion":  tipo_seccion,
                    "direccion":     direccion,
                    "condicion_viga": condicion,
                    "datos_hormigon": datos_hormigon,
                    "datos_acero":    datos_acero,
                    "datos_seccion":  datos_seccion,
                    **datos_asce,
                }
                return calc.calcular_series(payload)
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "ASCE", "El calculador no expone 'calcular' ni 'calcular_series'.")
            except Exception:
                pass
            return None
        except Exception as e:
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "ASCE", f"Error de cálculo: {e}")
            except Exception:
                pass
            return None

    def _calc_y_plot_rotacion(self):
        if not self.validar_campos():
            return
        series = self._calcular_series()
        if not series or "rotacion" not in series:
            return
        self.series_asce = series
        x, y = series["rotacion"]
        self._dibujar_asce(x, y, "Rotación, \u03B8 (rad)", "Momento–Rotación", color=self._COLOR_ROT)
        self._grafica_actual = "rotacion"
        self.cambios_pendientes = False
        self._persistir_grafica("rotacion", x, y, "Rotación, \u03B8 (rad)")

    def _calc_y_plot_curvatura(self):
        if not self.validar_campos():
            return
        series = self._calcular_series()
        if not series or "curvatura" not in series:
            return
        self.series_asce = series
        x, y = series["curvatura"]
        self._dibujar_asce(x, y, "Curvatura, \u03BA (1/m)", "Momento–Curvatura", color=self._COLOR_CURV)
        self._grafica_actual = "curvatura"
        self.cambios_pendientes = False
        self._persistir_grafica("curvatura", x, y, "Curvatura, \u03BA (1/m)")