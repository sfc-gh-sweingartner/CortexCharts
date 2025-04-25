-- Create Reports Table for Snowflake Interactive Charts
CREATE OR REPLACE TABLE  CORTEX_ANALYST_REPORTS (
    REPORT_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    REPORT_NAME VARCHAR(255) NOT NULL,
    REPORT_DESCRIPTION VARCHAR(4000),
    SQL_STATEMENT VARCHAR(16777216),
    CHART_CODE VARCHAR(16777216),
    CHART_METADATA VARCHAR(16777216), -- Stores JSON metadata about the chart's columns and configuration
    CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Create comment on table
COMMENT ON TABLE CORTEX_ANALYST_REPORTS IS 'Table to store saved reports from the Snowflake Interactive Charts application';

-- Create comments on columns
COMMENT ON COLUMN CORTEX_ANALYST_REPORTS.REPORT_ID IS 'Unique identifier for each report';
COMMENT ON COLUMN CORTEX_ANALYST_REPORTS.REPORT_NAME IS 'Name of the report';
COMMENT ON COLUMN CORTEX_ANALYST_REPORTS.REPORT_DESCRIPTION IS 'Description or prompt used to generate the report';
COMMENT ON COLUMN CORTEX_ANALYST_REPORTS.SQL_STATEMENT IS 'SQL query used to generate the report data';
COMMENT ON COLUMN CORTEX_ANALYST_REPORTS.CHART_CODE IS 'Altair chart code used to visualize the data';
COMMENT ON COLUMN CORTEX_ANALYST_REPORTS.CHART_METADATA IS 'JSON string containing metadata about chart columns and configuration';
COMMENT ON COLUMN CORTEX_ANALYST_REPORTS.CREATED_AT IS 'Timestamp when the report was created';
COMMENT ON COLUMN CORTEX_ANALYST_REPORTS.UPDATED_AT IS 'Timestamp when the report was last updated';

-- Create Dashboards Table for Snowflake Interactive Charts
CREATE OR REPLACE TABLE  CORTEX_ANALYST_DASHBOARDS (
    DASHBOARD_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    DASHBOARD_NAME VARCHAR(255) NOT NULL,
    REPORTS VARCHAR(16777216), -- Stores a comma-separated list of REPORT_IDs
    CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Create comment on table
COMMENT ON TABLE CORTEX_ANALYST_DASHBOARDS IS 'Table to store saved dashboards from the Snowflake Interactive Charts application';

-- Create comments on columns
COMMENT ON COLUMN CORTEX_ANALYST_DASHBOARDS.DASHBOARD_ID IS 'Unique identifier for each dashboard';
COMMENT ON COLUMN CORTEX_ANALYST_DASHBOARDS.DASHBOARD_NAME IS 'Name of the dashboard';
COMMENT ON COLUMN CORTEX_ANALYST_DASHBOARDS.REPORTS IS 'Comma-separated list of report IDs included in this dashboard';
COMMENT ON COLUMN CORTEX_ANALYST_DASHBOARDS.CREATED_AT IS 'Timestamp when the dashboard was created';
COMMENT ON COLUMN CORTEX_ANALYST_DASHBOARDS.UPDATED_AT IS 'Timestamp when the dashboard was last updated'; 