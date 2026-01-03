"""API response schemas."""
from app.models.ticker import Ticker, TickerMetrics

# For now, we'll use the models directly as response schemas
# If we need different response formats later, we can create separate schemas here
TickerResponse = Ticker
TickerMetricsResponse = TickerMetrics


