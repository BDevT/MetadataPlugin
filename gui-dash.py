import json
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import os
import base64

from plugins.pegasusdevPlugin.extract import extractPegasus

# Define the initial directory to display files from
INITIAL_DIR = 'data/pegasus'

# Initialize the Dash app with Bootstrap styling
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app using Dash HTML and Bootstrap components
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("PEGASUS Ingestor", className="text-center mb-4"), width=12)),
    
    dbc.Row(dbc.Col(dcc.Dropdown(id='file-dropdown', multi=False, placeholder="Select a file", className="mb-3"), width=12)),
    
    dbc.Row([
        dbc.Col(html.H5("File Content", className="mt-3 mb-2"), width=12),
        dbc.Col(html.Div(id='file-content', className="border p-3", style={'max-height': '300px', 'overflow-y': 'scroll'}), width=12),
    ]),
    
    dbc.Row([
        dbc.Col(html.H5("Metadata", className="mt-4 mb-2"), width=12),
        dbc.Col(dcc.Textarea(id='metadata-content', className="border p-3", style={'width': '100%', 'height': '300px'}), width=12),
    ]),
    
    dbc.Row(
        dbc.Col(
            html.Button('Submit', id='submit-button', n_clicks=0, className="btn btn-primary btn-lg rounded-pill"),
            width={"size": 6, "offset": 6}  # Adjust the size and offset as needed to control the button's width and position
        ),
        justify="center"  # This will center the column within the row
    ),
    
    dbc.Row(dbc.Col(html.Div(id='submit-feedback', className="text-center"), width=12)),  # For submit feedback
    
    dbc.Row(dbc.Col(html.Div(id='current-path', style={'display': 'none'}, children=INITIAL_DIR), width=12))
], fluid=True, className="py-3")

@app.callback(
    Output('file-content', 'children'),
    [Input('file-dropdown', 'value')],
    [State('current-path', 'children')]
)
def update_file_content(selected_file, current_path):
    if selected_file:
        file_path = os.path.join(current_path, selected_file)
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                return html.Pre(content, style={'white-space': 'pre-wrap'})
        except Exception as e:
            return f"Error reading file: {e}"
    return "Select a file to view its content."

# Function to extract metadata from .out files
def extract_metadata_from_out(file_path):
    # Static metadata information
    jsonOut = {
        "owner": "PEGASUS",
        "owner_group": "PEGASUS",
        "investigator": "PEGASUS",
        "contact_email": "pegasus@ukaea.uk",
        "source_folder": "path/to/data",  # Consider using the actual path or a method to determine it dynamically
        "input_datasets": ["path/to/data"],  # Consider populating this list dynamically based on the file or related data
        "used_software": ["ANSYS Mechanical"],
        "creation_time": "2021-01-01T00:00:00Z",  # Consider dynamically generating this based on the file's properties or current time
        "type": "derived"
    }

    # Extract additional metadata from the file using the extractPegasus function
    # Ensure the extractPegasus function returns a JSON string suitable for json.loads
    extracted_meta = extractPegasus(file_path)  # This should be defined in your plugins.pegasusdevPlugin.extract module

    # Parse the extracted metadata and add it under the 'meta' key
    try:
        jsonOut["meta"] = json.loads(extracted_meta)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from 'meta' field: {e}")
        jsonOut["meta"] = {"error": "Failed to decode JSON from extractPegasus output"}

    return jsonOut

# Callback function to update the file dropdown and to populate it on initial load
@app.callback(
    Output('file-dropdown', 'options'),
    Input('current-path', 'children')
)
def update_file_list(current_path):
    files = [f for f in os.listdir(current_path) if os.path.isfile(os.path.join(current_path, f))]
    options = [{'label': f, 'value': f} for f in files]
    return options

# Callback function to display the content of the selected file and populate the metadata textarea
@app.callback(
    Output('metadata-content', 'value'),
    [Input('file-dropdown', 'value')],
    [State('current-path', 'children')]
)
def update_metadata_view(selected_file, current_path):
    if selected_file and selected_file.endswith('.out'):
        file_path = os.path.join(current_path, selected_file)
        metadata_dict = extract_metadata_from_out(file_path)
        formatted_metadata = json.dumps(metadata_dict, indent=4)
        return formatted_metadata
    return ""

# Callback for the submit button
@app.callback(
    Output('submit-feedback', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('metadata-content', 'value')]
)
def submit_metadata(n_clicks, metadata):
    if n_clicks > 0:
        # Implement the logic for handling the submitted metadata here
        # This could involve saving the edited metadata back to a file, processing it, etc.
        return "Metadata submitted successfully."
    return ""

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
