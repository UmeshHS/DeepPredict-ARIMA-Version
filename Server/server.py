# server.py
from flask import Flask, request, jsonify
import util
import ts_forecast
import traceback

app = Flask(__name__)

# ----- Startup: load model & HPI forecast model once -----
try:
    util.load_saved_artifacts()
except Exception as e:
    print("Error loading artifacts in util.py:", e)
    traceback.print_exc()
    raise

# Fit ARIMA on HPI (this may take a few seconds). If it fails, server still runs.
try:
    ts_forecast.load_hpi_and_fit(csv_path='artifacts/bangalore_hpi.csv', arima_order=(1,1,1))
    print("HPI ARIMA model loaded (or fallback in place).")
except Exception as e:
    print("Warning: ARIMA model not fitted at startup:", e)
    traceback.print_exc()

# ----- API endpoints -----
@app.route('/get_location_names')
def get_location_names():
    try:
        response = jsonify({'locations': util.get_location_names()})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict_home_price', methods=['POST'])
def predict_home_price():
    try:
        data = request.form if request.form else request.get_json(force=True)
        total_sqft = float(data.get('total_sqft'))
        location = data.get('location')
        bhk = int(data.get('bhk'))
        bath = int(data.get('bath'))

        current_price = util.get_estimated_price(location, total_sqft, bhk, bath)
        response = jsonify({'estimated_price': current_price})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        print("predict_home_price error:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/predict_future_price', methods=['POST'])
def predict_future_price():
    try:
        data = request.form if request.form else request.get_json(force=True)
        total_sqft = float(data.get('total_sqft'))
        location = data.get('location')
        bhk = int(data.get('bhk'))
        bath = int(data.get('bath'))
        horizon_months = int(data.get('horizon_months', 12))  # default 12

        # 1) Current price from XGBoost
        current_price = util.get_estimated_price(location, total_sqft, bhk, bath)

        # 2) Market forecast summary (growth rate over horizon, volatility, risk)
        try:
            growth_rate, volatility, risk_label, forecast_series = ts_forecast.get_market_forecast_summary(steps=horizon_months)
        except Exception as e:
            # If something went wrong with forecast, fallback to zero growth and moderate risk
            print("ts_forecast.get_market_forecast_summary error:", e)
            traceback.print_exc()
            growth_rate, volatility, risk_label = 0.0, 0.0, "Moderate"
            forecast_series = None

        # 3) Compute future price as simple multiplier
        future_price = current_price * (1 + growth_rate)

        # 4) Basic prescriptive recommendation
        if risk_label == "Low" and growth_rate > 0.05:
            recommendation = "Buy"
        elif risk_label == "Moderate" and growth_rate > 0.02:
            recommendation = "Consider Hold"
        else:
            recommendation = "Avoid"

        response = jsonify({
            'current_price': round(current_price, 2),
            'future_price': round(future_price, 2),
            'expected_growth_percent': round(growth_rate * 100, 2),
            'volatility': round(volatility, 4),
            'risk': risk_label,
            'recommendation': recommendation
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        print("predict_future_price error:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    print("Starting server...")
    app.run(debug=True)
