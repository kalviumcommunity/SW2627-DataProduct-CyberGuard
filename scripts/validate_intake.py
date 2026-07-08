import os
import json
import pandas as pd
import chardet
from datetime import datetime

def validate_file_exists(filepath):
    """Check if file exists and is non-empty."""
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"
    
    if os.path.getsize(filepath) == 0:
        return False, f"File is empty: {filepath}"
    
    return True, "File exists and has content"

def validate_file_format(filepath, allowed_formats=['csv', 'json', 'xlsx']):
    """Check if file extension is supported."""
    extension = filepath.split('.')[-1].lower()
    
    if extension not in allowed_formats:
        return False, f"Unsupported format: {extension}. Allowed: {allowed_formats}"
    
    return True, f"Format valid: {extension}"

def validate_schema(df, expected_columns):
    """Validate that DataFrame has all expected columns."""
    missing = set(expected_columns) - set(df.columns)
    extra = set(df.columns) - set(expected_columns)
    
    issues = []
    if missing:
        issues.append(f"Missing columns: {missing}")
    if extra:
        issues.append(f"Unexpected columns: {extra}")
    
    if not issues:
        return True, f"Schema valid: {len(df.columns)} columns present"
    return False, " | ".join(issues)

def detect_encoding(filepath):
    """Detect file encoding with confidence."""
    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read(10000))
    
    encoding = result.get('encoding', 'utf-8')
    confidence = result.get('confidence', 0)
    
    return encoding, f"Detected: {encoding} (confidence: {confidence:.1%})"

def capture_dataset_stats(filepath, df):
    """Log row count and file size."""
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    row_count = len(df)
    col_count = len(df.columns)
    
    return {
        'rows': row_count,
        'columns': col_count,
        'file_size_mb': round(file_size_mb, 5),
        'bytes': os.path.getsize(filepath)
    }

def generate_intake_report(filepath, expected_columns):
    """Generate complete intake validation report."""
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'filepath': filepath,
        'validations': {}
    }
    
    # Check existence
    file_exists, msg = validate_file_exists(filepath)
    report['validations']['file_exists'] = msg
    if not file_exists:
        return report
    
    # Check format
    format_valid, msg = validate_file_format(filepath)
    report['validations']['format'] = msg
    if not format_valid:
        return report
    
    # Load data for remaining checks
    df = pd.read_csv(filepath)
    
    # Check schema
    schema_valid, msg = validate_schema(df, expected_columns)
    report['validations']['schema'] = msg
    
    # Check encoding
    encoding, msg = detect_encoding(filepath)
    report['validations']['encoding'] = msg
    
    # Capture statistics
    stats = capture_dataset_stats(filepath, df)
    report['statistics'] = stats
    
    # Save report to file
    with open('output/intake_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report

if __name__ == "__main__":
    filepath = "data/raw/sample.csv"
    expected_columns = [
        "customer_id",
        "customer_name",
        "transaction_amount",
        "transaction_date"
    ]
    report = generate_intake_report(filepath, expected_columns)
    print("Report generated successfully:")
    print(json.dumps(report, indent=2))
