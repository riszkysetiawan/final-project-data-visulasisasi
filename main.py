import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import base64

# Load secrets
secrets = st.secrets["connections.mydb"]



# Koneksi ke database MySQL
def run_query(query):
    engine = create_engine(f"mysql+pymysql://{secrets['username']}:{secrets['password']}@{secrets['host']}:{secrets['port']}/{secrets['database']}")
    df = pd.read_sql(query, engine)
    return df

# CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Sidebar Filters
selected_years = st.sidebar.multiselect('Select years', [year for year in range(2001, 2005)])
selected_years = list(map(int, selected_years))  # Convert to integers here

# Additional Filters
selected_region = st.sidebar.multiselect('Select Sales Territory Region', 
                                         ['Australia', 'Canada', 'France', 'Germany', 'Northwest', 'Southwest', 'United Kingdom'])

# Filter for scatter plot
price_range = st.sidebar.slider('Select List Price Range', 0, 1000, (0, 1000))

def visualize_sales_composition(selected_region, selected_years):
    query = '''
    SELECT st.SalesTerritoryRegion, YEAR(dt.FullDateAlternateKey) as Year, SUM(fi.SalesAmount) as TotalSales
    FROM factinternetsales fi
    JOIN dimsalesterritory st ON fi.SalesTerritoryKey = st.SalesTerritoryKey
    JOIN dimtime dt ON fi.OrderDateKey = dt.TimeKey
    GROUP BY st.SalesTerritoryRegion, YEAR(dt.FullDateAlternateKey)
    ORDER BY YEAR(dt.FullDateAlternateKey);
    '''
    df = run_query(query)
    
    # filter
    if selected_region:
        df = df[df['SalesTerritoryRegion'].isin(selected_region)]
    if selected_years:
        df = df[df['Year'].isin(selected_years)]
        
    if df.empty:
        st.warning('No data available for the selected filters.')
        return

    df['Year'] = df['Year'].astype(str)  # Ensure year is treated as a category

    # Create stacked column chart
    fig = px.bar(df, x='Year', y='TotalSales', color='SalesTerritoryRegion', 
                 title='Sales Composition by Territory Over Time', 
                 labels={'TotalSales': 'Total Sales', 'Year': 'Year', 'SalesTerritoryRegion': 'Sales Territory Region'},
                 barmode='stack')

    fig.update_layout(xaxis=dict(type='category'))  # Ensure x-axis is treated as categorical

    st.plotly_chart(fig)

    st.markdown("**Sales Composition by Territory Over Time**: This stacked column chart shows the composition of sales by sales territory over time. You can see how the sales contribution from each territory changes over time.")

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

    fig = px.histogram(df, x='TotalSales', nbins=50, title='Data Distribution of Total Sales', marginal="rug")
    fig.update_layout(xaxis_title='Total Sales', yaxis_title='Jumlah Transaksi Dilakukan')
    st.plotly_chart(fig)

    st.markdown("**Data Distribution of Total Sales**: Grafik ini menampilkan distribusi total penjualan. Anda dapat melihat bagaimana penjualan didistribusikan dalam berbagai rentang nilai.")

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

    st.markdown("**Total Sales Over Time**: Grafik ini menunjukkan total penjualan dari waktu ke waktu. Grafik ini membantu Anda untuk memahami tren penjualan selama periode waktu tertentu.")

# Grafik 4
def visualize_scatter_plot(price_range):
    query = '''
    SELECT p.ListPrice, SUM(s.OrderQuantity) AS TotalQuantity
    FROM factinternetsales s
    JOIN dimproduct p ON s.ProductKey = p.ProductKey
    GROUP BY p.ListPrice
    '''
    df = run_query(query)
    
    # Filter by price range
    df = df[(df['ListPrice'] >= price_range[0]) & (df['ListPrice'] <= price_range[1])]

    if df.empty:
        st.warning('No data available for the selected price range.')
        return

    fig = px.scatter(df, x='ListPrice', y='TotalQuantity', color='TotalQuantity', title='Scatter Plot of Product List Price vs. Total Order Quantity')
    fig.update_layout(xaxis_title='List Price', yaxis_title='Total Order Quantity')
    st.plotly_chart(fig)

    st.markdown("**Scatter Plot of Product List Price vs. Total Order Quantity**: Grafik ini menunjukkan hubungan antara harga jual produk dan jumlah total pesanan. Grafik ini membantu Anda memahami bagaimana harga produk mempengaruhi jumlah pesanan yang diterima.")

# Streamlit 
st.title('Dashboard Data Warehouse')

st.header('Sales Composition by Territory Over Time')
visualize_sales_composition(selected_region, selected_years)

st.header('Data Distribution of Total Sales')
visualize_data_distribution()

st.header('Total Sales Over Time')
visualize_total_sales_over_time(selected_years)

st.header('Scatter Plot of Product List Price vs. Total Order Quantity')
visualize_scatter_plot(price_range)

