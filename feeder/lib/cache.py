"""Part builders memoised per argument set, config included."""

import functools


def per_config(build):
    """Build once per argument set: the assembly, the guide and the tests build the same parts many times in one
    process. Config holds dicts and is not hashable, so the key is the arguments' repr. build123d operators return
    new shapes, so callers cannot change a cached one."""
    built = {}

    @functools.wraps(build)
    def cached(*args, **kwargs):
        key = repr((args, sorted(kwargs.items())))
        if key not in built:
            built[key] = build(*args, **kwargs)
        return built[key]

    return cached
