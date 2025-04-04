"""Datetime tool implementation.

This module provides the core functionality for datetime tools.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic_ai import RunContext

from .schema import DatetimeInput, DatetimeOutput

logger = logging.getLogger(__name__)

def get_current_date_description() -> str:
    """Get the description for the current date tool."""
    return "Get the current date in ISO format (YYYY-MM-DD)."

def get_current_time_description() -> str:
    """Get the description for the current time tool."""
    return "Get the current time in 24-hour format (HH:MM)."

def format_date_description() -> str:
    """Get the description for the format date tool."""
    return "Format a date string from one format to another."

async def get_current_date(ctx: RunContext[Dict], format: Optional[str] = None) -> Dict[str, Any]:
    """Get the current date.
    
    Args:
        ctx: The run context.
        format: Optional format string (default: ISO format YYYY-MM-DD).
        
    Returns:
        Dict with the formatted date string.
    """
    try:
        logger.info("Getting current date")
        now = datetime.now()
        
        if format:
            # Use the provided format string
            result = now.strftime(format)
            logger.info(f"Formatted date with custom format: {format}")
        else:
            # Use ISO format by default
            result = now.date().isoformat()
            logger.info(f"Formatted date with default ISO format")
        
        # Create and return standardized output
        output = DatetimeOutput.create(result)
        logger.info(f"Date result: {result}")
        return output.dict()
    except Exception as e:
        logger.error(f"Error getting current date: {str(e)}")
        return {
            "result": f"Error: {str(e)}",
            "timestamp": datetime.now().timestamp(),
            "metadata": {"error": str(e)}
        }

async def get_current_time(ctx: RunContext[Dict], format: Optional[str] = None) -> Dict[str, Any]:
    """Get the current time.
    
    Args:
        ctx: The run context.
        format: Optional format string (default: 24-hour format HH:MM).
        
    Returns:
        Dict with the formatted time string.
    """
    try:
        logger.info("Getting current time")
        now = datetime.now()
        
        if format:
            # Use the provided format string
            result = now.strftime(format)
            logger.info(f"Formatted time with custom format: {format}")
        else:
            # Use 24-hour format by default
            result = now.strftime("%H:%M")
            logger.info(f"Formatted time with default 24-hour format")
        
        # Create and return standardized output
        output = DatetimeOutput.create(result)
        logger.info(f"Time result: {result}")
        return output.dict()
    except Exception as e:
        logger.error(f"Error getting current time: {str(e)}")
        return {
            "result": f"Error: {str(e)}",
            "timestamp": datetime.now().timestamp(),
            "metadata": {"error": str(e)}
        }

async def format_date(ctx: RunContext[Dict], date_str: str, input_format: str = "%Y-%m-%d", output_format: str = "%B %d, %Y") -> Dict[str, Any]:
    """Format a date string from one format to another.
    
    Args:
        ctx: The run context.
        date_str: The date string to format
        input_format: The format of the input date string
        output_format: The desired output format
        
    Returns:
        Dict with the reformatted date string.
    """
    try:
        logger.info(f"Formatting date: {date_str} from {input_format} to {output_format}")
        parsed_date = datetime.strptime(date_str, input_format)
        result = parsed_date.strftime(output_format)
        logger.info(f"Formatted date result: {result}")
        
        # Create and return standardized output
        output = DatetimeOutput.create(result)
        return output.dict()
    except ValueError as e:
        error_msg = f"Error parsing date: {str(e)}"
        logger.error(error_msg)
        return {
            "result": error_msg,
            "timestamp": datetime.now().timestamp(),
            "metadata": {"error": str(e)}
        }