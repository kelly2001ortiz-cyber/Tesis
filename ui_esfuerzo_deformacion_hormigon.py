# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'esfuerzo_deformacion_hormigonkfLYpB.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGroupBox,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QWidget)

class Ui_esfuerzo_deformacion_hormigon(object):
    def setupUi(self, esfuerzo_deformacion_hormigon):
        if not esfuerzo_deformacion_hormigon.objectName():
            esfuerzo_deformacion_hormigon.setObjectName(u"esfuerzo_deformacion_hormigon")
        esfuerzo_deformacion_hormigon.resize(993, 486)
        self.groupBox_16 = QGroupBox(esfuerzo_deformacion_hormigon)
        self.groupBox_16.setObjectName(u"groupBox_16")
        self.groupBox_16.setEnabled(True)
        self.groupBox_16.setGeometry(QRect(10, 150, 351, 121))
        self.checkBox_4 = QCheckBox(self.groupBox_16)
        self.checkBox_4.setObjectName(u"checkBox_4")
        self.checkBox_4.setGeometry(QRect(30, 90, 141, 20))
        self.checkBox_3 = QCheckBox(self.groupBox_16)
        self.checkBox_3.setObjectName(u"checkBox_3")
        self.checkBox_3.setGeometry(QRect(30, 60, 141, 20))
        self.checkBox_2 = QCheckBox(self.groupBox_16)
        self.checkBox_2.setObjectName(u"checkBox_2")
        self.checkBox_2.setGeometry(QRect(30, 30, 76, 20))
        self.groupBox_2 = QGroupBox(esfuerzo_deformacion_hormigon)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(10, 10, 351, 131))
        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(30, 30, 121, 16))
        self.label_7 = QLabel(self.groupBox_2)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(30, 60, 151, 16))
        self.label_8 = QLabel(self.groupBox_2)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(30, 90, 151, 16))
        self.nombre_hormigon = QLineEdit(self.groupBox_2)
        self.nombre_hormigon.setObjectName(u"nombre_hormigon")
        self.nombre_hormigon.setGeometry(QRect(190, 30, 81, 22))
        self.nombre_hormigon.setReadOnly(True)
        self.esfuerzo_fc = QLineEdit(self.groupBox_2)
        self.esfuerzo_fc.setObjectName(u"esfuerzo_fc")
        self.esfuerzo_fc.setGeometry(QRect(190, 60, 81, 22))
        self.esfuerzo_fc.setReadOnly(True)
        self.label_9 = QLabel(self.groupBox_2)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(280, 60, 51, 16))
        self.label_10 = QLabel(self.groupBox_2)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setGeometry(QRect(280, 90, 51, 16))
        self.modulo_Ec = QLineEdit(self.groupBox_2)
        self.modulo_Ec.setObjectName(u"modulo_Ec")
        self.modulo_Ec.setGeometry(QRect(190, 90, 81, 22))
        self.modulo_Ec.setReadOnly(True)
        self.cuadricula_ed_hormigon = QWidget(esfuerzo_deformacion_hormigon)
        self.cuadricula_ed_hormigon.setObjectName(u"cuadricula_ed_hormigon")
        self.cuadricula_ed_hormigon.setGeometry(QRect(380, 20, 600, 450))
        self.btn_mostrar_tabla_ed_h = QPushButton(esfuerzo_deformacion_hormigon)
        self.btn_mostrar_tabla_ed_h.setObjectName(u"btn_mostrar_tabla_ed_h")
        self.btn_mostrar_tabla_ed_h.setGeometry(QRect(10, 280, 101, 24))

        self.retranslateUi(esfuerzo_deformacion_hormigon)

        QMetaObject.connectSlotsByName(esfuerzo_deformacion_hormigon)
    # setupUi

    def retranslateUi(self, esfuerzo_deformacion_hormigon):
        esfuerzo_deformacion_hormigon.setWindowTitle(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Diagrama Esfuerzo-Deformaci\u00f3n", None))
        self.groupBox_16.setTitle(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Modelos Constitutivos", None))
        self.checkBox_4.setText(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Mander Confinado", None))
        self.checkBox_3.setText(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Mander No Confinado", None))
        self.checkBox_2.setText(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Hognestad", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Informaci\u00f3n General", None))
        self.label_2.setText(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Nombre del material", None))
        self.label_7.setText(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Esfuerzo de compresi\u00f3n, f'c", None))
        self.label_8.setText(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Modulo de Elasticidad, Ec", None))
        self.nombre_hormigon.setText("")
        self.esfuerzo_fc.setText("")
        self.label_9.setText(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"kg/cm\u00b2", None))
        self.label_10.setText(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"kg/cm\u00b2", None))
        self.modulo_Ec.setText("")
        self.btn_mostrar_tabla_ed_h.setText(QCoreApplication.translate("esfuerzo_deformacion_hormigon", u"Mostrar Tabla", None))
    # retranslateUi

