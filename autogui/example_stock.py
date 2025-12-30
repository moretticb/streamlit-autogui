import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# Load dataset
@st.cache
def load_data():
    return pd.read_csv('https://raw.githubusercontent.com/datasets/finance-vix/main/data/vix-daily.csv')

data = load_data()

# Dashboard title
st.title("Finance Analytics Dashboard")

# Display dataset
st.subheader("Dataset Preview")
st.write(data.head())

# Sidebar for user input
st.sidebar.header("Filter Options")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime(data['Date'].min()))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime(data['Date'].max()))

# Filter data
filtered_data = data[(pd.to_datetime(data['Date']) >= start_date) & (pd.to_datetime(data['Date']) <= end_date)]

# Display filtered data
st.subheader("Filtered Dataset")
st.write(filtered_data)

# Visualization
st.subheader("Visualizations")

# Line Chart
st.write("VIX Closing Price Over Time")
fig, ax = plt.subplots()
ax.plot(pd.to_datetime(filtered_data['Date']), filtered_data['VIX Close'], label='VIX Close', color='blue')
ax.set_xlabel("Date")
ax.set_ylabel("VIX Close")
ax.legend()
plt.xticks(rotation=45)
st.pyplot(fig)

# Machine Learning Prediction
st.subheader("Machine Learning Prediction")

# Prepare data
filtered_data['Date'] = pd.to_datetime(filtered_data['Date'])
filtered_data['Date_ordinal'] = filtered_data['Date'].map(lambda x: x.toordinal())
X = filtered_data[['Date_ordinal']]
y = filtered_data['VIX Close']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Display results
st.write("Mean Squared Error:", mean_squared_error(y_test, y_pred))

# Prediction Visualization
st.write("Predicted vs Actual Values")
fig, ax = plt.subplots()
ax.scatter(y_test, y_pred, color='green', label='Predicted vs Actual')
ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], color='red', label='Ideal Fit')
ax.set_xlabel("Actual Values")
ax.set_ylabel("Predicted Values")
ax.legend()
st.pyplot(fig)
