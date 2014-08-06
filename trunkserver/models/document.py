import sys

from tornado.gen import coroutine, Return

from fields import *
from base import BaseDocument, DocumentMetaclass, ValidationError
from backends import get_db
from defines import coroutineDebug

class QNode(object):
    nodeDict = {}

    def toExpress(self, docCls):
        pass

class BaseQNode(QNode):
    mDict = {}

    def __init__(self, **kwargs):
        self.mDict = kwargs

    def toExpress(self, docCls):
        return docCls.query_to_db(self.mDict)

class OrQNode(QNode):
    mNode = None

    def __init__(self, node):
        if not isinstance(node, QNode):
            raise AssertionError("INVALID PARMS WHEN INIT QNode")
        self.mNode = node

    def toExpress(self, docCls):
        return {"$or":self.mNode.toExpress(docCls)}

class ListQNode(QNode):
    mList = []

    def __init__(self, nodelist):
        if not isinstance(nodelist, list) and filter(lambda node:not isinstance(node, QNode), nodelist):
            raise AssertionError("INVALID PARMS WHEN INIT QNode")
        self.mList = nodelist

    def toExpress(self, docCls):
        return [node.toExpress(docCls) for node in self.mList]



class Document(BaseDocument):
    __metaclass__ = DocumentMetaclass

    id = ObjectIdField(db_field="_id")
    _collection = None
    canSave = True

    @property
    def pk(self):
        return self.id

    @pk.setter
    def pk(self, value):
        self.id = value

    @classmethod
    def get_collection(cls):
        if not cls._collection:
            cls._collection = get_db(cls.db_alias)[cls._get_collection_name()]
        return cls._collection

    def to_client(self):
        data = {}
        cls = self.__class__
        for key in self:
            #don't return innerData to client.
            if getattr(cls, key, None) and getattr(cls, key).innerData:
                continue
            data[key] = str(self[key]) if isinstance(self[key], ObjectId) else self[key]
        return data

    def delete(self, callback):
        self.__class__.objects(id=self.pk).delete(callback=callback)

    def upsert(self, callback=None):
        spec = {}
        if self.id:
            spec["_id"] = self.id
        self.get_collection().update(spec, self.to_mongo(), callback=callback, upsert=True)

    @coroutineDebug
    @coroutine
    def save(self, force_insert=False):
        if not self.canSave:
            raise ValidationError("DOC CAN'T BE SAVE NOW")
        try:
            self.validate()

            if force_insert:
                self.id = ""
            dbdoc = self.to_mongo()
        except Exception, e:
            print "save error when validate:", e.message
            raise Return(None)
        result = yield self.get_collection().save(dbdoc)
        self.update_from_db(dbdoc)
        raise Return(result)

    @coroutineDebug
    @coroutine
    def remove(self):
        if self.id:
            resp = yield self.__class__.removeDoc(id=self.id)
            raise Return(resp)
        else:
            print "remove error"

    @classmethod
    @coroutineDebug
    @coroutine
    def removeDoc(cls, **query):
        if not query:
            return
        dbquery = cls.query_to_db(query)
        result = yield cls.get_collection().remove(dbquery)
        raise Return(result)

    @classmethod
    @coroutineDebug
    @coroutine
    def get(cls, str_id):
        query = {"_id":str_id} if isinstance(str_id, ObjectId) else {"_id":ObjectId(str_id)}
        resp = yield cls.get_collection().find_one(query)
        resp = cls.from_db(resp) if resp else None
        raise Return(resp)

    @classmethod
    @coroutineDebug
    @coroutine
    def findOne(cls, **kwargs):
        dbquery = cls.query_to_db(kwargs)
        resp = yield cls.get_collection().find_one(dbquery)
        resp = cls.from_db(resp) if resp else None
        raise Return(resp)

    @classmethod
    @coroutineDebug
    @coroutine
    def findMul(cls, fr, num, **kwargs):
        '''
        this query allow key-value only.
        :param fr:
        :param num:
        :param query:
        :return:
        '''
        dbquery = cls.query_to_db(kwargs)
        resp = yield cls.get_collection().find(dbquery).skip(fr).limit(num).to_list(num)
        raise Return([cls.from_db(item) for item in resp])

    @classmethod
    @coroutineDebug
    @coroutine
    def query(cls, fr, num, qnode):
        dbquery = qnode.toExpress(cls)
        resp = yield cls.get_collection().find(dbquery).skip(fr).limit(num).to_list(num)
        raise Return([cls.from_db(item) for item in resp])

    @classmethod
    def from_db(cls, dbDoc):
        if not dbDoc:
            return None
        obj = cls()
        obj.update_from_db(dbDoc)
        return obj

    def update_from_db(self, dbDoc):
        if not dbDoc:
            return

        try:
            for key in self:
                dbkey = getattr(self.__class__, key).db_field if getattr(self.__class__, key, None) else key
                if dbkey in dbDoc:
                    self[key] = dbDoc[dbkey]
        except ValidationError, e:
            self.canSave = False
            print "****VALIDERROR WHEN UPDATE FROM DB : ", e.message


    @classmethod
    def query_to_db(cls, query):
        dbQuery = {}
        if query:
            for k in query.keys():
                try:
                    if getattr(cls, k, None) and getattr(cls, k).db_field:
                        dbQuery[getattr(cls, k).db_field] = query[k]
                    else:
                        dbQuery[k] = query[k]
                except Exception, e:
                    print "query to db error", e.toString()

        return dbQuery


class EmbeddedDocument(BaseDocument):
    __metaclass__ = DocumentMetaclass

    def __delattr__(self, *args, **kwargs):
        """Handle deletions of fields"""
        field_name = args[0]
        if field_name in self._fields:
            default = self._fields[field_name].default
            if callable(default):
                default = default()
            setattr(self, field_name, default)
        else:
            super(EmbeddedDocument, self).__delattr__(*args, **kwargs)
