
import sqlite3
import os


class db:
    def __init__(self, path_to_db):
        self.conn = sqlite3.connect(path_to_db)
        self.cn = self.conn.cursor()
        self.conn.commit()

    def __exit__(self, ext_type, exc_value, traceback):
        self.cursor.close()
        if isinstance(exc_value, Exception):
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()
        print('Database closed')

    def create_db(self):
        self.cn.execute(
            "CREATE TABLE items(asin NVARCHAR(50) , domain NVARCHAR(10), price FLOAT, discount FLOAT, PRIMARY KEY (asin, domain))")
        self.conn.commit()
        print('Db created')
        return True

    def count_items(self):
        """Print items from db"""
        self.cn.execute("SELECT count(*) FROM items")
        print(self.cn.fetchall())

    def update_item(self, item):
        self.cn.execute("UPDATE items SET price=" +
                        str(item['price'])+", discount=" +
                        str(item['discount']) + " WHERE asin='"+str(item['asin'])+"' AND domain='"+str(item['domain'])+"'")
        self.conn.commit()

    def insert_item(self, item):
        self.cn.execute(
            "INSERT INTO items (asin,domain,price,discount) VALUES ('"+str(item['asin'])+"','"+str(
                item['domain'])+"',"+str(item['price'])+","+str(item['discount'])+")")
        self.conn.commit()

    def save_or_update(self, items):
        if items is not None or len(items) > 0:
            for item in items:
                self.cn.execute(
                    "SELECT * FROM items WHERE asin='"+str(item['asin'])+"' AND domain='"+str(item['domain'])+"'")
                if self.cn.fetchone() is None:
                    self.insert_item(item)
                else:
                    self.update_item(item)
            self.conn.commit()

    def save_items(self, items):
        """Save items to db"""
        self.cn.executemany(
            'INSERT INTO items (asin,domain,price,discount) VALUES (?,?,?,?)', items)
        self.conn.commit()
        print('Data saved')

    def print_items(self):
        """Print items from db"""
        self.cn.execute("SELECT * FROM items LIMIT 200;")
        print(self.cn.fetchall())

    def print_discount(self):
        """Print items from db"""
        self.cn.execute(
            "SELECT * FROM items WHERE discount > 0 LIMIT 200")
        print(self.cn.fetchall())

    def get_price(self, item):
        price = self.cn.execute(
            "SELECT price FROM items WHERE asin='"+str(item['asin'])+"' AND domain='"+str(item['domain'])+"'")
        p = price.fetchone()
        if p is not None and len(p) > 0:
            # print(p)
            return p[0]
        else:
            # print('No price found '+str(asin))
            return 0

    def get_discount(self, item):
        price = self.cn.execute(
            "SELECT discount FROM items WHERE asin='"+str(item['asin'])+"' AND domain='"+str(item['domain'])+"'")
        p = price.fetchone()
        if p is not None and len(p) > 0:
            # print(p)
            return p[0]
        else:
            # print('No price found '+str(asin))
            return 0
