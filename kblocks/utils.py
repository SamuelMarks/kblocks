from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from functools import wraps
import os
import gin
from absl import logging
from typing import Optional, Callable, Any, TypeVar, Generic

DEFAULT = '__default__'


class UpdateFrequency(object):
    BATCH = 'batch'
    EPOCH = 'epoch'

    @classmethod
    def validate(cls, freq):
        if freq not in (cls.BATCH, cls.EPOCH):
            raise ValueError(
                'Invalid frequency "{}" - must be one of {}'.format(
                    freq, (cls.BATCH, cls.EPOCH)))


@gin.configurable(module='kb.utils')
def identity(x):
    return x


@gin.configurable(module='kb.utils')
def ray_init(redis_address: Optional[str] = DEFAULT,
             num_cpus: Optional[int] = None,
             num_gpus: Optional[int] = None,
             local_mode: bool = False,
             **kwargs):
    import ray
    if redis_address == DEFAULT:
        redis_address = os.environ.get('REDIS_ADDRESS')
    return ray.init(redis_address,
                    num_cpus=num_cpus,
                    num_gpus=num_gpus,
                    local_mode=local_mode,
                    **kwargs)


@gin.configurable(module='kb.utils')
def proc(title: str = 'kblocks'):
    if title is not None:
        try:
            # dirty hack to make pyright shut up
            import importlib
            getattr(importlib.import_module('setproctitle'),
                    'setproctitle')(title)
            # import setproctitle  # pyright: disable
            # setproctitle.setproctitle(title)
        except ImportError:
            logging.warning(
                'Failed to import setproctitle - cannot change title.')


# S = TypeVar('S')
# T = TypeVar('T')

# def memoize(fn: Callable[[S], T]) -> Callable[[S], T]:
#     attr = '__cached_{}'.format(fn.__name__)

#     def wrapped(s: S):
#         out = getattr(s, attr, None)
#         if out is None:
#             out = fn(s)
#             setattr(s, attr, out)
#         return out

#     return wrapped


class memoized_property(property):  # pylint: disable=invalid-name
    """Descriptor that mimics @property but caches output in member variable."""

    def __get__(self, obj: Any, type: Optional[type] = ...) -> Any:
        # See https://docs.python.org/3/howto/descriptor.html#properties
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        attr = "__cached_" + self.fget.__name__
        cached = getattr(obj, attr, None)
        if cached is None:
            # cached = self.fget(obj)
            cached = super(memoized_property, self).__get__(obj, type)
            setattr(obj, attr, cached)
        return cached
