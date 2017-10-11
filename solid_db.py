from bson import ObjectId
import inflect
import time
from tinydb import TinyDB, Query, where


def current_time():
    '''Return a nice date/time string.'''
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


class SolidDB(object):

    def __init__(self, store_name):
        '''Connect to instance of TinyDB.'''
        self.db = TinyDB(store_name)
        self.pluralize = inflect.engine().plural_noun

    def get_id(self):
        '''Generate an object ID string.'''
        return str(ObjectId())

    def insert(self, model_name, data):
        '''Insert data into table.'''
        table_name = self.pluralize(model_name)
        data['_id'] = self.get_id()
        data['_model'] = table_name
        data['createdAt'] = current_time()
        data['updatedAt'] = current_time()
        self.db.table(table_name).insert(data)
        return data

    @property
    def tables(self):
        '''Return available tables.'''
        return filter(lambda x: x[0] != '_', self.db.tables())

    def update(self, new_doc, _id=None):
        '''Update the current document.'''
        if _id is None and '_id' not in new_doc:
            print('No _id is present | Not updating')
            return False
        _id = _id if _id else new_doc['_id']
        current_doc = self.find_by_id(_id)
        table = self.db.table(current_doc['_model'])
        q = Query()
        new_doc['updatedAt'] = current_time()
        table.update(new_doc, q._id==_id)
        current_doc.update(new_doc)
        return current_doc

    def find_where(self, table, key, value):
        # Grab matching elements from table.
        table = self.db.table(table)
        q = Query()
        return table.search(where(key)==value)

    def delete(self, _id):
        '''Delete the document.'''
        doc = self.find_by_id(_id)
        table = self.db.table(doc['_model'])
        q = Query()
        table.remove(q._id == _id)

    def find_by_id(self, _id):
        '''Find document with corresponding ID.'''
        q = Query()
        for table in self.tables:
            docs = self.db.table(table).search(q._id == _id)
            if len(docs)>0:
                return docs[0]
        return {}

    def all(self, table_name):
        '''List all models.'''
        table = self.db.table(table_name)
        models = table.all()
        if len(models) == 0:
            self.db.purge_table(table_name)
        return models


if __name__ == '__main__':
    db = SolidDB('data/db.json')

