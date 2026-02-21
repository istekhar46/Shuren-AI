"""
Schedule validation utilities for workout, meal, and hydration schedules.

This module provides validation functions for schedule data including:
- Day name validation (Monday-Sunday)
- Time format validation (HH:MM)
- Time range validation (00:00-23:59)
- Meal spacing validation (minimum 2 hours between meals)
- Meal ordering validation (chronological order)
- Day name to number conversion (Monday=0, Sunday=6)
- Time string to time object conversion
"""

from datetime import time
from typing import Dict
import re


# Valid day names
VALID_DAYS = {
    "monday", "tuesday", "wednesday", "thursday", 
    "friday", "saturday", "sunday"
}

# Day name to number mapping (Monday=0, Sunday=6)
DAY_TO_NUMBER = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}


def validate_day_name(day: str) -> bool:
    """
    Validate that a day name is valid (Monday-Sunday).
    
    Args:
        day: Day name to validate (case-insensitive)
    
    Returns:
        True if day name is valid, False otherwise
    
    Examples:
        >>> validate_day_name("Monday")
        True
        >>> validate_day_name("Moonday")
        False
    """
    if not day or not isinstance(day, str):
        return False
    return day.lower() in VALID_DAYS


def validate_time_format(time_str: str) -> bool:
    """
    Validate that a time string is in HH:MM format.
    
    Args:
        time_str: Time string to validate
    
    Returns:
        True if time is in valid HH:MM format, False otherwise
    
    Examples:
        >>> validate_time_format("07:00")
        True
        >>> validate_time_format("7:00")
        False
        >>> validate_time_format("25:00")
        False
    """
    if not time_str or not isinstance(time_str, str):
        return False
    
    # Check format: exactly HH:MM (2 digits : 2 digits)
    pattern = r'^([0-1][0-9]|2[0-3]):([0-5][0-9])$'
    return bool(re.match(pattern, time_str))


def validate_time_range(time_str: str) -> bool:
    """
    Validate that a time string is within valid range (00:00-23:59).
    
    Args:
        time_str: Time string in HH:MM format
    
    Returns:
        True if time is within valid range, False otherwise
    
    Examples:
        >>> validate_time_range("00:00")
        True
        >>> validate_time_range("23:59")
        True
        >>> validate_time_range("24:00")
        False
    """
    if not validate_time_format(time_str):
        return False
    
    try:
        hours, minutes = map(int, time_str.split(':'))
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except (ValueError, AttributeError):
        return False


def validate_meal_spacing(meal_times: Dict[str, str]) -> bool:
    """
    Validate that meals are spaced at least 2 hours apart.
    
    Args:
        meal_times: Dictionary mapping meal names to time strings (HH:MM)
    
    Returns:
        True if all meals are at least 2 hours apart, False otherwise
    
    Examples:
        >>> validate_meal_spacing({"breakfast": "08:00", "lunch": "13:00"})
        True
        >>> validate_meal_spacing({"breakfast": "08:00", "lunch": "09:00"})
        False
    """
    if not meal_times or not isinstance(meal_times, dict):
        return False
    
    # Validate all time formats first
    for time_str in meal_times.values():
        if not validate_time_format(time_str):
            return False
    
    # Convert to time objects and sort
    times = []
    for meal_name, time_str in meal_times.items():
        try:
            time_obj = time_str_to_time(time_str)
            times.append(time_obj)
        except ValueError:
            return False
    
    times.sort()
    
    # Check spacing between consecutive meals (minimum 2 hours = 120 minutes)
    for i in range(len(times) - 1):
        current_minutes = times[i].hour * 60 + times[i].minute
        next_minutes = times[i + 1].hour * 60 + times[i + 1].minute
        
        spacing_minutes = next_minutes - current_minutes
        if spacing_minutes < 120:  # Less than 2 hours
            return False
    
    return True


def validate_meal_ordering(meal_times: Dict[str, str]) -> bool:
    """
    Validate that meal times are in chronological order throughout the day.
    
    This function checks that when meals are sorted by their time values,
    they maintain chronological order (no time travel).
    
    Args:
        meal_times: Dictionary mapping meal names to time strings (HH:MM)
    
    Returns:
        True if meals are in chronological order, False otherwise
    
    Examples:
        >>> validate_meal_ordering({"breakfast": "08:00", "lunch": "13:00", "dinner": "19:00"})
        True
        >>> validate_meal_ordering({"breakfast": "13:00", "lunch": "08:00"})
        False
    """
    if not meal_times or not isinstance(meal_times, dict):
        return False
    
    # Validate all time formats first
    for time_str in meal_times.values():
        if not validate_time_format(time_str):
            return False
    
    # Convert to time objects
    times = []
    for time_str in meal_times.values():
        try:
            time_obj = time_str_to_time(time_str)
            times.append(time_obj)
        except ValueError:
            return False
    
    # Check if times are in ascending order
    for i in range(len(times) - 1):
        if times[i] >= times[i + 1]:
            return False
    
    return True


def day_name_to_number(day: str) -> int:
    """
    Convert day name to number (Monday=0, Sunday=6).
    
    Args:
        day: Day name (case-insensitive)
    
    Returns:
        Day number (0-6)
    
    Raises:
        ValueError: If day name is invalid
    
    Examples:
        >>> day_name_to_number("Monday")
        0
        >>> day_name_to_number("Sunday")
        6
        >>> day_name_to_number("Moonday")
        Traceback (most recent call last):
        ...
        ValueError: Invalid day name: Moonday
    """
    if not day or not isinstance(day, str):
        raise ValueError(f"Invalid day name: {day}")
    
    day_lower = day.lower()
    if day_lower not in DAY_TO_NUMBER:
        raise ValueError(f"Invalid day name: {day}")
    
    return DAY_TO_NUMBER[day_lower]


def time_str_to_time(time_str: str) -> time:
    """
    Convert time string to time object.
    
    Args:
        time_str: Time string in HH:MM format
    
    Returns:
        time object
    
    Raises:
        ValueError: If time string is invalid
    
    Examples:
        >>> time_str_to_time("07:00")
        datetime.time(7, 0)
        >>> time_str_to_time("23:59")
        datetime.time(23, 59)
        >>> time_str_to_time("25:00")
        Traceback (most recent call last):
        ...
        ValueError: Invalid time format: 25:00
    """
    if not validate_time_format(time_str):
        raise ValueError(f"Invalid time format: {time_str}")
    
    try:
        hours, minutes = map(int, time_str.split(':'))
        return time(hour=hours, minute=minutes)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid time format: {time_str}") from e
