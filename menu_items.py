from PyQt5 import QtCore, QtWidgets
class RefractionMenuWidget(QtWidgets.QScrollArea):
    """A vertical set of menu items, with convenience functions to bind 
    callbacks to its subcomponents
    """
    def __init__(self,*args,reflection_counts={},**kwargs):
        QtWidgets.QScrollArea.__init__(self,*args,**kwargs)
        self.reflection_counts = reflection_counts
        self.setup()

    def HLine(self):
        """create a horizontal break - https://stackoverflow.com/a/26369850 """
        toto = QtWidgets.QFrame()
        toto.setFrameShape(QtWidgets.QFrame.HLine)
        toto.setFrameShadow(QtWidgets.QFrame.Sunken)
        return toto

    def setup(self):
        menu_widget = QtWidgets.QWidget()
        self.setSizePolicy(
                   QtWidgets.QSizePolicy.Minimum,
                   QtWidgets.QSizePolicy.Minimum)
        menu_l = QtWidgets.QVBoxLayout()
        menu_widget.setLayout(menu_l)
        self.setWidget(menu_widget)
        self.setWidgetResizable(True)

        self.angle_label = QtWidgets.QLabel(self, text="Initial Angle: ")
        menu_l.addWidget(self.angle_label)

        menu_l.addWidget(QtWidgets.QLabel(self, text="Reflection Counts:"))

        self.count_labels = {}
        for key in self.reflection_counts:
            self.count_labels[key] = QtWidgets.QLabel(self, text=key+": 0")
            menu_l.addWidget(self.count_labels[key])


        label7_l = QtWidgets.QHBoxLayout()
        label7_l.addStretch(1)
        self.pausebtn = QtWidgets.QToolButton(text="Pause")
        self.unpausebtn = QtWidgets.QToolButton(text="Resume")
        self.savebtn= QtWidgets.QToolButton(text="Save")
        label7_l.addWidget(self.pausebtn)
        label7_l.addWidget(self.unpausebtn)
        label7_l.addWidget(self.savebtn)
        menu_l.addLayout(label7_l)

        menu_l.addWidget(self.HLine())

        #Layer Index of Refraction Config
        label_l = QtWidgets.QHBoxLayout()
        label_l.addWidget(QtWidgets.QLabel(self, text="N = "))
        label_l.addStretch(1)
        plusbtn = QtWidgets.QToolButton(text="+")
        plusbtn.clicked.connect(self.add_layer)
        minusbtn = QtWidgets.QToolButton(text="-")
        minusbtn.clicked.connect(self.remove_layer)
        updatebtn = QtWidgets.QToolButton(text="Update")
        label_l.addWidget(plusbtn)
        label_l.addWidget(minusbtn)
        label_l.addWidget(updatebtn)
        menu_l.addLayout(label_l)
        self.layer_list = QtWidgets.QListWidget(self)
        menu_l.addWidget(self.layer_list)

        label2_l = QtWidgets.QHBoxLayout()
        label2_l.addWidget(QtWidgets.QLabel(self, text="dN/dλ (nm⁻¹) = "))
        self.dndlambda_edit = QtWidgets.QLineEdit(self)
        self.dndlambda_edit.setText("0.001")
        label2_l.addWidget(self.dndlambda_edit)
        menu_l.addLayout(label2_l)
        
        menu_l.addWidget(self.HLine())

        #Source movement config
        radioWidget = QtWidgets.QWidget()
        radioBox  = QtWidgets.QVBoxLayout()
        radioWidget.setLayout(radioBox)
        radioBox.addWidget(QtWidgets.QLabel("Click and Drag:"))
        circlebtn = QtWidgets.QRadioButton("Snap to Circle")
        circlebtn.setChecked(True)
        freebtn = QtWidgets.QRadioButton("Free Movement")
        radioBox.addWidget(circlebtn)
        radioBox.addWidget(freebtn)

        radioBox.addWidget(QtWidgets.QLabel("Auto Move:"))
        orbitbtn = QtWidgets.QRadioButton("Circle Perimeter")
        spinbtn = QtWidgets.QRadioButton("Spin in Place")
        radioBox.addWidget(orbitbtn)
        radioBox.addWidget(spinbtn)

        label6_l = QtWidgets.QHBoxLayout()
        label6_l.addWidget(QtWidgets.QLabel("Automove Settings:"))
        radioBox.addLayout(label6_l)
        self.update_auto_btn = QtWidgets.QToolButton(text="Update")
        label6_l.addWidget(self.update_auto_btn)

        label3_l = QtWidgets.QHBoxLayout()
        label3_l.addWidget(QtWidgets.QLabel(self,text="  ω (°/sec) = "))
        self.omega_edit = QtWidgets.QLineEdit(self)
        self.omega_edit.setText("45")
        label3_l.addWidget(self.omega_edit)
        radioBox.addLayout(label3_l)

        label4_l = QtWidgets.QHBoxLayout()
        label4_l.addWidget(QtWidgets.QLabel(self,text="  θ₁(°) = "))
        self.theta0_edit= QtWidgets.QLineEdit(self)
        self.theta0_edit.setText("0")
        label4_l.addWidget(self.theta0_edit)
        radioBox.addLayout(label4_l)

        label5_l = QtWidgets.QHBoxLayout()
        label5_l.addWidget(QtWidgets.QLabel(self,text="  θ₂(°) = "))
        self.theta1_edit= QtWidgets.QLineEdit(self)
        self.theta1_edit.setText("360")
        label5_l.addWidget(self.theta1_edit)
        radioBox.addLayout(label5_l)

        menu_l.addWidget(radioWidget)

        menu_l.addWidget(self.HLine())
        
        #Light type config
        colorWidget = QtWidgets.QWidget()
        colorBox = QtWidgets.QVBoxLayout()
        colorWidget.setLayout(colorBox)
        colorBox.addWidget(QtWidgets.QLabel("Color:"))
        monobtn = QtWidgets.QRadioButton("Monochromatic")
        monobtn.setChecked(True)
        broadbtn = QtWidgets.QRadioButton("Broadband")
        colorBox.addWidget(monobtn)
        colorBox.addWidget(broadbtn)
        menu_l.addWidget(colorWidget)

        menu_l.addStretch(1)

        self.radiobtns = {
            'mono':monobtn,
            'broad':broadbtn,
            'spin':spinbtn,
            'orbit':orbitbtn,
            'free':freebtn,
            'circle':circlebtn
        }
        self.updatebtn = updatebtn

    def connectButton(self,btnname,callback):
        if btnname in self.radiobtns:
            btn = self.radiobtns[btnname]
            btn.toggled.connect(lambda:callback(btn))

    def connectLayersUpdate(self,callback):
        class _Event: pass
        def buildEvent():
            e = _Event()
            e.refraction_indices = self.get_layer_idxs()
            e.dndlambda = float(self.dndlambda_edit.text())
            return e

        self.updatebtn.clicked.connect(lambda:callback(buildEvent()))

    def connectAutoMoveUpdate(self,callback):
        class _Event: pass
        def buildEvent():
            e = _Event()
            e.angular_velocity = float(self.omega_edit.text())
            e.theta0 = float(self.theta0_edit.text())
            e.theta1 = float(self.theta1_edit.text())
            return e

        self.update_auto_btn.clicked.connect(lambda:callback(buildEvent()))

    def connectSave(self,callback):
        self.savebtn.clicked.connect(callback)

    def connectPause(self,callback):
        self.pausebtn.clicked.connect(callback)

    def connectUnpause(self,callback):
        self.unpausebtn.clicked.connect(callback)
    
    def setAngleLabelText(self,text):
        self.angle_label.setText(text)

    def add_layer(self):
        item = QtWidgets.QListWidgetItem("1.33",parent=self.layer_list)
        item.setFlags(QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsSelectable|
                QtCore.Qt.ItemIsEnabled)
        self.layer_list.addItem(item)

    def remove_layer(self):
        to_remove = self.layer_list.selectedItems()
        if len(to_remove) == 0 and self.layer_list.count() > 0:
            to_remove.append(self.layer_list.item(
                self.layer_list.count()-1))
        for item in to_remove:
            idx = self.layer_list.indexFromItem(item)
            self.layer_list.takeItem(idx.row())

    def setCountLabel(self,key,count,pct):
        self.count_labels[key].setText(
                "{}: {} ({}%)".format(key,count,pct))

    def get_layer_idxs(self):
        layers =[]
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            layers.append(float(item.text()))

        return layers

