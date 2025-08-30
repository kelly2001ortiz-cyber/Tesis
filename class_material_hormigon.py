from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import QEvent

from ui_material_hormigon import Ui_material_hormigon

from class_esfuerzo_deformacion_hormigon import VentanaEsfuerzoHormigon

from validation_utils2 import (
    ErrorFloatingLabel,
    validar_en_tiempo_real,
    mostrar_mensaje_error_flotante,
    corregir_y_normalizar,
)

__all__ = [
    "VentanaEsfuerzoHormigon",
]

class VentanaMaterialHormigon(QDialog):
    def __init__(self, datos_iniciales=None, datos_acero=None, datos_seccion=None):
        super().__init__()
        self.ui = Ui_material_hormigon()
        self.ui.setupUi(self)

        self.datos_acero = datos_acero
        self.datos_seccion   = datos_seccion

        
        self.campos_a_validar = [
            self.ui.esfuerzo_fc,
            self.ui.modulo_Ec,
            self.ui.def_max_sin_confinar,
            self.ui.def_ultima_sin_confinar,
        ]
        self.campos_invalidos = {c: False for c in self.campos_a_validar}
        self.error_label = ErrorFloatingLabel(self)

        self.datos_guardados_callback = None
        self.datos_guardados = datos_iniciales.copy() if datos_iniciales else {}

        # Rellenar campos si hay datos previos:
        if datos_iniciales:
            self.ui.nombre_hormigon.setText(datos_iniciales.get("nombre_hormigon"))
            self.ui.esfuerzo_fc.setText(datos_iniciales.get("esfuerzo_fc"))
            self.ui.modulo_Ec.setText(datos_iniciales.get("modulo_Ec"))
            self.ui.def_max_sin_confinar.setText(datos_iniciales.get("def_max_sin_confinar"))
            self.ui.def_ultima_sin_confinar.setText(datos_iniciales.get("def_ultima_sin_confinar"))
            self.ui.def_ultima_confinada.setText(datos_iniciales.get("def_ultima_confinada"))

        for campo in self.campos_a_validar:
            campo.textChanged.connect(lambda _, le=campo: self.on_modificacion(le))
            campo.editingFinished.connect(lambda le=campo: corregir_y_normalizar(le))
            campo.installEventFilter(self)

        self.ui.modulo_Ec.editingFinished.connect(self.validar_modulo_Ec)
        self.ui.nombre_hormigon.textChanged.connect(lambda: self.on_modificacion_nombre())

        self.ui.btn_cancelar_hormigon.clicked.connect(self.close)
        self.ui.btn_guardar_hormigon.clicked.connect(self.guardar)
        self.ui.btn_mostrar_diagrama_ed_hormigon.clicked.connect(self.mostrar_diagrama_ed_hormigon)

        self.cambios_pendientes = False
        self.ui.btn_mostrar_diagrama_ed_hormigon.setEnabled(True)

    def on_modificacion(self, line_edit):
        validar_en_tiempo_real(line_edit, self.campos_invalidos, self.error_label)
        self.cambios_pendientes = True
        self.ui.btn_mostrar_diagrama_ed_hormigon.setEnabled(False)

    def on_modificacion_nombre(self):
        self.cambios_pendientes = True
        self.ui.btn_mostrar_diagrama_ed_hormigon.setEnabled(False)

    def obtener_datos(self):
        return {
            "nombre_hormigon": self.ui.nombre_hormigon.text(),
            "esfuerzo_fc": self.ui.esfuerzo_fc.text(),
            "modulo_Ec": self.ui.modulo_Ec.text(),
            "def_max_sin_confinar": self.ui.def_max_sin_confinar.text(),
            "def_ultima_sin_confinar": self.ui.def_ultima_sin_confinar.text(),
            "def_ultima_confinada": self.ui.def_ultima_confinada.text(),
        }

    def validar_campos(self):
        for campo in self.campos_a_validar:
            validar_en_tiempo_real(campo, self.campos_invalidos, self.error_label)
            if self.campos_invalidos[campo]:
                campo.setFocus()
                QMessageBox.warning(
                    self,
                    "Revisar el formato",
                    "Formato incorrecto\nPor favor, revisar los campos resaltados en rojo"
                )
                return False
        return True

    def validar_modulo_Ec(self):
        from validation_utils2 import parsear_numero, mostrar_numero

        fc = parsear_numero(self.ui.esfuerzo_fc.text())
        def_max = parsear_numero(self.ui.def_max_sin_confinar.text())
        Ec = parsear_numero(self.ui.modulo_Ec.text())

        if fc is None or def_max is None or def_max <= 0:
            return  # no puedo validar todavía

        minimo = 1.2 * fc / def_max
        if Ec is None or Ec < minimo:
            self.ui.modulo_Ec.setText(mostrar_numero(minimo))
            
    def guardar(self):
        if not self.validar_campos():
            return
        self.datos_guardados = self.obtener_datos()
        if self.datos_guardados_callback:
            self.datos_guardados_callback(self.datos_guardados)
        self.cambios_pendientes = False
        self.ui.btn_mostrar_diagrama_ed_hormigon.setEnabled(True)

    def mostrar_diagrama_ed_hormigon(self):
        # Usar SIEMPRE los datos más recientes guardados (del dict global/hasta el último guardar)
        datos_para_diagrama = self.datos_guardados if hasattr(self, "datos_guardados") else self.obtener_datos()
        ventana = VentanaEsfuerzoHormigon(datos_para_diagrama, self.datos_acero, self.datos_seccion)
        ventana.exec()

    def eventFilter(self, obj, event):
        if obj in getattr(self, "campos_a_validar", []):
            if event.type() == QEvent.Enter:
                if self.campos_invalidos.get(obj, False):
                    mostrar_mensaje_error_flotante(obj, self.error_label)
            elif event.type() == QEvent.Leave:
                self.error_label.hide()
        return super().eventFilter(obj, event)
