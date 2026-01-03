"""User Regard Score API endpoints."""
import logging
import asyncio
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.auth import get_current_user, AuthenticatedUser
from app.core.rate_limiter import limiter, get_rate_limit
from app.core.supabase_client import get_supabase_admin
from app.core.progress_tracker import create_progress, update_progress, complete_progress, clear_progress
from app.services.trade_history_parser import parse_trade_history_csv
from app.services.regard_score_fetcher import enrich_trades_with_regard_scores
from app.services.user_regard_service import (
    compute_user_regard_base_stats,
    run_user_regard_ai_analysis,
    save_user_regard_summary,
)
from app.services.user_report_data import build_user_report_data
from app.services.user_report_narrative import generate_user_report_narrative
from app.services.user_report_pdf import generate_user_report_pdf
from app.services.open_positions_service import save_open_positions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["user-regard"])


# Response models
class UserRegardResponse(BaseModel):
    """Response model for user regard metrics."""
    regardScore: Optional[float] = None
    wins: int
    losses: int
    winRate: Optional[float] = None
    sampleSize: int
    lastUpdated: Optional[str] = None
    aiSummary: Optional[str] = None


class TradeHistoryUploadResponse(BaseModel):
    """Response model for trade history upload."""
    success: bool
    importedTrades: int
    skippedTrades: int
    message: str


class ProgressResponse(BaseModel):
    """Response model for progress tracking."""
    user_id: str
    current_step: int
    total_steps: int
    percentage: float
    status: str
    message: str
    error: Optional[str] = None
    created_at: str
    updated_at: str


@router.post("/trade-history/upload", response_model=TradeHistoryUploadResponse)
@limiter.limit(get_rate_limit())
async def upload_trade_history(
    request: Request,
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Upload and parse trade history CSV file.
    
    Args:
        file: CSV file containing trade history
        current_user: Authenticated user from middleware
        
    Returns:
        TradeHistoryUploadResponse with import results
    """
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    # Initialize progress tracking (5 steps: parsing, enriching, deleting, inserting, analyzing)
    progress = create_progress(current_user.id, total_steps=5)
    
    try:
        # Step 1: Read and parse CSV
        update_progress(current_user.id, 0, "parsing", "Reading and parsing CSV file...")
        content = await file.read()
        
        # Try to decode with UTF-8, fallback to latin-1 if needed
        try:
            csv_content = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                csv_content = content.decode('latin-1')
                logger.warning(f"File {file.filename} decoded with latin-1 instead of utf-8")
            except UnicodeDecodeError:
                update_progress(current_user.id, 0, "error", "File encoding not supported", "File encoding not supported. Please use UTF-8 or Latin-1.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File encoding not supported. Please use UTF-8 or Latin-1."
                )
        
        # Log first few lines for debugging
        lines = csv_content.split('\n')[:3]
        logger.info(f"CSV file preview (first 3 lines): {lines}")
        
        # Parse CSV
        try:
            result = parse_trade_history_csv(csv_content)
            if len(result) == 3:
                parsed_trades, open_positions, skipped_count = result
            elif len(result) == 2:
                # Backward compatibility if old version
                parsed_trades, skipped_count = result
                open_positions = []
            else:
                raise ValueError(f"Unexpected return from parse_trade_history_csv: {len(result)} items")
            
            update_progress(current_user.id, 1, "parsing", f"Parsed {len(parsed_trades)} trades and {len(open_positions)} open positions from CSV")
        except ValueError as e:
            logger.error(f"CSV parsing error: {e}", exc_info=True)
            update_progress(current_user.id, 0, "error", f"CSV parsing failed: {str(e)}", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error during CSV parsing: {e}", exc_info=True)
            update_progress(current_user.id, 0, "error", f"Parsing error: {str(e)}", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse CSV: {str(e)}"
            )
        
        if not parsed_trades:
            update_progress(current_user.id, 0, "error", "No valid trades found in CSV file", "No valid trades found in CSV file")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid trades found in CSV file"
            )
        
        # Step 2: Enrich trades with Regard Scores at entry/exit times
        update_progress(current_user.id, 2, "enriching", f"Fetching Regard Scores for {len(parsed_trades)} trades...")
        try:
            parsed_trades = await asyncio.wait_for(
                enrich_trades_with_regard_scores(parsed_trades),
                timeout=60.0
            )
            logger.info(f"Enriched {len(parsed_trades)} trades with Regard Scores")
            update_progress(current_user.id, 2, "enriching", f"Enriched {len(parsed_trades)} trades with Regard Scores")
        except asyncio.TimeoutError:
            logger.warning("Regard Score enrichment timed out after 60 seconds. Continuing without Regard Scores.")
            update_progress(current_user.id, 2, "enriching", "Regard Score enrichment timed out, continuing without scores")
        except Exception as e:
            logger.warning(f"Could not enrich trades with Regard Scores: {e}. Continuing without them.")
            update_progress(current_user.id, 2, "enriching", "Could not enrich trades with Regard Scores, continuing without them")
        
        # Step 3: Delete existing trades and save open positions
        update_progress(current_user.id, 3, "inserting", "Preparing database...")
        supabase = get_supabase_admin()
        try:
            delete_response = supabase.table("user_trades")\
                .delete()\
                .eq("user_id", current_user.id)\
                .execute()
            logger.info(f"Deleted existing trades for user {current_user.id}")
        except Exception as e:
            logger.warning(f"Could not delete existing trades (may not exist): {e}")
        
        # Save open positions (don't fail upload if this errors)
        try:
            await asyncio.wait_for(
                save_open_positions(current_user.id, open_positions),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Saving open positions timed out for user {current_user.id}")
        except Exception as e:
            logger.warning(f"Could not save open positions: {e}")
        
        # Validate table exists by trying a simple query
        try:
            test_response = supabase.table("user_trades")\
                .select("id")\
                .limit(1)\
                .execute()
            logger.debug("Table 'user_trades' is accessible")
        except Exception as e:
            error_msg = str(e)
            if "Could not find the table" in error_msg or "PGRST205" in error_msg:
                logger.error(f"Table 'user_trades' does not exist in Supabase. Please run the SQL schema from supabase_schema_user_regard.sql")
                update_progress(current_user.id, 3, "error", "Database table 'user_trades' does not exist. Please run the SQL schema in Supabase.", error_msg)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database table 'user_trades' does not exist. Please run the SQL schema from supabase_schema_user_regard.sql in your Supabase SQL Editor."
                )
            else:
                logger.error(f"Table 'user_trades' may not exist or is not accessible: {e}")
                update_progress(current_user.id, 3, "error", f"Database table error: {str(e)}", str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database table error: {str(e)}"
                )
        
        # Step 4: Insert trades in batches
        batch_size = 500
        imported_count = 0
        total_batches = (len(parsed_trades) + batch_size - 1) // batch_size
        
        import json
        
        for i in range(0, len(parsed_trades), batch_size):
            batch = parsed_trades[i:i + batch_size]
            
            batch_data = []
            for trade in batch:
                # Ensure raw_metadata is JSON-serializable
                raw_metadata = trade.raw_metadata
                if raw_metadata and not isinstance(raw_metadata, dict):
                    try:
                        raw_metadata = json.loads(raw_metadata) if isinstance(raw_metadata, str) else {}
                    except:
                        raw_metadata = {}
                
                trade_data = {
                    "user_id": current_user.id,
                    "ticker": trade.ticker,
                    "side": trade.side,
                    "quantity": float(trade.quantity),
                    "entry_time": trade.entry_time.isoformat(),
                    "exit_time": trade.exit_time.isoformat(),
                    "entry_price": float(trade.entry_price),
                    "exit_price": float(trade.exit_price),
                    "realized_pnl": float(trade.realized_pnl),
                    "holding_period_seconds": int(trade.holding_period_seconds),
                    "raw_metadata": raw_metadata or {},
                }
                
                # Only include regard scores if they exist
                regard_entry = getattr(trade, 'regard_score_at_entry', None)
                regard_exit = getattr(trade, 'regard_score_at_exit', None)
                if regard_entry is not None:
                    trade_data["regard_score_at_entry"] = float(regard_entry)
                if regard_exit is not None:
                    trade_data["regard_score_at_exit"] = float(regard_exit)
                
                batch_data.append(trade_data)
            
            if not batch_data:
                logger.warning(f"Batch {i//batch_size + 1} has no data to insert")
                continue
            
            batch_num = i//batch_size + 1
            update_progress(current_user.id, 3, "inserting", f"Inserting batch {batch_num}/{total_batches} ({len(batch_data)} trades)...")
            
            try:
                logger.info(f"Inserting batch {batch_num} with {len(batch_data)} trades")
                response = supabase.table("user_trades")\
                    .insert(batch_data)\
                    .execute()
                
                # Check if insert was successful
                if response.data:
                    imported_count += len(response.data)
                    logger.info(f"Successfully inserted batch {batch_num}: {len(response.data)} trades")
                else:
                    logger.warning(f"Batch {batch_num} insert returned no data. Response: {response}")
                    # Check for errors in response
                    if hasattr(response, 'error') and response.error:
                        logger.error(f"Supabase error: {response.error}")
                    
            except Exception as e:
                logger.error(f"Error inserting batch {batch_num}: {e}", exc_info=True)
                logger.error(f"Batch data sample (first item): {batch_data[0] if batch_data else 'No data'}")
                # Continue with next batch
        
        if imported_count == 0:
            update_progress(current_user.id, 3, "error", "Failed to import any trades", "Failed to import any trades")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to import any trades"
            )
        
        # Step 5: Recompute User Regard Score
        update_progress(current_user.id, 4, "analyzing", "Computing your Regard Score...")
        analysis_success = False
        try:
            # Compute base stats with timeout
            base_stats = await asyncio.wait_for(
                compute_user_regard_base_stats(current_user.id),
                timeout=60.0  # 60 second timeout for base stats (includes benchmark fetch)
            )
            update_progress(current_user.id, 4, "analyzing", "Running AI analysis...")
            
            # Run AI analysis with timeout
            ai_result = await asyncio.wait_for(
                run_user_regard_ai_analysis(base_stats),
                timeout=30.0  # 30 second timeout for AI
            )
            
            # Save summary
            await save_user_regard_summary(current_user.id, base_stats, ai_result)
            analysis_success = True
            update_progress(current_user.id, 5, "complete", "Analysis complete!")
        except asyncio.TimeoutError:
            logger.error(f"Regard score computation timed out for user {current_user.id}")
            update_progress(current_user.id, 4, "error", "Analysis timed out", "Analysis timed out")
        except Exception as e:
            logger.error(f"Error computing user regard score: {e}", exc_info=True)
            update_progress(current_user.id, 4, "error", f"Analysis failed: {str(e)}", str(e))
            # Don't fail the upload, just log the error
        
        message = (
            "Trade history uploaded and your Regard Score has been updated."
            if analysis_success
            else "Trade history uploaded, but we could not recalculate your Regard Score. Try again later."
        )
        
        # Mark progress as complete
        complete_progress(current_user.id, message)
        
        return TradeHistoryUploadResponse(
            success=True,
            importedTrades=imported_count,
            skippedTrades=skipped_count,
            message=message,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading trade history for user {current_user.id}: {e}", exc_info=True)
        update_progress(current_user.id, 0, "error", f"Internal server error: {str(e)}", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/trade-history/check-tables")
async def check_tables_exist(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Diagnostic endpoint to check if required tables exist in Supabase.
    
    Args:
        current_user: Authenticated user from middleware
        
    Returns:
        Dict with table existence status
    """
    supabase = get_supabase_admin()
    
    results = {
        "user_trades_exists": False,
        "user_regard_summaries_exists": False,
        "errors": []
    }
    
    # Check user_trades table
    try:
        response = supabase.table("user_trades")\
            .select("id")\
            .limit(1)\
            .execute()
        results["user_trades_exists"] = True
    except Exception as e:
        error_msg = str(e)
        results["errors"].append(f"user_trades: {error_msg}")
        if "Could not find the table" in error_msg or "PGRST205" in error_msg:
            results["user_trades_exists"] = False
        else:
            # Table might exist but have other issues
            results["user_trades_exists"] = None
    
    # Check user_regard_summaries table
    try:
        response = supabase.table("user_regard_summaries")\
            .select("user_id")\
            .limit(1)\
            .execute()
        results["user_regard_summaries_exists"] = True
    except Exception as e:
        error_msg = str(e)
        results["errors"].append(f"user_regard_summaries: {error_msg}")
        if "Could not find the table" in error_msg or "PGRST205" in error_msg:
            results["user_regard_summaries_exists"] = False
        else:
            results["user_regard_summaries_exists"] = None
    
    return results


@router.get("/trade-history/progress", response_model=ProgressResponse)
async def get_upload_progress(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get the current progress of a trade history upload.
    
    Args:
        current_user: Authenticated user from middleware
        
    Returns:
        ProgressResponse with current progress status
    """
    from app.core.progress_tracker import get_progress
    
    progress = get_progress(current_user.id)
    
    if not progress:
        # Return a default "not started" progress
        return ProgressResponse(
            user_id=current_user.id,
            current_step=0,
            total_steps=5,
            percentage=0.0,
            status="not_started",
            message="No upload in progress",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
    
    return ProgressResponse(**progress.to_dict())


@router.get("/user-regard", response_model=UserRegardResponse)
async def get_user_regard(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get the current user's Regard Score metrics.
    
    Args:
        current_user: Authenticated user from middleware
        
    Returns:
        UserRegardResponse with regard metrics
    """
    try:
        supabase = get_supabase_admin()
        
        response = supabase.table("user_regard_summaries")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            # No record exists
            return UserRegardResponse(
                regardScore=None,
                wins=0,
                losses=0,
                winRate=None,
                sampleSize=0,
                lastUpdated=None,
                aiSummary=None,
            )
        
        record = response.data[0]
        
        # Convert win_rate from 0-1 to 0-100 if needed, or keep as 0-1
        # Frontend expects 0-1 based on the code I saw, so we'll keep it as 0-1
        win_rate = record.get("win_rate")
        
        return UserRegardResponse(
            regardScore=record.get("regard_score"),
            wins=record.get("wins", 0),
            losses=record.get("losses", 0),
            winRate=win_rate,
            sampleSize=record.get("sample_size", 0),
            lastUpdated=record.get("last_updated"),
            aiSummary=record.get("ai_summary"),
        )
        
    except Exception as e:
        logger.error(f"Error fetching user regard for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch user regard metrics"
        )


@router.get("/user-regard/report")
@limiter.limit(get_rate_limit())
async def generate_user_report(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Generate and return a PDF report of the user's trading performance.
    
    Returns:
        PDF file as binary response
    """
    try:
        # Get display name from user metadata
        display_name = None
        if current_user.first_name or current_user.last_name:
            name_parts = []
            if current_user.first_name:
                name_parts.append(current_user.first_name)
            if current_user.last_name:
                name_parts.append(current_user.last_name)
            display_name = " ".join(name_parts)
        
        # Build report data
        logger.info(f"Building report data for user {current_user.id}")
        try:
            report_data = await build_user_report_data(current_user.id, display_name)
        except Exception as e:
            logger.error(f"Error building report data: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to build report data: {str(e)}"
            )
        
        # Check if there's enough data
        if report_data.sample_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough trade history to generate a meaningful report."
            )
        
        # Generate narrative
        logger.info(f"Generating narrative for user {current_user.id}")
        try:
            narrative = await generate_user_report_narrative(report_data)
        except Exception as e:
            logger.error(f"Error generating narrative: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate narrative: {str(e)}"
            )
        
        # Generate PDF (with timeout to prevent hanging)
        logger.info(f"Generating PDF for user {current_user.id}")
        try:
            pdf_bytes = await asyncio.wait_for(
                generate_user_report_pdf(report_data, narrative),
                timeout=60.0  # 60 second timeout for PDF generation
            )
        except asyncio.TimeoutError:
            logger.error(f"PDF generation timed out for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Report generation timed out. Please try again."
            )
        except Exception as e:
            logger.error(f"Error in PDF generation: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate PDF: {str(e)}"
            )
        
        # Generate filename
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_name = (display_name or "Trader").replace(" ", "-").replace("/", "-").replace("'", "").replace('"', "")[:20]
        filename = f"ragard-trading-report-{safe_name}-{date_str}.pdf"
        
        # Return PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except asyncio.CancelledError:
        # Task was cancelled during shutdown - this is expected
        logger.info(f"Report generation cancelled for user {current_user.id} during shutdown")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is shutting down. Please try again later."
        )
    except Exception as e:
        logger.error(f"Error generating user report for {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate report. Please try again later."
        )

