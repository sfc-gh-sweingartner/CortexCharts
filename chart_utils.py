"""
Chart Utilities
==============
Shared chart creation utilities for Cortex Analyst and Report Designer.
This module provides centralized chart generation logic to ensure consistent
visualization between different parts of the application.
"""
import pandas as pd
import altair as alt
import streamlit as st


def create_chart_from_metadata(df):
    """
    Create an Altair chart based on the chart_metadata in the dataframe.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with chart_metadata attribute containing chart configuration
        
    Returns:
    --------
    altair.Chart or None
        The created chart object or None if chart couldn't be created
    """
    try:
        if not hasattr(df, 'attrs') or 'chart_metadata' not in df.attrs:
            return None
            
        chart_metadata = df.attrs.get('chart_metadata', {})
        
        # Determine which chart type to create based on metadata
        if 'chart1_columns' in chart_metadata:
            return create_chart1(df, chart_metadata['chart1_columns'])
        elif 'chart2_columns' in chart_metadata:
            return create_chart2(df, chart_metadata['chart2_columns'])
        elif 'chart3_columns' in chart_metadata:
            return create_chart3(df, chart_metadata['chart3_columns'])
        elif 'chart4_columns' in chart_metadata:
            return create_chart4(df, chart_metadata['chart4_columns'])
        elif 'chart5_columns' in chart_metadata:
            return create_chart5(df, chart_metadata['chart5_columns'])
        elif 'chart6_columns' in chart_metadata:
            return create_chart6(df, chart_metadata['chart6_columns'])
        elif 'chart7_columns' in chart_metadata:
            return create_chart7(df, chart_metadata['chart7_columns'])
        elif 'chart8_columns' in chart_metadata:
            return create_chart8(df, chart_metadata['chart8_columns'])
        elif 'chart9_columns' in chart_metadata:
            return create_chart9(df, chart_metadata['chart9_columns'])
        
        # If no specific metadata found, return None
        return None
        
    except Exception as e:
        print(f"Error creating chart from metadata: {str(e)}")
        return None


def create_chart1(df, cols):
    """
    Create Chart 1: Bar Chart by Date
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with date_col and numeric_col
        
    Returns:
    --------
    altair.Chart
        Bar chart with date on x-axis and numeric value on y-axis
    """
    try:
        date_col = cols.get('date_col')
        numeric_col = cols.get('numeric_col')
        
        return alt.Chart(df).mark_bar().encode(
            x=alt.X(date_col + ':T', sort='ascending'),
            y=alt.Y(numeric_col + ':Q'),
            tooltip=[date_col, numeric_col]
        ).properties(title='1 Bar Chart by Date')
    except Exception as e:
        print(f"Error creating Chart 1: {str(e)}")
        return None


def create_chart2(df, cols):
    """
    Create Chart 2: Dual Axis Line Chart
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with date_col, num_col1, and num_col2
        
    Returns:
    --------
    altair.LayerChart
        Dual line chart with date on x-axis and two numeric values on independent y-axes
    """
    try:
        date_col = cols.get('date_col')
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        
        base = alt.Chart(df).encode(x=alt.X(date_col + ':T', sort='ascending'))
        line1 = base.mark_line(color='blue').encode(
            y=alt.Y(num_col1 + ':Q', axis=alt.Axis(title=num_col1)),
            tooltip=[date_col, num_col1]
        )
        line2 = base.mark_line(color='red').encode(
            y=alt.Y(num_col2 + ':Q', axis=alt.Axis(title=num_col2)),
            tooltip=[date_col, num_col2]
        )
        return alt.layer(line1, line2).resolve_scale(
            y='independent'
        ).properties(title='2 Dual Axis Line Chart')
    except Exception as e:
        print(f"Error creating Chart 2: {str(e)}")
        return None


def create_chart3(df, cols):
    """
    Create Chart 3: Stacked Bar Chart by Date
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with date_col, text_col, and numeric_col
        
    Returns:
    --------
    altair.Chart
        Stacked bar chart with date on x-axis, numeric value on y-axis, and categorical color
    """
    try:
        date_col = cols.get('date_col')
        text_col = cols.get('text_col')
        numeric_col = cols.get('numeric_col')
        
        return alt.Chart(df).mark_bar().encode(
            x=alt.X(date_col + ':T', sort='ascending'),
            y=alt.Y(numeric_col + ':Q', stack='zero'),
            color=alt.Color(text_col + ':N'),
            tooltip=[date_col, text_col, numeric_col]
        ).properties(title='3 Stacked Bar Chart by Date')
    except Exception as e:
        print(f"Error creating Chart 3: {str(e)}")
        return None


def create_chart4(df, cols):
    """
    Create Chart 4: Stacked Bar Chart with Text Column Selector for Colors
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with date_col, text_cols, and numeric_col
        
    Returns:
    --------
    altair.Chart
        Stacked bar chart with date on x-axis, numeric value on y-axis, and selectable categorical colors
    """
    try:
        date_col = cols.get('date_col')
        text_cols = cols.get('text_cols', [])
        numeric_col = cols.get('numeric_col')
        
        # Ensure we have at least one text column
        if not text_cols:
            # Find suitable text columns if not specified
            all_cols = list(df.columns)
            possible_text_cols = [col for col in all_cols if col != date_col and col != numeric_col]
            if possible_text_cols:
                text_cols = possible_text_cols
            else:
                # If no text columns available, return None
                return None
        
        # Generate a unique key for this chart based on dataframe and columns
        df_hash = hash(str(df.shape) + str(df.columns.tolist()))
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
        
        # Create the chart with the selected text column
        return alt.Chart(df).mark_bar().encode(
            x=alt.X(date_col + ':T', sort='ascending'),
            y=alt.Y(numeric_col + ':Q', stack='zero'),
            color=alt.Color(selected_text_col + ':N', title=selected_text_col),
            tooltip=[date_col, selected_text_col, numeric_col]
        ).properties(title='4 Stacked Bar Chart with Selectable Colors')
    except Exception as e:
        print(f"Error creating Chart 4: {str(e)}")
        return None


def create_chart5(df, cols):
    """
    Create Chart 5: Scatter Chart
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with num_col1, num_col2, and text_col
        
    Returns:
    --------
    altair.Chart
        Scatter chart with numeric x/y and categorical color
    """
    try:
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        text_col = cols.get('text_col')
        
        return alt.Chart(df).mark_circle(size=100).encode(
            x=alt.X(num_col1 + ':Q'),
            y=alt.Y(num_col2 + ':Q'),
            color=alt.Color(text_col + ':N'),
            tooltip=[text_col, num_col1, num_col2]
        ).properties(title='5 Scatter Chart')
    except Exception as e:
        print(f"Error creating Chart 5: {str(e)}")
        return None


def create_chart6(df, cols):
    """
    Create Chart 6: Scatter Chart with Multiple Dimensions
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with num_col1, num_col2, text_col1, and text_col2
        
    Returns:
    --------
    altair.Chart
        Scatter chart with numeric x/y and categorical color and shape
    """
    try:
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        text_col1 = cols.get('text_col1')
        text_col2 = cols.get('text_col2')
        
        return alt.Chart(df).mark_point(size=100).encode(
            x=alt.X(num_col1 + ':Q'),
            y=alt.Y(num_col2 + ':Q'),
            color=alt.Color(text_col1 + ':N'),
            shape=alt.Shape(text_col2 + ':N', scale=alt.Scale(
                range=["circle", "square", "cross", "diamond", "triangle-up", "triangle-down", 
                       "triangle-right", "triangle-left", "arrow", "wedge", "stroke"]
            )),
            tooltip=[text_col1, text_col2, num_col1, num_col2]
        ).properties(title='6 Scatter Chart with Multiple Dimensions')
    except Exception as e:
        print(f"Error creating Chart 6: {str(e)}")
        return None


def create_chart7(df, cols):
    """
    Create Chart 7: Bubble Chart
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with num_col1, num_col2, num_col3, and text_col
        
    Returns:
    --------
    altair.Chart
        Bubble chart with numeric x/y/size and categorical color
    """
    try:
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        num_col3 = cols.get('num_col3')
        text_col = cols.get('text_col')
        
        return alt.Chart(df).mark_circle().encode(
            x=alt.X(num_col1 + ':Q'),
            y=alt.Y(num_col2 + ':Q'),
            size=alt.Size(num_col3 + ':Q'),
            color=alt.Color(text_col + ':N'),
            tooltip=[text_col, num_col1, num_col2, num_col3]
        ).properties(title='7 Bubble Chart')
    except Exception as e:
        print(f"Error creating Chart 7: {str(e)}")
        return None


def create_chart8(df, cols):
    """
    Create Chart 8: Multi-Dimensional Bubble Chart
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with num_col1, num_col2, num_col3, text_col1, and text_col2
        
    Returns:
    --------
    altair.Chart
        Multi-dimensional bubble chart with numeric x/y/size and categorical color and shape
    """
    try:
        num_col1 = cols.get('num_col1')
        num_col2 = cols.get('num_col2')
        num_col3 = cols.get('num_col3')
        text_col1 = cols.get('text_col1')
        text_col2 = cols.get('text_col2')
        
        return alt.Chart(df).mark_point().encode(
            x=alt.X(num_col1 + ':Q'),
            y=alt.Y(num_col2 + ':Q'),
            size=alt.Size(num_col3 + ':Q'),
            color=alt.Color(text_col1 + ':N'),
            shape=alt.Shape(text_col2 + ':N', scale=alt.Scale(
                range=["circle", "square", "cross", "diamond", "triangle-up", "triangle-down", 
                       "triangle-right", "triangle-left", "arrow", "wedge", "stroke"]
            )),
            tooltip=[text_col1, text_col2, num_col1, num_col2, num_col3]
        ).properties(title='8 Multi-Dimensional Bubble Chart')
    except Exception as e:
        print(f"Error creating Chart 8: {str(e)}")
        return None


def create_chart9(df, cols):
    """
    Create Chart 9: Bar Chart with Text Column Selector
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with data
    cols : dict
        Column configuration with numeric_col and text_cols
        
    Returns:
    --------
    altair.Chart and selectbox widget
        Bar chart with numeric value on y-axis and selected text column on x-axis
    """
    try:
        numeric_col = cols.get('numeric_col')
        text_cols = cols.get('text_cols', [])
        
        if not text_cols:
            return None
        
        # Generate a unique key for this chart based on dataframe and columns
        df_hash = hash(str(df.shape) + str(df.columns.tolist()))
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
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(f"{selected_text_col}:N", sort='-y'),
            y=alt.Y(f"{numeric_col}:Q"),
            tooltip=[selected_text_col, numeric_col]
        ).properties(title='9 Bar Chart with Selectable X-Axis')
        
        return chart
    except Exception as e:
        print(f"Error creating Chart 9: {str(e)}")
        return None


# Utility functions for common chart operations
def detect_column_types(df):
    """
    Automatically detect different column types in a DataFrame
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to analyze
        
    Returns:
    --------
    dict
        Dictionary with categorized columns (date_cols, numeric_cols, text_cols)
    """
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    text_cols = [col for col in df.columns if col not in numeric_cols and col not in date_cols]
    
    return {
        'date_cols': date_cols,
        'numeric_cols': numeric_cols,
        'text_cols': text_cols
    }


def suggest_chart_type(df):
    """
    Analyze a DataFrame and suggest an appropriate chart type
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to analyze
        
    Returns:
    --------
    str
        Suggested chart type based on data structure
    """
    col_types = detect_column_types(df)
    date_cols = col_types['date_cols']
    numeric_cols = col_types['numeric_cols']
    text_cols = col_types['text_cols']
    
    # Chart 1: Single date column, single numeric column
    if len(date_cols) == 1 and len(numeric_cols) == 1 and len(text_cols) == 0:
        return 'chart1'
        
    # Chart 2: Single date column, multiple numeric columns
    elif len(date_cols) == 1 and len(numeric_cols) >= 2 and len(text_cols) == 0:
        return 'chart2'
        
    # Chart 3: Date column, numeric column, and one categorical column
    elif len(date_cols) == 1 and len(numeric_cols) >= 1 and len(text_cols) == 1:
        return 'chart3'
        
    # Chart 4: Date column, numeric column, and multiple categorical columns
    elif len(date_cols) == 1 and len(numeric_cols) >= 1 and len(text_cols) >= 2:
        return 'chart4'
        
    # Default to generic bar chart
    return 'bar'


def generate_chart_code_for_dataframe(df):
    """
    Generate chart code for a dataframe based on its chart_metadata.
    This centralizes chart code generation to avoid duplication across pages.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with chart_metadata attribute containing chart configuration
        
    Returns:
    --------
    str
        The generated chart code as a string
    """
    import io
    buf = io.StringIO()
    print("import altair as alt", file=buf)
    print("import pandas as pd", file=buf)
    print("\n# Chart code", file=buf)
    print("def create_chart(df):", file=buf)
    
    # Determine which chart type we have based on metadata and generate appropriate code
    if hasattr(df, 'attrs') and 'chart_metadata' in df.attrs:
        chart_metadata = df.attrs['chart_metadata']
        
        if 'chart1_columns' in chart_metadata:
            cols = chart_metadata['chart1_columns']
            date_col = cols.get('date_col')
            numeric_col = cols.get('numeric_col')
            
            if not date_col or not numeric_col:
                print(f"    # Error: Missing required columns for chart1", file=buf)
                print(f"    st.error('Missing required columns for Bar Chart by Date')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_bar().encode(", file=buf)
                print(f"        x=alt.X('{date_col}:T', sort='ascending'),", file=buf)
                print(f"        y=alt.Y('{numeric_col}:Q'),", file=buf)
                print(f"        tooltip=['{date_col}', '{numeric_col}']", file=buf)
                print(f"    ).properties(title='Bar Chart by Date')", file=buf)
            
        elif 'chart2_columns' in chart_metadata:
            cols = chart_metadata['chart2_columns']
            date_col = cols.get('date_col')
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            
            if not date_col or not num_col1 or not num_col2:
                print(f"    # Error: Missing required columns for chart2", file=buf)
                print(f"    st.error('Missing required columns for Dual Axis Line Chart')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    base = alt.Chart(df).encode(x=alt.X('{date_col}:T', sort='ascending'))", file=buf)
                print(f"    line1 = base.mark_line(color='blue').encode(", file=buf)
                print(f"        y=alt.Y('{num_col1}:Q', axis=alt.Axis(title='{num_col1}')),", file=buf)
                print(f"        tooltip=['{date_col}', '{num_col1}']", file=buf)
                print(f"    )", file=buf)
                print(f"    line2 = base.mark_line(color='red').encode(", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q', axis=alt.Axis(title='{num_col2}')),", file=buf)
                print(f"        tooltip=['{date_col}', '{num_col2}']", file=buf)
                print(f"    )", file=buf)
                print(f"    return alt.layer(line1, line2).resolve_scale(", file=buf)
                print(f"        y='independent'", file=buf)
                print(f"    ).properties(title='Dual Axis Line Chart')", file=buf)
        
        elif 'chart3_columns' in chart_metadata:
            cols = chart_metadata['chart3_columns']
            date_col = cols.get('date_col')
            text_col = cols.get('text_col')
            numeric_col = cols.get('numeric_col')
            
            if not date_col or not text_col or not numeric_col:
                print(f"    # Error: Missing required columns for chart3", file=buf)
                print(f"    st.error('Missing required columns for Stacked Bar Chart by Date')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_bar().encode(", file=buf)
                print(f"        x=alt.X('{date_col}:T', sort='ascending'),", file=buf)
                print(f"        y=alt.Y('{numeric_col}:Q', stack='zero'),", file=buf)
                print(f"        color=alt.Color('{text_col}:N'),", file=buf)
                print(f"        tooltip=['{date_col}', '{text_col}', '{numeric_col}']", file=buf)
                print(f"    ).properties(title='Stacked Bar Chart by Date')", file=buf)
        
        elif 'chart4_columns' in chart_metadata:
            cols = chart_metadata['chart4_columns']
            date_col = cols.get('date_col')
            text_cols = cols.get('text_cols', [])
            numeric_col = cols.get('numeric_col')
            
            if not date_col or not text_cols or not numeric_col or len(text_cols) < 2:
                print(f"    # Error: Missing required columns for chart4", file=buf)
                print(f"    st.error('Missing required columns for Stacked Bar Chart with Text Column Selector for Colors')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    # Generate a unique key for this chart based on dataframe and columns", file=buf)
                print(f"    df_hash = hash(str(df.shape) + str(df.columns.tolist()))", file=buf)
                print(f"    widget_key = f\"chart4_select_{{df_hash}}\"", file=buf)
                print(f"", file=buf)
                print(f"    # Initialize the session state value if it doesn't exist", file=buf)
                print(f"    if widget_key not in st.session_state:", file=buf)
                print(f"        st.session_state[widget_key] = {text_cols}[0]", file=buf)
                print(f"    # If the value exists but is not in text_cols (changed data), reset it", file=buf)
                print(f"    elif st.session_state[widget_key] not in {text_cols}:", file=buf)
                print(f"        st.session_state[widget_key] = {text_cols}[0]", file=buf)
                print(f"", file=buf)
                print(f"    # Get the selected column from session state", file=buf)
                print(f"    selected_text_col = st.selectbox(", file=buf)
                print(f"        \"Select column for color grouping:\",", file=buf)
                print(f"        options={text_cols},", file=buf)
                print(f"        index={text_cols}.index(st.session_state[widget_key]),", file=buf)
                print(f"        key=widget_key", file=buf)
                print(f"    )", file=buf)
                print(f"", file=buf)
                print(f"    # Create the chart with the selected text column", file=buf)
                print(f"    return alt.Chart(df).mark_bar().encode(", file=buf)
                print(f"        x=alt.X('{date_col}:T', sort='ascending'),", file=buf)
                print(f"        y=alt.Y('{numeric_col}:Q', stack='zero'),", file=buf)
                print(f"        color=alt.Color('{{selected_text_col}}:N', title='{{selected_text_col}}'),", file=buf)
                print(f"        tooltip=['{date_col}', '{{selected_text_col}}', '{numeric_col}']", file=buf)
                print(f"    ).properties(title='Stacked Bar Chart with Selectable Colors')", file=buf)
        
        elif 'chart5_columns' in chart_metadata:
            cols = chart_metadata['chart5_columns']
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            text_col = cols.get('text_col')
            
            if not num_col1 or not num_col2 or not text_col:
                print(f"    # Error: Missing required columns for chart5", file=buf)
                print(f"    st.error('Missing required columns for Scatter Chart')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_circle(size=60).encode(", file=buf)
                print(f"        x=alt.X('{num_col1}:Q'),", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q'),", file=buf)
                print(f"        color=alt.Color('{text_col}:N'),", file=buf)
                print(f"        tooltip=['{num_col1}', '{num_col2}', '{text_col}']", file=buf)
                print(f"    ).properties(title='Scatter Plot')", file=buf)
        
        elif 'chart6_columns' in chart_metadata:
            cols = chart_metadata['chart6_columns']
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            text_col1 = cols.get('text_col1')
            text_col2 = cols.get('text_col2')
            
            if not num_col1 or not num_col2 or not text_col1 or not text_col2:
                print(f"    # Error: Missing required columns for chart6", file=buf)
                print(f"    st.error('Missing required columns for Scatter Chart with Multiple Dimensions')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_point(size=100).encode(", file=buf)
                print(f"        x=alt.X('{num_col1}:Q'),", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q'),", file=buf)
                print(f"        color=alt.Color('{text_col1}:N'),", file=buf)
                print(f"        shape=alt.Shape('{text_col2}:N', scale=alt.Scale(", file=buf)
                print(f"            range=[\"circle\", \"square\", \"cross\", \"diamond\", \"triangle-up\", \"triangle-down\", ", file=buf)
                print(f"                   \"triangle-right\", \"triangle-left\", \"arrow\", \"wedge\", \"stroke\"]", file=buf)
                print(f"        )),", file=buf)
                print(f"        tooltip=['{text_col1}', '{text_col2}', '{num_col1}', '{num_col2}']", file=buf)
                print(f"    ).properties(title='Scatter Chart with Multiple Dimensions')", file=buf)
        
        elif 'chart7_columns' in chart_metadata:
            cols = chart_metadata['chart7_columns']
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            num_col3 = cols.get('num_col3')
            text_col = cols.get('text_col')
            
            if not num_col1 or not num_col2 or not num_col3 or not text_col:
                print(f"    # Error: Missing required columns for chart7", file=buf)
                print(f"    st.error('Missing required columns for Bubble Chart')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_circle().encode(", file=buf)
                print(f"        x=alt.X('{num_col1}:Q'),", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q'),", file=buf)
                print(f"        size=alt.Size('{num_col3}:Q'),", file=buf)
                print(f"        color=alt.Color('{text_col}:N'),", file=buf)
                print(f"        tooltip=['{num_col1}', '{num_col2}', '{num_col3}', '{text_col}']", file=buf)
                print(f"    ).properties(title='Bubble Chart')", file=buf)
        
        elif 'chart8_columns' in chart_metadata:
            cols = chart_metadata['chart8_columns']
            num_col1 = cols.get('num_col1')
            num_col2 = cols.get('num_col2')
            num_col3 = cols.get('num_col3')
            text_col1 = cols.get('text_col1')
            text_col2 = cols.get('text_col2')
            
            if not num_col1 or not num_col2 or not num_col3 or not text_col1 or not text_col2:
                print(f"    # Error: Missing required columns for chart8", file=buf)
                print(f"    st.error('Missing required columns for Multi-Dimensional Bubble Chart')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    return alt.Chart(df).mark_point().encode(", file=buf)
                print(f"        x=alt.X('{num_col1}:Q'),", file=buf)
                print(f"        y=alt.Y('{num_col2}:Q'),", file=buf)
                print(f"        size=alt.Size('{num_col3}:Q'),", file=buf)
                print(f"        color=alt.Color('{text_col1}:N'),", file=buf)
                print(f"        shape=alt.Shape('{text_col2}:N', scale=alt.Scale(", file=buf)
                print(f"            range=[\"circle\", \"square\", \"cross\", \"diamond\", \"triangle-up\", \"triangle-down\", ", file=buf)
                print(f"                   \"triangle-right\", \"triangle-left\", \"arrow\", \"wedge\", \"stroke\"]", file=buf)
                print(f"        )),", file=buf)
                print(f"        tooltip=['{text_col1}', '{text_col2}', '{num_col1}', '{num_col2}', '{num_col3}']", file=buf)
                print(f"    ).properties(title='Multi-Dimensional Bubble Chart')", file=buf)
        
        elif 'chart9_columns' in chart_metadata:
            cols = chart_metadata['chart9_columns']
            numeric_col = cols.get('numeric_col')
            text_cols = cols.get('text_cols')
            
            if not numeric_col or not text_cols or len(text_cols) == 0:
                print(f"    # Error: Missing required columns for chart9", file=buf)
                print(f"    st.error('Missing required columns for Bar Chart with Text Column Selector')", file=buf)
                print(f"    return None", file=buf)
            else:
                print(f"    # Generate a unique key for this chart based on dataframe and columns", file=buf)
                print(f"    df_hash = hash(str(df.shape) + str(df.columns.tolist()))", file=buf)
                print(f"    widget_key = f\"chart9_select_{{df_hash}}\"", file=buf)
                print(f"", file=buf)
                print(f"    # Initialize the session state value if it doesn't exist", file=buf)
                print(f"    if widget_key not in st.session_state:", file=buf)
                print(f"        st.session_state[widget_key] = {text_cols}[0]", file=buf)
                print(f"    # If the value exists but is not in text_cols (changed data), reset it", file=buf)
                print(f"    elif st.session_state[widget_key] not in {text_cols}:", file=buf)
                print(f"        st.session_state[widget_key] = {text_cols}[0]", file=buf)
                print(f"", file=buf)
                print(f"    # Get the selected column from session state", file=buf)
                print(f"    selected_text_col = st.selectbox(", file=buf)
                print(f"        \"Select column for X-axis:\",", file=buf)
                print(f"        options={text_cols},", file=buf)
                print(f"        index={text_cols}.index(st.session_state[widget_key]),", file=buf)
                print(f"        key=widget_key", file=buf)
                print(f"    )", file=buf)
                print(f"", file=buf)
                print(f"    # Create the bar chart with the selected text column", file=buf)
                print(f"    return alt.Chart(df).mark_bar().encode(", file=buf)
                print(f"        x=alt.X(f\"{{selected_text_col}}:N\", sort='-y'),", file=buf)
                print(f"        y=alt.Y(f\"{numeric_col}:Q\"),", file=buf)
                print(f"        tooltip=[selected_text_col, '{numeric_col}']", file=buf)
                print(f"    ).properties(title='Bar Chart with Selectable X-Axis')", file=buf)
        
        else:
            # No specific chart type identified in metadata
            print(f"    # No chart type identified in metadata", file=buf)
            print(f"    st.error('No valid chart type found in metadata. Please provide chart configuration.')", file=buf)
            print(f"    return None", file=buf)
    else:
        # No chart metadata
        print(f"    # No chart metadata available", file=buf)
        print(f"    st.error('No chart metadata available. Please provide chart configuration.')", file=buf)
        print(f"    return None", file=buf)
    
    # Return the generated code
    return buf.getvalue() 