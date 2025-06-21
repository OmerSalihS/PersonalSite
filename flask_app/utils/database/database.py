import os
import glob
import json
import csv
from io import StringIO
import itertools
import datetime
import hashlib
from cryptography.fernet import Fernet

# Import database connectors based on environment
DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"Environment check - DATABASE_URL: {'SET' if DATABASE_URL else 'NOT SET'}")
print(f"Available env vars starting with 'DATA': {[k for k in os.environ.keys() if k.startswith('DATA')]}")
print(f"Available env vars starting with 'RENDER': {[k for k in os.environ.keys() if k.startswith('RENDER')]}")

# Try to import based on environment
try:
    if DATABASE_URL:
        # Production (Render) - use PostgreSQL
        import psycopg2
        import psycopg2.extras
        from urllib.parse import urlparse
        mysql = None
        print(f"Using PostgreSQL in production. DATABASE_URL detected: {DATABASE_URL[:20]}...")
    else:
        # Development - use MySQL
        import mysql.connector
        psycopg2 = None
        print("Using MySQL in development. No DATABASE_URL detected.")
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback: try PostgreSQL first, then MySQL
    try:
        import psycopg2
        import psycopg2.extras
        from urllib.parse import urlparse
        mysql = None
        print("Fallback: Using PostgreSQL")
    except ImportError:
        try:
            import mysql.connector
            psycopg2 = None
            print("Fallback: Using MySQL")
        except ImportError:
            print("ERROR: Neither psycopg2 nor mysql.connector available!")
            raise

class database:

    def __init__(self, purge=False):
        # Check if we're on Render (has DATABASE_URL)
        self.is_production = bool(DATABASE_URL)
        
        if self.is_production:
            # Parse DATABASE_URL for PostgreSQL
            url = urlparse(DATABASE_URL)
            self.database = url.path[1:]  # Remove leading slash
            self.host = url.hostname
            self.user = url.username
            self.port = url.port or 5432
            self.password = url.password
        else:
            # Local MySQL settings
            self.database = 'db'
            self.host = '127.0.0.1'
            self.user = 'master'
            self.port = 3306
            self.password = 'master'
        
        # Encryption settings
        self.encryption = {
            'oneway': {
                'salt': b'averysaltysailortookalongwalkoffashortbridge',
                'n': 2**5,  # CPU/memory cost factor
                'r': 9,     # Block size factor
                'p': 1      # Parallelization factor
            },
            'reversible': {
                'key': '7pK_fnSKIjZKuv_Gwc--sZEMKn2zc8VvD6zS96XcNHE='
            }
        }
        
        self.createTables(purge=purge, data_path='flask_app/database/')

    def query(self, query="SELECT CURRENT_DATE", parameters=None):
        if self.is_production:
            # PostgreSQL connection
            cnx = psycopg2.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                database=self.database
            )
            
            cur = cnx.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if parameters is not None:
                cur.execute(query, parameters)
            else:
                cur.execute(query)
            
            # Fetch results
            try:
                row = cur.fetchall()
                # Convert RealDictRow to regular dict
                row = [dict(r) for r in row]
            except:
                row = []
            
            cnx.commit()
            
            if "INSERT" in query.upper() and "RETURNING" not in query.upper():
                # For PostgreSQL, we need to modify INSERT queries to return the ID
                if "INSERT INTO" in query.upper():
                    # This is a bit hacky, but for compatibility
                    pass
            
            cur.close()
            cnx.close()
            return row
        else:
            # MySQL connection (original code)
            cnx = mysql.connector.connect(host=self.host,
                                          user=self.user,
                                          password=self.password,
                                          port=self.port,
                                          database=self.database,
                                          charset='latin1'
                                         )

            if parameters is not None:
                cur = cnx.cursor(dictionary=True)
                cur.execute(query, parameters)
            else:
                cur = cnx.cursor(dictionary=True)
                cur.execute(query)

            # Fetch one result
            row = cur.fetchall()
            cnx.commit()

            if "INSERT" in query:
                cur.execute("SELECT LAST_INSERT_ID()")
                row = cur.fetchall()
                cnx.commit()
            cur.close()
            cnx.close()
            return row

    def about(self, nested=False):    
        query = """select concat(col.table_schema, '.', col.table_name) as 'table',
                          col.column_name                               as column_name,
                          col.column_key                                as is_key,
                          col.column_comment                            as column_comment,
                          kcu.referenced_column_name                    as fk_column_name,
                          kcu.referenced_table_name                     as fk_table_name
                    from information_schema.columns col
                    join information_schema.tables tab on col.table_schema = tab.table_schema and col.table_name = tab.table_name
                    left join information_schema.key_column_usage kcu on col.table_schema = kcu.table_schema
                                                                     and col.table_name = kcu.table_name
                                                                     and col.column_name = kcu.column_name
                                                                     and kcu.referenced_table_schema is not null
                    where col.table_schema not in('information_schema','sys', 'mysql', 'performance_schema')
                                              and tab.table_type = 'BASE TABLE'
                    order by col.table_schema, col.table_name, col.ordinal_position;"""
        results = self.query(query)
        if nested == False:
            return results

        table_info = {}
        for row in results:
            table_info[row['table']] = {} if table_info.get(row['table']) is None else table_info[row['table']]
            table_info[row['table']][row['column_name']] = {} if table_info.get(row['table']).get(row['column_name']) is None else table_info[row['table']][row['column_name']]
            table_info[row['table']][row['column_name']]['column_comment'] = row['column_comment']
            table_info[row['table']][row['column_name']]['fk_column_name'] = row['fk_column_name']
            table_info[row['table']][row['column_name']]['fk_table_name'] = row['fk_table_name']
            table_info[row['table']][row['column_name']]['is_key'] = row['is_key']
            table_info[row['table']][row['column_name']]['table'] = row['table']
        return table_info

    def createTables(self, purge=False, data_path='flask_app/database/'):
        """
        (1) Optionally drops existing tables (if purge==True).
        (2) Creates tables by running all .sql files in data_path/create_tables.
        (3) Inserts initial data from all .csv files in data_path/initial_data.
        """
        print('----- createTables() -----')
        if purge:
            print('Purging (dropping) existing tables...')
            
            if self.is_production:
                # PostgreSQL: Drop tables in reverse dependency order
                for table in ['skills', 'experiences', 'positions', 'institutions', 'feedback', 'users']:
                    try:
                        self.query(f"DROP TABLE IF EXISTS {table} CASCADE")
                        print(f"Dropped table {table}")
                    except Exception as e:
                        print(f"Error dropping {table}: {str(e)}")
            else:
                # MySQL: Temporarily turn off foreign key checks
                self.query("SET FOREIGN_KEY_CHECKS=0")
                for table in ['skills', 'experiences', 'positions', 'institutions', 'feedback', 'users']:
                    try:
                        self.query(f"DROP TABLE IF EXISTS {table}")
                        print(f"Dropped table {table}")
                    except Exception as e:
                        print(f"Error dropping {table}: {str(e)}")
                self.query("SET FOREIGN_KEY_CHECKS=1")
            print("Done purging!")

        # Create tables in the correct order
        table_order = ['users', 'institutions', 'positions', 'experiences', 'skills', 'feedback']
        for table in table_order:
            try:
                print(f"Running {data_path}create_tables/{table}.sql")
                with open(data_path + f"create_tables/{table}.sql") as read_file:
                    create_statement = read_file.read()
                self.query(create_statement)
            except Exception as e:
                print(f"Error executing SQL: {str(e)}")
                print(f"Problematic statement: {create_statement}")

        # Insert initial data
        for table in table_order:
            try:
                print(f"Inserting data into '{table}' from '{data_path}initial_data/{table}.csv'")
                params = []
                with open(data_path + f"initial_data/{table}.csv") as read_file:
                    scsv = read_file.read()            
                for row in csv.reader(StringIO(scsv), delimiter=','):
                    params.append(row)
            
                # Insert the data
                cols = params[0]; params = params[1:] 
                self.insertRows(table=table, columns=cols, parameters=params)
            except Exception as e:
                print(f"Error inserting into {table}: {str(e)}")
                if 'params' in locals() and len(params) > 0:
                    print(f"Problematic row: {params[0]}")
                else:
                    print('no initial data')

        print("----- Done creating and populating tables -----")

    def get_drop_order(self, dependencies):
        """
        Determine the order to drop tables based on dependencies.
        """
        result = []
        visited = set()
        temp_mark = set()
        
        def visit(node):
            if node in temp_mark:
                # We have a circular dependency
                return
            if node in visited:
                return
                
            temp_mark.add(node)
            
            # Visit all dependencies
            for dep in dependencies.get(node, set()):
                visit(dep)
                
            temp_mark.remove(node)
            visited.add(node)
            result.append(node)
        
        # Visit all nodes
        for node in dependencies:
            if node not in visited:
                visit(node)
                
        return result

    def insertRows(self, table='table', columns=['x', 'y'], parameters=[['v11', 'v12'], ['v21', 'v22']]):
        """
        Inserts each row in `parameters` into `table`, 
        matching each row to the list of `columns`.
        """
        # Build the "INSERT INTO tablename (col1, col2, ...) VALUES (%s, %s, ...)"
        placeholders = ", ".join(["%s"] * len(columns))
        
        if self.is_production:
            # PostgreSQL: Use double quotes for identifiers
            col_names = ", ".join([f'"{c}"' for c in columns])
            sql = f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders})'
        else:
            # MySQL: Use backticks for identifiers
            col_names = ", ".join([f"`{c}`" for c in columns])
            sql = f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})"

        # Insert each row
        for row in parameters:
            cleaned = []
            for val in row:
                if isinstance(val, str) and val.strip().upper() in ("NULL", ""):
                    cleaned.append(None)
                else:
                    cleaned.append(val)
            try:
                self.query(sql, cleaned)
            except Exception as err:
                print(f"Error inserting into {table}: {err}")
                print(f"Problematic row: {cleaned}")

    def getResumeData(self):
        """
        Returns a nested dictionary that represents the complete data
        """
        # Get all institutions
        institutions_query = "SELECT * FROM institutions"
        institutions = self.query(institutions_query)
        
        result = {}
        
        for inst in institutions:
            inst_id = inst['inst_id']
            result[inst_id] = inst
            result[inst_id]['positions'] = {}
            
            # Get positions for this institution
            positions_query = "SELECT * FROM positions WHERE inst_id = %s"
            positions = self.query(positions_query, (inst_id,))
            
            for pos in positions:
                pos_id = pos['position_id']
                result[inst_id]['positions'][pos_id] = pos
                result[inst_id]['positions'][pos_id]['experiences'] = {}
                
                # Get experiences for this position
                experiences_query = "SELECT * FROM experiences WHERE position_id = %s"
                experiences = self.query(experiences_query, (pos_id,))
                
                for exp in experiences:
                    exp_id = exp['experience_id']
                    result[inst_id]['positions'][pos_id]['experiences'][exp_id] = exp
                    result[inst_id]['positions'][pos_id]['experiences'][exp_id]['skills'] = {}
                    
                    # Get skills for this experience
                    skills_query = "SELECT * FROM skills WHERE experience_id = %s"
                    skills = self.query(skills_query, (exp_id,))
                    
                    for skill in skills:
                        skill_id = skill['skill_id']
                        result[inst_id]['positions'][pos_id]['experiences'][exp_id]['skills'][skill_id] = skill
            
        return result

    def createUser(self, email='me@email.com', password='password', role='user', name='User'):
        """
        Create a new user in the database.
        
        Args:
            email (str): User's email address
            password (str): User's password (will be encrypted)
            role (str): User's role ('guest' or 'owner')
            name (str): User's name
            
        Returns:
            dict: Information about success or failure of user creation
                {'success': 1} if successful, {'success': 0, 'message': 'error message'} if failed
        """
        try:
            # First check if user already exists
            existing_user = self.query("SELECT * FROM users WHERE email = %s", (email,))
            if existing_user:
                return {'success': 0, 'message': 'User already exists'}
            
            # Encrypt the password
            encrypted_password = self.onewayEncrypt(password)
            
            # Create new user
            self.query(
                "INSERT INTO users (email, password, role, name) VALUES (%s, %s, %s, %s)",
                (email, encrypted_password, role, name)
            )
            return {'success': 1}
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return {'success': 0, 'message': str(e)}
        
    def authenticate(self, email='me@email.com', password='password'):
        """
        Authenticate a user by checking if the email and password combination exists.
        
        Args:
            email (str): User's email address
            password (str): User's password (will be encrypted and compared)
            
        Returns:
            dict: Information about success or failure of authentication
                {'success': 1, 'role': 'user_role', 'name': 'user_name'} if successful, 
                {'success': 0, 'message': 'error message'} if failed
        """
        try:
            # Encrypt the provided password
            encrypted_password = self.onewayEncrypt(password)
            
            # Check if the email and encrypted password combination exists
            user = self.query(
                "SELECT * FROM users WHERE email = %s AND password = %s", 
                (email, encrypted_password)
            )
            
            if user:
                return {'success': 1, 'role': user[0]['role'], 'name': user[0]['name']}
            else:
                return {'success': 0, 'message': 'Invalid email or password'}
        except Exception as e:
            print(f"Error authenticating user: {str(e)}")
            return {'success': 0, 'message': str(e)}

    def onewayEncrypt(self, string):
        """
        Encrypt a string using scrypt (one-way encryption).
        
        Args:
            string (str): The string to encrypt
            
        Returns:
            str: The encrypted string in hexadecimal format
        """
        encrypted_string = hashlib.scrypt(
            string.encode('utf-8'),
            salt=self.encryption['oneway']['salt'],
            n=self.encryption['oneway']['n'],
            r=self.encryption['oneway']['r'],
            p=self.encryption['oneway']['p']
        ).hex()
        return encrypted_string

    def reversibleEncrypt(self, type, message):
        fernet = Fernet(self.encryption['reversible']['key'])
        
        if type == 'encrypt':
            message = fernet.encrypt(message.encode())
        elif type == 'decrypt':
            message = fernet.decrypt(message).decode()

        return message
