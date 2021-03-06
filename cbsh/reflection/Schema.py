# automatically generated by the FlatBuffers compiler, do not modify

# namespace: reflection

import flatbuffers

class Schema(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAsSchema(cls, buf, offset):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = Schema()
        x.Init(buf, n + offset)
        return x

    # Schema
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # Schema
    def Objects(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from .Object import Object
            obj = Object()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Schema
    def ObjectsLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # Schema
    def Enums(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from .Enum import Enum
            obj = Enum()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Schema
    def EnumsLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # Schema
    def FileIdent(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return bytes()

    # Schema
    def FileExt(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return bytes()

    # Schema
    def RootTable(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            x = self._tab.Indirect(o + self._tab.Pos)
            from .Object import Object
            obj = Object()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Schema
    def Services(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(14))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from .Service import Service
            obj = Service()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Schema
    def ServicesLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(14))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

def SchemaStart(builder): builder.StartObject(6)
def SchemaAddObjects(builder, objects): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(objects), 0)
def SchemaStartObjectsVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def SchemaAddEnums(builder, enums): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(enums), 0)
def SchemaStartEnumsVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def SchemaAddFileIdent(builder, fileIdent): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(fileIdent), 0)
def SchemaAddFileExt(builder, fileExt): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(fileExt), 0)
def SchemaAddRootTable(builder, rootTable): builder.PrependUOffsetTRelativeSlot(4, flatbuffers.number_types.UOffsetTFlags.py_type(rootTable), 0)
def SchemaAddServices(builder, services): builder.PrependUOffsetTRelativeSlot(5, flatbuffers.number_types.UOffsetTFlags.py_type(services), 0)
def SchemaStartServicesVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def SchemaEnd(builder): return builder.EndObject()
