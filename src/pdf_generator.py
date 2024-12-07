# pdf_generator.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime
import calendar
import io

class TimesheetPDFGenerator:
    def __init__(self):
        self.page_size = A4
        self.margins = 50
        self.font_size = 10
        self.font_name = 'Helvetica'
    
    def generate_timesheet_data(self, year, month, employee_name, hours_per_week, 
                              work_window_start, work_window_end, sick_days=None, 
                              holidays=None):
        """Generate timesheet data structure"""
        if sick_days is None:
            sick_days = []
        if holidays is None:
            holidays = []
        
        data = []
        
        # Header information
        data.append(['NAME:', employee_name, '', ''])
        data.append(['CONTRACT:', f'{hours_per_week}h a week since {datetime(year, month, 1).strftime("%d.%m.%Y")} to {datetime(year, month, calendar.monthrange(year, month)[1]).strftime("%d.%m.%Y")}', '', ''])
        data.append([''])
        
        # Statistics row
        data.append(['SICKDAYS', 'HOLIDAYS', 'NATIONAL HOLIDAYS', ''])
        data.append([len(sick_days), len(holidays), '0', ''])
        data.append([''])
        
        # Column headers
        data.append(['Weekday', 'Date', 'Work Started', 'Work Finished', 'Total Hours'])
        
        # Calendar data
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            for day in week:
                if day == 0:
                    continue
                    
                date = datetime(year, month, day)
                weekday = date.strftime("%A")
                date_str = date.strftime("%d.%m.%Y")
                
                is_holiday = day in holidays
                is_sick = day in sick_days
                is_weekend = weekday in ["Saturday", "Sunday"]
                
                if is_holiday or is_sick or is_weekend:
                    data.append([weekday, date_str, '0', '0', '0'])
                else:
                    work_start = f"{work_window_start:02d}:00"
                    work_duration = 2
                    work_end = f"{(work_window_start + 2):02d}:00"
                    data.append([weekday, date_str, work_start, work_end, str(work_duration)])
        
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
