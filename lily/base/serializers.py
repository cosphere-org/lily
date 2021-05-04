
from datetime import datetime, date
from copy import deepcopy

from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.contrib.postgres.fields import ArrayField


class MissingTypeError(Exception):
    """Could not find `_type` attribute.

    When Serializer is missing the semantic `_type` denoting a type which
    Entity a given Serializer represents.

    """


class MissingRequiredArgumentsException(Exception):
    pass


class Field:

    def __init__(
        self,
        required=True,
        default=None,
        validators=None,
        many=None,
        *args,
        **kwargs
    ):
        self.required = required
        self.default = default
        self.validators = validators or []
        self.many = many

        if self.default:
            self.required = False

    def serialize(self, value):
        return value


class BooleanField(Field):
    pass


class CharField(Field):

    def __init__(self, *args, min_length=None, max_length=None, **kwargs):

        self.min_length = min_length
        self.max_length = max_length

        super(CharField, self).__init__(*args, **kwargs)


class ChoiceField(Field):
    pass


class DictField(Field):
    pass


class JSONSchemaField(Field):

    def __init__(self, *args, schema=None, **kwargs):
        super(JSONSchemaField, self).__init__(*args, **kwargs)

        from .models import JSONSchemaValidator

        self.validators = [
            JSONSchemaValidator(schema=schema)
        ]


class DateField(Field):

    def serialize(self, value):
        if value:
            if isinstance(value, datetime):
                value = value.date()

            if isinstance(value, date):
                value = value.isoformat()

            return value


class DateTimeField(Field):

    def serialize(self, value):
        if value:
            if isinstance(value, (datetime, date)):
                value = value.isoformat().replace('+00:00', 'Z')

            if not value.endswith('Z'):
                value += 'Z'

            return value


class EnumChoiceField(ChoiceField):

    def __init__(self, *args, enum_name=None, enum=None, **kwargs):

        self.choices = {}
        for e in (kwargs.get('choices', []) or []):
            if isinstance(e, (tuple, list)):
                self.choices[e[0]] = e[0]

            else:
                self.choices[e] = e

        if enum_name:
            self.enum_name = enum_name

        if enum:
            self.enum_name = enum.__name__
            kwargs['choices'] = [e.value for e in enum]
            self.choices = {e: e for e in kwargs['choices']}

        if not (enum_name or enum):
            raise MissingRequiredArgumentsException(
                'either `enum_name` or `enum` must be provided')

        super(EnumChoiceField, self).__init__(*args, **kwargs)


class EmailField(Field):
    pass


class FloatField(Field):

    def __init__(self, *args, min_value=None, max_value=None, **kwargs):

        self.min_value = min_value
        self.max_value = max_value

        super(FloatField, self).__init__(*args, **kwargs)

    def serialize(self, value):
        if value is not None:
            return float(value)


class IntegerField(Field):

    def __init__(self, *args, min_value=None, max_value=None, **kwargs):

        self.min_value = min_value
        self.max_value = max_value

        super(IntegerField, self).__init__(*args, **kwargs)

    def serialize(self, value):

        if value is not None:
            return int(value)


class DecimalField(Field):
    pass


class JSONField(Field):
    pass


class ListField(Field):

    def __init__(self, child, *args, **kwargs):
        self.child = child

        super(ListField, self).__init__(*args, **kwargs)

    def serialize(self, value):

        if value is not None:
            return [self.child.serialize(v) for v in value]


class ListSerializer(Field):
    pass


class SerializerMethodField(Field):
    pass


class URLField(Field):
    pass


class UUIDField(Field):
    pass


class NullBooleanField(Field):
    pass


class ValidationError(Field):
    pass


class ReadOnlyField(Field):
    pass


class Serializer:

    _meta_cache = {}

    def __init__(self, instance=None, context=None, many=None, required=True):
        self.instance = instance
        self.many = many
        self.required = required
        self.context = context

        if 'fields' not in Serializer._meta_cache:
            self._fields = {}
            for attr in dir(self):
                if attr in ['data', 'instance', 'many', 'required', 'context']:
                    continue

                if isinstance(getattr(self, attr), SerializerMethodField):
                    self._fields[attr] = {
                        'is_field': True,
                        'is_method': True,
                        'serializer': getattr(self, attr),
                    }

                elif isinstance(getattr(self, attr), Field):
                    self._fields[attr] = {
                        'is_field': True,
                        'is_method': False,
                        'serializer': getattr(self, attr),
                    }

                elif isinstance(getattr(self, attr), Serializer):
                    self._fields[attr] = {
                        'is_field': False,
                        'is_method': False,
                        'serializer': getattr(self, attr),
                    }

        else:
            self._fields = Serializer._meta_cache['fields']

    def get_fields(self):
        """Calculate and return fields required by the schema renderer."""
        fields = {}
        allowed_types = (
            SerializerMethodField,
            Field,
            Serializer,
        )
        for attr in dir(self):
            if attr == 'data':
                continue

            if isinstance(getattr(self, attr), allowed_types):
                fields[attr] = getattr(self, attr)

        return fields

    def render_access(self, instance):

        try:
            out_access = {}
            for cmd, is_active in self.get_access(instance):
                if isinstance(cmd, str):
                    name = cmd

                else:
                    name = cmd.command_conf['name']

                out_access[name] = is_active

            return out_access

        except AttributeError:
            pass

        return {}

    def is_valid(self):
        return True

    def serialize(self):

        serialized = {}
        for name, field in self._fields.items():
            s = field['serializer']
            required = getattr(s, 'required', True)
            default = getattr(s, 'default', True)
            is_method = field['is_method']
            is_field = field['is_field']

            # -- VALUE
            if not is_method and not required:
                if isinstance(self.instance, dict):
                    value = self.instance.get(name, default)

                else:
                    value = getattr(self.instance, name, default)

            elif not is_method:
                if isinstance(self.instance, dict):
                    value = self.instance.get(name, default)

                else:
                    value = getattr(self.instance, name, default)

            # -- SERIALIZATION
            if is_method:
                serialized[name] = (
                    getattr(self, f'get_{name}')(self.instance))

            elif is_field:
                if s.many:
                    serialized[name] = [s.serialize(v) for v in value]

                else:
                    serialized[name] = s.serialize(value)

            else:
                def __serialize(v):
                    return s.__class__(v, context=self.context).data

                # -- if value of nested object is none just return it
                if not value:

                    if s.many:
                        serialized[name] = []

                    else:
                        serialized[name] = value

                if value and s.many:
                    try:
                        serialized[name] = [__serialize(v) for v in value]

                    except TypeError:
                        serialized[name] = [
                            __serialize(v) for v in value.all()]

                elif value:
                    serialized[name] = __serialize(value)

        # -- for `AbstractSerializer` do not attach any extra data they are
        # -- here only for storing SubEntities without having their own
        # -- interpretation
        if isinstance(self, AbstractSerializer):
            return serialized

        try:
            serialized['@type'] = self._type

        except AttributeError:
            raise MissingTypeError(
                'Each Serializer must have `type` specified which informs '
                'the client about the semantic type a result of the '
                'Serializer represents')

        access = self.render_access(self.instance)
        if access:
            serialized['@access'] = access

        return serialized

    @property
    def data(self):
        return self.serialize()


class AbstractSerializer(Serializer):
    """Store abstract entities.

    Designed for storing only abstract entities without having it's
    own meaning.

    """


class ModelSerializer(Serializer):

    def __init__(self, instance=None, context=None, many=None):
        from .models import (
            JSONSchemaField as ModelJSONSchemaField,
            EnumChoiceField as ModelEnumChoiceField,
        )

        super(ModelSerializer, self).__init__(instance, context, many)

        if 'fields' not in Serializer._meta_cache:

            model_fields_index = {}

            for field in self.Meta.model._meta.fields:
                model_fields_index[field.name] = field

                if isinstance(field, (models.OneToOneField, models.ForeignKey)):  # noqa
                    model_fields_index[f'{field.name}_id'] = field

            for field in self.Meta.fields:
                if field not in self._fields:
                    serializer = None

                    try:
                        model_field = model_fields_index[field]
                        required = True
                        if model_field.null or model_field.blank:
                            required = False

                        elif (model_field.default is not None and
                                model_field.default != NOT_PROVIDED):
                            required = False

                        if isinstance(model_field, models.AutoField):
                            serializer = IntegerField(required=required)

                        elif isinstance(model_field, models.OneToOneField):
                            serializer = IntegerField(required=required)

                        elif isinstance(model_field, models.ForeignKey):
                            serializer = IntegerField(required=required)

                        elif isinstance(model_field, models.IntegerField):
                            serializer = IntegerField(required=required)

                        elif isinstance(model_field, models.FloatField):
                            serializer = FloatField(required=required)

                        elif isinstance(model_field, models.JSONField):
                            serializer = JSONField(
                                required=required,
                                validators=model_field.validators)

                        elif isinstance(model_field, ModelJSONSchemaField):
                            serializer = JSONSchemaField(
                                required=required,
                                validators=model_field.validators)

                        elif isinstance(model_field, ArrayField):
                            if isinstance(model_field.base_field, models.IntegerField):  # noqa
                                base_serializer = IntegerField

                            elif isinstance(model_field.base_field, models.FloatField):  # noqa
                                base_serializer = FloatField

                            elif isinstance(model_field.base_field, models.CharField):  # noqa
                                base_serializer = CharField

                            serializer = base_serializer(many=True, required=required)  # noqa

                        elif isinstance(model_field, ModelEnumChoiceField):
                            serializer = EnumChoiceField(
                                required=required,
                                enum_name=model_field.enum_name,
                                choices=[c[0] for c in model_field.choices])

                        elif isinstance(model_field, models.CharField):
                            serializer = CharField(
                                required=required,
                                min_length=getattr(
                                    model_field, 'min_length', None),
                                max_length=getattr(
                                    model_field, 'max_length', None),
                            )

                        elif isinstance(model_field, models.TextField):
                            serializer = CharField(required=required)

                        elif isinstance(model_field, models.BooleanField):
                            serializer = BooleanField(required=required)

                        elif isinstance(model_field, models.DateTimeField):
                            serializer = DateTimeField(required=required)

                        elif isinstance(model_field, models.DateField):
                            serializer = DateField(required=required)

                        elif isinstance(model_field, models.URLField):
                            serializer = URLField(required=required)

                    except KeyError:
                        f = getattr(self.Meta.model, field)

                        if f and isinstance(f, property):
                            try:
                                t = f.fget.__annotations__['return']

                            except KeyError:
                                raise Exception('MISSING_TYPE_FOR_FIELD')

                            if t == bool:
                                serializer = BooleanField(required=False)

                            elif t == int:
                                serializer = IntegerField(required=False)

                            elif t == float:
                                serializer = FloatField(required=False)

                            elif t == str:
                                serializer = CharField(required=False)

                        else:
                            serializer = Field()

                    if not serializer:
                        raise Exception('CANNOT_MATCH_FIELD')

                    self._fields[field] = {
                        'serializer': serializer,
                        'is_field': True,
                        'is_method': False,
                    }

        else:
            self._fields = Serializer._meta_cache['fields']

    def get_fields(self):
        """Calculate and return fields required by the schema renderer."""

        return {
            attr: field['serializer']
            for attr, field in self._fields.items()
        }


class EmptySerializer(Serializer):

    _type = 'empty'


class ObjectSerializer(Serializer):

    _type = 'object'

    def serialize(self):

        serialized = deepcopy(self.instance)
        serialized['@type'] = self._type

        return serialized


class CommandSerializer(Serializer):

    _type = 'command'

    name = CharField()

    method = ChoiceField(choices=('post', 'get', 'delete', 'put'))

    uri = URLField()

    body = DictField(required=False)

    query = DictField(required=False)

    result = DictField(required=False)
