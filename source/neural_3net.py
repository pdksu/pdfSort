# Define three neurons forming a wedge-like region
def combined_neurons(x, y):
    # Each neuron defines one linear boundary
    n1 = neuron(x, y,  np.sin(np.pi/6), -np.cos(np.pi/6), 0)  # left edge of wedge
    n2 = neuron(x, y, -np.sin(np.pi/6), -np.cos(np.pi/6), 0)  # right edge of wedge
    n3 = neuron(x, y, 0, 1, -1.5)  # bottom edge: y > 1.5
    return 1 if n1 and n2 and n3 else 0  # inside all three

# Apply to all points
predictions = np.array([combined_neurons(x, y) for x, y in zip(x1, x2)])
