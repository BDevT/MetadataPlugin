#python3 -m venv venv
#source venv/bin/activate
# python3 python_file.py mark_down_file_folder output_json_file_folder
# python3 main_original.py ../data/markdown_first ../output_json

# Import necessary libraries/modules
import os
import pandas as pd
import argparse
#import markdown_to_json
#import markdown
import json
import re

# Function to convert Markdown content to JSON
def convert_md_to_json(markdown_text):

    # Split the Markdown content into sections based on headings
    sections = re.split(r'#+\s+', markdown_text)
    # Initialize the JSON structure
    json_data = {}

    # Process each section seperately
    for section in sections[1:]:
        section_lines = section.strip().split('\n')
        section_title = section_lines[0]
        section_content = '\n'.join(section_lines[1:])
        
        # If section content contains a table (identified by '|'), convert it to JSON
        if '|' in section_content:
            table_data = []
            rows = section_content.strip().split('\n')
            header = rows[0]
            keys = [cell.strip() for cell in header.split('|')[1:-1]]
            
            # Extract table rows and convert them into JSON format
            for row in rows[1:]:
                values = [cell.strip() for cell in row.split('|')[1:-1]]
                
                row_data = {}
                for i, key in enumerate(keys):
                    if i < len(values):  # Check if 'values' list has enough elements
                        if ',' in values[i]:
                            values[i] = [v.strip() for v in values[i].split(',')]
                        row_data[key] = values[i]
                    else:
                        row_data[key] = None  # Assign None if value is missing
                table_data.append(row_data)

            # Exclude the first row from specific sections
            if section_title == "HIVE testing log" or section_title == "Pulses":  # Fix conditional check
                # Exclude the first row from HIVE testing log
                table_data = table_data[1:]

            json_data[section_title] = table_data
        
        # If section content contains line breaks but no tables, replace line breaks with spaces
        elif '\n' in section_content:
            print("section_content = "+ section_content)
            section_content  = section_content.replace('\n', ' ')  
            json_data[section_title] = section_content 
        else:
            json_data[section_title] = section_content
             
    # Convert JSON data to a formatted JSON string
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

    # Display the JSON string on the console
    #print(json_str)
    return json_str

# Custom JSON Encoder to handle newline characters
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, str):
            # Replace newline characters with spaces
            return obj.replace('\n', ' ')
        return json.JSONEncoder.default(self, obj)

# Function for intermediate conversion from Markdown to JSON    
def intermediate_conversion(md_path, output_dir):
    try:
        # Read Markdown file content
        with open(md_path, 'r') as file:
            file_data = file.read()
        
        # Convert Markdown content to JSON
        json_data = convert_md_to_json(file_data)
        
        # Construct the path for the JSON output file
        json_filename = os.path.splitext(os.path.basename(md_path))[0] + ".json"
        json_path = os.path.join(output_dir, json_filename)
        
        # Save JSON data to a file
        with open(json_path, 'w') as file:
            file.write(json_data)
    except pd.errors.EmptyDataError:
        print(f"Skipped due to no valid data in Markdown: {md_path}")

# Function to convert all Markdown files in a directory to JSON format
def markdown_to_json_in_directory(root_dir, output_dir, extension=".md"):
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    # Traverse through the root directory and its subfolders
    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(extension):
                md_path = os.path.join(foldername, filename)
                intermediate_conversion(md_path, output_dir)

if __name__ == "__main__":
    # Parse command-line arguments for input and output directories
    parser = argparse.ArgumentParser(description="Convert Markdown files in a directory to JSON format.")
    parser.add_argument('input_directory', help="Input directory containing Markdown files.")
    parser.add_argument('output_directory', help="Output directory for JSON files.")
    args = parser.parse_args()
    # Perform Markdown to JSON conversion for all files in the input directory
    markdown_to_json_in_directory(args.input_directory, args.output_directory)
