from pymongo import MongoClient
from datetime import datetime
import os
import sys
from dotenv import load_dotenv
from pymongo.errors import ConnectionFailure, OperationFailure

class DatabaseError(Exception):
    pass

class Database:
    def __init__(self):
        try:
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
            
            # Connect to MongoDB Atlas
            self.client = MongoClient(os.getenv('DB_URL'))
            # Verify connection
            self.client.admin.command('ping')
            
            self.db = self.client['battery_shop']
            
            # Collections
            self.inventory = self.db['inventory']
            self.bills = self.db['bills']
            self.customers = self.db['customers']
            
            # Initialize inventory if empty
            if self.inventory.count_documents({}) == 0:
                self.initialize_inventory()
            
            # Initialize invoice counters if not exists
            if not self.db.counters.find_one({'_id': 'gst_invoice_counter'}):
                self.db.counters.insert_one({'_id': 'gst_invoice_counter', 'seq': 1})
            if not self.db.counters.find_one({'_id': 'non_gst_invoice_counter'}):
                self.db.counters.insert_one({'_id': 'non_gst_invoice_counter', 'seq': 1})
        except ConnectionFailure:
            raise DatabaseError("Failed to connect to database. Please check your internet connection and database URL.")
        except Exception as e:
            raise DatabaseError(f"Database initialization error: {str(e)}")
    
    def get_next_invoice_number(self, bill_type):
        try:
            counter_id = 'gst_invoice_counter' if bill_type == 'gst' else 'non_gst_invoice_counter'
            counter = self.db.counters.find_one_and_update(
                {'_id': counter_id},
                {'$inc': {'seq': 1}},
                return_document=True
            )
            return counter['seq']
        except Exception as e:
            raise DatabaseError(f"Failed to generate invoice number: {str(e)}")
    
    def initialize_inventory(self):
        try:
            initial_products = [
                {'model': 'Black 600', 'quantity': 0},
                {'model': 'Black 700', 'quantity': 0},
                {'model': 'Harvest 90', 'quantity': 0},
                {'model': 'Z4L', 'quantity': 0},
                {'model': 'CRTT150', 'quantity': 0},
                {'model': 'Felix 1000', 'quantity': 0}
            ]
            self.inventory.insert_many(initial_products)
        except Exception as e:
            raise DatabaseError(f"Failed to initialize inventory: {str(e)}")
    
    def add_new_model(self, model):
        try:
            if not self.inventory.find_one({'model': model}):
                self.inventory.insert_one({'model': model, 'quantity': 0})
                return True
            return False
        except Exception as e:
            raise DatabaseError(f"Failed to add new model: {str(e)}")
    
    def update_inventory(self, model, quantity):
        try:
            self.inventory.update_one(
                {'model': model},
                {'$inc': {'quantity': quantity}}
            )
        except Exception as e:
            raise DatabaseError(f"Failed to update inventory: {str(e)}")
    
    def get_inventory(self):
        try:
            return list(self.inventory.find().sort('model', 1))
        except Exception as e:
            raise DatabaseError(f"Failed to get inventory: {str(e)}")
    
    def search_customers(self, name):
        try:
            return list(self.customers.find(
                {'name': {'$regex': name, '$options': 'i'}}
            ).sort('name', 1))
        except Exception as e:
            raise DatabaseError(f"Failed to search customers: {str(e)}")
    
    def get_customer(self, name):
        try:
            return self.customers.find_one({'name': name})
        except Exception as e:
            raise DatabaseError(f"Failed to get customer: {str(e)}")
    
    def save_customer(self, name, gstin=None):
        try:
            self.customers.update_one(
                {'name': name},
                {'$set': {'name': name, 'gstin': gstin}},
                upsert=True
            )
        except Exception as e:
            raise DatabaseError(f"Failed to save customer: {str(e)}")
    
    def save_bill(self, bill_data):
        try:
            bill_data['date'] = datetime.now()
            bill_data['invoice_number'] = self.get_next_invoice_number(bill_data['bill_type'])
            
            if bill_data['bill_type'] == 'gst' and bill_data['customer_name'] != 'Customer':
                self.save_customer(bill_data['customer_name'], bill_data.get('customer_gstin'))
            
            self.bills.insert_one(bill_data)
            return bill_data['invoice_number']
        except Exception as e:
            raise DatabaseError(f"Failed to save bill: {str(e)}")
    
    def update_bill(self, invoice_number, bill_data):
        try:
            old_bill = self.bills.find_one({'invoice_number': invoice_number})
            old_items = {item['model']: item['quantity'] for item in old_bill['items']} if old_bill else {}
            new_items = {item['model']: item['quantity'] for item in bill_data['items']}
            
            all_models = set(old_items.keys()) | set(new_items.keys())
            for model in all_models:
                old_qty = old_items.get(model, 0)
                new_qty = new_items.get(model, 0)
                diff = old_qty - new_qty
                if diff != 0:
                    self.update_inventory(model, diff)
            
            bill_data['date'] = datetime.now()
            self.bills.update_one(
                {'invoice_number': invoice_number},
                {'$set': bill_data}
            )
            
            if bill_data['bill_type'] == 'gst' and bill_data['customer_name'] != 'Customer':
                self.save_customer(bill_data['customer_name'], bill_data.get('customer_gstin'))
        except Exception as e:
            raise DatabaseError(f"Failed to update bill: {str(e)}")
    
    def delete_bill(self, invoice_number):
        try:
            bill = self.bills.find_one({'invoice_number': invoice_number})
            if bill:
                for item in bill['items']:
                    self.update_inventory(item['model'], item['quantity'])
                self.bills.delete_one({'invoice_number': invoice_number})
                return True
            return False
        except Exception as e:
            raise DatabaseError(f"Failed to delete bill: {str(e)}")
    
    def search_bills(self, customer_name=None, start_date=None, end_date=None):
        try:
            query = {}
            if customer_name:
                query['customer_name'] = {'$regex': customer_name, '$options': 'i'}
            if start_date and end_date:
                query['date'] = {
                    '$gte': start_date,
                    '$lte': end_date
                }
            return list(self.bills.find(query).sort('date', -1))
        except Exception as e:
            raise DatabaseError(f"Failed to search bills: {str(e)}") 