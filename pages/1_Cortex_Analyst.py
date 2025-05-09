"""
Cortex Analyst App
====================
This app allows users to interact with their data using natural language.
"""
import json  # To handle JSON data
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import _snowflake  # For interacting with Snowflake-specific APIs
import pandas as pd
import streamlit as st  # Streamlit library for building the web app
import altair as alt  # For creating interactive charts
from snowflake.snowpark.context import (
    get_active_session,
)  # To interact with Snowflake sessions
from snowflake.snowpark.exceptions import SnowparkSQLException
import sys
import os

# Add path for utils module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.chart_utils import (
    create_chart1, create_chart2, create_chart3, create_chart4,
    create_chart5, create_chart6, create_chart7, create_chart8, create_chart9
)

# Set page config
st.set_page_config(
    page_title="Cortex Analyst",
    page_icon="❄️",
    layout="wide",
)

# List of available semantic model paths in the format: <DATABASE>.<SCHEMA>.<STAGE>/<FILE-NAME>
# Each path points to a YAML file defining a semantic model
AVAILABLE_SEMANTIC_MODELS_PATHS = [
    "SYNTHEA.SYNTHEA.SYNTHEA/synthea_joins_03.yaml",
    "TELCO_NETWORK_OPTIMIZATION_PROD.RAW.DATA/telco_network_opt.yaml"
]
API_ENDPOINT = "/api/v2/cortex/analyst/message"
FEEDBACK_API_ENDPOINT = "/api/v2/cortex/analyst/feedback"
API_TIMEOUT = 50000  # in milliseconds

# Initialize a Snowpark session for executing queries
session = get_active_session()


def main():
    # Initialize session state
    if "messages" not in st.session_state:
        reset_session_state()
    show_header_and_sidebar()
    display_conversation()
    handle_user_inputs()
    handle_error_notifications()
    # display_warnings()  # Commented out to hide warnings from users


def reset_session_state():
    """Reset important session state elements."""
    st.session_state.messages = []  # List to store conversation messages
    st.session_state.active_suggestion = None  # Currently selected suggestion
    st.session_state.warnings = []  # List to store warnings
    st.session_state.form_submitted = (
        {}
    )  # Dictionary to store feedback submission for each request
    st.session_state.sql_execution_mode = "Run"  # Default SQL execution mode


def show_header_and_sidebar():
    """Display the header and sidebar of the app."""
    # Set the title and introductory text of the app
    st.title("Cortex Analyst")
    st.markdown(
        "Welcome to Cortex Analyst! Type your questions below to interact with your data. "
    )

    # Sidebar with a reset button
    with st.sidebar:
        st.selectbox(
            "Selected semantic model:",
            AVAILABLE_SEMANTIC_MODELS_PATHS,
            format_func=lambda s: s.split("/")[-1],
            key="selected_semantic_model_path",
            on_change=reset_session_state,
        )
        st.divider()
        # Center this button
        _, btn_container, _ = st.columns([2, 6, 2])
        if btn_container.button("Clear Chat History", use_container_width=True):
            reset_session_state()
            
        # Add SQL execution mode toggle
        st.radio(
            "SQL Execution Mode:",
            options=["Run", "View"],
            index=0,
            key="sql_execution_mode",
            horizontal=True,
        )


def handle_user_inputs():
    """Handle user inputs from the chat interface."""
    # Handle chat input
    user_input = st.chat_input("What is your question?")
    if user_input:
        process_user_input(user_input)
    # Handle suggested question click
    elif st.session_state.active_suggestion is not None:
        suggestion = st.session_state.active_suggestion
        st.session_state.active_suggestion = None
        process_user_input(suggestion)


def handle_error_notifications():
    if st.session_state.get("fire_API_error_notify"):
        st.toast("An API error has occured!", icon="🚨")
        st.session_state["fire_API_error_notify"] = False


def process_user_input(prompt: str):
    """
    Process user input and update the conversation history.

    Args:
        prompt (str): The user's input.
    """
    # Clear previous warnings at the start of a new request
    st.session_state.warnings = []

    # Create a new message, append to history and display imidiately
    new_user_message = {
        "role": "user",
        "content": [{"type": "text", "text": prompt}],
    }
    st.session_state.messages.append(new_user_message)
    with st.chat_message("user"):
        user_msg_index = len(st.session_state.messages) - 1
        display_message(new_user_message["content"], user_msg_index)

    # Show progress indicator inside analyst chat message while waiting for response
    with st.chat_message("analyst"):
        with st.spinner("Waiting for Analyst's response..."):
            time.sleep(1)
            response, error_msg = get_analyst_response(st.session_state.messages)
            if error_msg is None:
                analyst_message = {
                    "role": "analyst",
                    "content": response["message"]["content"],
                    "request_id": response["request_id"],
                }
            else:
                analyst_message = {
                    "role": "analyst",
                    "content": [{"type": "text", "text": error_msg}],
                    "request_id": response["request_id"],
                }
                st.session_state["fire_API_error_notify"] = True

            # if "warnings" in response:
            #     st.session_state.warnings = response["warnings"]

            st.session_state.messages.append(analyst_message)
            st.rerun()


def display_warnings():
    """
    Display warnings to the user.
    """
    # warnings = st.session_state.warnings
    # for warning in warnings:
    #     st.warning(warning["message"], icon="⚠️")


def get_analyst_response(messages: List[Dict]) -> Tuple[Dict, Optional[str]]:
    """
    Send chat history to the Cortex Analyst API and return the response.

    Args:
        messages (List[Dict]): The conversation history.

    Returns:
        Optional[Dict]: The response from the Cortex Analyst API.
    """
    # Prepare the request body with the user's prompt
    request_body = {
        "messages": messages,
        "semantic_model_file": f"@{st.session_state.selected_semantic_model_path}",
    }

    # Send a POST request to the Cortex Analyst API endpoint
    # Adjusted to use positional arguments as per the API's requirement
    resp = _snowflake.send_snow_api_request(
        "POST",  # method
        API_ENDPOINT,  # path
        {},  # headers
        {},  # params
        request_body,  # body
        None,  # request_guid
        API_TIMEOUT,  # timeout in milliseconds
    )

    # Content is a string with serialized JSON object
    parsed_content = json.loads(resp["content"])

    # Check if the response is successful
    if resp["status"] < 400:
        # Return the content of the response as a JSON object
        return parsed_content, None
    else:
        # Craft readable error message
        error_msg = f"""
🚨 An Analyst API error has occurred 🚨

* response code: `{resp['status']}`
* request-id: `{parsed_content['request_id']}`
* error code: `{parsed_content['error_code']}`

Message:
```
{parsed_content['message']}
```
        """
        return parsed_content, error_msg


def display_conversation():
    """
    Display the conversation history between the user and the assistant.
    """
    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message["content"]
        with st.chat_message(role):
            if role == "analyst":
                display_message(content, idx, message["request_id"])
            else:
                display_message(content, idx)


def display_message(
    content: List[Dict[str, Union[str, Dict]]],
    message_index: int,
    request_id: Union[str, None] = None,
):
    """
    Display a single message content.

    Args:
        content (List[Dict[str, str]]): The message content.
        message_index (int): The index of the message.
    """
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        elif item["type"] == "suggestions":
            # Display suggestions as buttons
            for suggestion_index, suggestion in enumerate(item["suggestions"]):
                if st.button(
                    suggestion, key=f"suggestion_{message_index}_{suggestion_index}"
                ):
                    st.session_state.active_suggestion = suggestion
        elif item["type"] == "sql":
            # Display the SQL query and results
            display_sql_query(
                item["statement"], message_index, item["confidence"], request_id
            )
        else:
            # Handle other content types if necessary
            pass


@st.cache_data(show_spinner=False)
def get_query_exec_result(query: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Execute the SQL query and convert the results to a pandas DataFrame.

    Args:
        query (str): The SQL query.

    Returns:
        Tuple[Optional[pd.DataFrame], Optional[str]]: The query results and the error message.
    """
    global session
    try:
        df = session.sql(query).to_pandas()
        return df, None
    except SnowparkSQLException as e:
        return None, str(e)


def display_sql_confidence(confidence: dict):
    if confidence is None:
        return
    verified_query_used = confidence["verified_query_used"]
    with st.popover(
        "Verified Query Used",
        help="The verified query from [Verified Query Repository](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/verified-query-repository), used to generate the SQL",
    ):
        with st.container():
            if verified_query_used is None:
                st.text(
                    "There is no query from the Verified Query Repository used to generate this SQL answer"
                )
                return
            st.text(f"Name: {verified_query_used['name']}")
            st.text(f"Question: {verified_query_used['question']}")
            st.text(f"Verified by: {verified_query_used['verified_by']}")
            st.text(
                f"Verified at: {datetime.fromtimestamp(verified_query_used['verified_at'])}"
            )
            st.text("SQL query:")
            st.code(verified_query_used["sql"], language="sql", wrap_lines=True)


def display_sql_query(
    sql: str, message_index: int, confidence: dict, request_id: Union[str, None] = None
):
    """
    Executes the SQL query and displays the results in form of data frame and charts.

    Args:
        sql (str): The SQL query.
        message_index (int): The index of the message.
        confidence (dict): The confidence information of SQL query generation
        request_id (str): Request id from user request
    """

    # Display the SQL query
    with st.expander("SQL Query", expanded=False):
        st.code(sql, language="sql")
        display_sql_confidence(confidence)

    # Check if we should execute the SQL or just display it
    if st.session_state.sql_execution_mode == "Run":
        # Display the results of the SQL query
        with st.expander("Results", expanded=True):
            with st.spinner("Running SQL..."):
                df, err_msg = get_query_exec_result(sql)
                if df is None:
                    st.error(f"Could not execute generated SQL query. Error: {err_msg}")
                elif df.empty:
                    st.write("Query returned no data")
                else:
                    st.dataframe(df, use_container_width=True)
                    display_chart(df, message_index)
    else:
        # Display a message indicating SQL execution is disabled
        with st.expander("Results", expanded=True):
            st.info("SQL execution is disabled. Switch to 'Run' mode to execute queries.")
            
    if request_id:
        display_feedback_section(request_id)


def display_chart(df: pd.DataFrame, message_index: int) -> None:
    """
    Display the charts using Altair charts based on data structure.

    Args:
        df (pd.DataFrame): The query results.
        message_index (int): The index of the message.
    """
    # Limit to the top 5000 rows for visualization
    df_display = df.head(5000)
    
    # Create an Altair chart based on DataFrame content using predefined rules
    try:
        # Identify column types
        numeric_cols = [col for col in df_display.columns if pd.api.types.is_numeric_dtype(df_display[col])]
        
        # Improved date detection - first look for datetime types, then try to detect string date columns
        date_cols = [col for col in df_display.columns if pd.api.types.is_datetime64_any_dtype(df_display[col])]
        
        # Check for month/date columns that might be in various formats
        if not date_cols:
            # List all columns that could potentially be date columns
            potential_date_cols = []
            
            # First check columns with date-related names
            date_related_terms = ['date', 'month', 'year', 'day', 'time', 'dt', 'period']
            for col in df_display.columns:
                col_lower = col.lower()
                if any(term in col_lower for term in date_related_terms):
                    potential_date_cols.append(col)
            
            # Then check other string and object columns
            other_cols = [col for col in df_display.columns if col not in potential_date_cols 
                         and (pd.api.types.is_string_dtype(df_display[col]) or pd.api.types.is_object_dtype(df_display[col]))]
            potential_date_cols.extend(other_cols)
            
            # Try to convert potential date columns
            for col in potential_date_cols:
                try:
                    # Try to convert to datetime
                    temp_series = pd.to_datetime(df_display[col], errors='coerce')
                    # If at least 90% of non-null values converted successfully, consider it a date column
                    non_null_count = df_display[col].count()
                    if non_null_count > 0:
                        success_rate = temp_series.count() / non_null_count
                        if success_rate >= 0.9:
                            df_display[col] = temp_series
                            date_cols.append(col)
                            break  # Stop after finding one good date column
                except Exception as e:
                    continue
        
        # Recalculate text columns after date detection
        text_cols = [col for col in df_display.columns if col not in numeric_cols and col not in date_cols and 
                    (pd.api.types.is_string_dtype(df_display[col]) or pd.api.types.is_object_dtype(df_display[col]))]

        # Rule 1: Dates: 1 Dimensions: 0  Numeric Metrics: 1
        if len(date_cols) == 1 and len(text_cols) == 0 and len(numeric_cols) == 1:
            chart_metadata = {
                'chart1_columns': {
                    'date_col': date_cols[0],
                    'numeric_col': numeric_cols[0]
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            # Use chart_utils function
            alt_chart = create_chart1(df_display, chart_metadata['chart1_columns'])

        # Rule 2: Dates: 1 Dimensions: 0  Numeric Metrics: 2
        elif len(date_cols) == 1 and len(text_cols) == 0 and len(numeric_cols) == 2:
            chart_metadata = {
                'chart2_columns': {
                    'date_col': date_cols[0],
                    'num_col1': numeric_cols[0],
                    'num_col2': numeric_cols[1]
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            # Use chart_utils function
            alt_chart = create_chart2(df_display, chart_metadata['chart2_columns'])

        # Rule 3: Dates: 1 Dimensions: 1  Numeric Metrics: 1
        elif len(date_cols) == 1 and len(text_cols) == 1 and len(numeric_cols) == 1:
            chart_metadata = {
                'chart3_columns': {
                    'date_col': date_cols[0],
                    'text_col': text_cols[0],
                    'numeric_col': numeric_cols[0]
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            # Use chart_utils function
            alt_chart = create_chart3(df_display, chart_metadata['chart3_columns'])

        # Rule 4: Dates: 1 Dimensions: 2+  Numeric Metrics: 1
        elif len(date_cols) == 1 and len(text_cols) >= 2 and len(numeric_cols) == 1:
            # Get available text columns
            available_text_cols = [col for col in text_cols if col not in date_cols]
            
            chart_metadata = {
                'chart4_columns': {
                    'date_col': date_cols[0],
                    'text_cols': available_text_cols,
                    'numeric_col': numeric_cols[0]
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            # Use chart_utils function
            alt_chart = create_chart4(df_display, chart_metadata['chart4_columns'])

        # Rule 5: Dates: 0 Dimensions: 1  Numeric Metrics: 2
        elif len(date_cols) == 0 and len(text_cols) == 1 and len(numeric_cols) == 2:
            chart_metadata = {
                'chart5_columns': {
                    'num_col1': numeric_cols[0],
                    'num_col2': numeric_cols[1],
                    'text_col': text_cols[0]
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            # Use chart_utils function
            alt_chart = create_chart5(df_display, chart_metadata['chart5_columns'])

        # Rule 6: Dates: 0 Dimensions: 2  Numeric Metrics: 2
        elif len(date_cols) == 0 and len(text_cols) == 2 and len(numeric_cols) == 2:
            chart_metadata = {
                'chart6_columns': {
                    'num_col1': numeric_cols[0],
                    'num_col2': numeric_cols[1],
                    'text_col1': text_cols[0],
                    'text_col2': text_cols[1]
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            # Use chart_utils function
            alt_chart = create_chart6(df_display, chart_metadata['chart6_columns'])

        # Rule 7: Dates: 0 Dimensions: 1  Numeric Metrics: 3
        elif len(date_cols) == 0 and len(text_cols) == 1 and len(numeric_cols) == 3:
            chart_metadata = {
                'chart7_columns': {
                    'num_col1': numeric_cols[0],
                    'num_col2': numeric_cols[1],
                    'num_col3': numeric_cols[2],
                    'text_col': text_cols[0]
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            # Use chart_utils function
            alt_chart = create_chart7(df_display, chart_metadata['chart7_columns'])
            
        # Rule 8: Dates: 0 Dimensions: 2+ Numeric Metrics: 3+ Categorical Metrics: 2+
        elif len(date_cols) == 0 and len(numeric_cols) >= 3 and len(text_cols) >= 2:
            chart_metadata = {
                'chart8_columns': {
                    'num_col1': numeric_cols[0],
                    'num_col2': numeric_cols[1],
                    'num_col3': numeric_cols[2],
                    'text_col1': text_cols[0],
                    'text_col2': text_cols[1]
                }
            }
            df_display.attrs['chart_metadata'] = chart_metadata
            # Use chart_utils function
            alt_chart = create_chart8(df_display, chart_metadata['chart8_columns'])

        # Rule 9: Dates: 0 Dimensions: Any amount  Numeric Metrics: 1
        elif len(date_cols) == 0 and len(numeric_cols) == 1:
            non_numeric_cols = [col for col in df_display.columns if col not in numeric_cols]
            
            if non_numeric_cols:
                chart_metadata = {
                    'chart9_columns': {
                        'numeric_col': numeric_cols[0],
                        'text_cols': non_numeric_cols[:5],  # Store up to 5 text columns
                        'is_stacked': len(non_numeric_cols) >= 2  # Stack if multiple text columns
                    }
                }
                df_display.attrs['chart_metadata'] = chart_metadata
                # Use chart_utils function
                alt_chart = create_chart9(df_display, chart_metadata['chart9_columns'])
            else:
                alt_chart = None
        else:
            alt_chart = None

        if alt_chart:
            st.altair_chart(alt_chart, use_container_width=True)
            
            # Add "Open in Designer" button
            if st.button("Open in Designer", key=f"send_to_designer_{message_index}"):
                # Store data in session state to be accessed by Report Designer
                if "report_transfer" not in st.session_state:
                    st.session_state.report_transfer = {}
                
                # Extract the SQL statement from the message
                sql_statement = ""
                prompt = ""
                for message in st.session_state.messages:
                    if message["role"] == "analyst" and len(st.session_state.messages) - 1 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "sql":
                                sql_statement = item["statement"]
                    elif message["role"] == "user" and len(st.session_state.messages) - 2 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "text":
                                prompt = item["text"]
                
                # Extract interpretation from the assistant's message if possible
                interpretation = None
                for message in st.session_state.messages:
                    if message["role"] == "analyst" and len(st.session_state.messages) - 1 == st.session_state.messages.index(message):
                        for item in message["content"]:
                            if item["type"] == "text":
                                text = item["text"]
                                # Look for the interpretation pattern
                                if "This is our interpretation of your question:" in text:
                                    interpretation_parts = text.split("This is our interpretation of your question:")
                                    if len(interpretation_parts) > 1:
                                        interpretation = interpretation_parts[1].strip()
                                        # Remove quotes if present
                                        if interpretation.startswith('"') and interpretation.endswith('"'):
                                            interpretation = interpretation[1:-1].strip()
                
                # Use interpretation if found, otherwise use original prompt
                description = interpretation if interpretation else prompt
                
                # Generate chart code based on chart type by using a wrapper function
                from utils.chart_utils import generate_chart_code_for_dataframe
                chart_code = generate_chart_code_for_dataframe(df_display)
                
                # Store data to be accessed by the Report Designer
                st.session_state.report_transfer = {
                    "df": df_display,
                    "sql": sql_statement,
                    "prompt": description,
                    "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "redirect": True,
                    "chart_metadata": df_display.attrs.get('chart_metadata', {}),
                    "chart_code": chart_code  # Add the generated chart code
                }
                
                # Use Streamlit's native navigation to redirect to Report Designer
                st.switch_page("pages/2_Report_Designer.py")
        else:
            st.markdown("No appropriate chart found for this data.")
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def display_feedback_section(request_id: str):
    with st.popover("📝 Query Feedback"):
        if request_id not in st.session_state.form_submitted:
            with st.form(f"feedback_form_{request_id}", clear_on_submit=True):
                positive = st.radio(
                    "Rate the generated SQL", options=["👍", "👎"], horizontal=True
                )
                positive = positive == "👍"
                submit_disabled = (
                    request_id in st.session_state.form_submitted
                    and st.session_state.form_submitted[request_id]
                )

                feedback_message = st.text_input("Optional feedback message")
                submitted = st.form_submit_button("Submit", disabled=submit_disabled)
                if submitted:
                    err_msg = submit_feedback(request_id, positive, feedback_message)
                    st.session_state.form_submitted[request_id] = {"error": err_msg}
                    st.session_state.popover_open = False
                    st.rerun()
        elif (
            request_id in st.session_state.form_submitted
            and st.session_state.form_submitted[request_id]["error"] is None
        ):
            st.success("Feedback submitted", icon="✅")
        else:
            st.error(st.session_state.form_submitted[request_id]["error"])


def submit_feedback(
    request_id: str, positive: bool, feedback_message: str
) -> Optional[str]:
    request_body = {
        "request_id": request_id,
        "positive": positive,
        "feedback_message": feedback_message,
    }
    resp = _snowflake.send_snow_api_request(
        "POST",  # method
        FEEDBACK_API_ENDPOINT,  # path
        {},  # headers
        {},  # params
        request_body,  # body
        None,  # request_guid
        API_TIMEOUT,  # timeout in milliseconds
    )
    if resp["status"] == 200:
        return None

    parsed_content = json.loads(resp["content"])
    # Craft readable error message
    err_msg = f"""
        🚨 An Analyst API error has occurred 🚨
        
        * response code: `{resp['status']}`
        * request-id: `{parsed_content['request_id']}`
        * error code: `{parsed_content['error_code']}`
        
        Message:
        ```
        {parsed_content['message']}
        ```
        """
    return err_msg


if __name__ == "__main__":
    main() 
