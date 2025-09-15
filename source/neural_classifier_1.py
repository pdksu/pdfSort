import numpy as np
import matplotlib.pyplot as plt

# Create 2D data points
np.random.seed(1)
n = 150
x1 = np.random.uniform(-5, 5, n)
x2 = np.random.uniform(-5, 5, n)

labels = np.where(x2 > 0.5 * x1 + 1, 1, 0)

# Define a step neuron
def neuron(x1, x2, w1, w2, b):
    return 1 if w1 * x1 + w2 * x2 + b > 0 else 0

# <<< STUDENTS EDIT THIS >>>
w1 = 0.5
w2 = 0.5
b = -1
# <<< ------------------- >>>

# Predict with neuron
predictions = np.array([neuron(x, y, w1, w2, b) for x, y in zip(x1, x2)])

# Plot
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(x1[labels == 0], x2[labels == 0], color='lightgray', label='True: 0')
ax.scatter(x1[labels == 1], x2[labels == 1], color='black', label='True: 1', marker='x')
ax.scatter(x1[predictions != labels], x2[predictions != labels],
           facecolors='none', edgecolors='red', s=60, label='Wrong')

# Decision boundary
x_vals = np.linspace(-5, 5, 200)
y_vals = -(w1 * x_vals + b) / w2
ax.plot(x_vals, y_vals, 'b--', label='Neuron boundary')

ax.set_xlabel("x1")
ax.set_ylabel("x2")
ax.set_title("Step Neuron: Try to Classify Points")
ax.legend()
ax.set_aspect('equal')
ax.grid(True)
plt.tight_layout()
plt.show()
