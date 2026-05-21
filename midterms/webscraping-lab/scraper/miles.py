from bs4 import BeautifulSoup
import pandas as pd
import re
 
# Load the HTML file
with open("../Starlink.html", "r", encoding="utf-8") as file:
    html_content = file.read()
 
# Parse HTML
soup = BeautifulSoup(html_content, "html.parser")
 
# Find all bar elements in the graph
bars = soup.find_all("rect", class_="MuiBarElement-root")
 
# Extract bar heights
heights = []
for bar in bars:
    height = bar.get("height")
 
    if height:
        heights.append(float(height))
 
# Generate day labels
days = list(range(1, len(heights) + 1))
 
# Create dataframe
usage_data = pd.DataFrame({
    "Day": days,
    "Data_Usage_Value": heights
})
 
# Save to CSV
usage_data.to_csv("data_usage.csv", index=False)
 
print("CSV file created successfully!")
print(usage_data)