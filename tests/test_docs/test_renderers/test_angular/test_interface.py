# -*- coding: utf-8 -*-

from django.test import TestCase
import pytest

from lily.docs.renderers.angular.interface import Interface, Enum
from lily.docs.renderers.angular.utils import normalize_indentation


class EnumTestCase(TestCase):

    #
    # NAME
    #
    def test_name(self):
        assert Enum(
            'age', [], 'ReadCardsResponse'
        ).name == 'ReadCardsResponseAge'

    def test_name__with_index(self):
        assert Enum(
            'age', [], 'BulkDeletePathsResponse', 2
        ).name == 'BulkDeletePathsResponseAge2'

    #
    # RENDER
    #
    def test_render(self):

        enum = Enum('age', ['AA', 'BB'], 'ReadCardsResponse')

        assert enum.render() == normalize_indentation('''
            export enum ReadCardsResponseAge {
                AA: 'AA';
                BB: 'BB';
            }
        ''', 0)

    def test_render__removes_duplicates(self):

        enum = Enum('age', ['AA', 'BB', 'AA'], 'ReadCardsResponse')

        assert enum.render() == normalize_indentation('''
            export enum ReadCardsResponseAge {
                AA: 'AA';
                BB: 'BB';
            }
        ''', 0)

    def test_render__sorts_values(self):

        enum = Enum('age', ['XX', 'AA', 'BB'], 'ReadCardsResponse')

        assert enum.render() == normalize_indentation('''
            export enum ReadCardsResponseAge {
                AA: 'AA';
                BB: 'BB';
                XX: 'XX';
            }
        ''', 0)


class InterfaceTestCase(TestCase):

    def test_name(self):

        assert Interface(
            'READ_CARDS', Interface.TYPES.RESPONSE, {}
        ).name == 'ReadCardsResponse'

        assert Interface(
            'READ_CARDS', Interface.TYPES.REQUEST_QUERY, {}
        ).name == 'ReadCardsQuery'

        assert Interface(
            'READ_CARDS', Interface.TYPES.REQUEST_BODY, {}
        ).name == 'ReadCardsBody'

    def test_append_enum__no_duplicates(self):

        interface = Interface('READ_CARDS', Interface.TYPES.RESPONSE, {})

        e0 = interface.append_enum('age', [19, 91])

        assert len(interface.enums) == 1
        assert e0 == Enum('age', [19, 91], interface.name, None)

    def test_append_enum__with_duplicates(self):

        interface = Interface('READ_CARDS', Interface.TYPES.RESPONSE, {})

        e0 = interface.append_enum('age', [19, 91])
        e1 = interface.append_enum('age', [19, 91])

        assert len(interface.enums) == 1
        assert e0 == e1

    def test_append_enum__same_values_different_names(self):

        interface = Interface('READ_CARDS', Interface.TYPES.RESPONSE, {})

        e0 = interface.append_enum('age', [19, 91])  # noqa
        e1 = interface.append_enum('years', [19, 91])  # noqa

        assert len(interface.enums) == 2

    def test_append_enum__same_name_different_values(self):

        interface = Interface('X', Interface.TYPES.RESPONSE, {})

        e0 = interface.append_enum('age', [19, 91])  # noqa
        e1 = interface.append_enum('age', [19])

        assert len(interface.enums) == 2
        assert e1 == Enum('age', [19], interface.name, 1)


@pytest.mark.parametrize(
    'schema, expected',
    [
        # -- case 0 - empty schema
        (
            {'type': 'object', 'properties': {}},
            normalize_indentation('''
            export interface ReadCardsResponse {
            }
            ''', 0)
        ),

        # -- case 1 - simple schema
        (
            {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'integer',
                        'minimum': 18,
                    },
                    'name': {
                        'maxLength': 123,
                        'type': 'string',
                    },
                },
            },
            normalize_indentation('''
            export interface ReadCardsResponse {
                age: number;
                name?: string;
            }
            ''', 0)
        ),

        # -- case 2 - simple array
        (
            {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'array',
                        'items': {
                            'type': 'integer'
                        },
                    },
                    'surname': {
                        'maxLength': 123,
                        'type': 'string',
                    },
                },
            },
            normalize_indentation('''
            export interface ReadCardsResponse {
                age: number[];
                surname?: string;
            }
            ''', 0)
        ),

        # -- case 3 - enum
        (
            {
                'type': 'object',
                'required': ['occupation'],
                'properties': {
                    'occupation': {
                        'type': 'string',
                        'enum': ['AA', 'BB'],
                    },
                    'surname': {
                        'maxLength': 123,
                        'type': 'string',
                    },
                },
            },
            normalize_indentation('''
            export enum ReadCardsResponseOccupation {
                AA: 'AA';
                BB: 'BB';
            }

            export interface ReadCardsResponse {
                occupation: ReadCardsResponseOccupation;
                surname?: string;
            }
            ''', 0)
        ),

        # -- case 4 - enums
        (
            {
                'type': 'object',
                'required': ['occupation'],
                'properties': {
                    'occupation': {
                        'type': 'string',
                        'enum': ['AA', 'BB'],
                    },
                    'age': {
                        'type': 'string',
                        'enum': ['12', '21', '33'],
                    },
                    'surname': {
                        'maxLength': 123,
                        'type': 'string',
                    },
                },
            },
            normalize_indentation('''
            export enum ReadCardsResponseAge {
                12: '12';
                21: '21';
                33: '33';
            }

            export enum ReadCardsResponseOccupation {
                AA: 'AA';
                BB: 'BB';
            }

            export interface ReadCardsResponse {
                age?: ReadCardsResponseAge;
                occupation: ReadCardsResponseOccupation;
                surname?: string;
            }
            ''', 0)
        ),

        # -- case 5 - enums array
        (
            {
                'type': 'object',
                'required': ['occupation'],
                'properties': {
                    'occupation': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'enum': ['AA', 'BB'],
                        }
                    },
                    'surname': {
                        'maxLength': 123,
                        'type': 'string',
                    },
                },
            },
            normalize_indentation('''
            export enum ReadCardsResponseOccupation {
                AA: 'AA';
                BB: 'BB';
            }

            export interface ReadCardsResponse {
                occupation: ReadCardsResponseOccupation[];
                surname?: string;
            }
            ''', 0)
        ),

        # -- case 6 - 1 level deep nested
        (
            {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'integer',
                    },
                    'person': {
                        'type': 'object',
                        'required': ['name'],
                        'properties': {
                            'name': {
                                'type': 'string',
                            },
                            'category': {
                                'type': 'number'
                            }
                        },
                    },
                },
            },
            normalize_indentation('''
            export interface ReadCardsResponse {
                age: number;
                person?: {
                    category?: number;
                    name: string;
                };
            }
            ''', 0)
        ),

        # -- case 7 - 2 levels deep nested
        (
            {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'integer',
                    },
                    'person': {
                        'type': 'object',
                        'required': ['name'],
                        'properties': {
                            'name': {
                                'type': 'string',
                            },
                            'category': {
                                'type': 'object',
                                'required': ['id'],
                                'properties': {
                                    'id': {
                                        'type': 'integer',
                                    },
                                    'name': {
                                        'type': 'string',
                                    }
                                }
                            }
                        },
                    },
                },
            },
            normalize_indentation('''
            export interface ReadCardsResponse {
                age: number;
                person?: {
                    category?: {
                        id: number;
                        name?: string;
                    };
                    name: string;
                };
            }
            ''', 0)
        ),

        # -- case 8 - nested array
        (
            {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'integer',
                    },
                    'people': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'required': ['name'],
                            'properties': {
                                'name': {
                                    'type': 'string',
                                },
                                'category': {
                                    'type': 'number'
                                }
                            },
                        },
                    },
                },
            },
            normalize_indentation('''
            export interface ReadCardsResponse {
                age: number;
                people?: {
                    category?: number;
                    name: string;
                }[];
            }
            ''', 0)
        ),

        # -- case 9 - nested with enums
        (
            {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'string',
                        'enum': ['A', 'B'],
                    },
                    'people': {
                        'type': 'object',
                        'required': ['category'],
                        'properties': {
                            'category': {
                                'type': 'string',
                                'enum': ['CAT0', 'CAT1', 'CAT2'],
                            }
                        },
                    },
                },
            },
            normalize_indentation('''
            export enum ReadCardsResponseAge {
                A: 'A';
                B: 'B';
            }

            export enum ReadCardsResponseCategory {
                CAT0: 'CAT0';
                CAT1: 'CAT1';
                CAT2: 'CAT2';
            }

            export interface ReadCardsResponse {
                age: ReadCardsResponseAge;
                people?: {
                    category: ReadCardsResponseCategory;
                };
            }
            ''', 0)
        ),
    ], ids=list([str(i) for i in range(10)]))
def test_render(schema, expected):
    result = Interface('READ_CARDS', Interface.TYPES.RESPONSE, schema).render()

    assert result == expected
