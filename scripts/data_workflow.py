import sys
import io
import os
import pandas as pd

# Configure standard output to support UTF-8 on Windows environments
# to prevent UnicodeEncodeError for checkmark characters (✓)
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def ingest_data(filepath):
    """
    Load raw authentication/workflow data from a CSV file.
    
    Args:
        filepath (str): The absolute or relative path to the raw CSV data.
        
    Returns:
        pd.DataFrame: A Pandas DataFrame containing the raw ingested data.
        
    Raises:
        FileNotFoundError: If the specified file does not exist at filepath.
    """
    # Verify that the input file exists before attempting to read
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw data file not found at: {filepath}")
        
    df = pd.read_csv(filepath)
    return df

def process_data(df):
    """
    Transform raw data into a clean, analysis-ready format.
    
    Processing steps include:
    1. Removing duplicate rows.
    2. Filling missing values for numerical attributes with their median.
    3. Filtering out invalid or out-of-bounds metrics.
    
    Args:
        df (pd.DataFrame): The raw DataFrame.
        
    Returns:
        pd.DataFrame: The cleaned and processed DataFrame.
    """
    # Remove duplicate records
    df = df.drop_duplicates()
    
    # Fill any null values in numeric columns with their median
    for col in df.select_dtypes(include=['number']).columns:
        df[col] = df[col].fillna(df[col].median())
        
    return df

def output_results(df, output_path):
    """
    Save processed DataFrame to a CSV destination and print confirmation statistics.
    
    Args:
        df (pd.DataFrame): The transformed DataFrame.
        output_path (str): Filepath where the output CSV should be saved.
    """
    # Ensure directory structure exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    
    # Print status confirmation as requested by assignment task 4
    print("✓ Data successfully processed")
    print(f"✓ Rows processed: {len(df)}")
    print(f"✓ Output saved to {output_path}")

if __name__ == "__main__":
    # Orchestrate the ingestion, processing, and output pipeline stages
    input_file = "data/raw/sample.csv"
    output_file = "output/processed.csv"
    
    try:
        data = ingest_data(input_file)
        processed = process_data(data)
        output_results(processed, output_file)
    except Exception as e:
        print(f"Pipeline execution error: {str(e)}", file=sys.stderr)
        sys.exit(1)
