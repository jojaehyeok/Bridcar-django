from redis import asyncio as aioredis

from django.conf import settings


class RedisQueue(object):
    def __init__(self, key, **redis_kwargs):
        self.host = 'redis'
        self.port = 6379

        if key == None:
            raise Exception('INVALID_KEY')

        self.key = key

        self.rq = aioredis.Redis(**redis_kwargs, host=self.host, port=self.port)

    def size(self):
        return self.rq.llen(self.key)

    def isEmpty(self):
        return self.size() == 0

    async def put(self, element):
        await self.rq.lpush(self.key, element)

    async def get(self, isBlocking=False, timeout=None):
        if isBlocking:
            element = await self.rq.brpop(self.key, timeout=timeout)
            element = element[1]
        else:
            element = await self.rq.rpop(self.key)

        return element

    def get_without_pop(self):
        if self.isEmpty():
            return None

        element = self.rq.lindex(self.key, -1)

        return element
