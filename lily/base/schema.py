# -*- coding: utf-8 -*-

from . import serializers, parsers


class MissingReturnStatementError(Exception):
    """
    When Method used for calculating dynamical serialization field is
    missing the return annotation.

    """


class MissingMethodForFieldError(Exception):
    """
    When Method used for calculating dynamical serialization field is
    missing.

    """


class MissingSchemaMappingError(Exception):
    """
    When mapping between any type of a field in the Serializer and schema
    is missing.

    """


def to_schema(serializer):
    schema = {
        'type': 'object',
        'required': [],
        'properties': {},
    }

    try:
        fields = serializer.get_fields()

    except TypeError:
        fields = serializer().get_fields()

    for name, field in fields.items():

        # -- list serializer
        if isinstance(field, serializers.ListSerializer):
            schema['properties'][name] = {
                'type': 'array',
                'items': to_schema(field.child.__class__()),
            }
            if field.child.required:
                schema['required'].append(name)

        # -- singleton nested serializer
        elif (
                isinstance(field, serializers.Serializer) or
                isinstance(field, parsers.BodyParser) or
                isinstance(field, parsers.QueryParser)):
            schema['properties'][name] = to_schema(field)

            if field.required:
                schema['required'].append(name)

        # -- method serializer
        elif isinstance(field, serializers.SerializerMethodField):
            schema = method_field_to_schema(serializer, name, field, schema)

        # -- normal field boolean field
        elif is_simple_field(field):
            schema['properties'][name] = simple_field_to_schema(field)
            if field.required:
                schema['required'].append(name)

        # -- list field
        elif isinstance(field, serializers.ListField):
            if is_simple_field(field.child):
                schema['properties'][name] = {
                    'type': 'array',
                    'items': simple_field_to_schema(field.child),
                }

            else:
                schema['properties'][name] = {
                    'type': 'array',
                    'items': to_schema(field.child),
                }

            if field.child.required:
                schema['required'].append(name)

        # -- all not covered cases should raise an Error
        else:
            raise MissingSchemaMappingError(
                '{serializer}.{name}'.format(
                    serializer=serializer.__name__,
                    name=name))

    if not schema['required']:
        del schema['required']

    return schema


def method_field_to_schema(serializer, name, field, schema):
    try:
        method = getattr(serializer, 'get_{}'.format(name))
        return_value = method.__annotations__['return']

    except KeyError:
        raise MissingReturnStatementError()

    except AttributeError:
        raise MissingMethodForFieldError()

    else:
        if isinstance(return_value, list):
            item_type = return_value[0]

            if isinstance(item_type(), serializers.Serializer):
                schema['properties'][name] = {
                    'type': 'array',
                    'items': to_schema(item_type),
                }

            else:
                schema['properties'][name] = {
                    'type': 'array',
                    'items': {
                        'type': native_type_to_schema(item_type),
                    },
                }

        elif isinstance(return_value(), serializers.Serializer):
            schema['properties'][name] = to_schema(return_value)

        else:
            schema['properties'][name] = {
                'type': 'object',
                'type': native_type_to_schema(return_value),
            }

        schema['required'].append(name)

    return schema


def is_simple_field(field):
    return isinstance(
        field,
        (
            serializers.BooleanField,
            serializers.CharField,
            serializers.ChoiceField,
            serializers.DictField,
            serializers.EmailField,
            serializers.FloatField,
            serializers.IntegerField,
            serializers.DecimalField,
            serializers.URLField,
            serializers.JSONField,
        ))


def simple_field_to_schema(field):

    is_field = lambda _type: isinstance(field, _type)

    if is_field(serializers.BooleanField):
        field_schema = {
            'type': 'boolean',
        }

    # -- must be before CharField
    elif is_field(serializers.EmailField):
        field_schema = {
            'type': 'string',
            'format': 'email',
        }

    # -- must be before CharField
    elif is_field(serializers.URLField):
        field_schema = {
            'type': 'string',
            'format': 'uri',
        }

    elif is_field(serializers.CharField):

        field_schema = {
            'type': 'string',
        }

        if field.min_length:
            field_schema['minLength'] = field.min_length

        if field.max_length:
            field_schema['maxLength'] = field.max_length

    elif is_field(serializers.IntegerField):

        field_schema = {
            'type': 'number',
        }

        if field.min_value:
            field_schema['minimum'] = field.min_value

        if field.max_value:
            field_schema['maximum'] = field.max_value

    elif is_field(serializers.DecimalField):

        field_schema = {
            'type': 'string',
        }

    elif is_field(serializers.FloatField):

        field_schema = {
            'type': 'number',
        }

        if field.min_value:
            field_schema['minimum'] = field.min_value

        if field.max_value:
            field_schema['maximum'] = field.max_value

    elif is_field(serializers.ChoiceField):

        field_schema = {
            'type': 'string',
            'enum': sorted(field.choices.keys()),
        }

    elif is_field(serializers.DictField):
        field_schema = {
            'type': 'object',
        }

    elif is_field(serializers.JSONField):
        field_schema = {
            'type': 'object',
        }

    return field_schema


def native_type_to_schema(_type):

    if _type == int:
        return 'integer'

    elif _type == float:
        return 'float'

    elif _type == str:
        return 'string'

    elif _type == bool:
        return 'boolean'
