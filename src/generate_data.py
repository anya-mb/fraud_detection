import pandas as pd
import numpy as np

# Set a random seed for reproducibility
np.random.seed(42)

# Generate sample data
n_samples = 10000

rooms = np.random.randint(1, 6, size=n_samples)
area = np.random.uniform(50, 200, size=n_samples)
floor = np.random.randint(1, 10, size=n_samples)
price = (
    rooms * 50000
    + area * 3000
    + floor * 10000
    + np.random.normal(0, 25000, size=n_samples)
)

# Create a DataFrame
data = pd.DataFrame({"rooms": rooms, "area": area, "floor": floor, "price": price})

# Display the first few rows of the dataframe
print(data.head())

# Save to a CSV file
data.to_csv("../data/house_pricing_data.csv", index=False)
