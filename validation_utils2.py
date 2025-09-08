from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from babel.numbers import format_decimal
import re

def parsear_numero(text):
    t = re.sub(r"[ '\u00A0]", '', text)
    if ',' in t and '.' in t:
        if t.rfind(',') > t.rfind('.'):
            t = t.replace('.', '')
            t = t.replace(',', '.')
        else:
            t = t.replace(',', '')
    elif ',' in t:
        parts = t.rsplit(',', 1)
        t = parts[0].replace(',', '') + '.' + parts[1] if len(parts) > 1 else t.replace(',', '.')
    elif t.count('.') > 1:
        parts = t.rsplit('.', 1)
        t = parts[0].replace('.', '') + '.' + parts[1]
    try:
        return float(t)
    except Exception:
        return None

def mostrar_numero(numero):
    return format_decimal(numero, format="0.####", locale='en_US')

class ErrorFloatingLabel(QLabel):
    def __init__(self, parent=None, color="#FF3333", text="Formato incorrecto"):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip)
        self.setStyleSheet(f"""
            background: {color};
            color: white;
            border-radius: 2px;
            padding: 1.5px 6px;
            font-size: 12px;
            border: none;
        """)
        self.setText(text)
        self.hide()
        self.campo_actual = None

def validar_en_tiempo_real(line_edit, campos_invalidos, error_label, color="#FF3333"):
    texto = line_edit.text()
    valor = parsear_numero(texto)
    # Caso especial: axial_columna_asce bloqueado en "Viga"
    if line_edit.objectName() == "axial_columna_asce" and not line_edit.isEnabled():
        valido = True   # siempre válido aunque sea 0
    else:
        valido = valor is not None and valor > 0

    if not valido:
        line_edit.setStyleSheet(f"border: 1.5px solid {color};")
        campos_invalidos[line_edit] = True
    else:
        line_edit.setStyleSheet("")
        campos_invalidos[line_edit] = False
        if error_label.isVisible() and getattr(error_label, "campo_actual", None) == line_edit:
            error_label.hide()

def mostrar_mensaje_error_flotante(line_edit, error_label, offset_x=10):
    geo = line_edit.geometry()
    parent_global = line_edit.parent().mapToGlobal(geo.topRight())
    error_label.adjustSize()
    y_campo = parent_global.y() + geo.height() // 2
    y_label = error_label.height() // 2
    error_label.move(parent_global.x() + offset_x, y_campo - y_label)
    error_label.show()
    error_label.raise_()
    error_label.campo_actual = line_edit

def corregir_y_normalizar(line_edit):
    texto_original = line_edit.text()
    valor = parsear_numero(texto_original)

    if valor is not None:
        nombre = line_edit.objectName()

        # Corrección automática si valor < 2 para ramales
        if nombre in ("disenar_columna_ramalesX", "disenar_columna_ramalesY", "disenar_columna_varillasX_2", "disenar_columna_varillasY_2") and valor < 2:
            line_edit.setText("2")
            return

        texto_formateado = mostrar_numero(valor)
        if texto_original != texto_formateado:
            line_edit.setText(texto_formateado)