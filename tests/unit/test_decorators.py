"""
Unit tests for utility decorators — edge cases not covered by test_utils.py.
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import MagicMock

import pytest


class TestRetryDecorator:
    """Test retry decorator edge cases."""

    def test_sync_function_retries(self):
        from src.utils.decorators import retry

        calls = []

        @retry(max_attempts=3, delay=0)
        def flaky_sync():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("not yet")
            return "ok"

        result = flaky_sync()
        assert result == "ok"
        assert len(calls) == 3

    def test_sync_function_with_on_retry_callback(self):
        from src.utils.decorators import retry

        retried = []

        def on_retry_cb(exc, attempt):
            retried.append(attempt)

        @retry(max_attempts=3, delay=0, on_retry=on_retry_cb)
        def flaky():
            if len(retried) < 2:
                raise RuntimeError("fail")
            return "done"

        result = flaky()
        assert result == "done"
        assert len(retried) == 2

    def test_sync_raises_after_all_attempts(self):
        from src.utils.decorators import retry

        @retry(max_attempts=2, delay=0)
        def always_fail():
            raise KeyError("always")

        with pytest.raises(KeyError):
            always_fail()

    @pytest.mark.asyncio
    async def test_async_exhausts_retries(self):
        from src.utils.decorators import retry

        @retry(max_attempts=2, delay=0)
        async def async_always_fail():
            raise ValueError("async fail")

        with pytest.raises(ValueError):
            await async_always_fail()

    @pytest.mark.asyncio
    async def test_async_with_on_retry_callback(self):
        from src.utils.decorators import retry

        retried = []

        def on_retry_cb(exc, attempt):
            retried.append(attempt)

        @retry(max_attempts=3, delay=0, on_retry=on_retry_cb)
        async def flaky_async():
            if len(retried) < 1:
                raise RuntimeError("async fail")
            return "async done"

        result = await flaky_async()
        assert result == "async done"

    def test_specific_exceptions_filter(self):
        from src.utils.decorators import retry

        @retry(max_attempts=3, delay=0, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("not caught")

        with pytest.raises(TypeError):
            raises_type_error()


class TestTimeoutDecorator:
    """Test timeout decorator."""

    def test_non_async_raises_type_error(self):
        from src.utils.decorators import timeout

        with pytest.raises(TypeError):
            @timeout(30)
            def sync_function():
                pass

    @pytest.mark.asyncio
    async def test_async_completes_within_timeout(self):
        from src.utils.decorators import timeout

        @timeout(10)
        async def fast_function():
            return 42

        result = await fast_function()
        assert result == 42

    @pytest.mark.asyncio
    async def test_async_times_out(self):
        from src.utils.decorators import timeout

        @timeout(1)
        async def slow_function():
            await asyncio.sleep(100)

        with pytest.raises(asyncio.TimeoutError):
            await slow_function()


class TestLRUCache:
    """Test LRUCache directly."""

    def test_get_miss(self):
        from src.utils.decorators import LRUCache
        cache = LRUCache(maxsize=10)
        found, val = cache.get("nonexistent")
        assert found is False
        assert val is None

    def test_set_and_get_hit(self):
        from src.utils.decorators import LRUCache
        cache = LRUCache(maxsize=10)
        cache.set("key1", "value1")
        found, val = cache.get("key1")
        assert found is True
        assert val == "value1"

    def test_ttl_expiry(self):
        from src.utils.decorators import LRUCache
        from datetime import datetime, timedelta
        cache = LRUCache(maxsize=10, ttl_seconds=1)
        cache.set("key", "value")

        # Manually backdate the timestamp
        cache.cache["key"] = (cache.cache["key"][0], datetime.now() - timedelta(seconds=2))

        found, val = cache.get("key")
        assert found is False

    def test_lru_eviction(self):
        from src.utils.decorators import LRUCache
        cache = LRUCache(maxsize=2)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")  # Should evict k1 (oldest)

        found1, _ = cache.get("k1")
        found2, _ = cache.get("k2")
        found3, _ = cache.get("k3")

        assert found1 is False  # evicted
        assert found2 is True
        assert found3 is True

    def test_move_to_end_on_get(self):
        from src.utils.decorators import LRUCache
        cache = LRUCache(maxsize=2)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        # Access k1 to make it most recently used
        cache.get("k1")
        cache.set("k3", "v3")  # Should evict k2 (oldest unused)

        found1, _ = cache.get("k1")
        found2, _ = cache.get("k2")
        assert found1 is True   # not evicted (recently accessed)
        assert found2 is False  # evicted

    def test_overwrite_existing_key(self):
        from src.utils.decorators import LRUCache
        cache = LRUCache(maxsize=10)
        cache.set("key", "old")
        cache.set("key", "new")
        _, val = cache.get("key")
        assert val == "new"

    def test_clear(self):
        from src.utils.decorators import LRUCache
        cache = LRUCache(maxsize=10)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.clear()
        assert len(cache.cache) == 0


class TestCacheResultDecorator:
    """Test cache_result decorator edge cases."""

    def test_sync_function_cached(self):
        from src.utils.decorators import cache_result

        calls = []

        @cache_result(ttl_seconds=60)
        def sync_func(x):
            calls.append(x)
            return x * 10

        r1 = sync_func(5)
        r2 = sync_func(5)
        assert r1 == 50
        assert r2 == 50
        assert len(calls) == 1  # second call was cached

    def test_sync_cache_hit_returns_cached(self):
        from src.utils.decorators import cache_result

        @cache_result(ttl_seconds=60)
        def func(x):
            return x + 1

        func(10)
        result = func(10)
        assert result == 11

    def test_cache_clear_method(self):
        from src.utils.decorators import cache_result

        calls = []

        @cache_result(ttl_seconds=60)
        def func(x):
            calls.append(x)
            return x

        func(1)
        func.cache_clear()
        func(1)
        assert len(calls) == 2  # Re-computed after clear

    @pytest.mark.asyncio
    async def test_async_cache_hit(self):
        from src.utils.decorators import cache_result

        calls = []

        @cache_result(ttl_seconds=60)
        async def async_func(x):
            calls.append(x)
            return x * 3

        r1 = await async_func(7)
        r2 = await async_func(7)
        assert r1 == 21
        assert r2 == 21
        assert len(calls) == 1


class TestMeasureTimeDecorator:
    """Test measure_time decorator edge cases."""

    @pytest.mark.asyncio
    async def test_async_function(self):
        from src.utils.decorators import measure_time

        @measure_time()
        async def async_op():
            return "async result"

        result = await async_op()
        assert result == "async result"

    @pytest.mark.asyncio
    async def test_async_with_threshold_not_exceeded(self):
        from src.utils.decorators import measure_time

        @measure_time(threshold_ms=10000)  # Large threshold
        async def fast_async():
            return "fast"

        result = await fast_async()
        assert result == "fast"

    @pytest.mark.asyncio
    async def test_async_no_log(self):
        from src.utils.decorators import measure_time

        @measure_time(log_result=False)
        async def quiet_async():
            return "quiet"

        result = await quiet_async()
        assert result == "quiet"

    def test_sync_with_threshold(self):
        from src.utils.decorators import measure_time

        @measure_time(threshold_ms=0)  # Always log
        def sync_op():
            return 42

        assert sync_op() == 42

    def test_sync_no_log(self):
        from src.utils.decorators import measure_time

        @measure_time(log_result=False)
        def sync_quiet():
            return "quiet"

        assert sync_quiet() == "quiet"


class TestHandleErrorsDecorator:
    """Test handle_errors decorator edge cases."""

    @pytest.mark.asyncio
    async def test_async_success(self):
        from src.utils.decorators import handle_errors

        @handle_errors(default_return=None)
        async def async_ok():
            return "ok"

        result = await async_ok()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_async_error_returns_default(self):
        from src.utils.decorators import handle_errors

        @handle_errors(default_return="fallback")
        async def async_fail():
            raise RuntimeError("oops")

        result = await async_fail()
        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_async_reraise(self):
        from src.utils.decorators import handle_errors

        @handle_errors(default_return=None, reraise=True)
        async def async_fail():
            raise ValueError("reraise me")

        with pytest.raises(ValueError):
            await async_fail()

    def test_sync_success(self):
        from src.utils.decorators import handle_errors

        @handle_errors(default_return=None)
        def sync_ok():
            return "sync ok"

        assert sync_ok() == "sync ok"

    def test_sync_error_returns_default(self):
        from src.utils.decorators import handle_errors

        @handle_errors(default_return=[])
        def sync_fail():
            raise ValueError("fail")

        result = sync_fail()
        assert result == []

    def test_sync_reraise(self):
        from src.utils.decorators import handle_errors

        @handle_errors(default_return=None, reraise=True)
        def sync_fail():
            raise TypeError("reraise")

        with pytest.raises(TypeError):
            sync_fail()

    def test_specific_exception_type(self):
        from src.utils.decorators import handle_errors

        @handle_errors(default_return="caught", exceptions=(ValueError,))
        def raises_value_error():
            raise ValueError("specific")

        result = raises_value_error()
        assert result == "caught"

    def test_unhandled_exception_propagates(self):
        from src.utils.decorators import handle_errors

        @handle_errors(default_return=None, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("not handled")

        with pytest.raises(TypeError):
            raises_type_error()

    def test_custom_log_level(self):
        from src.utils.decorators import handle_errors

        @handle_errors(default_return=None, log_level="warning")
        def fail():
            raise RuntimeError("logged as warning")

        result = fail()
        assert result is None


class TestDeprecatedDecorator:
    """Test deprecated decorator."""

    def test_function_still_executes(self):
        from src.utils.decorators import deprecated

        @deprecated(reason="use new_func instead", version="2.0", alternative="new_func")
        def old_func():
            return "legacy result"

        result = old_func()
        assert result == "legacy result"

    def test_no_kwargs(self):
        from src.utils.decorators import deprecated

        @deprecated()
        def another_old_func():
            return 42

        result = another_old_func()
        assert result == 42

    def test_with_reason_only(self):
        from src.utils.decorators import deprecated

        @deprecated(reason="obsolete")
        def func():
            return "ok"

        assert func() == "ok"

    def test_with_version_only(self):
        from src.utils.decorators import deprecated

        @deprecated(version="3.0")
        def func():
            return True

        assert func() is True


class TestRateLimitDecorator:
    """Test rate_limit decorator."""

    def test_sync_function_executes(self):
        from src.utils.decorators import rate_limit

        @rate_limit(calls=100, period=1.0)
        def fast_func():
            return "ok"

        result = fast_func()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_async_function_executes(self):
        from src.utils.decorators import rate_limit

        @rate_limit(calls=100, period=1.0)
        async def fast_async():
            return "async ok"

        result = await fast_async()
        assert result == "async ok"

    def test_sync_respects_rate(self):
        from src.utils.decorators import rate_limit

        results = []

        @rate_limit(calls=2, period=0.1)  # 2 calls per 0.1s
        def limited():
            results.append(time.time())
            return len(results)

        limited()
        limited()
        # Third call should wait
        limited()
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_async_respects_rate(self):
        from src.utils.decorators import rate_limit

        results = []

        @rate_limit(calls=2, period=0.1)
        async def async_limited():
            results.append(time.time())
            return len(results)

        await async_limited()
        await async_limited()
        await async_limited()
        assert len(results) == 3


class TestSingletonDecorator:
    """Test singleton decorator."""

    def test_returns_same_instance(self):
        from src.utils.decorators import singleton

        @singleton
        class MyClass:
            def __init__(self, value=0):
                self.value = value

        inst1 = MyClass(1)
        inst2 = MyClass(2)
        assert inst1 is inst2

    def test_first_args_used(self):
        from src.utils.decorators import singleton

        @singleton
        class Counter:
            def __init__(self, start=0):
                self.count = start

        c1 = Counter(10)
        c2 = Counter(20)  # Same instance, start=10 already
        assert c1.count == 10
        assert c2.count == 10  # Not 20, same instance
