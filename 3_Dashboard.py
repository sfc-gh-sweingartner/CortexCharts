"""
Dashboard App
====================
This app displays interactive dashboards with Snowflake data visualizations.
"""
import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session
import datetime
import json
import decimal  # For handling Decimal objects
import sys
import os

# Add path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set page config
st.set_page_config(
    page_title="Dashboard",
    page_icon="📈",
    layout="wide",
)

# Initialize session
try:
    session = get_active_session()
except:
    st.error("Failed to connect to Snowflake. Please make sure you have an active session.")
    st.stop()

# Function to initialize session state
def init_session_state():
    if "selected_dashboard" not in st.session_state:
        st.session_state.selected_dashboard = None
    
    if "pinned_reports" not in st.session_state:
        st.session_state.pinned_reports = []
    
    if "dashboard_name" not in st.session_state:
        st.session_state.dashboard_name = ""
    
    if "create_new" not in st.session_state:
        st.session_state.create_new = False
    
    # Add debug mode flag
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
    
    # Initialize report data cache
    if "report_data_cache" not in st.session_state:
        st.session_state.report_data_cache = {}

# Function to load dashboards from Snowflake
def load_dashboards():
    try:
        query = "SELECT DASHBOARD_ID, DASHBOARD_NAME, REPORTS FROM CORTEX_ANALYST_DASHBOARDS ORDER BY DASHBOARD_NAME"
        dashboards = session.sql(query).collect()
        return pd.DataFrame(dashboards)
    except Exception as e:
        st.error(f"Error loading dashboards: {e}")
        return pd.DataFrame(columns=["DASHBOARD_ID", "DASHBOARD_NAME", "REPORTS"])

# Function to load reports from Snowflake
def load_reports():
    try:
        query = "SELECT REPORT_ID, REPORT_NAME, REPORT_DESCRIPTION, SQL_STATEMENT, CHART_CODE, CHART_METADATA FROM CORTEX_ANALYST_REPORTS ORDER BY REPORT_NAME"
        reports = session.sql(query).collect()
        return pd.DataFrame(reports)
    except Exception as e:
        st.error(f"Error loading reports: {e}")
        return pd.DataFrame(columns=["REPORT_ID", "REPORT_NAME", "REPORT_DESCRIPTION", "SQL_STATEMENT", "CHART_CODE", "CHART_METADATA"])

# Function to save a dashboard
def save_dashboard(dashboard_name, report_ids):
    try:
        # Convert list of report IDs to string
        reports_str = ",".join(map(str, report_ids))
        
        # Check if dashboard exists
        check_query = f"SELECT COUNT(*) FROM CORTEX_ANALYST_DASHBOARDS WHERE DASHBOARD_NAME = '{dashboard_name}'"
        count = session.sql(check_query).collect()[0][0]
        
        if count > 0:
            # Update existing dashboard
            update_query = f"""
            UPDATE CORTEX_ANALYST_DASHBOARDS 
            SET REPORTS = '{reports_str}', UPDATED_AT = CURRENT_TIMESTAMP()
            WHERE DASHBOARD_NAME = '{dashboard_name}'
            """
            session.sql(update_query).collect()
        else:
            # Insert new dashboard
            insert_query = f"""
            INSERT INTO CORTEX_ANALYST_DASHBOARDS (DASHBOARD_NAME, REPORTS)
            VALUES ('{dashboard_name}', '{reports_str}')
            """
            session.sql(insert_query).collect()
        
        return True
    except Exception as e:
        st.error(f"Error saving dashboard: {e}")
        return False

# Function to detect and process column types
def process_dataframe(df):
    """Process a dataframe to detect column types and improve chart rendering."""
    try:
        # Convert Decimal objects to float to avoid serialization issues
        for col in df.select_dtypes(include=['object']).columns:
            # Check if column contains Decimal objects
            if df[col].dropna().apply(lambda x: isinstance(x, decimal.Decimal)).any():
                df[col] = df[col].astype(float)
        
        # Improve date column detection and conversion
        date_related_terms = ['date', 'month', 'year', 'day', 'time', 'dt', 'period']
        for col in df.columns:
            # Skip columns that are already recognized as dates
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                continue
            
            # Try to convert columns with date-related names or that look like dates
            col_lower = col.lower()
            if any(term in col_lower for term in date_related_terms):
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass  # Keep original if conversion fails
        
        # Store column type information that can be used for chart creation
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        text_cols = [col for col in df.columns if col not in numeric_cols and col not in date_cols]
        
        # Store column information in dataframe attributes
        if not hasattr(df, 'attrs'):
            df.attrs = {}
        
        df.attrs['column_types'] = {
            'numeric_cols': numeric_cols,
            'date_cols': date_cols,
            'text_cols': text_cols
        }
        
        # Based on the column types, determine the chart type and generate chart metadata
        # This helps the chart rendering be more consistent
        if len(date_cols) == 1 and len(numeric_cols) >= 1:
            # Time series data detected
            chart_metadata = {
                'chart1_columns': {
                    'date_col': date_cols[0],
                    'numeric_col': numeric_cols[0]
                }
            }
            df.attrs['chart_metadata'] = chart_metadata
        elif len(date_cols) == 1 and len(text_cols) >= 1 and len(numeric_cols) >= 1:
            # Time series with categories
            chart_metadata = {
                'chart3_columns': {
                    'date_col': date_cols[0],
                    'text_col': text_cols[0],
                    'numeric_col': numeric_cols[0]
                }
            }
            df.attrs['chart_metadata'] = chart_metadata
        
        return df
    except Exception as e:
        st.error(f"Error processing dataframe: {e}")
        return df

# Function to render a report chart
def render_chart(report):
    """Render a chart for a report, preserving metadata and using improved chart code execution."""
    try:
        # Check if this report's data is cached
        report_id = report["REPORT_ID"]
        df = None
        chart_metadata = None
        stored_metadata = None
        
        # Extract stored metadata from the report if it exists
        if "CHART_METADATA" in report and report["CHART_METADATA"]:
            try:
                stored_metadata = json.loads(report["CHART_METADATA"])
                if st.session_state.debug_mode:
                    st.write(f"Loaded stored metadata for report {report['REPORT_NAME']}:", stored_metadata)
            except Exception as json_err:
                if st.session_state.debug_mode:
                    st.error(f"Error parsing stored metadata for report {report['REPORT_NAME']}: {json_err}")
        
        # If not in cache, fetch data
        if report_id not in st.session_state.report_data_cache:
            # Execute SQL to get data
            sql = report["SQL_STATEMENT"]
            if not sql or sql.strip() == "":
                st.error(f"Missing SQL statement for report: {report['REPORT_NAME']}")
                return None
            
            # Execute the SQL query
            try:
                data = session.sql(sql).collect()
                df = pd.DataFrame(data)
                
                # Process the dataframe to detect column types and improve rendering
                df = process_dataframe(df)
                
                # If we have stored metadata, apply it to the dataframe
                if stored_metadata:
                    if not hasattr(df, 'attrs'):
                        df.attrs = {}
                    df.attrs['chart_metadata'] = stored_metadata
                
                # Cache the processed dataframe
                st.session_state.report_data_cache[report_id] = {
                    'df': df,
                    'chart_metadata': df.attrs.get('chart_metadata', None) if hasattr(df, 'attrs') else None
                }
                
            except Exception as sql_err:
                st.error(f"SQL Error for report {report['REPORT_NAME']}: {sql_err}")
                return None
        else:
            # Use cached data
            cache_entry = st.session_state.report_data_cache[report_id]
            df = cache_entry['df']
            chart_metadata = cache_entry['chart_metadata']
        
        # Ensure we have a dataframe to work with
        if df is None:
            st.error(f"No data available for report: {report['REPORT_NAME']}")
            return None
        
        # Create a copy of the dataframe to avoid modifying the original
        df_copy = df.copy()
        
        # Ensure df_copy has all the necessary attributes
        if not hasattr(df_copy, 'attrs'):
            df_copy.attrs = {}
        
        # Apply stored metadata first if available (highest priority)
        if stored_metadata:
            df_copy.attrs['chart_metadata'] = stored_metadata
        # Apply chart metadata if available from cache
        elif chart_metadata is not None:
            df_copy.attrs['chart_metadata'] = chart_metadata
        # Or from the original dataframe
        elif hasattr(df, 'attrs') and 'chart_metadata' in df.attrs:
            df_copy.attrs['chart_metadata'] = df.attrs['chart_metadata']
        
        # Get the chart code
        chart_code = report["CHART_CODE"]
        if not chart_code or chart_code.strip() == "":
            st.error(f"Missing chart code for report: {report['REPORT_NAME']}")
            return None
        
        # Create local namespace for execution
        local_vars = {"pd": pd, "alt": alt, "df": df_copy, "json": json, "st": st}
        
        # Try to execute the custom chart code first
        try:
            # First check if this is Chart 4 with a template variable issue
            if "{selected_text_col}" in chart_code:
                # This is likely a Chart 4 with templating issue
                # Get metadata if available
                if hasattr(df_copy, 'attrs') and 'chart_metadata' in df_copy.attrs:
                    metadata = df_copy.attrs['chart_metadata']
                    if 'chart4_columns' in metadata:
                        # This is definitely Chart 4, fallback to our function-based implementation
                        return render_chart_4_fallback(df_copy, metadata['chart4_columns'], report['REPORT_NAME'])
            
            # Create a comprehensive globals dict with all necessary modules
            global_vars = {
                "st": st, 
                "pd": pd, 
                "alt": alt,
                "json": json,
                # Include other common modules that might be needed
                "datetime": datetime,
                "math": __import__('math'),
                "random": __import__('random'),
                # Add the globals from the current environment
                **globals()
            }
            
            # First execute the chart code (which should define create_chart)
            exec(chart_code, global_vars, local_vars)
            
            # Then call the create_chart function if it exists
            if "create_chart" in local_vars:
                chart = local_vars["create_chart"](df_copy)
                if chart:
                    return chart
            else:
                # If no create_chart function, check if chart variable was directly created
                chart = local_vars.get("chart")
                if chart:
                    return chart
        except Exception as code_err:
            if st.session_state.debug_mode:
                st.error(f"Error executing chart code for report {report['REPORT_NAME']}: {code_err}")
                
        # No custom chart was created successfully, create a simple default chart
        try:
            # Create a simple default chart based on available metadata
            if hasattr(df_copy, 'attrs') and 'chart_metadata' in df_copy.attrs and df_copy.attrs['chart_metadata']:
                metadata = df_copy.attrs['chart_metadata']
                
                # Check for different chart types in metadata
                if 'chart1_columns' in metadata:
                    # Time series chart
                    date_col = metadata['chart1_columns']['date_col']
                    numeric_col = metadata['chart1_columns']['numeric_col']
                    chart = alt.Chart(df_copy).mark_line().encode(
                        x=alt.X(date_col, title=date_col),
                        y=alt.Y(numeric_col, title=numeric_col)
                    ).properties(title=report['REPORT_NAME'])
                    return chart
                elif 'chart3_columns' in metadata:
                    # Time series with categories
                    date_col = metadata['chart3_columns']['date_col']
                    text_col = metadata['chart3_columns']['text_col']
                    numeric_col = metadata['chart3_columns']['numeric_col']
                    chart = alt.Chart(df_copy).mark_bar().encode(
                        x=alt.X(date_col, title=date_col),
                        y=alt.Y(numeric_col, title=numeric_col, stack='zero'),
                        color=alt.Color(text_col, title=text_col)
                    ).properties(title=report['REPORT_NAME'])
                    return chart
                elif 'chart4_columns' in metadata:
                    # Stacked bar chart with text column selector for colors
                    date_col = metadata['chart4_columns']['date_col']
                    text_cols = metadata['chart4_columns']['text_cols']
                    numeric_col = metadata['chart4_columns']['numeric_col']
                    
                    if not text_cols:
                        st.error(f"Missing text columns for report: {report['REPORT_NAME']}")
                        return None
                    
                    # Generate a unique key for this chart
                    df_hash = hash(str(df_copy.shape) + str(df_copy.columns.tolist()) + str(report['REPORT_ID']))
                    widget_key = f"chart4_select_{df_hash}"
                    
                    # Initialize the session state value if it doesn't exist
                    if widget_key not in st.session_state:
                        st.session_state[widget_key] = text_cols[0]
                    # If the value exists but is not in text_cols (changed data), reset it
                    elif st.session_state[widget_key] not in text_cols:
                        st.session_state[widget_key] = text_cols[0]
                    
                    # Get the selected column from session state
                    selected_text_col = st.selectbox(
                        "Select column for color grouping:",
                        options=text_cols,
                        index=text_cols.index(st.session_state[widget_key]),
                        key=widget_key
                    )
                    
                    # Define a function to create the chart to ensure proper variable capture
                    def create_chart_with_selected_col(df, date_col, numeric_col, selected_col, title):
                        return alt.Chart(df).mark_bar().encode(
                            x=alt.X(date_col + ':T', sort='ascending'),
                            y=alt.Y(numeric_col + ':Q', stack='zero'),
                            color=alt.Color(selected_col + ':N', title=selected_col),
                            tooltip=[date_col, selected_col, numeric_col]
                        ).properties(title=title)
                    
                    # Create the chart with the selected column
                    chart = create_chart_with_selected_col(
                        df_copy, 
                        date_col, 
                        numeric_col, 
                        selected_text_col,
                        report['REPORT_NAME']
                    )
                    return chart
                elif 'chart8_columns' in metadata:
                    # Multi-dimensional bubble chart
                    num_col1 = metadata['chart8_columns']['num_col1']
                    num_col2 = metadata['chart8_columns']['num_col2']
                    num_col3 = metadata['chart8_columns']['num_col3']
                    text_col1 = metadata['chart8_columns']['text_col1']
                    text_col2 = metadata['chart8_columns']['text_col2']
                    
                    # Create the proper multi-dimensional bubble chart with separate encodings
                    chart = alt.Chart(df_copy).mark_point().encode(
                        x=alt.X(num_col1, title=num_col1),
                        y=alt.Y(num_col2, title=num_col2),
                        size=alt.Size(num_col3, title=num_col3),
                        color=alt.Color(text_col1, title=text_col1),
                        shape=alt.Shape(text_col2, title=text_col2, scale=alt.Scale(
                            range=["circle", "square", "cross", "diamond", "triangle-up", "triangle-down", 
                                   "triangle-right", "triangle-left", "arrow", "wedge", "stroke"]
                        )),
                        tooltip=[text_col1, text_col2, num_col1, num_col2, num_col3]
                    ).properties(title=report['REPORT_NAME'])
                    return chart
                elif 'chart9_columns' in metadata:
                    # Bar chart with text column selector
                    numeric_col = metadata['chart9_columns']['numeric_col']
                    text_cols = metadata['chart9_columns']['text_cols']
                    
                    if not text_cols:
                        st.error(f"Missing text columns for report: {report['REPORT_NAME']}")
                        return None
                    
                    # Generate a unique key for this chart
                    df_hash = hash(str(df_copy.shape) + str(df_copy.columns.tolist()) + str(report['REPORT_ID']))
                    widget_key = f"chart9_select_{df_hash}"
                    
                    # Initialize the session state value if it doesn't exist
                    if widget_key not in st.session_state:
                        st.session_state[widget_key] = text_cols[0]
                    # If the value exists but is not in text_cols (changed data), reset it
                    elif st.session_state[widget_key] not in text_cols:
                        st.session_state[widget_key] = text_cols[0]
                    
                    # Get the selected column from session state
                    selected_text_col = st.selectbox(
                        "Select column for X-axis:",
                        options=text_cols,
                        index=text_cols.index(st.session_state[widget_key]),
                        key=widget_key
                    )
                    
                    # Create the bar chart with the selected text column
                    chart = alt.Chart(df_copy).mark_bar().encode(
                        x=alt.X(f"{selected_text_col}:N", sort='-y'),
                        y=alt.Y(f"{numeric_col}:Q"),
                        tooltip=[selected_text_col, numeric_col]
                    ).properties(title=report['REPORT_NAME'])
                    
                    return chart
            
            # If no metadata or chart creation failed, show a simple table view
            st.error(f"Could not create chart for report: {report['REPORT_NAME']}")
            return None
        except Exception as e:
            st.error(f"Error creating default chart for {report['REPORT_NAME']}: {e}")
            return None
    except Exception as e:
        st.error(f"Unexpected error rendering chart for {report['REPORT_NAME']}: {e}")
        return None

# Helper function for Chart 4 fallback
def render_chart_4_fallback(df, cols, title):
    """Special fallback implementation for Chart 4 to handle templating issues"""
    date_col = cols.get('date_col')
    text_cols = cols.get('text_cols', [])
    numeric_col = cols.get('numeric_col')
    
    if not text_cols:
        # Find suitable text columns if not specified
        all_cols = list(df.columns)
        possible_text_cols = [col for col in all_cols if col != date_col and col != numeric_col]
        if possible_text_cols:
            text_cols = possible_text_cols
        else:
            # If no text columns available, return None
            st.error("No text columns available for Chart 4")
            return None
    
    # Generate a unique key for this chart based on dataframe and hash of title
    df_hash = hash(str(df.shape) + str(df.columns.tolist()) + title)
    widget_key = f"chart4_fallback_{df_hash}"
    
    # Initialize the session state value if it doesn't exist
    if widget_key not in st.session_state:
        st.session_state[widget_key] = text_cols[0]
    # If the value exists but is not in text_cols (changed data), reset it
    elif st.session_state[widget_key] not in text_cols:
        st.session_state[widget_key] = text_cols[0]
    
    # Get the selected column from session state
    selected_text_col = st.selectbox(
        "Select column for color grouping:",
        options=text_cols,
        index=text_cols.index(st.session_state[widget_key]),
        key=widget_key
    )
    
    # Create the chart with the selected text column
    return alt.Chart(df).mark_bar().encode(
        x=alt.X(date_col + ':T', sort='ascending'),
        y=alt.Y(numeric_col + ':Q', stack='zero'),
        color=alt.Color(selected_text_col + ':N', title=selected_text_col),
        tooltip=[date_col, selected_text_col, numeric_col]
    ).properties(title=title)

# Main function
def main():
    # Initialize session state
    init_session_state()
    
    # Add debug mode toggle in sidebar
    with st.sidebar:
        st.divider()
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
    
    # Conditionally display title based on selected dashboard
    if st.session_state.get("selected_dashboard"):
        st.title(f"Dashboard: {st.session_state.selected_dashboard['name']}")
    else:
        st.title("Dashboard")
    
    # Load dashboards and reports
    dashboards_df = load_dashboards()
    reports_df = load_reports()
    
    # Dashboard sidebar
    with st.sidebar:
        st.header("Dashboards")
        
        # Create new dashboard button
        if st.button("Create New Dashboard"):
            st.session_state.create_new = True
            st.session_state.selected_dashboard = None
            st.session_state.pinned_reports = []
            st.session_state.dashboard_name = ""
            st.rerun()
        
        # Display dashboards list if any exist
        if not dashboards_df.empty:
            st.subheader("Saved Dashboards")
            for idx, row in dashboards_df.iterrows():
                if st.button(row["DASHBOARD_NAME"], key=f"dashboard_{row['DASHBOARD_ID']}"):
                    st.session_state.selected_dashboard = {
                        "id": row["DASHBOARD_ID"],
                        "name": row["DASHBOARD_NAME"],
                        "reports": row["REPORTS"].split(",") if row["REPORTS"] and row["REPORTS"] != "" else []
                    }
                    st.session_state.pinned_reports = [int(r) for r in st.session_state.selected_dashboard["reports"] if r.strip()]
                    st.session_state.dashboard_name = row["DASHBOARD_NAME"]
                    st.session_state.create_new = False
                    # Clear the data cache when switching dashboards
                    st.session_state.report_data_cache = {}
                    # Force page rerun to update the title immediately
                    st.rerun()
        
        # Clear cache button
        if st.button("Refresh Data"):
            st.session_state.report_data_cache = {}
            st.success("Data cache cleared. Refreshing...")
            st.rerun()
    
    # Debug information
    if st.session_state.debug_mode:
        with st.expander("Debug Information", expanded=False):
            st.write("### Report Data Cache")
            st.write(f"Cache contains data for {len(st.session_state.report_data_cache)} reports")
            if st.session_state.report_data_cache:
                for report_id, cache_data in st.session_state.report_data_cache.items():
                    st.write(f"Report ID: {report_id}")
                    if 'df' in cache_data:
                        st.write(f"DataFrame shape: {cache_data['df'].shape}")
                    if 'chart_metadata' in cache_data and cache_data['chart_metadata']:
                        st.write(f"Chart metadata: {cache_data['chart_metadata']}")
            
            st.write("### Stored Metadata")
            if not reports_df.empty:
                for _, report in reports_df.iterrows():
                    if "CHART_METADATA" in report and report["CHART_METADATA"]:
                        st.write(f"Report {report['REPORT_NAME']} (ID: {report['REPORT_ID']}) has stored metadata:")
                        try:
                            metadata = json.loads(report["CHART_METADATA"])
                            st.json(metadata)
                        except:
                            st.write("Invalid JSON metadata")
                    else:
                        st.write(f"Report {report['REPORT_NAME']} (ID: {report['REPORT_ID']}) has no stored metadata")
    
    # Main content area
    if st.session_state.create_new:
        st.subheader("Create New Dashboard")
        st.session_state.dashboard_name = st.text_input("Dashboard Name", st.session_state.dashboard_name)
        
        # Show available reports with checkboxes
        if not reports_df.empty:
            st.subheader("Available Reports")
            
            # Create a dataframe with a Pinned column initialized to False for all reports
            report_table = pd.DataFrame({
                "Report Name": reports_df["REPORT_NAME"],
                "Description": reports_df["REPORT_DESCRIPTION"],
                "Pinned": [False] * len(reports_df)
            })
            
            # Display the table with checkboxes
            edited_df = st.data_editor(
                report_table,
                column_config={
                    "Report Name": st.column_config.TextColumn("Report Name"),
                    "Description": st.column_config.TextColumn("Description"),
                    "Pinned": st.column_config.CheckboxColumn(
                        "Add to Dashboard",
                        help="Select to add this report to your dashboard",
                        default=False
                    )
                },
                hide_index=True,
                key="report_editor"
            )
            
            # Update pinned reports based on selection
            st.session_state.pinned_reports = [
                reports_df.iloc[i]["REPORT_ID"] 
                for i in range(len(edited_df)) 
                if edited_df.iloc[i]["Pinned"]
            ]
        
        # Save dashboard button
        if st.button("Save Dashboard"):
            if st.session_state.dashboard_name and st.session_state.pinned_reports:
                if save_dashboard(st.session_state.dashboard_name, st.session_state.pinned_reports):
                    st.success(f"Dashboard '{st.session_state.dashboard_name}' saved successfully!")
                    # Refresh dashboards
                    dashboards_df = load_dashboards()
                    
                    # Find the newly created dashboard to get its ID
                    new_dashboard = dashboards_df[dashboards_df["DASHBOARD_NAME"] == st.session_state.dashboard_name].iloc[0]
                    
                    # Update session state to select the new dashboard
                    st.session_state.selected_dashboard = {
                        "id": new_dashboard["DASHBOARD_ID"],
                        "name": new_dashboard["DASHBOARD_NAME"],
                        "reports": [str(r) for r in st.session_state.pinned_reports]
                    }
                    st.session_state.create_new = False
                    
                    # Refresh the page to show the dashboard
                    st.rerun()
            else:
                st.warning("Please provide a dashboard name and select at least one report.")
    
    elif st.session_state.selected_dashboard:
        # Display pinned reports in a grid layout
        if st.session_state.pinned_reports:
            # Filter reports to only show pinned ones
            pinned_reports = reports_df[reports_df["REPORT_ID"].isin(st.session_state.pinned_reports)]
            
            if len(pinned_reports) > 0:
                # Calculate number of rows needed (2 columns layout)
                num_reports = len(pinned_reports)
                num_rows = (num_reports + 1) // 2  # Ceiling division to get rows needed
                
                # Create reports in a grid with consistent heights
                for row in range(num_rows):
                    # Create a row with two columns
                    row_cols = st.columns(2)
                    
                    # Process up to 2 reports per row
                    for col in range(2):
                        report_idx = row * 2 + col
                        
                        # Check if we still have reports to display
                        if report_idx < num_reports:
                            # Get the report
                            report = pinned_reports.iloc[report_idx]
                            
                            # Create a container with consistent height for this chart
                            with row_cols[col]:
                                # Create a container with a minimum height
                                report_container = st.container()
                                
                                with report_container:
                                    # Display report header
                                    st.subheader(report["REPORT_NAME"])
                                    st.write(report["REPORT_DESCRIPTION"])
                                    
                                    # Create a fixed height container for the chart
                                    chart_container = st.container()
                                    with chart_container:
                                        # Generate the chart
                                        chart = render_chart(report)
                                        if chart:
                                            st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No reports found with the selected IDs.")
        else:
            st.info("No reports are pinned to this dashboard. Please select reports below.")
        
        # Show available reports with checkboxes
        if not reports_df.empty:
            st.subheader("Available Reports")
            
            # Create a dataframe for the interactive table
            report_table = pd.DataFrame({
                "Report Name": reports_df["REPORT_NAME"],
                "Description": reports_df["REPORT_DESCRIPTION"],
                "Pinned": [report_id in st.session_state.pinned_reports for report_id in reports_df["REPORT_ID"]]
            })
            
            # Show editable table
            edited_df = st.data_editor(
                report_table,
                column_config={
                    "Report Name": st.column_config.TextColumn("Report Name"),
                    "Description": st.column_config.TextColumn("Description"),
                    "Pinned": st.column_config.CheckboxColumn(
                        "Add to Dashboard",
                        help="Select to add this report to your dashboard"
                    )
                },
                hide_index=True,
                key="report_selector"
            )
            
            # Update pinned reports based on selection
            new_pinned = [
                reports_df.iloc[i]["REPORT_ID"] 
                for i in range(len(edited_df)) 
                if edited_df.iloc[i]["Pinned"]
            ]
            
            # Update session state if changed
            if set(new_pinned) != set(st.session_state.pinned_reports):
                st.session_state.pinned_reports = new_pinned
                st.rerun()
        
        # Save dashboard button
        if st.button("Save Dashboard"):
            if save_dashboard(st.session_state.dashboard_name, st.session_state.pinned_reports):
                st.success(f"Dashboard '{st.session_state.dashboard_name}' updated successfully!")
                # Refresh dashboards
                dashboards_df = load_dashboards()
    
    else:
        st.info("Select a dashboard from the sidebar or create a new one.")

if __name__ == "__main__":
    main() 