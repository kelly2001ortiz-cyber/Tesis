# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ayudazemzBD.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QHeaderView,
    QSizePolicy, QTreeWidget, QTreeWidgetItem, QWidget)

class Ui_ayuda(object):
    def setupUi(self, ayuda):
        if not ayuda.objectName():
            ayuda.setObjectName(u"ayuda")
        ayuda.resize(292, 252)
        self.groupBox = QGroupBox(ayuda)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 271, 231))
        self.treeWidget = QTreeWidget(self.groupBox)
        icon = QIcon()
        icon.addFile(u"New folder/ayuda.png", QSize(), QIcon.Normal, QIcon.On)
        icon1 = QIcon()
        icon1.addFile(u"New folder/items.png", QSize(), QIcon.Normal, QIcon.On)
        __qtreewidgetitem = QTreeWidgetItem(self.treeWidget)
        __qtreewidgetitem.setIcon(0, icon);
        __qtreewidgetitem1 = QTreeWidgetItem(__qtreewidgetitem)
        __qtreewidgetitem1.setIcon(0, icon1);
        __qtreewidgetitem2 = QTreeWidgetItem(__qtreewidgetitem)
        __qtreewidgetitem2.setIcon(0, icon1);
        __qtreewidgetitem3 = QTreeWidgetItem(__qtreewidgetitem)
        __qtreewidgetitem3.setIcon(0, icon1);
        __qtreewidgetitem4 = QTreeWidgetItem(__qtreewidgetitem)
        __qtreewidgetitem4.setIcon(0, icon1);
        __qtreewidgetitem5 = QTreeWidgetItem(self.treeWidget)
        __qtreewidgetitem5.setIcon(0, icon);
        __qtreewidgetitem6 = QTreeWidgetItem(__qtreewidgetitem5)
        __qtreewidgetitem6.setIcon(0, icon1);
        __qtreewidgetitem7 = QTreeWidgetItem(__qtreewidgetitem5)
        __qtreewidgetitem7.setIcon(0, icon);
        __qtreewidgetitem8 = QTreeWidgetItem(__qtreewidgetitem7)
        __qtreewidgetitem8.setIcon(0, icon1);
        __qtreewidgetitem9 = QTreeWidgetItem(__qtreewidgetitem7)
        __qtreewidgetitem9.setIcon(0, icon1);
        __qtreewidgetitem10 = QTreeWidgetItem(__qtreewidgetitem7)
        __qtreewidgetitem10.setIcon(0, icon1);
        __qtreewidgetitem11 = QTreeWidgetItem(__qtreewidgetitem7)
        __qtreewidgetitem11.setIcon(0, icon1);
        __qtreewidgetitem12 = QTreeWidgetItem(__qtreewidgetitem7)
        __qtreewidgetitem12.setIcon(0, icon1);
        __qtreewidgetitem13 = QTreeWidgetItem(self.treeWidget)
        __qtreewidgetitem13.setIcon(0, icon);
        __qtreewidgetitem14 = QTreeWidgetItem(__qtreewidgetitem13)
        __qtreewidgetitem14.setIcon(0, icon1);
        __qtreewidgetitem15 = QTreeWidgetItem(__qtreewidgetitem13)
        __qtreewidgetitem15.setIcon(0, icon1);
        __qtreewidgetitem16 = QTreeWidgetItem(__qtreewidgetitem13)
        __qtreewidgetitem16.setIcon(0, icon1);
        __qtreewidgetitem17 = QTreeWidgetItem(__qtreewidgetitem13)
        __qtreewidgetitem17.setIcon(0, icon1);
        self.treeWidget.setObjectName(u"treeWidget")
        self.treeWidget.setGeometry(QRect(10, 10, 251, 211))

        self.retranslateUi(ayuda)

        QMetaObject.connectSlotsByName(ayuda)
    # setupUi

    def retranslateUi(self, ayuda):
        ayuda.setWindowTitle(QCoreApplication.translate("ayuda", u"Documentaci\u00f3n", None))
        self.groupBox.setTitle("")
        ___qtreewidgetitem = self.treeWidget.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("ayuda", u"Contenido", None));

        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        ___qtreewidgetitem1 = self.treeWidget.topLevelItem(0)
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("ayuda", u"Ejemplos", None));
        ___qtreewidgetitem2 = ___qtreewidgetitem1.child(0)
        ___qtreewidgetitem2.setText(0, QCoreApplication.translate("ayuda", u"Ejemplo A", None));
        ___qtreewidgetitem3 = ___qtreewidgetitem1.child(1)
        ___qtreewidgetitem3.setText(0, QCoreApplication.translate("ayuda", u"Ejemplo B", None));
        ___qtreewidgetitem4 = ___qtreewidgetitem1.child(2)
        ___qtreewidgetitem4.setText(0, QCoreApplication.translate("ayuda", u"Ejemplo C", None));
        ___qtreewidgetitem5 = ___qtreewidgetitem1.child(3)
        ___qtreewidgetitem5.setText(0, QCoreApplication.translate("ayuda", u"Ejemplo D", None));
        ___qtreewidgetitem6 = self.treeWidget.topLevelItem(1)
        ___qtreewidgetitem6.setText(0, QCoreApplication.translate("ayuda", u"Manual", None));
        ___qtreewidgetitem7 = ___qtreewidgetitem6.child(0)
        ___qtreewidgetitem7.setText(0, QCoreApplication.translate("ayuda", u"Introducci\u00f3n", None));
        ___qtreewidgetitem8 = ___qtreewidgetitem6.child(1)
        ___qtreewidgetitem8.setText(0, QCoreApplication.translate("ayuda", u"Men\u00fa", None));
        ___qtreewidgetitem9 = ___qtreewidgetitem8.child(0)
        ___qtreewidgetitem9.setText(0, QCoreApplication.translate("ayuda", u"Archivo", None));
        ___qtreewidgetitem10 = ___qtreewidgetitem8.child(1)
        ___qtreewidgetitem10.setText(0, QCoreApplication.translate("ayuda", u"Definir", None));
        ___qtreewidgetitem11 = ___qtreewidgetitem8.child(2)
        ___qtreewidgetitem11.setText(0, QCoreApplication.translate("ayuda", u"Mostrar", None));
        ___qtreewidgetitem12 = ___qtreewidgetitem8.child(3)
        ___qtreewidgetitem12.setText(0, QCoreApplication.translate("ayuda", u"Reporte", None));
        ___qtreewidgetitem13 = ___qtreewidgetitem8.child(4)
        ___qtreewidgetitem13.setText(0, QCoreApplication.translate("ayuda", u"Ayuda", None));
        ___qtreewidgetitem14 = self.treeWidget.topLevelItem(2)
        ___qtreewidgetitem14.setText(0, QCoreApplication.translate("ayuda", u"Notas T\u00e9cnicas", None));
        ___qtreewidgetitem15 = ___qtreewidgetitem14.child(0)
        ___qtreewidgetitem15.setText(0, QCoreApplication.translate("ayuda", u"Modelo de Mander", None));
        ___qtreewidgetitem16 = ___qtreewidgetitem14.child(1)
        ___qtreewidgetitem16.setText(0, QCoreApplication.translate("ayuda", u"Modelo de Hognestad", None));
        ___qtreewidgetitem17 = ___qtreewidgetitem14.child(2)
        ___qtreewidgetitem17.setText(0, QCoreApplication.translate("ayuda", u"Modelo de Thompson y Park", None));
        ___qtreewidgetitem18 = ___qtreewidgetitem14.child(3)
        ___qtreewidgetitem18.setText(0, QCoreApplication.translate("ayuda", u"Modelo ASCE 41", None));
        self.treeWidget.setSortingEnabled(__sortingEnabled)

    # retranslateUi

