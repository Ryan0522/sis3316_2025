# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'axesDialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(357, 436)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 3, 1, 1)
        self.lineEdit_xmax = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_xmax.setText("")
        self.lineEdit_xmax.setObjectName("lineEdit_xmax")
        self.gridLayout.addWidget(self.lineEdit_xmax, 2, 5, 1, 1)
        self.label_5 = QtWidgets.QLabel(Dialog)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 2)
        self.lineEdit_xmin = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_xmin.setText("")
        self.lineEdit_xmin.setObjectName("lineEdit_xmin")
        self.gridLayout.addWidget(self.lineEdit_xmin, 2, 1, 1, 2)
        self.comboBox_yscale = QtWidgets.QComboBox(Dialog)
        self.comboBox_yscale.setObjectName("comboBox_yscale")
        self.comboBox_yscale.addItem("")
        self.comboBox_yscale.addItem("")
        self.gridLayout.addWidget(self.comboBox_yscale, 1, 2, 1, 4)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 4, 1, 1)
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.lineEdit_ymax = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_ymax.setText("")
        self.lineEdit_ymax.setObjectName("lineEdit_ymax")
        self.gridLayout.addWidget(self.lineEdit_ymax, 3, 5, 1, 1)
        self.lineEdit_ymin = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_ymin.setText("")
        self.lineEdit_ymin.setObjectName("lineEdit_ymin")
        self.gridLayout.addWidget(self.lineEdit_ymin, 3, 1, 1, 2)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 6, 2, 1, 4)
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 4, 1, 1)
        self.comboBox_hist = QtWidgets.QComboBox(Dialog)
        self.comboBox_hist.setObjectName("comboBox_hist")
        self.comboBox_hist.addItem("")
        self.comboBox_hist.addItem("")
        self.gridLayout.addWidget(self.comboBox_hist, 0, 2, 1, 4)
        self.checkBox_auto = QtWidgets.QCheckBox(Dialog)
        self.checkBox_auto.setEnabled(True)
        self.checkBox_auto.setChecked(False)
        self.checkBox_auto.setObjectName("checkBox_auto")
        self.gridLayout.addWidget(self.checkBox_auto, 5, 0, 1, 2)
        self.label_6 = QtWidgets.QLabel(Dialog)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 1, 0, 1, 2)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_5.setText(_translate("Dialog", "Histogram"))
        self.comboBox_yscale.setItemText(0, _translate("Dialog", "Linear"))
        self.comboBox_yscale.setItemText(1, _translate("Dialog", "Log"))
        self.label.setText(_translate("Dialog", "x min"))
        self.label_2.setText(_translate("Dialog", "x max"))
        self.label_3.setText(_translate("Dialog", "y min"))
        self.label_4.setText(_translate("Dialog", "y max"))
        self.comboBox_hist.setItemText(0, _translate("Dialog", "Time"))
        self.comboBox_hist.setItemText(1, _translate("Dialog", "ADC"))
        self.checkBox_auto.setText(_translate("Dialog", "Auto scale"))
        self.label_6.setText(_translate("Dialog", "y scale"))
