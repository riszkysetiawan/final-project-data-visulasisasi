import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from sqlalchemy import create_engine
import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

upn_base64 = get_base64_image("assets/img/upn.png")
favicon = f"data:image/png;base64,{upn_base64}"

st.set_page_config(page_title="Dashboard Data Warehouse", page_icon=favicon)

# Koneksi ke database MySQL
def run_query(query):
    engine = create_engine('mysql+pymysql://root:@localhost:3306/dump-dw_aw')
    df = pd.read_sql(query, engine)
    return df

blu_base64 = get_base64_image("assets/img/blu.png")

st.sidebar.markdown(
    f"""
    <div class="sidebar-logo">
        <img src="data:image/png;base64,{upn_base64}" width="50">
        <img src="data:image/png;base64,{blu_base64}" width="50">
        <h2>Dashboard Data Warehouse</h2>
    </div>
    """,
    unsafe_allow_html=True
)

#css
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("assets/css/style.css")

# Sidebar Filters
selected_years = st.sidebar.multiselect('Select years', [str(year) for year in range(2001, 2005)])

# Additional Filters
selected_region = st.sidebar.multiselect('Select Sales Territory Region', 
                                         ['Australia', 'Canada', 'France', 'Germany', 'Northwest', 'Southwest', 'United Kingdom'])

# Grafik 1
def visualize_sales_composition(selected_region, selected_years):
    query = '''
    SELECT st.SalesTerritoryRegion, dt.FullDateAlternateKey, SUM(fi.SalesAmount) as TotalSales
    FROM factinternetsales fi
    JOIN dimsalesterritory st ON fi.SalesTerritoryKey = st.SalesTerritoryKey
    JOIN dimtime dt ON fi.OrderDateKey = dt.TimeKey
    GROUP BY st.SalesTerritoryRegion, dt.FullDateAlternateKey
    ORDER BY dt.FullDateAlternateKey
    '''
    df = run_query(query)
    
    # filter
    df['FullDateAlternateKey'] = pd.to_datetime(df['FullDateAlternateKey'])
    df['Year'] = df['FullDateAlternateKey'].dt.year
    if selected_region:
        df = df[df['SalesTerritoryRegion'].isin(selected_region)]
    if selected_years:
        df = df[df['Year'].isin(map(int, selected_years))]

    if df.empty:
        st.warning('No data available for the selected filters.')
        return

    df_pivot = df.pivot_table(index='FullDateAlternateKey', columns='SalesTerritoryRegion', values='TotalSales', fill_value=0)
    df_percent = df_pivot.div(df_pivot.sum(axis=1), axis=0).reset_index()
    df_long = pd.melt(df_percent, id_vars=['FullDateAlternateKey'], var_name='SalesTerritoryRegion', value_name='Percentage')

    fig = px.area(df_long, x='FullDateAlternateKey', y='Percentage', color='SalesTerritoryRegion', 
                  title='Sales Composition by Territory Over Time')
    fig.update_layout(xaxis_title='Date', yaxis_title='Percentage of Total Sales', legend_title='Sales Territory Region')
    st.plotly_chart(fig)

# Grafik 2
def visualize_data_distribution():
    query = '''
    SELECT dt.FullDateAlternateKey, SUM(fi.SalesAmount) as TotalSales
    FROM factinternetsales fi
    JOIN dimtime dt ON fi.OrderDateKey = dt.TimeKey
    GROUP BY dt.FullDateAlternateKey
    ORDER BY dt.FullDateAlternateKey
    '''
    df = run_query(query)
    
    # filter
    df['FullDateAlternateKey'] = pd.to_datetime(df['FullDateAlternateKey'])
    df['Year'] = df['FullDateAlternateKey'].dt.year
    selected_years_dist = st.sidebar.multiselect('Select years for Distribution', df['Year'].unique(), default=df['Year'].unique())
    df = df[df['Year'].isin(selected_years_dist)]

    if df.empty:
        st.warning('No data available for the selected filters.')
        return

    fig, ax = plt.subplots()
    sns.histplot(df['TotalSales'], kde=True, ax=ax, color='teal')
    ax.set_title('Data Distribution of Total Sales')
    ax.set_xlabel('Total Sales')
    ax.set_ylabel('Density')
    st.pyplot(fig)

# Grafik 3
def visualize_total_sales_over_time(selected_years):
    query = '''
    SELECT dt.FullDateAlternateKey, SUM(fi.SalesAmount) as TotalSales
    FROM factinternetsales fi
    JOIN dimtime dt ON fi.OrderDateKey = dt.TimeKey
    GROUP BY dt.FullDateAlternateKey
    ORDER BY dt.FullDateAlternateKey
    '''
    df = run_query(query)
    
    #filter
    df['FullDateAlternateKey'] = pd.to_datetime(df['FullDateAlternateKey'])
    df['Year'] = df['FullDateAlternateKey'].dt.year
    if selected_years:
        df = df[df['Year'].isin(map(int, selected_years))]

    if df.empty:
        st.warning('No data available for the selected filters.')
        return

    fig = px.line(df, x='FullDateAlternateKey', y='TotalSales', title='Total Sales Over Time', 
                  labels={'FullDateAlternateKey': 'Date', 'TotalSales': 'Total Sales'},
                  hover_data={'FullDateAlternateKey': '|%B %d, %Y'}, template='plotly_white')
    fig.update_layout(xaxis_title='Date', yaxis_title='Total Sales')
    st.plotly_chart(fig)

# Grafik 4
def visualize_scatter_plot():
    query = '''
    SELECT p.ListPrice, SUM(s.OrderQuantity) AS TotalQuantity
    FROM factinternetsales s
    JOIN dimproduct p ON s.ProductKey = p.ProductKey
    GROUP BY p.ListPrice
    '''
    df = run_query(query)
    
    fig = px.scatter(df, x='ListPrice', y='TotalQuantity', color='TotalQuantity', title='Scatter Plot of Product List Price vs. Total Order Quantity')
    fig.update_layout(xaxis_title='List Price', yaxis_title='Total Order Quantity')
    st.plotly_chart(fig)

# Streamlit 
st.title('Dashboard Data Warehouse')

st.header('Sales Composition by Territory Over Time')
visualize_sales_composition(selected_region, selected_years)

st.header('Data Distribution of Total Sales')
visualize_data_distribution()

st.header('Total Sales Over Time')
visualize_total_sales_over_time(selected_years)

st.header('Scatter Plot of Product List Price vs. Total Order Quantity')
visualize_scatter_plot()

# Sidebar
with st.sidebar.expander("Information", expanded=True):
    st.write("This dashboard allows you to visualize sales data from a data warehouse. You can filter the data by year and sales territory region to see different visualizations.")
    st.write("The visualizations include:")
    st.write("- Sales Composition by Territory Over Time")
    st.write("- Data Distribution of Total Sales")
    st.write("- Total Sales Over Time")
    st.write("- Scatter Plot of Product List Price vs. Total Order Quantity")
    st.write("Use the filters on the left sidebar to customize the visualizations.")

# Add footer
def add_footer():
    footer = """
    <div class="footer">
        <p>Created By| <a href="https://www.linkedin.com/in/moch-rezeki-setiawan/"> Moch Rezeki Setiawan </a>© 2024 All Rights Reserved</p>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)

add_footer()
