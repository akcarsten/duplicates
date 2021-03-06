"""Duplicates package to identify duplicate files."""
import os
import hashlib
import pandas as pd


def create_table(folder: str, ext: str = None, pre: bool = False) -> pd.DataFrame:
    """Create a Pandas dataframe with a column 'file' for the path to a file and a
    column 'hash' with the corresponding hash identifier."""
    folder = format_path(folder)
    input_files = filelist(folder, ext=ext)

    if pre is True:
        input_files = preselect(input_files)

    summary_df = pd.DataFrame(columns=['file', 'hash'])

    summary_df['file'] = input_files
    summary_df['hash'] = hashtable(input_files)

    return summary_df


def format_path(file: str) -> str:
    """Format a path according to the systems separator."""
    return os.path.abspath([file.replace('/', os.path.sep)][0])


def filelist(filepath: str, ext: str = None) -> list:
    """ Lists all files in a folder including sub-folders.
    If only files with a specific extension are of interest
    this can be specified by the 'ext' parameter."""
    file_list = []
    for path, _, files in os.walk(filepath):
        for name in files:
            _, extension = os.path.splitext(name)
            if ext is None or extension == ext:
                file_list.append(os.path.join(path, name))

    return file_list


def save_csv(csv_path: str, duplicates: pd.DataFrame) -> None:
    """Save a Pandas dataframe as a csv file."""
    csv_file = os.path.join(csv_path, 'duplicates.csv')
    duplicates.to_csv(csv_file, index=False)


def hashfile(file: str, block_size: int = 65536) -> str:
    """Generate the hash of any file according to the sha256 algorithm."""
    with open(file, 'rb') as message:
        m = hashlib.sha256()
        block = message.read(block_size)
        while len(block) > 0:
            m.update(block)
            block = message.read(block_size)
        digest = m.hexdigest()

    return digest


def hashtable(files: list) -> list:
    """Go through a list of files and calculate their hash identifiers."""
    if isinstance(files, list) is False:
        files = [files]

    hash_identifier = []
    for file in files:
        print(file, end='\r')
        try:  # Avoid crash in case a file name is too long
            hash_identifier.extend([hashfile(file)])
        except OSError:
            hash_identifier.extend(['No hash could be generated'])

    return hash_identifier


def list_all_duplicates(folder: str,
                        to_csv: bool = False,
                        csv_path: str = './',
                        ext: str = None,
                        fastscan: bool = False) -> pd.DataFrame:
    """Go through a folder and find all duplicate files.
    The returned dataframe contains all files, not only the duplicates.
    With the 'to_csv' parameter the results can also be saved in a .csv file.
    The location of that .csv file can be specified by the 'csv_path' parameter.
    To improve performance when handling large files the fastscan parameter
    can be set to True. In this case files are pre-selected based on their size."""
    duplicate_files = create_table(folder, ext, pre=fastscan)
    duplicate_files = duplicate_files[duplicate_files['hash'].duplicated(keep=False)]
    duplicate_files.sort_values(by='hash', inplace=True)

    if to_csv is True:
        save_csv(csv_path, duplicate_files)

    return duplicate_files


def find_duplicates(file: str, folder: str) -> pd.DataFrame:
    """Search a folder for duplicates of a file of interest.
    In contrast to 'list_all_duplicates', this allows
    limiting the search to one particular file."""
    file = format_path(file)
    folder = format_path(folder)

    file_hash = hashtable(file)

    duplicate_files = list_all_duplicates(folder)

    if len(file_hash) == 1:
        file_hash = file_hash[0]

    return duplicate_files[duplicate_files['hash'] == file_hash]


def compare_folders(reference_folder: str, compare_folder: str,
                    to_csv: bool = False, csv_path: str = './', ext: str = None) -> pd.DataFrame:
    """Directly compare two folders of interest and identify duplicates between them.
    With the 'to_csv' parameter the results can also be saved in a .csv file.
    The location of that .csv file can be specified by the 'csv_path' parameter.
    Further the search can be limited to files with a specific extension via the 'ext' parameter."""
    df_reference = create_table(reference_folder, ext)
    df_compare = create_table(compare_folder, ext)

    ind_duplicates = [x == df_reference['hash'] for x in df_compare['hash'].values]
    duplicate_files = df_compare.iloc[ind_duplicates]

    duplicate_files.drop_duplicates(subset='file', inplace=True)

    if to_csv is True:
        save_csv(csv_path, duplicate_files)

    return duplicate_files


def preselect(input_files: list) -> list:
    """Pre-select potential duplicate files based on their size."""
    checked_files = []
    for file in input_files:
        if os.path.isfile(file):
            checked_files.append(file)

    summary_df = pd.DataFrame(columns=['file', 'size'])

    summary_df['file'] = checked_files
    summary_df['size'] = [os.path.getsize(file) for file in checked_files]

    summary_df = summary_df[summary_df['size'].duplicated(keep=False)]

    return summary_df['file'].tolist()
