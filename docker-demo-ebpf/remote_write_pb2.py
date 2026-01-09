# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Generated from Prometheus Remote Write v2 proto
# Simplified version for demonstration
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

class Label(_message.Message):
    __slots__ = ('name', 'value')
    NAME_FIELD_NUMBER = 1
    VALUE_FIELD_NUMBER = 2
    name: str
    value: str
    
    def __init__(self, name: str = "", value: str = ""):
        self.name = name
        self.value = value


class Sample(_message.Message):
    __slots__ = ('value', 'timestamp')
    VALUE_FIELD_NUMBER = 1
    TIMESTAMP_FIELD_NUMBER = 2
    value: float
    timestamp: int
    
    def __init__(self, value: float = 0.0, timestamp: int = 0):
        self.value = value
        self.timestamp = timestamp


class TimeSeries(_message.Message):
    __slots__ = ('labels', 'samples')
    LABELS_FIELD_NUMBER = 1
    SAMPLES_FIELD_NUMBER = 2
    labels: _containers.RepeatedCompositeFieldContainer[Label]
    samples: _containers.RepeatedCompositeFieldContainer[Sample]
    
    def __init__(self):
        self.labels = []
        self.samples = []


class WriteRequest(_message.Message):
    __slots__ = ('timeseries',)
    TIMESERIES_FIELD_NUMBER = 1
    timeseries: _containers.RepeatedCompositeFieldContainer[TimeSeries]
    
    def __init__(self):
        self.timeseries = []
