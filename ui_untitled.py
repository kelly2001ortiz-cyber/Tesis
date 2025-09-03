# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'untitledzJcwDx.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QFrame,
    QHeaderView, QSizePolicy, QTableWidget, QTableWidgetItem,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 300)
        self.tablePuntosControl = QTableWidget(Dialog)
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
        self.tablePuntosControl.setGeometry(QRect(60, 50, 297, 113))
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

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        ___qtablewidgetitem = self.tablePuntosControl.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Dialog", u"\u03b5 (cm/cm)", None));
        ___qtablewidgetitem1 = self.tablePuntosControl.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Dialog", u"\u03c3 (kg/cm\u00b2)", None));
        ___qtablewidgetitem2 = self.tablePuntosControl.verticalHeaderItem(0)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("Dialog", u"Punto de Fluencia", None));
        ___qtablewidgetitem3 = self.tablePuntosControl.verticalHeaderItem(1)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("Dialog", u"Punto Fin Fluencia", None));
        ___qtablewidgetitem4 = self.tablePuntosControl.verticalHeaderItem(2)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("Dialog", u"Punto \u00daltimo", None));

        __sortingEnabled = self.tablePuntosControl.isSortingEnabled()
        self.tablePuntosControl.setSortingEnabled(False)
        self.tablePuntosControl.setSortingEnabled(__sortingEnabled)

    # retranslateUi

