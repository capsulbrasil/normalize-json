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
    'map': str | list[str],
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

def flatten(target: RawObject, separator: str = '.', preserve_arrays: bool = False):
    out: RawObject = {}

    def internal_flatten(obj: typing.Any, parent: str = '') -> typing.Any:
        if isinstance(obj, dict):
            for k, v in typing.cast(RawObject, obj).items():
                internal_flatten(v, '%s%s%s' % (parent, separator, k))

        elif isinstance(obj, list):
            if preserve_arrays:
                out[parent] = obj
                return

            for i, v in enumerate(typing.cast(list[RawObject], obj)):
                internal_flatten(v, '%s[%d]' % (parent, i))

        else:
            out[parent] = obj

    internal_flatten(target)
    return out


def check_types(node: Node, value: typing.Any, expected: typing.Any):
    actual = value[0].__class__.__name__ \
        if node.get('array') \
        else value.__class__.__name__

    if actual == TYPE_MAPPING.get(str(expected)):
        return None

    return actual, str(expected)

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

def get_initial_value(target: typing.Any, original_name: str, flat_obj: RawObject):
    initial_value = flat_obj.get(original_name) \
        if original_name[0] == '.' \
        else target.get(original_name)

    return initial_value


def translate(target: T | tuple[T, int], mapping: Mapping, acc: RawObject = {}, inherited_modifiers: list[Modifier] | None = None, inherited_flat_obj: tuple[RawObject, RawObject] | None = None) -> T:
    ret: RawObject = {}
    flat_obj, flat_obj_arr = inherited_flat_obj or (
        flatten(typing.cast(RawObject, target)),
        flatten(typing.cast(RawObject, target), preserve_arrays=True)
    )

    target_index: int = 0

    if isinstance(target, tuple):
        target, target_index = typing.cast(tuple[T, int], target)

    if isinstance(target, dict):
        if '__fields' not in mapping:
            raise TypeError('__fields not present')

        for original_name, node in mapping['__fields'].items():
            mapped_name = node['map']
            mapped_type = node['type']
            initial_value: typing.Any = None

            for n in mapped_name if isinstance(mapped_name, list) else mapped_name.split('|'):
                n = n.strip()
                if typing.cast(RawObject, target).get(n):
                    mapped_name = n

            mapped_name = typing.cast(str, mapped_name)
            if '[]' in mapped_name and node.get('array'):
                mapped_name = mapped_name.replace('[]', '[%d]' % target_index)

            elif mapped_name in flat_obj_arr:
                initial_value = flat_obj_arr.get(mapped_name)

            modifiers = node.get('modifiers', inherited_modifiers or [])

            if 'reverse' in modifiers:
                mapped_name, original_name = original_name, mapped_name

            if '__fields' in node:
                child: typing.Any = target[mapped_name]
                ret[original_name] = translate(child, node, acc, modifiers, (flat_obj, flat_obj_arr))
                continue

            if not initial_value:
                initial_value = get_initial_value(target, mapped_name, flat_obj)

            value = handle_modifiers(node, modifiers, initial_value)
            if err := check_types(node, value, mapped_type):
                raise ValueError('check_types @ %s (got "%s", expected "%s")' % (original_name, *err))

            ret[original_name] = value

    if isinstance(target, list):
        if not 'array' in mapping:
            raise ValueError('unexpected array')

        result = [
            translate((e, idx), mapping, acc, inherited_modifiers, (flat_obj, flat_obj_arr))
            for idx, e in enumerate(typing.cast(list[typing.Any], target))
        ]

        return typing.cast(T, result)


    return typing.cast(T, ret)


