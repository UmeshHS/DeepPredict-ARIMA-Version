import json
import pickle
import os
import numpy as np

__locations = None
__data_columns = None
__model = None

def get_location_names():
    """
    Returns the list of location names from the loaded columns.json file.
    """
    global __locations
    return __locations

def get_estimated_price(location, sqft, bhk, bath):
    """
    Returns the estimated house price based on input parameters.
    """
    global __data_columns, __model
    location = location.lower().strip()
    try:
        loc_index = __data_columns.index(location)
    except ValueError:
        loc_index = -1  # if location not found

    x = np.zeros(len(__data_columns))
    x[0] = sqft
    x[1] = bath
    x[2] = bhk
    if loc_index >= 0:
        x[loc_index] = 1

    return round(__model.predict([x])[0], 2)

def load_saved_artifacts():
    """
    Loads model and column data from the artifacts folder.
    """
    print("Loading saved artifacts ...start")
    global __data_columns
    global __locations
    global __model

    base_dir = os.path.dirname(__file__)
    columns_path = os.path.join(base_dir, 'artifacts', 'columns.json')
    model_path = os.path.join(base_dir, 'artifacts', 'banglore_home_prices_model.pickle')

    with open(columns_path, 'r') as f:
        data = json.load(f)
        __data_columns = data['data_columns']
        __locations = [col.title() for col in __data_columns[3:]]  # Capitalized names for display

    with open(model_path, 'rb') as f:
        __model = pickle.load(f)

    print("Loading saved artifacts ...done")

# Run directly for quick testing
if __name__ == "__main__":
    load_saved_artifacts()
    print(get_location_names()[:10])  # Show first 10 locations
    print("Predicted price (RT Nagar):", get_estimated_price('r.t. nagar', 1000, 2, 2))
    print("Predicted price (Indiranagar):", get_estimated_price('indiranagar', 1200, 2, 2))
    print("Predicted price (Whitefield):", get_estimated_price('whitefield', 1500, 3, 3))
