#encoding=utf-8
import sys

from tornado.gen import coroutine, Return

from fields import *
from base import BaseDocument, DocumentMetaclass, ValidationError
from backends import get_db
from defines import coroutineDebug
from mylog import mylog

def qAnd(*args):
    query = {}
    for arg in args:
        if isinstance(arg, dict):
            query.update(arg)
    return query

class QNode(object):
    nodeDict = {}

    def toExpress(self, docCls):
        pass

class BaseQNode(QNode):
    mDict = {}

    def __init__(self, **kwargs):
        self.mDict = kwargs

    def toExpress(self, docCls):
        return docCls.query_dict_to_db(self.mDict)



class QIn(QNode):
    mDict = {}

    def __init__(self, **kwargs):
        self.mDict = kwargs

    def toExpress(self, docCls):
        return dict([(k, {"$in": v}) for k, v in self.mDict.items()])

class QLess(QNode):
    mNode = None

    def __init__(self, node):
        if not isinstance(node, BaseQNode):
            raise AssertionError("INVALID PARMS WHEN INIT QNode")
        self.mNode = node

    def toExpress(self, docCls):
        return dict([(k, {"$lt":v}) for k,v in self.mNode.toExpress(docCls).items()])

class QGt(QNode):
    mNode = None

    def __init__(self, node):
        if not isinstance(node, BaseQNode):
            raise AssertionError("INVALID PARMS WHEN INIT QNode")
        self.mNode = node

    def toExpress(self, docCls):
        return dict([(k, {"$gt":v}) for k,v in self.mNode.toExpress(docCls).items()])

class QSize(QNode):
    mNode = None

    def __init__(self, node):
        if not isinstance(node, BaseQNode):
            raise AssertionError("INVALID PARMS WHEN INIT QNode")
        self.mNode = node

    def toExpress(self, docCls):
        return dict([(k, {"$size":v}) for k,v in self.mNode.toExpress(docCls).items()])

class QOr(QNode):
    mNodeList = None

    def __init__(self, *nodes):
        if len(nodes) == 0:
            raise AssertionError("INVALID PARMS WHEN INIT QNode")
        self.mNodeList = nodes

    def toExpress(self, docCls):
        return {"$or":[node.toExpress(docCls) for node in self.mNodeList]}

class QAnd(QNode):
    mNodeList = None

    def __init__(self, *nodes):
        if len(nodes) == 0:
            raise AssertionError("INVALID PARMS WHEN INIT QNode")
        self.mNodeList = nodes

    def toExpress(self, docCls):
        query = {}
        for node in self.mNodeList:
            query.update(node.toExpress(docCls))
        return query



class Document(BaseDocument):
    __metaclass__ = DocumentMetaclass

    id = ObjectIdField(db_field="_id")
    _collection = None

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
            if cls._fields[key].innerData or self[key] is None:
                continue
            data[key] = cls._fields[key].to_client(self[key])
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

        self.validate()

        if force_insert:
            self.id = ""
        try:
            dbdoc = self.to_mongo()
        except Exception, e:
            mylog.getlog().error("save error when validate"+e.message)
            raise Return(None)
        result = yield self.get_collection().save(dbdoc)
        self.update_from_db(dbdoc)
        raise Return(result)

    @coroutineDebug
    @coroutine
    def remove(self):
        if self.id:
            resp = yield self.get_collection().remove(self.query_dict_to_db({"id":self.id}))
            raise Return(resp)
        else:
            print "remove error"


    @classmethod
    @coroutineDebug
    @coroutine
    def get(cls, str_id):
        try:
            query = cls.query_dict_to_db({"id":str_id})
        except Exception, e:
            mylog.getlog().error("DOCEMENT GET ERROR")
            raise Return(None)
        resp = yield cls.get_collection().find_one(query)
        resp = cls.from_db(resp) if resp else None
        raise Return(resp)


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
        try:
            obj.update_from_db(dbDoc)
            return obj
        except Exception, e:
            mylog.getlog().error("DOCUMENT FROM DB ERROR: "+e.message)
            return None

    def update_from_db(self, dbDoc):
        if not dbDoc:
            return

        for name, field in self._fields.items():
            docKey = field.db_field or name
            if docKey in dbDoc:
                self[name] = dbDoc[docKey]

    def update(self, **kwargs):
        for k, v in kwargs.iteritems():
            if getattr(self, k, None):
                self[k] = v

    #turn all the key to document db_field and the value to db_field.to_mongo()
    @classmethod
    def query_dict_to_db(cls, queryDict):
        def trans(queryDict, parField=None):
            result = {}
            for k, v in queryDict.items():
                if k in cls._fields.keys():
                    v = trans(v, cls._fields[k]) if isinstance(v, dict) else cls._fields[k].to_mongo(v)
                    k = cls._fields[k].db_field
                elif re.match(r"^\$", k) and parField:
                    if isinstance(v, dict):
                        v = trans(v, parField)
                    else:
                        try:
                            v = parField.to_mongo(v)
                        except Exception, e:
                            pass
                result[k] = v
            return result

        return trans(queryDict)

    @classmethod
    def key_to_db(cls, key):
        if key in cls._fields.keys():
            return cls._fields[key].db_field
        else:
            return None

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
