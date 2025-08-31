import psycopg2
import os
import sys

from configparser import ConfigParser
from psycopg2 import pool  # Explicitly import the pool module

"""
This file contains the utility to connect to the postgres database
and perform certain sql queries.
"""


class DB_connect:
    def __init__(self):
        self.pool = None
        self._connect()  # Call the internal connection method during initialization

    def _load_config(self, filename: str = 'database.ini', section: str = 'postgresql') -> dict:
        """
        Load database configuration from the file
        :param filename: name of the configuration file
        :param section: section of database configuration
        :return: a dictionary of database parameters
        """

        parser = ConfigParser()
        # Look for database.ini in the project root or current directory
        script_dir = os.path.dirname(__file__)
        project_root_dir = os.path.abspath(os.path.join(script_dir, '..')) # Adjust if your database.ini is higher up
        
        config_paths = [
            os.path.join(script_dir, filename), # Current directory
            os.path.join(project_root_dir, filename), # Project root
            # Add other potential paths if needed
        ]
        
        found_config = False
        for path in config_paths:
            if os.path.exists(path):
                if parser.read(path):
                    found_config = True
                    print(f"Loaded database configuration from: {path}")
                    break
        
        if not found_config:
            raise Exception(f"Configuration file '{filename}' not found in expected paths: {config_paths}")

        config = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                config[param[0]] = param[1]
        else:
            raise Exception(f'Section {section} not found in the {filename} file')

        return config

    def _connect(self):
        """
        Connect to the PostgreSQL database server and create a connection pool.
        This pool will remain open until explicitly closed by the class instance.
        :return: None
        """

        try:
            config_params = self._load_config()

            self.pool = pool.SimpleConnectionPool(minconn=1,
                                                    maxconn=10,
                                                    **config_params
                                                    )
            print("Connection Pooling to PostgreSQL DB successful")

        except (psycopg2.DatabaseError, Exception) as e:
            print(f"Error occurred while connecting to PostgreSQL DB: {e}")
            self.pool = None

    def get_connection(self):
        """
        Retrieves a connection from the pool.
        :return: A psycopg2 connection object or None if an error occurs.
        """
        if self.pool:
            try:
                conn = self.pool.getconn()
                return conn
            except Exception as e:
                print(f"Error getting connection from pool: {e}")
                return None
        print("Connection pool is not initialized.")
        return None

    def put_connection(self, conn):
        """
        Returns a connection to the pool.
        :param conn: The psycopg2 connection object to return.
        :return: None
        """
        if self.pool and conn:
            try:
                self.pool.putconn(conn)
            except Exception as e:
                print(f"Error putting connection back to pool: {e}")
        elif not self.pool:
            print("Connection pool is not initialized, cannot return connection.")


    def closeall(self):
        """
        Closes all connections in the pool.
        :return: None
        """

        if self.pool:
            self.pool.closeall()
            print("Connection pool to PostgreSQL DB closed.")
            self.pool = None


"""
Test code for the class, this will be executed when the file is run directly.
This is not recommended for production use.
"""
if __name__ == '__main__':
    # Create an instance of DB_connect
    db_instance = DB_connect()

    # Check if the connection pool was successfully created before using it
    if db_instance.pool:
        conn = None
        try:
            # Get a connection from the pool to test
            print("Attempting to get a connection from the pool...")
            conn = db_instance.get_connection() # Use the new method
            print("Successfully retrieved a connection from the pool.")

            # It's good practice to perform a simple query to verify the connection is live
            if conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT version();')
                    db_version = cur.fetchone()
                    print(f"Database connection verified. Version: {db_version[0]}")
            else:
                print("Could not get a connection from the pool.")

        except (psycopg2.Error, Exception) as e:
            print(f"An error occurred while using the connection: {e}")

        finally:
            # Return the connection to the pool if it was acquired
            if conn:
                db_instance.put_connection(conn) # Use the new method
                print("Connection returned to the pool.")
            # Close all connections in the pool when the script is done
            db_instance.closeall()
    else:
        print("Failed to create a database connection pool. Please check configuration and database status.")