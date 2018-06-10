=============================
Nameko Cache Tools
=============================

.. image:: https://badge.fury.io/py/nameko-cachetools.png
    :target: http://badge.fury.io/py/nameko-cachetools

.. image:: https://travis-ci.org/santiycr/nameko-cachetools.png?branch=master
    :target: https://travis-ci.org/santiycr/nameko-cachetools

A few tools to cache interactions between your nameko services, increasing
resiliency and performance at the expense of consistency, when it makes sense.


To use Nameko Cache Tools in a project::



        from nameko.rpc import rpc
        from nameko_cachetools import CachedRpcProxy


        class Service(object):
            name = "demo"

            other_service = CachedRpcProxy('other_service')

            @rpc
            def do_something(self, request):
                # this rpc response will be cached first, then use the different
                # cache strategies available in CachedRpcProxy or
                # CacheFirstRpcProxy
                other_service.do_something('hi')


Caching strategies:
-------------------


CachedRpcProxy
^^^^^^^^^^^^^^

If a cached version of this request exists, a response from the cache is
sent instead of hangling forever or raising an exception.

If a cached version doesn't exist, it will behave like a normal rpc,
and wait indefinitey for a reply. All successful replies are cached.

**WARNING**: Do NOT use this for setters, rpcs meant to modify state in the
target service

Arguments:

cache
  the cache to use. This should resemble a dict but can be more
  sophisticated, like the caches provided by the cachetools package.

failover_timeout
  if a cached version of this query exists, how long
  in seconds should your original request wait until it deems the target
  service as unresponsive and moves on to use a cached response

CacheFirstRpcProxy
^^^^^^^^^^^^^^^^^^

Stores responses from the original services and keeps them cached.

If further requests come in with the same arguments and found in the cache,
a response from the cache is sent instead of hitting the destination service.

**WARNING**: Do NOT use this for setters, rpcs meant to modify state in the
target service

Arguments:

cache
  the cache to use. This should resemble a dict but can be more
  sophisticated, like the caches provided by the cachetools package.

