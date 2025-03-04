# Copyright 2018-present Kensho Technologies, LLC.
import unittest

from frozendict import frozendict
from graphql.type import GraphQLList, GraphQLObjectType, GraphQLString
import pytest
import six

from .. import get_graphql_schema_from_orientdb_schema_data
from ..schema_generation.graphql_schema import _get_union_type_name
from ..schema_generation.orientdb.schema_graph_builder import get_orientdb_schema_graph
from ..schema_generation.orientdb.schema_properties import (
    ORIENTDB_BASE_EDGE_CLASS_NAME, ORIENTDB_BASE_VERTEX_CLASS_NAME, PROPERTY_TYPE_EMBEDDED_LIST_ID,
    PROPERTY_TYPE_EMBEDDED_SET_ID, PROPERTY_TYPE_LINK_ID, PROPERTY_TYPE_STRING_ID
)


BASE_VERTEX_SCHEMA_DATA = frozendict({
    'name': ORIENTDB_BASE_VERTEX_CLASS_NAME,
    'abstract': False,
    'properties': []
})

BASE_EDGE_SCHEMA_DATA = frozendict({
    'name': ORIENTDB_BASE_EDGE_CLASS_NAME,
    'abstract': False,
    'properties': []
})

EXTERNAL_SOURCE_SCHEMA_DATA = frozendict({
    'name': 'ExternalSource',
    'abstract': False,
    'properties': []
})

ENTITY_SCHEMA_DATA = frozendict({
    'name': 'Entity',
    'abstract': True,
    'superClasses': [ORIENTDB_BASE_VERTEX_CLASS_NAME],
    'properties': [
        {
            'name': 'name',
            'type': PROPERTY_TYPE_STRING_ID,
        }
    ]
})

PERSON_SCHEMA_DATA = frozendict({
    'name': 'Person',
    'abstract': False,
    'superClass': 'Entity',
    'properties': [
        {
            'name': 'alias',
            'type': PROPERTY_TYPE_EMBEDDED_SET_ID,
            'linkedType': PROPERTY_TYPE_STRING_ID,
            'defaultValue': '{}'
        },
    ],
})

BABY_SCHEMA_DATA = frozendict({
    'name': 'Baby',
    'abstract': False,
    'superClass': 'Person',
    'properties': [],
})


DATA_POINT_SCHEMA_DATA = frozendict({
    'name': 'DataPoint',
    'abstract': True,
    'properties': [
        {
            'name': 'data_source',
            'type': PROPERTY_TYPE_EMBEDDED_LIST_ID,
            'linkedClass': 'ExternalSource',
            'defaultValue': '[]'
        }
    ],
    'superClass': 'V',
})

PERSON_LIVES_IN_EDGE_SCHEMA_DATA = frozendict({
    'name': 'Person_LivesIn',
    'abstract': False,
    'customFields': {
        'human_name_in': 'Location where person lives',
        'human_name_out': 'Person',
    },
    'properties': [
        {
            'name': 'in',
            'type': PROPERTY_TYPE_LINK_ID,
            'linkedClass': 'Location',
        },
        {
            'name': 'out',
            'type': PROPERTY_TYPE_LINK_ID,
            'linkedClass': 'Person',
        }
    ],
    'superClass': ORIENTDB_BASE_EDGE_CLASS_NAME
})


BABY_LIVES_IN_EDGE_SCHEMA_DATA = frozendict({
    'name': 'Baby_LivesIn',
    'abstract': False,
    'properties': [
        {
            'name': 'in',
            'type': PROPERTY_TYPE_LINK_ID,
            'linkedClass': 'Location',
        },
        {
            'name': 'out',
            'type': PROPERTY_TYPE_LINK_ID,
            'linkedClass': 'Baby',
        }
    ],
    'superClass': 'Person_LivesIn',
})

LOCATION_SCHEMA_DATA = frozendict({
    'name': 'Location',
    'abstract': False,
    'superClasses': ['Entity'],
    'properties': [
        {
            'name': 'description',
            'type': PROPERTY_TYPE_STRING_ID,
        }
    ]
})

CLASS_WITH_INVALID_PROPERTY_NAME_SCHEMA_DATA = frozendict({
    'name': 'ClassWithInvalidPropertyName',
    'abstract': False,
    'superClasses': [ORIENTDB_BASE_VERTEX_CLASS_NAME],
    'properties': [
        {
            'name': '$invalid_name',
            'type': PROPERTY_TYPE_STRING_ID
        }
    ],
})


class GraphqlSchemaGenerationTests(unittest.TestCase):
    def test_parsed_vertex(self):
        schema_data = [
            BASE_VERTEX_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
        ]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        self.assertTrue(schema_graph.get_element_by_class_name('Entity').is_vertex)

    def test_parsed_edge(self):
        schema_data = [
            BASE_EDGE_SCHEMA_DATA,
            BASE_VERTEX_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
            LOCATION_SCHEMA_DATA,
            PERSON_LIVES_IN_EDGE_SCHEMA_DATA,
            PERSON_SCHEMA_DATA,
        ]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        self.assertTrue(schema_graph.get_element_by_class_name('Person_LivesIn').is_edge)

    def test_parsed_non_graph_class(self):
        schema_data = [EXTERNAL_SOURCE_SCHEMA_DATA]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        self.assertTrue(schema_graph.get_element_by_class_name('ExternalSource').is_non_graph)

    def test_no_superclass(self):
        schema_data = [BASE_VERTEX_SCHEMA_DATA]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        self.assertEqual({ORIENTDB_BASE_VERTEX_CLASS_NAME},
                         schema_graph.get_superclass_set(ORIENTDB_BASE_VERTEX_CLASS_NAME))

    def test_parsed_superclass_field(self):
        schema_data = [
            BASE_EDGE_SCHEMA_DATA,
            BASE_VERTEX_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
            LOCATION_SCHEMA_DATA,
            PERSON_LIVES_IN_EDGE_SCHEMA_DATA,
            PERSON_SCHEMA_DATA,
        ]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        self.assertEqual({'Person_LivesIn', ORIENTDB_BASE_EDGE_CLASS_NAME},
                         schema_graph.get_superclass_set('Person_LivesIn'))

    def test_parsed_superclasses_field(self):
        schema_data = [
            BASE_VERTEX_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
        ]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        self.assertEqual({'Entity', ORIENTDB_BASE_VERTEX_CLASS_NAME},
                         schema_graph.get_superclass_set('Entity'))

    def test_parsed_property(self):
        schema_data = [
            BASE_VERTEX_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
        ]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        name_property = schema_graph.get_element_by_class_name('Entity').properties['name']
        self.assertTrue(name_property.type.is_same_type(GraphQLString))

    def test_native_orientdb_collection_property(self):
        schema_data = [
            BASE_VERTEX_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
            PERSON_SCHEMA_DATA,
        ]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        alias_property = schema_graph.get_element_by_class_name('Person').properties['alias']
        self.assertTrue(alias_property.type.is_same_type(GraphQLList(GraphQLString)))
        self.assertEqual(alias_property.default, set())

    def test_class_collection_property(self):
        schema_data = [
            BASE_VERTEX_SCHEMA_DATA,
            DATA_POINT_SCHEMA_DATA,
            EXTERNAL_SOURCE_SCHEMA_DATA,
        ]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        friends_property = schema_graph.get_element_by_class_name('DataPoint').properties[
            'data_source']
        self.assertTrue(friends_property.type.is_same_type(
            GraphQLList(GraphQLObjectType('ExternalSource', {}))))
        self.assertEqual(friends_property.default, list())

    def test_link_parsing(self):
        schema_data = [
            BASE_EDGE_SCHEMA_DATA,
            BASE_VERTEX_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
            LOCATION_SCHEMA_DATA,
            PERSON_LIVES_IN_EDGE_SCHEMA_DATA,
            PERSON_SCHEMA_DATA,
        ]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        person_lives_in_edge = schema_graph.get_element_by_class_name('Person_LivesIn')
        self.assertEqual(person_lives_in_edge.base_in_connection, 'Person')
        self.assertEqual(person_lives_in_edge.base_out_connection, 'Location')

    def test_parsed_class_fields(self):
        schema_data = [
            BASE_EDGE_SCHEMA_DATA,
            BASE_VERTEX_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
            LOCATION_SCHEMA_DATA,
            PERSON_LIVES_IN_EDGE_SCHEMA_DATA,
            PERSON_SCHEMA_DATA,
        ]
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        person_lives_in_edge = schema_graph.get_element_by_class_name('Person_LivesIn')
        self.assertEqual(PERSON_LIVES_IN_EDGE_SCHEMA_DATA['customFields'],
                         person_lives_in_edge.class_fields)

    def test_type_equivalence_dicts(self):
        schema_data = [
            BASE_EDGE_SCHEMA_DATA,
            BASE_VERTEX_SCHEMA_DATA,
            BABY_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
            LOCATION_SCHEMA_DATA,
            PERSON_LIVES_IN_EDGE_SCHEMA_DATA,
            PERSON_SCHEMA_DATA,
        ]
        schema, type_equivalence_dicts = get_graphql_schema_from_orientdb_schema_data(schema_data)

        # Sanity check
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        person_subclass_set = schema_graph.get_subclass_set('Person')
        self.assertIsNotNone(schema.get_type(_get_union_type_name(person_subclass_set)))

        person, person_baby_union = next(six.iteritems(type_equivalence_dicts))
        baby = schema.get_type('Baby')
        location = schema.get_type('Location')

        # Assert that there is exactly 1 type equivalence
        self.assertEqual(1, len(type_equivalence_dicts))

        # Assert that the Person class is part of the schema.
        self.assertEqual(person, schema.get_type('Person'))

        # Assert that the union consists of the Baby and Person classes
        self.assertEqual(set(person_baby_union.types), {baby, person})

        # Assert that arbitrarily chosen inherited property is still correctly inherited
        self.assertTrue(baby.fields['name'].type.is_same_type(GraphQLString))

        # Assert that arbitrarily chosen edge is correctly represented on all ends
        location_list_type = GraphQLList(location)
        union_list_type = GraphQLList(person_baby_union)
        self.assertTrue(person.fields['out_Person_LivesIn'].type.is_same_type(location_list_type))
        self.assertTrue(baby.fields['out_Person_LivesIn'].type.is_same_type(location_list_type))
        self.assertTrue(location.fields['in_Person_LivesIn'].type.is_same_type(union_list_type))

    def test_filter_type_equivalences_with_no_edges(self):
        schema_data = [
            BASE_VERTEX_SCHEMA_DATA,
            BABY_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
            PERSON_SCHEMA_DATA,
        ]
        schema, type_equivalence_dicts = get_graphql_schema_from_orientdb_schema_data(schema_data)
        # Since there is not ingoing edge to Person, we filter the Person_Baby union
        # from the type equivalence dict since it is not discoverable by the GraphQL Schema.
        self.assertEqual(0, len(type_equivalence_dicts))
        # Sanity check
        schema_graph = get_orientdb_schema_graph(schema_data, [])
        person_subclass_set = schema_graph.get_subclass_set('Person')
        self.assertIsNone(schema.get_type(_get_union_type_name(person_subclass_set)))

    def test_edge_inheritance(self):
        schema_data = [
            BASE_EDGE_SCHEMA_DATA,
            BABY_LIVES_IN_EDGE_SCHEMA_DATA,
            BASE_VERTEX_SCHEMA_DATA,
            BABY_SCHEMA_DATA,
            ENTITY_SCHEMA_DATA,
            LOCATION_SCHEMA_DATA,
            PERSON_LIVES_IN_EDGE_SCHEMA_DATA,
            PERSON_SCHEMA_DATA,
        ]

        schema_graph = get_orientdb_schema_graph(schema_data, [])
        baby_lives_in_edge = schema_graph.get_element_by_class_name('Baby_LivesIn')
        self.assertEqual('Baby', baby_lives_in_edge.base_in_connection)

    def test_ignore_properties_with_invalid_name_warning(self):
        schema_data = [
            BASE_VERTEX_SCHEMA_DATA,
            CLASS_WITH_INVALID_PROPERTY_NAME_SCHEMA_DATA,
        ]

        with pytest.warns(UserWarning):
            get_graphql_schema_from_orientdb_schema_data(schema_data)
