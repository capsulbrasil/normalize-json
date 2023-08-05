# normalize-json

## Run typechecking

```sh
$ python -m pyright
```

## Run tests

```sh
$ python -m unittest tests/*.py
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
    "smartest programmed that has ever lived",
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
    "nested_prop": {
      "map": "nested_prop",
      "type": "object",
      "__fields": {
        "name": {
          "map": "name",
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

Running `translate(sample, mapping)` against it would derive the following JSON:

```json
{
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

### Types

The node accept the following Python primitive types (plus `objectid` and `datetime`):

- `object`
- `string`
- `datetime`
- `number`
- `integer`
- `objectid`
- `boolean`

### Modifiers

You can change the default behavior passing a array of "modifiers" in your mapping node. Those will be inherited all the way down until the "modifiers" property is overriden.

Available modifiers are:

- `strict`: raise when the expected value isn't present
- `reverse`: shift origin and mapped names
- `default_null`: set None (or null) as the default value for absent properties
- `enforce`: cast values to expected type instead of raising a TypeError

## License

This library is [MIT licensed](https://github.com/capsulbrasil/normalize-json/tree/master/LICENSE).
