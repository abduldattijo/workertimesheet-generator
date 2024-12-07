# utils.py
import calendar
from datetime import datetime
from typing import List, Tuple

def parse_dates(date_string: str) -> List[int]:
    """
    Parse comma-separated dates into list of integers
    
    Args:
        date_string: String of comma-separated dates (e.g., "1,15,22")
        
    Returns:
        List of integer dates
    """
    if not date_string or date_string.strip() == '':
        return []
    try:
        return [int(x.strip()) for x in date_string.split(',') if x.strip()]
    except ValueError:
        raise ValueError("Invalid date format. Please use comma-separated numbers (e.g., 1,15,22)")

def validate_input(employee_name: str, hours_per_week: int, year: int, 
                  month: int) -> List[str]:
    """
    Validate user input for timesheet generation
    
    Args:
        employee_name: Name of the employee
        hours_per_week: Weekly working hours
        year: Year for timesheet
        month: Month for timesheet
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors = []
    
    if not employee_name or employee_name.strip() == '':
        errors.append("Employee name is required")
    
    if hours_per_week < 1:
        errors.append("Hours per week must be at least 1")
    elif hours_per_week > 40:
        errors.append("Hours per week cannot exceed 40")
    
    if year < 2020 or year > 2030:
        errors.append("Year must be between 2020 and 2030")
    
    if month < 1 or month > 12:
        errors.append("Month must be between 1 and 12")
    
    return errors

def get_month_info(year: int, month: int) -> Tuple[int, int]:
    """
    Get the number of days in a month and the first day of the month
    
    Args:
        year: Year
        month: Month
        
    Returns:
        Tuple of (days_in_month, first_day_of_week)
    """
    return (
        calendar.monthrange(year, month)[1],  # Days in month
        calendar.monthrange(year, month)[0]    # First day of week (0 = Monday)
    )