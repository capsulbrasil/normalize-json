# pyright: basic

from unittest import TestCase
from src.normalize_json.normalize import flatten

class TestFlatten(TestCase):
    def test_flatten_array(self):
        result = flatten([
            {
                'person': {
                    'name': 'joao',
                    'details': {
                        'dogs': [
                            'thor',
                            'bobby'
                        ]
                    }
                }
            },
            {
                'person': {
                    'name': 'also joao',
                    'details': {
                        'dogs': [
                            'spike'
                        ]
                    }
                }
            }
        ], preserve_arrays=True)

        self.assertEqual(result['[0].person.name'], 'joao')
        self.assertEqual(result['[0].person.details.dogs'], ['thor', 'bobby'])
        self.assertEqual(result['[1].person.name'], 'also joao')
        self.assertEqual(result['[1].person.details.dogs'], ['spike'])
