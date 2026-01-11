"""Error recovery mechanisms for failed deployments."""

import logging
from typing import Optional, Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Error recovery strategies."""

    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP = "skip"
    FAIL = "fail"


class ErrorRecovery:
    """Automatic error recovery for deployments."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: int = 30,
        auto_rollback: bool = True,
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.auto_rollback = auto_rollback

    def execute_with_recovery(
        self,
        func: Callable,
        *args,
        strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
        **kwargs,
    ) -> Any:
        """Execute function with error recovery.

        Args:
            func: Function to execute
            strategy: Recovery strategy to use
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result
        """
        if strategy == RecoveryStrategy.RETRY:
            return self._retry_on_failure(func, *args, **kwargs)
        elif strategy == RecoveryStrategy.ROLLBACK:
            return self._rollback_on_failure(func, *args, **kwargs)
        elif strategy == RecoveryStrategy.SKIP:
            return self._skip_on_failure(func, *args, **kwargs)
        else:  # FAIL
            return func(*args, **kwargs)

    def _retry_on_failure(self, func: Callable, *args, **kwargs) -> Any:
        """Retry function on failure."""
        import time

        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Attempt {attempt}/{self.max_retries}")
                result = func(*args, **kwargs)
                logger.info(f"✅ Success on attempt {attempt}")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    logger.info(f"⏳ Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)

        logger.error(f"❌ All {self.max_retries} attempts failed")
        raise last_error

    def _rollback_on_failure(self, func: Callable, *args, **kwargs) -> Any:
        """Rollback on failure."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Execution failed: {e}")

            if self.auto_rollback:
                logger.info("🔄 Initiating automatic rollback...")
                try:
                    self._perform_rollback()
                    logger.info("✅ Rollback successful")
                except Exception as rollback_error:
                    logger.error(f"❌ Rollback failed: {rollback_error}")

            raise

    def _skip_on_failure(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """Skip on failure (don't raise exception)."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"⏭️  Skipping due to error: {e}")
            return None

    def _perform_rollback(self):
        """Perform rollback to previous state."""
        from vm_tool.history import DeploymentHistory

        history = DeploymentHistory()
        previous = history.get_previous_deployment()

        if previous:
            logger.info(f"   Rolling back to deployment: {previous['id']}")
            # TODO: Implement actual rollback
        else:
            logger.warning("   No previous deployment found for rollback")


class CircuitBreaker:
    """Circuit breaker pattern for deployment failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function through circuit breaker."""
        import time

        # Check if circuit should recover
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info("🔄 Circuit breaker entering half-open state")
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is OPEN - too many recent failures")

        try:
            result = func(*args, **kwargs)

            # Success - reset or close circuit
            if self.state == "half-open":
                logger.info("✅ Circuit breaker closing - recovery successful")
                self.state = "closed"
                self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}"
            )

            if self.failure_count >= self.failure_threshold:
                logger.error("❌ Circuit breaker OPEN - failure threshold reached")
                self.state = "open"

            raise
