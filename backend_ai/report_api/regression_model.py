import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer
from .utils import (
    generate_price_score,
    generate_space_efficiency,
    generate_bed_score,
    generate_bath_score,
)


class InvestmentRegressor:
    def __init__(self, avg_price, avg_pps, avg_beds, avg_baths, min_samples=10):
        self.avg_price = avg_price
        self.avg_pps = avg_pps
        self.avg_beds = avg_beds
        self.avg_baths = avg_baths
        self.avg_sqft = avg_price / avg_pps
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
        area_sqft = float(property_data.get("area_sqft"))
        beds = int(property_data.get("beds"))
        baths = int(property_data.get("baths"))
        price = float(property_data.get("price"))

        x_y = self.clean_data(compiled_data)

        if x_y is None or price == 0 or area_sqft == 0 or beds == 0 or baths == 0:
            return 2.5, {}

        X, y = x_y

        # Train the model
        self.model.fit(X, y)

        # Subject and prediction
        subject_X = np.array([[area_sqft, beds, baths]])
        predicted_price = self.model.predict(subject_X)[0]

        price_score, price_remarks = generate_price_score(price, predicted_price)

        pps_score, pps_remarks = generate_space_efficiency(
            price, area_sqft, self.avg_pps
        )

        bed_final, bed_count_score, space_worth_bed, bed_remarks = generate_bed_score(
            beds, area_sqft, price, predicted_price, self.avg_beds, self.avg_sqft
        )

        (
            bath_final,
            bath_ratio_score,
            space_worth_bath,
            bath_price_worth,
            bath_remarks,
        ) = generate_bath_score(
            baths,
            beds,
            area_sqft,
            price,
            predicted_price,
            self.avg_baths,
            self.avg_sqft,
        )

        # Price Volatility
        pps_series = y / X[:, 0]
        volatility = pps_series.std() / pps_series.mean()
        market_stability = -0.6 if volatility > 0.15 else 0.3

        # Model layout score
        layout_score = -0.1 if price > predicted_price else 0.1

        breakdown = {
            "predicted_price": predicted_price,
            "price_score": price_score,
            "price_remarks": price_remarks,
            "pps_score": pps_score,
            "pps_remarks": pps_remarks,
            "bed_count_score": bed_count_score,
            "space_worth_bed": space_worth_bed,
            "bed_final": bed_final,
            "bed_remarks": bed_remarks,
            "bath_ratio_score": bath_ratio_score,
            "bath_price_worth": bath_price_worth,
            "space_worth_bath": space_worth_bath,
            "bath_final": bath_final,
            "bath_remarks": bath_remarks,
            "market_stability": market_stability,
            "layout_score": layout_score,
        }

        total_score = (
            price_score
            + pps_score
            + bed_final
            + bath_final
            + market_stability
            + layout_score
        )
        final_rating = round(min(5.0, max(0.0, total_score)) * 2) / 2

        return float(final_rating), breakdown
