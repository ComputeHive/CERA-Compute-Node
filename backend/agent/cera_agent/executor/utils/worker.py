from typing import Any

from executor.models.flattenedcode import FlattenedCode

_fn_cache: dict = {}


def worker_init(flattened_code: FlattenedCode) -> None:
    global _fn_cache
    namespace: dict = {}
    exec(compile(flattened_code.code_deps, "<deps>", "exec"), namespace)
    exec(compile(flattened_code.function_content, "<fn>", "exec"), namespace)
    _fn_cache = namespace


def worker(fn_name: str, kwargs: dict | list) -> Any:
    target_fn = _fn_cache[fn_name]
    if isinstance(kwargs, list):
        return [target_fn(**kw) for kw in kwargs]
    return target_fn(**kwargs)
