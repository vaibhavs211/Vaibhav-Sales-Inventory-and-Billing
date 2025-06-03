from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTableWidget, QTableWidgetItem, QLabel, QLineEdit, 
                            QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox,
                            QDialog, QTextEdit, QSizePolicy, QCompleter)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QStringListModel
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument, QFont, QPixmap
from db_connection import Database, DatabaseError
from datetime import datetime
import os
import math
import sys

class BillPreviewDialog(QDialog):
    def __init__(self, bill_data, parent=None):
        super().__init__(parent)
        self.bill_data = bill_data
        self.setup_ui()
    
    def setup_ui(self):
        try:
            self.setWindowTitle("Bill Preview")
            self.setModal(True)
            layout = QVBoxLayout()
            
            # Create text widget for bill preview
            self.text_edit = QTextEdit()
            self.text_edit.setReadOnly(True)
            self.text_edit.setFont(QFont('Arial', 12))
            self.text_edit.setHtml(self.generate_bill_html())
            layout.addWidget(self.text_edit)
            
            # Buttons
            btn_layout = QHBoxLayout()
            print_btn = QPushButton("Print")
            print_btn.setFont(QFont('Arial', 12))
            print_btn.setMinimumHeight(40)
            print_btn.clicked.connect(self.print_bill)
            close_btn = QPushButton("Close")
            close_btn.setFont(QFont('Arial', 12))
            close_btn.setMinimumHeight(40)
            close_btn.clicked.connect(self.accept)
            btn_layout.addWidget(print_btn)
            btn_layout.addWidget(close_btn)
            layout.addLayout(btn_layout)
            
            self.setLayout(layout)
            self.resize(900, 1000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to setup bill preview: {str(e)}")
    
    def generate_bill_html(self):
        bill = self.bill_data
        shop_gstin = "27DUSPS0660B1ZF"
        shop_contact = "9922444406, 9405903830"
        bank_details = {
            'name': 'Bank of Maharashtra',
            'branch': 'Hinganghat Branch',
            'account': '60211537562',
            'ifsc': 'MAHB0000059',
            'pan': 'DUSPS0660B'
        }
        
        def number_to_words(number):
            units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
            teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
            tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
            if number == 0:
                return "Zero"
            def convert_less_than_thousand(n):
                if n == 0:
                    return ""
                elif n < 10:
                    return units[n]
                elif n < 20:
                    return teens[n - 10]
                elif n < 100:
                    return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")
                else:
                    return units[n // 100] + " Hundred" + (" and " + convert_less_than_thousand(n % 100) if n % 100 != 0 else "")
            def convert(n):
                if n == 0:
                    return ""
                elif n < 1000:
                    return convert_less_than_thousand(n)
                elif n < 100000:
                    return convert_less_than_thousand(n // 1000) + " Thousand" + (" " + convert_less_than_thousand(n % 1000) if n % 1000 != 0 else "")
                elif n < 10000000:
                    return convert_less_than_thousand(n // 100000) + " Lakh" + (" " + convert(n % 100000) if n % 100000 != 0 else "")
                else:
                    return convert_less_than_thousand(n // 10000000) + " Crore" + (" " + convert(n % 10000000) if n % 10000000 != 0 else "")
            rupees = int(number)
            paise = int((number - rupees) * 100)
            result = convert(rupees) + " Rupees"
            if paise > 0:
                result += " and " + convert_less_than_thousand(paise) + " Paise"
            return result
        amount_in_words = number_to_words(bill['total'])
        
        # Get the correct path for the logo image
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle
            application_path = sys._MEIPASS
        else:
            # If the application is run from a Python interpreter
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        logo_path = os.path.join(application_path, 'Amaron-Logo.png').replace('\\', '/') # Use forward slashes for HTML

        html = f"""
        <div style='font-family: Arial; font-size: 14px; padding: 24px;'>
            <table width='800' style=' border-collapse: collapse; margin-bottom: 0;'>
                <tr>
                    <td width='600' style='vertical-align: top; padding: 0;'>
                        <div style='font-size: 28px; font-weight: bold;'>Vaibhav Sales</div>
                        <div style='font-size: 15px; margin-top: 2px;'>Deals Inverter, UPS and All Types of Batteries</div>
                        <div style='font-size: 14px; margin-top: 2px;'>Tukdoji Square, Nehru Ward,<br>Hinganghat- 442301, Dist. Wardha (M.S.)</div>
                    </td>
                    <td style='vertical-align: top; width: 40%; text-align: right; padding: 0;'>
                        <div style='font-size: 13px;'>Subject to Hinganghat Jurisdiction</div>
                        <div style='font-size: 13px;'>GSTIN: {shop_gstin}</div>
                        <div style='font-size: 13px;'>{shop_contact}</div>
                        <div style='font-size: 13px; margin-top: 8px;'>Authorised Dealer:     </div><br>
                        <img src='{logo_path}' width='160' height='40' style='object-fit: contain;'>
                    </td>
                </tr>
            </table>
            <hr style='border: 1px solid #000; margin: 10px 0 16px 0;'>
            <table width='800' style='border-collapse: collapse; margin-bottom: 0;'>
                <tr>
                    <td width='650' style=' vertical-align: top; padding: 0;'>
                        <span style='font-size: 17px; font-weight: bold;'>M/s. {bill['customer_name']}</span><br>
                        {f"<span style='font-size: 13px;'>GSTIN: {bill.get('customer_gstin', '')}</span>" if bill['bill_type'] == 'gst' else ""}
                    </td>
                    <td width='150' style=' text-align: left; vertical-align: top; padding: 0;'>
                        <span style='font-size: 13px;'><b>Bill No.:</b> {bill['invoice_number']}</span><br>
                        <span style='font-size: 13px;'><b>Date:</b> {bill['date'].strftime('%Y-%m-%d')}</span>
                    </td>
                </tr>
            </table>
            <hr style='border: 1px solid #000; margin: 10px 0 16px 0;'>
            <table cellpadding='10' border='0' width='800' style=' border-collapse: collapse; margin: 0 0 20px 0;'>
                <tr style='background: #f0f0f0;'>
                    <th width='50' style='border: 1px solid #000; padding: 8px;  font-size: 14px;'>Sr. No.</th>
                    <th width='470' style='border: 1px solid #000; padding: 8px;  font-size: 14px;'>Particulars</th>
                    <th width='80' style='border: 1px solid #000; padding: 8px;  font-size: 14px;'>Qty</th>
                    <th width='100' style='border: 1px solid #000; padding: 8px;  font-size: 14px;'>Rate</th>
                    <th width='100' style='border: 1px solid #000; padding: 8px;  font-size: 14px;'>Amount</th>
                </tr>
        """
        total_items = 0
        for idx, item in enumerate(bill['items'], 1):
            total_items += 1
            html += f"""
                <tr>
                    <td style='border: 1px solid #000; padding: 8px; text-align: center;'>{idx}</td>
                    <td style='border: 1px solid #000; padding: 8px;'>{item['model']}</td>
                    <td style='border: 1px solid #000; padding: 8px; text-align: center;'>{item['quantity']}</td>
                    <td style='border: 1px solid #000; padding: 8px; text-align: right;'>₹{item['discounted_price']:.2f}</td>
                    <td style='border: 1px solid #000; padding: 8px; text-align: right;'>₹{item['total']:.2f}</td>
                </tr>
            """
        if total_items<10:
            for _ in range(10 - total_items):
                html += """
                    <tr>
                        <td style='border-left: 1px solid #000; border-right: 1px solid #000;'>&nbsp;</td>
                        <td style='border-left: 1px solid #000; border-right: 1px solid #000;'>&nbsp;</td>
                        <td style='border-left: 1px solid #000; border-right: 1px solid #000;'>&nbsp;</td>
                        <td style='border-left: 1px solid #000; border-right: 1px solid #000;'>&nbsp;</td>
                        <td style='border-left: 1px solid #000; border-right: 1px solid #000;'>&nbsp;</td>
                    </tr>
                """
        if bill['bill_type'] == 'gst':
            html += f"""
                <tr>
                    <td rowspan='4' colspan='2' align='left' valign='bottom' style='border: 1px solid #000; padding: 8px;'><p><strong>Amount in words:</strong> {amount_in_words}</p></td>
                    <td colspan='2' style='text-align:right; border:1px solid #000; padding:8px;'><strong>Subtotal</strong></td>
                    <td style='border:1px solid #000; padding:8px; text-align:right;'>₹{bill['subtotal']:.2f}</td>
                </tr>
                <tr>
                    <td colspan='2' style='text-align:right; border:1px solid #000; padding:8px;'><strong>CGST ({bill['gst_percent']/2:.1f}%)</strong></td>
                    <td style='border:1px solid #000; padding:8px; text-align:right;'>₹{bill['cgst']:.2f}</td>
                </tr>
                <tr>
                    <td colspan='2' style='text-align:right; border:1px solid #000; padding:8px;'><strong>SGST ({bill['gst_percent']/2:.1f}%)</strong></td>
                    <td style='border:1px solid #000; padding:8px; text-align:right;'>₹{bill['sgst']:.2f}</td>
                </tr>
            """
        else:
            html += f"""
                <tr>
                    <td rowspan='3' colspan='2' align='left' valign='bottom' style='border: 1px solid #000; padding: 8px;'><p><strong>Amount in words:</strong> {amount_in_words}</p></td>
                    <td colspan='2' style='text-align:right; border:1px solid #000; padding:8px;'><strong>Subtotal</strong></td>
                    <td style='border:1px solid #000; padding:8px; text-align:right;'>₹{bill['subtotal']:.2f}</td>
                </tr>
                <tr>
                    <td colspan='2' style='border: 1px solid #000; padding: 8px; text-align: right;'><strong>Buyback Amount</strong></td>
                    <td style='border: 1px solid #000; padding: 8px; text-align: right;'>₹{bill['buyback']:.2f}</td>
                </tr>
            """
        html += f"""
                <tr>
                    <td colspan='2' style='text-align:right; border:1px solid #000; padding:8px;'><strong>Grand Total</strong></td>
                    <td style='border:1px solid #000; padding:8px; text-align:right;'>₹{bill['total']:.2f}</td>
                </tr>
            </table>
            <div style='display: flex; margin: 20px 0;'>
                <div style='width: 70%;'>
                    
                    <p style='margin: 10px 0;'>
                        <strong>Bank Details:</strong><br>
                        Name of Bank: {bank_details['name']}<br>
                        {bank_details['branch']}<br>
                        A/c No.: {bank_details['account']}<br>
                        IFSC: {bank_details['ifsc']}<br>
                        PAN: {bank_details['pan']}
                    </p>
                </div>
                <div style='width: 30%; text-align: right;'>
                    <p style='margin: 0;'>For, Vaibhav Sales</p>
                    <div style='height: 50px;'></div>
                    <p style='margin: 0;'>Auth. Signatory</p>
                </div>
            </div>
            <hr style='border: 1px solid #000; margin: 20px 0;'>
            <div style='display: flex; justify-content: space-between; font-size: 12px;'>
                <div style='width: 70%;'>
                    <p style='margin: 0;'>No Exchange, No Return. Receipt subject to clearance of cheque. Warranty applicable as per companies norms. No warranty for damage to any part.</p>
                    <p style='margin: 5px 0;'>Thanks!</p>
                </div>
            </div>
        </div>
        """
        return html
    
    def print_bill(self):
        try:
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QDialog.Accepted:
                self.text_edit.print_(printer)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print bill: {str(e)}")

class BillingModule(QDialog):
    bill_generated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.db = Database()
            self.editing_invoice_number = None
            self.setup_ui()
            # Prefill customer name for non-GST bills
            if self.bill_type.currentText() == "Non-GST":
                self.customer_name.setText("Customer")
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
    
    def setup_ui(self):
        try:
            self.setWindowTitle("New Bill")
            self.setModal(True)
            layout = QVBoxLayout()
            
            # Customer details
            customer_layout = QHBoxLayout()
            customer_label = QLabel("Customer Name:")
            customer_label.setFont(QFont('Arial', 12))
            customer_label.setMinimumHeight(35)
            customer_layout.addWidget(customer_label)
            
            self.customer_name = QLineEdit()
            self.customer_name.setFont(QFont('Arial', 12))
            self.customer_name.setMinimumHeight(35)
            self.customer_name.textChanged.connect(self.on_customer_name_changed)
            customer_layout.addWidget(self.customer_name)
            
            # QCompleter setup
            self._customer_completer = QCompleter(self)
            self._customer_completer.setCaseSensitivity(Qt.CaseInsensitive)
            self._customer_completer.setFilterMode(Qt.MatchContains)
            self._customer_completer.setCompletionMode(QCompleter.PopupCompletion)
            self._customer_model = QStringListModel([], self)
            self._customer_completer.setModel(self._customer_model)
            self.customer_name.setCompleter(self._customer_completer)
            self._customer_completer.activated[str].connect(self._on_customer_chosen)
            
            # GST number
            self.gst_label = QLabel("GST Number:")
            self.gst_label.setFont(QFont('Arial', 12))
            self.gst_label.setMinimumHeight(35)
            self.gst_input = QLineEdit()
            self.gst_input.setFont(QFont('Arial', 12))
            self.gst_input.setMinimumHeight(35)
            self.gst_input.setVisible(False)
            self.gst_label.setVisible(False)
            customer_layout.addWidget(self.gst_label)
            customer_layout.addWidget(self.gst_input)
            
            # Bill type
            bill_type_label = QLabel("Bill Type:")
            bill_type_label.setFont(QFont('Arial', 12))
            bill_type_label.setMinimumHeight(35)
            customer_layout.addWidget(bill_type_label)
            
            self.bill_type = QComboBox()
            self.bill_type.setFont(QFont('Arial', 12))
            self.bill_type.setMinimumHeight(35)
            self.bill_type.addItems(["Non-GST", "GST"])
            self.bill_type.currentTextChanged.connect(self.toggle_gst)
            customer_layout.addWidget(self.bill_type)
            
            # GST percentage
            self.gst_percent_label = QLabel("GST %:")
            self.gst_percent_label.setFont(QFont('Arial', 12))
            self.gst_percent_label.setMinimumHeight(35)
            self.gst_percent_input = QDoubleSpinBox()
            self.gst_percent_input.setFont(QFont('Arial', 12))
            self.gst_percent_input.setMinimumHeight(35)
            self.gst_percent_input.setRange(0, 100)
            self.gst_percent_input.setValue(28)
            self.gst_percent_input.setVisible(False)
            self.gst_percent_label.setVisible(False)
            customer_layout.addWidget(self.gst_percent_label)
            customer_layout.addWidget(self.gst_percent_input)
            
            layout.addLayout(customer_layout)
            
            # Items table
            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(['Model', 'Quantity', 'Price', 'Total', 'Actions'])
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setFont(QFont('Arial', 14))
            self.table.horizontalHeader().setDefaultSectionSize(250)
            self.table.verticalHeader().setDefaultSectionSize(50)
            self.table.setStyleSheet("""
                QTableWidget {
                    font-size: 14px;
                }
                QHeaderView::section {
                    font-size: 14px;
                    padding: 8px;
                }
            """)
            layout.addWidget(self.table)
            
            # Add item section
            add_layout = QHBoxLayout()
            
            model_label = QLabel("Model:")
            model_label.setFont(QFont('Arial', 12))
            model_label.setMinimumHeight(35)
            add_layout.addWidget(model_label)
            
            self.model_combo = QComboBox()
            self.model_combo.setFont(QFont('Arial', 12))
            self.model_combo.setMinimumHeight(35)
            self.update_model_list()
            add_layout.addWidget(self.model_combo)
            
            quantity_label = QLabel("Quantity:")
            quantity_label.setFont(QFont('Arial', 12))
            quantity_label.setMinimumHeight(35)
            add_layout.addWidget(quantity_label)
            
            self.quantity_spin = QSpinBox()
            self.quantity_spin.setFont(QFont('Arial', 12))
            self.quantity_spin.setMinimumHeight(35)
            self.quantity_spin.setRange(1, 100)
            add_layout.addWidget(self.quantity_spin)
            
            price_label = QLabel("Price:")
            price_label.setFont(QFont('Arial', 12))
            price_label.setMinimumHeight(35)
            add_layout.addWidget(price_label)
            
            self.price_spin = QDoubleSpinBox()
            self.price_spin.setFont(QFont('Arial', 12))
            self.price_spin.setMinimumHeight(35)
            self.price_spin.setRange(0, 100000)
            self.price_spin.setDecimals(2)
            add_layout.addWidget(self.price_spin)
            
            add_btn = QPushButton("Add Item")
            add_btn.setFont(QFont('Arial', 12))
            add_btn.setMinimumHeight(35)
            add_btn.clicked.connect(self.add_item)
            add_layout.addWidget(add_btn)
            
            layout.addLayout(add_layout)
            
            # Totals section
            totals_layout = QHBoxLayout()
            
            # Discount
            discount_label = QLabel("Discount %:")
            discount_label.setFont(QFont('Arial', 12))
            discount_label.setMinimumHeight(35)
            totals_layout.addWidget(discount_label)
            
            self.discount_spin = QDoubleSpinBox()
            self.discount_spin.setFont(QFont('Arial', 12))
            self.discount_spin.setMinimumHeight(35)
            self.discount_spin.setRange(0, 100)
            totals_layout.addWidget(self.discount_spin)
            
            # Buyback
            buyback_label = QLabel("Buyback:")
            buyback_label.setFont(QFont('Arial', 12))
            buyback_label.setMinimumHeight(35)
            self.buyback_spin = QDoubleSpinBox()
            self.buyback_spin.setFont(QFont('Arial', 12))
            self.buyback_spin.setMinimumHeight(35)
            self.buyback_spin.setRange(0, 100000)
            self.buyback_spin.setDecimals(2)
            totals_layout.addWidget(buyback_label)
            totals_layout.addWidget(self.buyback_spin)
            self.buyback_label = buyback_label
            
            layout.addLayout(totals_layout)
            
            # Total labels
            totals_display = QHBoxLayout()
            self.subtotal_label = QLabel("Subtotal: ₹0.00")
            self.subtotal_label.setFont(QFont('Arial', 12))
            self.gst_amount_label = QLabel("GST: ₹0.00")
            self.gst_amount_label.setFont(QFont('Arial', 12))
            self.total_label = QLabel("Total: ₹0.00")
            self.total_label.setFont(QFont('Arial', 12))
            totals_display.addWidget(self.subtotal_label)
            totals_display.addWidget(self.gst_amount_label)
            totals_display.addWidget(self.total_label)
            layout.addLayout(totals_display)
            
            # Buttons
            btn_layout = QHBoxLayout()
            calculate_btn = QPushButton("Calculate Total")
            calculate_btn.setFont(QFont('Arial', 12))
            calculate_btn.setMinimumHeight(40)
            calculate_btn.clicked.connect(self.calculate_total)
            generate_btn = QPushButton("Generate Bill")
            generate_btn.setFont(QFont('Arial', 12))
            generate_btn.setMinimumHeight(40)
            generate_btn.clicked.connect(self.generate_bill)
            clear_btn = QPushButton("Clear")
            clear_btn.setFont(QFont('Arial', 12))
            clear_btn.setMinimumHeight(40)
            clear_btn.clicked.connect(self.clear_bill)
            
            btn_layout.addWidget(calculate_btn)
            btn_layout.addWidget(generate_btn)
            btn_layout.addWidget(clear_btn)
            layout.addLayout(btn_layout)
            
            self.setLayout(layout)
            self.resize(1200, 800)
            self.toggle_gst(self.bill_type.currentText())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to setup billing interface: {str(e)}")
    
    def on_customer_name_changed(self, text):
        try:
            if self.bill_type.currentText() != "GST":
                self._customer_model.setStringList([])
                return
            names = [c['name'] for c in self.db.search_customers(text)]
            if not names:
                self._customer_model.setStringList([])
                return
            self._customer_model.setStringList(names)
            self.customer_name.completer().complete()
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to search customers: {str(e)}")
    
    def _on_customer_chosen(self, name):
        try:
            self.customer_name.setText(name)
            customer = self.db.get_customer(name)
            self.gst_input.setText(customer.get('gstin',''))
            self.gst_input.setFocus()
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get customer details: {str(e)}")
    
    def toggle_gst(self, bill_type):
        is_gst = bill_type == "GST"
        self.gst_label.setVisible(is_gst)
        self.gst_input.setVisible(is_gst)
        self.gst_percent_label.setVisible(is_gst)
        self.gst_percent_input.setVisible(is_gst)
        self.gst_amount_label.setVisible(is_gst)
        self.buyback_spin.setVisible(not is_gst)
        self.buyback_label.setVisible(not is_gst)
        if not is_gst:
            self.customer_name.setText("Customer")
            self.gst_input.clear()
        elif self.customer_name.text() == "Customer":
            self.customer_name.clear()
    
    def update_model_list(self):
        try:
            self.model_combo.clear()
            inventory = self.db.get_inventory()
            self.model_combo.addItems([item['model'] for item in inventory])
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update model list: {str(e)}")
    
    def add_item(self):
        try:
            model = self.model_combo.currentText()
            quantity = self.quantity_spin.value()
            price    = self.price_spin.value()
            discount = self.discount_spin.value()

            if self.bill_type.currentText() == "GST":
                gst_percent = self.gst_percent_input.value()
                # 1. apply discount to entered price, then round
                discounted_price = round(price * (1 - discount/100))
                # 2. compute base price from discounted, then round
                base_price = round(discounted_price / (1 + gst_percent/100))
                # 3. amount = base_price * qty
                amount = base_price * quantity
                rate_to_display   = base_price
                total_to_display  = amount
            else:
                # non-GST path unchanged
                rate_to_display  = round(price * (1 - discount/100))
                total_to_display = rate_to_display * quantity

            inventory = self.db.get_inventory()
            item = next((i for i in inventory if i['model'] == model), None)
            if not item:
                QMessageBox.warning(self, "Error", "Item not found in inventory")
                return
            if item['quantity'] < quantity:
                QMessageBox.warning(self, "Error", "Insufficient stock")
                return
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(model))
            self.table.setItem(row, 1, QTableWidgetItem(str(quantity)))
            self.table.setItem(row, 2, QTableWidgetItem(f"₹{rate_to_display:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"₹{total_to_display:.2f}"))
            delete_btn = QPushButton("×")
            delete_btn.setFont(QFont('Arial', 12))
            delete_btn.setFixedSize(35, 35)
            delete_btn.clicked.connect(lambda: self.delete_item(row))
            self.table.setCellWidget(row, 4, delete_btn)
            self.calculate_total()
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add item: {str(e)}")
    
    def delete_item(self, row):
        self.table.removeRow(row)
        self.calculate_total()
    
    def calculate_total(self):
        try:
            subtotal = 0
            for row in range(self.table.rowCount()):
                amt = float(self.table.item(row, 3).text().replace('₹',''))
                subtotal += amt
            if self.bill_type.currentText() == "GST":
                gst_percent = self.gst_percent_input.value()
                gst_amount = subtotal * gst_percent / 100
                cgst = sgst = gst_amount / 2
                final_total = round(subtotal + gst_amount)
                self.gst_amount_label.setText(
                    f"CGST: ₹{cgst:.2f} | SGST: ₹{sgst:.2f}"
                )
            else:
                buyback = self.buyback_spin.value()
                gst_amount = cgst = sgst = 0
                final_total = subtotal - buyback
                self.gst_amount_label.setText("")  # or hide
            self.subtotal_label.setText(f"Subtotal: ₹{subtotal:.2f}")
            self.total_label   .setText(f"Total: ₹{final_total:.2f}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to calculate total: {str(e)}")
    
    def clear_bill(self):
        self.editing_invoice_number = None
        if self.bill_type.currentText() == "Non-GST":
            self.customer_name.setText("Customer")
        else:
            self.customer_name.clear()
        self.gst_percent_input.setValue(28)
        self.discount_spin.setValue(0)
        self.buyback_spin.setValue(0)
        self.table.setRowCount(0)
        self.gst_input.clear()
        self.model_combo.setCurrentIndex(-1)
        self.quantity_spin.setValue(0)
        self.price_spin.setValue(0)
        self.calculate_total()

    def setup_for_edit(self, bill):
        try:
            self.editing_invoice_number = bill['invoice_number']
            self.customer_name.setText(bill['customer_name'])
            self.bill_type.setCurrentText(bill['bill_type'].upper())
            self.discount_spin.setValue(bill['discount'])
            self.buyback_spin.setValue(bill.get('buyback', 0))
            self.gst_input.clear()
            self.table.setRowCount(0)
            self.model_combo.setCurrentIndex(-1)
            self.quantity_spin.setValue(0)
            self.price_spin.setValue(0)
            if bill['bill_type'] == 'gst':
                self.gst_percent_input.setValue(bill['gst_percent'])
                self.gst_input.setText(bill.get('customer_gstin', ''))
            for item in bill['items']:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(item['model']))
                self.table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
                price = item.get('discounted_price', item.get('price', 0))
                self.table.setItem(row, 2, QTableWidgetItem(f"₹{price:.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"₹{item['total']:.2f}"))
                delete_btn = QPushButton("×")
                delete_btn.setFont(QFont('Arial', 12))
                delete_btn.setFixedSize(35, 35)
                delete_btn.clicked.connect(lambda _, r=row: self.delete_item(r))
                self.table.setCellWidget(row, 4, delete_btn)
            self.calculate_total()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to setup bill for editing: {str(e)}")

    def generate_bill(self):
        try:
            if self.table.rowCount() == 0:
                QMessageBox.warning(self, "Error", "No items in bill")
                return
            customer_name = self.customer_name.text()
            if not customer_name:
                QMessageBox.warning(self, "Error", "Please enter customer name")
                return
            if self.bill_type.currentText() == "GST":
                gstin = self.gst_input.text().strip()
                if not gstin:
                    QMessageBox.warning(self, "Error", "Please enter GST number for GST bill")
                    return
            self.calculate_total()
            items = []
            for row in range(self.table.rowCount()):
                model = self.table.item(row, 0).text()
                quantity = int(self.table.item(row, 1).text())
                discounted_price = float(self.table.item(row, 2).text().replace('₹', ''))
                total = float(self.table.item(row, 3).text().replace('₹', ''))
                items.append({
                    'model': model,
                    'quantity': quantity,
                    'discounted_price': discounted_price,
                    'total': total
                })
            bill_data = {
                'customer_name': customer_name,
                'bill_type': self.bill_type.currentText().lower(),
                'items': items,
                'discount': self.discount_spin.value(),
            }
            if self.bill_type.currentText() == "GST":
                gst_percent = self.gst_percent_input.value()
                subtotal = sum(item['total'] for item in items)
                gst_amount = subtotal * gst_percent / 100
                cgst = gst_amount / 2
                sgst = gst_amount / 2
                final_total = round(subtotal + gst_amount)
                bill_data.update({
                    'gst_percent': gst_percent,
                    'subtotal': subtotal,
                    'cgst': cgst,
                    'sgst': sgst,
                    'total': final_total,
                    'customer_gstin': self.gst_input.text().strip()
                })
            else:
                subtotal = sum(item['total'] for item in items)
                buyback  = self.buyback_spin.value()
                final_total = subtotal - buyback
                bill_data.update({
                    'subtotal': subtotal,
                    'cgst': 0,
                    'sgst': 0,
                    'total': final_total,
                    'buyback': buyback
                })
            if self.editing_invoice_number:
                self.db.update_bill(self.editing_invoice_number, bill_data)
                bill_data['invoice_number'] = self.editing_invoice_number
            else:
                invoice_number = self.db.save_bill(bill_data)
                bill_data['invoice_number'] = invoice_number
                
                for item in items:
                    model = item['model']
                    qty   = item['quantity']
                    self.db.update_inventory(model, -qty)
            dialog = BillPreviewDialog(bill_data, self)
            dialog.exec_()
            self.clear_bill()
            self.bill_generated.emit()
        except DatabaseError as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate bill: {str(e)}") 