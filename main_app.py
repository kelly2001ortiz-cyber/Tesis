from PySide6.QtWidgets import (
    QMainWindow, QApplication, QDialog, QMessageBox, QFileDialog
)
from PySide6.QtCore import Slot
import sys
import os
import json
import numpy as np

# ==== UIs (ajusta si tus nombres difieren) ====
from ui_ventana_principal import Ui_ventana_principal
from ui_ayuda import Ui_ayuda

# ==== Vistas/Controladores existentes (ajusta si difieren) ====
from class_material_hormigon import VentanaMaterialHormigon
from class_material_acero import VentanaMaterialAcero
from class_definir_fibras import VentanaDefinirFibras
from seccion_columna_controller import SeccionColumnaController
from vista_dinamica_seccion_columna import SeccionColumnaGrafico
from seccion_viga_controller import SeccionVigaController
from vista_dinamica_seccion_viga import SeccionVigaGrafico
from class_definir_asce import VentanaDefinirASCE
from calculo_mc_service import CalculadoraMomentoCurvatura
from calculo_mc_servicev import CalculadoraMomentoCurvaturaV
from mostrar_mc_dialog import VentanaMostrarMC
from mostrar_mc_dialogv import VentanaMostrarMCV
from class_mostrar_DI import VentanaMostrarDI
from class_mostrar_fibras import class_mostrar_fibras

# ---------------- Ventanas auxiliares ----------------

class VentanaAyuda(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ayuda()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())


# ---------------- Ventana principal ----------------

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ventana_principal()
        self.ui.setupUi(self)
        self.showMaximized()

        self.ui._owner = self  # para que otras clases puedan invalidar resultados/apagar fibras
        # ====== Estado de archivo/proyecto ======
        self._project_path = None          # ruta actual del .mcproj
        self._is_dirty = False             # hay cambios no guardados
        self._app_title = "Diagrama M-C"   # título base de la app (ajusta si quieres)
        self._update_window_title()

        # ====== Datos iniciales de ejemplo (reemplaza por los tuyos si ya los cargas) ======
        self._set_default_data()

        # ====== Ventanas auxiliares ======
        self.ventana_ayuda = VentanaAyuda()

        self.calc_mc = CalculadoraMomentoCurvatura()
        self.calc_mcv = CalculadoraMomentoCurvaturaV()
        # Resultados (se reemplazan en cada click a Calcular)
        self.mc_matriz = None   # np.ndarray columnas: [θ_Hog, M_Hog, θ_Mu, M_Mu, θ_Mc, M_Mc]
        self.mc_series = {}     # dict con series por modelo
        self.di_matriz = None   # np.ndarray (n,3): [c,  Pn,  Mn]
        self.di_series = {}     # {'phi':(x=Mn,y=Pn), 'sinphi':(x,y)}
        
        # ====== Inicializar interfaz ======
        self.actualizar_lineedit_materiales()
        self.conectar_lineedits_proyecto()
        # Para desahabilitar la direccion en viga
        self.ui.seccion_analisis.currentIndexChanged.connect(self.actualizar_direccion)
        self.actualizar_direccion()

        # Menús (ajusta nombres si difieren en tu UI)
        self.ui.actionHormig_n_2.triggered.connect(self.abrir_material_hormigon)
        self.ui.actionAcero_2.triggered.connect(self.abrir_material_acero)
        self.ui.actionDocumentaci_n.triggered.connect(self.abrir_documentacion)
        self.ui.actionParametros_ASCE.triggered.connect(self.abrir_definir_asce)
        self.ui.actionCapas_de_Fibras.triggered.connect(self.abrir_definir_fibras)
        self.ui.actionDiagrama_de_iteracion.triggered.connect(self.abrir_mostrar_di)
        self.ui.actionDiagrama_M_C.triggered.connect(self.abrir_mostrar_mc)
        self.ui.actionProyecto.triggered.connect(self.mostrar_proyecto)
        self.ui.actionSeccion.triggered.connect(self.mostrar_seccion)
        self.ui.seccion_analisis.currentTextChanged.connect(self.cambiar_pagina_analisis)
        self.ui.seccion_analisis.currentTextChanged.connect(self.invalidar_resultados_y_apagar_fibras)
        self.ui.direccion_analisis.currentTextChanged.connect(self.invalidar_resultados_y_apagar_fibras)
        self.ui.actionCapas_de_Fibras_2.triggered.connect(self.mostrar_fibras)

        # === Acciones de archivo ===
        # Asegúrate de tener estas acciones en tu .ui: actionNuevo, actionAbrir, actionGuardar, actionGuardar_como, actionSalir
        if hasattr(self.ui, "actionNuevo"):
            self.ui.actionNuevo.triggered.connect(self.menu_nuevo)
        if hasattr(self.ui, "actionAbrir"):
            self.ui.actionAbrir.triggered.connect(self.menu_abrir)
        if hasattr(self.ui, "actionGuardar"):
            self.ui.actionGuardar.triggered.connect(self.menu_guardar)
        if hasattr(self.ui, "actionGuardar_como"):
            self.ui.actionGuardar_como.triggered.connect(self.menu_guardar_como)
        if hasattr(self.ui, "actionSalir"):
            self.ui.actionSalir.triggered.connect(self.menu_salir)

        # Página inicial
        self.mostrar_columna()

        # Controladores de sección
        self.seccion_columna_controller = None
        self.seccion_viga_controller = None

        # Marcar cambios cuando se modifiquen datos
        self._wire_dirty_flags()

    # ---------------- Utilidades de estado/archivo ----------------

    def _set_default_data(self):
        """Inicializa los diccionarios de datos por defecto."""
        self.material_hormigon_data = {
            "nombre_hormigon": "f'c 210",
            "esfuerzo_fc": "210",
            "modulo_Ec": "218819.788",
            "def_max_sin_confinar": "0.002",
            "def_ultima_sin_confinar": "0.0038",
            "def_ultima_confinada": "0.09",
        }
        self.material_acero_data = {
            "nombre_acero": "fy 4200",
            "esfuerzo_fy": "4200",
            "modulo_Es": "2000000",
            "esfuerzo_ultimo_acero": "7457",
            "def_fluencia_acero": "0.0021",
            "def_inicio_endurecimiento": "0.0139",
            "def_ultima_acero": "0.09",
        }
        self.seccion_columna_data = {
            "disenar_columna_base": "40",
            "disenar_columna_altura": "90",
            "disenar_columna_varillasX_2": "10",
            "disenar_columna_varillasY_2": "10",
            "disenar_columna_diametro_longitudinal_2": "25",
            "disenar_columna_recubrimiento": "3",
            "disenar_columna_ramalesX": "4",
            "disenar_columna_ramalesY": "4",
            "disenar_columna_diametro_transversal": "12",
            "disenar_columna_espaciamiento": "10",
        }
        self.seccion_viga_data = {
            "disenar_viga_base": "40",
            "disenar_viga_altura": "80",
            "disenar_viga_recubrimiento": "3",
            "disenar_viga_varillas_inferior": "4",
            "disenar_viga_diametro_inferior": "25",
            "disenar_viga_varillas_superior": "2",
            "disenar_viga_diametro_superior": "14",
            "disenar_viga_diametro_transversal": "10",
            "disenar_viga_espaciamiento": "10",
        }
        self.proyecto_data = {
            "descripcion_proyecto": "Nombre Proyecto",
            "descripcion_ingeniero": "Luis Flor",
            "descripcion_seccion": "C40X40",
        }
        self.capas_fibras_data = {"fibras_x": "10", "fibras_y": "10"}
        self.asce_data = {
            # Viga
            "long_viga_asce": "6",
            "coef_viga_asce": "1.05",
            "cortante_viga_asce": "2000",
            "condicion_viga_asce": "Flexión",
            # Columna
            "long_columna_asce": "6",
            "axial_columna_asce": "20000",
            "cortante_columna_asce": "6000",
            "condicion_columna_asce": "Flexión",
            # Campos de solo-lectura (se sobreescriben SIEMPRE antes de abrir el diálogo)
            "def_max_asce": "",
            "def_ultima_asce": "",
            "def_fluencia_asce": "",
        }

    def _wire_dirty_flags(self):
        """Conecta callbacks que marcan el proyecto como modificado."""
        # Proyecto
        self.ui.descripcion_proyecto.textChanged.connect(self._mark_dirty)
        self.ui.descripcion_ingeniero.textChanged.connect(self._mark_dirty)
        self.ui.descripcion_seccion.textChanged.connect(self._mark_dirty)
        # Selector Columna/Viga
        self.ui.seccion_analisis.currentTextChanged.connect(self._mark_dirty)
        self.ui.direccion_analisis.currentTextChanged.connect(self._mark_dirty)

    def _wire_dirty_lineedits(self, parent):
        """Conecta todos los QLineEdit dentro del widget `parent` a _mark_dirty()."""
        from PySide6.QtWidgets import QLineEdit
        for le in parent.findChildren(QLineEdit):
            le.textEdited.connect(self._mark_dirty)

    def _mark_dirty(self, *args, **kwargs):
        if not self._is_dirty:
            self._is_dirty = True
            self._update_window_title()

    def _clear_dirty(self):
        self._is_dirty = False
        self._update_window_title()

    def _update_window_title(self):
        name = os.path.basename(self._project_path) if self._project_path else "Sin título.mcproj"
        mark = "*" if self._is_dirty else ""
        self.setWindowTitle(f"{self._app_title} - {name}{mark}")

    def _project_to_dict(self):
        """Empaqueta todos los datos que deseamos guardar."""
        payload = {
            "version": 1,
            "tipo_seleccionado": self.ui.seccion_analisis.currentText(),  # "Columna" o "Viga"
            "direccion_analisis": self.ui.direccion_analisis.currentText(),
            "material_hormigon_data": self.material_hormigon_data,
            "material_acero_data": self.material_acero_data,
            "seccion_columna_data": self.seccion_columna_data,
            "seccion_viga_data": self.seccion_viga_data,
            "proyecto_data": self.proyecto_data,
            "capas_fibras_data": self.capas_fibras_data,
            "asce_data": self.asce_data,
        }
        return payload

    def _apply_project_dict(self, payload: dict):
        """Carga los datos del payload a la UI y a las estructuras."""
        # Validaciones simples
        def getd(obj, key, default):
            return obj.get(key, default) if isinstance(obj, dict) else default

        self.material_hormigon_data = getd(payload, "material_hormigon_data", self.material_hormigon_data)
        self.material_acero_data = getd(payload, "material_acero_data", self.material_acero_data)
        self.seccion_columna_data = getd(payload, "seccion_columna_data", self.seccion_columna_data)
        self.seccion_viga_data = getd(payload, "seccion_viga_data", self.seccion_viga_data)
        self.proyecto_data = getd(payload, "proyecto_data", self.proyecto_data)
        self.capas_fibras_data = getd(payload, "capas_fibras_data", self.capas_fibras_data)
        self.asce_data = getd(payload, "asce_data", self.asce_data)

        # Refrescar campos visibles
        self.ui.descripcion_proyecto.setText(str(self.proyecto_data.get("descripcion_proyecto", "")))
        self.ui.descripcion_ingeniero.setText(str(self.proyecto_data.get("descripcion_ingeniero", "")))
        self.ui.descripcion_seccion.setText(str(self.proyecto_data.get("descripcion_seccion", "")))
        self.actualizar_lineedit_materiales()

        # Cambiar página según lo guardado
        tipo = payload.get("tipo_seleccionado", "Columna")
        idx = self.ui.seccion_analisis.findText(tipo)
        if idx >= 0:
            self.ui.seccion_analisis.setCurrentIndex(idx)

        # Dirección (si corresponde)
        dir_txt = payload.get("direccion_analisis")
        if dir_txt and self.ui.direccion_analisis.isEnabled():
            didx = self.ui.direccion_analisis.findText(dir_txt)
            if didx >= 0:
                self.ui.direccion_analisis.setCurrentIndex(didx)

        # Re-dibujar vistas/propiedades
        if tipo.lower() == "columna":
            self.mostrar_columna()
        else:
            self.mostrar_viga()

        # Los resultados calculados se invalidan al cargar
        self.mc_matriz = None
        self.mc_series = {}
        self.di_matriz = None
        self.di_series = {}

    def _maybe_save_changes(self) -> bool:
        """Si hay cambios no guardados, pregunta. True si se puede continuar, False si se cancela."""
        if not self._is_dirty:
            return True
        msg = QMessageBox(self)
        msg.setWindowTitle("Cambios no guardados")
        msg.setText("Tienes cambios sin guardar.\n¿Deseas guardar antes de continuar?")

        # Botones en español
        guardar_btn = msg.addButton("Guardar", QMessageBox.ButtonRole.AcceptRole)
        descartar_btn = msg.addButton("Descartar", QMessageBox.ButtonRole.DestructiveRole)
        cancelar_btn = msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)

        msg.setDefaultButton(guardar_btn)
        msg.exec()

        if msg.clickedButton() == guardar_btn:
            return self._handle_save_flow()
        elif msg.clickedButton() == descartar_btn:
            return True
        else:
            return False

    def _handle_save_flow(self) -> bool:
        """Gestiona Guardar/Guardar como, devolviendo True si se guardó o False si falló/canceló."""
        if self._project_path:
            return self._save_to_path(self._project_path)
        else:
            return self._save_as_dialog()

    def _save_as_dialog(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar como",
            self._suggested_filename(),
            "Proyecto M-C (*.mcproj);;JSON (*.json);;Todos los archivos (*)"
        )
        if not path:
            return False
        if not (path.endswith(".mcproj") or path.endswith(".json")):
            path += ".mcproj"
        ok = self._save_to_path(path)
        if ok:
            self._project_path = path
            self._clear_dirty()
        return ok

    def _save_to_path(self, path: str) -> bool:
        try:
            payload = self._project_to_dict()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            self._project_path = path
            self._clear_dirty()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar el archivo.\n\n{e}")
            return False

    def _suggested_filename(self) -> str:
        base = self.proyecto_data.get("descripcion_seccion", "Proyecto_MC")
        return f"{base}.mcproj"

    # ---------------- Navegación/secciones ----------------

    def actualizar_direccion(self):
        tipo = self.ui.seccion_analisis.currentText()
        if tipo == "Viga":
            # Deshabilitar y fijar en Dirección Y
            self.ui.direccion_analisis.setCurrentText("Dirección Y")  # ojo: usa exactamente como está escrito en tu combobox
            self.ui.direccion_analisis.setEnabled(False)
            self.ui.actionDiagrama_de_iteracion.setEnabled(False)
        else:
            # Habilitar para Columna
            self.ui.direccion_analisis.setEnabled(True)
            self.ui.actionDiagrama_de_iteracion.setEnabled(True)

    def cambiar_pagina_analisis(self, texto):
        if texto.lower() == "columna":
            self.ui.stackedWidget.setCurrentWidget(self.ui.pg_p_columna)
            self.mostrar_columna()
            self.ui.texto_seccion.setText("COLUMNA")
        elif texto.lower() == "viga":
            self.ui.stackedWidget.setCurrentWidget(self.ui.pg_p_viga)
            self.mostrar_viga()
            self.ui.texto_seccion.setText("VIGA")

    def mostrar_fibras(self):
        """Dibuja la sección de fibras dentro de ui.cuadricula_seccion SIN cambiar de página."""
        if self.ui.actionCapas_de_Fibras_2.isChecked():
            visor = class_mostrar_fibras(
                self.ui,
                self.seccion_columna_data,
                self.seccion_viga_data,
                self.capas_fibras_data,
            )
            visor.mostrar()
            self._visor_fibras = visor  # mantener referencia
        else:
            texto = self.ui.seccion_analisis.currentText()
            if texto.lower() == "columna":
                self.mostrar_columna()
            elif texto.lower() == "viga":
                self.mostrar_viga()

    def conectar_lineedits_proyecto(self):
        self.ui.descripcion_proyecto.textChanged.connect(
            lambda text: self._on_change_and_set(self.actualizar_proyecto_data, "descripcion_proyecto", text)
        )
        self.ui.descripcion_ingeniero.textChanged.connect(
            lambda text: self._on_change_and_set(self.actualizar_proyecto_data, "descripcion_ingeniero", text)
        )
        self.ui.descripcion_seccion.textChanged.connect(
            lambda text: self._on_change_and_set(self.actualizar_proyecto_data, "descripcion_seccion", text)
        )

    def _on_change_and_set(self, setter, key, value):
        setter(key, value)
        self._mark_dirty()

    def actualizar_proyecto_data(self, clave, valor):
        self.proyecto_data[clave] = valor

    def actualizar_lineedit_materiales(self):
        self.ui.proyecto_fc.setText(str(self.material_hormigon_data.get("esfuerzo_fc", "")))
        self.ui.proyecto_fy.setText(str(self.material_acero_data.get("esfuerzo_fy", "")))

    # ---------------- Abrir diálogos ----------------

    def abrir_material_hormigon(self):
        ventana = VentanaMaterialHormigon(self.material_hormigon_data, self.material_acero_data, self.seccion_columna_data)
        ventana.datos_guardados_callback = self._wrap_dirty(self.actualizar_material_hormigon_data)
        ventana.exec()

    def _wrap_dirty(self, fn):
        def inner(datos):
            fn(datos)
            self._mark_dirty()
        return inner

    def actualizar_material_hormigon_data(self, datos):
        self.material_hormigon_data = datos.copy()
        self.actualizar_lineedit_materiales()
        # 🔴 Invalida resultados para forzar "Calcular" otra vez
        self.invalidar_resultados_y_apagar_fibras()

    def abrir_material_acero(self):
        ventana = VentanaMaterialAcero(self.material_acero_data)
        ventana.datos_guardados_callback = self._wrap_dirty(self.actualizar_material_acero_data)
        ventana.exec()

    def actualizar_material_acero_data(self, datos):
        self.material_acero_data = datos.copy()
        if datos.get("def_ultima_acero") is not None:
            self.material_hormigon_data["def_ultima_confinada"] = datos["def_ultima_acero"]
        self.actualizar_lineedit_materiales()
         # 🔴 Invalida resultados para forzar "Calcular" otra vez
        self.invalidar_resultados_y_apagar_fibras()

    def abrir_documentacion(self):
        self.ventana_ayuda.exec()

    def abrir_definir_asce(self):
        # --- Poblar SIEMPRE los 3 lineedits de solo-lectura desde los diccionarios de materiales ---
        self.asce_data["def_max_asce"] = str(self.material_hormigon_data.get("def_max_sin_confinar", ""))
        self.asce_data["def_ultima_asce"] = str(self.material_hormigon_data.get("def_ultima_sin_confinar", ""))
        self.asce_data["def_fluencia_asce"] = str(self.material_acero_data.get("def_fluencia_acero", ""))

        self.ventana_definir_asce = VentanaDefinirASCE(self.asce_data)

        self.ventana_definir_asce.ui.def_max_asce.setText(self.asce_data["def_max_asce"])
        self.ventana_definir_asce.ui.def_ultima_asce.setText(self.asce_data["def_ultima_asce"])
        self.ventana_definir_asce.ui.def_fluencia_asce.setText(self.asce_data["def_fluencia_asce"])

        self.ventana_definir_asce.datos_guardados_callback = self._wrap_dirty(self.actualizar_asce_data)
        self.ventana_definir_asce.exec()

    def actualizar_asce_data(self, datos):
        self.asce_data = datos.copy()
        self.mc_matriz = None
        self.mc_series = {}
        self.di_matriz = None
        self.di_series = {}

    def _apagar_capa_fibras(self):
        accion = getattr(self.ui, "actionCapas_de_Fibras_2", None)
        if accion is not None and accion.isChecked():
            accion.setChecked(False)

    # en VentanaPrincipal (método nuevo)
    def invalidar_resultados_y_apagar_fibras(self):
        # 1) desmarcar la capa de fibras
        try:
            act = getattr(self.ui, "actionCapas_de_Fibras_2", None)
            if act is not None and act.isChecked():
                act.setChecked(False)
        except Exception:
            pass
        # 2) invalidar resultados (obliga a “Calcular” otra vez)
        self.mc_matriz = None
        self.mc_series = {}
        self.di_matriz = None
        self.di_series = {}

    def abrir_definir_fibras(self):
        ventana = VentanaDefinirFibras(self.capas_fibras_data, self._wrap_dirty(self.actualizar_fibras_data), parent=self)

        ventana.exec()

    def actualizar_fibras_data(self, datos):
        self.capas_fibras_data = datos.copy()
        self.mc_matriz = None
        self.mc_series = {}
        self.di_matriz = None
        self.di_series = {}

    def abrir_mostrar_di(self):
        if not getattr(self, "di_series", None):
            QMessageBox.warning(self, "Diagrama de Interacción", "Primero presiona Calcular para generar el DI.")
            return
        self.ventana_mostrar_di = VentanaMostrarDI(
            self.seccion_columna_data,
            di_matriz=self.di_matriz,
            di_series=self.di_series,
            parent=self
        )
        self.ventana_mostrar_di.exec()

    def abrir_mostrar_mc(self):
        if not getattr(self, "mc_series", None):
            QMessageBox.warning(self, "Diagrama M–C", "Primero presiona Calcular para generar las curvas.")
            return
        texto = self.ui.seccion_analisis.currentText()
        if texto.lower() == "columna":
            dlg = VentanaMostrarMC(self.mc_series, parent=self)
        elif texto.lower() == "viga":
            dlg = VentanaMostrarMC(self.mc_series, parent=self)
        dlg.exec()

    # ---------------- Vistas secciones / propiedades ----------------

    @Slot()
    def mostrar_proyecto(self):
        self.ui.stackedWidget_proyecto.setCurrentIndex(0)
        self.actualizar_lineedit_materiales()
        texto = self.ui.seccion_analisis.currentText()
        if texto.lower() == "columna":
            self.propiedades_columna()
        elif texto.lower() == "viga":
            self.propiedades_viga()

    @Slot()
    def mostrar_seccion(self):
        self.ui.stackedWidget_proyecto.setCurrentIndex(1)
        texto = self.ui.seccion_analisis.currentText()
        if texto.lower() == "columna":
            self.mostrar_columna()
        elif texto.lower() == "viga":
            self.mostrar_viga()

    @Slot()
    def mostrar_columna(self):
        self.ui.stackedWidget_seccion.setCurrentWidget(self.ui.pg_columna)
        self.seccion_columna_controller = SeccionColumnaController(
            self.ui, self.seccion_columna_data, self._wrap_dirty(self.actualizar_seccion_columna_data)
        )
        self.ui.disenar_columna_nombre.setText(str(self.proyecto_data.get("descripcion_seccion", "")))
        SeccionColumnaGrafico(self.ui.cuadricula_seccion, self.seccion_columna_data, ui=self.ui)
        self.propiedades_columna()
        # <<< conecta todos los lineedit de pg_columna
        self._wire_dirty_lineedits(self.ui.pg_columna)

    def propiedades_columna(self):
        b = int(self.seccion_columna_data.get("disenar_columna_base", "0"))
        h = int(self.seccion_columna_data.get("disenar_columna_altura", "0"))
        n_x = int((self.seccion_columna_data.get("disenar_columna_varillasX_2", "0")))
        n_y = int((self.seccion_columna_data.get("disenar_columna_varillasY_2", "0")))
        dlong = int(self.seccion_columna_data.get("disenar_columna_diametro_longitudinal_2", "0"))
        Ag = round(b * h, 2)
        As = round(((n_x * 2) + (n_y - 2) * 2) * np.pi / 4 * (dlong / 10) ** 2, 2)
        rho = round(As / Ag * 100, 4)
        self.ui.columna_area_gruesa.setText(str(Ag))
        self.ui.columna_total_as.setText(str(As))
        self.ui.columna_rho.setText(str(rho))

    def actualizar_seccion_columna_data(self, datos):
        self.seccion_columna_data = datos.copy()
        if hasattr(self, "ventana_definir_asce") and self.ventana_definir_asce is not None:
            condicion = self.ventana_definir_asce.ui.condicion_columna_asce.currentText()
        else:
            # Si nunca se abrió el diálogo, usar un default razonable o lo que tengas en asce_data
            condicion = self.asce_data.get("condicion_columna_asce", "Flexión")
        mc_matriz, mc_series, di_matriz, di_series = self.calc_mc.ejecutar(
            self.material_hormigon_data,
            self.material_acero_data,
            self.seccion_columna_data,
            self.capas_fibras_data,
            self.ui.direccion_analisis,
            self.asce_data,
            condicion,
        )
        self.mc_matriz = mc_matriz
        self.mc_series = mc_series
        self.di_matriz = di_matriz
        self.di_series = di_series

    @Slot()
    def mostrar_viga(self):
        self.ui.stackedWidget_seccion.setCurrentWidget(self.ui.pg_viga)
        self.seccion_viga_controller = SeccionVigaController(
            self.ui, self.seccion_viga_data, self._wrap_dirty(self.actualizar_seccion_viga_data)
        )
        self.ui.disenar_viga_nombre.setText(str(self.proyecto_data.get("descripcion_seccion", "")))
        SeccionVigaGrafico(self.ui.cuadricula_seccion, self.seccion_viga_data, ui=self.ui)
        self.propiedades_viga()
        # <<< conecta todos los lineedit de pg_viga
        self._wire_dirty_lineedits(self.ui.pg_viga)

    def propiedades_viga(self):
        b = int(self.seccion_viga_data.get("disenar_viga_base", "0"))
        h = int(self.seccion_viga_data.get("disenar_viga_altura", "0"))
        n_sup = int((self.seccion_viga_data.get("disenar_viga_varillas_superior", "0")))
        n_inf = int((self.seccion_viga_data.get("disenar_viga_varillas_inferior", "0")))
        d_sup = int(self.seccion_viga_data.get("disenar_viga_diametro_superior", "0"))
        d_inf = int(self.seccion_viga_data.get("disenar_viga_diametro_inferior", "0"))
        Ag = round(b * h, 2)
        As_sup = round(n_sup * np.pi / 4 * (d_sup / 10) ** 2, 2)
        As_inf = round(n_inf * np.pi / 4 * (d_inf / 10) ** 2, 2)
        rho_sup = round(As_sup / Ag * 100, 4)
        rho_inf = round(As_inf / Ag * 100, 4)
        self.ui.viga_area_gruesa.setText(str(Ag))
        self.ui.viga_as_sup.setText(str(As_sup))
        self.ui.viga_as_inf.setText(str(As_inf))
        self.ui.viga_rho_sup.setText(str(rho_sup))
        self.ui.viga_rho_inf.setText(str(rho_inf))

    def actualizar_seccion_viga_data(self, datos):
        self.seccion_viga_data = datos.copy()
        # Leer texto del QComboBox que vive en el diálogo VentanaDefinirASCE
        if hasattr(self, "ventana_definir_asce") and self.ventana_definir_asce is not None:
            condicion = self.ventana_definir_asce.ui.condicion_viga_asce.currentText()
        else:
            # Si nunca se abrió el diálogo, usar un default razonable o lo que tengas en asce_data
            condicion = self.asce_data.get("condicion_viga_asce", "Flexión")

        mc_matriz, mc_series = self.calc_mcv.ejecutar(
            self.material_hormigon_data,
            self.material_acero_data,
            self.seccion_viga_data,
            self.capas_fibras_data,
            self.asce_data,
            condicion,
        )
        self.mc_matriz = mc_matriz
        self.mc_series = mc_series

    # ---------------- Acciones de menú (Archivo) ----------------

    def menu_nuevo(self):
        if not self._maybe_save_changes():
            return
        self._set_default_data()
        # Limpiar ruta y resultados
        self._project_path = None
        self.mc_matriz = None
        self.mc_series = {}
        self.di_matriz = None
        self.di_series = {}
        # Refrescar UI
        self.actualizar_lineedit_materiales()
        self.ui.descripcion_proyecto.setText(self.proyecto_data["descripcion_proyecto"])
        self.ui.descripcion_ingeniero.setText(self.proyecto_data["descripcion_ingeniero"])
        self.ui.descripcion_seccion.setText(self.proyecto_data["descripcion_seccion"])
        # Forzar vista inicial
        idx = self.ui.seccion_analisis.findText("Columna")
        if idx >= 0:
            self.ui.seccion_analisis.setCurrentIndex(idx)
        self.mostrar_columna()
        self._clear_dirty()

    def menu_abrir(self):
        if not self._maybe_save_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir proyecto",
            "",
            "Proyecto M-C (*.mcproj *.json);;Todos los archivos (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self._apply_project_dict(payload)
            self._project_path = path
            self._clear_dirty()
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", f"No se pudo abrir el archivo.\n\n{e}")

    def menu_guardar(self):
        if self._project_path:
            self._save_to_path(self._project_path)
        else:
            self._save_as_dialog()

    def menu_guardar_como(self):
        self._save_as_dialog()

    def menu_salir(self):
        # Salir ventana principal (respetando cambios)
        self.close()

    # ---------------- Eventos de ventana ----------------

    def closeEvent(self, event):
        if self._maybe_save_changes():
            event.accept()
        else:
            event.ignore()


# ---------------- main ----------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VentanaPrincipal()
    window.show()
    sys.exit(app.exec())
