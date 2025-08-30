from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication


class VentanaMostrarTabla(QDialog):
    def __init__(self, series: dict, checks: dict, etiquetas: dict,
                 titulo: str = "Tabla de resultados", subheaders=("X", "Y"), parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        # Un tamaño inicial mínimo; luego se fijará con _ajustar_y_bloquear_tamano()
        self.resize(200, 500)

        layout = QVBoxLayout(self)

        # Determinar qué modelos están activos
        modelos_activos = [(clave, etiquetas[clave]) for clave, chk in checks.items()
                           if chk.isChecked() and clave in series]

        if not modelos_activos:
            lbl = QLabel("No hay métodos seleccionados.")
            layout.addWidget(lbl)
            # Bloquear algo razonable
            self.setFixedSize(self.sizeHint())
            return

        # Filas = datos + 2 encabezados
        max_filas = max(len(series[clave][0]) for clave, _ in modelos_activos)
        ncols = len(modelos_activos) * 2

        self.tabla = QTableWidget(max_filas + 2, ncols)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)  # solo lectura
        self.tabla.setSelectionBehavior(QTableWidget.SelectItems)
        self.tabla.setSelectionMode(QTableWidget.ContiguousSelection)
        self.tabla.setWordWrap(False)

        # Ocultar headers nativos (evita números y texto por defecto)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setVisible(False)

        # Ajuste de ancho de columnas: fijas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        for c in range(ncols):
            self.tabla.setColumnWidth(c, 100)  # ancho en píxeles

        # Alto para filas de encabezado
        self.tabla.setRowHeight(0, 28)
        self.tabla.setRowHeight(1, 24)

        # Fuente en negrita para encabezados
        bold_font = self.font()
        bold_font.setBold(True)

        # --- Fila 0: encabezado del método ---
        for i, (clave, etiqueta) in enumerate(modelos_activos):
            c0 = i * 2
            top = QTableWidgetItem(etiqueta)
            top.setTextAlignment(Qt.AlignCenter)
            top.setFont(bold_font)
            self.tabla.setItem(0, c0, top)
            self.tabla.setSpan(0, c0, 1, 2)

        # --- Fila 1: subencabezados personalizados ---
        for i, (_clave, _etiqueta) in enumerate(modelos_activos):
            h1 = QTableWidgetItem(subheaders[0])
            h2 = QTableWidgetItem(subheaders[1])
            for h in (h1, h2):
                h.setTextAlignment(Qt.AlignCenter)
                h.setFont(bold_font)
            self.tabla.setItem(1, i*2,   h1)
            self.tabla.setItem(1, i*2+1, h2)

        # --- Datos ---
        for i, (clave, _etiqueta) in enumerate(modelos_activos):
            x, y = series[clave]
            for r in range(len(x)):
                it_x = QTableWidgetItem(f"{float(x[r]):.6g}")
                it_y = QTableWidgetItem(f"{float(y[r]):.6g}")
                it_x.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                it_y.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                self.tabla.setItem(r+2, i*2,   it_x)
                self.tabla.setItem(r+2, i*2+1, it_y)

        layout.addWidget(self.tabla)

        # Botón copiar todo
        botones = QHBoxLayout()
        self.btn_copiar = QPushButton("Copiar toda la tabla")
        self.btn_copiar.clicked.connect(self.copiar_todo)
        botones.addStretch()
        botones.addWidget(self.btn_copiar)
        layout.addLayout(botones)

        # Ajusta y bloquea el tamaño en función de la tabla
        self._ajustar_y_bloquear_tamano()

    def _ajustar_y_bloquear_tamano(self):
        """
        Calcula el ancho/alto necesario en función de:
        - Ancho de columnas fijas
        - Bordes de la tabla
        - Scrollbars visibles
        - Márgenes/espaciados del layout
        Luego fija el tamaño del diálogo para que no se pueda redimensionar.
        Además, limita a un porcentaje del tamaño de pantalla y activa scroll si hace falta.
        """
        # --- Ancho real de la tabla ---
        ancho_tabla = self.tabla.frameWidth() * 2 + self.tabla.verticalHeader().width()
        for c in range(self.tabla.columnCount()):
            ancho_tabla += self.tabla.columnWidth(c)

        # Considerar si el scrollbar vertical será necesario (puede variar),
        # pero si estuviera visible, sumar su sizeHint.
        if self.tabla.verticalScrollBar().isVisible():
            ancho_tabla += self.tabla.verticalScrollBar().sizeHint().width()

        # Márgenes del layout principal
        l, t, r, b = self.layout().getContentsMargins()
        ancho_total = ancho_tabla + l + r

        # Asegúrate de no quedar más angosto que la fila de botones
        ancho_total = max(ancho_total, self.btn_copiar.sizeHint().width() + l + r)

        # Límites por pantalla (90% del disponible)
        screen = getattr(self, "screen", None)() if hasattr(self, "screen") else None
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        geom = screen.availableGeometry()
        ancho_max = int(geom.width() * 0.9)
        ancho_final = min(ancho_total, ancho_max)

        # Política de scroll horizontal según si capamos o no
        self.tabla.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded if ancho_total > ancho_final else Qt.ScrollBarAlwaysOff
        )

        # --- Altura real de la tabla ---
        alto_tabla = self.tabla.frameWidth() * 2
        for r in range(self.tabla.rowCount()):
            alto_tabla += self.tabla.rowHeight(r)
        # Scrollbar horizontal si existiera
        if self.tabla.horizontalScrollBar().isVisible():
            alto_tabla += self.tabla.horizontalScrollBar().sizeHint().height()

        # Altura de la fila de botones (+ espaciado del layout)
        alto_botones = max(self.btn_copiar.sizeHint().height(), 32)
        alto_total = alto_tabla + alto_botones + t + b + self.layout().spacing()

        # Límite por pantalla (90% del alto disponible)
        alto_max = int(geom.height() * 0.9)
        alto_final = min(alto_total, alto_max)

        # Si capamos por alto, dejar scroll vertical en la tabla
        self.tabla.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded if alto_total > alto_final else Qt.ScrollBarAlwaysOff
        )

        # Fijar tamaño (ya no se puede ni agrandar ni disminuir)
        self.setFixedSize(ancho_final, alto_final)
        self.setSizeGripEnabled(False)

    def copiar_todo(self):
        rows = self.tabla.rowCount()
        cols = self.tabla.columnCount()

        # Construir texto tabulado incluyendo las dos filas de encabezado personalizadas
        contenido = []
        for r in range(rows):
            fila = []
            for c in range(cols):
                item = self.tabla.item(r, c)
                fila.append(item.text() if item else "")
            contenido.append("\t".join(fila))
        QGuiApplication.clipboard().setText("\n".join(contenido))
