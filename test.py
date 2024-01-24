import fnmatch

def is_md_file(file_name):
    return fnmatch.fnmatch(file_name, '*.md')

# Example usage
file_name = 'abc.md'

if is_md_file(file_name):
    print(f"{file_name} matches the pattern '*.md', returning True.")
else:
    print(f"{file_name} does not match the pattern '*.md', returning False.")
