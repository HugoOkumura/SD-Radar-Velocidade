from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Leitura(_message.Message):
    __slots__ = ("limite", "data", "velocidade", "placa")
    LIMITE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    VELOCIDADE_FIELD_NUMBER: _ClassVar[int]
    PLACA_FIELD_NUMBER: _ClassVar[int]
    limite: int
    data: _timestamp_pb2.Timestamp
    velocidade: float
    placa: str
    def __init__(self, limite: _Optional[int] = ..., data: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., velocidade: _Optional[float] = ..., placa: _Optional[str] = ...) -> None: ...

class Usuario(_message.Message):
    __slots__ = ("id", "nome", "placa")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    PLACA_FIELD_NUMBER: _ClassVar[int]
    id: str
    nome: str
    placa: str
    def __init__(self, id: _Optional[str] = ..., nome: _Optional[str] = ..., placa: _Optional[str] = ...) -> None: ...

class Resposta(_message.Message):
    __slots__ = ("user", "sucesso")
    USER_FIELD_NUMBER: _ClassVar[int]
    SUCESSO_FIELD_NUMBER: _ClassVar[int]
    user: Usuario
    sucesso: bool
    def __init__(self, user: _Optional[_Union[Usuario, _Mapping]] = ..., sucesso: bool = ...) -> None: ...
