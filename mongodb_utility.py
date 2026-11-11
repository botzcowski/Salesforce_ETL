from pymongo import MongoClient, InsertOne, DeleteMany, ReplaceOne, UpdateOne
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, BulkWriteError
import json

class mongodb:
    URL = ""
    user = ""
    passwd = ""
    database = ""
    client = None
    __message = "" 

    def __init__(self, _url, _database, _user, _passwd):
        self.URL = _url
        self.user = _user
        self.passwd = _passwd
        self.database = _database    
    
    def connectToDB(self):
        self.client = MongoClient("mongodb://" + self.user + ":" + self.passwd + "@" + self.URL + "/" + self.database, connectTimeoutMS=5000, socketTimeoutMS=120000, serverSelectionTimeoutMS=120000)

        try:
            self.client[self.database].list_collection_names()
            return True
        except Exception as e:
            self.__message = str(e)
            return False
 
    def saveRecord(self, collection, query, recid, document):
        try:
            db = self.client[self.database]
            if query is not None:
                db[collection].delete_one(query)
            
            db[collection].update_one({ '_id': recid }, { '$set': { 'record': document } }, upsert=True)
            self.__message = "Document inserted successful for " + recid
            return True
        except Exception as e:
            self.__message = str(e)
            return False

    def bulkSaveRecords(self, collection, keys, documents):
        try:
            requests=[UpdateOne({'_id':idn}, {'$set':data}, upsert=True) for idn, data in zip(keys, documents)]
            db = self.client[self.database]
            db[collection].bulk_write(requests)
            self.__message = "Documents inserted successful"
            return True
        except BulkWriteError as e:
            self.__message = str(e)
            return False

    def get_message(self):
        return self.__message