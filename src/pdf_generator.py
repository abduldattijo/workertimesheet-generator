# pdf_generator.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime, timedelta
import calendar
import io
import random

class TimesheetPDFGenerator:
    def __init__(self):
        self.page_size = A4
        self.margins = 50
        self.font_size = 10
        self.font_name = 'Helvetica'
    
    def calculate_monthly_hours(self, hours_per_week):
        """Calculate total monthly hours based on 4.33 weeks per month"""
        return round(hours_per_week * 4.33, 2)

    def format_time(self, start_hour, duration):
        """Format time strings based on start hour and duration"""
        start_time = f"{start_hour:02d}:00"
        end_hour = start_hour + duration
        end_minutes = int((duration % 1) * 60)
        end_time = f"{int(end_hour):02d}:{end_minutes:02d}"
        return start_time, end_time

    def distribute_random_hours(self, total_hours, num_days):
        """Distribute hours randomly across days while maintaining total"""
        if num_days == 0:
            return []
        
        # Create list of possible hour chunks (0.5 to 3 hours in 0.5 increments)
        possible_hours = [0.5, 1, 1.5, 2, 2.5, 3]
        hours_left = total_hours
        days_left = num_days
        distribution = []

        while days_left > 0:
            if days_left == 1:
                # Last day gets remaining hours
                distribution.append(round(hours_left, 1))
                break
            
            # Pick a random amount that leaves enough for remaining days
            max_possible = min(3, hours_left - (0.5 * (days_left - 1)))
            valid_options = [h for h in possible_hours if h <= max_possible]
            
            if not valid_options:
                # If no valid options, use minimum hours
                hours = round(hours_left / days_left, 1)
            else:
                hours = random.choice(valid_options)
            
            distribution.append(hours)
            hours_left = round(hours_left - hours, 1)
            days_left -= 1

        random.shuffle(distribution)
        return distribution

    def generate_timesheet_data(self, year, month, employee_name, hours_per_week, 
                              work_window_start, work_window_end, sick_days=None, 
                              holidays=None, national_holidays=None, working_day_indices=None):
        """Generate timesheet data structure"""
        if sick_days is None:
            sick_days = []
        if holidays is None:
            holidays = []
        if national_holidays is None:
            national_holidays = []
        if working_day_indices is None:
            working_day_indices = [0, 1, 2, 3, 4]  # Default to Monday-Friday
        
        # Calculate total monthly hours
        total_monthly_hours = self.calculate_monthly_hours(hours_per_week)
        
        data = []
        
        # Header information
        data.append(['NAME:', employee_name, '', ''])
        data.append(['CONTRACT:', f'{hours_per_week}h a week since {datetime(year, month, 1).strftime("%d.%m.%Y")} to {datetime(year, month, calendar.monthrange(year, month)[1]).strftime("%d.%m.%Y")}', '', ''])
        data.append([''])
        
        # Statistics row
        data.append(['SICKDAYS', 'HOLIDAYS', 'NATIONAL HOLIDAYS', ''])
        data.append([len(sick_days), len(holidays), len(national_holidays), ''])
        data.append([''])
        
        # Column headers
        data.append(['Weekday', 'Date', 'Work Started', 'Work Finished', 'Total Hours'])
        
        # Get all working days in the month
        cal = calendar.monthcalendar(year, month)
        working_days_count = 0
        workdays = []
        
        # First pass: count working days
        for week in cal:
            for day in week:
                if day == 0:
                    continue
                date = datetime(year, month, day)
                weekday = date.weekday()
                if (weekday in working_day_indices and 
                    day not in sick_days and 
                    day not in holidays and 
                    day not in national_holidays):
                    working_days_count += 1
                    workdays.append(day)
        
        # Distribute hours randomly
        random_hours = self.distribute_random_hours(total_monthly_hours, working_days_count)
        hour_index = 0
        
        # Second pass: generate timesheet
        for week in cal:
            for day in week:
                if day == 0:
                    continue
                
                date = datetime(year, month, day)
                weekday = date.weekday()
                weekday_name = date.strftime("%A")
                date_str = date.strftime("%d.%m.%Y")
                
                is_holiday = day in holidays
                is_sick = day in sick_days
                is_national_holiday = day in national_holidays
                is_workday = weekday in working_day_indices
                
                if is_sick:
                    data.append([weekday_name, date_str, "Sick", "Sick", '0'])
                elif is_holiday:
                    data.append([weekday_name, date_str, "Holiday", "Holiday", '0'])
                elif is_national_holiday:
                    data.append([weekday_name, date_str, "National Holiday", "National Holiday", '0'])
                elif not is_workday:
                    data.append([weekday_name, date_str, '0', '0', '0'])
                elif hour_index < len(random_hours):
                    hours = random_hours[hour_index]
                    start_time, end_time = self.format_time(10, hours)
                    data.append([weekday_name, date_str, start_time, end_time, str(hours)])
                    hour_index += 1
                else:
                    data.append([weekday_name, date_str, '0', '0', '0'])
        
        # Footer
        data.append([''])
        data.append(['NAME', '', '', ''])
        data.append(['DATE SIGNED', '', '', ''])
        data.append(['SIGNATURE', '', '', ''])
        
        return data

    def create_pdf(self, data):
        """Create PDF in memory"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=self.margins,
            leftMargin=self.margins,
            topMargin=self.margins,
            bottomMargin=self.margins
        )
        
        story = []
        
        style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), self.font_size),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 3), (-1, 4), 1, colors.green),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.white),
            ('BACKGROUND', (0, 3), (-1, 3), colors.green),
            ('GRID', (0, 6), (-1, -5), 1, colors.black),
            ('BACKGROUND', (0, 6), (-1, 6), colors.green),
            ('TEXTCOLOR', (0, 6), (-1, 6), colors.white),
        ])
        
        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1*inch])
        table.setStyle(style)
        
        story.append(table)
        doc.build(story)
        
        buffer.seek(0)
        return buffer