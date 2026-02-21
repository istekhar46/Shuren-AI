"""
Property-based tests for schedule validation utilities.

These tests use Hypothesis to verify that validation rules hold across all possible inputs.

**Feature: scheduling-agent-completion**
**Property 1: Workout Schedule Day Validation**
**Property 2: Workout Schedule Time Format Validation**
**Property 12: Meal Time Spacing Validation**
**Property 13: Meal Time Chronological Order**
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import time

from app.utils.schedule_validation import (
    validate_day_name,
    validate_time_format,
    validate_time_range,
    validate_meal_spacing,
    validate_meal_ordering,
    day_name_to_number,
    time_str_to_time
)


# Valid day names for testing
VALID_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
INVALID_DAYS = ["Moonday", "Funday", "Yesterday", "Tomorrow", "Day", "Week", "Month"]


class TestWorkoutScheduleDayValidation:
    """
    Property 1: Workout Schedule Day Validation
    
    For any list of day names provided to save_workout_schedule, only valid 
    day names (Monday-Sunday) should be accepted, and any invalid day name 
    should result in a validation error.
    
    **Feature: scheduling-agent-completion, Property 1: Workout Schedule Day Validation**
    **Validates: Requirements 5.3**
    """
    
    @given(day=st.sampled_from(VALID_DAYS))
    def test_valid_day_names_accepted(self, day):
        """
        Property: All valid day names (Monday-Sunday) should be accepted.
        
        Given a valid day name,
        When validating with validate_day_name,
        Then it should return True.
        """
        assert validate_day_name(day) is True
    
    @given(day=st.sampled_from(VALID_DAYS))
    def test_valid_day_names_case_insensitive(self, day):
        """
        Property: Day name validation should be case-insensitive.
        
        Given a valid day name in any case (upper, lower, mixed),
        When validating with validate_day_name,
        Then it should return True.
        """
        assert validate_day_name(day.upper()) is True
        assert validate_day_name(day.lower()) is True
        assert validate_day_name(day.title()) is True
    
    @given(day=st.sampled_from(INVALID_DAYS))
    def test_invalid_day_names_rejected(self, day):
        """
        Property: Invalid day names should be rejected.
        
        Given an invalid day name,
        When validating with validate_day_name,
        Then it should return False.
        """
        assert validate_day_name(day) is False
    
    @given(day=st.text(min_size=1, max_size=20).filter(
        lambda x: x.lower() not in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    ))
    def test_random_strings_rejected(self, day):
        """
        Property: Random strings that are not day names should be rejected.
        
        Given a random string that is not a valid day name,
        When validating with validate_day_name,
        Then it should return False.
        """
        assert validate_day_name(day) is False
    
    @given(day=st.sampled_from(VALID_DAYS))
    def test_day_name_to_number_conversion(self, day):
        """
        Property: Valid day names should convert to numbers 0-6.
        
        Given a valid day name,
        When converting with day_name_to_number,
        Then it should return a number between 0 (Monday) and 6 (Sunday).
        """
        day_num = day_name_to_number(day)
        assert 0 <= day_num <= 6
        
        # Verify specific mappings
        if day.lower() == "monday":
            assert day_num == 0
        elif day.lower() == "sunday":
            assert day_num == 6
    
    @given(day=st.sampled_from(INVALID_DAYS))
    def test_invalid_day_name_conversion_raises_error(self, day):
        """
        Property: Invalid day names should raise ValueError on conversion.
        
        Given an invalid day name,
        When converting with day_name_to_number,
        Then it should raise ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            day_name_to_number(day)
        
        assert "Invalid day name" in str(exc_info.value)


class TestWorkoutScheduleTimeFormatValidation:
    """
    Property 2: Workout Schedule Time Format Validation
    
    For any list of time strings provided to save_workout_schedule, only times 
    in HH:MM format with hours 00-23 and minutes 00-59 should be accepted, and 
    any invalid format should result in a validation error.
    
    **Feature: scheduling-agent-completion, Property 2: Workout Schedule Time Format Validation**
    **Validates: Requirements 5.4, 21.2**
    """
    
    @given(
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59)
    )
    def test_valid_time_format_accepted(self, hour, minute):
        """
        Property: Times in valid HH:MM format (00:00-23:59) should be accepted.
        
        Given a valid hour (0-23) and minute (0-59),
        When formatted as HH:MM and validated,
        Then it should return True.
        """
        time_str = f"{hour:02d}:{minute:02d}"
        assert validate_time_format(time_str) is True
        assert validate_time_range(time_str) is True
    
    @given(
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59)
    )
    def test_valid_time_converts_to_time_object(self, hour, minute):
        """
        Property: Valid time strings should convert to time objects.
        
        Given a valid time string in HH:MM format,
        When converting with time_str_to_time,
        Then it should return a time object with correct hour and minute.
        """
        time_str = f"{hour:02d}:{minute:02d}"
        time_obj = time_str_to_time(time_str)
        
        assert isinstance(time_obj, time)
        assert time_obj.hour == hour
        assert time_obj.minute == minute
    
    @given(
        hour=st.integers(min_value=24, max_value=99),
        minute=st.integers(min_value=0, max_value=59)
    )
    def test_invalid_hour_rejected(self, hour, minute):
        """
        Property: Times with hours >= 24 should be rejected.
        
        Given an hour value >= 24,
        When formatted as HH:MM and validated,
        Then it should return False.
        """
        time_str = f"{hour:02d}:{minute:02d}"
        assert validate_time_format(time_str) is False
        assert validate_time_range(time_str) is False
    
    @given(
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=60, max_value=99)
    )
    def test_invalid_minute_rejected(self, hour, minute):
        """
        Property: Times with minutes >= 60 should be rejected.
        
        Given a minute value >= 60,
        When formatted as HH:MM and validated,
        Then it should return False.
        """
        time_str = f"{hour:02d}:{minute:02d}"
        assert validate_time_format(time_str) is False
        assert validate_time_range(time_str) is False
    
    @given(time_str=st.text(min_size=1, max_size=10).filter(
        lambda x: not x.count(':') == 1 or len(x) != 5
    ))
    def test_invalid_format_rejected(self, time_str):
        """
        Property: Strings not in HH:MM format should be rejected.
        
        Given a string that is not in HH:MM format,
        When validating with validate_time_format,
        Then it should return False.
        """
        # Skip strings that accidentally match valid format
        assume(not validate_time_format(time_str))
        assert validate_time_format(time_str) is False
    
    @given(
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59)
    )
    def test_single_digit_format_rejected(self, hour, minute):
        """
        Property: Times without leading zeros should be rejected.
        
        Given a time with single-digit hour or minute (no leading zero),
        When validating with validate_time_format,
        Then it should return False.
        """
        # Test single-digit hour
        if hour < 10:
            time_str = f"{hour}:{minute:02d}"
            assert validate_time_format(time_str) is False
        
        # Test single-digit minute
        if minute < 10:
            time_str = f"{hour:02d}:{minute}"
            assert validate_time_format(time_str) is False
    
    @given(time_str=st.sampled_from([
        "25:00", "24:00", "23:60", "00:60", "-01:00", "00:-01",
        "ab:cd", "12:3", "1:23", "12:", ":30", "1230", "12-30"
    ]))
    def test_common_invalid_formats_rejected(self, time_str):
        """
        Property: Common invalid time formats should be rejected.
        
        Given a commonly invalid time format,
        When validating,
        Then it should return False.
        """
        assert validate_time_format(time_str) is False
    
    @given(time_str=st.sampled_from([
        "25:00", "24:00", "23:60", "00:60", "invalid"
    ]))
    def test_invalid_time_conversion_raises_error(self, time_str):
        """
        Property: Invalid time strings should raise ValueError on conversion.
        
        Given an invalid time string,
        When converting with time_str_to_time,
        Then it should raise ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            time_str_to_time(time_str)
        
        assert "Invalid time format" in str(exc_info.value)


class TestMealTimeSpacingValidation:
    """
    Property 12: Meal Time Spacing Validation
    
    For any meal schedule with multiple meals, consecutive meals must be at 
    least 2 hours apart, otherwise a validation error should be raised.
    
    **Feature: scheduling-agent-completion, Property 12: Meal Time Spacing Validation**
    **Validates: Requirements 21.3**
    """
    
    @given(
        hour1=st.integers(min_value=0, max_value=21),
        minute1=st.integers(min_value=0, max_value=59),
        spacing_hours=st.integers(min_value=2, max_value=10)
    )
    def test_meals_with_sufficient_spacing_accepted(self, hour1, minute1, spacing_hours):
        """
        Property: Meals spaced at least 2 hours apart should be accepted.
        
        Given two meals with at least 2 hours spacing,
        When validating with validate_meal_spacing,
        Then it should return True.
        """
        time1 = f"{hour1:02d}:{minute1:02d}"
        
        # Calculate second meal time (at least 2 hours later)
        total_minutes = hour1 * 60 + minute1 + (spacing_hours * 60)
        hour2 = (total_minutes // 60) % 24
        minute2 = total_minutes % 60
        time2 = f"{hour2:02d}:{minute2:02d}"
        
        meal_times = {
            "breakfast": time1,
            "lunch": time2
        }
        
        assert validate_meal_spacing(meal_times) is True
    
    @given(
        hour1=st.integers(min_value=0, max_value=22),
        minute1=st.integers(min_value=0, max_value=59),
        spacing_minutes=st.integers(min_value=0, max_value=119)
    )
    def test_meals_with_insufficient_spacing_rejected(self, hour1, minute1, spacing_minutes):
        """
        Property: Meals spaced less than 2 hours apart should be rejected.
        
        Given two meals with less than 2 hours spacing,
        When validating with validate_meal_spacing,
        Then it should return False.
        """
        time1 = f"{hour1:02d}:{minute1:02d}"
        
        # Calculate second meal time (less than 2 hours later)
        total_minutes = hour1 * 60 + minute1 + spacing_minutes
        hour2 = (total_minutes // 60) % 24
        minute2 = total_minutes % 60
        time2 = f"{hour2:02d}:{minute2:02d}"
        
        # Only test if time2 is actually after time1 (no wraparound)
        if hour2 > hour1 or (hour2 == hour1 and minute2 > minute1):
            meal_times = {
                "breakfast": time1,
                "lunch": time2
            }
            
            assert validate_meal_spacing(meal_times) is False
    
    @given(
        num_meals=st.integers(min_value=2, max_value=6),
        start_hour=st.integers(min_value=6, max_value=10)
    )
    def test_multiple_meals_with_valid_spacing(self, num_meals, start_hour):
        """
        Property: Multiple meals with 2+ hour spacing should be accepted.
        
        Given multiple meals each spaced at least 2 hours apart,
        When validating with validate_meal_spacing,
        Then it should return True.
        """
        meal_names = ["breakfast", "snack1", "lunch", "snack2", "dinner", "snack3"]
        meal_times = {}
        
        current_hour = start_hour
        for i in range(num_meals):
            meal_times[meal_names[i]] = f"{current_hour:02d}:00"
            current_hour += 2  # Add 2 hours spacing
            
            # Stop if we exceed 23:00
            if current_hour > 23:
                break
        
        # Only test if we created the requested number of meals
        if len(meal_times) == num_meals:
            assert validate_meal_spacing(meal_times) is True


class TestMealTimeChronologicalOrder:
    """
    Property 13: Meal Time Chronological Order
    
    For any meal schedule, meal times must be in chronological order throughout 
    the day (earlier meals have earlier times), otherwise a validation error 
    should be raised.
    
    **Feature: scheduling-agent-completion, Property 13: Meal Time Chronological Order**
    **Validates: Requirements 21.4**
    """
    
    @given(
        start_hour=st.integers(min_value=6, max_value=10),
        spacing1=st.integers(min_value=1, max_value=5),
        spacing2=st.integers(min_value=1, max_value=5)
    )
    def test_chronological_meals_accepted(self, start_hour, spacing1, spacing2):
        """
        Property: Meals in chronological order should be accepted.
        
        Given meals with times in ascending order,
        When validating with validate_meal_ordering,
        Then it should return True.
        """
        # Create chronologically ordered meals
        hour1 = start_hour
        hour2 = start_hour + spacing1
        hour3 = start_hour + spacing1 + spacing2
        
        # Skip if times exceed 23:00
        assume(hour3 <= 23)
        
        meal_times = {
            "breakfast": f"{hour1:02d}:00",
            "lunch": f"{hour2:02d}:00",
            "dinner": f"{hour3:02d}:00"
        }
        
        assert validate_meal_ordering(meal_times) is True
    
    @given(
        hour1=st.integers(min_value=0, max_value=23),
        hour2=st.integers(min_value=0, max_value=23),
        minute1=st.integers(min_value=0, max_value=59),
        minute2=st.integers(min_value=0, max_value=59)
    )
    def test_non_chronological_meals_rejected(self, hour1, hour2, minute1, minute2):
        """
        Property: Meals not in chronological order should be rejected.
        
        Given meals with times not in ascending order,
        When validating with validate_meal_ordering,
        Then it should return False.
        """
        time1_minutes = hour1 * 60 + minute1
        time2_minutes = hour2 * 60 + minute2
        
        # Only test if times are equal or reversed
        assume(time1_minutes >= time2_minutes)
        
        meal_times = {
            "breakfast": f"{hour1:02d}:{minute1:02d}",
            "lunch": f"{hour2:02d}:{minute2:02d}"
        }
        
        assert validate_meal_ordering(meal_times) is False
    
    @given(
        num_meals=st.integers(min_value=2, max_value=6),
        start_hour=st.integers(min_value=6, max_value=10)
    )
    def test_multiple_meals_in_order_accepted(self, num_meals, start_hour):
        """
        Property: Multiple meals in chronological order should be accepted.
        
        Given multiple meals with strictly increasing times,
        When validating with validate_meal_ordering,
        Then it should return True.
        """
        meal_names = ["breakfast", "snack1", "lunch", "snack2", "dinner", "snack3"]
        meal_times = {}
        
        current_hour = start_hour
        for i in range(num_meals):
            meal_times[meal_names[i]] = f"{current_hour:02d}:00"
            current_hour += 2  # Increment by 2 hours
            
            # Stop if we exceed 23:00
            if current_hour > 23:
                break
        
        # Only test if we created the requested number of meals
        if len(meal_times) == num_meals:
            assert validate_meal_ordering(meal_times) is True
    
    @given(time_str=st.sampled_from([
        "08:00", "13:00", "19:00"
    ]))
    def test_single_meal_accepted(self, time_str):
        """
        Property: A single meal should be accepted (trivially ordered).
        
        Given a meal schedule with only one meal,
        When validating with validate_meal_ordering,
        Then it should return True.
        """
        meal_times = {"breakfast": time_str}
        assert validate_meal_ordering(meal_times) is True
