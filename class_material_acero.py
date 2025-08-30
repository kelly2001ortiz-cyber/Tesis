from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import QEvent

from ui_material_acero import Ui_material_acero

from class_esfuerzo_deformacion_acero import VentanaEsfuerzoAcero

from validation_utils2 import (
    ErrorFloatingLabel,
    validar_en_tiempo_real,
    mostrar_mensaje_error_flotante,
    corregir_y_normalizar,
)

__all__ = [
    "VentanaEsfuerzoAcero",
]

class VentanaMaterialAcero(QDialog):
    def __init__(self, datos_iniciales=None):
        super().__init__()
        self.ui = Ui_material_acero()
        self.ui.setupUi(self)

        self.campos_a_validar = [
            self.ui.esfuerzo_fy,
            self.ui.modulo_Es,
            self.ui.esfuerzo_ultimo_acero,
            self.ui.def_fluencia_acero,
            self.ui.def_inicio_endurecimiento,
            self.ui.def_ultima_acero,
        ]
        self.campos_invalidos = {c: False for c in self.campos_a_validar}
        self.error_label = ErrorFloatingLabel(self)

        self.datos_guardados_callback = None
        self.datos_guardados = datos_iniciales.copy() if datos_iniciales else {}

        if datos_iniciales:
            self.ui.nombre_acero.setText(datos_iniciales.get("nombre_acero"))
            self.ui.esfuerzo_fy.setText(datos_iniciales.get("esfuerzo_fy"))
            self.ui.modulo_Es.setText(datos_iniciales.get("modulo_Es"))
            self.ui.esfuerzo_ultimo_acero.setText(datos_iniciales.get("esfuerzo_ultimo_acero"))
            self.ui.def_fluencia_acero.setText(datos_iniciales.get("def_fluencia_acero"))
            self.ui.def_inicio_endurecimiento.setText(datos_iniciales.get("def_inicio_endurecimiento"))
            self.ui.def_ultima_acero.setText(datos_iniciales.get("def_ultima_acero"))

        for campo in self.campos_a_validar:
            campo.textChanged.connect(lambda _, le=campo: self.on_modificacion(le))
            campo.editingFinished.connect(lambda le=campo: corregir_y_normalizar(le))
            campo.installEventFilter(self)

        self.ui.nombre_acero.textChanged.connect(lambda: self.on_modificacion_nombre())

        self.ui.btn_cancelar_acero.clicked.connect(self.close)
        self.ui.btn_guardar_acero.clicked.connect(self.guardar)
        self.ui.btn_mostrar_diagrama_ed_acero.clicked.connect(self.mostrar_diagrama_ed_acero)

        self.cambios_pendientes = False
        self.ui.btn_mostrar_diagrama_ed_acero.setEnabled(True)

    def on_modificacion(self, line_edit):
        validar_en_tiempo_real(line_edit, self.campos_invalidos, self.error_label)
        self.cambios_pendientes = True
        self.ui.btn_mostrar_diagrama_ed_acero.setEnabled(False)

    def on_modificacion_nombre(self):
        self.cambios_pendientes = True
        self.ui.btn_mostrar_diagrama_ed_acero.setEnabled(False)

    def obtener_datos(self):
        return {
            "nombre_acero": self.ui.nombre_acero.text(),
            "esfuerzo_fy": self.ui.esfuerzo_fy.text(),
            "modulo_Es": self.ui.modulo_Es.text(),
            "esfuerzo_ultimo_acero": self.ui.esfuerzo_ultimo_acero.text(),
            "def_fluencia_acero": self.ui.def_fluencia_acero.text(),
            "def_inicio_endurecimiento": self.ui.def_inicio_endurecimiento.text(),
            "def_ultima_acero": self.ui.def_ultima_acero.text(),
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

    def guardar(self):
        if not self.validar_campos():
            return
        self.datos_guardados = self.obtener_datos()
        if self.datos_guardados_callback:
            self.datos_guardados_callback(self.datos_guardados)
        self.cambios_pendientes = False
        self.ui.btn_mostrar_diagrama_ed_acero.setEnabled(True)

    def mostrar_diagrama_ed_acero(self):
        # Usar SIEMPRE los datos más recientes guardados (del dict global/hasta el último guardar)
        datos_para_diagrama = self.datos_guardados if hasattr(self, "datos_guardados") else self.obtener_datos()
        ventana = VentanaEsfuerzoAcero(datos_para_diagrama)
        ventana.exec()

    def eventFilter(self, obj, event):
        if obj in getattr(self, "campos_a_validar", []):
            if event.type() == QEvent.Enter:
                if self.campos_invalidos.get(obj, False):
                    mostrar_mensaje_error_flotante(obj, self.error_label)
            elif event.type() == QEvent.Leave:
                self.error_label.hide()
        return super().eventFilter(obj, event)
