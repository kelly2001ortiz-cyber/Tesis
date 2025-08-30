# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'definir_seccion.ui'
##
## Created by: Qt User Interface Compiler version 6.x
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

class Ui_definir_seccion(object):
    def setupUi(self, definir_seccion):
        if not definir_seccion.objectName():
            definir_seccion.setObjectName("definir_seccion")
        definir_seccion.resize(258, 310)
        definir_seccion.setWindowTitle("")

        self.groupBox = QGroupBox(definir_seccion)
        self.groupBox.setObjectName("groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 231, 101))

        self.label = QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.label.setGeometry(QRect(30, 30, 101, 16))

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.label_3.setGeometry(QRect(30, 60, 101, 16))

        self.nombre_definir_seccion = QLineEdit(self.groupBox)
        self.nombre_definir_seccion.setObjectName("nombre_definir_seccion")
        self.nombre_definir_seccion.setGeometry(QRect(120, 30, 81, 22))

        self.material_definir_seccion = QComboBox(self.groupBox)
        self.material_definir_seccion.setObjectName("material_definir_seccion")
        self.material_definir_seccion.setGeometry(QRect(120, 60, 81, 22))

        self.groupBox_4 = QGroupBox(definir_seccion)
        self.groupBox_4.setObjectName("groupBox_4")
        self.groupBox_4.setGeometry(QRect(10, 120, 231, 91))

        self.label_31 = QLabel(self.groupBox_4)
        self.label_31.setObjectName("label_31")
        self.label_31.setGeometry(QRect(280, 90, 31, 16))

        self.radiobtn_viga_definir_seccion = QRadioButton(self.groupBox_4)
        self.radiobtn_viga_definir_seccion.setObjectName("radiobtn_viga_definir_seccion")
        self.radiobtn_viga_definir_seccion.setGeometry(QRect(40, 30, 89, 20))

        self.radiobtn_columna_definir_seccion = QRadioButton(self.groupBox_4)
        self.radiobtn_columna_definir_seccion.setObjectName("radiobtn_columna_definir_seccion")
        self.radiobtn_columna_definir_seccion.setGeometry(QRect(40, 60, 89, 20))

        self.btn_ok_definir_seccion = QPushButton(definir_seccion)
        self.btn_ok_definir_seccion.setObjectName("btn_ok_definir_seccion")
        self.btn_ok_definir_seccion.setGeometry(QRect(30, 260, 75, 24))

        self.btn_cancelar_definir_seccion = QPushButton(definir_seccion)
        self.btn_cancelar_definir_seccion.setObjectName("btn_cancelar_definir_seccion")
        self.btn_cancelar_definir_seccion.setGeometry(QRect(130, 260, 75, 24))

        self.btn_disenar_definir_seccion = QPushButton(definir_seccion)
        self.btn_disenar_definir_seccion.setObjectName("btn_disenar_definir_seccion")
        self.btn_disenar_definir_seccion.setGeometry(QRect(70, 220, 101, 24))

        self.retranslateUi(definir_seccion)
        QMetaObject.connectSlotsByName(definir_seccion)

    def retranslateUi(self, definir_seccion):
        definir_seccion.setWindowTitle(QCoreApplication.translate("definir_seccion", u"Definir Sección", None))
        self.groupBox.setTitle(QCoreApplication.translate("definir_seccion", u"Información General", None))
        self.label.setText(QCoreApplication.translate("definir_seccion", u"Nombre", None))
        self.label_3.setText(QCoreApplication.translate("definir_seccion", u"Material", None))
        self.nombre_definir_seccion.setText(QCoreApplication.translate("definir_seccion", u"V40x60", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("definir_seccion", u"Tipo de Sección", None))
        self.label_31.setText(QCoreApplication.translate("definir_seccion", u"kg", None))
        self.radiobtn_viga_definir_seccion.setText(QCoreApplication.translate("definir_seccion", u"Viga", None))
        self.radiobtn_columna_definir_seccion.setText(QCoreApplication.translate("definir_seccion", u"Columna", None))
        self.btn_ok_definir_seccion.setText(QCoreApplication.translate("definir_seccion", u"OK", None))
        self.btn_cancelar_definir_seccion.setText(QCoreApplication.translate("definir_seccion", u"Cancelar", None))
        self.btn_disenar_definir_seccion.setText(QCoreApplication.translate("definir_seccion", u"Diseñar Sección", None))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = Ui_definir_seccion()
    ventana.show()
    sys.exit(app.exec())