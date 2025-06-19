from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTableWidget, QTableWidgetItem, QDialog, QLabel, 
                            QLineEdit, QMessageBox, QInputDialog, QStyledItemDelegate)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from db_connection import Database, DatabaseError
from dotenv import load_dotenv
import sys
import os

class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = {}
    
    def createEditor(self, parent, option, index):
        if index.column() == 2:  # Action column
            widget = QWidget(parent)
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            
            add_btn = QPushButton("+")
            add_btn.setFixedSize(30, 30)
            add_btn.clicked.connect(lambda: self.parent().add_stock(index.row()))
            
            sub_btn = QPushButton("-")
            sub_btn.setFixedSize(30, 30)
            sub_btn.clicked.connect(lambda: self.parent().subtract_stock(index.row()))
            
            layout.addWidget(add_btn)
            layout.addWidget(sub_btn)
            widget.setLayout(layout)
            return widget
        return super().createEditor(parent, option, index)

class AddModelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Model")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Model input
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model Name:"))
        self.model_input = QLineEdit()
        self.model_input.setFont(QFont('Arial', 14))
        model_layout.addWidget(self.model_input)
        layout.addLayout(model_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.setFont(QFont('Arial', 14))
        add_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont('Arial', 14))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_model_name(self):
        return self.model_input.text().strip()

class InventoryModule(QWidget):
    model_added = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.db = Database()
            self.is_admin = False
            self.setup_ui()
            self.load_inventory()
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Top buttons layout
        btn_layout = QHBoxLayout()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFont(QFont('Arial', 12))
        refresh_btn.setMinimumHeight(35)
        refresh_btn.clicked.connect(self.load_inventory)
        btn_layout.addWidget(refresh_btn)
        
        # Admin login/logout button
        self.admin_btn = QPushButton("Admin Login")
        self.admin_btn.setFont(QFont('Arial', 12))
        self.admin_btn.setMinimumHeight(35)
        self.admin_btn.clicked.connect(self.toggle_admin)
        btn_layout.addWidget(self.admin_btn)
        
        layout.addLayout(btn_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Model', 'Quantity', 'Actions'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultSectionSize(400)
        self.table.setFont(QFont('Arial', 14))
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
            }
            QHeaderView::section {
                font-size: 14px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.table)
        
        # Add model button
        self.add_model_btn = QPushButton("Add New Model")
        self.add_model_btn.setFont(QFont('Arial', 12))
        self.add_model_btn.clicked.connect(self.show_add_model_dialog)
        layout.addWidget(self.add_model_btn)
        
        self.setLayout(layout)
    
    def toggle_admin(self):
        if not self.is_admin:
            # Show login dialog
            password, ok = QInputDialog.getText(
                self, "Admin Login",
                "Enter admin password:",
                QLineEdit.Password
            )
            # Get the correct path for .env file
            if getattr(sys, 'frozen', False):
                # If the application is run as a bundle
                application_path = sys._MEIPASS
            else:
                # If the application is run from a Python interpreter
                application_path = os.path.dirname(os.path.abspath(__file__))

            # Load .env file from the correct location
            env_path = os.path.join(application_path, '.env')
            load_dotenv(env_path)
            if ok and password == (os.getenv('PASS')):
                self.is_admin = True
                self.admin_btn.setText("Admin Logout")
                self.add_model_btn.setVisible(True)
                self.load_inventory()  # Reload to show action buttons
                QMessageBox.information(self, "Success", "Admin login successful")
            elif ok:
                QMessageBox.warning(self, "Error", "Incorrect password")
        else:
            # Logout
            self.is_admin = False
            self.admin_btn.setText("Admin Login")
            self.add_model_btn.setVisible(False)
            self.load_inventory()  # Reload to hide action buttons
            QMessageBox.information(self, "Success", "Admin logout successful")
    
    def load_inventory(self):
        try:
            self.table.setRowCount(0)
            inventory = self.db.get_inventory()
            
            for row, item in enumerate(inventory):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(item['model']))
                self.table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
                
                # Add action buttons only if admin is logged in
                if self.is_admin:
                    action_widget = QWidget()
                    action_layout = QHBoxLayout()
                    action_layout.setContentsMargins(0, 0, 0, 0)
                    
                    add_btn = QPushButton("+")
                    add_btn.setFixedSize(30, 30)
                    add_btn.clicked.connect(lambda checked, r=row: self.add_stock(r))
                    
                    sub_btn = QPushButton("-")
                    sub_btn.setFixedSize(30, 30)
                    sub_btn.clicked.connect(lambda checked, r=row: self.subtract_stock(r))
                    
                    action_layout.addWidget(add_btn)
                    action_layout.addWidget(sub_btn)
                    action_widget.setLayout(action_layout)
                    
                    self.table.setCellWidget(row, 2, action_widget)
                else:
                    # Empty cell when not admin
                    self.table.setItem(row, 2, QTableWidgetItem(""))
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load inventory: {str(e)}")
    
    def add_stock(self, row):
        if not self.is_admin:
            QMessageBox.warning(self, "Error", "Admin access required")
            return
            
        try:
            model = self.table.item(row, 0).text()
            current_qty = int(self.table.item(row, 1).text())
            
            quantity, ok = QInputDialog.getInt(
                self, "Add Stock",
                f"Enter quantity to add for {model}:",
                1, 1, 1000, 1
            )
            
            if ok:
                self.db.update_inventory(model, quantity)
                self.load_inventory()
                QMessageBox.information(self, "Success", "Stock added successfully")
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add stock: {str(e)}")
    
    def subtract_stock(self, row):
        if not self.is_admin:
            QMessageBox.warning(self, "Error", "Admin access required")
            return
            
        try:
            model = self.table.item(row, 0).text()
            current_qty = int(self.table.item(row, 1).text())
            
            quantity, ok = QInputDialog.getInt(
                self, "Remove Stock",
                f"Enter quantity to remove for {model}:",
                1, 1, current_qty, 1
            )
            
            if ok:
                self.db.update_inventory(model, -quantity)
                self.load_inventory()
                QMessageBox.information(self, "Success", "Stock removed successfully")
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove stock: {str(e)}")
    
    def show_add_model_dialog(self):
        if not self.is_admin:
            QMessageBox.warning(self, "Error", "Admin access required")
            return
            
        try:
            dialog = AddModelDialog(self)
            if dialog.exec_():
                model_name = dialog.get_model_name()
                if model_name:
                    if self.db.add_new_model(model_name):
                        self.load_inventory()
                        self.model_added.emit()
                        QMessageBox.information(self, "Success", "New model added successfully")
                    else:
                        QMessageBox.warning(self, "Error", "Model already exists")
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add new model: {str(e)}") 