import zipfile

def extract_zip(file_path, output_dir):
    with zipfile.ZipFile(file_path, 'r') as z:
        z.extractall(output_dir)
