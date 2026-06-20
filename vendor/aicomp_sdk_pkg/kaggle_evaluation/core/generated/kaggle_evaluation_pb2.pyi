from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class KaggleEvaluationRequest(_message.Message):
    __slots__ = ("name", "args", "kwargs")
    class KwargsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Payload
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Payload, _Mapping]] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    KWARGS_FIELD_NUMBER: _ClassVar[int]
    name: str
    args: _containers.RepeatedCompositeFieldContainer[Payload]
    kwargs: _containers.MessageMap[str, Payload]
    def __init__(self, name: _Optional[str] = ..., args: _Optional[_Iterable[_Union[Payload, _Mapping]]] = ..., kwargs: _Optional[_Mapping[str, Payload]] = ...) -> None: ...

class KaggleEvaluationResponse(_message.Message):
    __slots__ = ("payload",)
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    payload: Payload
    def __init__(self, payload: _Optional[_Union[Payload, _Mapping]] = ...) -> None: ...

class Payload(_message.Message):
    __slots__ = ("str_value", "bool_value", "int_value", "float_value", "none_value", "list_value", "tuple_value", "dict_value", "pandas_dataframe_value", "polars_dataframe_value", "pandas_series_value", "polars_series_value", "numpy_array_value", "numpy_scalar_value", "bytes_io_value", "enum_value", "dataclass_value", "pydantic_model_value")
    STR_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    NONE_VALUE_FIELD_NUMBER: _ClassVar[int]
    LIST_VALUE_FIELD_NUMBER: _ClassVar[int]
    TUPLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    DICT_VALUE_FIELD_NUMBER: _ClassVar[int]
    PANDAS_DATAFRAME_VALUE_FIELD_NUMBER: _ClassVar[int]
    POLARS_DATAFRAME_VALUE_FIELD_NUMBER: _ClassVar[int]
    PANDAS_SERIES_VALUE_FIELD_NUMBER: _ClassVar[int]
    POLARS_SERIES_VALUE_FIELD_NUMBER: _ClassVar[int]
    NUMPY_ARRAY_VALUE_FIELD_NUMBER: _ClassVar[int]
    NUMPY_SCALAR_VALUE_FIELD_NUMBER: _ClassVar[int]
    BYTES_IO_VALUE_FIELD_NUMBER: _ClassVar[int]
    ENUM_VALUE_FIELD_NUMBER: _ClassVar[int]
    DATACLASS_VALUE_FIELD_NUMBER: _ClassVar[int]
    PYDANTIC_MODEL_VALUE_FIELD_NUMBER: _ClassVar[int]
    str_value: str
    bool_value: bool
    int_value: int
    float_value: float
    none_value: bool
    list_value: PayloadList
    tuple_value: PayloadList
    dict_value: PayloadMap
    pandas_dataframe_value: bytes
    polars_dataframe_value: bytes
    pandas_series_value: bytes
    polars_series_value: bytes
    numpy_array_value: bytes
    numpy_scalar_value: bytes
    bytes_io_value: bytes
    enum_value: DataModel
    dataclass_value: DataModel
    pydantic_model_value: DataModel
    def __init__(self, str_value: _Optional[str] = ..., bool_value: bool = ..., int_value: _Optional[int] = ..., float_value: _Optional[float] = ..., none_value: bool = ..., list_value: _Optional[_Union[PayloadList, _Mapping]] = ..., tuple_value: _Optional[_Union[PayloadList, _Mapping]] = ..., dict_value: _Optional[_Union[PayloadMap, _Mapping]] = ..., pandas_dataframe_value: _Optional[bytes] = ..., polars_dataframe_value: _Optional[bytes] = ..., pandas_series_value: _Optional[bytes] = ..., polars_series_value: _Optional[bytes] = ..., numpy_array_value: _Optional[bytes] = ..., numpy_scalar_value: _Optional[bytes] = ..., bytes_io_value: _Optional[bytes] = ..., enum_value: _Optional[_Union[DataModel, _Mapping]] = ..., dataclass_value: _Optional[_Union[DataModel, _Mapping]] = ..., pydantic_model_value: _Optional[_Union[DataModel, _Mapping]] = ...) -> None: ...

class PayloadList(_message.Message):
    __slots__ = ("payloads",)
    PAYLOADS_FIELD_NUMBER: _ClassVar[int]
    payloads: _containers.RepeatedCompositeFieldContainer[Payload]
    def __init__(self, payloads: _Optional[_Iterable[_Union[Payload, _Mapping]]] = ...) -> None: ...

class PayloadMap(_message.Message):
    __slots__ = ("payload_map",)
    class PayloadMapEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Payload
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Payload, _Mapping]] = ...) -> None: ...
    PAYLOAD_MAP_FIELD_NUMBER: _ClassVar[int]
    payload_map: _containers.MessageMap[str, Payload]
    def __init__(self, payload_map: _Optional[_Mapping[str, Payload]] = ...) -> None: ...

class DataModel(_message.Message):
    __slots__ = ("module", "class_name", "data")
    MODULE_FIELD_NUMBER: _ClassVar[int]
    CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    module: str
    class_name: str
    data: str
    def __init__(self, module: _Optional[str] = ..., class_name: _Optional[str] = ..., data: _Optional[str] = ...) -> None: ...
