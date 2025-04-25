"""
Text2SQL Interactive Charts
====================
This is the main landing page for the Text2SQL Interactive Charts application.

The overall design of this solution is as follows:
This Streamlit application has a home page (Home.py) and the user first goes to Cortex Analyst (1_Cortex_Analyst.py) page and asks a question.
This Text2SQL chatbot page returns a SQL Statement and a table with data in it.  
Based on the columns in that table, this chatbot then automatically places an appropriate chart under the table. 
A user can then click "Open in Designer" and that opens the same SQL, table, and chart in the Report Designer ( 2_Report_Designer.py)
They can then override the report name, description, SQL and the charting code and then save the report
Any customised charts / reports are saved into the CORTEX_ANALYST_REPORTS table.
Then users move onto the Dashboard page to assemble many charts / reports into dashboards.
This information is saved in the CORTEX_ANALYST_DASHBOARDS table.
The utils library defines the default charts that are used by the solution. 

"""
import streamlit as st

st.set_page_config(
    page_title="Snowflake Interactive Charts",
    page_icon="❄️",
    layout="wide",
)

# Main page content
st.title("Welcome to Text2SQL Interactive Charts")
st.markdown("""
This application provides a suite of tools to interact with your Snowflake data:

- **Cortex Analyst**: Ask questions about your data using natural language
- **Report Designer**: Create and customize reports from your data
- **Dashboard**: View and interact with visualizations in a dashboard format

Select Cortex Analyst on the left to get started. Ask questions and if you like the results,
send it to Report Designer to modify if if you like then save the report. 
Once you have a report, you can add it to the Dashboard.

The stats below are mock KPI's but they make you look good so let's just keep them.
                        
""")

# Add some mock visualizations or stats for the home page
col1, col2 = st.columns(2)
with col1:
    st.subheader("Recent Activity")
    st.info("You have 5 active sessions")
    st.metric(label="Queries Executed Today", value="143", delta="12")
    
with col2:
    st.subheader("Quick Stats")
    st.metric(label="Data Analyzed", value="1.2 TB", delta="0.3 TB", delta_color="normal")
    st.metric(label="Time Saved", value="120 hours", delta="15%", delta_color="normal") 