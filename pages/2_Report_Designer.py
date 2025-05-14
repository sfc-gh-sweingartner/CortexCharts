"""
Report Designer App
====================
This app allows users to create and customize reports from their Snowflake data.
"""
import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session
from datetime import datetime
import json
import time
import sys
import os

# Add path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.chart_utils import create_chart_from_metadata, generate_chart_code_for_dataframe

# Set page config
st.set_page_config(
    page_title="Report Designer",
    page_icon="📊",
    layout="wide",
)

# Initialize session
try:
    session = get_active_session()
except:
    st.error("Failed to connect to Snowflake. Please make sure you have an active session.")
    st.stop()

def init_session_state():
    """Initialize session state variables if they don't exist."""
    if "report_data" not in st.session_state:
        st.session_state.report_data = None
    if "report_name" not in st.session_state:
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.report_name = f"Report_{current_time}"
    if "report_description" not in st.session_state:
        st.session_state.report_description = ""
    if "sql_statement" not in st.session_state:
        st.session_state.sql_statement = ""
    if "chart_code" not in st.session_state:
        st.session_state.chart_code = """import altair as alt
import pandas as pd
import streamlit as st

# Chart code
def create_chart(df):
    # Get column names from metadata if available
    if hasattr(df, 'attrs') and 'chart_metadata' in df.attrs and 'chart4_columns' in df.attrs['chart_metadata']:
        cols = df.attrs['chart_metadata']['chart4_columns']
        date_col = cols.get('date_col', 'BIRTH_YEAR')
        text_cols = cols.get('text_cols', [])
        numeric_col = cols.get('numeric_col', 'TOTAL_HEALTHCARE_EXPENSES')
    else:
        # Fallback to column detection
        date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        text_cols = [col for col in df.columns if col not in numeric_cols and col not in date_cols]
        date_col = date_cols[0] if date_cols else df.columns[0]
        numeric_col = numeric_cols[0] if numeric_cols else df.columns[-1]
        
        # Use text columns that are not the date column
        text_cols = [col for col in text_cols if col != date_col]
        if not text_cols:
            # If no text columns, look for any other column that's not the date or numeric
            text_cols = [col for col in df.columns if col != date_col and col != numeric_col][:2]

    # Generate a unique key for this chart
    df_hash = hash(str(df.shape) + str(df.columns.tolist()))
    widget_key = f"chart4_select_{df_hash}"
    
    # Initialize the session state value if it doesn't exist
    if widget_key not in st.session_state and text_cols:
        st.session_state[widget_key] = text_cols[0]
    # If the value exists but is not in text_cols (changed data), reset it
    elif widget_key in st.session_state and text_cols and st.session_state[widget_key] not in text_cols:
        st.session_state[widget_key] = text_cols[0]
    
    # Ensure we have text columns to select from
    if not text_cols:
        st.error("No text columns available for color grouping")
        return None
    
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
    ).properties(title='Stacked Bar Chart with Selectable Colors')"""
    if "use_custom_chart_code" not in st.session_state:
        st.session_state.use_custom_chart_code = False
    if "chart_metadata" not in st.session_state:
        st.session_state.chart_metadata = None
    if "column_types" not in st.session_state:
        st.session_state.column_types = {
            'numeric_cols': [],
            'date_cols': [],
            'text_cols': []
        }

def get_report_from_transfer():
    """Check if there's data transferred from Cortex Analyst and load it."""
    if "report_transfer" in st.session_state and st.session_state.report_transfer:
        # Set the report name with timestamp
        current_time = st.session_state.report_transfer.get("timestamp", datetime.now().strftime("%Y%m%d%H%M%S"))
        st.session_state.report_name = f"Report_{current_time}"
        
        # Set the report description from the prompt
        st.session_state.report_description = st.session_state.report_transfer.get("prompt", "")
        
        # Set the SQL statement
        st.session_state.sql_statement = st.session_state.report_transfer.get("sql", "")
        
        # Set the chart code
        st.session_state.chart_code = st.session_state.report_transfer.get("chart_code", "")
        
        # Set the report data
        st.session_state.report_data = st.session_state.report_transfer.get("df", None)
        
        # Store chart metadata separately if available
        if hasattr(st.session_state.report_data, 'attrs') and 'chart_metadata' in st.session_state.report_data.attrs:
            st.session_state.chart_metadata = st.session_state.report_data.attrs['chart_metadata']
            # Update the chart code to match the metadata - this ensures UI is showing the right code
            update_chart_code_from_metadata()
        
        # Reset the custom chart code flag
        st.session_state.use_custom_chart_code = False
        
        # Clear the transfer data to avoid reloading on page refresh
        st.session_state.report_transfer = {}
        
        st.success("Data loaded from Cortex Analyst!")
        time.sleep(1)
        st.rerun()

def execute_sql_query(sql_statement):
    """Execute a SQL query and return the results as a pandas DataFrame."""
    try:
        if not sql_statement.strip():
            st.warning("Please enter a SQL query.")
            return None
        
        df = session.sql(sql_statement).to_pandas()
        if df.empty:
            st.warning("Query returned no data.")
            return None
        
        # Improve date column detection and conversion
        # Look for potential date columns
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
        # This can help when custom chart code needs to know about column types
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
        
        # Also store this information in session state
        st.session_state.column_types = {
            'numeric_cols': numeric_cols,
            'date_cols': date_cols,
            'text_cols': text_cols
        }
            
        return df
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return None

def evaluate_chart_code(chart_code, df):
    """Evaluate the chart code string and create an Altair chart."""
    try:
        # Ensure we're working with a copy of the dataframe to avoid modifying the original
        df_copy = df.copy()
        
        # Make sure df_copy has the chart_metadata if it exists in the original
        if hasattr(df, 'attrs') and 'chart_metadata' in df.attrs:
            if not hasattr(df_copy, 'attrs'):
                df_copy.attrs = {}
            df_copy.attrs['chart_metadata'] = df.attrs['chart_metadata']
            
        # Use metadata-based chart if not using custom code
        if not st.session_state.use_custom_chart_code and hasattr(df, 'attrs') and 'chart_metadata' in df.attrs:
            chart = create_chart_from_metadata(df)
            
            # Special handling for KPI tiles
            if isinstance(chart, dict) and chart.get("type") == "kpi_tiles":
                # For KPI tiles, we need to render them explicitly
                from utils.chart_utils import _render_kpi_tiles
                st.subheader("KPI Tiles")
                _render_kpi_tiles(chart["data"])
                return None, None  # Return None to avoid duplicate rendering
            
            if chart:
                return chart, None
        
        # Use provided chart code
        try:
            # Create a namespace for the chart code
            namespace = {"pd": pd, "alt": alt, "df": df_copy, "st": st}
            
            # Execute the chart code
            exec(chart_code, namespace)
            
            # Get the create_chart function from the namespace
            if "create_chart" in namespace:
                chart_function = namespace["create_chart"]
                chart = chart_function(df_copy)
                
                # Special handling for KPI tiles
                if isinstance(chart, dict) and chart.get("type") == "kpi_tiles":
                    # For KPI tiles, we need to render them explicitly
                    from utils.chart_utils import _render_kpi_tiles
                    st.subheader("KPI Tiles")
                    _render_kpi_tiles(chart["data"])
                    return None, None  # Return None to avoid duplicate rendering
                
                return chart, None
            else:
                error_msg = "Chart code must define a 'create_chart(df)' function."
                return None, error_msg
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            return None, f"Error creating chart from code: {str(e)}\n\n{error_trace}"
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return None, f"Error in evaluate_chart_code: {str(e)}\n\n{error_trace}"

def save_report_to_snowflake():
    """Save the report details to Snowflake."""
    try:
        # Get chart metadata if available
        chart_metadata_json = None
        if st.session_state.chart_metadata is not None:
            chart_metadata_json = json.dumps(st.session_state.chart_metadata)
        
        # Create parameters for the SQL query
        params = {
            "report_name": st.session_state.report_name,
            "report_description": st.session_state.report_description,
            "sql_statement": st.session_state.sql_statement,
            "chart_code": st.session_state.chart_code,
            "chart_metadata": chart_metadata_json
        }
        
        # Execute SQL to insert/update the report
        sql = """
        INSERT INTO CORTEX_ANALYST_REPORTS (REPORT_NAME, REPORT_DESCRIPTION, SQL_STATEMENT, CHART_CODE, CHART_METADATA)
        VALUES (?, ?, ?, ?, ?)
        """
        
        session.sql(sql, params=list(params.values())).collect()
        return True
    except Exception as e:
        st.error(f"Error saving report: {str(e)}")
        return False

def update_chart_code_from_metadata():
    """Generate chart code based on chart metadata in session state."""
    if not st.session_state.chart_metadata:
        return
    
    # Only update if not using custom code
    if st.session_state.use_custom_chart_code:
        return
    
    # Use the centralized chart code generation function
    from utils.chart_utils import generate_chart_code_for_dataframe
    
    # Create a temporary dataframe with the chart metadata
    temp_df = pd.DataFrame()
    temp_df.attrs['chart_metadata'] = st.session_state.chart_metadata
    
    # Generate the chart code
    st.session_state.chart_code = generate_chart_code_for_dataframe(temp_df)

# Main function
def main():
    st.title("Report Designer")
    st.markdown("Design and customize reports from your Snowflake data.")
    
    # Initialize session state variables
    init_session_state()
    
    # Check for data transferred from Cortex Analyst
    get_report_from_transfer()
    
    # Add debug mode in sidebar
    with st.sidebar:
        st.divider()
        debug_mode = st.checkbox("Debug Mode", value=False)
    
    # Create the main content layout
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Report name input
        st.text_input("Report Name", key="report_name")
        
        # Save button
        if st.button("Save Report", use_container_width=True):
            if save_report_to_snowflake():
                st.success("Report saved successfully!")
            else:
                st.error("Failed to save report.")
    
    # Report description (prompt)
    st.text_area("Report Description", key="report_description", height=100)
    
    # SQL editor tab and chart code editor tab
    tab1, tab2 = st.tabs(["SQL Query", "Chart Code"])
    
    with tab1:
        # SQL editor
        st.text_area("SQL Statement", key="sql_statement", height=200)
        
        # Run button
        if st.button("Run SQL", use_container_width=True):
            df = execute_sql_query(st.session_state.sql_statement)
            if df is not None:
                st.session_state.report_data = df
                st.success(f"Query executed successfully! {len(df)} rows returned.")
    
    with tab2:
        # Chart code editor
        st.text_area("Chart Code", key="chart_code", height=200)
        
        # Update chart button
        update_chart = st.button("Update Chart", use_container_width=True)
        if update_chart:
            st.session_state.use_custom_chart_code = True
            st.success("Chart updated with new code!")
            st.rerun()
    
    # Display debug information if enabled
    if debug_mode and st.session_state.report_data is not None:
        with st.expander("Debug Information", expanded=True):
            st.write("### Chart Metadata")
            st.write(st.session_state.chart_metadata)
            
            st.write("### Column Types")
            if hasattr(st.session_state.report_data, 'attrs') and 'column_types' in st.session_state.report_data.attrs:
                st.write(st.session_state.report_data.attrs['column_types'])
            elif 'column_types' in st.session_state:
                st.write(st.session_state.column_types)
            else:
                st.write("No column type information available")
            
            st.write("### Custom Chart Code Flag")
            st.write(f"Using custom chart code: {st.session_state.use_custom_chart_code}")
    
    # Display results
    if st.session_state.report_data is not None:
        # Show data preview
        st.subheader("Data Preview")
        st.dataframe(st.session_state.report_data.head(10), use_container_width=True)
        
        # Show chart
        st.subheader("Chart Preview")
        
        # Ensure we have a copy of the dataframe to work with
        df_for_chart = st.session_state.report_data.copy()
        
        # Apply stored metadata to the dataframe if available
        if st.session_state.chart_metadata is not None:
            if not hasattr(df_for_chart, 'attrs'):
                df_for_chart.attrs = {}
            df_for_chart.attrs['chart_metadata'] = st.session_state.chart_metadata
        
        # Evaluate the chart code
        chart, error = evaluate_chart_code(st.session_state.chart_code, df_for_chart)
        
        if chart:
            st.altair_chart(chart, use_container_width=True)
        elif error:
            st.error("Chart creation failed")
            with st.expander("View Error Details", expanded=True):
                st.code(error)
    else:
        # Show placeholder when no data is loaded
        st.info("Run a SQL query or import data from Cortex Analyst to get started.")

if __name__ == "__main__":
    main()
