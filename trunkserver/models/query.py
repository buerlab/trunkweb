# -*- coding: utf-8 -*-f
import copy, operator, itertools, re, pprint
import pymongo
from collections import defaultdict
from tornado.gen import coroutine, Return

# Delete rules
DO_NOTHING = 0
NULLIFY = 1
CASCADE = 2
DENY = 3
PULL = 4


class DoesNotExist(Exception):
    pass

class InvalidQueryError(Exception):
    pass

class MultipleObjectsReturned(Exception):
    pass

class OperationError(Exception):
    pass


class QNodeVisitor(object):
    """Base visitor class for visiting Q-object nodes in a query tree.
    """

    def visit_combination(self, combination):
        """Called by QCombination objects.
        """
        return combination

    def visit_query(self, query):
        """Called by (New)Q objects.
        """
        return query


class SimplificationVisitor(QNodeVisitor):
    """Simplifies query trees by combinging unnecessary 'and' connection nodes
    into a single Q-object.
    """

    def visit_combination(self, combination):
        if combination.operation == combination.AND:
            # The simplification only applies to 'simple' queries
            if all(isinstance(node, Q) for node in combination.children):
                queries = [node.query for node in combination.children]
                return Q(**self._query_conjunction(queries))
        return combination

    def _query_conjunction(self, queries):
        """Merges query dicts - effectively &ing them together.
        """
        query_ops = set()
        combined_query = {}
        for query in queries:
            ops = set(query.keys())
            # Make sure that the same operation isn't applied more than once
            # to a single field
            intersection = ops.intersection(query_ops)
            if intersection:
                msg = 'Duplicate query conditions: '
                raise InvalidQueryError(msg + ', '.join(intersection))

            query_ops.update(ops)
            combined_query.update(copy.deepcopy(query))
        return combined_query


class QueryTreeTransformerVisitor(QNodeVisitor):
    """Transforms the query tree in to a form that may be used with MongoDB.
    """

    def visit_combination(self, combination):
        if combination.operation == combination.AND:
            # MongoDB doesn't allow us to have too many $or operations in our
            # queries, so the aim is to move the ORs up the tree to one
            # 'master' $or. Firstly, we must find all the necessary parts (part
            # of an AND combination or just standard Q object), and store them
            # separately from the OR parts.
            or_groups = []
            and_parts = []
            for node in combination.children:
                if isinstance(node, QCombination):
                    if node.operation == node.OR:
                        # Any of the children in an $or component may cause
                        # the query to succeed
                        or_groups.append(node.children)
                    elif node.operation == node.AND:
                        and_parts.append(node)
                elif isinstance(node, Q):
                    and_parts.append(node)

            # Now we combine the parts into a usable query. AND together all of
            # the necessary parts. Then for each $or part, create a new query
            # that ANDs the necessary part with the $or part.
            clauses = []
            for or_group in itertools.product(*or_groups):
                q_object = reduce(lambda a, b: a & b, and_parts, Q())
                q_object = reduce(lambda a, b: a & b, or_group, q_object)
                clauses.append(q_object)
                # Finally, $or the generated clauses in to one query. Each of the
            # clauses is sufficient for the query to succeed.
            return reduce(lambda a, b: a | b, clauses, Q())

        if combination.operation == combination.OR:
            children = []
            # Crush any nested ORs in to this combination as MongoDB doesn't
            # support nested $or operations
            for node in combination.children:
                if (isinstance(node, QCombination) and
                    node.operation == combination.OR):
                    children += node.children
                else:
                    children.append(node)
            combination.children = children

        return combination


class QueryCompilerVisitor(QNodeVisitor):
    """Compiles the nodes in a query tree to a PyMongo-compatible query
    dictionary.
    """

    def __init__(self, document):
        self.document = document

    def visit_combination(self, combination):
        if combination.operation == combination.OR:
            return {'$or': combination.children}
        elif combination.operation == combination.AND:
            return self._mongo_query_conjunction(combination.children)
        return combination

    def visit_query(self, query):
        return QuerySet._transform_query(self.document, **query.query)

    def _mongo_query_conjunction(self, queries):
        """Merges Mongo query dicts - effectively &ing them together.
        """
        combined_query = {}
        for query in queries:
            for field, ops in query.items():
                if field not in combined_query:
                    combined_query[field] = ops
                else:
                    # The field is already present in the query the only way
                    # we can merge is if both the existing value and the new
                    # value are operation dicts, reject anything else
                    if (not isinstance(combined_query[field], dict) or
                        not isinstance(ops, dict)):
                        message = 'Conflicting values for ' + field
                        raise InvalidQueryError(message)

                    current_ops = set(combined_query[field].keys())
                    new_ops = set(ops.keys())
                    # Make sure that the same operation isn't applied more than
                    # once to a single field
                    intersection = current_ops.intersection(new_ops)
                    if intersection:
                        msg = 'Duplicate query conditions: '
                        raise InvalidQueryError(msg + ', '.join(intersection))

                    # Right! We've got two non-overlapping dicts of operations!
                    combined_query[field].update(copy.deepcopy(ops))
        return combined_query


class QNode(object):
    """Base class for nodes in query trees.
    """

    AND = 0
    OR = 1

    def to_query(self, document):
        query = self.accept(SimplificationVisitor())
        query = query.accept(QueryTreeTransformerVisitor())
        query = query.accept(QueryCompilerVisitor(document))
        return query

    def accept(self, visitor):
        raise NotImplementedError

    def _combine(self, other, operation):
        """Combine this node with another node into a QCombination object.
        """
        if getattr(other, 'empty', True):
            return self

        if self.empty:
            return other

        return QCombination(operation, [self, other])

    @property
    def empty(self):
        return False

    def __or__(self, other):
        return self._combine(other, self.OR)

    def __and__(self, other):
        return self._combine(other, self.AND)


class QCombination(QNode):
    """Represents the combination of several conditions by a given logical
    operator.
    """

    def __init__(self, operation, children):
        self.operation = operation
        self.children = []
        for node in children:
            # If the child is a combination of the same type, we can merge its
            # children directly into this combinations children
            if isinstance(node, QCombination) and node.operation == operation:
                self.children += node.children
            else:
                self.children.append(node)

    def accept(self, visitor):
        for i in range(len(self.children)):
            if isinstance(self.children[i], QNode):
                self.children[i] = self.children[i].accept(visitor)

        return visitor.visit_combination(self)

    @property
    def empty(self):
        return not bool(self.children)


class Q(QNode):
    """A simple query object, used in a query tree to build up more complex
    query structures.
    """

    def __init__(self, **query):
        self.query = query

    def accept(self, visitor):
        return visitor.visit_query(self)

    @property
    def empty(self):
        return not bool(self.query)

class QueryFieldList(object):
    ONLY = 1
    EXCLUDE = 0

    def __init__(self, fields=[], value=ONLY, always_include=[]):
        self.value = value
        self.fields = set(fields)
        self.always_include = set(always_include)
        self._id = None
        self.projection = {}

    def as_dict(self):
        field_list = {field: self.value for field in self.fields}
        field_list.update(self.projection)
        if self._id is not None:
            field_list['_id'] = self._id
        return field_list

    def __add__(self, f):
        if not self.fields:
            self.fields = f.fields
            self.value = f.value
        elif self.value is self.ONLY and f.value is self.ONLY:
            self.fields = self.fields.intersection(f.fields)
        elif self.value is self.EXCLUDE and f.value is self.EXCLUDE:
            self.fields = self.fields.union(f.fields)
        elif self.value is self.ONLY and f.value is self.EXCLUDE:
            self.fields -= f.fields
        elif self.value is self.EXCLUDE and f.value is self.ONLY:
            self.value = self.ONLY
            self.fields = f.fields - self.fields
        elif isinstance(f.value, dict):
            self.projection.update({ field:f.value for field in f.fields })

        if '_id' in f.fields:
            self._id = f.value

        if self.always_include:
            if self.value is self.ONLY and self.fields:
                self.fields = self.fields.union(self.always_include)
            else:
                self.fields -= self.always_include
        return self

    def reset(self):
        self.fields = set()
        self.value = self.ONLY

    def __nonzero__(self):
        return bool(self.fields)


class QuerySet(object):
    """A set of results returned from a query. Wraps a MongoDB cursor,
    providing :class:`~mongoengine.Document` objects as the results.
    """

    __already_indexed = set()
    __dereference = False

    def __init__(self, document, collection):
        self._document = document
        self._collection = collection
        self._mongo_query = None
        self._query_obj = Q()
        self._initial_query = {}
        self._where_clause = None
        self._loaded_fields = QueryFieldList()
        self._ordering = []
        self._snapshot = False
        self._timeout = True
        self._class_check = True
        self._slave_okay = False
        self._iter = False
        self._scalar = []
        self._cursor_obj = None
        self._limit = None
        self._skip = None
        self._hint = -1  # Using -1 as None is a valid value for hint

    def clone(self):
        """Creates a copy of the current :class:`~mongoengine.queryset.QuerySet`

        .. versionadded:: 0.5
        """
        c = self.__class__(self._document, self._collection)

        copy_props = ('_initial_query', '_query_obj', '_where_clause',
                      '_loaded_fields', '_ordering', '_snapshot',
                      '_timeout', '_limit', '_skip', '_slave_okay', '_hint')

        for prop in copy_props:
            val = getattr(self, prop)
            setattr(c, prop, copy.deepcopy(val))

        return c

    @property
    def _query(self):
        if self._mongo_query is None:
            self._mongo_query = self._query_obj.to_query(self._document)
            if self._class_check:
                self._mongo_query.update(self._initial_query)
        return self._mongo_query

    def __call__(self, q_obj=None, class_check=True, slave_okay=False, **query):
        """Filter the selected documents by calling the
        :class:`~mongoengine.queryset.QuerySet` with a query.

        :param q_obj: a :class:`~mongoengine.queryset.Q` object to be used in
            the query; the :class:`~mongoengine.queryset.QuerySet` is filtered
            multiple times with different :class:`~mongoengine.queryset.Q`
            objects, only the last one will be used
        :param class_check: If set to False bypass class name check when
            querying collection
        :param slave_okay: if True, allows this query to be run against a
            replica secondary.
        :param query: Django-style query keyword arguments
        """
        query = Q(**query)
        if q_obj:
            query &= q_obj
        self._query_obj &= query
        self._mongo_query = None
        self._cursor_obj = None
        self._class_check = class_check
        return self

    def each(self, callback):
        def _cb(doc, error):
            if not error:
                callback(self._document._from_son(doc), error)
            else:
                callback(doc, error)

        self._cursor.each(callback=_cb)

    def to_list(self, callback):
        def _cb(docs, error):
            if not error:
                docs = [self._document._from_son(d) for d in docs]
                callback(docs, error)
            else:
                callback(docs, error)

        self._cursor.to_list(callback=_cb)

    def raw_each(self, callback):
        self._cursor.each(callback=callback)

    def raw_list(self, callback):
        self._cursor.to_list(callback=callback)

    @classmethod
    def _lookup_field(cls, document, parts):
        """Lookup a field based on its attribute and return a list containing
        the field's parents and the field.
        """
        if not isinstance(parts, (list, tuple)):
            parts = [parts]
        fields = []
        field = None

        for field_name in parts:
            # Handle ListField indexing:
            if field_name.isdigit():
                try:
                    new_field = field.field
                except AttributeError, err:
                    raise InvalidQueryError("Can't use index on unsubscriptable field (%s)" % err)
                fields.append(field_name)
                continue

            if field is None:
                # Look up first field from the document
                if field_name == 'pk':
                    # Deal with "primary key" alias
                    field_name = document._meta['id_field']
                if field_name in document._fields:
                    field = document._fields[field_name]
                else:
                    raise InvalidQueryError('Cannot resolve field "%s"' % field_name)
            else:
                if hasattr(getattr(field, 'field', None), 'lookup_member'):
                    new_field = field.field.lookup_member(field_name)
                else:
                # Look up subfield on the previous field
                    new_field = field.lookup_member(field_name)
                from base import ComplexBaseField
                if not new_field and isinstance(field, ComplexBaseField):
                    fields.append(field_name)
                    continue
                elif not new_field:
                    raise InvalidQueryError('Cannot resolve field "%s"' % field_name)
                field = new_field  # update field to the new field type
            fields.append(field)
        return fields

    @classmethod
    def _translate_field_name(cls, doc_cls, field, sep='.'):
        """Translate a field attribute name to a database field name.
        """
        parts = field.split(sep)
        parts = [f.db_field for f in QuerySet._lookup_field(doc_cls, parts)]
        return '.'.join(parts)

    @classmethod
    def _transform_query(cls, _doc_cls=None, _field_operation=False, **query):
        """Transform a query from Django-style format to Mongo format.
        """
        operators = ['ne', 'gt', 'gte', 'lt', 'lte', 'in', 'nin', 'mod', 'all', 'size', 'exists', 'not', 'type']
        geo_operators = ['within_distance', 'within_spherical_distance', 'within_box', 'within_polygon', 'near', 'near_sphere']
        match_operators = ['contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'exact', 'iexact']
        custom_operators = ['match']

        mongo_query = {}
        merge_query = defaultdict(list)
        for key, value in query.items():
            if key == "__raw__":
                mongo_query.update(value)
                continue

            parts = key.split('__')
            indices = [(i, p) for i, p in enumerate(parts) if p.isdigit()]
            parts = [part for part in parts if not part.isdigit()]
            # Check for an operator and transform to mongo-style if there is
            op = None
            if parts[-1] in operators + match_operators + geo_operators + custom_operators:
                op = parts.pop()

            negate = False
            if parts[-1] == 'not':
                parts.pop()
                negate = True

            if _doc_cls:
                # Switch field names to proper names [set in Field(name='foo')]
                fields = QuerySet._lookup_field(_doc_cls, parts)
                parts = []

                cleaned_fields = []
                for field in fields:
                    append_field = True
                    if isinstance(field, basestring):
                        parts.append(field)
                        append_field = False
                    else:
                        parts.append(field.db_field)
                    if append_field:
                        cleaned_fields.append(field)

                # Convert value to proper value
                field = cleaned_fields[-1]

                singular_ops = [None, 'ne', 'gt', 'gte', 'lt', 'lte', 'not', 'type']
                singular_ops += match_operators
                if op in singular_ops:
                    if isinstance(field, basestring):
                        if op in match_operators and isinstance(value, basestring):
                            from fields import StringField
                            value = StringField.prepare_query_value(op, value)
                        else:
                            value = field
                    else:
                        value = field.prepare_query_value(op, value)
                elif op in ('in', 'nin', 'all', 'near'):
                    # 'in', 'nin' and 'all' require a list of values
                    value = [field.prepare_query_value(op, v) for v in value]

            # if op and op not in match_operators:
            if op:
                if op in geo_operators:
                    if op == "within_distance":
                        value = {'$within': {'$center': value}}
                    elif op == "within_spherical_distance":
                        value = {'$within': {'$centerSphere': value}}
                    elif op == "within_polygon":
                        value = {'$within': {'$polygon': value}}
                    elif op == "near":
                        value = {'$near': value}
                    elif op == "near_sphere":
                        value = {'$nearSphere': value}
                    elif op == 'within_box':
                        value = {'$within': {'$box': value}}
                    else:
                        raise NotImplementedError("Geo method '%s' has not "
                                                  "been implemented" % op)
                elif op in custom_operators:
                    if op == 'match':
                        value = {"$elemMatch": value}
                    else:
                        NotImplementedError("Custom method '%s' has not "
                                            "been implemented" % op)
                elif op not in match_operators:
                    value = {'$' + op: value}

            if negate:
                value = {'$not': value}

            for i, part in indices:
                parts.insert(i, part)
            key = '.'.join(parts)
            if op is None or key not in mongo_query:
                mongo_query[key] = value
            elif key in mongo_query:
                if key in mongo_query and isinstance(mongo_query[key], dict):
                    mongo_query[key].update(value)
                else:
                    # Store for manually merging later
                    merge_query[key].append(value)

        # The queryset has been filter in such a way we must manually merge
        for k, v in merge_query.items():
            merge_query[k].append(mongo_query[k])
            del mongo_query[k]
            if isinstance(v, list):
                value = [{k:val} for val in v]
                if '$and' in mongo_query.keys():
                    mongo_query['$and'].append(value)
                else:
                    mongo_query['$and'] = value

        return mongo_query

    @property
    def _cursor_args(self):
        cursor_args = {
            'snapshot': self._snapshot,
            'timeout': self._timeout,
            'slave_okay': self._slave_okay
        }
        if self._loaded_fields:
            cursor_args['fields'] = self._loaded_fields.as_dict()
        return cursor_args

    @property
    def _cursor(self):
        if self._cursor_obj is None:
            self._cursor_obj = self._collection.find(self._query, **self._cursor_args)
            # Apply where clauses to cursor
            if self._where_clause:
                self._cursor_obj.where(self._where_clause)

            # apply default ordering
            if self._ordering:
                self._cursor_obj.sort(self._ordering)

            if self._limit is not None:
                self._cursor_obj.limit(self._limit - (self._skip or 0))

            if self._skip is not None:
                self._cursor_obj.skip(self._skip)

            if self._hint != -1:
                self._cursor_obj.hint(self._hint)
        return self._cursor_obj

    def count(self, callback):
        """Count the selected elements in the query.
        """
        if self._limit == 0:
            callback(0)
        self._cursor.count(with_limit_and_skip=True, callback=callback)

    def order_by(self, *keys):
        """Order the :class:`~mongoengine.queryset.QuerySet` by the keys. The
        order may be specified by prepending each of the keys by a + or a -.
        Ascending order is assumed.

        :param keys: fields to order the query results by; keys may be
            prefixed with **+** or **-** to determine the ordering direction
        """
        key_list = []
        for key in keys:
            if not key: continue
            direction = pymongo.ASCENDING
            if key[0] == '-':
                direction = pymongo.DESCENDING
            if key[0] in ('-', '+'):
                key = key[1:]
            key = key.replace('__', '.')
            try:
                key = QuerySet._translate_field_name(self._document, key)
            except:
                pass
            key_list.append((key, direction))

        self._ordering = key_list
        self._cursor.sort(key_list)
        return self

    def limit(self, n):
        """Limit the number of returned documents to `n`. This may also be
        achieved using array-slicing syntax (e.g. ``User.objects[:5]``).

        :param n: the maximum number of objects to return
        """
        if n == 0:
            self._cursor.limit(1)
        else:
            self._cursor.limit(n)
        self._limit = n

        # Return self to allow chaining
        return self

    def skip(self, n):
        """Skip `n` documents before returning the results. This may also be
        achieved using array-slicing syntax (e.g. ``User.objects[5:]``).

        :param n: the number of objects to skip before returning results
        """
        self._cursor.skip(n)
        self._skip = n
        return self

    def only(self, *fields):
        """Load only a subset of this document's fields. ::

            post = BlogPost.objects(...).only("title", "author.name")

        :param fields: fields to include

        .. versionadded:: 0.3
        .. versionchanged:: 0.5 - Added subfield support
        """
        fields = {f: QueryFieldList.ONLY for f in fields}
        return self.fields(**fields)

    def exclude(self, *fields):
        """Opposite to .only(), exclude some document's fields. ::

            post = BlogPost.objects(...).exclude("comments")

        :param fields: fields to exclude

        .. versionadded:: 0.5
        """
        fields = {f: QueryFieldList.EXCLUDE for f in fields}
        return self.fields(**fields)

    def fields(self, **kwargs):
        """Manipulate how you load this document's fields.  Used by `.only()`
        and `.exclude()` to manipulate which fields to retrieve.  Fields also
        allows for a greater level of control for example:

        Retrieving a Subrange of Array Elements:

        You can use the $slice operator to retrieve a subrange of elements in
        an array ::

            post = BlogPost.objects(...).fields(slice__comments=5) // first 5 comments

        :param kwargs: A dictionary identifying what to include

        .. versionadded:: 0.5
        """

        # Check for an operator and transform to mongo-style if there is
        operators = ["slice"]
        cleaned_fields = []
        for key, value in kwargs.items():
            parts = key.split('__')
            if parts[0] in operators:
                op = parts.pop(0)
                value = {'$' + op: value}
            key = '.'.join(parts)
            cleaned_fields.append((key, value))

        fields = sorted(cleaned_fields, key=operator.itemgetter(1))
        for value, group in itertools.groupby(fields, lambda x: x[1]):
            fields = [field for field, value in group]
            fields = self._fields_to_dbfields(fields)
            self._loaded_fields += QueryFieldList(fields, value=value)
        return self

    def all_fields(self):
        """Include all fields. Reset all previously calls of .only() and .exclude(). ::

            post = BlogPost.objects(...).exclude("comments").only("title").all_fields()

        .. versionadded:: 0.5
        """
        self._loaded_fields = QueryFieldList(always_include=self._loaded_fields.always_include)
        return self

    def _fields_to_dbfields(self, fields):
        """Translate fields paths to its db equivalents"""
        ret = []
        for field in fields:
            field = ".".join(f if isinstance(f, (str, unicode)) else f.db_field for f in QuerySet._lookup_field(self._document, field.split('.')))
            ret.append(field)
        return ret

    def get(self, callback, *q_objs, **query):
        """Retrieve the the matching object raising
        :class:`~mongoengine.queryset.MultipleObjectsReturned` or
        `DocumentName.MultipleObjectsReturned` exception if multiple results and
        :class:`~mongoengine.queryset.DoesNotExist` or `DocumentName.DoesNotExist`
        if no results are found.

        .. versionadded:: 0.3
        """
        def _cb(docs, error):
            if error:
                callback(docs, error)
            else:
                if len(docs)>1:
                    self._cursor.rewind()
                    message = u'%d items returned, instead of 1' % len(docs)
                    callback(None, MultipleObjectsReturned(message))
                elif len(docs) == 0:
                    callback(None, error)
                else:
                    callback(docs[0], error)

        self.__call__(*q_objs, **query)
        self.limit(2)
        self.to_list(_cb)

    def insert(self, doc, callback):
        if not doc:
            raise OperationError("No update parameters, would remove data")

        self._collection.insert(doc, callback=callback)

    def update(self, update, multi=False, callback=None):
        if not update:
            raise OperationError("No update parameters, would remove data")

        query = self._query

        try:
            self._collection.update(query, update, multi=multi, callback=callback)
        except pymongo.errors.OperationFailure, err:
            if unicode(err) == u'multi not coded yet':
                message = u'update() method requires MongoDB 1.1.3+'
                raise OperationError(message)
            raise OperationError(u'Update failed (%s)' % unicode(err))

    def findAndModify(self, callback, *args, **kwargs):
        def _cb(doc, error):
            if error:
                callback(doc, error)
            else:
                callback(self._document._from_son(doc), error)
        self._collection.find_and_modify(query=self._query, fields=self._loaded_fields.as_dict(), callback=_cb, *args, **kwargs)

    def _sub_js_fields(self, code):
        """When fields are specified with [~fieldname] syntax, where
        *fieldname* is the Python name of a field, *fieldname* will be
        substituted for the MongoDB name of the field (specified using the
        :attr:`name` keyword argument in a field's constructor).
        """
        def field_sub(match):
            # Extract just the field name, and look up the field objects
            field_name = match.group(1).split('.')
            fields = QuerySet._lookup_field(self._document, field_name)
            # Substitute the correct name for the field into the javascript
            return u'["%s"]' % fields[-1].db_field

        def field_path_sub(match):
            # Extract just the field name, and look up the field objects
            field_name = match.group(1).split('.')
            fields = QuerySet._lookup_field(self._document, field_name)
            # Substitute the correct name for the field into the javascript
            return ".".join([f.db_field for f in fields])

        code = re.sub(u'\[\s*~([A-z_][A-z_0-9.]+?)\s*\]', field_sub, code)
        code = re.sub(u'\{\{\s*~([A-z_][A-z_0-9.]+?)\s*\}\}', field_path_sub, code)
        return code

    def where(self, where_clause):
        """Filter ``QuerySet`` results with a ``$where`` clause (a Javascript
        expression). Performs automatic field name substitution like
        :meth:`mongoengine.queryset.Queryset.exec_js`.

        .. note:: When using this mode of query, the database will call your
                  function, or evaluate your predicate clause, for each object
                  in the collection.

        .. versionadded:: 0.5
        """
        where_clause = self._sub_js_fields(where_clause)
        self._where_clause = where_clause
        return self

    def explain(self, format=False):
        """Return an explain plan record for the
        :class:`~mongoengine.queryset.QuerySet`\ 's cursor.

        :param format: format the plan before returning it
        """

        plan = self._cursor.explain()
        if format:
            plan = pprint.pformat(plan)
        return plan

    def snapshot(self, enabled):
        """Enable or disable snapshot mode when querying.

        :param enabled: whether or not snapshot mode is enabled

        ..versionchanged:: 0.5 - made chainable
        """
        self._snapshot = enabled
        return self

    def timeout(self, enabled):
        """Enable or disable the default mongod timeout when querying.

        :param enabled: whether or not the timeout is used

        ..versionchanged:: 0.5 - made chainable
        """
        self._timeout = enabled
        return self

    def slave_okay(self, enabled=True):
        """Enable or disable the slave_okay when querying.

        :param enabled: whether or not the slave_okay is enabled
        """
        self._slave_okay = enabled
        return self

    def delete(self, callback):
        doc = self._document

        # Handle deletes where skips or limits have been applied
        if self._skip or self._limit:
            raise NotImplemented
            # for doc in self:
            #     doc.delete()
            # return

        self._collection.remove(self._query, callback=callback)

class QuerySetManager(object):
    def __get__(self, instance, owner):
        """Descriptor for instantiating a new QuerySet object when
        Document.objects is accessed.
        """
        if instance is not None:
            # Document class being used rather than a document object
            return self

        # owner is the document that contains the QuerySetManager
        queryset = QuerySet(owner, owner.get_collection())
        return queryset

