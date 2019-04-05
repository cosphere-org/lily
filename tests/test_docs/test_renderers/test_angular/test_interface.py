
from django.test import TestCase
import pytest

from lily.docs.renderers.angular.interface import Interface, Enum
from lily.base.utils import normalize_indentation


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
                AA = 'AA',
                BB = 'BB',
            }
        ''', 0)

    def test_render__numerical(self):

        enum = Enum('age', [0, 1], 'ReadCardsResponse')

        assert enum.render() == normalize_indentation('''
            export enum ReadCardsResponseAge {
                VALUE_0 = 0,
                VALUE_1 = 1,
            }
        ''', 0)

    def test_render__removes_duplicates(self):

        enum = Enum('age', ['AA', 'BB', 'AA'], 'ReadCardsResponse')

        assert enum.render() == normalize_indentation('''
            export enum ReadCardsResponseAge {
                AA = 'AA',
                BB = 'BB',
            }
        ''', 0)

    def test_render__sorts_values(self):

        enum = Enum('age', ['XX', 'AA', 'BB'], 'ReadCardsResponse')

        assert enum.render() == normalize_indentation('''
            export enum ReadCardsResponseAge {
                AA = 'AA',
                BB = 'BB',
                XX = 'XX',
            }
        ''', 0)


class InterfaceTestCase(TestCase):

    def test_name(self):

        assert Interface(
            'READ_CARDS', Interface.TYPES.RESPONSE, {'hi': 'there'}, ''
        ).name == 'ReadCardsResponse'

        assert Interface(
            'READ_CARDS', Interface.TYPES.REQUEST_QUERY, {'hi': 'there'}, ''
        ).name == 'ReadCardsQuery'

        assert Interface(
            'READ_CARDS', Interface.TYPES.REQUEST_BODY, {'hi': 'there'}, ''
        ).name == 'ReadCardsBody'

    def test_is_empty(self):

        assert Interface('X', 'X', None, '').is_empty() is True
        assert Interface('X', 'X', {}, '').is_empty() is True
        assert Interface('X', 'X', {'a': 'b'}, '').is_empty() is False

    def test_append_enum__no_duplicates(self):

        interface = Interface('READ_CARDS', Interface.TYPES.RESPONSE, {}, '')

        e0 = interface.append_enum('age', [19, 91])

        assert len(interface.enums) == 1
        assert e0 == Enum('age', [19, 91], interface.name, None)

    def test_append_enum__with_duplicates(self):

        interface = Interface('READ_CARDS', Interface.TYPES.RESPONSE, {}, '')

        e0 = interface.append_enum('age', [19, 91])
        e1 = interface.append_enum('age', [19, 91])

        assert len(interface.enums) == 1
        assert e0 == e1

    def test_append_enum__same_values_different_names(self):

        interface = Interface('READ_CARDS', Interface.TYPES.RESPONSE, {}, '')

        e0 = interface.append_enum('age', [19, 91])  # noqa
        e1 = interface.append_enum('years', [19, 91])  # noqa

        assert len(interface.enums) == 2

    def test_append_enum__same_name_different_values(self):

        interface = Interface('X', Interface.TYPES.RESPONSE, {}, '')

        e0 = interface.append_enum('age', [19, 91])  # noqa
        e1 = interface.append_enum('age', [19])

        assert len(interface.enums) == 2
        assert e1 == Enum('age', [19], interface.name, 1)


@pytest.mark.parametrize(
    'schema, bulk_read_field, expected',
    [
        # -- case 0 - None schema
        (
            None,
            None,
            '',
        ),

        # -- case 1 - {} schema
        (
            {},
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export interface ReadCardsResponse {}
            ''', 0),
        ),

        # -- case 2 - empty schema
        (
            {'type': 'object', 'properties': {}},
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export interface ReadCardsResponse {
            }
            ''', 0)
        ),

        # -- case 3 - simple schema
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
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export interface ReadCardsResponse {
                age: number;
                name?: string;
            }
            ''', 0)
        ),

        # -- case 4 - simple array
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
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export interface ReadCardsResponse {
                age: number[];
                surname?: string;
            }
            ''', 0)
        ),

        # -- case 5 - enum
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
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export enum ReadCardsResponseOccupation {
                AA = 'AA',
                BB = 'BB',
            }

            export interface ReadCardsResponse {
                occupation: ReadCardsResponseOccupation;
                surname?: string;
            }
            ''', 0)
        ),

        # -- case 6 - enums
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
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export enum ReadCardsResponseAge {
                12 = '12',
                21 = '21',
                33 = '33',
            }

            export enum ReadCardsResponseOccupation {
                AA = 'AA',
                BB = 'BB',
            }

            export interface ReadCardsResponse {
                age?: ReadCardsResponseAge;
                occupation: ReadCardsResponseOccupation;
                surname?: string;
            }
            ''', 0)
        ),

        # -- case 7 - enums array
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
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export enum ReadCardsResponseOccupation {
                AA = 'AA',
                BB = 'BB',
            }

            export interface ReadCardsResponse {
                occupation: ReadCardsResponseOccupation[];
                surname?: string;
            }
            ''', 0)
        ),

        # -- case 8 - 1 level deep nested
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
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export interface ReadCardsResponse {
                age: number;
                person?: {
                    category?: number;
                    name: string;
                };
            }
            ''', 0)
        ),

        # -- case 9 - 2 levels deep nested
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
            None,
            normalize_indentation('''
            /**
             * http://here
             */

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

        # -- case 10 - nested array
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
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export interface ReadCardsResponse {
                age: number;
                people?: {
                    category?: number;
                    name: string;
                }[];
            }
            ''', 0)
        ),

        # -- case 11 - nested with enums
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
            None,
            normalize_indentation('''
            /**
             * http://here
             */

            export enum ReadCardsResponseAge {
                A = 'A',
                B = 'B',
            }

            export enum ReadCardsResponseCategory {
                CAT0 = 'CAT0',
                CAT1 = 'CAT1',
                CAT2 = 'CAT2',
            }

            export interface ReadCardsResponse {
                age: ReadCardsResponseAge;
                people?: {
                    category: ReadCardsResponseCategory;
                };
            }
            ''', 0)
        ),

        # -- case 12 - mixed up primitive types
        (
            {
                'required': ['attempt_stats', 'count'],
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer'},
                    'attempt_stats': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'required': ['created_timestamp'],
                            'properties': {
                                'created_timestamp': {
                                    'type': 'number'
                                },
                                'card_id': {
                                    'type': 'any'
                                },
                                'states_path': {
                                    'type': 'object'
                                },
                                'id': {
                                    'type': 'integer'
                                },
                                'successful': {
                                    'type': 'boolean'
                                }
                            },
                        }
                    }
                },
            },
            None,
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponse {
                    attempt_stats: {
                        card_id?: any;
                        created_timestamp: number;
                        id?: number;
                        states_path?: Object;
                        successful?: boolean;
                    }[];
                    count: number;
                }

            ''', 0)
        ),

        # -- case 13 - bulk read response
        (
            {
                'type': 'object',
                'required': ['people'],
                'properties': {
                    'people': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'required': ['name', 'age'],
                            'properties': {
                                'name': {
                                    'type': 'string',
                                },
                                'age': {
                                    'type': 'integer',
                                },
                            },
                        },
                    },
                },
            },
            'cards',
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponseEntity {
                    age: number;
                    name: string;
                }

                export interface ReadCardsResponse {
                    cards: ReadCardsResponseEntity[];
                }
            ''', 0)
        ),

        # -- case 14 - bulk read simple response - integer
        (
            {
                'type': 'object',
                'required': [
                    'card_ids'
                ],
                'properties': {
                    'card_ids': {
                        'type': 'array',
                        'items': {
                            'type': 'integer'
                        }
                    }
                }
            },
            'card_ids',
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponseEntity extends Number {}

                export interface ReadCardsResponse {
                    card_ids: ReadCardsResponseEntity[];
                }
            ''', 0)
        ),

        # -- case 15 - bulk read simple response - boolean
        (
            {
                'type': 'object',
                'required': [
                    'card_ids'
                ],
                'properties': {
                    'card_ids': {
                        'type': 'array',
                        'items': {
                            'type': 'boolean'
                        }
                    }
                }
            },
            'card_ids',
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponseEntity extends Boolean {}

                export interface ReadCardsResponse {
                    card_ids: ReadCardsResponseEntity[];
                }
            ''', 0)
        ),

        # -- case 16 - bulk read simple response - string
        (
            {
                'type': 'object',
                'required': [
                    'card_ids'
                ],
                'properties': {
                    'card_ids': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        }
                    }
                }
            },
            'card_ids',
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponseEntity extends String {}

                export interface ReadCardsResponse {
                    card_ids: ReadCardsResponseEntity[];
                }
            ''', 0)
        ),

        # -- case 17 - bulk read response
        (
            {
                'type': 'object',
                'required': ['people'],
                'properties': {
                    'people': {
                        'type': 'object',
                    },
                },
            },
            'cards',
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponseEntity extends Object {};

                export interface ReadCardsResponse {
                    cards: ReadCardsResponseEntity[];
                }
            ''', 0)
        ),
    ], ids=list([str(i) for i in range(18)]))
def test_render(schema, bulk_read_field, expected):
    result = Interface(
        'READ_CARDS',
        Interface.TYPES.RESPONSE,
        schema,
        'http://here',
        bulk_read_field=bulk_read_field).render()

    assert result == expected
