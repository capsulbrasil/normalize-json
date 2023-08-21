# pyright: basic

from unittest import TestCase
from src.normalize_json.normalize import Mapping, unserialize, translate

mapping1: Mapping = {
    'array': True,
    '__fields': {
        'name': {
            'map': 'nome',
            'type': 'string'
        },
        'age': {
            'map': [
                'idade',
                'anos'
            ],
            'type': 'string',
            'modifiers': [
                'enforce',
                'default_null'
            ]
        },
        'object_array': {
            'array': True,
            'type': 'object',
            '__fields': {
                'age': {
                    'map': [
                        '.idade',
                        '.anos'
                    ],
                    'type': 'string',
                    'modifiers': [
                        'enforce',
                        'default_null'
                    ]
                },
                'name': {
                    'map': '.nome',
                    'type': 'string'
                }
            }
        },
        'deep_mested_map': {
            'map': '[].jobs.business.name',
            'type': 'string',
            'default': 'nope'
        },
        'nested': {
            'type': 'object',
            '__fields': {
                'original_age': {
                    'map': [
                        '.idade',
                        '.anos'
                    ],
                    'type': 'integer',
                    'default': 0
                },
                'to_array': {
                    'map': [
                        '.idade',
                        '.anos'
                    ],
                    'array': True,
                    'type': 'integer',
                    'default': []
                },
                'deeper_nesting': {
                    'type': 'object',
                    '__fields': {
                        'i_dont_exist': {
                            'type': 'string',
                            'default': 'cool'
                        },
                        'path_test': {
                            'map': '.idade',
                            'type': 'string',
                            'modifiers': [
                                'enforce'
                            ],
                            'default': None
                        }
                    }
                }
            }
        }
    }
}


sample1 = [
    { 'nome': 'João', 'idade': 23 },
    { 'nome': 'Pedro', 'idade': 24 },
    { 'nome': 'Terry', 'anos': 50 },
    {
        'nome': 'Davis',
        'jobs': {
            'business': {
                'name': 'Capsul'
            }
        }
    },
]

class TestTranslateArrayEntry(TestCase):
    def test_translate_output(self):
        unserialized = unserialize(sample1)
        result = translate(unserialized, mapping1)
