
from copy import deepcopy

from django.db import models


class MissingTypeError(Exception):
    """Could not find `_type` attribute.

    When Serializer is missing the semantic `_type` denoting a type which
    Entity a given Serializer represents.

    """


class MissingRequiredArgumentsException(Exception):
    pass


class Field:

    def __init__(self, required=True, default=None, *args, **kwargs):
        self.required = required
        self.default = default

    def serialize(self, value):
        return value


class BooleanField(Field):
    pass


class CharField(Field):
    pass


class ChoiceField(Field):
    pass


class DictField(Field):
    pass


class JSONSchemaField(Field):
    pass


class DateField(Field):
    pass

    # def serialize(self, value):
    #     if value:
    #         return value.isoformat().replace('+00:00', 'Z')


class DateTimeField(Field):
    pass

    # def serialize(self, value):
    #     if value:
    #         return value.isoformat().replace('+00:00', 'Z')


class EnumChoiceField(ChoiceField):

    def __init__(self, *args, enum_name=None, enum=None, **kwargs):

        if enum_name:
            self.enum_name = enum_name

        if enum:
            self.enum_name = enum.__name__
            kwargs['choices'] = [e.value for e in enum]

        if not (enum_name or enum):
            raise MissingRequiredArgumentsException(
                'either `enum_name` or `enum` must be provided')

        super(EnumChoiceField, self).__init__(*args, **kwargs)


class EmailField(Field):
    pass


class FloatField(Field):
    pass


class IntegerField(Field):
    pass


class JSONField(Field):
    pass


class ListField(Field):
    pass


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

    def __init__(self, instance=None, context=None, many=None):
        self.instance = instance
        self.many = many
        self.context = context

        if 'fields' not in Serializer._meta_cache:
            self._fields = {}
            for attr in dir(self):
                if attr == 'data':
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

            if not is_method and not required:
                if isinstance(self.instance, dict):
                    value = self.instance.get(name, default)

                else:
                    value = getattr(self.instance, name, default)

            elif not is_method:
                if isinstance(self.instance, dict):
                    value = self.instance[name]

                else:
                    value = getattr(self.instance, name)

            if is_method:
                serialized[name] = (
                    getattr(self, f'get_{name}')(self.instance))

            elif is_field:
                serialized[name] = s.serialize(value)

            else:
                def __serialize(v):
                    return s.__class__(v, context=self.context).data

                # -- if value of nested object is none just return it
                if not value:
                    serialized[name] = value

                if value and s.many:
                    try:
                        serialized[name] = [__serialize(v) for v in value]

                    except TypeError:
                        serialized[name] = [
                            __serialize(v) for v in value.all()]

                elif value:
                    serialized[name] = __serialize(value)

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


class ModelSerializer(Serializer):

    def __init__(self, instance=None, context=None, many=None):
        super(ModelSerializer, self).__init__(instance, context, many)

        if 'fields' not in Serializer._meta_cache:

            model_fields_index = {}
            for field in self.Meta.model._meta.fields:
                model_fields_index[field.name] = field

                if isinstance(field, (models.OneToOneField, models.ForeignKey)):  # noqa
                    model_fields_index[f'{field.name}_id'] = field

            for field in self.Meta.fields:
                if field not in self._fields:
                    try:
                        model_field = model_fields_index[field]

                        if isinstance(model_field, models.AutoField):
                            serializer = IntegerField()

                        elif isinstance(model_field, models.IntegerField):
                            serializer = IntegerField()

                        elif isinstance(model_field, models.OneToOneField):
                            serializer = IntegerField()

                        elif isinstance(model_field, models.ForeignKey):
                            serializer = IntegerField()

                        elif isinstance(model_field, models.CharField):
                            serializer = CharField()

                        elif isinstance(model_field, models.TextField):
                            serializer = CharField()

                        elif isinstance(model_field, models.JSONField):
                            serializer = JSONField()

                        elif isinstance(model_field, models.BooleanField):
                            serializer = BooleanField()

                        elif isinstance(model_field, models.DateTimeField):
                            serializer = DateTimeField()

                        elif isinstance(model_field, models.DateField):
                            serializer = DateField()

                        elif isinstance(model_field, models.URLField):
                            serializer = URLField()

                    except KeyError:
                        serializer = Field()

                    self._fields[field] = {
                        'serializer': serializer,
                        'is_field': True,
                        'is_method': False,
                    }

        else:
            self._fields = Serializer._meta_cache['fields']


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
