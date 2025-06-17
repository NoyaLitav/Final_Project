import pandas as pd

# Load the DataFrame
file_path = 'path_to_your_file.csv'
parkinghistory = pd.read_csv(file_path)

# Drop rows with missing values in 'final_choice' column
parkinghistory_cleaned = parkinghistory.dropna(subset=['final_choice'])

# Save the cleaned DataFrame to a new file
cleaned_file_path = 'path_to_your_cleaned_file.csv'
parkinghistory_cleaned.to_csv(cleaned_file_path, index=False)

print(f'Cleaned file saved to {cleaned_file_path}')
