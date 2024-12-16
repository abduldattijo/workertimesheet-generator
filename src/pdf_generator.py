# pdf_generator.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime, timedelta
import calendar
import io

class TimesheetPDFGenerator:
    def __init__(self):
        self.page_size = A4
        self.margins = 50
        self.font_size = 10
        self.font_name = 'Helvetica'
        self.standard_start = "10:00"
        self.standard_end = "12:00"
        self.standard_hours = 2
    
    def calculate_monthly_hours(self, hours_per_week):
        """Calculate total monthly hours based on 4.33 weeks per month"""
        return round(hours_per_week * 4.33, 2)
    
    def get_work_slots(self, total_monthly_hours):
        """Calculate how many 2-hour slots we need per month"""
        return round(total_monthly_hours / 2)  # Since each slot is 2 hours
    
    def is_working_day(self, weekday, first_workday, working_days):
        """Determine if a given weekday is a working day"""
        # Convert weekday to 0-based index relative to first working day
        relative_day = (weekday - first_workday) % 7
        return relative_day < working_days
    
    def generate_timesheet_data(self, year, month, employee_name, hours_per_week, 
                              work_window_start, work_window_end, sick_days=None, 
                              holidays=None, national_holidays=None, working_days=5,
                              first_workday=0):
        """Generate timesheet data structure"""
        if sick_days is None:
            sick_days = []
        if holidays is None:
            holidays = []
        if national_holidays is None:
            national_holidays = []
        
        total_monthly_hours = self.calculate_monthly_hours(hours_per_week)
        needed_slots = self.get_work_slots(total_monthly_hours)
        
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
        
        # Calendar data
        cal = calendar.monthcalendar(year, month)
        slots_used = 0
        
        for week in cal:
            for day in week:
                if day == 0:
                    continue
                    
                date = datetime(year, month, day)
                weekday = date.weekday()  # 0 = Monday, 6 = Sunday
                weekday_name = date.strftime("%A")
                date_str = date.strftime("%d.%m.%Y")
                
                is_holiday = day in holidays
                is_sick = day in sick_days
                is_national_holiday = day in national_holidays
                is_workday = self.is_working_day(weekday, first_workday, working_days)
                
                if is_sick:
                    data.append([weekday_name, date_str, "Sick", "Sick", '0'])
                elif is_holiday:
                    data.append([weekday_name, date_str, "Holiday", "Holiday", '0'])
                elif is_national_holiday:
                    data.append([weekday_name, date_str, "National Holiday", "National Holiday", '0'])
                elif not is_workday:
                    data.append([weekday_name, date_str, '0', '0', '0'])
                elif slots_used < needed_slots:
                    # Add standard 2-hour slot
                    data.append([weekday_name, date_str, self.standard_start, self.standard_end, str(self.standard_hours)])
                    slots_used += 1
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