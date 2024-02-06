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

        # Remove ° character from section lines
        section_lines = [line.replace('°', '') for line in section_lines]

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
            section_content  = section_content.replace('\n', ' ')  
            json_data[section_title] = section_content 
        else:
            json_data[section_title] = section_content
             
    # Convert JSON data to a formatted JSON string
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

    # Display the JSON string on the console
    return json_str