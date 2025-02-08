
**2. Interactive Chart Code (`interactive_chart.py`):**

```python
import plotly.graph_objects as go
import numpy as np

# Sample data for demonstration
np.random.seed(42)
x_data = np.arange(100)
y_data = np.random.randn(100).cumsum()

fig = go.Figure(data=[go.Scatter(x=x_data, y=y_data, mode='lines', name='Sample Data')])

fig.update_layout(
    title='Interactive Time Series Chart',
    xaxis_title='Time',
    yaxis_title='Value',
    xaxis=dict(
        rangeslider=dict(
            visible=True
        ),
        type="linear" # or 'date' if x-axis is dates
    ),
    yaxis=dict(
        autorange=True,
        type="linear"
    ),
    hovermode="x unified", # Show hover info for all traces at the same x value
    template="plotly_white" # Choose a clean template
)

# Enable zoom and pan using layout update
fig.update_layout(
    dragmode="zoom", # or 'pan' for panning, 'select' for box selection, 'lasso' for lasso selection
    hovermode="closest"
)

fig.show()
