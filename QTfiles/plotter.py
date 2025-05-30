# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plotter.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 500)
        MainWindow.setStyleSheet("background-color: rgb(136, 138, 133);")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setAutoFillBackground(False)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setStyleSheet("background-color: rgb(238, 238, 236);\n"
"selection-color: rgb(85, 87, 83);")
        self.comboBox.setObjectName("comboBox")
        self.verticalLayout.addWidget(self.comboBox)
        self.customGraphWidget = GraphicsLayoutWidget(self.centralwidget)
        self.customGraphWidget.setObjectName("customGraphWidget")
        self.verticalLayout.addWidget(self.customGraphWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1000, 22))
        self.menubar.setStyleSheet("background-color: rgb(238, 238, 236);\n"
"selection-color: rgb(136, 138, 133);")
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menu_Scale = QtWidgets.QMenu(self.menubar)
        self.menu_Scale.setObjectName("menu_Scale")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionx_limits = QtWidgets.QAction(MainWindow)
        self.actionx_limits.setObjectName("actionx_limits")
        self.actiony_scale = QtWidgets.QAction(MainWindow)
        self.actiony_scale.setObjectName("actiony_scale")
        self.actiony_limits = QtWidgets.QAction(MainWindow)
        self.actiony_limits.setObjectName("actiony_limits")
        self.actionAdd_channel = QtWidgets.QAction(MainWindow)
        self.actionAdd_channel.setObjectName("actionAdd_channel")
        self.actionRemove_channel = QtWidgets.QAction(MainWindow)
        self.actionRemove_channel.setObjectName("actionRemove_channel")
        self.actionSettings = QtWidgets.QAction(MainWindow)
        self.actionSettings.setObjectName("actionSettings")
        self.menuFile.addAction(self.actionAdd_channel)
        self.menuFile.addAction(self.actionRemove_channel)
        self.menu_Scale.addAction(self.actionSettings)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menu_Scale.menuAction())

        self.retranslateUi(MainWindow)
        self.actionAdd_channel.triggered.connect(MainWindow.slotAddChannel)
        self.comboBox.currentTextChanged['QString'].connect(MainWindow.slotComboBox)
        self.actionRemove_channel.triggered.connect(MainWindow.slotDeleteChannel)
        self.actionSettings.triggered.connect(MainWindow.slotAxes)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Live Plotter"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menu_Scale.setTitle(_translate("MainWindow", "Axes"))
        self.actionx_limits.setText(_translate("MainWindow", "x limits"))
        self.actiony_scale.setText(_translate("MainWindow", "y scale"))
        self.actiony_limits.setText(_translate("MainWindow", "y limits"))
        self.actionAdd_channel.setText(_translate("MainWindow", "Add channel"))
        self.actionRemove_channel.setText(_translate("MainWindow", "Remove channel"))
        self.actionSettings.setText(_translate("MainWindow", "Settings"))
from pyqtgraph import GraphicsLayoutWidget
