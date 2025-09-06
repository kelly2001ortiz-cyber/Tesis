# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mostrar_MC - copiasgtZVc.ui'
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
    QPushButton, QSizePolicy, QWidget)

class Ui_mostrar_MC(object):
    def setupUi(self, mostrar_MC):
        if not mostrar_MC.objectName():
            mostrar_MC.setObjectName(u"mostrar_MC")
        mostrar_MC.resize(984, 625)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(mostrar_MC.sizePolicy().hasHeightForWidth())
        mostrar_MC.setSizePolicy(sizePolicy)
        mostrar_MC.setMinimumSize(QSize(984, 625))
        mostrar_MC.setMaximumSize(QSize(984, 625))
        self.groupBox_16 = QGroupBox(mostrar_MC)
        self.groupBox_16.setObjectName(u"groupBox_16")
        self.groupBox_16.setEnabled(True)
        self.groupBox_16.setGeometry(QRect(10, 10, 281, 91))
        self.checkBox_2 = QCheckBox(self.groupBox_16)
        self.checkBox_2.setObjectName(u"checkBox_2")
        self.checkBox_2.setGeometry(QRect(30, 30, 76, 20))
        self.checkBox_3 = QCheckBox(self.groupBox_16)
        self.checkBox_3.setObjectName(u"checkBox_3")
        self.checkBox_3.setGeometry(QRect(30, 60, 91, 20))
        self.cuadricula_MC = QWidget(mostrar_MC)
        self.cuadricula_MC.setObjectName(u"cuadricula_MC")
        self.cuadricula_MC.setGeometry(QRect(310, 20, 661, 591))
        self.btn_mostrar_tablaMC = QPushButton(mostrar_MC)
        self.btn_mostrar_tablaMC.setObjectName(u"btn_mostrar_tablaMC")
        self.btn_mostrar_tablaMC.setGeometry(QRect(10, 110, 91, 24))

        self.retranslateUi(mostrar_MC)

        QMetaObject.connectSlotsByName(mostrar_MC)
    # setupUi

    def retranslateUi(self, mostrar_MC):
        mostrar_MC.setWindowTitle(QCoreApplication.translate("mostrar_MC", u"Diagrama Momento - Curvatura", None))
        self.groupBox_16.setTitle(QCoreApplication.translate("mostrar_MC", u"Modelos Idealizados", None))
        self.checkBox_2.setText(QCoreApplication.translate("mostrar_MC", u"Hognestad", None))
        self.checkBox_3.setText(QCoreApplication.translate("mostrar_MC", u"Mander", None))
        self.btn_mostrar_tablaMC.setText(QCoreApplication.translate("mostrar_MC", u"Mostrar Tabla", None))
    # retranslateUi

