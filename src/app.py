# app.py
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
            
            # Working days selection
            st.write("Select Working Days:")
            working_days = {}
            col_a, col_b = st.columns(2)
            with col_a:
                working_days["Monday"] = st.checkbox("Monday", value=True)
                working_days["Tuesday"] = st.checkbox("Tuesday", value=True)
                working_days["Wednesday"] = st.checkbox("Wednesday", value=True)
                working_days["Thursday"] = st.checkbox("Thursday", value=True)
            with col_b:
                working_days["Friday"] = st.checkbox("Friday", value=True)
                working_days["Saturday"] = st.checkbox("Saturday")
                working_days["Sunday"] = st.checkbox("Sunday")
        
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
        
        st.subheader("Absences and Holidays")
        
        col3, col4 = st.columns(2)
        
        with col3:
            sick_days_str = st.text_input(
                "Sick Days",
                help="Enter sick days as comma-separated numbers (e.g., 1,15,22)"
            )
            
            holidays_str = st.text_input(
                "Personal Holidays",
                help="Enter holiday days as comma-separated numbers (e.g., 5,6,7,8)"
            )
        
        with col4:
            national_holidays_str = st.text_input(
                "National Holidays",
                help="Enter national holiday days as comma-separated numbers (e.g., 1,25)"
            )
        
        submitted = st.form_submit_button("Generate Timesheet")
    
    # Handle form submission and download button outside the form
    if submitted:
        # Check if at least one working day is selected
        if not any(working_days.values()):
            st.error("Please select at least one working day")
            return
            
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
                national_holidays = parse_dates(national_holidays_str)
                
                # Convert working days to list of indices
                working_day_indices = [i for i, (day, checked) in enumerate(working_days.items()) if checked]
                
                # Generate timesheet data
                data = pdf_generator.generate_timesheet_data(
                    year=year,
                    month=month,
                    employee_name=employee_name,
                    hours_per_week=hours_per_week,
                    work_window_start=10,  # Fixed to 10:00
                    work_window_end=12,    # Fixed to 12:00
                    sick_days=sick_days,
                    holidays=holidays,
                    national_holidays=national_holidays,
                    working_day_indices=working_day_indices
                )
                
                # Create PDF
                pdf_buffer = pdf_generator.create_pdf(data)
                
                # Create download button
                pdf_bytes = pdf_buffer.getvalue()
                filename = f"timesheet_{employee_name.replace(' ', '_')}_{year}_{month}.pdf"
                
                st.success("✅ Timesheet generated successfully!")
                
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
                raise e

if __name__ == "__main__":
    main()