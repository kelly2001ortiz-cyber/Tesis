# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'material_aceroRiGKNm.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QWidget)

class Ui_material_acero(object):
    def setupUi(self, material_acero):
        if not material_acero.objectName():
            material_acero.setObjectName(u"material_acero")
        material_acero.resize(392, 396)
        self.groupBox = QGroupBox(material_acero)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 371, 131))
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
        self.nombre_acero.setGeometry(QRect(210, 30, 81, 22))
        self.esfuerzo_fy = QLineEdit(self.groupBox)
        self.esfuerzo_fy.setObjectName(u"esfuerzo_fy")
        self.esfuerzo_fy.setGeometry(QRect(210, 60, 81, 22))
        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(300, 60, 51, 16))
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(300, 90, 51, 16))
        self.modulo_Es = QLineEdit(self.groupBox)
        self.modulo_Es.setObjectName(u"modulo_Es")
        self.modulo_Es.setGeometry(QRect(210, 90, 81, 22))
        self.groupBox_2 = QGroupBox(material_acero)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(10, 150, 371, 201))
        self.label_13 = QLabel(self.groupBox_2)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setGeometry(QRect(30, 30, 181, 16))
        self.label_15 = QLabel(self.groupBox_2)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setGeometry(QRect(30, 60, 181, 16))
        self.label_16 = QLabel(self.groupBox_2)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setGeometry(QRect(30, 90, 181, 16))
        self.esfuerzo_ultimo_acero = QLineEdit(self.groupBox_2)
        self.esfuerzo_ultimo_acero.setObjectName(u"esfuerzo_ultimo_acero")
        self.esfuerzo_ultimo_acero.setGeometry(QRect(210, 30, 81, 22))
        self.def_fluencia_acero = QLineEdit(self.groupBox_2)
        self.def_fluencia_acero.setObjectName(u"def_fluencia_acero")
        self.def_fluencia_acero.setGeometry(QRect(210, 60, 81, 22))
        self.def_inicio_endurecimiento = QLineEdit(self.groupBox_2)
        self.def_inicio_endurecimiento.setObjectName(u"def_inicio_endurecimiento")
        self.def_inicio_endurecimiento.setGeometry(QRect(210, 90, 81, 22))
        self.def_ultima_acero = QLineEdit(self.groupBox_2)
        self.def_ultima_acero.setObjectName(u"def_ultima_acero")
        self.def_ultima_acero.setGeometry(QRect(210, 120, 81, 22))
        self.label_25 = QLabel(self.groupBox_2)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setGeometry(QRect(30, 120, 141, 16))
        self.label_7 = QLabel(self.groupBox_2)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(300, 30, 51, 16))
        self.btn_mostrar_diagrama_ed_acero = QPushButton(self.groupBox_2)
        self.btn_mostrar_diagrama_ed_acero.setObjectName(u"btn_mostrar_diagrama_ed_acero")
        self.btn_mostrar_diagrama_ed_acero.setGeometry(QRect(70, 160, 225, 24))
        self.btn_guardar_acero = QPushButton(material_acero)
        self.btn_guardar_acero.setObjectName(u"btn_guardar_acero")
        self.btn_guardar_acero.setGeometry(QRect(110, 360, 75, 24))
        self.btn_cancelar_acero = QPushButton(material_acero)
        self.btn_cancelar_acero.setObjectName(u"btn_cancelar_acero")
        self.btn_cancelar_acero.setGeometry(QRect(190, 360, 75, 24))

        self.retranslateUi(material_acero)

        QMetaObject.connectSlotsByName(material_acero)
    # setupUi

    def retranslateUi(self, material_acero):
        material_acero.setWindowTitle(QCoreApplication.translate("material_acero", u"Propiedades del Material", None))
        self.groupBox.setTitle(QCoreApplication.translate("material_acero", u"Informaci\u00f3n General", None))
        self.label.setText(QCoreApplication.translate("material_acero", u"Nombre del material", None))
        self.label_3.setText(QCoreApplication.translate("material_acero", u"Esfuerzo de fluencia, fy", None))
        self.label_4.setText(QCoreApplication.translate("material_acero", u"Modulo de Elasticidad, Es", None))
        self.nombre_acero.setText(QCoreApplication.translate("material_acero", u"fy 4200", None))
        self.esfuerzo_fy.setText(QCoreApplication.translate("material_acero", u"4200", None))
        self.label_5.setText(QCoreApplication.translate("material_acero", u"kg/cm\u00b2", None))
        self.label_6.setText(QCoreApplication.translate("material_acero", u"kg/cm\u00b2", None))
        self.modulo_Es.setText(QCoreApplication.translate("material_acero", u"2000000", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("material_acero", u"Datos para Curva Esfuerzo Deformaci\u00f3n", None))
        self.label_13.setText(QCoreApplication.translate("material_acero", u"Esfuerzo \u00faltimo del acero, fsu", None))
        self.label_15.setText(QCoreApplication.translate("material_acero", u"Def. de fluencia del acero, \u03b5y", None))
        self.label_16.setText(QCoreApplication.translate("material_acero", u"Def. inicio endurecimiento, \u03b5sh", None))
        self.esfuerzo_ultimo_acero.setText(QCoreApplication.translate("material_acero", u"7457", None))
        self.def_fluencia_acero.setText(QCoreApplication.translate("material_acero", u"0.0021", None))
        self.def_inicio_endurecimiento.setText(QCoreApplication.translate("material_acero", u"0.0139", None))
        self.def_ultima_acero.setText(QCoreApplication.translate("material_acero", u"0.09", None))
        self.label_25.setText(QCoreApplication.translate("material_acero", u"Def. \u00faltima del acero, \u03b5su", None))
        self.label_7.setText(QCoreApplication.translate("material_acero", u"kg/cm\u00b2", None))
        self.btn_mostrar_diagrama_ed_acero.setText(QCoreApplication.translate("material_acero", u"Mostrar Diagrama Esfuerzo Deformaci\u00f3n", None))
        self.btn_guardar_acero.setText(QCoreApplication.translate("material_acero", u"Guardar", None))
        self.btn_cancelar_acero.setText(QCoreApplication.translate("material_acero", u"Cancelar", None))
    # retranslateUi

