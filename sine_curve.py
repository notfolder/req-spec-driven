import numpy as np
import matplotlib.pyplot as plt


def draw_sine_wave():
    # 1. Create an array of x values (e.g., from -2*pi to 2*pi)
    x = np.linspace(-2 * np.pi, 2 * np.pi, 400)  # 400 points over the range

    # 2. Calculate the sine wave y values
    y = np.sin(x)

    # 3. Plot the data
    plt.figure(figsize=(10, 6))  # Set figure size for better viewing
    plt.plot(x, y, label="sin(x)", color="blue")

    # 4. Add labels and title for clarity
    plt.title("Sine Curve (sin(x))")
    plt.xlabel("X Axis (Radians)")
    plt.ylabel("Amplitude (sin(x))")

    # 5. Customize the plot grid and legend
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.show()  # Display the plot


if __name__ == "__main__":
    draw_sine_wave()
