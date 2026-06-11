from PySide6.QtWidgets import QWidget, QLayout, QVBoxLayout
from grafico_seccion import dibujar_seccion

class class_mostrar_seccion:
    """
    Muestra el grafico de seccion, armado y la malla de fibras.

    """

    def __init__(
        self, 
        ui, 
        seccion_columna_data: dict, 
        seccion_viga_data: dict, 
        capas_fibras_data: dict,
        datos_seccion: dict,
        config=None):

        self.ui = ui
        self.seccion_columna_data = seccion_columna_data or {}
        self.seccion_viga_data = seccion_viga_data or {}
        self.capas_fibras_data = capas_fibras_data or {}
        self.datos_seccion = datos_seccion or {}
        self.config = config

        self._fib_widget = None


    def mostrar(self):
        tipo = (self.ui.seccion_analisis.currentText() or "").strip().lower()
        
        nf_x = int(self.capas_fibras_data.get("fibras_x", 0))
        nf_y = int(self.capas_fibras_data.get("fibras_y", 0))

        seccion = True
        armado = True
        rejilla = False
        ejes = True
        confinado = True

        if self.config is not None:
            seccion = bool(self.config.get("seccion", seccion))
            armado = bool(self.config.get("armado", armado))
            rejilla = bool(self.config.get("rejilla", rejilla))
            ejes = bool(self.config.get("ejes", ejes))
            confinado = bool(self.config.get("confinado", confinado))
            
        if tipo == "columna":
            b = float(self.seccion_columna_data.get("disenar_columna_base", 0))
            h = float(self.seccion_columna_data.get("disenar_columna_altura", 0))
            r = float(self.seccion_columna_data.get("disenar_columna_recubrimiento", 0))
            de = float(self.seccion_columna_data.get("disenar_columna_diametro_transversal", 0))/10
            
            d_edge = int(float(self.seccion_columna_data.get("disenar_columna_diametro_longitudinal_2", 0)))/10
            d_corner = int(float(self.seccion_columna_data.get("disenar_columna_diametro_longitudinal_esq", 0)))/10
            
            nb_x = int(float(self.seccion_columna_data.get("disenar_columna_varillasX_2", 0)))
            nb_y = int(float(self.seccion_columna_data.get("disenar_columna_varillasY_2", 0)))
            conf = int(confinado)

            data = [b , h, r, de, d_edge, d_corner, nb_x, nb_y, nf_x, nf_y, conf]
            config = [seccion, armado, rejilla, ejes]

        elif tipo == "viga":
            b = float(self.seccion_viga_data.get("disenar_viga_base", 0))
            h = float(self.seccion_viga_data.get("disenar_viga_altura", 0))
            r = float(self.seccion_viga_data.get("disenar_viga_recubrimiento", 0))
            de = float(self.seccion_viga_data.get("disenar_viga_diametro_transversal", 0))/10
            
            d_sup = float(self.seccion_viga_data.get("disenar_viga_diametro_superior", 0)) / 10
            d_inf = float(self.seccion_viga_data.get("disenar_viga_diametro_inferior", 0)) / 10

            nb_sup = int(float(self.seccion_viga_data.get("disenar_viga_varillas_superior", 0)))
            nb_inf = int(float(self.seccion_viga_data.get("disenar_viga_varillas_inferior", 0)))
            conf = int(confinado)

            data = [b , h, r, de, d_sup, d_inf, nb_sup, nb_inf, nf_x, nf_y, conf]
            config = [seccion, armado, rejilla, ejes]

        self._montar_seccion(data, tipo, config)


    def _montar_seccion(self, data, tipo, config):
        self._fib_widget = dibujar_seccion(data, tipo, config)
        
        container = self.ui.cuadricula_seccion
        
        if isinstance(container, QLayout):
            self._clear_layout(container)
            container.addWidget(self._fib_widget)
        
        elif isinstance(container, QWidget):
            lay = container.layout()
            
            if lay is None:
                lay = QVBoxLayout(container)
                container.setLayout(lay)
            
            self._clear_layout(lay)
            lay.addWidget(self._fib_widget)
        
        else:
            raise TypeError("ui.cuadricula_seccion debe ser un QLayout o un QWidget con layout.")


    def _clear_layout(self, layout: QLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()