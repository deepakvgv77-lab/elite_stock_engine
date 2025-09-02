class EliteStockEngineError(Exception):
    pass

class DataFetchError(EliteStockEngineError):
    def __init__(self, source: str, message: str = None):
        self.source = source
        self.message = message or f"Data fetch failed for {source}"
        super().__init__(self.message)

class DataValidationError(EliteStockEngineError):
    def __init__(self, validator: str, details: str = None):
        self.validator = validator
        self.details = details
        self.message = f"Data validation failed: {validator}"
        if details:
            self.message += f" - {details}"
        super().__init__(self.message)

class DatabaseError(EliteStockEngineError):
    def __init__(self, operation: str, details: str = None):
        self.operation = operation
        self.details = details
        self.message = f"Database operation failed: {operation}"
        if details:
            self.message += f" - {details}"
        super().__init__(self.message)

class ConfigurationError(EliteStockEngineError):
    def __init__(self, config_key: str, message: str = None):
        self.config_key = config_key
        self.message = message or f"Invalid configuration for {config_key}"
        super().__init__(self.message)

class RateLimitError(EliteStockEngineError):
    def __init__(self, source: str, retry_after: int = None):
        self.source = source
        self.retry_after = retry_after
        self.message = f"Rate limit exceeded for {source}"
        if retry_after:
            self.message += f". Retry after {retry_after} seconds"
        super().__init__(self.message)

class CircuitBreakerOpenError(EliteStockEngineError):
    def __init__(self, service: str):
        self.service = service
        self.message = f"Circuit breaker is open for {service}"
        super().__init__(self.message)
