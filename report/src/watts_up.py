import pandas as pd # For reading datasets
import seaborn as sns # For beautiful visuals
import matplotlib.pyplot as plt # For visuals
from IPython.display import display # For Pretty print of dataframes
import os #for file system manipulation
import zipfile #for zip extraction

def extract_all_zips(source_dir, dest_dir):
    """
    Extracts all ZIP files found in the source directory and its subdirectories into the destination directory.
    
    :param source_dir: Path to the directory to search for ZIP files.
    :param dest_dir: Path to the directory where ZIP files should be extracted.
    """
    # Ensure the destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f'Created directory: {dest_dir}')
    # Walk through the source directory
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            # Check if the file is a ZIP file
            if file.endswith('.zip'):
                # Construct full file path
                zip_path = os.path.join(root, file)
                # Open the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Extract all the contents into the destination directory
                    zip_ref.extractall(dest_dir)
                    print(f'Extracted {file} into {dest_dir}')

def create_dataframes_dict(base_directory):
    """
    Creates a dictionary of pandas DataFrames from CSV files located in subdirectories.
    Each key in the dictionary is the CSV file name.
    
    :param base_directory: The path to the directory containing the folders with CSV files.
    :return: A dictionary where each key is a combination of the folder name and the CSV file name (without the extension),
             and each value is the corresponding pandas DataFrame.
    """
    # Initialize an empty dictionary to store the dataframes
    dataframes = {}

    # Walk through all directories within the base directory
    for root, dirs, files in os.walk(base_directory):
        for dir_name in dirs:
            # Construct the path to the inside of the folder
            folder_path = os.path.join(root, dir_name)
            # List all CSV files in the current folder
            csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
            # Iterate over all found CSV files
            for csv_file in csv_files:
                # Construct the full path to the CSV file
                csv_file_path = os.path.join(folder_path, csv_file)
                # Read the CSV file into a DataFrame
                df = pd.read_csv(csv_file_path)
                # Create a unique key name combining folder and file name (without extension)
                key_name = f"{os.path.splitext(csv_file)[0]}"
                # Add the DataFrame to the dictionary
                dataframes[key_name] = df

        
    return dataframes

def display_dataframes(dataframes):   
    # Display information for each DataFrame
    print ("There are ", len(dataframes), " Dataframes imported", '\n', '-'*30)
    for name, df in dataframes.items():
        print(f"DataFrame: {name}")
        df.info()  # Display information about the DataFrame
        display(df.head())  # Show the first few rows of the DataFrame
        print("-" * 80)  # Print a separator line

def organize_and_print_dataframes(dataframes_dict):
    """
    Organizes DataFrames by state and prints them out.
    
    :param dataframes_dict: A dictionary where each key is a string combining the type and state,
                            and each value is a DataFrame.
    """
    # Initialize a dictionary to hold data frames categorized by state
    data_by_state = {}

    # Populate the dictionary
    for key, df in dataframes_dict.items():
        # Split the key to separate type and state
        parts = key.split('_')
        state = parts[-1]  # The state abbreviation is at the end
        if state not in data_by_state:
            data_by_state[state] = {}
        data_by_state[state][key] = df  # Store the entire DataFrame under its original key

    # Print the organized DataFrames
    for state in data_by_state.keys():
        print(">>>", f"Dataframes for {state}:")
        for key in data_by_state[state]:
            print(key)
        print("=" * 30, "\n")
    return data_by_state


def get_dataframe_from_state(data_by_state, state, dataframe_key):
    """
    Returns a specified DataFrame from a specified state.
    
    Parameters:
        data_by_state (dict): A dictionary where keys are state names and values are dictionaries of DataFrames.
        state (str): The state from which to retrieve the DataFrame.
        dataframe_key (str): The key corresponding to the DataFrame to retrieve.
        
    Returns:
        pandas.DataFrame: The requested DataFrame.
    """
    # Normalize the state key to ensure consistent case-sensitive matching
    state = state.lower()  # or state.upper() depending on your dictionary keys
    
    # Check if the state exists in the data
    if state in data_by_state:
        # Check if the dataframe_key exists for the state
        if dataframe_key in data_by_state[state]:
            # Return the requested DataFrame
            return data_by_state[state][dataframe_key]
        else:
            print(f"Dataframe key '{dataframe_key}' not found for state '{state}'.")
            return None  # Return None if the DataFrame key doesn't exist
    else:
        print(f"State '{state}' not found.")
        return None  # Return None if the state doesn't exist
    

def convert_columns_to_datetime(df, columns):
    """
    Converts specified columns of a DataFrame to datetime.

    Parameters:
        df (pd.DataFrame): The DataFrame whose columns are to be converted.
        columns (list): A list of column names to be converted to datetime.
    """
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column])

def convert_df_columns_to_datetime(data_by_state, columns_to_convert):
    """
    Applies datetime conversion to specified columns across all DataFrames 
    within a nested dictionary structure.

    Parameters:
        data_by_state (dict): Nested dictionary of DataFrames.
        columns_to_convert (list): List of column names to convert to datetime.
    """
    for state, dfs in data_by_state.items():
        for df_name, df in dfs.items():
            convert_columns_to_datetime(df, columns_to_convert)


def check_column_conversion(df, column_name):
    """
    Checks if a specific column in a DataFrame has been successfully converted to datetime.

    Parameters:
        df (pd.DataFrame): The DataFrame to check.
        column_name (str): The name of the column to check.

    Returns:
        bool: True if the column is successfully converted to datetime, False otherwise.
    """
    return column_name in df.columns and pd.api.types.is_datetime64_any_dtype(df[column_name])

def check_datetime_conversions(data_by_state, columns):
    """
    Checks and prints whether specified columns in each DataFrame within a nested dictionary 
    structure have been successfully converted to datetime objects.

    Parameters:
        data_by_state (dict): Nested dictionary of DataFrames.
        columns (list): List of column names to check for successful datetime conversion.
    """
    for state, dfs in data_by_state.items():
        print(f"State: {state}")
        for df_name, df in dfs.items():
            print(f"DataFrame: {df_name}")
            for column in columns:
                converted = check_column_conversion(df, column)
                print(f"'{column}' converted successfully: {converted}")
            print("-" * 50)  # Print a separator for readability

def print_missing_values_summary(data_by_state):
    """
    Prints the sum of missing values for each DataFrame within a nested dictionary structure.

    Parameters:
        data_by_state (dict): Nested dictionary of DataFrames, categorized by state.
    """
    for state, dfs in data_by_state.items():
        print(f"State: {state}")
        for df_name, df in dfs.items():
            # Calculate the sum of missing values for each column
            missing_values = df.isnull().sum()
            # Calculate total missing values
            total_missing = missing_values.sum()
            # Print the summary
            print(f"DataFrame: {df_name} - Total Missing Values: {total_missing}")
            # Optional: print detailed missing values count for each column
            # Uncomment the following line if detailed info is needed
            # print(missing_values[missing_values > 0])
        print("-" * 50)  # Print a separator for readability
def plot_column_distributions(data_by_state, columns):
    """
    Plots the distribution of specified columns for each DataFrame within a nested dictionary structure.

    Parameters:
        data_by_state (dict): Nested dictionary of DataFrames, categorized by state.
        columns (list): List of column names for which to plot distributions.
    """
    for state, dfs in data_by_state.items():
        for df_name, df in dfs.items():
            for column in columns:
                if column in df.columns:
                    plt.figure(figsize=(10, 6))
                    sns.distplot(df[column].dropna(), kde=True, bins=30)  # dropna() to remove missing values
                    plt.title(f"{column} Distribution in {state} - {df_name}")
                    plt.xlabel(column)
                    plt.ylabel('Density')
                    plt.show()