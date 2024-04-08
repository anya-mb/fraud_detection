from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib
import pandas as pd

# Load the data
data = pd.read_csv("../data/house_pricing_data.csv")

X = data[["rooms", "area", "floor"]]
y = data["price"]

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train a linear regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Save the trained model
joblib.dump(model, "../lambda/calculate_prediction/house_price_model.pkl")
