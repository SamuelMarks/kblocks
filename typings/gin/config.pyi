from typing import Any, Callable, List, Tuple, Union

def parse_config_files_and_bindings(
    config_files: List[str],
    bindings: Union[List[str], str],
    finalize_config: bool = True,
    skip_unknown: bool = False,
) -> None: ...
def operative_config_str(
    max_line_length: int = 80, continuation_indent: int = 4
) -> str: ...
def query_parameter(binding_key: str) -> Any: ...
def bind_parameter(binding_key: str, value: Any) -> None: ...

_FILE_READERS: List[Tuple[Callable[[str], Any], Callable[[str], Any]]] = ...

REQUIRED: object = ...
