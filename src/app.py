import streamlit as st
import base64
from datetime import datetime
import calendar
from pdf_generator import TimesheetPDFGenerator
from utils import parse_dates, validate_input, get_month_info

def main():
    st.set_page_config(
        page_title="Timesheet Generator",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("Employee Timesheet Generator")
    st.markdown("Generate professional timesheets for your employees")
    
    # Initialize PDF generator
    pdf_generator = TimesheetPDFGenerator()
    
    # Create form for input fields
    with st.form("timesheet_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            employee_name = st.text_input(
                "Employee Name",
                help="Enter the full name of the employee"
            )
            
            hours_per_week = st.number_input(
                "Hours per Week",
                min_value=1,
                max_value=40,
                value=4,
                help="Number of contracted hours per week"
            )
            
            work_start = st.number_input(
                "Work Window Start (24h format)",
                min_value=0,
                max_value=23,
                value=10,
                help="Start time of the work day in 24-hour format"
            )
        
        with col2:
            year = st.number_input(
                "Year",
                min_value=2020,
                max_value=2030,
                value=datetime.now().year,
                help="Select the year for the timesheet"
            )
            
            month = st.selectbox(
                "Month",
                range(1, 13),
                format_func=lambda x: calendar.month_name[x],
                help="Select the month for the timesheet"
            )
        
        st.subheader("Absences")
        
        col3, col4 = st.columns(2)
        
        with col3:
            sick_days_str = st.text_input(
                "Sick Days",
                help="Enter sick days as comma-separated numbers (e.g., 1,15,22)"
            )
        
        with col4:
            holidays_str = st.text_input(
                "Holidays",
                help="Enter holiday days as comma-separated numbers (e.g., 5,6,7,8)"
            )
        
        submitted = st.form_submit_button("Generate Timesheet")
    
    # Handle form submission and download button outside the form
    if submitted:
        # Validate input
        errors = validate_input(employee_name, hours_per_week, year, month)
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            try:
                # Parse dates
                sick_days = parse_dates(sick_days_str)
                holidays = parse_dates(holidays_str)
                
                # Generate timesheet data
                data = pdf_generator.generate_timesheet_data(
                    year=year,
                    month=month,
                    employee_name=employee_name,
                    hours_per_week=hours_per_week,
                    work_window_start=work_start,
                    work_window_end=work_start + 5,
                    sick_days=sick_days,
                    holidays=holidays
                )
                
                # Create PDF
                pdf_buffer = pdf_generator.create_pdf(data)
                
                # Create download button
                pdf_bytes = pdf_buffer.getvalue()
                filename = f"timesheet_{employee_name.replace(' ', '_')}_{year}_{month}.pdf"
                
                st.success("✅ Timesheet generated successfully!")
                
                # Place download button outside the form
                st.download_button(
                    label="📥 Download Timesheet PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    key='download-pdf'
                )
                
            except ValueError as e:
                st.error(f"Error: {str(e)}")
            except Exception as e:
                st.error("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    main()