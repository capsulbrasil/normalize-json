import typing
import json
import re
import dateutil.parser as dateparser
import unicodedata

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
    'strict',
    'reverse',
    'default_null',
    'enforce',
    'normalize_unicode'
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
    'array': bool,
    'default': typing.Any,
    'modifiers': list[Modifier],
    'trim_start': int,
    'trim_end': int,
    'pick_until': str,
    'enum': dict[str, str],
    '__fields': dict[str, 'Node']
}, total=False)

Mapping = typing.TypedDict('Mapping', {
    'array': typing.NotRequired[bool],
    'modifiers': typing.NotRequired[list[Modifier]],
    '__fields': typing.NotRequired[dict[str, 'Node']]
})

StringMapping = typing.TypedDict('StringMapping', {
    '__fields': dict[str, str | list[str]]
})

RawObject = dict[str, typing.Any]

def unserialize(raw: typing.Any, mime: AcceptedMime = 'application/json'):
    match mime:
        case 'application/json':
            if isinstance(raw, str): return json.loads(raw)
            if isinstance(raw, bytes): return json.loads(raw)
            else: return raw

    raise TypeError('invalid mime')

def flatten(target: typing.Any, separator: str = '.', preserve_arrays: bool = False):
    if not isinstance(target, dict) and not isinstance(target, list):
        return target

    ret: RawObject = {}

    def internal_flatten(obj: typing.Any, parent: str = '', depth: int = 0) -> typing.Any:
        if isinstance(obj, dict):
            for k, v in typing.cast(RawObject, obj).items():
                internal_flatten(v, '%s%s%s' % (parent, separator, k), depth + 1)

        elif isinstance(obj, list):
            if preserve_arrays and depth > 0:
                ret[parent] = [
                    flatten(elem, separator, preserve_arrays)
                    for elem in typing.cast(list[typing.Any], obj)
                ]
                return

            for i, v in enumerate(typing.cast(list[RawObject], obj)):
                internal_flatten(v, '%s[%d]' % (parent, i), depth + 1)

        else:
            ret[parent] = obj

    internal_flatten(target)
    return ret


def check_types(node: Node, value: typing.Any, modifiers: list[Modifier]):
    actual = value[0].__class__.__name__ \
        if node.get('array') \
        else value.__class__.__name__

    node_type = node.get('type', 'string')

    if node.get('array') and value == []:
        return None
    if node.get('enum'):
        if actual == 'NoneType' and 'default_null' in modifiers:
            return None

        if node.get('array'):
            for v in value:
                if v not in node['enum']:
                    break
            else:
                return None
        elif value in node['enum']:
            return None

        return value, list(node['enum'].keys())

    vexpected = TYPE_MAPPING.get(node_type)
    if actual == vexpected \
            or (actual == 'int' and vexpected in ['number', 'float']) \
            or (actual == 'NoneType' and 'default_null' in modifiers):
        return None

    return actual, node_type

def handle_modifiers(node: Node, mapped_name: str, modifiers: list[Modifier], old_value: typing.Any):
    value = old_value

    if not value:
        if 'default' in node:
            value = node['default']
        elif 'default_null' in modifiers:
            return None
        else:
            raise ValueError('value for %s wasnt provided' % mapped_name)

    if 'normalize_unicode' in modifiers and isinstance(value, str):
        value = unicodedata.normalize('NFKD', value)

    if trim := node.get('trim_start'):
        value = value[trim*-1:]

    if trim := node.get('trim_end'):
        value = value[:trim]

    if pick := node.get('pick_until'):
        value = value.split(pick)[0]

    if 'enforce' in modifiers and check_types(node, value, modifiers):
        match node.get('type', 'string'):
            case 'number':
                value = re.sub(r'[^0-9\.]', '', value) or 0
                value = float(value)
            case 'integer':
                value = re.sub(r'[^0-9]', '', value) or 0
                value = int(value)
            case 'string': value = str(value)
            case 'datetime': value = dateparser.parse(value)
            case _: ...

    return value

def get_initial_value(target: typing.Any, mapped_name: str, flat_obj: RawObject):
    initial_value = flat_obj.get(mapped_name) \
        if mapped_name[0] == '.' or mapped_name[:2] == '[]' \
        else target.get(mapped_name)

    return initial_value


def translate(
    target: T | tuple[T, int],
    mapping: Mapping, acc: RawObject = {},
    inherited_modifiers: list[Modifier] | None = None,
    inherited_flat_obj: tuple[RawObject, RawObject] | None = None,
    substitute: dict[str, typing.Any] = {}
) -> T:
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

        root_modifiers = mapping.get('modifiers', inherited_modifiers or [])

        for original_name, node in mapping['__fields'].items():
            mapped_name = node.get('map', original_name)
            initial_value: typing.Any = None

            var_name: str|None = None

            modifiers = node.get('modifiers', root_modifiers)
            if 'reverse' in modifiers:
                mapped_name, original_name = original_name, mapped_name

            for n in mapped_name if isinstance(mapped_name, list) else mapped_name.split('|'):
                mapped_name = n.strip()

                if '[]' in mapped_name:
                    mapped_name = mapped_name.replace('[]', '[%d]' % target_index)

                if typing.cast(typing.Any, target).get(mapped_name):
                    initial_value = target[mapped_name]
                    break
                elif flat_obj.get(mapped_name):
                    mapped_name = mapped_name
                    initial_value = flat_obj[mapped_name]
                    break
                elif mapped_name in flat_obj_arr and flat_obj_arr[mapped_name] != None:
                    initial_value = flat_obj_arr.get(mapped_name)
                    break
                elif mapped_name[:2] == "{{" and mapped_name[-2:] == "}}":
                    var_name = mapped_name[2:].replace(' ', '')[:-2]
                    break

            mapped_name = typing.cast(str, mapped_name)
            original_name = typing.cast(str, original_name)

            if var_name:
                ret[original_name] = substitute.get(var_name)
                continue

            if '__fields' in node:
                if not node.get('map'):
                    value = translate(typing.cast(typing.Any, target), node, acc, modifiers, substitute=substitute)
                else:
                    child: typing.Any = initial_value \
                            if initial_value or isinstance(initial_value, list) \
                            else target[original_name]
                    value = translate(child, node, acc, modifiers, (flat_obj, flat_obj_arr), substitute=substitute)
                if node.get('array') and not isinstance(value, list):
                    value = [value]

                ret[original_name] = value
                continue

            if not initial_value:
                initial_value = get_initial_value(target, mapped_name, flat_obj)

            value = handle_modifiers(node, mapped_name, modifiers, initial_value)
            if node.get('array') and not isinstance(value, list):
                value = [value]

            if err := check_types(node, value, modifiers):
                raise ValueError('check_types @ %s (got "%s", expected "%s")' % (original_name, *err))

            if node.get('enum') and value != None:
                if node.get('array'):
                    value = [
                        node['enum'].get(v)
                        for v in value
                    ]
                else:
                    value = node['enum'].get(value)

            ret[original_name] = value

    if isinstance(target, list):
        if not mapping.get('array'):
            raise ValueError('illegal array')

        result = [
            translate((e, idx), mapping, acc, inherited_modifiers, (flat_obj, flat_obj_arr), substitute=substitute)
            for idx, e in enumerate(typing.cast(list[typing.Any], target))
        ]

        return typing.cast(T, result)

    return typing.cast(T, ret)


def translate_string(target: str, mapping: StringMapping):
    for k, v in mapping['__fields'].items():
        if isinstance(v, str):
            if v == target:
                return k
        else:
            if target in v:
                return k

