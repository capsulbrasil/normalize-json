# normalize-json

## Install

```sh
$ pip install normalize-json
```

## CLI

```sh
$ python -m normalize-json -h
```

## Use cases

This library can be used to normalize several API specs into a single standardized structure.
Click [here](https://github.com/capsulbrasil/normalize-json/tree/master/examples) to view some examples.

## Usage

### Mapping

Mapping is the schema object you use to specify how your properties should be converted.

Suppose you have the following structured data:

```json
{
  "skills": [
    "smartest programmer that has ever lived",
    "high priest",
    "builder of the temple of god"
  ],
  "nested_prop": {
    "name": "Terry Davis",
    "age": 50
  }
}
```

An example mapping could be as following. In this example we'll rename the `.nested_prop.age` path to `.nested_prop.years_on_earth` while converting its value to `string` and move the `.skills` path to `.nested_prop.skills`. Notice how properties with names starting with a dot (".") will be treated as paths whereas properties without a dot in the beginning will be treated as same-level properties.

```json
{
  "modifiers": [
    "default_null"
  ],
  "__fields": {
    "secret": {
      "map": "{{ secret.key }}"
    },
    "nested_prop": {
      "type": "object",
      "__fields": {
        "name": {
          "type": "string"
        },
        "years_on_earth": {
          "map": "age",
          "type": "string",
          "modifiers": [
            "enforce"
          ]
        },
        "mastered_skills": {
          "map": ".skills",
          "type": "string",
          "array": true
        }
      }
    }
  }
}
```

Running `translate(sample, mapping, substitute={ 'secret.key': 'abc123' })` against it would derive the following JSON:

```json
{
  "secret": "abc123",
  "nested_prop": {
    "name": "Terry Davis",
    "years_on_earth": "50",
    "mastered_skills": [
      "smartest programmed that has ever lived",
      "high priest",
      "builder of the temple of god"
    ]
  }
}
```

A minimal example is as following:

```python
import normalize_json as normalize
import json

sample = {
  'person': {
    'name': 'João',
    'pet': {
      'name': 'Thor'
    }
  }
}

mapping = {
  '__fields': {
    'pet': {
      '__fields': {
        'name': '.person.pet.name'
      }
    }
  }
}

string_mapping = {
  '__fields': {
    'dog': 'beef',
    'bird': [
      'seeds',
      'plants'
    ]
  }
}

def output(obj):
  print(json.dumps(obj, indent=2))

def main():
  """
  {
    "person.name": "João",
    "person.pet.name": "Thor"
  }
  """
  output(normalize.flatten(sample))

  """
  {
    "pet": {
      "name": "Thor"
    }
  }
  """
  output(normalize.translate(sample, mapping))

  """
  "dog"
  """
  output(normalize.translate_string('beef', string_mapping))

  """
  "bird"
  """
  output(normalize.translate_string('seeds', string_mapping))

if __name__ == '__main__':
  main()
```

### Types

The node accept the following Python primitive types (plus `objectid` and `datetime`):

- `object`
- `string`
- `datetime`
- `number`
- `integer`
- `objectid`
- `boolean`

### Enums

String values can be mapped using enums:

```python
mapping: Mapping = {
  '__fields': {
    'status': {
      'enum': {
        'ativo': 'active',
        'inativo': 'inactive',
      }
    },
    'colors': {
      'array': True,
      'enum': {
        'azul': 'blue',
        'vermelho': 'red',
        'verde': 'green',
      }
    }
  }
}

sample = {
  'status': 'ativo',
  'colors': [
    'azul',
    'vermelho',
  ]
}

# { 'status': 'active', 'colors': ['blue', 'red'] }
result = normalize.translate(sample, mapping)
```

### Modifiers

You can change the default behavior passing a array of "modifiers" in your mapping node. Those will be inherited all the way down until the "modifiers" property is overriden.

Available modifiers are:

- `strict`: raise when the expected value isn't present
- `reverse`: shift origin and mapped names
- `default_null`: set None (or null) as the default value for absent properties
- `enforce`: cast values to expected type instead of raising a TypeError

### Attributes

- `array`: whether the expected value is an array or not
- `trim_start`: trim `n` characters from the beginning of the string
- `trim_end`: trim `n` characters from the end of the string
- `pick_until`: same as `value.split(str)[0]`

## Support and contributing

You can obtain suport if you're using this library on production. Just email the author at joaosan177[at]gmail.com. You may also send PRs, just make sure to include tests and follow PEP guidelines.

### Run typechecking

```sh
$ python -m pyright
```

### Run tests

```sh
$ python -m unittest tests/*.py
```


## License

This library is [MIT licensed](https://github.com/capsulbrasil/normalize-json/tree/master/LICENSE).
