import sqlite3
from shinymud.config import DB_NAME    


class DB(object):
    def __init__(self):
        self.conn  = sqlite3.Connection(DB_NAME)
    
    def insert(self, query, params=None):
        """Insert a new row into a table.
        If successful, return the id of the new row.
        If there is a problem with the query, it will raise an exception.
        If the insert violates a database constraint, it will raise an exception.
         
        ex:
            db = DB()
            new_id = db.insert("into table mytable (field1, field2...) values (?, ?...)", [val1, val2...])
        """
        cursor = self.conn.cursor()
        if params:
            cursor.execute("insert " + query, params)
        else:
            cursor.execute("insert " + query)
        new_id = cursor.lastrowid
        self.conn.commit()
        return new_id
    
    def insert_from_dict(self, table, d):
        query = "INTO " + table + " "
        keys = []
        values = []
        for key,val in d.items():
            keys.append(key)
            values.append(val)
        key_string = "(" + ",".join(keys) + ")"
        val_string = "(" + ",".join(['?' for _ in values]) + ")"
        query = query + key_string + " VALUES " + val_string
        self.insert(query, values) 
        
    def select(self, query, params=None):
        """Fetch data from the database.
        If the select is successful, it returns a list of dictionaries.
        If there are no rows to return, it returns an empty list.
        If there is a problem with the query, it will raise an exception.
         
        ex:
            db = DB()
            rows = db.select("* from mytable where field1=?", [val1])
            print rows
            > [{'field1': somevalue, 'field2', someothervalue...}, {'field1':...}...]
        """
        cursor = self.conn.cursor()
        if params:
            cursor.execute("select " + query, params)
        else:
            cursor.execute("select " + query)
        keys = [_[0] for _ in cursor.description]
        rows = [dict([(keys[i], vals[i]) for i in range(len(keys))]) for vals in cursor.fetchall()]
        return rows
    
    def update(self, query, params=None):
        """Change data in the database.
        If successful, returns the number of rows updated (may be zero if no matches).
        If there is a problem with the query, it will raise an exception.
        """
        cursor = self.conn.cursor()
        if params:
            cursor.execute("update " + query, params)
        else:
            cursor.execute("update " + query)
        return cursor.rowcount
    
    def delete(self, query, params=None):
        """Delete rows from a table.
        If successful, returns the number of rows deleted (may be zero if no matches).
        If there is a problem with the query, it will raise an exception.
        """
        cursor = self.conn.cursor()
        if params:
            cursor.execute("delete " + query, params)
        else:
            cursor.execute("delete " + query)
        return cursor.rowcount
    