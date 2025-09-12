from PySide6.QtWidgets import QVBoxLayout, QLineEdit
from seccion_viga_dibujar import dibujar_seccion_viga
from validation_utils2 import parsear_numero

class SeccionVigaGrafico:
    def __init__(self, widget_container, datos, ui=None):
        self.container = widget_container
        self.datos = datos
        self.ui = ui
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
            self.datos[nombre] = texto  # Guardar en el diccionario como texto
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
            self.dibujar_viga()
        
    def dibujar_viga(self):
        layout = self.container.layout()
        if layout is None:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.container.setLayout(layout)
        else:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)

        # Extraer y convertir datos
        b = parsear_numero(self.datos.get("disenar_viga_base", "0"))
        h = parsear_numero(self.datos.get("disenar_viga_altura", "0"))
        r = parsear_numero(self.datos.get("disenar_viga_recubrimiento", "0"))
        dest = parsear_numero(self.datos.get("disenar_viga_diametro_transversal", "0"))
        n_sup = int(parsear_numero(self.datos.get("disenar_viga_varillas_superior", "0")))
        n_inf = int(parsear_numero(self.datos.get("disenar_viga_varillas_inferior", "0")))
        d_sup = parsear_numero(self.datos.get("disenar_viga_diametro_superior", "0"))
        d_inf = parsear_numero(self.datos.get("disenar_viga_diametro_inferior", "0"))
        # Crear y agregar el widget gráfico
        grafico = dibujar_seccion_viga(
            b=b,
            h=h,
            r=r,
            dest=dest/10,
            n_sup=n_sup,
            n_inf=n_inf,
            d_sup=d_sup/10,
            d_inf=d_inf/10
        )
        layout.addWidget(grafico)
