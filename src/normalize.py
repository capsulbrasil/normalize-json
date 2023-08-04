import typing
import json
import dateutil.parser as dateparser

T = typing.TypeVar('T')

TYPE_MAPPING = {
    'object': 'dict',
    'string': 'str',
    'datetime': 'datetime',
    'number': 'float',
    'integer': 'int',
    'objectid': 'ObjectId',
    'boolean': 'bool'
}

Modifier = typing.Literal[
    'array',
    'strict',
    'reverse',
    'default_null',
    'enforce'
]

AcceptedType = typing.Literal[
    'object',
    'string',
    'datetime',
    'number',
    'integer',
    'objectid',
    'boolean'
]

AcceptedMime = typing.Literal[
    'application/json'
]

Node = typing.TypedDict('Node', {
    'map': str,
    'type': AcceptedType,
    'array': typing.NotRequired[bool],
    'default': typing.NotRequired[typing.Any],
    'modifiers': typing.NotRequired[list[Modifier]],
    '__fields': typing.NotRequired[dict[str, 'Node']]
})

Mapping = typing.TypedDict('Mapping', {
    'modifiers': typing.NotRequired[list[Modifier]],
    '__fields': typing.NotRequired[dict[str, 'Node']]
})

RawObject = dict[str, typing.Any]

def unserialize(raw: RawObject | str | bytes, mime: AcceptedMime = 'application/json'):
    match mime:
        case 'application/json':
            if isinstance(raw, dict): return raw
            if isinstance(raw, bytes): return json.loads(raw)

    raise TypeError('invalid mime')

def check_types(actual: typing.Any, expected: typing.Any):
    return actual.__class__.__name__ == TYPE_MAPPING.get(str(expected))

def handle_modifiers(node: Node, modifiers: list[Modifier], old_value: typing.Any):
    value = old_value
    if not value:
        if 'default' in node:
            value = node['default']
        elif 'default_null' in modifiers:
            return None
        else:
            raise ValueError('value for %s wasnt provided' % node['map'])

    if 'enforce' in modifiers:
        match node['type']:
            case 'number': value = float(value)
            case 'integer': value = int(value)
            case 'string': value = str(value)
            case 'datetime': value = dateparser.parse(value)
            case _: ...

    return value


def translate(target: T, mapping: Mapping, acc: RawObject = {}, inherited_modifiers: list[Modifier] | None = None) -> T:
    ret: RawObject = {}

    if isinstance(target, dict):
        if '__fields' not in mapping:
            raise TypeError('__fields not present')

        for original_name, node in mapping['__fields'].items():
            mapped_name = node['map']
            mapped_type = node['type']
            modifiers = node.get('modifiers', inherited_modifiers or [])

            if '__fields' in node:
                child: typing.Any = target[original_name]
                ret[mapped_name] = translate(child, node, acc, modifiers)
                continue

            value = handle_modifiers(node, modifiers, typing.cast(RawObject, target).get(original_name))
            if not check_types(value, mapped_type):
                raise ValueError('check_types')

            ret[mapped_name] = value

    if isinstance(target, list):
        if not 'array' in mapping:
            raise ValueError('unexpected array')

        result = [
            translate(e, mapping, acc, inherited_modifiers)
            for e in typing.cast(list[typing.Any], target)
        ]

        return typing.cast(T, result)


    return typing.cast(T, ret)

