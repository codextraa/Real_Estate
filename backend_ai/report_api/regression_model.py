import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer


class InvestmentRegressor:
    def __init__(self, min_samples=5):
        self.min_samples = min_samples
        self.features = ["area_sqft", "beds", "baths"]
        self.imputer = SimpleImputer(strategy="median")
        self.model = LinearRegression()

    def clean_data(self, compiled_data):
        """Removes properties without prices and handles missing feature data."""
        if not compiled_data:
            return None

        df = pd.DataFrame(compiled_data)
        # Remove properties without prices
        df = df.dropna(subset=["price"])

        if len(df) < self.min_samples:
            return None

        # Handle missing feature data
        X = self.imputer.fit_transform(df[self.features])
        y = df["price"]

        return X, y

    def calculate_rating(self, compiled_data, property_data):  # pylint: disable=R0914
        """Main entry point to get the 0.0 - 5.0 score."""
        area_sqft = property_data.get("area_sqft")
        beds = property_data.get("beds")
        baths = property_data.get("baths")
        price = property_data.get("price")

        x_y = self.clean_data(compiled_data)

        if x_y is None:
            return 2.5

        X, y = x_y

        # Train the model
        self.model.fit(X, y)

        # Subject and prediction
        subject_X = np.array([[float(area_sqft), int(beds), int(baths)]])
        predicted_price = self.model.predict(subject_X)[0]
        actual_price = float(price)

        # Rating
        price_ratio = predicted_price / actual_price
        raw_rating = min(5.0, max(0.0, price_ratio * 2.5))
        rating = round(raw_rating * 2) / 2

        return float(rating)
