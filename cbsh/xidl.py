#####################################################################################
#
#  Copyright (c) Crossbar.io Technologies GmbH
#
#  Unless a separate license agreement exists between you and Crossbar.io GmbH (e.g.
#  you have purchased a commercial license), the license terms below apply.
#
#  Should you enter into a separate license agreement after having received a copy of
#  this software, then the terms of such license agreement replace the terms below at
#  the time at which such license agreement becomes effective.
#
#  In case a separate license agreement ends, and such agreement ends without being
#  replaced by another separate license agreement, the license terms below apply
#  from the time at which said agreement ends.
#
#  LICENSE TERMS
#
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License, version 3, as published by the
#  Free Software Foundation. This program is distributed in the hope that it will be
#  useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.en.html>.
#
#####################################################################################

import os
import json
from pprint import pprint

from cbsh.reflection.Schema import Schema


filename = 'tests/idl/example.bfbs'
output_filename = 'tests/idl/example.json'

INTERFACE_ATTRS = ['type', 'uuid']
INTERFACE_MEMBER_ATTRS = ['type', 'stream']
INTERFACE_MEMBER_TYPES = ['procedure', 'topic']
INTERFACE_MEMBER_STREAM_VALUES = [None, 'in', 'out', 'inout']


_BASETYPE_ID2NAME = {
    None: 'Unknown',
    0: 'None',
    1: 'UType',
    2: 'Bool',
    3: 'Byte',
    4: 'UByte',
    5: 'Short',
    6: 'UShort',
    7: 'Int',
    8: 'UInt',
    9: 'Long',
    10: 'ULong',
    11: 'Float',
    12: 'Double',
    13: 'String',
    14: 'Vector',
    15: 'Obj',
    16: 'Union',
}

schema = None  # type: dict
schema = {
    'meta': {},
    'tables': [],
    'enums': [],
    'services': [],
}

schema_by_uri = None  # type: dict
schema_by_uri = {
    'meta': {},
    'uri': {},
}

# idl_parser.cpp: line 2404:
# while (token_ != kTokenEof) { ... }
#
# "namespace"       => ParseNamespace()
# "enum"            => ParseEnum(false, nullptr)
# "union"           => ParseEnum(true, nullptr)
# "root_type"       => SetRootType(name)
# "file_identifier" => file_identifier_
# "file_extension"  => file_extension_
# "attribute"       => known_attributes_[name] = false;
# "rpc_service"     => ParseService()
#                   => ParseDecl()
#

EXTRACT_ATTRS_RAW = False

def extract_attributes(item, allowed_attributes=None):
    num_attrs = item.AttributesLength()
    attrs = [item.Attributes(i) for i in range(num_attrs)]
    attrs_dict = {
        x.Key().decode('utf8'): x.Value().decode('utf8') if x.Value().decode('utf8') not in ['0'] else None
        for x in attrs
    }
    if allowed_attributes:
        for attr in attrs_dict:
            if attr not in allowed_attributes:
                raise Exception('invalid XBR attribute  "{}" - must be one of {}'.format(attr, allowed_attributes))
    return attrs_dict

def extract_docs(item):
    num_docs = item.DocumentationLength()
    item_docs = [
        item.Documentation(i).decode('utf8').strip()
        for i in range(num_docs)
    ]
    return item_docs
    

filepath = os.path.abspath(filename)

with open(filepath, 'rb') as f:
    buf = f.read()
    _schema = Schema.GetRootAsSchema(buf, 0)

    _root = _schema.RootTable()
    if _root:
        root_name = _root.Name().decode('utf8')
    else:
        root_name = None

    schema_meta = {
        'filename': filename,
        'filepath': filepath,
        'file_ident': _schema.FileIdent().decode('utf8'),
        'file_ext': _schema.FileExt().decode('utf8'),
        'root': root_name,
    }

    schema['meta'] = schema_meta
    schema_by_uri['meta'] = schema_meta

    enums = []
    objects = []
    services = []

    fqn2type = {}

    enum_cnt = 0
    object_cnt = 0
    service_cnt = 0

    for i in range(_schema.EnumsLength()):
        item = _schema.Enums(i)
        name = item.Name().decode('utf8')
        if name in fqn2type:
            raise Exception('duplicate name '.format(name))
        enum_cnt += 1

    for i in range(_schema.ObjectsLength()):
        item = _schema.Objects(i)
        name = item.Name().decode('utf8')
        if name in fqn2type:
            raise Exception('duplicate name '.format(name))
        object_cnt += 1

    for i in range(_schema.ServicesLength()):
        item = _schema.Services(i)
        name = item.Name().decode('utf8')
        if name in fqn2type:
            raise Exception('duplicate name '.format(name))
        service_cnt += 1

    print('Processing schema with {} enums, {} objects and {} services'.format(enum_cnt, object_cnt, service_cnt))


    # enums
    #
    num_enums = _schema.EnumsLength()
    for i in range(num_enums):

        # extract enum base information
        #
        _enum = _schema.Enums(i)
        enum_name = _enum.Name().decode('utf8')
        print('Processing enum {} ("{}")'.format(i, enum_name))

        enum = {
            '_index': i,
            'type': 'enum',
            'name': enum_name,
            'docs': extract_docs(_enum),
        }
        if EXTRACT_ATTRS_RAW:
            enum['attr'] = extract_attributes(_enum)

        # extract enum values
        #
        enum_values_dict =  {}
        for j in range(_enum.ValuesLength()):
            _enum_value = _enum.Values(j)
            enum_value_name = _enum_value.Name().decode('utf8')
            enum_value = {
                'docs': extract_docs(_enum_value),
                # enum values cannot have attributes
            }
            if enum_value_name in enum_values_dict:
                raise Exception('duplicate enum value "{}"'.format(enum_value_name))
            enum_values_dict[enum_value_name] = enum_value
        enum['values'] = enum_values_dict

        if enum_name in schema_by_uri['uri']:
            raise Exception(
                'unexpected duplicate definition for qualified name "{}"'.
                format(enum_name))

        enums.append(enum)
        schema_by_uri['uri'][enum_name] = enum

    # objects (tables/structs)
    #
    for i in range(_schema.ObjectsLength()):

        _obj = _schema.Objects(i)
        obj_name = _obj.Name().decode('utf8')
        print('Processing object {} ("{}")'.format(i, obj_name))

        obj = {
            '_index': i,
            'type': 'table',
            'name': obj_name,
            'docs': extract_docs(_obj),
        }
        print('OBJECT                     ', i, obj_name)
        if EXTRACT_ATTRS_RAW:
            obj['attr'] = extract_attributes(_obj)

        # extract fields
        num_fields = _obj.FieldsLength()
        fields = []
        fields_by_name = {}
        for j in range(num_fields):

            _field = _obj.Fields(j)
            field_name = _field.Name().decode('utf8')
            print('Processing field {} ("{}")'.format(i, field_name))

            _field_type = _field.Type()
            _field_index = int(_field_type.Index())
            _field_base_type = _BASETYPE_ID2NAME.get(_field_type.BaseType(), None)
            _field_element = _BASETYPE_ID2NAME.get(_field_type.Element(), None)
            if _field_element == 'None':
                _field_element = None

            field = {
                '_index': j,
                #'def': 'field',
                #'name': field_name,
                'id': int(_field.Id()),
                'offset': int(_field.Offset()),
                'base_type': _field_base_type,
            }
            if _field_element:
                field['element_type'] = _field_element

            if _field_index != -1:

                #field['field_index'] = _field_index

                if _field_base_type == 'Obj' or _field_element == 'Obj':

                    # obj/struct
                    if _field_index < _schema.ObjectsLength():
                        _obj_ref = _schema.Objects(_field_index).Name().decode('utf8')
                        print('Found referenced table/struct: {}'.format(_obj_ref))
                        field['referenced_type'] = _obj_ref
                    else:
                        print('WARNING - referenced table/struct for index {} ("{}.{}") not found'.format(_field_index, obj_name, field_name))
                        field['referenced_type'] = '**********************'

                elif _field_base_type in ['UType' ,
                                          'Bool',
                                          'Byte',
                                          'UByte',
                                          'Short',
                                          'UShort',
                                          'Int',
                                          'UInt',
                                          'Long',
                                          'ULong',
                                          'Float',
                                          'Double',
                                          'String']:
                    # enum
                    if _field_index < len(enums):
                        _enum_ref = enums[_field_index]['name']
                        print('Found referenced enum: {}'.format(_enum_ref))
                        field['referenced_type'] = _enum_ref
                    else:
                        print('WARNING - referenced enum not found')
                        field['referenced_type'] = '**********************'

                else:
                    raise Exception('unhandled field type: {} {} {} {}'.format(field_name, _field_base_type, _field_element, _field_index))

            field_docs = extract_docs(_field)
            if field_docs:
                field['docs'] = field_docs

            _field_attrs = extract_attributes(_field)
            if _field_attrs:
                field['attr'] = _field_attrs

            fields.append(field)
            fields_by_name[field_name] = field

        obj['fields'] = fields_by_name

        if obj['name'] in schema_by_uri['uri']:
            raise Exception(
                'unexpected duplicate definition for qualified name "{}"'.
                format(field['name']))

        # always append the object here, so we can dereference indexes correctly
        objects.append(obj)

        # skip our "void marker"
        if False and obj_name in ['Void']:
            pass
        else:
            schema_by_uri['uri'][obj['name']] = obj

    # iterate over services
    #
    num_services = _schema.ServicesLength()
    for i in range(num_services):
        _service = _schema.Services(i)

        service_name = _service.Name().decode('utf8')

        service_attrs_dict = extract_attributes(_service, INTERFACE_ATTRS)

        service_type = service_attrs_dict.get('type', None)
        if service_type != 'interface':
            raise Exception('invalid value "{}" for attribute "type" in XBR interface'.format(service_type))

        service = {
            '_index': i,
            'type': service_type,
            'name': service_name,
            'docs': extract_docs(_service),
        }

        if EXTRACT_ATTRS_RAW:
            service['attrs'] = service_attrs_dict
        else:
            service['uuid'] = service_attrs_dict.get('uuid', None)

        num_calls = _service.CallsLength()
        calls = []
        calls_by_name = {}
        for j in range(num_calls):
            _call = _service.Calls(j)

            _call_name = _call.Name().decode('utf8')

            call_attrs_dict = extract_attributes(_call)

            call_type = call_attrs_dict.get('type', None)
            if call_type not in INTERFACE_MEMBER_TYPES:
                raise Exception('invalid XBR interface member type "{}" - must be one of {}'.format(call_type, INTERFACE_MEMBER_TYPES))

            call_stream = call_attrs_dict.get('stream', None)
            if call_stream in ['none', 'None', 'null', 'Null']:
                call_stream = None

            if call_stream not in INTERFACE_MEMBER_STREAM_VALUES:
                raise Exception('invalid XBR interface member stream modifier "{}" - must be one of {}'.format(call_stream, INTERFACE_MEMBER_STREAM_VALUES))

            def _decode_type(x):
                res = x.Name().decode('utf8')
                if res in ['Void', 'wamp.Void']:
                    res = None
                return res

            call = {
                'type': call_type,
                # 'name': _call_name,
                'in': _decode_type(_call.Request()),
                'out': _decode_type(_call.Response()),
                'stream': call_stream,
                # 'id': int(_call.Id()),
                # 'offset': int(_call.Offset()),
            }
            #call['attrs'] = call_attrs_dict
            call['docs'] = extract_docs(_call)

            calls.append(call)
            calls_by_name[_call_name] = call

        # service['calls'] = sorted(calls, key=lambda field: field['id'])
        service['slots'] = calls_by_name

        services.append(service)

        if service_name in schema_by_uri['uri']:
            raise Exception(
                'unexpected duplicate definition for qualified name "{}"'.
                format(service_name))
        else:
            schema_by_uri['uri'][service_name] = service

schema['enums'] = sorted(enums, key=lambda enum: enum['name'])
schema['tables'] = sorted(objects, key=lambda obj: obj['name'])
schema['services'] = sorted(services, key=lambda service: service['name'])

if False:
    if True:
        pprint(schema_by_uri, width=240)
    else:
        pprint(schema_by_uri['meta'])

if False:
    pprint(schema_by_uri['uri']['wamp.proto.Serializer'])
    pprint(schema_by_uri['uri']['com.example.accelstorage.TimeRange'])
    pprint(schema_by_uri['uri']['com.example.accelstorage.AccelSamples'])

if False:
    pprint(schema['services'])

# pprint(schema_by_uri, width=240)

output_filepath = os.path.abspath(output_filename)
with open(output_filepath, 'wb') as f:
    data = json.dumps(
        schema_by_uri,
        ensure_ascii=False,
        sort_keys=False,
        indent=4,
        separators=(', ', ': ')).encode('utf8')
    f.write(data)

print('output file written: {}'.format(output_filepath))
