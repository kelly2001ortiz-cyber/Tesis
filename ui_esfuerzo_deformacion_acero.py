# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'esfuerzo_deformacion_aceroyfSsqj.ui'
##
## Created by: Qt User Interface Compiler version 6.4.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QDialog,
    QFrame, QGroupBox, QHeaderView, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QTableWidget,
    QTableWidgetItem, QWidget)

class Ui_esfuerzo_deformacion_acero(object):
    def setupUi(self, esfuerzo_deformacion_acero):
        if not esfuerzo_deformacion_acero.objectName():
            esfuerzo_deformacion_acero.setObjectName(u"esfuerzo_deformacion_acero")
        esfuerzo_deformacion_acero.resize(982, 482)
        self.groupBox_15 = QGroupBox(esfuerzo_deformacion_acero)
        self.groupBox_15.setObjectName(u"groupBox_15")
        self.groupBox_15.setGeometry(QRect(10, 220, 341, 161))
        self.tablePuntosControl = QTableWidget(self.groupBox_15)
        if (self.tablePuntosControl.columnCount() < 2):
            self.tablePuntosControl.setColumnCount(2)
        brush = QBrush(QColor(0, 0, 0, 255))
        brush.setStyle(Qt.SolidPattern)
        __qtablewidgetitem = QTableWidgetItem()
        __qtablewidgetitem.setForeground(brush);
        self.tablePuntosControl.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tablePuntosControl.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        if (self.tablePuntosControl.rowCount() < 3):
            self.tablePuntosControl.setRowCount(3)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tablePuntosControl.setVerticalHeaderItem(0, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tablePuntosControl.setVerticalHeaderItem(1, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tablePuntosControl.setVerticalHeaderItem(2, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        __qtablewidgetitem5.setTextAlignment(Qt.AlignCenter);
        self.tablePuntosControl.setItem(0, 0, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        __qtablewidgetitem6.setTextAlignment(Qt.AlignCenter);
        self.tablePuntosControl.setItem(1, 0, __qtablewidgetitem6)
        self.tablePuntosControl.setObjectName(u"tablePuntosControl")
        self.tablePuntosControl.setGeometry(QRect(10, 30, 297, 113))
        self.tablePuntosControl.setMinimumSize(QSize(297, 113))
        self.tablePuntosControl.setMaximumSize(QSize(297, 113))
        self.tablePuntosControl.setFocusPolicy(Qt.NoFocus)
        self.tablePuntosControl.setStyleSheet(u"QTableView::item, QTableWidget::item {\n"
"    padding: 0px;\n"
"    margin: 0px;\n"
"    border: none;\n"
"    outline: none;\n"
"}\n"
"QTableView::item:pressed, QTableWidget::item:pressed,\n"
"QTableView::item:hover, QTableWidget::item:hover {\n"
"    margin: 0px;\n"
"    padding: 0px;\n"
"    border: none;\n"
"    background: transparent;\n"
"}\n"
"")
        self.tablePuntosControl.setFrameShape(QFrame.NoFrame)
        self.tablePuntosControl.setFrameShadow(QFrame.Plain)
        self.tablePuntosControl.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tablePuntosControl.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tablePuntosControl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablePuntosControl.setSelectionMode(QAbstractItemView.NoSelection)
        self.tablePuntosControl.setShowGrid(True)
        self.tablePuntosControl.setGridStyle(Qt.SolidLine)
        self.tablePuntosControl.setSortingEnabled(False)
        self.tablePuntosControl.setWordWrap(True)
        self.tablePuntosControl.setCornerButtonEnabled(True)
        self.tablePuntosControl.horizontalHeader().setCascadingSectionResizes(False)
        self.tablePuntosControl.horizontalHeader().setDefaultSectionSize(95)
        self.tablePuntosControl.horizontalHeader().setProperty("showSortIndicator", False)
        self.tablePuntosControl.horizontalHeader().setStretchLastSection(False)
        self.tablePuntosControl.verticalHeader().setCascadingSectionResizes(False)
        self.tablePuntosControl.verticalHeader().setProperty("showSortIndicator", False)
        self.tablePuntosControl.verticalHeader().setStretchLastSection(False)
        self.groupBox = QGroupBox(esfuerzo_deformacion_acero)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 341, 131))
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(30, 30, 121, 16))
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(30, 60, 151, 16))
        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(30, 90, 151, 16))
        self.nombre_acero = QLineEdit(self.groupBox)
        self.nombre_acero.setObjectName(u"nombre_acero")
        self.nombre_acero.setGeometry(QRect(180, 30, 81, 22))
        self.nombre_acero.setReadOnly(True)
        self.esfuerzo_fy = QLineEdit(self.groupBox)
        self.esfuerzo_fy.setObjectName(u"esfuerzo_fy")
        self.esfuerzo_fy.setGeometry(QRect(180, 60, 81, 22))
        self.esfuerzo_fy.setReadOnly(True)
        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(270, 60, 51, 16))
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(270, 90, 51, 16))
        self.modulo_Es = QLineEdit(self.groupBox)
        self.modulo_Es.setObjectName(u"modulo_Es")
        self.modulo_Es.setGeometry(QRect(180, 90, 81, 22))
        self.modulo_Es.setReadOnly(True)
        self.groupBox_16 = QGroupBox(esfuerzo_deformacion_acero)
        self.groupBox_16.setObjectName(u"groupBox_16")
        self.groupBox_16.setEnabled(True)
        self.groupBox_16.setGeometry(QRect(10, 150, 341, 61))
        self.ThompsonPark_ed = QCheckBox(self.groupBox_16)
        self.ThompsonPark_ed.setObjectName(u"ThompsonPark_ed")
        self.ThompsonPark_ed.setEnabled(False)
        self.ThompsonPark_ed.setGeometry(QRect(30, 30, 121, 20))
        self.ThompsonPark_ed.setChecked(True)
        self.cuadricula_ed_acero = QWidget(esfuerzo_deformacion_acero)
        self.cuadricula_ed_acero.setObjectName(u"cuadricula_ed_acero")
        self.cuadricula_ed_acero.setGeometry(QRect(370, 20, 600, 450))
        self.btn_mostrar_tabla_ed_a = QPushButton(esfuerzo_deformacion_acero)
        self.btn_mostrar_tabla_ed_a.setObjectName(u"btn_mostrar_tabla_ed_a")
        self.btn_mostrar_tabla_ed_a.setGeometry(QRect(10, 390, 101, 24))

        self.retranslateUi(esfuerzo_deformacion_acero)

        QMetaObject.connectSlotsByName(esfuerzo_deformacion_acero)
    # setupUi

    def retranslateUi(self, esfuerzo_deformacion_acero):
        esfuerzo_deformacion_acero.setWindowTitle(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Diagrama Esfuerzo-Deformaci\u00f3n", None))
        self.groupBox_15.setTitle(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Puntos Caracter\u00edsticos", None))
        ___qtablewidgetitem = self.tablePuntosControl.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"\u03b5 (cm/cm)", None));
        ___qtablewidgetitem1 = self.tablePuntosControl.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"\u03c3 (kg/cm\u00b2)", None));
        ___qtablewidgetitem2 = self.tablePuntosControl.verticalHeaderItem(0)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Punto de Fluencia", None));
        ___qtablewidgetitem3 = self.tablePuntosControl.verticalHeaderItem(1)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Punto Fin Fluencia", None));
        ___qtablewidgetitem4 = self.tablePuntosControl.verticalHeaderItem(2)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Punto \u00daltimo", None));

        __sortingEnabled = self.tablePuntosControl.isSortingEnabled()
        self.tablePuntosControl.setSortingEnabled(False)
        self.tablePuntosControl.setSortingEnabled(__sortingEnabled)

        self.groupBox.setTitle(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Informaci\u00f3n General", None))
        self.label.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Nombre del material", None))
        self.label_3.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Esfuerzo de fluencia, fy", None))
        self.label_4.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Modulo de Elasticidad, Es", None))
        self.nombre_acero.setText("")
        self.esfuerzo_fy.setText("")
        self.label_5.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"kg/cm\u00b2", None))
        self.label_6.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"kg/cm\u00b2", None))
        self.modulo_Es.setText("")
        self.groupBox_16.setTitle(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Modelo Constitutivo", None))
        self.ThompsonPark_ed.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Thompson - Park", None))
        self.btn_mostrar_tabla_ed_a.setText(QCoreApplication.translate("esfuerzo_deformacion_acero", u"Mostrar Tabla", None))
    # retranslateUi

