========
Usage
========

To use nameko-cachetools in a project::



        from nameko.rpc import rpc
        from nameko_cachetools import CachedRpcProxy


        class Service(object):
            name = "demo"

            other_service = CachedRpcProxy('other_service')

            @rpc
            def do_something(self, request):
                # this rpc response will be cached, further queries will be
                # timed and cached values will be returned if not response is
                # received or an exception is raised at the destination service
                other_service.do_something('hi')

To use a more advanced cache from the cachetools module::



        from nameko.rpc import rpc
        from nameko_cachetools import CachedRpcProxy
        from cachetools import TTLCache


        class Service(object):
            name = "demo"

            # use a TTL cache that will only hold 1024 different rpc interactions
            # and expire them afer 30 seconds
            other_service = CachedRpcProxy('other_service', cache=TTLCache(1024, 30))

            @rpc
            def do_something(self, request):
                # this rpc response will be cached. For the next 30 seconds,
                # further queries will not reach the target service but still
                # return the cached response
                other_service.do_something('hi')


Caching strategies:
-------------------


CachedRpcProxy
^^^^^^^^^^^^^^

If a cached version of this request exists, a response from the cache is
sent instead of hanging forever or raising an exception.

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
