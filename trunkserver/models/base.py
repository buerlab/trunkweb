# -*- coding: utf-8 -*-f

from bson import ObjectId, DBRef, SON
from collections import defaultdict
from query import QuerySetManager
import weakref, operator

ALLOW_INHERITANCE = True

class InvalidDocumentError(Exception):
    pass

class ValidationError(AssertionError):
    """Validation exception.

    May represent an error validating a field or a
    document containing fields with validation errors.

    :ivar errors: A dictionary of errors for fields within this
        document or list, or None if the error is for an
        individual field.
    """

    errors = {}
    field_name = None
    _message = None

    def __init__(self, message="", **kwargs):
        self.errors = kwargs.get('errors', {})
        self.field_name = kwargs.get('field_name')
        self.message = message

    def __str__(self):
        return self.message

    def __repr__(self):
        return '%s(%s,)' % (self.__class__.__name__, self.message)

    def __getattribute__(self, name):
        message = super(ValidationError, self).__getattribute__(name)
        if name == 'message':
            if self.field_name:
                message = '%s' % message
            if self.errors:
                message = '%s(%s)' % (message, self._format_errors())
        return message

    def _get_message(self):
        return self._message

    def _set_message(self, message):
        self._message = message

    message = property(_get_message, _set_message)

    def to_dict(self):
        """Returns a dictionary of all errors within a document

        Keys are field names or list indices and values are the
        validation error messages, or a nested dictionary of
        errors for an embedded document or list.
        """

        def build_dict(source):
            errors_dict = {}
            if not source:
                return errors_dict
            if isinstance(source, dict):
                for field_name, error in source.iteritems():
                    errors_dict[field_name] = build_dict(error)
            elif isinstance(source, ValidationError) and source.errors:
                return build_dict(source.errors)
            else:
                return unicode(source)
            return errors_dict
        if not self.errors:
            return {}
        return build_dict(self.errors)

    def _format_errors(self):
        """Returns a string listing all errors within a document"""

        def generate_key(value, prefix=''):
            if isinstance(value, list):
                value = ' '.join([generate_key(k) for k in value])
            if isinstance(value, dict):
                value = ' '.join(
                    [generate_key(v, k) for k, v in value.iteritems()])

            results = "%s.%s" % (prefix, value) if prefix else value
            return results

        error_dict = defaultdict(list)
        for k, v in self.to_dict().iteritems():
            error_dict[generate_key(v)].append(k)
        return ' '.join(["%s: %s" % (k, v) for k, v in error_dict.iteritems()])


class BaseField(object):
    def __init__(self, db_field=None, required=False, default=None, innerData=False):
        self.modified = False
        self.db_field = db_field
        self.name = None
        self.required = required
        self.default = default
        self.innerData = innerData

    def __get__(self, instance, owner):
        """Descriptor for retrieving a value from a field in a document. Do
        any necessary conversion between Python and MongoDB types.
        """
        if instance is None:
            # Document class being used rather than a document object
            return self

        value = instance._data.get(self.name)

        if value is None:
            value = self.default
            # Allow callable default values
            if callable(value):
                value = value()

        return value

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document.
        """
        instance._data[self.name] = value
        if instance._initialised:
            instance._mark_as_changed(self.db_field)

    def to_python(self, value):
        """Convert a MongoDB-compatible type to a Python type.
        """
        return value

    def to_mongo(self, value):
        """Convert a Python type to a MongoDB-compatible type.
        """
        return self.to_python(value)

    def to_son(self, value):
        return self.to_mongo(value)

    def prepare_query_value(self, op, value):
        """Prepare a value that is being used in a query for PyMongo.
        """
        return value

    def error(self, message="", errors=None, field_name=None):
        """Raises a ValidationError.
        """
        field_name = field_name or self.name
        raise ValidationError(message, errors=errors, field_name=field_name)

    def validate(self, value):
        """Perform validation on a value.
        """
        pass

class ComplexBaseField(BaseField):

    field = None

    def __get__(self, instance, owner):
        if instance is None:
            # Document class being used rather than a document object
            return self

        value = super(ComplexBaseField, self).__get__(instance, owner)

        if instance._readonly:
            return value

        # Convert lists / values so we can watch for any changes on them
        if isinstance(value, (list, tuple)) and not isinstance(value, BaseList):
            value = BaseList(value, instance, self.name)
            instance._data[self.name] = value
        elif isinstance(value, dict) and not isinstance(value, BaseDict):
            value = BaseDict(value, instance, self.name)
            instance._data[self.name] = value

        return value

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document.
        """
        instance._data[self.name] = value
        instance._mark_as_changed(self.name)

    def to_python(self, value):
        """Convert a MongoDB-compatible type to a Python type.
        """
        if isinstance(value, basestring):
            return value

        if hasattr(value, 'to_python'):
            return value.to_python()

        if not hasattr(value, '__iter__'):
            return value

        if hasattr(value, 'items'):  # dict
            if self.field:
                value_dict = {key: self.field.to_python(item) for key, item in value.iteritems()}
            else:
                value_dict = {k: v.to_python() if hasattr(v, 'to_python') else self.to_python(v) for k, v in value.iteritems()}
            return value_dict
        else:
            if self.field:
                return [self.field.to_python(v) for v in value]
            else:
                return [v.to_python() if hasattr(v, 'to_python') else self.to_python(v) for v in value]

    def to_mongo(self, value):
        """Convert a Python type to a MongoDB-compatible type.
        """
        if isinstance(value, basestring):
            return value

        if hasattr(value, 'to_mongo'):
            return value.to_mongo()

        if not hasattr(value, '__iter__'):
            return value

        if hasattr(value, 'items'):  # dict
            if self.field:
                value_dict = {key: self.field.to_mongo(item) for key, item in value.iteritems()}
            else:
                value_dict = {k: v.to_mongo() if hasattr(v, 'to_mongo') else self.to_mongo(v) for k, v in value.iteritems()}
            return value_dict
        else:
            if self.field:
                return [self.field.to_mongo(v) for v in value]
            else:
                return [v.to_mongo() if hasattr(v, 'to_mongo') else self.to_mongo(v) for v in value]

    def to_son(self, value):
        """Convert a Python type to a MongoDB-compatible type.
        """
        if isinstance(value, basestring):
            return value

        if hasattr(value, 'to_son'):
            return value.to_son()

        if not hasattr(value, '__iter__'):
            return value

        if hasattr(value, 'items'):  # dict
            if self.field:
                value_dict = {key: self.field.to_son(item) for key, item in value.iteritems()}
            else:
                value_dict = {k: v.to_son() if hasattr(v, 'to_son') else self.to_son(v) for k, v in value.iteritems()}
            return value_dict
        else:
            if self.field:
                return [self.field.to_son(v) for v in value]
            else:
                return [v.to_son() if hasattr(v, 'to_son') else self.to_son(v) for v in value]

    def validate(self, value):
        """If field is provided ensure the value is valid.
        """
        errors = {}
        if self.field:
            if hasattr(value, 'iteritems') or hasattr(value, 'items'):
                sequence = value.iteritems()
            else:
                sequence = enumerate(value)
            for k, v in sequence:
                try:
                    self.field.validate(v)
                except ValidationError, error:
                    errors[k] = error.errors or error
                except (ValueError, AssertionError), error:
                    errors[k] = error

            if errors:
                field_class = self.field.__class__.__name__
                self.error('Invalid %s item (%s)' % (field_class, value), errors=errors)
            # Don't allow empty values if required
        if self.required and not value:
            self.error('Field is required and cannot be empty')

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)

    def lookup_member(self, member_name):
        if self.field:
            return self.field.lookup_member(member_name)
        return None


class DocumentMetaclass(type):
    """Metaclass for all documents.
    """

    def __new__(cls, name, bases, attrs):
        flattened_bases = cls._get_bases(bases)
        super_new = super(DocumentMetaclass, cls).__new__

        # Merge all fields from subclasses
        doc_fields = {}
        for base in flattened_bases[::-1]:
            if hasattr(base, '_fields'):
                doc_fields.update(base._fields)

            # Standard object mixin - merge in any Fields
            base_fields = {}
            for attr_name, attr_value in base.__dict__.iteritems():
                if not isinstance(attr_value, BaseField):
                    continue
                attr_value.name = attr_name
                if not attr_value.db_field:
                    attr_value.db_field = attr_name
                base_fields[attr_name] = attr_value
            doc_fields.update(base_fields)

        # Discover any document fields
        field_names = {}
        for attr_name, attr_value in attrs.iteritems():
            if not isinstance(attr_value, BaseField):
                continue
            attr_value.name = attr_name
            if not attr_value.db_field:
                attr_value.db_field = attr_name
            doc_fields[attr_name] = attr_value

            # Count names to ensure no db_field redefinitions
            field_names[attr_value.db_field] = field_names.get(attr_value.db_field, 0) + 1

        # Ensure no duplicate db_fields
        duplicate_db_fields = [k for k, v in field_names.iteritems() if v > 1]
        if duplicate_db_fields:
            msg = ("Multiple db_fields defined for: %s " % ", ".join(duplicate_db_fields))
            raise InvalidDocumentError(msg)

        # Set _fields and db_field maps
        attrs['_fields'] = doc_fields
        attrs['_db_field_map'] = { k : getattr(v, 'db_field', k) for k, v in doc_fields.iteritems()}
        attrs['_reverse_db_field_map'] = { v : k for k, v in attrs['_db_field_map'].iteritems()}
        attrs['objects'] = QuerySetManager()

        # Create the new_class
        new_class = super_new(cls, name, bases, attrs)

        return new_class

    @classmethod
    def _get_bases(cls, bases):
        if isinstance(bases, BasesTuple):
            return bases
        seen = []
        bases = cls.__get_bases(bases)
        unique_bases = (b for b in bases if not (b in seen or seen.append(b)))
        return BasesTuple(unique_bases)

    @classmethod
    def __get_bases(cls, bases):
        for base in bases:
            if base is object:
                continue
            yield base
            for child_base in cls.__get_bases(base.__bases__):
                yield child_base


class BaseDocument(object):
    _initialised = False
    _readonly = False

    def __init__(self, **values):
        self._data = {}
        self._changed_fields = set()

        self.merge(**values)

        self._initialised = True

    def merge(self, **values):
        for key, value in values.iteritems():
            key = self._reverse_db_field_map.get(key, key)
            setattr(self, key, value)

    def _mark_as_changed(self, key):
        if not key:
            return
        self._changed_fields.add(key)

    def validate(self):
        """Ensure that all fields' values are valid and that required fields
        are present.
        """
        # Get a list of tuples of field names and their current values
        fields = [(field, getattr(self, name)) for name, field in self._fields.items()]

        # Ensure that each field is matched to a valid value
        errors = {}
        for field, value in fields:
            if value is not None:
                try:
                    field.validate(value)
                except ValidationError, error:
                    errors[field.name] = error.errors or error
                except (ValueError, AttributeError, AssertionError), error:
                    errors[field.name] = error
            elif field.required:
                errors[field.name] = ValidationError('Field is required',
                    field_name=field.name)
        if errors:
            raise ValidationError('ValidationError', errors=errors)

    @classmethod
    def _get_collection_name(cls):
        """Returns the collection name for this class.
        """
        return cls.col_name

    @property
    def changed(self):
        return len(self._changed_fields)>0

    def to_mongo(self):
        """Return data dictionary ready for use with MongoDB.
        """
        data = {}
        for field_name, field in self._fields.iteritems():
            value = getattr(self, field_name, None)
            if value is not None:
                data[field.db_field] = field.to_mongo(value)
            # Only add _cls and _types if allow_inheritance is not False
        if '_id' in data and data['_id'] is None:
            del data['_id']

        return data

    def to_son(self):
        data = {}
        for field_name, field in self._fields.iteritems():
            value = getattr(self, field_name, None)
            if value is not None:
                data[field_name] = field.to_son(value)
                # Only add _cls and _types if allow_inheritance is not False
        if '_id' in data and data['_id'] is None:
            del data['_id']

        return data

    @classmethod
    def _from_son(cls, son):
        """Create an instance of a Document (subclass) from a PyMongo SON.
        """
#        data = {"%s" % key: value for key, value in son.iteritems()}
        data = son

        changed_fields = set()
        errors_dict = {}

        for field_name, field in cls._fields.iteritems():
            if field.db_field in data:
                value = data[field.db_field]
                try:
                    data[field_name] = (value if value is None else field.to_python(value))
                    if field_name != field.db_field:
                        del data[field.db_field]
                except (AttributeError, ValueError), e:
                    errors_dict[field_name] = e
            elif field.default:
                default = field.default
                if callable(default):
                    default = default()
                if isinstance(default, BaseDocument):
                    changed_fields.add(field_name)

        if errors_dict:
            errors = "\n".join(["%s - %s" % (k, v) for k, v in errors_dict.iteritems()])
            msg = ("Invalid data to create a `%s` instance.\n%s" % (cls.__name__, errors))
            raise InvalidDocumentError(msg)

        obj = cls(**data)
        obj._changed_fields = changed_fields
        obj._created = False
        return obj

    def _get_changed_fields(self):
        changed = self._changed_fields.copy()
        from document import EmbeddedDocument

        for f_name in self._fields:
            value = self._data.get(f_name)
            f_dbfield = getattr(self.__class__, f_name).db_field or f_name
            if f_dbfield not in changed and isinstance(value, EmbeddedDocument):
                embedded_changed = value._get_changed_fields()
                changed.update({ "%s.%s" % (f_dbfield, k) for k in embedded_changed })
            elif f_dbfield not in changed and isinstance(value, (list, tuple, dict)):
                if not hasattr(value, 'items'):
                    iterator = enumerate(value)
                else:
                    iterator = value.iteritems()
                for index, value in iterator:
                    if not hasattr(value, '_get_changed_fields'):
                        continue

                    embedded_changed = value._get_changed_fields()
                    changed.update({"%s.%s.%s" % (f_dbfield, index, k) for k in embedded_changed if k})

        return changed

    def _diff(self):
        doc = self.to_mongo()
        set_fields = self._get_changed_fields()
        set_data = {}
        unset_data = []

        for path in set_fields:
            d = doc
            for p in path.split('.'):
                if p.isdigit():
                    d = d[int(p)]
                elif hasattr(d, 'get'):
                    d = d.get(p)
            set_data[path] = d

        return set_data, unset_data

    def __iter__(self):
        return iter(self._fields)

    def __getitem__(self, name):
        """Dictionary-style field access, return a field's value if present.
        """
        try:
            if name in self._fields:
                return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
        """Dictionary-style field access, set a field's value.
        """
        # Ensure that the field exists before settings its value
        if name not in self._fields:
            raise KeyError(name)
        return setattr(self, name, value)

    def __contains__(self, name):
        try:
            val = getattr(self, name)
            return val is not None
        except AttributeError:
            return False

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        try:
            u = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return '<%s: %s>' % (self.__class__.__name__, u)

    def __str__(self):
        if hasattr(self, '__unicode__'):
            return unicode(self).encode('utf-8')
        return '%s object' % self.__class__.__name__

    def __eq__(self, other):
        if isinstance(other, self.__class__) and hasattr(other, 'id'):
            if self.id == other.id:
                return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if self.pk is None:
            # For new object
            return super(BaseDocument, self).__hash__()
        else:
            return hash(self.pk)


class BasesTuple(tuple):
    """Special class to handle introspection of bases tuple in __new__"""
    pass


class BaseList(list):
    """A special list so we can watch any changes
    """

    _instance = None
    _name = None

    def __init__(self, list_items, instance, name):
        self._instance = weakref.proxy(instance)
        self._name = name
        super(BaseList, self).__init__(list_items)

    def __setitem__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).__setitem__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).__delitem__(*args, **kwargs)

    def __getstate__(self):
        self.observer = None
        return self

    def __setstate__(self, state):
        self = state
        return self

    def append(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).append(*args, **kwargs)

    def extend(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).extend(*args, **kwargs)

    def insert(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).insert(*args, **kwargs)

    def pop(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).remove(*args, **kwargs)

    def reverse(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).reverse(**kwargs)

    def sort(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).sort(*args, **kwargs)

    def _mark_as_changed(self):
        if hasattr(self._instance, '_mark_as_changed'):
            self._instance._mark_as_changed(self._name)


class BaseDict(dict):
    """A special dict so we can watch any changes
"""

    _instance = None
    _name = None

    def __init__(self, dict_items, instance, name):
        self._instance = weakref.proxy(instance)
        self._name = name
        super(BaseDict, self).__init__(dict_items)

    def __setitem__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).__setitem__(*args, **kwargs)

    def __delete__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).__delete__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).__delitem__(*args, **kwargs)

    def __delattr__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).__delattr__(*args, **kwargs)

    def __getstate__(self):
        self.instance = None
        return self

    def __setstate__(self, state):
        self = state
        return self

    def clear(self):
        self._mark_as_changed()
        return super(BaseDict, self).clear()

    def pop(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).pop(*args, **kwargs)

    def popitem(self):
        self._mark_as_changed()
        return super(BaseDict, self).popitem()

    def update(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).update(*args, **kwargs)

    def _mark_as_changed(self):
        if hasattr(self._instance, '_mark_as_changed'):
            self._instance._mark_as_changed(self._name)
