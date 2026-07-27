import plotly.express as px
import pandas as pd
import streamlit as st

def render_chart(data: list[dict], columns: list[str]):
    """
    Automatically detects the best chart type and renders it using Plotly.
    """
    if not data or len(data) == 0:
        return
        
    df = pd.DataFrame(data)
    
    # Identify column types
    categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    # Need at least one numerical column to plot anything meaningful
    if not numerical_cols:
        return
        
    # 1. Line Chart: If there is a date column and a numerical column
    if date_cols and len(numerical_cols) >= 1:
        x_col = date_cols[0]
        y_col = numerical_cols[0]
        fig = px.line(df, x=x_col, y=y_col, title=f"{y_col.capitalize()} over Time", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        return
        
    # 2. Bar Chart / Pie Chart: If there is a categorical column and a numerical column
    if categorical_cols and len(numerical_cols) >= 1:
        x_col = categorical_cols[0]
        y_col = numerical_cols[0]
        
        # If there are few unique categories, maybe a pie chart
        unique_cats = df[x_col].nunique()
        
        if unique_cats <= 5:
            fig = px.pie(df, names=x_col, values=y_col, title=f"{y_col.capitalize()} by {x_col.capitalize()}", hole=0.4)
        else:
            # Sort by Y descending for better bar charts
            df_sorted = df.sort_values(by=y_col, ascending=False).head(15) # Top 15 max
            fig = px.bar(df_sorted, x=x_col, y=y_col, title=f"Top {y_col.capitalize()} by {x_col.capitalize()}", color=y_col, color_continuous_scale="Viridis")
            
        st.plotly_chart(fig, use_container_width=True)
        return
        
    # 3. Histogram: If there are only numerical columns and many rows
    if len(numerical_cols) >= 1 and len(df) > 5:
        fig = px.histogram(df, x=numerical_cols[0], title=f"Distribution of {numerical_cols[0].capitalize()}")
        st.plotly_chart(fig, use_container_width=True)
        return
