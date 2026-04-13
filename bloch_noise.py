"""
Quantum Decoherence Visualised — Bloch Sphere Noise Simulator
Author: Bavanitha Sindhubabu
GitHub: github.com/BavanithaS

Simulates how three quantum noise channels (depolarizing, amplitude damping,
phase damping) degrade a qubit state on the Bloch sphere.
Produces animated GIFs and fidelity-vs-error-rate plots.

Dependencies: qiskit, qiskit-aer, numpy, matplotlib
  pip install qiskit qiskit-aer numpy matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, amplitude_damping_error, phase_damping_error
from qiskit.quantum_info import DensityMatrix, state_fidelity, Statevector


# ─── Bloch vector from density matrix ────────────────────────────────────────

def bloch_vector(dm: DensityMatrix):
    """Extract (x, y, z) Bloch vector from a single-qubit density matrix."""
    rho = np.array(dm.data)
    x = 2 * np.real(rho[0, 1])
    y = 2 * np.imag(rho[1, 0])
    z = np.real(rho[0, 0] - rho[1, 1])
    return np.array([x, y, z])


# ─── Simulate noise on |+⟩ state ─────────────────────────────────────────────

def simulate_noisy_state(noise_type: str, error_rate: float) -> DensityMatrix:
    """
    Prepare |+⟩ state, apply a noisy identity gate, return density matrix.
    noise_type: 'depolarizing' | 'amplitude_damping' | 'phase_damping'
    """
    qc = QuantumCircuit(1)
    qc.h(0)          # |+⟩ = (|0⟩ + |1⟩)/√2
    qc.id(0)         # identity — noise applied here
    qc.save_density_matrix()

    noise_model = NoiseModel()
    if noise_type == "depolarizing":
        error = depolarizing_error(error_rate, 1)
    elif noise_type == "amplitude_damping":
        error = amplitude_damping_error(error_rate)
    elif noise_type == "phase_damping":
        error = phase_damping_error(error_rate)
    else:
        raise ValueError(f"Unknown noise type: {noise_type}")

    noise_model.add_all_qubit_quantum_error(error, ["id"])

    sim = AerSimulator(method="density_matrix", noise_model=noise_model)
    result = sim.run(qc, shots=1).result()
    dm = DensityMatrix(result.data()["density_matrix"])
    return dm


# ─── Compute fidelity sweep ───────────────────────────────────────────────────

def fidelity_sweep(noise_type: str, error_rates: np.ndarray) -> np.ndarray:
    """Compute fidelity vs error rate against ideal |+⟩ state."""
    ideal = DensityMatrix(Statevector.from_label("+"))
    fidelities = []
    for p in error_rates:
        dm = simulate_noisy_state(noise_type, p)
        fidelities.append(state_fidelity(ideal, dm))
    return np.array(fidelities)


# ─── Draw static Bloch sphere ─────────────────────────────────────────────────

def draw_bloch_sphere(ax, alpha=0.08):
    """Draw a wireframe unit sphere."""
    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, np.pi, 20)
    xs = np.outer(np.cos(u), np.sin(v))
    ys = np.outer(np.sin(u), np.sin(v))
    zs = np.outer(np.ones_like(u), np.cos(v))
    ax.plot_wireframe(xs, ys, zs, color="#334155", alpha=alpha, linewidth=0.4)
    # Axes
    for d, label, col in [([1,0,0],[0,0,0], "|+⟩"), ([-1,0,0],[0,0,0], "|−⟩"),
                            ([0,0,1],[0,0,0], "|0⟩"), ([0,0,-1],[0,0,0], "|1⟩")]:
        ax.quiver(0, 0, 0, d[0]*1.25, d[1]*1.25, d[2]*1.25,
                  color="#64748b", linewidth=0.6, arrow_length_ratio=0.07)
        ax.text(d[0]*1.35, d[1]*1.35, d[2]*1.35, label,
                fontsize=7, color="#94a3b8", ha="center")
    ax.set_xlim([-1.4, 1.4]); ax.set_ylim([-1.4, 1.4]); ax.set_zlim([-1.4, 1.4])
    ax.set_axis_off()


# ─── Figure 1: Animated Bloch sphere trajectories ────────────────────────────

NOISE_STYLES = {
    "depolarizing":    {"color": "#f97316", "label": "Depolarizing"},
    "amplitude_damping": {"color": "#22d3ee", "label": "Amplitude Damping"},
    "phase_damping":   {"color": "#a78bfa", "label": "Phase Damping"},
}

def plot_bloch_trajectories(save_gif=True):
    """
    For each noise channel, animate the Bloch vector trajectory as error_rate
    increases from 0 → 1. Saves a GIF and a static PNG.
    """
    error_rates = np.linspace(0, 0.99, 60)

    fig = plt.figure(figsize=(14, 5), facecolor="#0f172a")
    axes = []
    for i, (ntype, style) in enumerate(NOISE_STYLES.items()):
        ax = fig.add_subplot(1, 3, i+1, projection="3d", facecolor="#0f172a")
        axes.append((ax, ntype, style))

    # Precompute all trajectories
    trajectories = {}
    print("Computing Bloch trajectories...")
    for ntype, style in NOISE_STYLES.items():
        vecs = []
        for p in error_rates:
            dm = simulate_noisy_state(ntype, p)
            vecs.append(bloch_vector(dm))
        trajectories[ntype] = np.array(vecs)

    # Static plot (save PNG)
    for ax, ntype, style in axes:
        ax.cla()
        draw_bloch_sphere(ax)
        traj = trajectories[ntype]
        ax.plot(traj[:, 0], traj[:, 1], traj[:, 2],
                color=style["color"], linewidth=2.0, alpha=0.9)
        # Start point
        ax.scatter(*traj[0], color="white", s=40, zorder=5)
        # End point
        ax.scatter(*traj[-1], color=style["color"], s=60, zorder=5, edgecolors="white", linewidth=0.8)
        ax.set_title(style["label"], color="white", fontsize=10, pad=4,
                     fontfamily="monospace")

    fig.suptitle("Qubit Decoherence on the Bloch Sphere  |  |+⟩ state under noise",
                 color="#e2e8f0", fontsize=11, fontfamily="monospace", y=0.98)
    plt.tight_layout()
    plt.savefig("bloch_trajectories.png", dpi=160, bbox_inches="tight",
                facecolor="#0f172a")
    print("Saved: bloch_trajectories.png")

    # Animated GIF
    if save_gif:
        print("Rendering GIF (this takes ~30s)...")
        fig2 = plt.figure(figsize=(14, 5), facecolor="#0f172a")
        anim_axes = []
        quivers = []
        trails = []
        for i, (ntype, style) in enumerate(NOISE_STYLES.items()):
            ax = fig2.add_subplot(1, 3, i+1, projection="3d", facecolor="#0f172a")
            draw_bloch_sphere(ax)
            ax.set_title(style["label"], color="white", fontsize=10, pad=4,
                         fontfamily="monospace")
            anim_axes.append((ax, ntype, style))
            quivers.append(None)
            trails.append(ax.plot([], [], [], color=style["color"], alpha=0.5, linewidth=1.2)[0])

        fig2.suptitle("Qubit Decoherence on the Bloch Sphere  |  |+⟩ state under noise",
                      color="#e2e8f0", fontsize=11, fontfamily="monospace", y=0.98)

        def update(frame):
            artists = []
            for idx, (ax, ntype, style) in enumerate(anim_axes):
                traj = trajectories[ntype]
                vec = traj[frame]
                # Trail
                trails[idx].set_data(traj[:frame+1, 0], traj[:frame+1, 1])
                trails[idx].set_3d_properties(traj[:frame+1, 2])
                artists.append(trails[idx])
                # Current vector quiver — redraw
                if quivers[idx] is not None:
                    quivers[idx].remove()
                quivers[idx] = ax.quiver(0, 0, 0, vec[0], vec[1], vec[2],
                                          color=style["color"], linewidth=2.5,
                                          arrow_length_ratio=0.15, normalize=False)
                artists.append(quivers[idx])
                # Error rate label
                ax.set_xlabel(f"p = {error_rates[frame]:.2f}", color="#94a3b8",
                               fontsize=8, labelpad=2)
            return artists

        ani = animation.FuncAnimation(fig2, update, frames=len(error_rates),
                                       interval=80, blit=False)
        ani.save("bloch_decoherence.gif", writer="pillow", fps=12, dpi=100)
        print("Saved: bloch_decoherence.gif")
    plt.close("all")


# ─── Figure 2: Fidelity vs error rate ────────────────────────────────────────

def plot_fidelity_curves():
    """Plot fidelity F(ρ_noisy, |+⟩) vs error rate for all three channels."""
    error_rates = np.linspace(0, 0.99, 50)

    fig, ax = plt.subplots(figsize=(8, 5), facecolor="#0f172a")
    ax.set_facecolor("#0f172a")

    print("Computing fidelity curves...")
    for ntype, style in NOISE_STYLES.items():
        fids = fidelity_sweep(ntype, error_rates)
        ax.plot(error_rates, fids, color=style["color"], linewidth=2.2,
                label=style["label"])
        # Annotate endpoint
        ax.annotate(f'{fids[-1]:.2f}', xy=(error_rates[-1], fids[-1]),
                    xytext=(-30, 6), textcoords="offset points",
                    color=style["color"], fontsize=8, fontfamily="monospace")

    ax.axhline(0.5, color="#334155", linewidth=0.8, linestyle="--", alpha=0.7)
    ax.text(0.01, 0.51, "F = 0.5 (threshold)", color="#475569",
            fontsize=7.5, fontfamily="monospace")

    ax.set_xlabel("Error rate  p", color="#94a3b8", fontsize=10, fontfamily="monospace")
    ax.set_ylabel("Fidelity  F(ρ, |+⟩)", color="#94a3b8", fontsize=10, fontfamily="monospace")
    ax.set_title("State Fidelity vs Error Rate — three noise channels",
                 color="#e2e8f0", fontsize=11, fontfamily="monospace", pad=12)
    ax.tick_params(colors="#64748b")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])
    ax.legend(facecolor="#1e293b", edgecolor="#334155", labelcolor="white",
              fontsize=9, loc="upper right")
    ax.grid(color="#1e293b", linewidth=0.6)

    plt.tight_layout()
    plt.savefig("fidelity_vs_error.png", dpi=160, bbox_inches="tight",
                facecolor="#0f172a")
    print("Saved: fidelity_vs_error.png")
    plt.close()


# ─── Figure 3: Density matrix heatmaps ───────────────────────────────────────

def plot_density_matrices():
    """
    Show real part of density matrix at p=0, 0.3, 0.6, 0.99
    for depolarizing noise — visualises transition from pure to mixed state.
    """
    error_rates = [0.0, 0.30, 0.60, 0.99]
    fig, axes = plt.subplots(1, 4, figsize=(11, 3), facecolor="#0f172a")
    fig.suptitle("Density Matrix  Re(ρ)  under Depolarizing Noise  |  |+⟩ → mixed state",
                 color="#e2e8f0", fontsize=10, fontfamily="monospace", y=1.02)

    labels = ["|0⟩", "|1⟩"]
    for ax, p in zip(axes, error_rates):
        if p == 0.0:
            ideal = DensityMatrix(Statevector.from_label("+"))
            rho = np.real(np.array(ideal.data))
        else:
            dm = simulate_noisy_state("depolarizing", p)
            rho = np.real(np.array(dm.data))

        im = ax.imshow(rho, cmap="plasma", vmin=-0.5, vmax=0.5)
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
        ax.set_xticklabels(labels, color="#94a3b8", fontsize=9)
        ax.set_yticklabels(labels, color="#94a3b8", fontsize=9)
        ax.set_title(f"p = {p:.2f}", color="#e2e8f0", fontsize=9,
                     fontfamily="monospace")
        ax.set_facecolor("#0f172a")
        for spine in ax.spines.values():
            spine.set_edgecolor("#334155")
        # Annotate values
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{rho[i,j]:.2f}", ha="center", va="center",
                        color="white", fontsize=10, fontfamily="monospace",
                        fontweight="bold")

    plt.colorbar(im, ax=axes[-1], fraction=0.046, pad=0.04).ax.yaxis.set_tick_params(color="#94a3b8")
    plt.tight_layout()
    plt.savefig("density_matrix_evolution.png", dpi=160, bbox_inches="tight",
                facecolor="#0f172a")
    print("Saved: density_matrix_evolution.png")
    plt.close()


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  Quantum Decoherence — Bloch Sphere Visualiser")
    print("  Bavanitha Sindhubabu  |  github.com/BavanithaS")
    print("=" * 55)
    plot_bloch_trajectories(save_gif=True)
    plot_fidelity_curves()
    plot_density_matrices()
    print("\nAll outputs saved. See README for interpretation.")
