# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import io
import random

class TimesheetGenerator:
    def __init__(self):
        self.possible_statuses = ["Work", "Sick", "Holiday", "National Holiday", "Off"]
    
    def calculate_monthly_hours(self, hours_per_week):
        """Calculate total monthly hours based on 4.33 weeks per month"""
        return round(hours_per_week * 4.33, 2)

    def distribute_random_hours(self, total_hours, num_days):
        """Distribute hours randomly across days"""
        if num_days == 0:
            return []
        
        possible_hours = [0.5, 1, 1.5, 2, 2.5, 3]
        hours_left = total_hours
        days_left = num_days
        distribution = []

        while days_left > 0:
            if days_left == 1:
                distribution.append(round(hours_left, 1))
                break
            
            max_possible = min(3, hours_left - (0.5 * (days_left - 1)))
            valid_options = [h for h in possible_hours if h <= max_possible]
            
            if valid_options:
                hours = random.choice(valid_options)
            else:
                hours = round(hours_left / days_left, 1)
            
            distribution.append(hours)
            hours_left = round(hours_left - hours, 1)
            days_left -= 1

        random.shuffle(distribution)
        return distribution

    def format_time(self, hours):
        """Generate start and end times for given hours"""
        if hours == 0:
            return "", ""
        start_time = "10:00"
        end_hour = 10 + int(hours)
        end_minutes = int((hours % 1) * 60)
        end_time = f"{end_hour:02d}:{end_minutes:02d}"
        return start_time, end_time

    def generate_timesheet_data(self, year, month, employee_name, hours_per_week, working_days, specific_dates):
        """Generate initial timesheet data with specific dates for holidays/sick days"""
        total_monthly_hours = self.calculate_monthly_hours(hours_per_week)
        
        # Generate calendar data
        cal = calendar.monthcalendar(year, month)
        data = []
        working_days_count = 0
        
        # Count potential working days (excluding specific dates)
        for week in cal:
            for day in week:
                if day != 0:
                    date_str = f"{day:02d}.{month:02d}.{year}"
                    if (datetime(year, month, day).weekday() in working_days and 
                        date_str not in specific_dates['sick'] and 
                        date_str not in specific_dates['holiday'] and 
                        date_str not in specific_dates['national']):
                        working_days_count += 1
        
        # Generate random hours distribution
        random_hours = self.distribute_random_hours(total_monthly_hours, working_days_count)
        hour_index = 0
        
        for week in cal:
            for day in week:
                if day == 0:
                    continue
                
                date = datetime(year, month, day)
                weekday = date.weekday()
                weekday_name = date.strftime("%A")
                date_str = f"{day:02d}.{month:02d}.{year}"
                
                if date_str in specific_dates['sick']:
                    status = "Sick"
                    hours = 0
                    start_time, end_time = "Sick", "Sick"
                elif date_str in specific_dates['holiday']:
                    status = "Holiday"
                    hours = 0
                    start_time, end_time = "Holiday", "Holiday"
                elif date_str in specific_dates['national']:
                    status = "National Holiday"
                    hours = 0
                    start_time, end_time = "National Holiday", "National Holiday"
                elif weekday in working_days and hour_index < len(random_hours):
                    hours = random_hours[hour_index]
                    start_time, end_time = self.format_time(hours)
                    status = "Work"
                    hour_index += 1
                else:
                    hours = 0
                    start_time, end_time = "0", "0"
                    status = "Off"
                
                data.append({
                    "Weekday": weekday_name,
                    "Date": date_str,
                    "Status": status,
                    "Work Started": start_time,
                    "Work Finished": end_time,
                    "Total Hours": hours
                })
        
        return pd.DataFrame(data)

def update_row_based_on_status(edited_df):
    """Update row values based on status changes"""
    for index, row in edited_df.iterrows():
        if row['Status'] == 'Sick':
            edited_df.at[index, 'Work Started'] = 'Sick'
            edited_df.at[index, 'Work Finished'] = 'Sick'
            edited_df.at[index, 'Total Hours'] = 0
        elif row['Status'] == 'Holiday':
            edited_df.at[index, 'Work Started'] = 'Holiday'
            edited_df.at[index, 'Work Finished'] = 'Holiday'
            edited_df.at[index, 'Total Hours'] = 0
        elif row['Status'] == 'National Holiday':
            edited_df.at[index, 'Work Started'] = 'National Holiday'
            edited_df.at[index, 'Work Finished'] = 'National Holiday'
            edited_df.at[index, 'Total Hours'] = 0
        elif row['Status'] == 'Off':
            edited_df.at[index, 'Work Started'] = '0'
            edited_df.at[index, 'Work Finished'] = '0'
            edited_df.at[index, 'Total Hours'] = 0
        elif row['Status'] == 'Work' and row['Work Started'] in ['Sick', 'Holiday', 'National Holiday', '0']:
            # Reset to default work hours if changing to Work status
            edited_df.at[index, 'Work Started'] = '10:00'
            edited_df.at[index, 'Work Finished'] = '12:00'
            edited_df.at[index, 'Total Hours'] = 2
    return edited_df

def main():
    st.set_page_config(page_title="Interactive Timesheet Generator", layout="wide")
    
    # Initialize session state
    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = None
    if 'generated_timesheet' not in st.session_state:
        st.session_state.generated_timesheet = False
    if 'current_employee' not in st.session_state:
        st.session_state.current_employee = None
    
    st.title("Interactive Timesheet Generator")
    st.markdown("Generate, edit, and export timesheets")
    
    # Initialize generator
    generator = TimesheetGenerator()
    
    with st.form("timesheet_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            employee_name = st.text_input("Employee Name")
            hours_per_week = st.number_input("Hours per Week", min_value=1, max_value=40, value=5)
            
            workweek_type = st.radio(
                "Select Workweek Type",
                options=["5-day week", "6-day week"],
                horizontal=True
            )
            
            first_workday = st.selectbox(
                "Select First Working Day",
                options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
        
        with col2:
            year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)
            month = st.selectbox("Month", range(1, 13), format_func=lambda x: calendar.month_name[x])
            
            st.markdown("Enter days as single numbers (e.g., 1, 2, 3)")
            sick_days = st.text_input(
                "Sick Days",
                help="Example: 1, 2, 3"
            )
            
            holidays = st.text_input(
                "Holidays",
                help="Example: 1, 2, 3"
            )
            
            national_holidays = st.text_input(
                "National Holidays",
                help="Example: 1, 2, 3"
            )
        
        generate_button = st.form_submit_button("Generate Timesheet")
    
    if generate_button:
        if not employee_name:
            st.error("Please enter an employee name")
            return
        
        # Reset state if employee changes
        if st.session_state.current_employee != employee_name:
            st.session_state.edited_df = None
            st.session_state.generated_timesheet = False
            st.session_state.current_employee = employee_name
        
        days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, 
                   "Friday": 4, "Saturday": 5, "Sunday": 6}
        first_day_num = days_map[first_workday]
        
        num_days = 5 if workweek_type == "5-day week" else 6
        working_days = [(first_day_num + i) % 7 for i in range(num_days)]
        
        def parse_dates(date_str):
            if not date_str:
                return []
            try:
                dates = []
                input_days = [d.strip() for d in str(date_str).split(',')]
                for d in input_days:
                    if d:
                        try:
                            if d.isdigit():
                                day = int(d)
                                if 1 <= day <= calendar.monthrange(year, month)[1]:
                                    dates.append(f"{day:02d}.{month:02d}.{year}")
                        except ValueError:
                            st.error(f"Invalid date format in: {d}")
                            continue
                return dates
            except Exception as e:
                st.error(f"Error parsing dates: {str(e)}")
                return []
        
        try:
            specific_dates = {
                'sick': parse_dates(sick_days),
                'holiday': parse_dates(holidays),
                'national': parse_dates(national_holidays)
            }

        except ValueError as e:
            st.error(f"Error parsing dates: {str(e)}")
            return
        
        # Generate initial timesheet
        df = generator.generate_timesheet_data(
            year, month, employee_name, hours_per_week, working_days, specific_dates
        )
        
        # Store in session state
        st.session_state.edited_df = df
        st.session_state.generated_timesheet = True

    # Show editor and export options if timesheet exists
    if st.session_state.generated_timesheet and st.session_state.edited_df is not None:
        st.write("### Edit Timesheet")
        st.markdown("""
        Instructions:
        - Select a status for any day to automatically update its times and hours
        - Status options: Work, Sick, Holiday, National Holiday, Off
        - Time and hours will update automatically based on status
        """)
        
        # Use session state for editing with dynamic updates
        edited_df = st.data_editor(
            st.session_state.edited_df,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=generator.possible_statuses,
                    required=True
                ),
                "Work Started": st.column_config.TextColumn(
                    "Work Started",
                    help="Updates automatically based on status"
                ),
                "Work Finished": st.column_config.TextColumn(
                    "Work Finished",
                    help="Updates automatically based on status"
                ),
                "Total Hours": st.column_config.NumberColumn(
                    "Total Hours",
                    help="Updates automatically based on status",
                    min_value=0,
                    max_value=24,
                    step=0.5
                )
            },
            hide_index=True,
            num_rows="fixed",
            key="timesheet_editor",
            disabled=["Work Started", "Work Finished", "Total Hours"]
        )
        
        # Update related columns based on status
        edited_df = update_row_based_on_status(edited_df)
        
        # Store edited data back to session state
        st.session_state.edited_df = edited_df
        
        # Export options
        st.write("### Export Options")
        
        # CSV export
        csv = edited_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"timesheet_{st.session_state.current_employee.replace(' ', '_')}_{year}_{month}.csv",
            mime="text/csv"
        )

        # Display Excel import instructions
        st.info("""💡 Tip: You can open the CSV file in Excel by:
                1. Opening Excel
                2. Going to Data -> From Text/CSV
                3. Selecting the downloaded CSV file""")
        
        # Display statistics
        total_hours = edited_df['Total Hours'].sum()
        
        # Count days from the DataFrame status
        work_days = len(edited_df[edited_df['Status'] == 'Work'])
        sick_days = len(edited_df[edited_df['Status'] == 'Sick'])
        holidays = len(edited_df[edited_df['Status'] == 'Holiday'])
        national_holidays = len(edited_df[edited_df['Status'] == 'National Holiday'])
        
        st.write("### Monthly Summary")
        col5, col6, col7, col8, col9 = st.columns(5)
        col5.metric("Total Hours", f"{total_hours:.1f}")
        col6.metric("Work Days", work_days)
        col7.metric("Sick Days", sick_days)
        col8.metric("Holidays", holidays)
        col9.metric("National Holidays", national_holidays)

if __name__ == "__main__":
    main()

    