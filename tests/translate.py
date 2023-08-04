import json
from unittest import TestCase
from src.normalize import Mapping, unserialize, translate

mapping1: Mapping = {
    '__fields': {
        'nome': {
            'map': 'name',
            'type': 'string'
        },
        'idade': {
            'map': 'age',
            'type': 'string',
            'modifiers': [
                'enforce'
            ]
        },
        'cachorro': {
            'map': 'dog',
            'type': 'object',
            '__fields': {
                'apelido': {
                    'map': 'alias',
                    'type': 'string'
                }
            }
        },
        'profissoes': {
            'map': 'jobs',
            'type': 'object',
            'array': True,
            '__fields': {
                'empresa': {
                    'map': 'business',
                    'type': 'string'
                },
                'cargo': {
                    'map': 'position',
                    'type': 'string'
                },
                'salario': {
                    'map': 'wage',
                    'type': 'string',
                    'default': 1500,
                    'modifiers': [
                        'enforce'
                    ]
                }
            }
        }
    }
}

sample1 = {
    'nome': 'jurandir',
    'idade': 23,
    'cachorro': {
        'apelido': 'Thor'
    },
    'profissoes': [
        {
            'empresa': 'capsul',
            'cargo': 'programador'
        },
        {
            'empresa': 'self-employed',
            'cargo': 'tradutor e diagramador'
        }
    ]
}

class TestTranslate(TestCase):
    def test_translate_output(self):
        unserialized = unserialize(sample1)
        result = translate(unserialized, mapping1)

        self.assertEqual(result['name'], sample1['nome'])
        self.assertEqual(result['age'], str(sample1['idade']))
        self.assertEqual(result['dog']['alias'], str(sample1['cachorro']['apelido']))

        self.assertEqual(result['jobs'][0]['business'], str(sample1['profissoes'][0]['empresa']))
        self.assertEqual(result['jobs'][0]['wage'], '1500')

        self.assertEqual(result['jobs'][1]['business'], str(sample1['profissoes'][1]['empresa']))
        self.assertEqual(result['jobs'][1]['wage'], '1500')

