from PySide6.QtWidgets import QVBoxLayout, QLineEdit
from seccion_viga_dibujar import dibujar_seccion_viga
from validation_utils2 import parsear_numero

try:
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
except Exception:
    NavigationToolbar2QT = None


class SeccionVigaGrafico:
    def __init__(self, widget_container, datos, ui=None, mostrar_toolbar=True, mostrar_coords=True, show_highlight=True):
        self.container = widget_container
        self.datos = datos
        self.ui = ui

        # Flags de visualización
        self.mostrar_toolbar = mostrar_toolbar
        self.mostrar_coords = mostrar_coords
        self.show_highlight = bool(show_highlight)

        self.dibujar_viga()
        if self.ui is not None:
            self.conectar_lineedits()

    def conectar_lineedits(self):
        campos = [
            "disenar_viga_base",
            "disenar_viga_altura",
            "disenar_viga_recubrimiento",
            "disenar_viga_diametro_superior",
            "disenar_viga_diametro_inferior",
            "disenar_viga_varillas_superior",
            "disenar_viga_varillas_inferior",
            "disenar_viga_diametro_transversal",
            "disenar_viga_espaciamiento",
        ]

        for nombre in campos:
            lineedit: QLineEdit = getattr(self.ui, nombre, None)
            if lineedit:
                lineedit.editingFinished.connect(lambda n=nombre, le=lineedit: self.actualizar_valor(n, le))

    def actualizar_valor(self, nombre, lineedit):
        texto = lineedit.text()
        valor = parsear_numero(texto)
        if valor is not None:
            self.datos[nombre] = texto

            try:
                if hasattr(self.ui, "actionCapas_de_Fibras_2"):
                    self.ui.actionCapas_de_Fibras_2.setChecked(False)
            except Exception:
                pass

            owner = getattr(self.ui, "_owner", None)
            if owner is not None:
                if hasattr(owner, "_invalidar_asce_persistencia"):
                    owner._invalidar_asce_persistencia()
                if hasattr(owner, "invalidar_resultados_y_apagar_fibras"):
                    owner.invalidar_resultados_y_apagar_fibras()

            self.dibujar_viga()

    def _limpiar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def _aplicar_visibilidad_extras(self, grafico_widget):
        """
        Igual que en columnas: oculta toolbar y/o coordenadas si corresponde.
        """
        if not self.mostrar_toolbar and NavigationToolbar2QT is not None:
            for tb in grafico_widget.findChildren(NavigationToolbar2QT):
                try:
                    tb.setVisible(False)
                except Exception:
                    pass

        if not self.mostrar_coords:
            if hasattr(grafico_widget, "ax") and getattr(grafico_widget, "ax") is not None:
                try:
                    grafico_widget.ax.format_coord = lambda x, y: ""
                except Exception:
                    pass

            if hasattr(grafico_widget, "label") and grafico_widget.label is not None:
                try:
                    grafico_widget.label.setVisible(False)
                except Exception:
                    pass

            try:
                if hasattr(grafico_widget, "canvas") and grafico_widget.canvas is not None:
                    grafico_widget.canvas.mpl_connect("motion_notify_event", lambda event: None)
            except Exception:
                pass

    def dibujar_viga(self):
        layout = self.container.layout()
        if layout is None:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.container.setLayout(layout)
        else:
            self._limpiar_layout(layout)

        b = parsear_numero(self.datos.get("disenar_viga_base", "0"))
        h = parsear_numero(self.datos.get("disenar_viga_altura", "0"))
        r = parsear_numero(self.datos.get("disenar_viga_recubrimiento", "0"))
        dest = parsear_numero(self.datos.get("disenar_viga_diametro_transversal", "0"))
        n_sup = int(parsear_numero(self.datos.get("disenar_viga_varillas_superior", "0")))
        n_inf = int(parsear_numero(self.datos.get("disenar_viga_varillas_inferior", "0")))
        d_sup = parsear_numero(self.datos.get("disenar_viga_diametro_superior", "0"))
        d_inf = parsear_numero(self.datos.get("disenar_viga_diametro_inferior", "0"))

        grafico = dibujar_seccion_viga(
            b=b,
            h=h,
            r=r,
            dest=dest / 10,
            n_sup=n_sup,
            n_inf=n_inf,
            d_sup=d_sup / 10,
            d_inf=d_inf / 10,
            show_highlight=self.show_highlight,
        )

        self._aplicar_visibilidad_extras(grafico)
        layout.addWidget(grafico)