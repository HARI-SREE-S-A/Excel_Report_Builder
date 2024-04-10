import dash
from dash import dcc, html, Input, Output
from dash.dash_table import DataTable
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Set up the Google Sheet connection
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('path/to/your/credentials.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("Call Entries updated").sheet1

# Read the data into a pandas DataFrame
data = sheet.get_all_values()
column_names = data.pop(0)
df = pd.DataFrame(data, columns=column_names)

# Define specific sheet names
sheet_names = ["Kavitha", "Meenu", "Ajanya", "AJITH"]
# Create a dictionary to store category data for each sheet
category_data = {}
# Consolidate data from all sheets into a single DataFrame
consolidated_data = pd.DataFrame()
for sheet_name in sheet_names:
    sheet_data = df[df['Sheet'] == sheet_name]
    category_data[sheet_name] = sheet_data
    consolidated_data = pd.concat([consolidated_data, sheet_data], ignore_index=True)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the Dash app
app.layout = html.Div([
    html.H1("Category Distribution"),

    # Date Picker for the dynamic pie chart
    dcc.DatePickerSingle(
        id='date-picker',
        min_date_allowed=consolidated_data['Date'].min(),
        max_date_allowed=consolidated_data['Date'].max(),
        initial_visible_month=consolidated_data['Date'].max(),
        date=consolidated_data['Date'].max()  # Default to the latest date
    ),

    # First pie chart showing consolidated data count for category column in all four sheets
    dcc.Graph(id='consolidated-pie-chart'),

    # Second pie chart which will be dynamic based on selected date
    dcc.Graph(id='dynamic-pie-chart'),

    # Display the interactive table
    html.Div([
        html.H2("Category Wise Data"),
        DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in category_data[next(iter(category_data))].columns],
            data=[],
            export_format='csv',  # Enable exporting to CSV
            sort_action='native',  # Enable native sorting
            filter_action='native',  # Enable native filtering
            page_action='native',  # Enable pagination
            page_size=10,  # Set number of rows per page
            row_selectable='single'  # Allow selecting a single row
        )
    ])
])


# Callback to update the second pie chart and table based on selected date
@app.callback(
    [Output('dynamic-pie-chart', 'figure'),
     Output('table', 'data')],
    [Input('date-picker', 'date'),
     Input('dynamic-pie-chart', 'clickData')]  # Add input for clickData
)
def update_visuals(selected_date, clickData):
    filtered_consolidated_data = consolidated_data[consolidated_data['Date'] == selected_date]

    table_data = []

    for sheet_name, df in category_data.items():
        filtered_sheet_data = df[df['Date'] == selected_date]
        table_data.extend(filtered_sheet_data.to_dict('records'))

    # Dynamic pie chart based on selected date
    dynamic_pie_chart_figure = px.pie(filtered_consolidated_data.groupby('Category').size().reset_index(name='Count'),
                                      values='Count', names='Category', title='Dynamic Category Distribution')

    # Update table data based on clicked category
    if clickData:
        clicked_category = clickData['points'][0]['label']
        table_data = [row for row in table_data if row['Category'] == clicked_category]

    return dynamic_pie_chart_figure, table_data


# Callback to update the first pie chart for consolidated data
@app.callback(
    Output('consolidated-pie-chart', 'figure'),
    [Input('date-picker', 'date')]
)
def update_consolidated_pie_chart(selected_date):
    # Static pie chart for consolidated data (total count)
    consolidated_pie_chart_figure = px.pie(consolidated_data.groupby('Category').size().reset_index(name='Count'),
                                           values='Count', names='Category', title='Consolidated Category Distribution')
    return consolidated_pie_chart_figure


# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
