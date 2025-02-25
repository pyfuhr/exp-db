import sys
from PyQt6 import QtGui, uic, QtCore
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QFileDialog, QTableWidgetItem
from PyQt6.QtWidgets import QMessageBox
import sqlite3
from json import loads, dumps
from hashlib import sha1
con: sqlite3.Connection = None

class AddExp(QWidget):
    def __init__(self):
        super(AddExp, self).__init__()
        uic.loadUi('add_e.ui', self)
        self.add_bt.clicked.connect(self.add)
        self.addfile_bt.clicked.connect(self.add_file)
        self.delfile_bt.clicked.connect(self.del_file)
        self.file_tw.cellDoubleClicked.connect(self.show_item)
        self.set_mode(0)

    @QtCore.pyqtSlot(int, int)
    def show_item(self, r, c):
        if c == 1:
            print(self.file_tw.item(r, c).text())

    def add_file(self):
        file = QFileDialog.getOpenFileName()[0]
        name = self.fname_le.text()
        self.fname_le.clear()
        rows = self.file_tw.rowCount()
        self.file_tw.insertRow(rows)
        self.file_tw.setItem(rows, 0, QTableWidgetItem(name))
        self.file_tw.setItem(rows, 1, QTableWidgetItem(file))

    def del_file(self):
        self.file_tw.removeRow(self.file_tw.currentRow())

    def clear(self):
        for i in range(0,self.file_tw.rowCount()):
            self.file_tw.removeRow(0)
        self.file_tw.clear()
        self.fname_le.clear()
        self.name_le.clear()
        self.desc_te.clear()
        self.techp_cmb.clear()
        self.sample_cmb.clear()
        self.lid_le.clear()

    def set_mode(self, mode):
        # 0 - add, 1 - view
        self.clear()
        if mode == 0:
            self.setWindowTitle("Добавить экперимент")
            self.add_bt.show()
            self.gotechp_bt.hide()
            self.gosample_bt.hide()
            if not (con is None):
                cur = con.cursor()
                techp = cur.execute("SELECT local_id, name, hash_id FROM techprocesses")
                for it in techp.fetchall():
                    self.techp_cmb.addItem(f'{it[0]}.{it[1]}.{it[2]}')
                samples = cur.execute("SELECT local_id, name, hash_id FROM samples")
                for it in samples.fetchall():
                    self.sample_cmb.addItem(f'{it[0]}.{it[1]}.{it[2]}')
        else:
            self.setWindowTitle("Просмотр эксперимента")
            self.gotechp_bt.show()
            self.gosample_bt.show()
            self.add_bt.hide()

    def add(self):
        if con is None:
            mb = QMessageBox()
            mb.setText("Select database")
            mb.exec()
            return
        
        name = self.name_le.text()
        lid = self.lid_le.text()
        desc = self.desc_te.toPlainText()
        techp = self.techp_cmb.currentText().rsplit('.', 1)[1]
        sample = self.sample_cmb.currentText().rsplit('.', 1)[1]
        dt = self.dte.dateTime().toSecsSinceEpoch()
        # upload files
        uploaded_files = self.upload_files()
        ho = sha1()
        ho.update(lid.encode()); ho.update(name.encode()); ho.update(desc.encode()); ho.update(techp.encode()); ho.update(sample.encode()); ho.update(str(dt).encode())
        ho.update(uploaded_files.encode())
        hid = ho.hexdigest()

        cur = con.cursor()
        cur.execute("INSERT INTO experiments (hash_id, local_id, name, desc, techprocess, sample, date, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (hid, lid, name, desc, techp, sample, dt, uploaded_files))
        con.commit()

        self.clear()
        self.close()

    @QtCore.pyqtSlot(int)
    def get(self, id):
        if con is None:
            mb = QMessageBox()
            mb.setText("Select database")
            mb.exec()
            return
        
        cur = con.cursor()
        cur.execute("SELECT local_id, name, desc, techprocess, sample, date, data FROM experiments WHERE hash_id=?", (id, ))
        lid, name, desc, techp, sample, dt, uploaded_files = cur.fetchone()
        self.name_le.insert(name)
        self.desc_te.setPlainText(desc)
        cur.execute("SELECT local_id, name FROM techprocesses WHERE hash_id=?", (str(techp), ))
        self.techp_cmb.addItem(f'{'.'.join(map(str, cur.fetchone()))}.{techp}')
        cur.execute("SELECT local_id, name FROM samples WHERE hash_id=?", (str(sample), ))
        self.sample_cmb.addItem(f'{'.'.join(map(str, cur.fetchone()))}.{sample}')
        self.dte.setDateTime(QtCore.QDateTime.fromSecsSinceEpoch(dt))
        self.lid_le.insert(str(lid))
        if uploaded_files:
            d = loads(uploaded_files)
            for i, key in enumerate(d.keys()):
                self.file_tw.insertRow(i)
                self.file_tw.setItem(i, 0, QTableWidgetItem(key))
                self.file_tw.setItem(i, 1, QTableWidgetItem(d[key]))

    def upload_files(self):
        d = {}
        for i in range(self.file_tw.rowCount()):
            d[self.file_tw.item(i, 0).text()]= self.file_tw.item(i, 1).text()
        return dumps(d)

class AddSample(QWidget):
    def __init__(self):
        super(AddSample, self).__init__()
        uic.loadUi('add_s.ui', self)
        self.add_bt.clicked.connect(self.add)
        self.set_mode(0)

    def set_mode(self, mode):
        self.clear()
        # 0 - add, 1 - view
        if mode == 0:
            self.setWindowTitle("Добавить образец")
            self.add_bt.show()
            self.find_bt.hide()
        else:
            self.setWindowTitle("Просмотр образца")
            self.add_bt.hide()
            self.find_bt.show()

    def add(self):
        if con is None:
            mb = QMessageBox()
            mb.setText("Select database")
            mb.exec()
            return

        lid = self.lid_le.text()
        name = self.name_le.text()
        desc = self.desc_te.toPlainText()

        ho = sha1()
        ho.update(lid.encode()); ho.update(name.encode()); ho.update(desc.encode())
        hid = ho.hexdigest()

        cur = con.cursor()
        cur.execute("INSERT INTO samples (hash_id, name, desc, local_id) VALUES (?, ?, ?, ?)", (hid, name, desc, lid))
        con.commit()

        self.clear()
        self.close()

    def clear(self):
        self.name_le.clear()
        self.desc_te.clear()
        self.lid_le.clear()

    def get(self, id):
        if con is None:
            mb = QMessageBox()
            mb.setText("Select database")
            mb.exec()
            return
        
        print(id)
        
        cur = con.cursor()
        cur.execute("SELECT name, desc, local_id FROM samples WHERE hash_id=?", (id, ))
        name, desc, local_id = cur.fetchone()
        self.name_le.insert(name)
        self.desc_te.setPlainText(desc)
        self.lid_le.insert(str(local_id))

class AddTechp(QWidget):
    def __init__(self):
        super(AddTechp, self).__init__()
        uic.loadUi('add_t.ui', self)
        self.add_bt.clicked.connect(self.add)
        self.set_mode(0)

    def set_mode(self, mode):
        self.clear()
        # 0 - add, 1 - view
        if mode == 0:
            self.setWindowTitle("Добавить тепроцесс")
            self.add_bt.show()
            self.find_bt.hide()
        else:
            self.setWindowTitle("Просмотр техпроцесса")
            self.add_bt.hide()
            self.find_bt.show()

    def add(self):
        if con is None:
            mb = QMessageBox()
            mb.setText("Select database")
            mb.exec()
            return

        lid = self.lid_le.text()
        name = self.name_le.text()
        desc = self.desc_te.toPlainText()

        ho = sha1()
        ho.update(lid.encode()); ho.update(name.encode()); ho.update(desc.encode())
        hid = ho.hexdigest()

        cur = con.cursor()
        cur.execute("INSERT INTO techprocesses (hash_id, name, desc, local_id) VALUES (?, ?, ?, ?)", (hid, name, desc, lid))
        con.commit()

        self.clear()
        self.close()

    def clear(self):
        self.name_le.clear()
        self.lid_le.clear()
        self.desc_te.clear()

    def get(self, id):
        if con is None:
            mb = QMessageBox()
            mb.setText("Select database")
            mb.exec()
            return
        
        cur = con.cursor()
        cur.execute("SELECT name, desc, local_id FROM techprocesses WHERE hash_id=?", (id, ))
        name, desc, local_id = cur.fetchone()
        self.name_le.insert(name)
        self.desc_te.setPlainText(desc)
        self.lid_le.insert(str(local_id))

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('mainapp.ui', self)
        self.addsample = AddSample()
        self.addtechp = AddTechp()
        self.addexp = AddExp()
        self.addexp.gosample_bt.clicked.connect(lambda: self.addsample.set_mode(1) or self.addsample.get(self.addexp.sample_cmb.currentText().rsplit('.', 1)[1]) or self.addsample.show())
        self.addexp.gotechp_bt.clicked.connect(lambda: self.addtechp.set_mode(1) or self.addtechp.get(self.addexp.techp_cmb.currentText().rsplit('.', 1)[1]) or self.addtechp.show())
        self.addexp_act.triggered.connect(lambda: self.addexp.set_mode(0) or self.addexp.show())
        self.addsample_act.triggered.connect(lambda: self.addsample.set_mode(0) or self.addsample.show())
        self.addtechp_act.triggered.connect(lambda: self.addtechp.set_mode(0) or self.addtechp.show())
        self.open_act.triggered.connect(self.opendb)
        self.show()
        self.tabWidget.tabBarClicked.connect(self.update_listw)
        self.exp_lw.doubleClicked.connect(lambda: self.addexp.set_mode(1) or self.addexp.get(self.exp_lw.currentItem().text().rsplit('.',1)[1]) or self.addexp.show())
        self.samp_lw.doubleClicked.connect(lambda: self.addsample.set_mode(1) or self.addsample.get(self.samp_lw.currentItem().text().rsplit('.',1)[1]) or self.addsample.show())
        self.techp_lw.doubleClicked.connect(lambda: self.addtechp.set_mode(1) or self.addtechp.get(self.techp_lw.currentItem().text().rsplit('.',1)[1]) or self.addtechp.show())

    def update_listw(self):
        self.exp_lw.clear()
        self.techp_lw.clear()
        self.samp_lw.clear()
        if not (con is None):
            cur = con.cursor()
            cur.execute("SELECT local_id, name, hash_id FROM experiments")
            data = cur.fetchall()
            for it in data:
                self.exp_lw.addItem(f'{it[0]}.{it[1]}.{it[2]}')
            cur.execute("SELECT local_id, name, hash_id FROM techprocesses")
            data = cur.fetchall()
            for it in data:
                self.techp_lw.addItem(f'{it[0]}.{it[1]}.{it[2]}')
            cur.execute("SELECT local_id, name, hash_id FROM samples")
            data = cur.fetchall()
            for it in data:
                self.samp_lw.addItem(f'{it[0]}.{it[1]}.{it[2]}')
    
    def opendb(self):
        global con
        con = sqlite3.connect(QFileDialog.getOpenFileName()[0])
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())