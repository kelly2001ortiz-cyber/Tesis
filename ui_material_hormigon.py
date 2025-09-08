# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'material_hormigonUUHSqu.ui'
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

class Ui_material_hormigon(object):
    def setupUi(self, material_hormigon):
        if not material_hormigon.objectName():
            material_hormigon.setObjectName(u"material_hormigon")
        material_hormigon.resize(391, 365)
        self.groupBox = QGroupBox(material_hormigon)
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
        self.nombre_hormigon = QLineEdit(self.groupBox)
        self.nombre_hormigon.setObjectName(u"nombre_hormigon")
        self.nombre_hormigon.setGeometry(QRect(220, 30, 81, 22))
        self.esfuerzo_fc = QLineEdit(self.groupBox)
        self.esfuerzo_fc.setObjectName(u"esfuerzo_fc")
        self.esfuerzo_fc.setGeometry(QRect(220, 60, 81, 22))
        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(310, 60, 51, 16))
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(310, 90, 51, 16))
        self.modulo_Ec = QLineEdit(self.groupBox)
        self.modulo_Ec.setObjectName(u"modulo_Ec")
        self.modulo_Ec.setGeometry(QRect(220, 90, 81, 22))
        self.groupBox_2 = QGroupBox(material_hormigon)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(10, 150, 371, 171))
        self.label_13 = QLabel(self.groupBox_2)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setGeometry(QRect(30, 30, 201, 16))
        self.label_15 = QLabel(self.groupBox_2)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setGeometry(QRect(30, 60, 181, 16))
        self.def_max_sin_confinar = QLineEdit(self.groupBox_2)
        self.def_max_sin_confinar.setObjectName(u"def_max_sin_confinar")
        self.def_max_sin_confinar.setGeometry(QRect(220, 30, 81, 22))
        self.def_ultima_sin_confinar = QLineEdit(self.groupBox_2)
        self.def_ultima_sin_confinar.setObjectName(u"def_ultima_sin_confinar")
        self.def_ultima_sin_confinar.setGeometry(QRect(220, 60, 81, 22))
        self.def_ultima_confinada = QLineEdit(self.groupBox_2)
        self.def_ultima_confinada.setObjectName(u"def_ultima_confinada")
        self.def_ultima_confinada.setEnabled(False)
        self.def_ultima_confinada.setGeometry(QRect(220, 90, 81, 22))
        self.def_ultima_confinada.setReadOnly(True)
        self.label_19 = QLabel(self.groupBox_2)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setGeometry(QRect(30, 90, 201, 16))
        self.btn_mostrar_diagrama_ed_hormigon = QPushButton(self.groupBox_2)
        self.btn_mostrar_diagrama_ed_hormigon.setObjectName(u"btn_mostrar_diagrama_ed_hormigon")
        self.btn_mostrar_diagrama_ed_hormigon.setGeometry(QRect(70, 130, 225, 24))
        self.btn_cancelar_hormigon = QPushButton(material_hormigon)
        self.btn_cancelar_hormigon.setObjectName(u"btn_cancelar_hormigon")
        self.btn_cancelar_hormigon.setGeometry(QRect(193, 330, 75, 24))
        self.btn_guardar_hormigon = QPushButton(material_hormigon)
        self.btn_guardar_hormigon.setObjectName(u"btn_guardar_hormigon")
        self.btn_guardar_hormigon.setGeometry(QRect(113, 330, 75, 24))

        self.retranslateUi(material_hormigon)

        QMetaObject.connectSlotsByName(material_hormigon)
    # setupUi

    def retranslateUi(self, material_hormigon):
        material_hormigon.setWindowTitle(QCoreApplication.translate("material_hormigon", u"Propiedades del Material", None))
        self.groupBox.setTitle(QCoreApplication.translate("material_hormigon", u"Informaci\u00f3n General", None))
        self.label.setText(QCoreApplication.translate("material_hormigon", u"Nombre del material", None))
        self.label_3.setText(QCoreApplication.translate("material_hormigon", u"Esfuerzo de compresi\u00f3n, f'c", None))
        self.label_4.setText(QCoreApplication.translate("material_hormigon", u"Modulo de Elasticidad, Ec", None))
        self.nombre_hormigon.setText(QCoreApplication.translate("material_hormigon", u"f'c 210", None))
        self.esfuerzo_fc.setText(QCoreApplication.translate("material_hormigon", u"210", None))
        self.label_5.setText(QCoreApplication.translate("material_hormigon", u"kg/cm\u00b2", None))
        self.label_6.setText(QCoreApplication.translate("material_hormigon", u"kg/cm\u00b2", None))
        self.modulo_Ec.setText(QCoreApplication.translate("material_hormigon", u"218819.788", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("material_hormigon", u"Datos para Curva Esfuerzo Deformaci\u00f3n", None))
        self.label_13.setText(QCoreApplication.translate("material_hormigon", u"Def. a compresi\u00f3n sin confinar, \u03b5co ", None))
        self.label_15.setText(QCoreApplication.translate("material_hormigon", u"Def. \u00faltima no confinada", None))
        self.def_max_sin_confinar.setText(QCoreApplication.translate("material_hormigon", u"0.002", None))
        self.def_ultima_sin_confinar.setText(QCoreApplication.translate("material_hormigon", u"0.0038", None))
        self.def_ultima_confinada.setText(QCoreApplication.translate("material_hormigon", u"0.09", None))
        self.label_19.setText(QCoreApplication.translate("material_hormigon", u"Def. \u00faltima confinada, \u03b5cu", None))
        self.btn_mostrar_diagrama_ed_hormigon.setText(QCoreApplication.translate("material_hormigon", u"Mostrar Diagrama Esfuerzo Deformaci\u00f3n", None))
        self.btn_cancelar_hormigon.setText(QCoreApplication.translate("material_hormigon", u"Cancelar", None))
        self.btn_guardar_hormigon.setText(QCoreApplication.translate("material_hormigon", u"Guardar", None))
    # retranslateUi

