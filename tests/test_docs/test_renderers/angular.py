# -*- coding: utf-8 -*-


# def serialize_name(self):
#     if self.type == SERIALIZER_TYPES.RESPONSE:
#         return 'Response'

#     elif self.type == SERIALIZER_TYPES.REQUEST_BODY:
#         return 'RequestBody'

#     elif self.type == SERIALIZER_TYPES.REQUEST_QUERY:
#         return 'RequestQuery'

#
# remove_enums_duplicates
#

# def test_remove_enums_duplicates(self):

#     schema = SchemaRenderer(HumanSerializer).render()
#     schema.enums = [
#         Enum('kind', ['1', '2']),

#         # -- duplicated name, same values
#         Enum('kind', ['1', '2']),

#         # -- duplicated name, same values - different order
#         Enum('kind', ['2', '1']),

#         # -- duplicated name, different values
#         Enum('kind', ['1', '2', '3']),

#         # -- other duplicated name, different values
#         Enum('kind', ['1', 'a']),
#     ]

#     enums = schema.remove_enums_duplicates()

#     assert len(enums) == 3
#     enums_index = {enum.name: enum.values for enum in enums}
#     assert enums_index['ResponseKind'] == ['1', '2']
#     assert enums_index['ResponseKind1'] == ['1', '2', '3']
#     assert enums_index['ResponseKind2'] == ['1', 'a']


# @pytest.mark.parametrize(
#     'name, expected', [
#         # -- empty to empty
#         ('', ''),

#         # -- single letter capital to same
#         ('A', 'A'),

#         # -- camel to camel
#         ('Abc', 'Abc'),

#         # -- camel to camel
#         ('Abc', 'Abc'),

#         # -- all UPPER to camel
#         ('ABCD', 'Abcd'),

#         # -- all lower to camel
#         ('abcd', 'Abcd'),

#         # -- underscore case
#         ('ab_cde_f', 'AbCdeF'),

#         # -- mixed case
#         ('ab_CDe_f', 'AbCdeF'),

#     ])
# def test_to_camelcase(name, expected):

#     assert to_camelcase(name) == expected


# class Enum:

#     def __init__(self, name, values):
#         self.name = name
#         self.values = list(values)
# def remove_enums_duplicates(self):

#     enums = {}
#     duplicated_names = {}
#     for enum in self.enums:
#         name = self.serialize_enum_name(enum)

#         # -- if enum of that name already exists
#         if name in enums:
#             # -- compare its value with the one currently processing
#             if set(enums[name].values) != set(enum.values):
#                 duplicated_names.setdefault(name, [])
#                 duplicated_names[name].append(enum)

#         else:
#             enum.name = name
#             enums[name] = enum

#     for name, duplicated_enums in duplicated_names.items():
#         for i, enum in enumerate(duplicated_enums):
#             enum.name = '{name}{index}'.format(name=name, index=i + 1)
#             enums[enum.name] = enum

#     return list(enums.values())

# def serialize_enum_name(self, enum):

#     name = to_camelcase(enum.name)

#     if self.type == SERIALIZER_TYPES.RESPONSE:
#         return 'Response{}'.format(name)

#     elif self.type == SERIALIZER_TYPES.REQUEST_BODY:
#         return 'RequestBody{}'.format(name)

#     elif self.type == SERIALIZER_TYPES.REQUEST_QUERY:
#         return 'RequestQuery{}'.format(name)

# def to_camelcase(name):
#     tokens = re.split(r'\_+', name)

#     return ''.join([token.capitalize() for token in tokens])
