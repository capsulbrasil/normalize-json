import argparse
import typing
import sys
import json
from . import translate, flatten, RawObject, Mapping

CliOptions = typing.TypedDict('CliOptions', {
    'target': str,
    'mapping': typing.NotRequired[str],
    'op': typing.Literal[
        'translate',
        'flatten'
    ]
})

def output(obj: RawObject):
    print(json.dumps(obj, indent=2))

def main(options: CliOptions):
    target: RawObject = {}
    mapping: Mapping = {}

    with open(options['target']) as fh:
        target = json.loads(fh.read())

    if options.get('mapping'):
        with open(typing.cast(str, options.get('mapping'))) as fh:
            mapping = json.loads(fh.read())

    match options['op']:
        case 'translate':
            if not target:
                print('mapping argument is required')
                sys.exit(1)

            result = translate(target, mapping)
            output(result)

        case 'flatten':
            result = flatten(target)
            output(result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='normalize-json',
        description='schematic JSON transformations'
    )

    parser.add_argument('target')
    parser.add_argument('-m', '--mapping')
    parser.add_argument('--op', required=True, choices=[
        'translate',
        'flatten'
    ])

    options = typing.cast(CliOptions, parser.parse_args().__dict__)
    main(options)
