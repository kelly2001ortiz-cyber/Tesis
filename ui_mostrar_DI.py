# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mostrar_DIhzLlJV.ui'
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
    QFrame, QGroupBox, QHeaderView, QPushButton,
    QSizePolicy, QTableWidget, QTableWidgetItem, QWidget)

class Ui_mostrar_DI(object):
    def setupUi(self, mostrar_DI):
        if not mostrar_DI.objectName():
            mostrar_DI.setObjectName(u"mostrar_DI")
        mostrar_DI.resize(995, 627)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(mostrar_DI.sizePolicy().hasHeightForWidth())
        mostrar_DI.setSizePolicy(sizePolicy)
        self.groupBox_15 = QGroupBox(mostrar_DI)
        self.groupBox_15.setObjectName(u"groupBox_15")
        self.groupBox_15.setGeometry(QRect(10, 10, 371, 201))
        self.groupBox_15.setMinimumSize(QSize(371, 201))
        self.groupBox_15.setMaximumSize(QSize(371, 201))
        self.tablePuntosControl = QTableWidget(self.groupBox_15)
        if (self.tablePuntosControl.columnCount() < 2):
            self.tablePuntosControl.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
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
        self.tablePuntosControl.setObjectName(u"tablePuntosControl")
        self.tablePuntosControl.setGeometry(QRect(10, 30, 340, 113))
        self.tablePuntosControl.setMinimumSize(QSize(340, 113))
        self.tablePuntosControl.setMaximumSize(QSize(340, 113))
        self.tablePuntosControl.setFocusPolicy(Qt.NoFocus)
        self.tablePuntosControl.setLayoutDirection(Qt.LeftToRight)
        self.tablePuntosControl.setFrameShape(QFrame.NoFrame)
        self.tablePuntosControl.setFrameShadow(QFrame.Plain)
        self.tablePuntosControl.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tablePuntosControl.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tablePuntosControl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablePuntosControl.setSelectionMode(QAbstractItemView.NoSelection)
        self.tablePuntosControl.setTextElideMode(Qt.ElideMiddle)
        self.tablePuntosControl.setShowGrid(True)
        self.tablePuntosControl.setGridStyle(Qt.SolidLine)
        self.tablePuntosControl.setSortingEnabled(False)
        self.tablePuntosControl.setWordWrap(True)
        self.tablePuntosControl.setCornerButtonEnabled(True)
        self.tablePuntosControl.horizontalHeader().setCascadingSectionResizes(False)
        self.tablePuntosControl.horizontalHeader().setDefaultSectionSize(110)
        self.tablePuntosControl.horizontalHeader().setProperty("showSortIndicator", False)
        self.tablePuntosControl.horizontalHeader().setStretchLastSection(False)
        self.tablePuntosControl.verticalHeader().setCascadingSectionResizes(False)
        self.tablePuntosControl.verticalHeader().setProperty("showSortIndicator", False)
        self.tablePuntosControl.verticalHeader().setStretchLastSection(False)
        self.btn_mostrar_tablaDI = QPushButton(self.groupBox_15)
        self.btn_mostrar_tablaDI.setObjectName(u"btn_mostrar_tablaDI")
        self.btn_mostrar_tablaDI.setGeometry(QRect(10, 160, 91, 24))
        self.checkBox_conphi = QCheckBox(self.groupBox_15)
        self.checkBox_conphi.setObjectName(u"checkBox_conphi")
        self.checkBox_conphi.setGeometry(QRect(120, 160, 76, 20))
        self.checkBox_sinphi = QCheckBox(self.groupBox_15)
        self.checkBox_sinphi.setObjectName(u"checkBox_sinphi")
        self.checkBox_sinphi.setGeometry(QRect(200, 160, 76, 20))
        self.groupBox_16 = QGroupBox(mostrar_DI)
        self.groupBox_16.setObjectName(u"groupBox_16")
        self.groupBox_16.setGeometry(QRect(10, 220, 371, 391))
        self.groupBox_16.setMinimumSize(QSize(371, 391))
        self.groupBox_16.setMaximumSize(QSize(371, 391))
        self.cuadricula_seccionDI = QWidget(self.groupBox_16)
        self.cuadricula_seccionDI.setObjectName(u"cuadricula_seccionDI")
        self.cuadricula_seccionDI.setGeometry(QRect(10, 30, 348, 348))
        self.cuadricula_DI = QWidget(mostrar_DI)
        self.cuadricula_DI.setObjectName(u"cuadricula_DI")
        self.cuadricula_DI.setGeometry(QRect(410, 20, 571, 591))
        self.cuadricula_DI.setMinimumSize(QSize(571, 591))
        self.cuadricula_DI.setMaximumSize(QSize(571, 591))

        self.retranslateUi(mostrar_DI)

        QMetaObject.connectSlotsByName(mostrar_DI)
    # setupUi

    def retranslateUi(self, mostrar_DI):
        mostrar_DI.setWindowTitle(QCoreApplication.translate("mostrar_DI", u"Diagrama de Interacci\u00f3n", None))
        self.groupBox_15.setTitle(QCoreApplication.translate("mostrar_DI", u"Puntos de Control", None))
        ___qtablewidgetitem = self.tablePuntosControl.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("mostrar_DI", u"\u03c6Pn (T)", None));
        ___qtablewidgetitem1 = self.tablePuntosControl.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("mostrar_DI", u"\u03c6Mn (Tm)", None));
        ___qtablewidgetitem2 = self.tablePuntosControl.verticalHeaderItem(0)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("mostrar_DI", u"M\u00e1xima Tensi\u00f3n", None));
        ___qtablewidgetitem3 = self.tablePuntosControl.verticalHeaderItem(1)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("mostrar_DI", u"Punto Balanceado", None));
        ___qtablewidgetitem4 = self.tablePuntosControl.verticalHeaderItem(2)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("mostrar_DI", u"M\u00e1xima Compresi\u00f3n", None));
        self.btn_mostrar_tablaDI.setText(QCoreApplication.translate("mostrar_DI", u"Mostrar Tabla", None))
        self.checkBox_conphi.setText(QCoreApplication.translate("mostrar_DI", u"Con phi", None))
        self.checkBox_sinphi.setText(QCoreApplication.translate("mostrar_DI", u"Sin phi", None))
        self.groupBox_16.setTitle(QCoreApplication.translate("mostrar_DI", u"Secci\u00f3n", None))
    # retranslateUi

