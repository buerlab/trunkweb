from base import BaseDocument, BaseField, ComplexBaseField
from bson import Binary, DBRef, ObjectId
from operator import itemgetter
import re, decimal, datetime, time, warnings, uuid
from query import QuerySet, DO_NOTHING


class ObjectIdField(BaseField):
    """An field wrapper around MongoDB's ObjectIds.
    """

    def to_python(self, value):
        if not isinstance(value, ObjectId):
            value = ObjectId(value)
        return value

    def to_mongo(self, value):
        if not isinstance(value, ObjectId):
            try:
                return ObjectId(unicode(value))
            except Exception, e:
                # e.message attribute has been deprecated since Python 2.6
                self.error(unicode(e))
        return value

    def to_client(self, value):
        return str(value)

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)

    def validate(self, value):
        try:
            ObjectId(unicode(value))
        except:
            self.error('Invalid Object ID')


class StringField(BaseField):
    """A unicode string field.
    """

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        super(StringField, self).__init__(**kwargs)

    def to_python(self, value):
        if isinstance(value, unicode):
            return value
        try:
            value = value.decode('utf-8')
        except:
            pass
        return value

    def validate(self, value):
        if not isinstance(value, basestring):
            self.error('StringField only accepts string values')

        if self.max_length is not None and len(value) > self.max_length:
            self.error('String value is too long')

        if self.min_length is not None and len(value) < self.min_length:
            self.error('String value is too short')

        if self.regex is not None and self.regex.match(value) is None:
            self.error('String value did not match validation regex')

    def lookup_member(self, member_name):
        return None

    def prepare_query_value(self, op, value):
        if not isinstance(op, basestring):
            return value

        if op.lstrip('i') in ('startswith', 'endswith', 'contains', 'exact'):
            flags = 0
            if op.startswith('i'):
                flags = re.IGNORECASE
                op = op.lstrip('i')

            regex = r'%s'
            if op == 'startswith':
                regex = r'^%s'
            elif op == 'endswith':
                regex = r'%s$'
            elif op == 'exact':
                regex = r'^%s$'

            # escape unsafe characters which could lead to a re.error
            value = re.escape(value)
            value = re.compile(regex % value, flags)
        return value


class URLField(StringField):
    """A field that validates input as an URL.

    .. versionadded:: 0.3
    """

    URL_REGEX = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    def __init__(self, verify_exists=False, **kwargs):
        self.verify_exists = verify_exists
        super(URLField, self).__init__(**kwargs)

    def validate(self, value):
        if not URLField.URL_REGEX.match(value):
            self.error('Invalid URL: %s' % value)

        if self.verify_exists:
            import urllib2
            try:
                request = urllib2.Request(value)
                urllib2.urlopen(request)
            except Exception, e:
                self.error('This URL appears to be a broken link: %s' % e)


class EmailField(StringField):
    """A field that validates input as an E-Mail-Address.

    .. versionadded:: 0.4
    """

    EMAIL_REGEX = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE  # domain
    )

    def validate(self, value):
        if not EmailField.EMAIL_REGEX.match(value):
            self.error('Invalid Mail-address: %s' % value)


class IntField(BaseField):
    """An integer field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(IntField, self).__init__(**kwargs)

    def to_python(self, value):
        try:
            value = int(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        try:
            value = int(value)
        except:
            self.error('%s could not be converted to int' % value)

        if self.min_value is not None and value < self.min_value:
            self.error('Integer value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Integer value is too large')

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return int(value)


class FloatField(BaseField):
    """An floating point number field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(FloatField, self).__init__(**kwargs)

    def to_python(self, value):
        try:
            value = float(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        try:
            value = float(value)
        except ValueError:
            self.error('FloatField only accepts float values')

        if self.min_value is not None and value < self.min_value:
            self.error('Float value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Float value is too large')

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return float(value)

class TimeStampField(FloatField):

    def __set__(self, instance, value):
        """Descriptor for assigning a value to a field in a document.
        """
        try:
            value = int(float(value))
            if value > 999999999999:
                value = value*0.001
            super(TimeStampField, self).__set__(instance, value)
        except ValueError:
            pass


class DecimalField(BaseField):
    """A fixed-point decimal number field.

    .. versionadded:: 0.3
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(DecimalField, self).__init__(**kwargs)

    def to_python(self, value):
        original_value = value
        if not isinstance(value, basestring):
            value = unicode(value)
        try:
            value = decimal.Decimal(value)
        except ValueError:
            return original_value
        return value

    def to_mongo(self, value):
        return unicode(value)

    def validate(self, value):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, basestring):
                value = str(value)
            try:
                value = decimal.Decimal(value)
            except Exception, exc:
                self.error('Could not convert value to decimal: %s' % exc)

        if self.min_value is not None and value < self.min_value:
            self.error('Decimal value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Decimal value is too large')


class BooleanField(BaseField):
    """A boolean field type.

    .. versionadded:: 0.1.2
    """

    def to_python(self, value):
        try:
            value = bool(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        if not isinstance(value, bool):
            self.error('BooleanField only accepts boolean values')


class DateTimeField(BaseField):
    """A datetime field.

    Note: Microseconds are rounded to the nearest millisecond.
      Pre UTC microsecond support is effecively broken.
      Use :class:`~mongoengine.fields.ComplexDateTimeField` if you
      need accurate microsecond support.
    """

    def validate(self, value):
        if not isinstance(value, (datetime.datetime, datetime.date)):
            self.error(u'cannot parse date "%s"' % value)

    def to_mongo(self, value):
        return self.prepare_query_value(None, value)

    def prepare_query_value(self, op, value):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)

        # Attempt to parse a datetime:
        # value = smart_str(value)
        # split usecs, because they are not recognized by strptime.
        if '.' in value:
            try:
                value, usecs = value.split('.')
                usecs = int(usecs)
            except ValueError:
                return None
        else:
            usecs = 0
        kwargs = {'microsecond': usecs}
        try:  # Seconds are optional, so try converting seconds first.
            return datetime.datetime(*time.strptime(value, '%Y-%m-%d %H:%M:%S')[:6],
                **kwargs)
        except ValueError:
            try:  # Try without seconds.
                return datetime.datetime(*time.strptime(value, '%Y-%m-%d %H:%M')[:5],
                    **kwargs)
            except ValueError:  # Try without hour/minutes/seconds.
                try:
                    return datetime.datetime(*time.strptime(value, '%Y-%m-%d')[:3],
                        **kwargs)
                except ValueError:
                    return None


class EmbeddedDocumentField(BaseField):
    """An embedded document field - with a declared document_type.
    Only valid values are subclasses of :class:`~mongoengine.EmbeddedDocument`.
    """

    def __init__(self, document_type, **kwargs):
        from document import EmbeddedDocument
        if not issubclass(document_type, EmbeddedDocument):
            self.error('Invalid embedded document class provided to an '
                       'EmbeddedDocumentField')
        self.document_type_obj = document_type
        super(EmbeddedDocumentField, self).__init__(**kwargs)

    @property
    def document_type(self):
        return self.document_type_obj

    def to_python(self, value):
        if not isinstance(value, self.document_type):
            return self.document_type._from_son(value)
        return value

    def to_mongo(self, value):
        if not isinstance(value, self.document_type):
            return value
        return self.document_type.to_mongo(value)

    def to_son(self, value):
        if not isinstance(value, self.document_type):
            return value
        return self.document_type.to_son(value)

    def validate(self, value):
        """Make sure that the document instance is an instance of the
        EmbeddedDocument subclass provided when the document was defined.
        """
        # Using isinstance also works for subclasses of self.document
        if not isinstance(value, self.document_type):
            self.error('Invalid embedded document instance provided to an '
                       'EmbeddedDocumentField')
        self.document_type.validate(value)

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)


class ListField(ComplexBaseField):
    """A list field that wraps a standard field, allowing multiple instances
    of the field to be used as a list in the database.

    If using with ReferenceFields see: :ref:`one-to-many-with-listfields`

    .. note::
        Required means it cannot be empty - as the default for ListFields is []
    """

    # ListFields cannot be indexed with _types - MongoDB doesn't support this
    _index_with_types = False

    def __init__(self, field=None, **kwargs):
        self.field = field
        kwargs.setdefault('default', lambda: [])
        super(ListField, self).__init__(**kwargs)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, (list, tuple, QuerySet)) or isinstance(value, basestring):
            self.error('Only lists and tuples may be used in a list field')
        super(ListField, self).validate(value)

    def prepare_query_value(self, op, value):
        if self.field:
            if op in ('set', 'unset') and (not isinstance(value, basestring)
                                           and not isinstance(value, BaseDocument)
                                           and hasattr(value, '__iter__')):
                return [self.field.prepare_query_value(op, v) for v in value]
            return self.field.prepare_query_value(op, value)
        return super(ListField, self).prepare_query_value(op, value)


class SortedListField(ListField):
    """A ListField that sorts the contents of its list before writing to
    the database in order to ensure that a sorted list is always
    retrieved.

    .. warning::
        There is a potential race condition when handling lists.  If you set /
        save the whole list then other processes trying to save the whole list
        as well could overwrite changes.  The safest way to append to a list is
        to perform a push operation.

    .. versionadded:: 0.4
    .. versionchanged:: 0.6 - added reverse keyword
    """

    _ordering = None
    _order_reverse = False

    def __init__(self, field, **kwargs):
        if 'ordering' in kwargs.keys():
            self._ordering = kwargs.pop('ordering')
        if 'reverse' in kwargs.keys():
            self._order_reverse = kwargs.pop('reverse')
        super(SortedListField, self).__init__(field, **kwargs)

    def to_mongo(self, value):
        value = super(SortedListField, self).to_mongo(value)
        if self._ordering is not None:
            return sorted(value, key=itemgetter(self._ordering), reverse=self._order_reverse)
        return sorted(value, reverse=self._order_reverse)


class DictField(ComplexBaseField):
    """A dictionary field that wraps a standard Python dictionary. This is
    similar to an embedded document, but the structure is not defined.

    .. note::
        Required means it cannot be empty - as the default for ListFields is []

    .. versionadded:: 0.3
    .. versionchanged:: 0.5 - Can now handle complex / varying types of data
    """

    def __init__(self, basecls=None, field=None, *args, **kwargs):
        self.field = field
        self.basecls = basecls or BaseField
        if not issubclass(self.basecls, BaseField):
            self.error('DictField only accepts dict values')
        kwargs.setdefault('default', lambda: {})
        super(DictField, self).__init__(*args, **kwargs)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, dict):
            self.error('Only dictionaries may be used in a DictField')

        if any(k for k in value.keys() if not isinstance(k, basestring)):
            self.error('Invalid dictionary key - documents must have only string keys')
        if any(('.' in k or '$' in k) for k in value.keys()):
            self.error('Invalid dictionary key name - keys may not contain "."'
                       ' or "$" characters')
        super(DictField, self).validate(value)

    def lookup_member(self, member_name):
        return DictField(basecls=self.basecls, db_field=member_name)

    def prepare_query_value(self, op, value):
        match_operators = ['contains', 'icontains', 'startswith',
                           'istartswith', 'endswith', 'iendswith',
                           'exact', 'iexact']

        if op in match_operators and isinstance(value, basestring):
            return StringField().prepare_query_value(op, value)

        return super(DictField, self).prepare_query_value(op, value)


class MapField(DictField):
    """A field that maps a name to a specified field type. Similar to
    a DictField, except the 'value' of each item must match the specified
    field type.

    .. versionadded:: 0.5
    """

    def __init__(self, field=None, *args, **kwargs):
        if not isinstance(field, BaseField):
            self.error('Argument to MapField constructor must be a valid '
                       'field')
        super(MapField, self).__init__(field=field, *args, **kwargs)


class BinaryField(BaseField):
    """A binary data field.
    """

    def __init__(self, max_bytes=None, **kwargs):
        self.max_bytes = max_bytes
        super(BinaryField, self).__init__(**kwargs)

    def to_mongo(self, value):
        return Binary(value)

    def validate(self, value):
        if not isinstance(value, (str, unicode, Binary)):
            self.error("BinaryField only accepts instances of "
                       "(%s, %s, Binary)" % (str.__name__, unicode.__name__))

        if self.max_bytes is not None and len(value) > self.max_bytes:
            self.error('Binary value is too long')

class UUIDField(BaseField):
    """A UUID field.
    """
    _binary = None

    def __init__(self, binary=None, **kwargs):
        """
        Store UUID data in the database

        :param binary: (optional) boolean store as binary.

        .. versionchanged:: 0.6.19
        """
        if binary is None:
            binary = False
            msg = ("UUIDFields will soon default to store as binary, please "
                   "configure binary=False if you wish to store as a string")
            warnings.warn(msg, FutureWarning)
        self._binary = binary
        super(UUIDField, self).__init__(**kwargs)

    def to_python(self, value):
        if not self._binary:
            original_value = value
            try:
                if not isinstance(value, basestring):
                    value = unicode(value)
                return uuid.UUID(value)
            except:
                return original_value
        return value

    def to_mongo(self, value):
        if not self._binary:
            return unicode(value)
        return value

    def prepare_query_value(self, op, value):
        if value is None:
            return None
        return self.to_mongo(value)

    def validate(self, value):
        if not isinstance(value, uuid.UUID):
            if not isinstance(value, basestring):
                value = str(value)
            try:
                value = uuid.UUID(value)
            except Exception, exc:
                self.error('Could not convert to UUID: %s' % exc)
