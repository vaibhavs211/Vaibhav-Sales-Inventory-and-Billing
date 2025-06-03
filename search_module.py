from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTableWidget, QTableWidgetItem, QLabel, QLineEdit, 
                            QMessageBox, QCalendarWidget, QDialog, QComboBox)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
from db_connection import Database, DatabaseError
from datetime import datetime, timedelta
from billing_module import BillPreviewDialog, BillingModule

class DatePickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        self.calendar = QCalendarWidget()
        self.calendar.setFont(QFont('Arial', 12))
        layout.addWidget(self.calendar)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setFont(QFont('Arial', 12))
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont('Arial', 12))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_date(self):
        return self.calendar.selectedDate().toPyDate()

class SearchModule(QWidget):
    bill_changed = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.db = Database()
            self.setup_ui()
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
    
    def setup_ui(self):
        try:
            layout = QVBoxLayout()
            
            # Search section
            search_layout = QHBoxLayout()
            
            # Customer name search
            search_layout.addWidget(QLabel("Customer Name:"))
            self.customer_search = QLineEdit()
            self.customer_search.setFont(QFont('Arial', 12))
            search_layout.addWidget(self.customer_search)
            
            # Date range
            search_layout.addWidget(QLabel("From:"))
            self.from_date = QLineEdit()
            self.from_date.setReadOnly(True)
            self.from_date.setFont(QFont('Arial', 12))
            search_layout.addWidget(self.from_date)
            from_btn = QPushButton("Select")
            from_btn.setFont(QFont('Arial', 12))
            from_btn.clicked.connect(lambda: self.show_calendar('from'))
            search_layout.addWidget(from_btn)
            
            search_layout.addWidget(QLabel("To:"))
            self.to_date = QLineEdit()
            self.to_date.setReadOnly(True)
            self.to_date.setFont(QFont('Arial', 12))
            search_layout.addWidget(self.to_date)
            to_btn = QPushButton("Select")
            to_btn.setFont(QFont('Arial', 12))
            to_btn.clicked.connect(lambda: self.show_calendar('to'))
            search_layout.addWidget(to_btn)
            
            # Search button
            search_btn = QPushButton("Search")
            search_btn.setFont(QFont('Arial', 12))
            search_btn.clicked.connect(self.search_bills)
            search_layout.addWidget(search_btn)
            
            layout.addLayout(search_layout)
            
            # Filter section
            filter_layout = QHBoxLayout()
            self.bill_type_filter = QComboBox()
            self.bill_type_filter.addItem("All")
            self.bill_type_filter.addItem("GST")
            self.bill_type_filter.addItem("Non-GST")
            filter_layout.addWidget(QLabel("Bill Type:"))
            filter_layout.addWidget(self.bill_type_filter)
            layout.addLayout(filter_layout)
            self.bill_type_filter.currentIndexChanged.connect(self.search_bills)
            
            # Results table
            self.table = QTableWidget()
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels(['Invoice #', 'Date', 'Customer', 'Type', 'Items', 'Total', 'Actions'])
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setFont(QFont('Arial', 12))
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
            self.table.doubleClicked.connect(self.show_bill_details)
            layout.addWidget(self.table)
            
            self.setLayout(layout)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to setup search interface: {str(e)}")
    
    def show_calendar(self, target):
        try:
            dialog = DatePickerDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                date = dialog.get_date()
                if target == 'from':
                    self.from_date.setText(date.strftime('%Y-%m-%d'))
                else:
                    self.to_date.setText(date.strftime('%Y-%m-%d'))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show calendar: {str(e)}")
    
    def search_bills(self):
        try:
            self.table.setRowCount(0)
            
            customer_name = self.customer_search.text()
            from_date = self.from_date.text()
            to_date = self.to_date.text()
            
            try:
                if from_date:
                    from_date = datetime.strptime(from_date, '%Y-%m-%d')
                if to_date:
                    to_date = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid date format")
                return
            
            bill_type = self.bill_type_filter.currentText()
            bills = self.db.search_bills(customer_name, from_date, to_date)
            
            if bill_type == "GST":
                bills = [b for b in bills if b.get('bill_type', '').lower() == 'gst']
            elif bill_type == "Non-GST":
                bills = [b for b in bills if b.get('bill_type', '').lower() == 'non-gst']
            
            for row, bill in enumerate(bills):
                items_text = ", ".join([f"{item['model']}({item['quantity']})" for item in bill['items']])
                self.table.insertRow(row)
                
                # Add invoice number
                self.table.setItem(row, 0, QTableWidgetItem(str(bill['invoice_number'])))
                
                # Add date (without time)
                self.table.setItem(row, 1, QTableWidgetItem(bill['date'].strftime('%Y-%m-%d')))
                self.table.setItem(row, 2, QTableWidgetItem(bill['customer_name']))
                self.table.setItem(row, 3, QTableWidgetItem(bill['bill_type'].upper()))
                self.table.setItem(row, 4, QTableWidgetItem(items_text))
                self.table.setItem(row, 5, QTableWidgetItem(f"₹{bill['total']:.2f}"))
                
                # Add action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout()
                action_layout.setContentsMargins(0, 0, 0, 0)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setFont(QFont('Arial', 10))
                edit_btn.clicked.connect(lambda checked, b=bill: self.edit_bill(b))
                
                delete_btn = QPushButton("Delete")
                delete_btn.setFont(QFont('Arial', 10))
                delete_btn.clicked.connect(lambda checked, b=bill: self.delete_bill(b))
                
                action_layout.addWidget(edit_btn)
                action_layout.addWidget(delete_btn)
                action_widget.setLayout(action_layout)
                
                self.table.setCellWidget(row, 6, action_widget)
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to search bills: {str(e)}")
    
    def edit_bill(self, bill):
        try:
            edit_dialog = BillingModule(self)
            edit_dialog.setWindowTitle(f"Edit Bill #{bill['invoice_number']}")
            edit_dialog.setup_for_edit(bill)
            if edit_dialog.exec_() == QDialog.Accepted:
                self.search_bills()
                self.bill_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit bill: {str(e)}")
    
    def delete_bill(self, bill):
        try:
            reply = QMessageBox.question(
                self, 'Confirm Delete',
                f"Are you sure you want to delete bill #{bill['invoice_number']}?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if self.db.delete_bill(bill['invoice_number']):
                    QMessageBox.information(self, "Success", "Bill deleted successfully")
                    self.search_bills()
                    self.bill_changed.emit()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete bill")
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete bill: {str(e)}")
    
    def show_bill_details(self, index):
        try:
            row = index.row()
            date = self.table.item(row, 1).text()
            customer = self.table.item(row, 2).text()
            
            # Search for the bill
            bills = self.db.search_bills(customer, datetime.strptime(date, '%Y-%m-%d'))
            if not bills:
                return
            
            bill = bills[0]
            
            # Show bill preview
            dialog = BillPreviewDialog(bill, self)
            dialog.exec_()
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show bill details: {str(e)}") 