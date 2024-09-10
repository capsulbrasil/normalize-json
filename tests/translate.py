# pyright: basic

from unittest import TestCase
from src.normalize_json.normalize import Mapping, unserialize, translate

mapping1: Mapping = {
    '__fields': {
        'name': {
            'map': 'nome',
            'type': 'string'
        },
        'age': {
            'map': 'idade',
            'type': 'string',
            'modifiers': [
                'enforce'
            ]
        },
        'array_elem': {
            'map': '.profissoes[1].cargo',
            'type': 'string',
            'array': True
        },
        'array_copy': {
            'map': '.detalhes.habilidades',
            'type': 'string',
            'array': True
        },
        'trim_me_start': {
            'type': 'string',
            'trim_start': 3
        },
        'trim_me_end': {
            'type': 'string',
            'trim_end': 3
        },
        'pick_until': {
            'type': 'string',
            'pick_until': ' '
        },
        'dog': {
            'map': 'cachorro',
            'type': 'object',
            '__fields': {
                'alias': {
                    'map': 'apelido',
                    'type': 'string'
                }
            }
        },
        'jobs': {
            'map': 'profissoes',
            'type': 'object',
            'array': True,
            '__fields': {
                'business': {
                    'map': 'empresa',
                    'type': 'string'
                },
                'position': {
                    'map': '.nome',
                    'type': 'string'
                },
                'wage': {
                    'map': 'salario',
                    'type': 'string',
                    'default': 1500,
                    'modifiers': [
                        'enforce'
                    ]
                },
                'skill': {
                    'map': '.detalhes.habilidades[]',
                    'type': 'string',
                    'array': True
                }
            }
        },
        'details': {
            'map': 'detalhes',
            'type': 'object',
            '__fields': {
                'skills': {
                    'map': 'habilidades',
                    'type': 'string',
                    'array': True
                }
            }
        }
    }
}


sample1 = {
    'nome': 'jurandir',
    'idade': 23,
    'trim_me_start': 'abc123',
    'trim_me_end': 'abc123',
    'pick_until': 'Terry A. Davis',
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
    ],
    'detalhes': {
        'habilidades': [
            'programacao',
            'escrita'
        ]
    }
}

mapping2: Mapping = {
    'modifiers': [
        'default_null'
    ],
    '__fields': {
        'secret_key': {
            'map': '{{ secrets.key }}'
        },
        'status': {
            'enum': {
                'pago': 'paid',
                'pendente': 'pending',
                'recusado': 'refused',
            }
        },
        'statuses': {
            'array': True,
            'enum': {
                'pago': 'paid',
                'pendente': 'pending',
                'recusado': 'refused',
            }
        },
        'items': {
            'map': 'items',
            'type': 'object',
            '__fields': {
                'meta': {
                    'map': 'meta',
                    'type': 'object',
                    '__fields': {
                        'page': {
                            'type': 'integer'
                        }
                    }
                },
                'data': {
                    'map': 'data',
                    'array': True,
                    'type': 'object',
                    '__fields': {
                        'name': {
                            'type': 'string'
                        },
                        'age': {
                            'type': 'integer',
                            'map': [
                                'age',
                                '{{ defaults.age }}'
                            ]
                        }
                    }
                }
            }
        }
    }
}

sample2 = {
    'status': 'pago',
    'statuses': [
        'pendente',
        'recusado',
    ],
    'items': {
        'meta': {
            'page': 1,
        },
        'data': [
            { 'name': 'João', 'age': 23 },
            { 'name': 'Thor', 'age': 15 }
        ]
    }
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

        self.assertEqual(result['trim_me_start'], '123')
        self.assertEqual(result['trim_me_end'], 'abc')
        self.assertEqual(result['pick_until'], 'Terry')

    def test_translate_inloco(self):
        unserialized = unserialize(sample2)
        result = translate(unserialized, mapping2)

        self.assertEqual(result['items']['meta']['page'], 1)
        self.assertEqual(result['items']['data'][0]['name'], 'João')
        self.assertEqual(result['items']['data'][0]['age'], 23)
        self.assertEqual(result['items']['data'][1]['name'], 'Thor')
        self.assertEqual(result['items']['data'][1]['age'], 15)

    def test_translate_enums(self):
        unserialized = unserialize(sample2)
        result = translate(unserialized, mapping2)
        self.assertEqual(result['status'], 'paid')
        self.assertEqual(result['statuses'][0], 'pending')
        self.assertEqual(result['statuses'][1], 'refused')


    def test_translate_substitute(self):
        sample2_copy = sample2.copy()
        del sample2_copy['items']['data'][0]['age']

        unserialized = unserialize(sample2_copy)
        result = translate(unserialized, mapping2, substitute={
            'secrets.key': 'abc123',
            'defaults.age': 20
        })

        self.assertEqual(result['secret_key'], 'abc123')
        self.assertEqual(result['items']['data'][0]['age'], 20)
