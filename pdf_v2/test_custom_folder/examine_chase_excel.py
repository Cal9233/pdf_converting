import pandas as pd
import os

# Path to the Chase Excel file from Older_program
excel_path = "/var/www/cal.lueshub.com/pdf_converting/Older_program/Excel/Chase_Combined_20250603_105445.xlsx"

if os.path.exists(excel_path):
    # Read the Excel file
    df = pd.read_excel(excel_path)
    
    print("=== Chase Excel File Structure ===")
    print(f"Columns: {list(df.columns)}")
    print(f"Total rows: {len(df)}")
    print(f"\n=== First 10 rows ===")
    print(df.head(10).to_string())
    
    print(f"\n=== Name distribution ===")
    name_counts = df['Name'].value_counts()
    for name, count in name_counts.items():
        print(f"{name}: {count} transactions")
    
    print(f"\n=== Sample of different cardholders ===")
    for name in df['Name'].unique():
        sample = df[df['Name'] == name].head(3)
        print(f"\n--- {name} ---")
        print(sample[['Date', 'Merchant', 'Amount']].to_string(index=False))
else:
    print(f"File not found: {excel_path}")