import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from inventory_module import InventoryModule
from billing_module import BillingModule
from search_module import SearchModule
from db_connection import DatabaseError

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window icon
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle
            application_path = sys._MEIPASS
        else:
            # If the application is run from a Python interpreter
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(application_path, 'logo.ico')
        self.setWindowIcon(QIcon(icon_path))
        
        self.setWindowTitle("Battery Shop Management System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create modules
        self.inventory = InventoryModule()
        self.billing = BillingModule()
        self.search = SearchModule()
        
        # Add tabs
        self.tabs.addTab(self.inventory, "Inventory")
        self.tabs.addTab(self.billing, "Billing")
        self.tabs.addTab(self.search, "Search")
        
        # Connect signals
        self.inventory.model_added.connect(self.billing.update_model_list)
        self.inventory.model_added.connect(self.inventory.load_inventory)
        self.billing.bill_generated.connect(self.inventory.load_inventory)
        self.search.bill_changed.connect(self.inventory.load_inventory)

def main():
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Fatal Error", f"Application failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 