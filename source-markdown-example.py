import pathlib
import shutil
import time

def copy_markdown_files(source_folder):
    source_path = pathlib.Path(source_folder)
    spool_path = pathlib.Path('/tmp/spool')

    # Create /tmp/spool/ if it doesn't exist
    spool_path.mkdir(parents=True, exist_ok=True)

    # Get a list of Markdown files in the source folder
    markdown_files = list(source_path.glob('*.md'))

    for i, markdown_file in enumerate(markdown_files, start=1):
        # Create a folder in /tmp/spool/ for each Markdown file
        markdown_root = spool_path / 'bags'

        time.sleep( 1.0 )
        dest_folder = markdown_root / 'bag{0}'.format( i )
        #dest_folder = markdown_root / f'folder_{i}'
        dest_folder.mkdir(parents=True, exist_ok=True)
       
        print(f"The '{dest_folder.name}' folder is created.")

        # Copy the Markdown file to the destination folder
        shutil.copy(markdown_file, dest_folder)
        print(f"File '{markdown_file.name}' copied to '{dest_folder}'")

if __name__ == "__main__":
    # Replace 'source_folder_path' with the actual path of your source folder
    source_folder_path = 'markdown-folder'
    
    copy_markdown_files(source_folder_path)
