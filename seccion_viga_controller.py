# seccion_viga_controller.py

from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QMessageBox
from validation_utils2 import (
    ErrorFloatingLabel,
    validar_en_tiempo_real,
    corregir_y_normalizar,
    mostrar_mensaje_error_flotante,
)

class SeccionVigaController(QObject):  # <--- Ahora hereda de QObject
    def __init__(self, ui, datos_iniciales, datos_guardados_callback=None):
        super().__init__()   # <--- Llama al init de QObject
        self.ui = ui  # instancia de Ui_ventana_principal
        self.datos_guardados_callback = datos_guardados_callback

        self.campos_a_validar = [
            self.ui.disenar_viga_base,
            self.ui.disenar_viga_altura,
            self.ui.disenar_viga_recubrimiento,
            self.ui.disenar_viga_varillas_inferior,
            self.ui.disenar_viga_diametro_inferior,
            self.ui.disenar_viga_varillas_superior,
            self.ui.disenar_viga_diametro_superior,
            self.ui.disenar_viga_diametro_transversal,
            self.ui.disenar_viga_espaciamiento,
        ]
        self.campos_invalidos = {c: False for c in self.campos_a_validar}
        self.error_label = ErrorFloatingLabel(self.ui.pg_viga)
        self._conectar_senales()
        self.llenar_campos(datos_iniciales)

    def _conectar_senales(self):
        try:
            self.ui.btn_calcular_viga.clicked.disconnect()
        except Exception:
            pass
        self.ui.btn_calcular_viga.clicked.connect(self.calcular)

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
        self.ui.disenar_viga_nombre.setText(datos.get("disenar_viga_nombre", ""))
        self.ui.disenar_viga_base.setText(datos.get("disenar_viga_base", ""))
        self.ui.disenar_viga_altura.setText(datos.get("disenar_viga_altura", ""))
        self.ui.disenar_viga_recubrimiento.setText(datos.get("disenar_viga_recubrimiento", ""))
        self.ui.disenar_viga_varillas_inferior.setText(datos.get("disenar_viga_varillas_inferior", ""))
        self.ui.disenar_viga_diametro_inferior.setText(datos.get("disenar_viga_diametro_inferior", ""))
        self.ui.disenar_viga_varillas_superior.setText(datos.get("disenar_viga_varillas_superior", ""))
        self.ui.disenar_viga_diametro_superior.setText(datos.get("disenar_viga_diametro_superior", ""))
        self.ui.disenar_viga_diametro_transversal.setText(datos.get("disenar_viga_diametro_transversal", ""))
        self.ui.disenar_viga_espaciamiento.setText(datos.get("disenar_viga_espaciamiento", ""))

    def on_modificacion(self, line_edit):
        validar_en_tiempo_real(line_edit, self.campos_invalidos, self.error_label)

    def obtener_datos(self):
        return {
            "disenar_viga_nombre": self.ui.disenar_viga_nombre.text(),
            "disenar_viga_base": self.ui.disenar_viga_base.text(),
            "disenar_viga_altura": self.ui.disenar_viga_altura.text(),
            "disenar_viga_recubrimiento": self.ui.disenar_viga_recubrimiento.text(),
            "disenar_viga_varillas_inferior": self.ui.disenar_viga_varillas_inferior.text(),
            "disenar_viga_diametro_inferior": self.ui.disenar_viga_diametro_inferior.text(),
            "disenar_viga_varillas_superior": self.ui.disenar_viga_varillas_superior.text(),
            "disenar_viga_diametro_superior": self.ui.disenar_viga_diametro_superior.text(),
            "disenar_viga_diametro_transversal": self.ui.disenar_viga_diametro_transversal.text(),
            "disenar_viga_espaciamiento": self.ui.disenar_viga_espaciamiento.text(),
        }

    def validar_campos(self):
        for campo in self.campos_a_validar:
            validar_en_tiempo_real(campo, self.campos_invalidos, self.error_label)
            if self.campos_invalidos[campo]:
                campo.setFocus()
                QMessageBox.warning(
                    self.ui.pg_viga,
                    "Revisar el formato",
                    "Formato incorrecto\nPor favor, revisar los campos resaltados en rojo"
                )
                return False
        return True

    def calcular(self):
        if not self.validar_campos():
            return
        datos = self.obtener_datos()
        QMessageBox.information(
                    self.ui.pg_viga,
                    "Cálculo terminado",
                    "Puede continuar"
                )
        if self.datos_guardados_callback:
            self.datos_guardados_callback(datos)
