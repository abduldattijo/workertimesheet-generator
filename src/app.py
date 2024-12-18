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
                
                # Determine day status
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

def main():
    st.set_page_config(page_title="Interactive Timesheet Generator", layout="wide")
    
    st.title("Interactive Timesheet Generator")
    st.markdown("Generate, edit, and export timesheets")
    
    # Initialize generator
    generator = TimesheetGenerator()
    
    with st.form("timesheet_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            employee_name = st.text_input("Employee Name")
            hours_per_week = st.number_input("Hours per Week", min_value=1, max_value=40, value=5)
            
            # Workweek type selection
            workweek_type = st.radio(
                "Select Workweek Type",
                options=["5-day week", "6-day week"],
                horizontal=True
            )
            
            # First working day selection
            first_workday = st.selectbox(
                "Select First Working Day",
                options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
        
        with col2:
            year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)
            month = st.selectbox("Month", range(1, 13), format_func=lambda x: calendar.month_name[x])
            
            st.markdown("Enter dates in DD.MM.YYYY format, separated by commas")
            # Specific dates inputs
            sick_days = st.text_input(
                "Sick Days",
                help="Example: 15.5.2024, 16.5.2024"
            )
            
            holidays = st.text_input(
                "Holidays",
                help="Example: 20.5.2024, 21.5.2024"
            )
            
            national_holidays = st.text_input(
                "National Holidays",
                help="Example: 1.5.2024"
            )
        
        generate_button = st.form_submit_button("Generate Timesheet")
    
    if generate_button:
        if not employee_name:
            st.error("Please enter an employee name")
            return
        
        # Convert workweek settings to working days
        days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, 
                   "Friday": 4, "Saturday": 5, "Sunday": 6}
        first_day_num = days_map[first_workday]
        
        # Generate working days based on workweek type and first day
        num_days = 5 if workweek_type == "5-day week" else 6
        working_days = [(first_day_num + i) % 7 for i in range(num_days)]
        
        # Parse dates with proper format handling
        def parse_dates(date_str):
            if not date_str:
                return []
            try:
                dates = []
                for d in date_str.split(','):
                    if d.strip():
                        # Split the date and handle single digits
                        parts = [p.strip() for p in d.strip().split('.')]
                        if len(parts) == 1:  # If only day is provided
                            day = int(parts[0])
                            dates.append(f"{day:02d}.{month:02d}.{year}")
                        elif len(parts) == 3:  # If full date is provided
                            day, m, y = map(int, parts)
                            dates.append(f"{day:02d}.{month:02d}.{year}")
                        else:
                            st.error(f"Invalid date format: {d}. Please use either D or DD.MM.YYYY")
                            continue
                return dates
            except ValueError:
                st.error(f"Invalid date format in: {date_str}. Please use either single digits (e.g., 2, 15) or full dates (DD.MM.YYYY)")
                return []
        # Parse and validate dates
        try:
            specific_dates = {
                'sick': parse_dates(sick_days),
                'holiday': parse_dates(holidays),
                'national': parse_dates(national_holidays)
            }
            
            # Validate dates are within the selected month
            for category, dates in specific_dates.items():
                valid_dates = []
                for date in dates:
                    day, m, y = map(int, date.split('.'))
                    if m == month and y == year and 1 <= day <= calendar.monthrange(year, month)[1]:
                        valid_dates.append(date)
                    else:
                        st.warning(f"Ignoring {category} date {date} - not in selected month")
                specific_dates[category] = valid_dates

        except ValueError as e:
            st.error(f"Error parsing dates: {str(e)}")
            return
        
        # Generate timesheet
        df = generator.generate_timesheet_data(
            year, month, employee_name, hours_per_week, working_days, specific_dates
        )
        
        # Show editable grid
        st.write("### Edit Timesheet")
        st.markdown("""
        Instructions:
        - Double-click any cell to edit
        - For Status, choose from: Work, Sick, Holiday, National Holiday, Off
        - Time format: HH:MM (e.g., 10:00)
        - Edit hours as needed
        """)
        
        edited_df = st.data_editor(
            df,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=generator.possible_statuses,
                    required=True
                ),
                "Work Started": st.column_config.TextColumn(
                    "Work Started",
                    help="Format: HH:MM"
                ),
                "Work Finished": st.column_config.TextColumn(
                    "Work Finished",
                    help="Format: HH:MM"
                ),
                "Total Hours": st.column_config.NumberColumn(
                    "Total Hours",
                    help="Hours worked",
                    min_value=0,
                    max_value=24,
                    step=0.5
                )
            },
            hide_index=True,
            num_rows="fixed",
        )
        
        # Export options
        st.write("### Export Options")
        col3, col4 = st.columns(2)
        
        with col3:
            # Excel export
            excel_buffer = io.BytesIO()
            edited_df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)
            
            st.download_button(
                label="📥 Download as Excel",
                data=excel_buffer,
                file_name=f"timesheet_{employee_name.replace(' ', '_')}_{year}_{month}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col4:
            # CSV export
            csv = edited_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"timesheet_{employee_name.replace(' ', '_')}_{year}_{month}.csv",
                mime="text/csv"
            )
        
        # Display statistics
        total_hours = edited_df['Total Hours'].sum()
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