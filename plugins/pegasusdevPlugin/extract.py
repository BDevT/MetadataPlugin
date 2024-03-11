"""
This module provides functions to extract information from a Pegasus output file.

The `extractPegasus` function parses the provided file and returns a JSON string containing the extracted data.
"""
import json
import re

def extract_match(pattern, line, cast_type=str, default=None):
    """
    Extracts a match from a regular expression pattern in a given line.

    Args:
        pattern (str): The regular expression pattern to search for.
        line (str): The line of text to search in.
        cast_type (type, optional): The type to cast the extracted value to. Defaults to str.
        default (object, optional): The value to return if no match is found. Defaults to None.

    Returns:
        object: The extracted value (cast to the specified type) if a match is found, otherwise the default value.
    """
    match = re.search(pattern, line)
    return cast_type(match.group(1)) if match else default

def extractPegasus(file_path):
    """
    Extracts information from a Pegasus output file and returns it as a JSON string.

    This function parses the given file, looking for specific keywords and patterns to extract data about
    solution options, statistics, and hardware/software information. The extracted data is then formatted as a JSON object
    and returned.

    Args:
        file_path (str): The path to the Pegasus output file.

    Returns:
        str: A JSON string containing the extracted data.
    """
    data = {
        "Solution Options": [],
        "Stats": []
    }

    with open(file_path, 'r') as file:
        lines = file.readlines()
        solution_options_started = False

        for line in lines:
            # Solution Options
            if "S O L U T I O N   O P T I O N S" in line:
                solution_options_started = True
                solution_option = {
                    "problem_dimensionality": "",
                    "degrees_of_freedom": [],
                    "analysis_type": "",
                    "offset_temperature_from_absolute_zero": 0,
                    "equation_solver": {},
                    "plastic_material_properties_included": False,
                    "newton_raphson_option": "",
                    "globally_assembled_matrix": ""
                }
            elif solution_options_started:
                if "PROBLEM DIMENSIONALITY" in line:
                    solution_option["problem_dimensionality"] = line.split(". . . . . . . . . . . . .")[-1].strip()
                elif "DEGREES OF FREEDOM" in line:
                    # Split the line at 'DEGREES OF FREEDOM' and take the second part, then split by spaces
                    degrees_of_freedom = line.split("DEGREES OF FREEDOM")[-1].strip().split()
                    # Filter out empty strings which may result from multiple spaces
                    solution_option["degrees_of_freedom"] = [dof for dof in degrees_of_freedom if dof and dof != "."]
                elif "ANALYSIS TYPE" in line:
                    solution_option["analysis_type"] = line.split(". . . . . . . . . . . . .")[-1].strip()
                elif "OFFSET TEMPERATURE FROM ABSOLUTE ZERO" in line:
                    solution_option["offset_temperature_from_absolute_zero"] = float(line.split()[-1])
                elif "EQUATION SOLVER OPTION" in line:
                    solution_option["equation_solver"]["option"] = line.split(". . . . . . . . . . . . .")[-1].strip()
                elif "MEMORY SAVING OPTION" in line:
                    solution_option["equation_solver"]["memory_saving_option"] = line.split(". . . . . . . . . .")[-1].strip()
                elif "TOLERANCE" in line:
                    solution_option["equation_solver"]["tolerance"] = line.split(". . . . . . . . . . . . .")[-1].strip()
                elif "PLASTIC MATERIAL PROPERTIES INCLUDED" in line:
                    solution_option["plastic_material_properties_included"] = "YES" in line
                elif "NEWTON-RAPHSON OPTION" in line:
                    solution_option["newton_raphson_option"] = line.split(". . . . . . . . . . . . .")[-1].strip()
                elif "GLOBALLY ASSEMBLED MATRIX" in line:
                    solution_option["globally_assembled_matrix"] = line.split(". . . . . . . . . . . . .")[-1].strip()
                    data["Solution Options"].append(solution_option)
                    solution_options_started = False

            # Stats
            if "Release:" in line:
                stats = {
                    "release_info": {},
                    "execution_info": {},
                    "hardware_info": {},
                    "compiler_info": [],
                    "job_info": {},
                    "performance_metrics": {},
                    "memory_usage": {},
                    "io_metrics": {}
                }
                stats["release_info"] = {
                        "release": extract_match("Release: (.+?) ", line),
                        "build": extract_match("Build: (.+?) ", line),
                        "update": extract_match("Update: (.+?) ", line),
                        "platform": extract_match("Platform: (.+?)$", line)
                    }
            elif "Date Run:" in line:
                stats["execution_info"] = {
                    "date_run": extract_match("Date Run: (.+?) ", line),
                    "time": extract_match("Time: (.+?) ", line),
                    "process_id": extract_match("Process ID: (.+?)$", line, int)
                }
            elif "Operating System:" in line:
                stats["execution_info"]["operating_system"] = {
                    "name": extract_match("Operating System: (.+?)  ", line),
                    "build": extract_match("Build: (.+?)$", line)
                }
            elif "Processor Model:" in line:
                stats["hardware_info"]["processor_model"] = extract_match("Processor Model: (.+?)$", line)
            elif "Total number of cores available" in line:
                stats["hardware_info"]["total_number_of_cores_available"] = extract_match("available : +(.+?)$", line, int)
            elif "Number of physical cores available" in line:
                stats["hardware_info"]["number_of_physical_cores_available"] = extract_match("available : +(.+?)$", line, int)
            elif "Total CPU time for main thread" in line:
                stats["performance_metrics"]["total_cpu_time_main_thread"] = extract_match("= +(.+?) seconds", line, float)
            elif "Total CPU time summed for all threads" in line:
                stats["performance_metrics"]["total_cpu_time_all_threads"] = extract_match("= +(.+?) seconds", line, float)
            elif "Sum of memory used on all processes" in line:
                stats["memory_usage"]["sum_memory_used_all_processes"] = extract_match("= +(.+?) MB", line, float)
            elif "Physical memory available" in line:
                stats["memory_usage"]["physical_memory_available"] = extract_match("available +: +(.+?)$", line)
            elif "Total amount of I/O written to disk" in line:
                stats["io_metrics"]["total_io_written_to_disk"] = extract_match("disk +: +(.+?)$", line)
            elif "Total amount of I/O read from disk" in line:
                stats["io_metrics"]["total_io_read_from_disk"] = extract_match("disk +: +(.+?)$", line)
            elif "+------------------ E N D   A N S Y S   S T A T I S T I C S -------------------+" in line:
                data["Stats"].append(stats)

    return json.dumps(data, indent=4)