from flask import Flask, render_template, request, flash, redirect, url_for
import mysql.connector
import plotly.express as px
import pandas as pd

app = Flask(__name__)
app.secret_key = b'\xf0\xf1s\x9cZ\x11Oa\x81\xc7\xfbU;\x8d\x03\xec$+\x8f1\xf0P\x0eI'  # Secret key for flash messages

# MySQL connection settings
db_config = {
    'host': 'localhost',
    'user': 'root',  # Replace with your MySQL username
    'password': 'rkarthih279@',  # Replace with your MySQL password
    'database': 'carbon_emission'  # Replace with your database name
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_option = request.form.get('selection')  # Get the selected option
        print(f"Selected Option: {selected_option}")  # Debugging output

        if selected_option == 'calculator':
            return redirect(url_for('calculator'))
        elif selected_option == 'view_all_calculations':
            return redirect(url_for('view_all_calculations'))
        elif selected_option == 'top_3_emissions':
            return redirect(url_for('top_3_emissions'))
        elif selected_option == 'graph_emissions':
            return redirect(url_for('graph_emissions'))
        else:
            flash("Invalid selection. Please choose a valid option.")
            return redirect(url_for('index'))

    return render_template('home.html')

# Route for the calculator form and emissions calculation
@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if request.method == 'POST':
        # Getting user inputs from the form
        name = request.form['name']
        electricity = float(request.form['Electricity'])
        petrol = float(request.form['Petrol'])
        diesel = float(request.form['Diesel'])
        wastewater = float(request.form['Wastewater'])
        gas = float(request.form['Gas'])

        # Emission factors
        electricity_factor = 0.404  # kg CO₂ per kWh
        petrol_factor = 2.31  # kg CO₂ per liter
        diesel_factor = 2.68  # kg CO₂ per liter
        wastewater_factor = 0.7  # kg CO₂ per cubic meter
        gas_factor = 2.0  # kg CO₂ per cubic meter

        # Emission calculations
        electricity_emissions = electricity * electricity_factor
        petrol_emissions = petrol * petrol_factor
        diesel_emissions = diesel * diesel_factor
        wastewater_emissions = wastewater * wastewater_factor
        gas_emissions = gas * gas_factor

        # Total emissions
        total_emissions = electricity_emissions + petrol_emissions + diesel_emissions + wastewater_emissions + gas_emissions

        # Save the result in the MySQL database
        save_result(name, electricity, petrol, diesel, wastewater, gas, total_emissions)

        # Return the result to the user
        return render_template('calc.html', total_emissions=total_emissions, name=name)

    return render_template('calc.html')

def save_result(name, electricity, petrol, diesel, wastewater, gas, total_emissions):
    # Establish connection to MySQL
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # SQL query to insert data
    cursor.execute("""
        INSERT INTO emissions (name, electricity, petrol, diesel, wastewater, gas, total_emission) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (name, electricity, petrol, diesel, wastewater, gas, total_emissions))

    conn.commit()
    cursor.close()
    conn.close()

@app.route('/view_all_calculations')
def view_all_calculations():
    calculations = get_all_calculations()
    return render_template('view.html', calculations=calculations)

def get_all_calculations():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM emissions")
    calculations = cursor.fetchall()
    cursor.close()
    conn.close()
    return calculations

@app.route('/top_3_emissions')
def top_3_emissions():
    top_3_emissions = get_top_3_emissions()
    return render_template('top3.html', top_3_emissions=top_3_emissions)

def get_top_3_emissions():
    global_standard = 309.18  # Example standard, change as needed
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, total_emission FROM emissions ORDER BY total_emission DESC LIMIT 3")
    top_3 = cursor.fetchall()
    for entry in top_3:
        entry['comparison'] = 'Above Standard' if entry['total_emission'] > global_standard else 'Below Standard'
    cursor.close()
    conn.close()
    return top_3

@app.route('/graph_emissions')
def graph_emissions():
    # Choose a chart type based on a query parameter
    chart_type = request.args.get('chart', 'line')  # Default to line chart
    graph = get_emissions_graph(chart_type)
    return render_template('graph.html', graph=graph)

def get_emissions_graph(chart_type='line'):
    # Connect to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Execute query to fetch emissions data
    cursor.execute("SELECT * FROM `normalized_historical_emissions-2`")
    data = cursor.fetchall()
    df = pd.DataFrame(data)

    # Generate different graphs based on the chart_type parameter
    if chart_type == 'line':
        fig = px.line(
            df, x='Year', y='Emissions', color='Country', line_group='Sector',
            title='Historical Carbon Emissions by Country and Sector',
            labels={'Emissions': 'CO₂ Emissions (kg)', 'Year': 'Year'},
            template='plotly_dark'
        )
        fig.update_layout(width=950, height=500)
        
    elif chart_type == 'bar':
        fig = px.bar(
            df, x='Year', y='Emissions', color='Country', barmode='stack',
            title='Carbon Emissions by Country and Year',
            labels={'Emissions': 'CO₂ Emissions (kg)', 'Year': 'Year'},
            template='plotly_dark'
        )
        fig.update_layout(width=950, height=500)
        
    elif chart_type == 'pie':
        # Filter for a specific year for a snapshot comparison
        df_filtered = df[df['Year'] == df['Year'].max()]  # Latest year

        # Define the categories you're interested in for the pie chart
        emission_sources = ['Total fossil fuels and cement', 'Coal', 'Oil', 'Gas', 'Cement', 'Gas flaring']

        # Filter the dataframe to only include the rows for these sources
        df_filtered_sources = df_filtered[df_filtered['Sector'].isin(emission_sources)]
        
        # Create the pie chart
        fig = px.pie(
            df_filtered_sources, names='Sector', values='Emissions',
            title=f'Carbon Emissions by Source in {df_filtered["Year"].max()}',
            labels={'Emissions': 'CO₂ Emissions (kg)', 'Emission_Source': 'Source'},
            template='plotly_dark'
        )
        fig.update_layout(width=950, height=500)
        
    elif chart_type == 'scatter':
        fig = px.scatter(
            df, x='Year', y='Emissions', color='Country', symbol='Sector',
            title='Emissions Over Time by Country and Sector',
            labels={'Emissions': 'CO₂ Emissions (kg)', 'Year': 'Year'},
            template='plotly_dark'
        )
        fig.update_layout(width=950, height=500)

    elif chart_type == 'area':
        fig = px.area(
            df, x='Year', y='Emissions', color='Country', line_group='Sector',
            title='Accumulated Carbon Emissions by Country',
            labels={'Emissions': 'CO₂ Emissions (kg)', 'Year': 'Year'},
            template='plotly_dark'
        )
        fig.update_layout(width=950, height=500)

    else:
        fig = px.line(  # Fallback to line if chart_type is unrecognized
            df, x='Year', y='Emissions', color='Country', line_group='Sector',
            title='Historical Carbon Emissions by Country and Sector',
            labels={'Emissions': 'CO₂ Emissions (kg)', 'Year': 'Year'},
            template='plotly_dark'
        )
        fig.update_layout(width=950, height=00)

    # Render the figure to HTML
    graph = fig.to_html(full_html=False)

    # Close database connections
    cursor.close()
    conn.close()

    return graph


if __name__ == '__main__':
    app.run(debug=True)
