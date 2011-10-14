# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import genmsg.msgs
from genmsg.msgs import MsgSpec
from genmsg.msg_loader import MsgContext

import time
import sys

def test_is_special():
    import genpy.generator
    for t in ['time', 'duration', 'Header']:
        assert genpy.generator.is_special(t)
        
def test_Simple():
    import genpy.generator
    val = genpy.generator.get_special('time').import_str
    assert 'import genpy' == val, val
    assert 'import genpy' == genpy.generator.get_special('duration').import_str
    assert 'import std_msgs.msg' == genpy.generator.get_special('Header').import_str

    assert 'genpy.Time()' == genpy.generator.get_special('time').constructor
    assert 'genpy.Duration()' == genpy.generator.get_special('duration').constructor
    assert 'std_msgs.msg._Header.Header()' == genpy.generator.get_special('Header').constructor

    assert 'self.foo.canon()' == genpy.generator.get_special('time').get_post_deserialize('self.foo')
    assert 'bar.canon()' == genpy.generator.get_special('time').get_post_deserialize('bar')
    assert 'self.foo.canon()' == genpy.generator.get_special('duration').get_post_deserialize('self.foo')
    assert None == genpy.generator.get_special('Header').get_post_deserialize('self.foo')

def test_compute_post_deserialize():
    import genpy.generator
    assert 'self.bar.canon()' == genpy.generator.compute_post_deserialize('time', 'self.bar')
    assert 'self.bar.canon()' == genpy.generator.compute_post_deserialize('duration', 'self.bar')
    assert None == genpy.generator.compute_post_deserialize('Header', 'self.bar')

    assert None == genpy.generator.compute_post_deserialize('int8', 'self.bar')
    assert None == genpy.generator.compute_post_deserialize('string', 'self.bar')

def test_flatten():
    import genpy.generator
    from genpy.generator import flatten
    msg_context = MsgContext.create_default()

    simple = MsgSpec(['string'], ['data'], [], 'string data\n', 'simple/String')
    simple2 = MsgSpec(['string', 'int32'], ['data', 'data2'], [], 'string data\nint32 data2\n', 'simpe/Data2')
    assert simple == flatten(msg_context, simple)
    assert simple2 == flatten(msg_context, simple2)

    b1 = MsgSpec(['int8'], ['data'], [], 'X', 'f_msgs/Base')
    b2 = MsgSpec(['f_msgs/Base'], ['data'], [], 'X', 'f_msgs/Base2')
    b3 = MsgSpec(['f_msgs/Base2', 'f_msgs/Base2'], ['data3', 'data4'], [], 'X', 'f_msgs/Base3')
    b4 = MsgSpec(['f_msgs/Base3', 'f_msgs/Base3'], ['dataA', 'dataB'], [], 'X', 'f_msgs/Base4')

    msg_context.register('f_msgs/Base', b1)
    msg_context.register('f_msgs/Base2', b2)
    msg_context.register('f_msgs/Base3', b3)
    msg_context.register('f_msgs/Base4', b4)

    assert MsgSpec(['int8'], ['data.data'], [], 'X', 'f_msgs/Base2') == flatten(msg_context, b2)
    assert MsgSpec(['int8', 'int8'], ['data3.data.data', 'data4.data.data'], [], 'X', 'f_msgs/Base3') == flatten(msg_context, b3)
    assert MsgSpec(['int8', 'int8', 'int8', 'int8'],
                              ['dataA.data3.data.data', 'dataA.data4.data.data', 'dataB.data3.data.data', 'dataB.data4.data.data'],
                              [], 'X', 'f_msgs/Base4') == flatten(msg_context, b4)
        
def test_default_value():
    import genpy.generator
    from genpy.generator import default_value
    msg_context = MsgContext.create_default()

    msg_context.register('fake_msgs/String', MsgSpec(['string'], ['data'], [], 'string data\n', 'fake_msgs/String'))
    msg_context.register('fake_msgs/ThreeNums', MsgSpec(['int32', 'int32', 'int32'], ['x', 'y', 'z'], [], 'int32 x\nint32 y\nint32 z\n', 'fake_msgs/ThreeNums'))

    # trip-wire: make sure all builtins have a default value
    for t in genmsg.msgs.BUILTIN_TYPES:
        assert type(default_value(msg_context, t, 'roslib')) == str

    # simple types first
    for t in ['uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64', 'byte', 'char']:
        assert '0' == default_value(msg_context, t, 'std_msgs')
        assert '0' == default_value(msg_context, t, 'roslib')
    for t in ['float32', 'float64']:
        assert '0.' == default_value(msg_context, t, 'std_msgs')
        assert '0.' == default_value(msg_context, t, 'roslib')
    assert "''" == default_value(msg_context, 'string', 'roslib')

    # builtin specials
    assert 'genpy.Time()' == default_value(msg_context, 'time', 'roslib')
    assert 'genpy.Duration()' == default_value(msg_context, 'duration', 'roslib')
    assert 'std_msgs.msg._Header.Header()' == default_value(msg_context, 'Header', 'roslib')

    assert 'genpy.Time()' == default_value(msg_context, 'time', 'std_msgs')
    assert 'genpy.Duration()' == default_value(msg_context, 'duration', 'std_msgs')
    assert 'std_msgs.msg._Header.Header()' == default_value(msg_context, 'Header', 'std_msgs')

    # generic instances
    # - unregistered type
    assert None == default_value(msg_context, "unknown_msgs/Foo", "unknown_msgs")
    # - wrong context
    assert None == default_value(msg_context, 'ThreeNums', 'std_msgs')

    # - registered types
    assert 'fake_msgs.msg.String()' == default_value(msg_context, 'fake_msgs/String', 'std_msgs')
    assert 'fake_msgs.msg.String()' == default_value(msg_context, 'fake_msgs/String', 'fake_msgs')
    assert 'fake_msgs.msg.String()' == default_value(msg_context, 'String', 'fake_msgs')
    assert 'fake_msgs.msg.ThreeNums()' == default_value(msg_context, 'fake_msgs/ThreeNums', 'roslib')
    assert 'fake_msgs.msg.ThreeNums()' == default_value(msg_context, 'fake_msgs/ThreeNums', 'fake_msgs')
    assert 'fake_msgs.msg.ThreeNums()' == default_value(msg_context, 'ThreeNums', 'fake_msgs')

    # var-length arrays always default to empty arrays... except for byte and uint8 which are strings
    for t in ['int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64', 'float32', 'float64', 'char']:
        assert '[]' == default_value(msg_context, t+'[]', 'std_msgs')
        assert '[]' == default_value(msg_context, t+'[]', 'roslib')

    assert "''" == default_value(msg_context, 'uint8[]', 'roslib')
    assert "''" == default_value(msg_context, 'byte[]', 'roslib')

    # fixed-length arrays should be zero-filled... except for byte and uint8 which are strings
    for t in ['float32', 'float64']:
        assert '[0.,0.,0.]' == default_value(msg_context, t+'[3]', 'std_msgs')
        assert '[0.]' == default_value(msg_context, t+'[1]', 'std_msgs')
    for t in ['int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64', 'char']:
        assert '[0,0,0,0]' == default_value(msg_context, t+'[4]', 'std_msgs')
        assert '[0]' == default_value(msg_context, t+'[1]', 'roslib')

    assert "chr(0)*1" == default_value(msg_context, 'uint8[1]', 'roslib')
    assert "chr(0)*4" == default_value(msg_context, 'uint8[4]', 'roslib')
    assert "chr(0)*1" == default_value(msg_context, 'byte[1]', 'roslib')
    assert "chr(0)*4" == default_value(msg_context, 'byte[4]', 'roslib')

    assert '[]' == default_value(msg_context, 'fake_msgs/String[]', 'std_msgs')
    assert '[fake_msgs.msg.String(),fake_msgs.msg.String()]' == default_value(msg_context, 'fake_msgs/String[2]', 'std_msgs')

def test_make_python_safe():
    from genpy.generator import make_python_safe
    from genmsg.msgs import Constant
    s = MsgSpec(['int32', 'int32', 'int32', 'int32'], ['ok', 'if', 'self', 'fine'],
                [Constant('int32', 'if', '1', '1'), Constant('int32', 'okgo', '1', '1')],
                'x', 'test_msgs/Foo')
    s2 = make_python_safe(s)
    assert s != s2
    assert ['ok', 'if_', 'self_', 'fine'] == s2.names
    assert s2.types == s.types
    assert [Constant('int32', 'if_', '1', '1') == Constant('int32', 'okgo', '1', '1')], s2.constants
    assert s2.text == s.text
    
def test_compute_pkg_type():
    import genpy.generator
    from genpy.generator import compute_pkg_type, MsgGenerationException
    try:
        compute_pkg_type('std_msgs', 'really/bad/std_msgs/String')
    except MsgGenerationException: pass
    assert ('std_msgs', 'String') == compute_pkg_type('std_msgs', 'std_msgs/String')
    assert ('std_msgs', 'String') == compute_pkg_type('foo', 'std_msgs/String')    
    assert ('std_msgs', 'String') == compute_pkg_type('std_msgs', 'String')
        
def test_compute_import():
    import genpy.generator
    msg_context = MsgContext.create_default()

    assert [] == genpy.generator.compute_import(msg_context, 'foo', 'bar')
    assert [] == genpy.generator.compute_import(msg_context, 'foo', 'int32')

    msg_context.register('ci_msgs/Base', MsgSpec(['int8'], ['data'], [], 'int8 data\n', 'ci_msgs/Base'))
    msg_context.register('ci2_msgs/Base2', MsgSpec(['ci_msgs/Base'], ['data2'], [], 'ci_msgs/Base data2\n', 'ci2_msgs/Base2'))
    msg_context.register('ci3_msgs/Base3', MsgSpec(['ci2_msgs/Base2'], ['data3'], [], 'ci2_msgs/Base2 data3\n', 'ci3_msgs/Base3'))
    msg_context.register('ci4_msgs/Base', MsgSpec(['int8'], ['data'], [], 'int8 data\n', 'ci4_msgs/Base'))
    msg_context.register('ci4_msgs/Base4', MsgSpec(['ci2_msgs/Base2', 'ci3_msgs/Base3'],
                                       ['data4a', 'data4b'],
                                       [], 'ci2_msgs/Base2 data4a\nci3_msgs/Base3 data4b\n', 'ci4_msgs/Base4'))

    msg_context.register('ci5_msgs/Base', MsgSpec(['time'], ['data'], [], 'time data\n', 'ci5_msgs/Base'))

    assert ['import ci_msgs.msg'] == genpy.generator.compute_import(msg_context, 'foo', 'ci_msgs/Base')
    assert ['import ci_msgs.msg'] == genpy.generator.compute_import(msg_context, 'ci_msgs', 'ci_msgs/Base')
    assert ['import ci2_msgs.msg', 'import ci_msgs.msg'] == genpy.generator.compute_import(msg_context, 'ci2_msgs', 'ci2_msgs/Base2')
    assert ['import ci2_msgs.msg', 'import ci_msgs.msg'] == genpy.generator.compute_import(msg_context, 'foo', 'ci2_msgs/Base2')
    assert ['import ci3_msgs.msg', 'import ci2_msgs.msg', 'import ci_msgs.msg'] == genpy.generator.compute_import(msg_context, 'ci3_msgs', 'ci3_msgs/Base3')

    assert set(['import ci4_msgs.msg', 'import ci3_msgs.msg', 'import ci2_msgs.msg', 'import ci_msgs.msg']) == set(genpy.generator.compute_import(msg_context, 'foo', 'ci4_msgs/Base4'))
    assert set(['import ci4_msgs.msg', 'import ci3_msgs.msg', 'import ci2_msgs.msg', 'import ci_msgs.msg']) == set(genpy.generator.compute_import(msg_context, 'ci4_msgs', 'ci4_msgs/Base4'))

    assert ['import ci4_msgs.msg'] == genpy.generator.compute_import(msg_context, 'foo', 'ci4_msgs/Base')    
    assert ['import ci4_msgs.msg'] == genpy.generator.compute_import(msg_context, 'ci4_msgs', 'ci4_msgs/Base')
    assert ['import ci4_msgs.msg'] == genpy.generator.compute_import(msg_context, 'ci4_msgs', 'Base')

    assert ['import ci5_msgs.msg', 'import genpy'] == genpy.generator.compute_import(msg_context, 'foo', 'ci5_msgs/Base')
        
def test_get_registered_ex():
    import genpy.generator
    msg_context = MsgContext.create_default()
    s = MsgSpec(['string'], ['data'], [], 'string data\n', 'tgr_msgs/String')
    msg_context.register('tgr_msgs/String', s)
    assert s == genpy.generator.get_registered_ex(msg_context, 'tgr_msgs/String')
    try:
        genpy.generator.get_registered_ex(msg_context, 'bad_msgs/String')
    except genpy.generator.MsgGenerationException: pass
            
def test_compute_constructor():
    import genpy.generator
    from genpy.generator import compute_constructor
    msg_context = MsgContext.create_default()
    msg_context.register('fake_msgs/String', MsgSpec(['string'], ['data'], [], 'string data\n', 'fake_msgs/String'))
    msg_context.register('fake_msgs/ThreeNums', MsgSpec(['int32', 'int32', 'int32'], ['x', 'y', 'z'], [], 'int32 x\nint32 y\nint32 z\n', 'fake_msgs/ThreeNums'))

    # builtin specials
    assert 'genpy.Time()' == compute_constructor(msg_context, 'roslib', 'time')
    assert 'genpy.Duration()' == compute_constructor(msg_context, 'roslib', 'duration')
    assert 'std_msgs.msg._Header.Header()' == compute_constructor(msg_context, 'std_msgs', 'Header')

    assert 'genpy.Time()' == compute_constructor(msg_context, 'std_msgs', 'time')
    assert 'genpy.Duration()' == compute_constructor(msg_context, 'std_msgs', 'duration')

    # generic instances
    # - unregistered type
    assert None == compute_constructor(msg_context, "unknown_msgs", "unknown_msgs/Foo")
    assert None == compute_constructor(msg_context, "unknown_msgs", "Foo")
    # - wrong context
    assert None == compute_constructor(msg_context, 'std_msgs', 'ThreeNums')

    # - registered types
    assert 'fake_msgs.msg.String()' == compute_constructor(msg_context, 'std_msgs', 'fake_msgs/String')
    assert 'fake_msgs.msg.String()' == compute_constructor(msg_context, 'fake_msgs', 'fake_msgs/String')
    assert 'fake_msgs.msg.String()' == compute_constructor(msg_context, 'fake_msgs', 'String')
    assert 'fake_msgs.msg.ThreeNums()' == compute_constructor(msg_context, 'fake_msgs', 'fake_msgs/ThreeNums')
    assert 'fake_msgs.msg.ThreeNums()' == compute_constructor(msg_context, 'fake_msgs', 'fake_msgs/ThreeNums')
    assert 'fake_msgs.msg.ThreeNums()' == compute_constructor(msg_context, 'fake_msgs', 'ThreeNums')

def test_len_serializer_generator():
    import genpy.generator
    # generator tests are mainly tripwires/coverage tests
    # Test Serializers
    # string serializer simply initializes local var
    g = genpy.generator.len_serializer_generator('foo', True, True)
    assert 'length = len(foo)' == '\n'.join(g)
    # array len serializer writes var
    g = genpy.generator.len_serializer_generator('foo', False, True)        
    assert "length = len(foo)\nbuff.write(_struct_I.pack(length))" == '\n'.join(g)

    # Test Deserializers
    val = """start = end
end += 4
(length,) = _struct_I.unpack(str[start:end])"""
    # string serializer and array serializer are identical
    g = genpy.generator.len_serializer_generator('foo', True, False)
    assert val == '\n'.join(g)
    g = genpy.generator.len_serializer_generator('foo', False, False)        
    assert val == '\n'.join(g)

def test_string_serializer_generator():
    import genpy.generator
    # generator tests are mainly tripwires/coverage tests
    # Test Serializers
    g = genpy.generator.string_serializer_generator('foo', 'string', 'var_name', True)
    assert """length = len(var_name)
buff.write(struct.pack('<I%ss'%length, length, var_name.encode()))""" == '\n'.join(g)

    for t in ['uint8[]', 'byte[]', 'uint8[10]', 'byte[20]']:
        g = genpy.generator.string_serializer_generator('foo', 'uint8[]', 'b_name', True)
        assert """length = len(b_name)
# - if encoded as a list instead, serialize as bytes instead of string
if type(b_name) in [list, tuple]:
  buff.write(struct.pack('<I%sB'%length, length, *b_name))
else:
  buff.write(struct.pack('<I%ss'%length, length, b_name))""" == '\n'.join(g)

    # Test Deserializers
    val = """start = end
end += 4
(length,) = _struct_I.unpack(str[start:end])
start = end
end += length
var_name = str[start:end]"""
    # string serializer and array serializer are identical
    g = genpy.generator.string_serializer_generator('foo', 'string', 'var_name', False)
    assert val == '\n'.join(g)
