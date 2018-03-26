# -*- coding: utf-8 -*-

import redis
from django.conf import settings
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)


class Lock(object):

    db = redis.Redis(
        host=settings.LILY_ASYNC_LOCK_DB_HOST,
        port=settings.LILY_ASYNC_LOCK_DB_PORT,
        db=settings.LILY_ASYNC_LOCK_DB_INDEX)

    def __init__(self, lock_id):
        self.lock_id = lock_id

    def acquire(self, expire):

        if self.db.get(self.lock_id):
            logger.debug('Lock: {} already exists'.format(self.lock_id))
            return False

        else:
            self.db.set(self.lock_id, True, expire)
            logger.debug('Lock: {} created'.format(self.lock_id))
            return True

    def release(self):
        self.db.delete(self.lock_id)
