"""
Tests for `nameko_cachetools` module.
"""
import time
import pytest
from mock import Mock, patch

import eventlet
from nameko.rpc import rpc
from nameko.standalone.rpc import ServiceRpcProxy
from nameko_cachetools import CachedRpcProxy, CacheFirstRpcProxy
from nameko.testing.services import (entrypoint_hook, entrypoint_waiter,
                                     get_extension)


def test_cached_response(rabbit_config, container_factory):

    class Service(object):
        name = "service"

        cached_service = CachedRpcProxy('some_other_service')
        cache_first_service = CacheFirstRpcProxy('some_other_service')

        @rpc
        def cached(self):
            return self.cached_service.some_method('hi', some_arg=True)

        @rpc
        def cache_first(self):
            return self.cache_first.some_method('hi', some_arg=True)

    container = container_factory(Service, rabbit_config)
    container.start()

    cached_rpc = get_extension(container, CachedRpcProxy)
    cache_first_rpc = get_extension(container, CacheFirstRpcProxy)

    def fake_some_method(*args, **kwargs):
        return 'hi'

    with patch('nameko.rpc.MethodProxy.__call__', fake_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook() == 'hi'

    def broken_some_method(*args, **kwargs):
        raise Exception('hmm')

    with patch('nameko.rpc.MethodProxy.__call__', broken_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook() == 'hi'

    cached_rpc.cache = {}

    with patch('nameko.rpc.MethodProxy.__call__', broken_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            with pytest.raises(Exception):
                hook()


def test_cached_response_on_timeout(rabbit_config, container_factory):

    class Service(object):
        name = "service"

        cached_service = CachedRpcProxy('some_other_service', failover_timeout=1)
        cache_first_service = CacheFirstRpcProxy('some_other_service')

        @rpc
        def cached(self):
            return self.cached_service.some_method('hi', some_arg=True)

        @rpc
        def cache_first(self):
            return self.cache_first.some_method('hi', some_arg=True)

    container = container_factory(Service, rabbit_config)
    container.start()

    cached_rpc = get_extension(container, CachedRpcProxy)
    cache_first_rpc = get_extension(container, CacheFirstRpcProxy)

    def fake_some_method(*args, **kwargs):
        return 'hi'

    with patch('nameko.rpc.MethodProxy.__call__', fake_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook() == 'hi'

    def slow_response(*args, **kwargs):
        eventlet.sleep(3)
        return 'hi'

    start = time.time()
    with patch('nameko.rpc.MethodProxy.__call__', slow_response):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook() == 'hi'
    assert time.time() - start < 2

    cached_rpc.cache = {}

    start = time.time()
    with patch('nameko.rpc.MethodProxy.__call__', slow_response):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook() == 'hi'
    assert time.time() - start >= 3


def test_cached_response_rich_dict_values(rabbit_config, container_factory):

    class Service(object):
        name = "service"

        cached_service = CachedRpcProxy('some_other_service', failover_timeout=1)
        cache_first_service = CacheFirstRpcProxy('some_other_service')

        @rpc
        def cached(self):
            return self.cached_service.some_method('hi', some_arg=True)

        @rpc
        def cache_first(self):
            return self.cache_first.some_method('hi', some_arg=True)

    container = container_factory(Service, rabbit_config)
    container.start()

    cached_rpc = get_extension(container, CachedRpcProxy)
    cache_first_rpc = get_extension(container, CacheFirstRpcProxy)

    def fake_some_method(*args, **kwargs):
        return ['hi', 'ho']

    with patch('nameko.rpc.MethodProxy.__call__', fake_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook() == ['hi', 'ho']

    def broken_some_method(*args, **kwargs):
        raise Exception('hmm')

    with patch('nameko.rpc.MethodProxy.__call__', broken_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook() == ['hi', 'ho']

    def fake_some_method(*args, **kwargs):
        return {'hi': 'ho'}

    with patch('nameko.rpc.MethodProxy.__call__', fake_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook() == {'hi': 'ho'}

    def broken_some_method(*args, **kwargs):
        raise Exception('hmm')

    with patch('nameko.rpc.MethodProxy.__call__', broken_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook() == {'hi': 'ho'}
