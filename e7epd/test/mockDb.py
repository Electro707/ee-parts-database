import logging
from copy import deepcopy

class MockDbCollection:
    def __init__(self, name: str, documents=None):
        self.log = logging.getLogger(f'mockDB.{name}')
        self.documents = deepcopy(documents or [])

    @staticmethod
    def _matches(document, query):
        if not query:
            return True

        return all(document.get(key) == value for key, value in query.items())

    def count_documents(self, query=None):
        self.log.debug(f"Returning document count with query {query}")
        return sum(self._matches(doc, query) for doc in self.documents)

    def find_one(self, query=None):
        self.log.debug(f"Finding one document with query {query}")
        for doc in self.documents:
            if self._matches(doc, query):
                return deepcopy(doc)

        return None

    def find(self, query=None):
        self.log.debug(f"Finding documents with query {query}")
        return [deepcopy(doc) for doc in self.documents if self._matches(doc, query)]

    def find_one_and_update(self, query=None, toUpdate=None):
        self.log.debug(f"Finding document with query {query} and updating with {toUpdate}")
        for doc in self.documents:
            if not self._matches(doc, query):
                continue
            for u in toUpdate:
                if u == '$set':
                    for key in toUpdate[u]:
                        doc[key] = toUpdate[u][key]
                else:
                    doc[u] = toUpdate[u]

    def insert_one(self, document):
        self.log.debug(f"Inserting document {document}")
        self.documents.append(deepcopy(document))

    def delete_one(self, query):
        self.log.debug(f"Deleting query {query}")


class MockDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):

        fakeData = None
        if name == 'parts':
            fakeData = [{'ipn': 'TEST-PART',
                         'stock': 3, 'type': 'ic',
                         'mfg_part_numb': 'TEST-PART-MFG',
                         'ic_type': 'TEST',
                         'manufacturer': 'e707',
                         'package': 'tht',
                         'storage': '',
                         'comments': '',
                         'datasheet': '',
                         'user': '',
                         }]

        if name not in self.collections:
            self.collections[name] = MockDbCollection(name, fakeData)

        return self.collections[name]