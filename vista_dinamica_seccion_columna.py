# vista_dinamica_seccion_columna.py
from PySide6.QtWidgets import QVBoxLayout, QLineEdit
from seccion_columna_dibujar import dibujar_seccion_columna
from validation_utils2 import parsear_numero

# Intenta importar la toolbar de Matplotlib para poder ocultarla si existe
try:
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
except Exception:
    NavigationToolbar2QT = None


class SeccionColumnaGrafico:
    """
    Crea/actualiza el gráfico de la sección de columna dentro de un contenedor Qt (QWidget).
    Ahora admite:
      - mostrar_toolbar: bool -> mostrar/ocultar toolbar de Matplotlib
      - mostrar_coords: bool -> mostrar/ocultar coordenadas del puntero
    """
    def __init__(self, widget_container, datos, ui=None, mostrar_toolbar=True, mostrar_coords=True):
        self.container = widget_container
        self.datos = datos
        self.ui = ui  # Acceso a los QLineEdit si se pasa

        # Flags de visualización
        self.mostrar_toolbar = mostrar_toolbar
        self.mostrar_coords = mostrar_coords

        self.dibujar_columna()

        if self.ui is not None:
            self.conectar_lineedits()

    def conectar_lineedits(self):
        campos = [
            "disenar_columna_base",
            "disenar_columna_altura",
            "disenar_columna_recubrimiento",
            "disenar_columna_diametro_transversal",
            "disenar_columna_varillasX_2",
            "disenar_columna_varillasY_2",
            "disenar_columna_diametro_longitudinal_2",
            "disenar_columna_ramalesX",
            "disenar_columna_ramalesY",
            "disenar_columna_espaciamiento",
        ]

        for nombre in campos:
            lineedit: QLineEdit = getattr(self.ui, nombre, None)
            if lineedit:
                lineedit.editingFinished.connect(lambda n=nombre, le=lineedit: self.actualizar_valor(n, le))

    def actualizar_valor(self, nombre, lineedit):
        texto = lineedit.text()
        valor = parsear_numero(texto)
        if valor is not None:
            # Guardar como texto (tu código actual trabaja así)
            self.datos[nombre] = texto
            # NUEVO: apagar fibras e invalidar resultados
            try:
                if hasattr(self.ui, "actionCapas_de_Fibras_2"):
                    self.ui.actionCapas_de_Fibras_2.setChecked(False)
            except Exception:
                pass
            owner = getattr(self.ui, "_owner", None)
            if owner is not None:
                # Llama al helper que agregaste en VentanaPrincipal
                if hasattr(owner, "_invalidar_asce_persistencia"):
                    owner._invalidar_asce_persistencia()
                # 3) Mantén invalidación de resultados/ fibras
                if hasattr(owner, "invalidar_resultados_y_apagar_fibras"):
                    owner.invalidar_resultados_y_apagar_fibras()
            self.dibujar_columna()

    def _limpiar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def _aplicar_visibilidad_extras(self, grafico_widget):
        """
        Intenta ocultar toolbar y/o coordenadas si están presentes en el widget creado
        por 'dibujar_seccion_columna'. Este método es "best-effort" y no rompe si
        alguno de los elementos no existe.
        """
        # 1) Toolbar
        if not self.mostrar_toolbar and NavigationToolbar2QT is not None:
            for tb in grafico_widget.findChildren(NavigationToolbar2QT):
                tb.setVisible(False)

        # 2) Coordenadas (varias estrategias):
        if not self.mostrar_coords:
            # a) Si el widget de dibujo expone 'ax' (Axes de Matplotlib), vaciar el formateador
            if hasattr(grafico_widget, "ax") and getattr(grafico_widget, "ax") is not None:
                try:
                    grafico_widget.ax.format_coord = lambda x, y: ""
                except Exception:
                    pass

            # b) Algunos layouts ponen un QLabel debajo para coordenadas (p.ej. atributo 'label')
            if hasattr(grafico_widget, "label") and grafico_widget.label is not None:
                try:
                    grafico_widget.label.setVisible(False)
                except Exception:
                    pass

            # c) Si la toolbar no se ocultó (o no existía), interceptar el evento de movimiento
            #    para no mostrar nada en el status del canvas (esto es un fallback inofensivo).
            try:
                if hasattr(grafico_widget, "canvas") and grafico_widget.canvas is not None:
                    grafico_widget.canvas.mpl_connect("motion_notify_event", lambda event: None)
            except Exception:
                pass

    def dibujar_columna(self):
        layout = self.container.layout()
        if layout is None:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.container.setLayout(layout)
        else:
            self._limpiar_layout(layout)

        # Extraer y convertir datos
        b = parsear_numero(self.datos.get("disenar_columna_base", "0"))
        h = parsear_numero(self.datos.get("disenar_columna_altura", "0"))
        r = parsear_numero(self.datos.get("disenar_columna_recubrimiento", "0"))
        dest = parsear_numero(self.datos.get("disenar_columna_diametro_transversal", "0"))
        n_x = int(parsear_numero(self.datos.get("disenar_columna_varillasX_2", "0")))
        n_y = int(parsear_numero(self.datos.get("disenar_columna_varillasY_2", "0")))
        dlong = parsear_numero(self.datos.get("disenar_columna_diametro_longitudinal_2", "0"))

        # Crear y agregar el widget gráfico
        grafico = dibujar_seccion_columna(
            b=b,
            h=h,
            r=r,
            dest=dest / 10,     # mm -> cm
            n_x=n_x,
            n_y=n_y,
            dlong=dlong / 10    # mm -> cm
        )

        # Aplicar visibilidad (ocultar toolbar/coords si corresponde SOLO en este uso)
        self._aplicar_visibilidad_extras(grafico)

        layout.addWidget(grafico)
