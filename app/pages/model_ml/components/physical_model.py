import numpy as np
from scipy.optimize import curve_fit


class PhysicalModel:
    def __init__(self, model_type='NL'):
        self.model_type = model_type
        self.params = None

    def _linear_irradiance(self, X, a, b):
        E, _ = X            
        return a + b * E

    def _linear_weather(self, X, a, b, c, d, e):
        E, T = X                   
        return a + b * E + c * T   

    def _nonlinear(self, X, a, b, c, d):
        E, T = X 
        return a * E * (1 - b * (T + E / 800 * (c - 20) - 25) - d * np.log(E + 1e-10))

    def fit(self, X, y):
        if self.model_type == 'LI':
            initial_params = [0.0, 1.0]
            self.params, _ = curve_fit(self._linear_irradiance, X, y, initial_params, maxfev=5000)
        elif self.model_type == 'LW':
            initial_params = [0.0, 1.0, 0.0, 0.0, 0.0]
            self.params, _ = curve_fit(self._linear_weather, X, y, initial_params, maxfev=5000)
        elif self.model_type == 'NL':
            initial_params = [1.0, 0.0, -1.0e4, -1.0e-1]
            self.params, _ = curve_fit(self._nonlinear, X, y, initial_params, maxfev=5000)
        else:
            raise ValueError("Invalid model type. Choose 'LI', 'LW', or 'NL'.")

    def predict(self, X):
        if self.params is None:
            raise ValueError("Model not fitted. Call 'fit' before making predictions.")

        if self.model_type == 'LI':
            return self._linear_irradiance(X, *self.params)
        elif self.model_type == 'LW':
            return self._linear_weather(X, *self.params)
        elif self.model_type == 'NL':
            return self._nonlinear(X, *self.params)
