# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'definir_fibrasZhfJFE.ui'
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

class Ui_definir_fibras(object):
    def setupUi(self, definir_fibras):
        if not definir_fibras.objectName():
            definir_fibras.setObjectName(u"definir_fibras")
        definir_fibras.resize(362, 156)
        self.groupBox = QGroupBox(definir_fibras)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 341, 101))
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(30, 30, 191, 16))
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(30, 60, 191, 16))
        self.fibras_x = QLineEdit(self.groupBox)
        self.fibras_x.setObjectName(u"fibras_x")
        self.fibras_x.setGeometry(QRect(230, 30, 81, 22))
        self.fibras_y = QLineEdit(self.groupBox)
        self.fibras_y.setObjectName(u"fibras_y")
        self.fibras_y.setGeometry(QRect(230, 60, 81, 22))
        self.btn_ok_fibras = QPushButton(definir_fibras)
        self.btn_ok_fibras.setObjectName(u"btn_ok_fibras")
        self.btn_ok_fibras.setGeometry(QRect(100, 120, 75, 24))
        self.btn_cancelar_fibras = QPushButton(definir_fibras)
        self.btn_cancelar_fibras.setObjectName(u"btn_cancelar_fibras")
        self.btn_cancelar_fibras.setGeometry(QRect(180, 120, 75, 24))

        self.retranslateUi(definir_fibras)

        QMetaObject.connectSlotsByName(definir_fibras)
    # setupUi

    def retranslateUi(self, definir_fibras):
        definir_fibras.setWindowTitle(QCoreApplication.translate("definir_fibras", u"Definir Capas de Fibras", None))
        self.groupBox.setTitle(QCoreApplication.translate("definir_fibras", u"Distribuci\u00f3n de Fibras", None))
        self.label.setText(QCoreApplication.translate("definir_fibras", u"N\u00famero de Fibras en direcci\u00f3n X", None))
        self.label_2.setText(QCoreApplication.translate("definir_fibras", u"N\u00famero de Fibras en direcci\u00f3n Y", None))
        self.btn_ok_fibras.setText(QCoreApplication.translate("definir_fibras", u"OK", None))
        self.btn_cancelar_fibras.setText(QCoreApplication.translate("definir_fibras", u"Cancelar", None))
    # retranslateUi

