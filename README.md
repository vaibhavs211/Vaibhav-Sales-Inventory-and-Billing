# Vaibhav Sales – Battery Shop Management

A full-featured PyQt5 desktop application backed by MongoDB Atlas to streamline day-to-day battery shop operations. It supports:

- **Inventory Module** – View and manage stock levels in real time.  
  - Anyone can view current models and quantities.  
  - **Admin-only** controls to add new models or increment/decrement stock.  
- **Billing Module** – Create, calculate, and print both **GST** and **Non-GST** invoices on A4 paper.  
  - Enter item, quantity, price, discount.  
  - For GST bills: applies discount → computes base amount → splits CGST/SGST equally → renders amount in words.  
  - For Non-GST bills: applies discount → subtracts any buyback amount.  
  - Auto-assigns sequential invoice numbers, saves customer GSTIN, and updates inventory.  
  - HTML-based preview dialog with professional layout, branding, and “print” integration.  
- **Search Module** – Browse past bills with flexible filters: customer name (partial/regex), date range, bill type (GST vs Non-GST).  
  - Edit or delete existing invoices (rolling back stock adjustments).  
  - Export all GST invoices to Excel with one click.

---

## Features

- **Modern PyQt5 GUI** with dialogs, tables, completers, and styled widgets.  
- **MongoDB Atlas** backend via `pymongo`, secure connection via `.env`.  
- **Robust “Database” layer** manages counters, atomic invoice sequencing, upserts customers, and enforces stock integrity.  
- **Single-file executable** via PyInstaller — no Python install needed on client PCs.  
- **Environmental configuration**: store your `DB_URL`, optional admin password, and other secrets in a `.env` file.

---



## Getting Started

Follow these steps to get the project up and running on your local machine:

1. **Clone the repository**

   ```bash
   git clone https://github.com/vaibhavs211/Vaibhav-Sales-Inventory-and-Billing.git
   cd Vaibhav-Sales-Inventory-and-Billing
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create and configure your environment file**
   In the project root, create a file named `.env` with the following contents:

   ```ini
   DB_URL=your_mongodb_atlas_connection_string
   PASS="AdminPasswordForInventoryActions"
   ```

   Replace `your_mongodb_atlas_connection_string` with your actual MongoDB URI and `AdminPasswordForInventoryActions` with actual Password.

4. **Run in development mode**

   ```bash
   python main.py
   ```

5. **Build a standalone Windows executable**
   All build settings (icon, data files, hidden imports) are defined in `battery_shop.spec`. To bundle into a single `exe`, simply run:

   ```bash
   pyinstaller --clean --onefile --windowed battery_shop.spec
   ```


   After building, you’ll find `Battery Shop.exe` in the `dist/` folder. You can copy **just** this single executable to any Windows machine—and it will run even if Python is not installed.



---

## Module Breakdown

### InventoryModule

* **View**: list every battery model and its current stock.
* **Admin**: after logging in (password in `.env`), add new models or adjust stock with “+” / “–” controls.

### BillingModule

* **Non-GST**: apply discount, subtract buyback, show final total.
* **GST**: apply discount → compute base from gross → split CGST/SGST → calculate total.
* **Customer lookup**: auto-complete names, save GSTIN.
* **Preview & Print**: HTML invoice rendered in a `QTextEdit`, ready for A4 printing.

### SearchModule

* **Filter** by customer name, date range, and bill type.
* **Actions**: Edit (reload into BillingModule), Delete (remove and restore stock).
* **Export**: one-click download of all GST bills into an Excel file via `pandas` & `openpyxl`.


---

> **Contributions welcome!**
> Feel free to open issues for bugs or feature requests, and submit pull requests with improvements.
