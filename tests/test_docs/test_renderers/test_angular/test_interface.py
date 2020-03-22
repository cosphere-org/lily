
from django.test import TestCase
import pytest

from lily.docs.renderers.angular.interface import Interface, Enum
from lily.base.utils import normalize_indentation
from lily import EventFactory


class EnumTestCase(TestCase):

    #
    # NAME
    #
    def test_name(self):
        assert Enum('age', []).name == 'Age'
        assert Enum('a_ge', []).name == 'AGe'

    def test_name__empty_name(self):

        with pytest.raises(EventFactory.BrokenRequest) as e:
            Enum('', ['what'])

        assert e.value.data == {
            '@event': 'ENUMS_WITHOUT_NAME_DETECTED',
            '@type': 'error',
            'name': '',
            'values': ['what'],
        }

    #
    # RENDER
    #
    def test_render(self):

        enum = Enum('age', ['AA', 'BB'])

        assert enum.render() == normalize_indentation('''
            export enum Age {
                AA = 'AA',
                BB = 'BB',
            }
        ''', 0)

    def test_render__numerical(self):

        enum0 = Enum('position', [0, 1])
        enum1 = Enum('position', ['0', '1', '2'])

        assert enum0.render() == normalize_indentation('''
            export enum Position {
                VALUE_0 = 0,
                VALUE_1 = 1,
            }
        ''', 0)
        assert enum1.render() == normalize_indentation('''
            export enum Position {
                VALUE_0 = '0',
                VALUE_1 = '1',
                VALUE_2 = '2',
            }
        ''', 0)

    def test_render__starts_from_number(self):

        enum = Enum('quality', ['240p', '720p', '1080p'])

        assert enum.render() == normalize_indentation('''
            export enum Quality {
                VALUE_1080P = '1080p',
                VALUE_240P = '240p',
                VALUE_720P = '720p',
            }
        ''', 0)

    def test_render__contains_extra_characters(self):

        enum = Enum(
            'content_type',
            ['image/svg+xml', 'video/png', 'audio/ogg-what'])

        assert enum.render() == normalize_indentation('''
            export enum ContentType {
                AUDIO_OGG_WHAT = 'audio/ogg-what',
                IMAGE_SVG_XML = 'image/svg+xml',
                VIDEO_PNG = 'video/png',
            }
        ''', 0)

    def test_render__removes_duplicates(self):

        enum = Enum('class', ['AA', 'BB', 'AA'])

        assert enum.render() == normalize_indentation('''
            export enum Class {
                AA = 'AA',
                BB = 'BB',
            }
        ''', 0)

    def test_render__sorts_values(self):

        enum = Enum('category', ['XX', 'AA', 'BB'])

        assert enum.render() == normalize_indentation('''
            export enum Category {
                AA = 'AA',
                BB = 'BB',
                XX = 'XX',
            }
        ''', 0)

    #
    # EQUAL_FIELD_AND_VALUES
    #
    def test__eq__(self):

        # -- identical
        assert (
            Enum('category', ['XX', 'AA', 'BB']) ==
            Enum('category', ['XX', 'AA', 'BB']))

        # -- the same, but with some duplicates and different order
        assert (
            Enum('category', ['XX', 'AA', 'BB']) ==
            Enum('category', ['XX', 'BB', 'AA', 'BB']))

        # -- different name
        assert (
            Enum('categories', ['XX', 'AA']) !=
            Enum('category', ['XX', 'AA']))

        # -- different values
        assert (
            Enum('category', ['XX', 'AA']) !=
            Enum('category', ['XX', 'YY']))


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
        assert e0 == Enum('age', [19, 91], None)

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
        assert e1 == Enum('age', [19], 1)


@pytest.mark.parametrize(
    'schema, bulk_read_field, expected_rendered, expected_enums',
    [
        # -- case 0 - None schema
        (
            None,
            None,
            '',
            [],
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
            [],
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
            ''', 0),
            [],
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
            ''', 0),
            [],
        ),

        # -- case 4 - simple array
        (
            {
                'type': 'object',
                'required': ['age'],
                'entity_type': 'human',
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
                '@type'?: 'human';
                '@access'?: {
                    [name: string]: boolean;
                };
                age: number[];
                surname?: string;
            }
            ''', 0),
            [],
        ),

        # -- case 5 - enum
        (
            {
                'type': 'object',
                'required': ['occupation'],
                'properties': {
                    'occupation': {
                        'type': 'string',
                        'enum_name': 'occupation_type',
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

            export interface ReadCardsResponse {
                occupation: OccupationType;
                surname?: string;
            }
            ''', 0),
            [Enum('OccupationType', ['AA', 'BB'])],
        ),

        # -- case 6 - enum with const value
        (
            {
                'type': 'object',
                'properties': {
                    'employees': {
                        'type': 'array',
                        'items': {
                            'oneOf': [
                                {
                                    'type': 'object',
                                    'properties': {
                                        'name': {
                                            'type': 'string',
                                        },
                                        'occupation': {
                                            'type': 'string',
                                            'enum_name': 'occupation_type',
                                            'enum': ['AA', 'BB'],
                                            'const_value': 'AA',
                                        }
                                    },
                                    'required': ['occupation'],
                                },
                                {
                                    'type': 'object',
                                    'properties': {
                                        'occupation': {
                                            'type': 'string',
                                            'enum_name': 'occupation_type',
                                            'enum': ['AA', 'BB'],
                                            'const_value': 'BB',
                                        }
                                    },
                                    'required': ['occupation'],
                                },
                            ]
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
                employees?: ({
                    name?: string;
                    occupation: OccupationType.AA;
                } | {
                    occupation: OccupationType.BB;
                })[];
            }

            ''', 0),
            [Enum('OccupationType', ['AA', 'BB'])],
        ),

        # -- case 7 - enums
        (
            {
                'type': 'object',
                'required': ['occupation'],
                'properties': {
                    'occupation': {
                        'type': 'string',
                        'enum': ['AA', 'BB'],
                        'enum_name': 'occupation',
                    },
                    'age': {
                        'type': 'string',
                        'enum': ['12', '21', '33'],
                        'enum_name': 'AgeChoice',
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
                age?: AgeChoice;
                occupation: Occupation;
                surname?: string;
            }
            ''', 0),
            [
                Enum('AgeChoice', ['12', '21', '33']),
                Enum('Occupation', ['AA', 'BB']),
            ],
        ),

        # -- case 8 - enums array
        (
            {
                'type': 'object',
                'required': ['occupation'],
                'properties': {
                    'occupation': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'enum_name': 'occupation',
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

            export interface ReadCardsResponse {
                occupation: Occupation[];
                surname?: string;
            }
            ''', 0),
            [Enum('Occupation', ['AA', 'BB'])],
        ),

        # -- case 9 - 1 level deep nested
        (
            {
                'type': 'object',
                'required': ['age'],
                'entity_type': 'employee',
                'properties': {
                    'age': {
                        'type': 'integer',
                    },
                    'person': {
                        'type': 'object',
                        'required': ['name'],
                        'entity_type': 'human',
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
                '@type'?: 'employee';
                '@access'?: {
                    [name: string]: boolean;
                };
                age: number;
                person?: {
                    '@type'?: 'human';
                    '@access'?: {
                        [name: string]: boolean;
                    };
                    category?: number;
                    name: string;
                };
            }
            ''', 0),
            [],
        ),

        # -- case 10 - 2 levels deep nested
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
            ''', 0),
            [],
        ),

        # -- case 11 - nested array
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
            ''', 0),
            [],
        ),

        # -- case 12 - nested with enums
        (
            {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'string',
                        'enum': ['A', 'B'],
                        'enum_name': 'MyAge',
                    },
                    'people': {
                        'type': 'object',
                        'required': ['category'],
                        'properties': {
                            'category': {
                                'type': 'string',
                                'enum_name': 'cat',
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

            export interface ReadCardsResponse {
                age: MyAge;
                people?: {
                    category: Cat;
                };
            }
            ''', 0),
            [
                Enum('Cat', ['CAT0', 'CAT1', 'CAT2']),
                Enum('MyAge', ['A', 'B']),
            ],
        ),

        # -- case 13 - mixed up primitive types
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
                        states_path?: any;
                        successful?: boolean;
                    }[];
                    count: number;
                }

            ''', 0),
            [],
        ),

        # -- case 14 - const types
        (
            {
                'required': ['type', 'age'],
                'type': 'object',
                'properties': {
                    'type': {
                        'type': 'string',
                        'pattern': '^MAN$',
                        'const': 'MAN',
                    },
                    'age': {
                        'type': 'number',
                    }
                },
            },
            None,
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponse {
                    age: number;
                    type: "MAN";
                }

            ''', 0),
            [],
        ),

        # -- case 15 - const and oneOf
        (
            {
                'required': ['person'],
                'type': 'object',
                'properties': {
                    'person': {
                        'oneOf': [
                            {
                                'type': 'object',
                                'properties': {
                                    'type': {
                                        'type': 'string',
                                        'pattern': '^DOG$',
                                        'const': 'DOG',
                                    },
                                    'age': {
                                        'type': 'number',
                                    }
                                }
                            },
                            {
                                'type': 'object',
                                'properties': {
                                    'type': {
                                        'type': 'string',
                                        'pattern': '^CAT$',
                                        'const': 'CAT',
                                    },
                                    'name': {
                                        'type': 'string',
                                    }
                                }
                            },
                        ],
                    }
                }
            },
            None,
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponse {
                    person: {
                        age?: number;
                        type?: "DOG";
                    } | {
                        name?: string;
                        type?: "CAT";
                    };
                }
            ''', 0),
            [],
        ),

        # -- case 16 - bulk read response
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
            ''', 0),
            [],
        ),

        # -- case 17 - bulk read simple response - integer
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
            ''', 0),
            [],
        ),

        # -- case 18 - bulk read simple response - boolean
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
            ''', 0),
            [],
        ),

        # -- case 19 - bulk read simple response - string
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
            ''', 0),
            [],
        ),

        # -- case 20 - bulk read response
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
            ''', 0),
            [],
        ),

        # -- case 21 - one of - null or string
        (
            {
                'type': 'object',
                'properties': {
                    'name': {
                        'oneOf': [
                            {'type': 'null'},
                            {'type': 'string'},
                        ],
                    },
                },
            },
            None,
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponse {
                    name?: null | string;
                }
            ''', 0),
            [],
        ),

        # -- case 23 - one of - null or object
        (
            {
                'type': 'object',
                'required': ['background'],
                'properties': {
                    'background': {
                        'oneOf': [
                            {'type': 'null'},
                            {
                                'type': 'object',
                                'properties': {
                                    'audio_uri': {
                                        'type': 'string',
                                    },
                                    'audio_stop': {
                                        'type': 'number',
                                    },
                                },
                            },
                        ],
                    },
                },
            },
            None,
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponse {
                    background: null | {
                        audio_stop?: number;
                        audio_uri?: string;
                    };
                }
            ''', 0),
            [],
        ),

        # -- case 24 - one of - null or object or string or other object
        (
            {
                'type': 'object',
                'required': ['background'],
                'properties': {
                    'background': {
                        'oneOf': [
                            {'type': 'null'},
                            {
                                'type': 'object',
                                'properties': {
                                    'audio_uri': {
                                        'type': 'string',
                                    },
                                    'audio_stop': {
                                        'type': 'number',
                                    },
                                },
                            },
                            {'type': 'string'},
                            {
                                'type': 'object',
                                'properties': {
                                    'text': {
                                        'type': 'string',
                                    },
                                    'age': {
                                        'type': 'number',
                                    },
                                },
                            },
                        ],
                    },
                },
            },
            None,
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponse {
                    background: null | {
                        audio_stop?: number;
                        audio_uri?: string;
                    } | string | {
                        age?: number;
                        text?: string;
                    };
                }
            ''', 0),
            [],
        ),

        # -- case 25 - one of - null or complex object
        (
            {
                'type': 'object',
                'required': ['background'],
                'properties': {
                    'background': {
                        'oneOf': [
                            {'type': 'null'},
                            {
                                'type': 'object',
                                'properties': {
                                    'audio_uri': {
                                        'oneOf': [
                                            {'type': 'null'},
                                            {
                                                'type': 'string',
                                                'format': 'url',
                                            },
                                        ],
                                    },
                                    'audio_text': {
                                        'oneOf': [
                                            {'type': 'null'},
                                            {'type': 'string'},
                                        ],
                                    },
                                    'audio_language': {
                                        'oneOf': [
                                            {'type': 'null'},
                                            {
                                                'type': 'string',
                                                'enum_name': 'language',
                                                'enum': [
                                                    'fr',
                                                    'nb',
                                                    'is',
                                                    'en',
                                                ],
                                            },
                                        ],
                                    },
                                    'audio_stop': {
                                        'oneOf': [
                                            {'type': 'null'},
                                            {'type': 'number'},
                                        ],
                                    },
                                },
                            },
                        ],
                    },
                },
            },
            None,
            normalize_indentation('''
                /**
                 * http://here
                 */

                export interface ReadCardsResponse {
                    background: null | {
                        audio_language?: null | Language;
                        audio_stop?: null | number;
                        audio_text?: null | string;
                        audio_uri?: null | string;
                    };
                }

            ''', 0),
            [Enum('Language', ['fr', 'is', 'nb', 'en'])],
        ),
    ], ids=list([str(i) for i in range(25)]))
def test_render(schema, bulk_read_field, expected_rendered, expected_enums):

    rendered, enums = Interface(
        'READ_CARDS',
        Interface.TYPES.RESPONSE,
        schema,
        'http://here',
        bulk_read_field=bulk_read_field).render()

    assert rendered == expected_rendered
    assert (
        sorted(enums, key=lambda x: x.name) ==
        sorted(expected_enums, key=lambda x: x.name))
