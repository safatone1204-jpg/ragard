"""Integration tests for scoring system."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.scoring import calculate_ragard_score
from app.models.ticker import TickerMetrics


@pytest.fixture
def mock_ticker():
    """Create a mock ticker for testing."""
    return TickerMetrics(
        symbol="TEST",
        company_name="Test Company",
        price=100.0,
        change_pct=5.0,
        market_cap=1000000000,
        ragard_score=None,
        risk_level="medium",
        volume=1000000,
        float_shares=50000000,
        exit_liquidity_rating="good",
        hype_vs_price_text="Moderate hype",
        ragard_label=None,
    )


@pytest.mark.asyncio
async def test_scoring_uses_centralized_module(mock_ticker):
    """Test that scoring routes through centralized module."""
    with patch('app.services.scoring.get_regard_score_for_symbol') as mock_get_score:
        # Mock successful score calculation
        mock_get_score.return_value = {
            'regard_score': 75,
            'data_completeness': 'full',
            'missing_factors': [],
            'base_score': 70.0,
            'ai_regard_score': 80,
        }
        
        result = await calculate_ragard_score(mock_ticker)
        
        # Verify centralized module was called
        mock_get_score.assert_called_once_with("TEST")
        
        # Verify result
        assert result == 75


@pytest.mark.asyncio
async def test_scoring_returns_none_on_failure(mock_ticker):
    """Test that scoring returns None (not placeholder) on failure."""
    with patch('app.services.scoring.get_regard_score_for_symbol') as mock_get_score:
        # Mock failure (returns None)
        mock_get_score.return_value = {
            'regard_score': None,
            'data_completeness': 'unknown',
            'missing_factors': ['market_data'],
            'base_score': None,
            'ai_regard_score': None,
        }
        
        result = await calculate_ragard_score(mock_ticker)
        
        # Should return None, not placeholder 50
        assert result is None


@pytest.mark.asyncio
async def test_scoring_handles_exception_gracefully(mock_ticker):
    """Test that scoring handles exceptions without returning placeholder."""
    with patch('app.services.scoring.get_regard_score_for_symbol') as mock_get_score:
        # Mock exception
        mock_get_score.side_effect = Exception("Network error")
        
        result = await calculate_ragard_score(mock_ticker)
        
        # Should return None, not placeholder 50
        assert result is None


@pytest.mark.asyncio
async def test_scoring_logs_errors(mock_ticker):
    """Test that scoring logs errors appropriately."""
    import logging
    
    with patch('app.services.scoring.get_regard_score_for_symbol') as mock_get_score:
        with patch('app.services.scoring.logger') as mock_logger:
            # Mock exception
            mock_get_score.side_effect = Exception("Test error")
            
            await calculate_ragard_score(mock_ticker)
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            assert "TEST" in str(mock_logger.error.call_args)

