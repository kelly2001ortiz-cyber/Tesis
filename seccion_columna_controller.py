from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QMessageBox
from validation_utils2 import (
    ErrorFloatingLabel,
    validar_en_tiempo_real,
    corregir_y_normalizar,
    mostrar_mensaje_error_flotante,
)

class SeccionColumnaController(QObject):  # <--- Ahora hereda de QObject
    def __init__(self, ui, datos_iniciales, datos_guardados_callback=None):
        super().__init__()   # <--- Llama al init de QObject
        self.ui = ui  # instancia de Ui_ventana_principal
        self.datos_guardados_callback = datos_guardados_callback

        self.campos_a_validar = [
            self.ui.disenar_columna_base,
            self.ui.disenar_columna_altura,
            self.ui.disenar_columna_varillasX_2,
            self.ui.disenar_columna_varillasY_2,
            self.ui.disenar_columna_diametro_longitudinal_2,
            self.ui.disenar_columna_recubrimiento,
            self.ui.disenar_columna_ramalesX,
            self.ui.disenar_columna_ramalesY,
            self.ui.disenar_columna_diametro_transversal,
            self.ui.disenar_columna_espaciamiento,
            self.ui.disenar_columna_diametro_longitudinal_esq,
            self.ui.disenar_columna_axial,
        ]
        self.campos_invalidos = {c: False for c in self.campos_a_validar}
        self.error_label = ErrorFloatingLabel(self.ui.pg_columna)
        self._conectar_senales()
        self.llenar_campos(datos_iniciales)

    def _conectar_senales(self):
        try:
            self.ui.btn_calcular_columna.clicked.disconnect()
        except Exception:
            pass
        self.ui.btn_calcular_columna.clicked.connect(self.calcular)

        for campo in self.campos_a_validar:
            try:
                campo.textChanged.disconnect()
            except Exception:
                pass
            campo.textChanged.connect(lambda _, le=campo: self.on_modificacion(le))
            try:
                campo.editingFinished.disconnect()
            except Exception:
                pass
            if campo is self.ui.disenar_columna_axial:
                campo.editingFinished.connect(self._on_editing_finished_axial)
            else:
                campo.editingFinished.connect(lambda le=campo: corregir_y_normalizar(le))
            campo.installEventFilter(self)  # <-- ¡Ya funciona!

    def eventFilter(self, obj, event):
        if obj in self.campos_a_validar:
            if event.type() == QEvent.Enter:
                if self.campos_invalidos.get(obj, False):
                    mostrar_mensaje_error_flotante(obj, self.error_label)
            elif event.type() == QEvent.Leave:
                self.error_label.hide()
        return False

    def llenar_campos(self, datos):
        self.ui.disenar_columna_nombre.setText(datos.get("disenar_columna_nombre", ""))
        self.ui.disenar_columna_base.setText(datos.get("disenar_columna_base", ""))
        self.ui.disenar_columna_altura.setText(datos.get("disenar_columna_altura", ""))
        self.ui.disenar_columna_varillasX_2.setText(datos.get("disenar_columna_varillasX_2", ""))
        self.ui.disenar_columna_varillasY_2.setText(datos.get("disenar_columna_varillasY_2", ""))
        self.ui.disenar_columna_diametro_longitudinal_2.setText(datos.get("disenar_columna_diametro_longitudinal_2", ""))
        self.ui.disenar_columna_recubrimiento.setText(datos.get("disenar_columna_recubrimiento", ""))
        self.ui.disenar_columna_ramalesX.setText(datos.get("disenar_columna_ramalesX", ""))
        self.ui.disenar_columna_ramalesY.setText(datos.get("disenar_columna_ramalesY", ""))
        self.ui.disenar_columna_diametro_transversal.setText(datos.get("disenar_columna_diametro_transversal", ""))
        self.ui.disenar_columna_espaciamiento.setText(datos.get("disenar_columna_espaciamiento", ""))
        self.ui.disenar_columna_diametro_longitudinal_esq.setText(datos.get("disenar_columna_diametro_longitudinal_esq", ""))
        self.ui.disenar_columna_axial.setText(datos.get("disenar_columna_axial", ""))
        
    def on_modificacion(self, line_edit):
        if line_edit is self.ui.disenar_columna_axial:
            self._validar_carga_axial(mostrar_tooltip=False)
        else:
            validar_en_tiempo_real(line_edit, self.campos_invalidos, self.error_label)

    def _on_editing_finished_axial(self):
        from validation_utils2 import corregir_y_normalizar
        corregir_y_normalizar(self.ui.disenar_columna_axial)
        self._ajustar_carga_axial_a_limites()
         
    def obtener_datos(self):
        return {
            "disenar_columna_nombre": self.ui.disenar_columna_nombre.text(),
            "disenar_columna_base": self.ui.disenar_columna_base.text(),
            "disenar_columna_altura": self.ui.disenar_columna_altura.text(),
            "disenar_columna_varillasX_2": self.ui.disenar_columna_varillasX_2.text(),
            "disenar_columna_varillasY_2": self.ui.disenar_columna_varillasY_2.text(),
            "disenar_columna_diametro_longitudinal_2": self.ui.disenar_columna_diametro_longitudinal_2.text(),
            "disenar_columna_recubrimiento": self.ui.disenar_columna_recubrimiento.text(),
            "disenar_columna_ramalesX": self.ui.disenar_columna_ramalesX.text(),
            "disenar_columna_ramalesY": self.ui.disenar_columna_ramalesY.text(),
            "disenar_columna_diametro_transversal": self.ui.disenar_columna_diametro_transversal.text(),
            "disenar_columna_espaciamiento": self.ui.disenar_columna_espaciamiento.text(),
            "disenar_columna_diametro_longitudinal_esq": self.ui.disenar_columna_diametro_longitudinal_esq.text(),
            "disenar_columna_axial": self.ui.disenar_columna_axial.text(),
        }

    def _parse_float(self, text, default=0.0):
        try:
            from validation_utils2 import parsear_numero
            v = parsear_numero(text)
            return default if v is None else float(v)
        except Exception:
            return default


    def _limites_axiales_columna(self):
        owner = getattr(self.ui, "_owner", None)
        if owner is None:
            return None, None

        datos_h = getattr(owner, "material_hormigon_data", {}) or {}
        datos_s = getattr(owner, "material_acero_data", {}) or {}

        fc = self._parse_float(datos_h.get("esfuerzo_fc"), 0.0)   # kg/cm2
        fy = self._parse_float(datos_s.get("esfuerzo_fy"), 0.0)   # kg/cm2

        b = self._parse_float(self.ui.disenar_columna_base.text(), 0.0)   # cm
        h = self._parse_float(self.ui.disenar_columna_altura.text(), 0.0) # cm

        nx = int(round(self._parse_float(self.ui.disenar_columna_varillasX_2.text(), 0.0)))
        ny = int(round(self._parse_float(self.ui.disenar_columna_varillasY_2.text(), 0.0)))

        d_gen = self._parse_float(self.ui.disenar_columna_diametro_longitudinal_2.text(), 0.0) / 10.0   # mm -> cm
        d_esq = self._parse_float(self.ui.disenar_columna_diametro_longitudinal_esq.text(), 0.0) / 10.0 # mm -> cm

        if fc <= 0 or fy <= 0 or b <= 0 or h <= 0 or nx < 2 or ny < 2 or d_gen <= 0 or d_esq <= 0:
            return None, None

        Ag = b * h  # cm2

        A_esq = 3.141592653589793 * d_esq**2 / 4.0
        A_gen = 3.141592653589793 * d_gen**2 / 4.0

        # mismo conteo que usa tu columna rectangular con 4 esquinas + barras intermedias
        n_total = 4 + 2 * max(0, nx - 2) + 2 * max(0, ny - 2)
        Ast = 4 * A_esq + (n_total - 4) * A_gen

        P0 = 0.85 * fc * (Ag - Ast) + fy * Ast   # kg
        Pmin = - 0.80 * P0                         # kg
        Pmax = fy * Ast                        # kg

        return Pmin, Pmax

    def _validar_carga_axial(self, mostrar_tooltip=False):
        from validation_utils2 import parsear_numero, mostrar_mensaje_error_flotante

        le = self.ui.disenar_columna_axial
        valor = parsear_numero(le.text())

        Pmin, Pmax = self._limites_axiales_columna()

        valido = (
            valor is not None and
            Pmin is not None and
            Pmax is not None and
            Pmin <= float(valor) <= Pmax
        )

        if not valido:
            le.setStyleSheet("border: 1.5px solid #FF3333;")
            self.campos_invalidos[le] = True
            if mostrar_tooltip:
                mostrar_mensaje_error_flotante(le, self.error_label)
        else:
            le.setStyleSheet("")
            self.campos_invalidos[le] = False
            if self.error_label.isVisible() and getattr(self.error_label, "campo_actual", None) == le:
                self.error_label.hide()

        return valido

    def _ajustar_carga_axial_a_limites(self):
        from validation_utils2 import parsear_numero, mostrar_numero

        le = self.ui.disenar_columna_axial
        valor = parsear_numero(le.text())

        Pmin, Pmax = self._limites_axiales_columna()

        if valor is None or Pmin is None or Pmax is None:
            return

        valor_ajustado = float(valor)

        if valor_ajustado > Pmax:
            valor_ajustado = Pmax
        elif valor_ajustado < Pmin:
            valor_ajustado = Pmin

        texto_nuevo = mostrar_numero(valor_ajustado)
        if le.text() != texto_nuevo:
            le.setText(texto_nuevo)

        self._validar_carga_axial(mostrar_tooltip=False)
    
    def validar_campos(self):
        for campo in self.campos_a_validar:
            if campo is self.ui.disenar_columna_axial:
                self._validar_carga_axial(mostrar_tooltip=False)
            else:
                validar_en_tiempo_real(campo, self.campos_invalidos, self.error_label)

            if self.campos_invalidos[campo]:
                campo.setFocus()

                if campo is self.ui.disenar_columna_axial:
                    Pmin, Pmax = self._limites_axiales_columna()
                    if Pmin is None or Pmax is None:
                        msg = (
                            "No se pudo validar la carga axial.\n"
                            "Revisa primero materiales y geometría de la columna."
                        )
                    else:
                        msg = (
                            "La carga axial está fuera del rango permitido.\n\n"
                            f"Rango admisible: {Pmin:.2f} kg a {Pmax:.2f} kg"
                        )
                else:
                    msg = "Formato incorrecto\nPor favor, revisar los campos resaltados en rojo"

                QMessageBox.warning(
                    self.ui.pg_columna,
                    "Revisar el formato",
                    msg
                )
                return False
        return True

    def calcular(self):
        if not self.validar_campos():
            return
        datos = self.obtener_datos()
        QMessageBox.information(
                    self.ui.pg_columna,
                    "Cálculo terminado",
                    "Puede continuar"
                )
        if self.datos_guardados_callback:
            self.datos_guardados_callback(datos)
