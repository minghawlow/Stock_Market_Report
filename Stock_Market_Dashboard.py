import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# Set the page width to the maximum available width
st.set_page_config(page_title='Stock Market Report',page_icon=':chart_with_upwards_trend:', layout="wide")

# Add a title to your Streamlit app
st.title('Stock Market Report')

# Read the Stock_Listing.csv file to extract unique company names and their corresponding security codes
df_listing = pd.read_csv("Stock_Listing.csv")

# Create a sidebar input field for choosing a market type
selected_market_type = st.selectbox('Select Market Type', ['All'] + df_listing['Market_Type'].unique().tolist())

# Filter the DataFrame based on the selected market type
if selected_market_type == 'All':
    filtered_df = df_listing
else:
    filtered_df = df_listing[df_listing['Market_Type'] == selected_market_type]

# Create a selectbox for choosing a sector based on the selected market type
available_sectors = filtered_df['Sector'].unique().tolist()
selected_sector = st.selectbox('Select Sector', ['All'] + available_sectors)

# Filter the DataFrame based on the selected sector
if selected_sector == 'All':
    filtered_df = filtered_df
else:
    filtered_df = filtered_df[filtered_df['Sector'] == selected_sector]

# Get the list of available companies based on the selected sector
if selected_sector == 'All':
    available_companies = filtered_df['Company_Name'].unique()
else:
    available_companies = filtered_df['Company_Name'].unique()

# Create a sidebar input field for choosing a company or entering a security code
selection_option = st.radio('Select Option', ['Select Company', 'Select Stock Code'])

selected_company = ""
selected_security_code = ""

if selection_option == 'Select Company':
    # Add a selection dropdown for choosing a company
    selected_company = st.selectbox('Select Company', available_companies)

    # Map the selected company to the corresponding security code with '.KL' appended
    selected_security_code = df_listing[df_listing['Company_Name'] == selected_company]['Security_Code'].values[0] + '.KL'
else:
    # Create a list of security codes as options for the selectbox
    security_codes = df_listing['Security_Code'].unique()

    # Add a selectbox for choosing a security code
    selected_security_code = st.selectbox('Select Security Code', security_codes)

    # Map the selected security code to the corresponding company name
    selected_company = df_listing[df_listing['Security_Code'] == selected_security_code]['Company_Name'].values[0]

    # Append '.KL' to the selected security code
    selected_security_code += '.KL'

# Create a function to get historical stock data based on user selections
def get_historical_stock_data(stock_symbol, period='1mo'):
    data = yf.download(stock_symbol, period='max', interval=period)
    data['Average'] = (data['High'] + data['Low']) / 2
    data['Year'] = data.index.year
    data['Month'] = data.index.month
    return data

# Get historical stock data based on user selections
data = get_historical_stock_data(selected_security_code, '1mo')

# Calculate the minimum and maximum years in the dataset
min_year = data['Year'].min()
max_year = data['Year'].max()

# Create a sidebar input field for selecting a range of years using a slider
selected_years_range = st.slider('Select Year Range', min_value=min_year, max_value=max_year, value=(min_year, max_year))
data = data[(data['Year'] >= selected_years_range[0]) & (data['Year'] <= selected_years_range[1])]

# Create a function to get the latest stock data
def get_latest_stock_data(stock_symbol):
    try:
        data = yf.Ticker(stock_symbol)
        info = data.info
        return info
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

# Get the latest stock data
latest_data = get_latest_stock_data(selected_security_code)

# Calculate the last price, change, and change percent
if latest_data:
    current_price = latest_data.get('currentPrice', 'N/A')
    previous_close = latest_data.get('previousClose', 'N/A')
    
    if current_price != 'N/A' and previous_close != 'N/A':
        last_price = f"RM {current_price:.2f}"  # Assuming the currency is in Malaysian Ringgit (RM)
        price_change = current_price - previous_close
        percent_change = (price_change / previous_close) * 100
        change_color = 'green' if price_change >= 0 else 'red'
        change_text = f"RM {price_change:.2f} ({percent_change:.2f}%)"
    else:
        last_price = 'N/A'
        price_change = 'N/A'
        percent_change = 'N/A'
        change_color = 'black'
        change_text = 'N/A'
    
   # Customize the font size and color using Markdown
    combined_markdown = "**<span style='font-size: 34px; color: black;'>{}</span>**<br><span style='font-size: 20px; color: silver;'>{}</span>".format(latest_data.get('longName', 'N/A'), latest_data.get('symbol', 'N/A'))

    # Display the customized text using st.markdown
    st.markdown(combined_markdown, unsafe_allow_html=True)
    sector = df_listing[df_listing['Company_Name'] == selected_company]['Sector'].values[0]
    st.metric(label=f"Sector", value=sector)
    try:
        st.metric(label=f"Last Price", value=last_price, delta=f"{percent_change:.2f}%")
    except:
        pass

# Create a function to generate the stock price chart using Altair with a gradient
def generate_stock_chart(data):
    if not data.empty:
        filtered_data = data

        # Calculate overall price change
        price_change = filtered_data['Close'].iloc[-1] - filtered_data['Close'].iloc[0]

        # Determine line color based on overall price change
        line_color = 'green' if price_change >= 0 else 'red'

        # Determine gradient color based on overall price change
        gradient_color = 'lightgreen' if price_change >= 0 else 'coral'

        # Your existing code for creating the chart
        chart = alt.Chart(filtered_data.reset_index()).mark_area(
            line={'color': line_color},
            color=alt.Gradient(
                gradient='linear',
                stops=[
                    alt.GradientStop(color='white', offset=0),
                    alt.GradientStop(color=gradient_color, offset=1)
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0
            )
        ).encode(
            x=alt.X('Date:T', title=''),
            y=alt.Y('Close:Q', title='Stock Price'),
        ).properties(
            width=800,
            height=400
        ).configure_axis(
            grid=False
        )

        return chart
    else:
        st.warning(f"No historical data available for {selected_security_code}")

# Plot the stock chart
stock_chart = generate_stock_chart(data)
st.altair_chart(stock_chart, use_container_width=True)

# Display the year range subtitle
subheader_text = f"Year Range: {selected_years_range[0]} - {selected_years_range[1]}"
st.write(subheader_text)

# Function to generate and display the styled table
def display_styled_table(data):
    # Check if data is empty
    if data.empty:
        st.warning(f"No data available for {selected_company} in the selected year range")
    else:
        # Pivot the DataFrame to create the table
        pivot_table = data.pivot(index='Year', columns='Month', values='Average')

        # Sort the DataFrame by 'Year' in descending order
        pivot_table.sort_values(by='Year', ascending=False, inplace=True)

        # Define a function to apply styles for the highest and lowest values in each row
        def highlight_max_min_in_row(s):
            is_max = s == s.max()
            is_min = s == s.min()
            styles = ['background-color: lightgreen' if v else 'background-color: lightcoral' if w else '' for v, w in zip(is_max, is_min)]
            return styles

        # Apply the styles to the pivot table row-wise and format values with 4 decimal places
        styled_table = pivot_table.style.apply(highlight_max_min_in_row, axis=1).format("{:.4f}")

        # Display the styled table
        st.table(styled_table)

        # Add a download button for CSV
        csv_data = download_styled_table_as_csv(pivot_table)
        st.download_button("Download as CSV", csv_data, file_name=f"{selected_company}.csv", key="csv-download")

def download_styled_table_as_csv(pivot_table):
    # Convert the pivot table to CSV format
    csv_data = pivot_table.to_csv(index=True, encoding='utf-8')

    return csv_data

display_styled_table(data)


def get_dividend_table(selected_security_code, selected_years_range):
    # Create a Ticker object
    stock = yf.Ticker(selected_security_code)

    # Get historical market data
    hist = stock.history(period="max")

    # Extract Year, Month, and Quarter from the index
    hist['Year'] = hist.index.year
    hist['Month'] = hist.index.month

    hist = hist[(hist['Year'] >= selected_years_range[0]) & (hist['Year'] <= selected_years_range[1])]

    # Group data by Year, Quarter, and Month and calculate the sum of dividends
    dividends_by_month = hist.groupby(['Year', 'Month'])['Dividends'].sum()
    dividends_by_month = dividends_by_month.reset_index()

    # Pivot the DataFrame to create the table
    pivot_table = dividends_by_month.pivot_table(index=['Year'], columns=['Month'], values='Dividends', aggfunc='sum', fill_value=0)
    pivot_table.sort_values(by='Year', ascending=False, inplace=True)
    # Rename the columns with month names
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    new_columns = [f'{month_names[m-1]}' for m in pivot_table.columns]
    pivot_table.columns = new_columns

    # Calculate the total dividends for each year
    pivot_table = pivot_table.map(lambda x: '' if x == 0.00 else "{:.4f}".format(x))
    pivot_table['Total'] = pivot_table.sum(axis=1)
    
    # Create a styler object
    styler = pivot_table.style

    # Define a function for conditional formatting
    def highlight_non_zero(val):
        if val != '':
            return f'background-color: #BFEFFF'
        return ''

    # Apply the conditional formatting to the entire DataFrame
    styled_table = styler.map(highlight_non_zero)


    # Define CSS style to set equal column widths
    column_width_style = '''
        <style>
            table {
                table-layout: fixed; /* Set the table layout to fixed */
                overflow-x: auto; /* Enable horizontal scrolling */
            }
            th, td {
                width: 10%;  /* You can adjust the width percentage as needed */
                text-align: center;  /* Center-align content */
                white-space: nowrap;  /* Prevent text wrapping */
                overflow: hidden;  /* Hide overflowing content */
                text-overflow: ellipsis;  /* Display ellipsis for long text */
                min-width: 250px; /* Set a minimum width for the columns */
            }
        </style>
    '''

    # Apply the column width style using st.markdown
    st.markdown(column_width_style, unsafe_allow_html=True)

    # Display the styled table
    st.table(styled_table)

    # Add a download button for CSV
    csv_data = download_styled_table_as_csv(pivot_table)
    st.download_button("Download as CSV", csv_data, file_name=f"{selected_company}_dividend_table.csv", key="download_dividend_csv")

def download_styled_table_as_csv(pivot_table):
    # Convert the pivot table to CSV format
    csv_data = pivot_table.to_csv(index=True, encoding='utf-8')

    return csv_data

# Streamlit app
st.subheader('Dividend Table')
dividend_table = get_dividend_table(selected_security_code, selected_years_range)

# Style the header and index of the DataFrame
# Define a CSS style for the table headers
header_style = '''
    <style>
        th {
            background-color: #F8F8FF;
        }
    </style>
'''

# Apply the style using st.markdown
st.markdown(header_style, unsafe_allow_html=True)
 # Apply the styling to the DataFrame


