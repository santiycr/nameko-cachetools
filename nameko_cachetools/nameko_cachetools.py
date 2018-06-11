#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A few tools to cache interactions between your nameko services, increasing
resiliency and performance at the expense of consistency, when it makes sense.
"""


import json
from logging import getLogger

from eventlet.timeout import Timeout
from nameko.rpc import RpcProxy, ServiceProxy, MethodProxy


_log = getLogger(__name__)


class CachedRpcProxy(RpcProxy):
    """
    Stores responses from the original services and keeps them cached.

    If a cached version of this request exists, a response from the cache is
    sent instead of hangling forever or raising an exception.

    If a cached version doesn't exist, it will behave like a normal rpc,
    and wait indefinitey for a reply. All successful replies are cached.

    WARNING: Do NOT use this for setters, rpcs meant to modify state in the
    target service

    args:
      - cache: the cache to use. This should resemble a dict but can be more
        sophisticated, like the caches provided by the cachetools package.
      - failover_timeout: if a cached version of this query exists, how long
        in seconds should your original request wait until it deems the target
        service as unresponsive and moves on to use a cached response
    """

    def __init__(self, target_service, **options):
        self.target_service = target_service
        self.cache = options.pop('cache', dict())
        self.options = options

    def get_dependency(self, worker_ctx):
        return CachedServiceProxy(
            worker_ctx,
            self.target_service,
            self.rpc_reply_listener,
            cache=self.cache,
            **self.options
        )


class CacheFirstRpcProxy(RpcProxy):
    """
    Stores responses from the original services and keeps them cached.

    If further requests come in with the same arguments, a response from the
    cache is sent instead of hitting the destination service.

    WARNING: Do NOT use this for setters, rpcs meant to modify state in the
    target service

    args:
      - cache: the cache to use. This should resemble a dict but can be more
        sophisticated, like the caches provided by the cachetools package.
    """

    def __init__(self, target_service, **options):
        self.target_service = target_service
        self.cache = options.pop('cache', dict())
        options['use_cache_first'] = True
        self.options = options

    def get_dependency(self, worker_ctx):
        return CachedServiceProxy(
            worker_ctx,
            self.target_service,
            self.rpc_reply_listener,
            cache=self.cache,
            **self.options
        )


class CachedServiceProxy(ServiceProxy):

    def __init__(self, *args, **kwargs):
        cache = kwargs.pop('cache')
        super(CachedServiceProxy, self).__init__(*args, **kwargs)
        self.cache = cache.get(self.service_name, {})
        cache[self.service_name] = self.cache

    def __getattr__(self, name):
        return CachedMethodProxy(
            self.worker_ctx,
            self.service_name,
            name,
            self.reply_listener,
            cache=self.cache,
            **self.options
        )


class CachedMethodProxy(MethodProxy):

    def __init__(self, *args, **kwargs):
        self.cache = kwargs.pop('cache')
        self.failover_timeout = kwargs.pop('failover_timeout', 0)
        self.use_cache_first = kwargs.pop('use_cache_first', False)
        super(CachedMethodProxy, self).__init__(*args, **kwargs)

    def get_from_cache(self, key):
        if key not in self.cache:
            return False, None
        return True, self.cache[key][0]

    def __call__(self, *args, **kwargs):
        args_hash = json.dumps((args, kwargs), sort_keys=True)
        timeout = None
        incache, cached_response = self.get_from_cache(args_hash)
        if self.use_cache_first and incache:
            return cached_response
        if self.failover_timeout and incache:
            # we have a value, let's set a timeout and use our cache if service
            # isn't responsive
            timeout = Timeout(self.failover_timeout)
        try:
            reply = super(CachedMethodProxy, self).__call__(*args, **kwargs)
        except (Exception, Timeout) as e:
            error = 'timeout' if isinstance(e, Timeout) else 'error'
            _log.warn('%s when getting value for %s. using cache', error, self)
            if incache:
                _log.warn('response found in cache. using cache')
                return cached_response
            else:
                _log.error('request not in cache, re-raising %s', self.cache)
                raise e
        finally:
            if timeout:
                timeout.cancel()
        self.cache[args_hash] = (reply,)
        return reply
