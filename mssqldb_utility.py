import pandas as pd
from sqlalchemy import create_engine, URL

class mssqldb:
    host = ""
    user = ""
    passwd = ""
    database = ""
    table = ""
    engine = None
    __message = "" 

    def __init__(self, _host, _database, _table, _user, _passwd):
        self.host = _host
        self.user = _user
        self.passwd = _passwd
        self.database = _database    
        self.table = _table
    
    def connectToDB(self):
        connect_url = URL.create(
            'mssql+pyodbc',
            username=self.user,
            password=self.passwd,
            host=self.host,
            database=self.database,
            query=dict(driver='ODBC Driver 17 for SQL Server'))
        
        self.engine = create_engine(
            url=connect_url,
            fast_executemany=True,
        )

        try:
            with self.engine.connect() as connection:
                return True
        except Exception as e:
            self.__message = str(e)
            return False
 
    def bulkSaveRecords(self, file):

        try:
            df = pd.read_csv(file, low_memory=False)      
            df.to_sql(con=self.engine, schema="dbo", name=self.table, if_exists="append", index=False, chunksize=1000)                  
            self.__message = "Record inserted successful"
            return True
        except Exception as e:
            self.__message = str(e)
            return False

    def disconnectFromDB(self):
        self.engine.dispose()

    def get_message(self):
        return self.__message
