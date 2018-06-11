"""
Tests for `nameko_cachetools` module.
"""
import time
import pytest
from mock import Mock, patch
import random

import eventlet
from nameko.rpc import rpc
from nameko.standalone.rpc import ServiceRpcProxy
from nameko_cachetools import CachedRpcProxy, CacheFirstRpcProxy
from nameko.testing.services import (entrypoint_hook, entrypoint_waiter,
                                     get_extension)


@pytest.fixture
def container(container_factory, rabbit_config):
    class Service(object):
        name = "service"

        cached_service = CachedRpcProxy('some_other_service', failover_timeout=1)
        cache_first_service = CacheFirstRpcProxy('some_other_service')

        @rpc
        def cached(self, *args, **kwargs):
            return self.cached_service.some_method(*args, **kwargs)

        @rpc
        def cache_first(self, *args, **kwargs):
            return self.cache_first_service.some_method(*args, **kwargs)

    container = container_factory(Service, rabbit_config)
    container.start()

    return container


def test_cached_response(container):

    cached_rpc = get_extension(container, CachedRpcProxy)

    def fake_some_method(*args, **kwargs):
        return 'hi'

    with patch('nameko.rpc.MethodProxy.__call__', fake_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook('test') == 'hi'

    def broken_some_method(*args, **kwargs):
        raise Exception('hmm')

    with patch('nameko.rpc.MethodProxy.__call__', broken_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook('test') == 'hi'

    with patch('nameko.rpc.MethodProxy.__call__', broken_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            with pytest.raises(Exception):
                hook('unknown')

    cached_rpc.cache = {}

    with patch('nameko.rpc.MethodProxy.__call__', broken_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            with pytest.raises(Exception):
                hook('test')


def test_cached_response_on_timeout(container):

    cached_rpc = get_extension(container, CachedRpcProxy)

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

def test_cached_rich_args_rich_response(container):

    response = {}
    request = {}
    for i in range(400):
        response[random.randint(1, 1000)] = ['a', (2, 3), {'b': 4.3}]
        request[random.randint(1, 1000)] = ['b', [4, 6], {'c': 8.9}]

    def fake_some_method(*args, **kwargs):
        return response

    with patch('nameko.rpc.MethodProxy.__call__', fake_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook(request) == response

    def broken_some_method(*args, **kwargs):
        raise Exception('hmm')

    with patch('nameko.rpc.MethodProxy.__call__', broken_some_method):
        with entrypoint_hook(container, 'cached') as hook:
            assert hook(request) == response

def test_cache_first(container):

    mock = Mock()
    with patch('nameko.rpc.MethodProxy.__call__', mock):
        with entrypoint_hook(container, 'cache_first') as hook:
            hook('ho')
    mock.assert_called_once_with('ho')

    mock.reset_mock()
    with patch('nameko.rpc.MethodProxy.__call__', mock):
        with entrypoint_hook(container, 'cache_first') as hook:
            hook('ho')
    mock.assert_not_called()

    cache_first_rpc = get_extension(container, CacheFirstRpcProxy)
    cache_first_rpc.cache = {}

    with patch('nameko.rpc.MethodProxy.__call__', mock):
        with entrypoint_hook(container, 'cache_first') as hook:
            hook('ho')
    mock.assert_called_once_with('ho')
