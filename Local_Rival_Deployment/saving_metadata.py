import os
import pandas as pd

# =========================
# 📊 EXCEL TRACKER LOGIC (PANDAS VERSION)
# =========================
def save_metadata_to_excel(final_function_name, metadata, filename="Generated_Functions_Tracker.xlsx"):
    """Creates an Excel file if it doesn't exist and appends a new row using Pandas."""
    
    # 1. Create a dictionary for your new row (Pandas needs lists for values)
    new_data = {
        "Published": ["No"],
        "Function Name": [final_function_name],
        "Tool Type": ["Function"],
        "Runtime": ["Python"],
        "Category": [metadata.category_name],
        "Sector": [metadata.sector_name],
        "Organization": ["Agent Foundry"],
        "Description": [metadata.short_description],
        "Tags": [", ".join(metadata.tags)]
    }

    # 2. Convert the dictionary into a Pandas DataFrame
    new_df = pd.DataFrame(new_data)

    # 3. Check if file exists to decide whether to append or create new
    if not os.path.exists(filename):
        # Create a brand new file with headers
        new_df.to_excel(filename, index=False)
    else:
        # Read the existing Excel file
        existing_df = pd.read_excel(filename)
        
        # Merge the old data with the new row
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Overwrite the file with the updated data
        updated_df.to_excel(filename, index=False)

    return filename