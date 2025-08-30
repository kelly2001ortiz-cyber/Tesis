# class_definir_asce.py
# -*- coding: utf-8 -*-
"""
Diálogo ASCE con validaciones en vivo y guardado por callback, compatible con Python < 3.10.
- Valida en tiempo real 6 campos numéricos (Viga y Columna), usando validation_utils2.
- Guarda en self.datos_guardados y dispara datos_guardados_callback al pulsar Guardar.
- NO rellena los 3 QLineEdit de solo lectura (def_*); eso se hace en el main antes de exec().

UI esperada (de ui_definir_asce.py):
  - Solo lectura: def_max_asce, def_ultima_asce, def_fluencia_asce  [NO se tocan aquí]
  - Viga: long_viga_asce, coef_viga_asce, cortante_viga_asce, condicion_viga_asce (QComboBox)
  - Columna: long_columna_asce, axial_columna_asce, cortante_columna_asce, condicion_columna_asce (QComboBox)
"""

from typing import Optional

from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import QEvent

from ui_definir_asce import Ui_definir_asce
from validation_utils2 import (
    ErrorFloatingLabel,
    validar_en_tiempo_real,
    mostrar_mensaje_error_flotante,
    corregir_y_normalizar,
)


class VentanaDefinirASCE(QDialog):
    """
    Diálogo para parámetros ASCE:
      - Valida en vivo 6 campos numéricos (3 Viga + 3 Columna).
      - Guarda en self.datos_guardados y dispara datos_guardados_callback al pulsar Guardar.
      - NO rellena los 3 QLineEdit de solo lectura (def_*); eso lo hace el main.

    Campos validados:
      Viga: long_viga_asce, coef_viga_asce, cortante_viga_asce
      Columna: long_columna_asce, axial_columna_asce, cortante_columna_asce
    """

    def __init__(self, datos_iniciales: Optional[dict] = None):
        super().__init__()
        self.ui = Ui_definir_asce()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())

        # ---- Estado + callback de guardado ----
        self.datos_guardados = datos_iniciales.copy() if datos_iniciales else {}
        self.datos_guardados_callback = None
        self.cambios_pendientes = False

        # ---- Campos a validar (mismo patrón que class_material_hormigon) ----
        self.campos_a_validar = [
            # Viga
            self.ui.long_viga_asce,
            self.ui.coef_viga_asce,
            self.ui.cortante_viga_asce,
            # Columna
            self.ui.long_columna_asce,
            self.ui.axial_columna_asce,
            self.ui.cortante_columna_asce,
        ]
        self.campos_invalidos = {c: False for c in self.campos_a_validar}
        self.error_label = ErrorFloatingLabel(self)

        # Conexiones de validación y normalización
        for campo in self.campos_a_validar:
            campo.textChanged.connect(lambda _, le=campo: self.on_modificacion(le))
            campo.editingFinished.connect(lambda le=campo: corregir_y_normalizar(le))
            campo.installEventFilter(self)

        # Botones
        self.ui.btn_cancelar_asce.clicked.connect(self.close)
        self.ui.btn_guardar_asce.clicked.connect(self.guardar)

        # ---- Precarga si hay datos ----
        if datos_iniciales:
            self._cargar_datos(datos_iniciales)

    # ----------------- Carga/lectura -----------------
    def _cargar_datos(self, d: dict):
        # NOTA: los 3 QLineEdit de solo lectura (def_*) se llenan en el main
        # Viga
        self.ui.long_viga_asce.setText(str(d.get("long_viga_asce", "")))
        self.ui.coef_viga_asce.setText(str(d.get("coef_viga_asce", "")))
        self.ui.cortante_viga_asce.setText(str(d.get("cortante_viga_asce", "")))
        self._set_combo_text(self.ui.condicion_viga_asce, d.get("condicion_viga_asce"))

        # Columna
        self.ui.long_columna_asce.setText(str(d.get("long_columna_asce", "")))
        self.ui.axial_columna_asce.setText(str(d.get("axial_columna_asce", "")))
        self.ui.cortante_columna_asce.setText(str(d.get("cortante_columna_asce", "")))
        self._set_combo_text(self.ui.condicion_columna_asce, d.get("condicion_columna_asce"))

        # (Opcional) Si en el dict llegan también los 3 valores de solo-lectura, muéstralos:
        if "def_max_asce" in d:
            self.ui.def_max_asce.setText(str(d.get("def_max_asce", "")))
        if "def_ultima_asce" in d:
            self.ui.def_ultima_asce.setText(str(d.get("def_ultima_asce", "")))
        if "def_fluencia_asce" in d:
            self.ui.def_fluencia_asce.setText(str(d.get("def_fluencia_asce", "")))

    def _set_combo_text(self, combo, text):
        if not text:
            return
        target = (text or "").strip().lower()
        for i in range(combo.count()):
            if (combo.itemText(i) or "").strip().lower() == target:
                combo.setCurrentIndex(i)
                return

    def _obtener_datos(self) -> dict:
        return {
            # Solo-lectura (poblados desde el main antes de exec())
            "def_max_asce": self.ui.def_max_asce.text(),
            "def_ultima_asce": self.ui.def_ultima_asce.text(),
            "def_fluencia_asce": self.ui.def_fluencia_asce.text(),
            # Viga
            "long_viga_asce": self.ui.long_viga_asce.text(),
            "coef_viga_asce": self.ui.coef_viga_asce.text(),
            "cortante_viga_asce": self.ui.cortante_viga_asce.text(),
            "condicion_viga_asce": self.ui.condicion_viga_asce.currentText(),
            # Columna
            "long_columna_asce": self.ui.long_columna_asce.text(),
            "axial_columna_asce": self.ui.axial_columna_asce.text(),
            "cortante_columna_asce": self.ui.cortante_columna_asce.text(),
            "condicion_columna_asce": self.ui.condicion_columna_asce.currentText(),
        }

    # ----------------- Validación -----------------
    def on_modificacion(self, line_edit):
        validar_en_tiempo_real(line_edit, self.campos_invalidos, self.error_label)
        self.cambios_pendientes = True

    def validar_campos(self) -> bool:
        for campo in self.campos_a_validar:
            validar_en_tiempo_real(campo, self.campos_invalidos, self.error_label)
            if self.campos_invalidos[campo]:
                campo.setFocus()
                QMessageBox.warning(
                    self, "Revisar el formato",
                    "Formato incorrecto\nPor favor, revisar los campos resaltados en rojo"
                )
                return False
        return True

    def eventFilter(self, obj, event):
        if obj in getattr(self, "campos_a_validar", []):
            if event.type() == QEvent.Enter:
                if self.campos_invalidos.get(obj, False):
                    mostrar_mensaje_error_flotante(obj, self.error_label)
            elif event.type() == QEvent.Leave:
                self.error_label.hide()
        return super().eventFilter(obj, event)

    # ----------------- Guardar -----------------
    def guardar(self):
        if not self.validar_campos():
            return
        self.datos_guardados = self._obtener_datos()
        if self.datos_guardados_callback:
            self.datos_guardados_callback(self.datos_guardados)
        self.cambios_pendientes = False
