# gradient
import numpy as np
from matplotlib import pyplot as plt

coords = np.linspace(-2,2,101)
skip = 5
X, Y = np.meshgrid(coords[::skip], coords[::skip])
R = np.sqrt(X**2 + Y**2)
Z = np.exp(-R**2)
x, y = np.meshgrid(coords, coords)
r = np.sqrt(x**2 + y**2)
z = np.exp(-r**2)

ds = coords[skip] - coords[0]
dX, dY = np.gradient(Z, ds)

plt.contour(x, y, z, 25)
plt.set_cmap('autumn')
plt.show()