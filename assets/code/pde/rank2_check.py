# === TECT VERSION HEADER BEGIN ===
# Theory tag    : Math56-Addendum-v2p4-2026-04-20
# Regime        : Brazovskii (lambda<0, gamma>0 sizeable)
# Module version: v1.0
# Sync doc      : /Contents/docs/status/TECT-Theory-Code-Sync.md
# Last synced   : 2026-04-20
# Notes         : Code is version-locked to the above theory tag.
#                 The module-version field tracks the file's own API
#                 generation (filename = <module>_v<N>.py); the theory
#                 tag is global. Re-run PDE/stamp_version_headers.py
#                 after any tag bump or version-table edit.
# === TECT VERSION HEADER END ===
import numpy as np

psi = np.load('rank2_D0_1em4\\Psi_corr.npy')
print('shape:', psi.shape)
print('max|psi|:', np.max(np.abs(psi)))

L, grid = 16.0, 64
dk = 2 * np.pi / L

kvecs, fam = [], []
for s1 in [+1,-1]:
    for s2 in [+1,-1]:
        kvecs.append([0,       s1*dk, s2*dk]); fam.append(0)
        kvecs.append([s1*dk,   0,     s2*dk]); fam.append(1)
        kvecs.append([s1*dk,   s2*dk, 0    ]); fam.append(2)
kvecs = np.array(kvecs)
fam   = np.array(fam)

n_int = psi.shape[0]
psi_k = np.array([np.fft.fftn(psi[mu]) / grid**3 for mu in range(n_int)])

A = np.zeros((n_int, 12), dtype=complex)
for j, kv in enumerate(kvecs):
    nx = int(round(kv[0] / dk)) % grid
    ny = int(round(kv[1] / dk)) % grid
    nz = int(round(kv[2] / dk)) % grid
    A[:, j] = psi_k[:, nx, ny, nz]

_, s_all, _ = np.linalg.svd(A, full_matrices=False)
print('Global SVD s =', np.round(s_all, 6))
print('Global rank  =', np.sum(s_all > 1e-6 * s_all[0]))

for alpha in range(3):
    mask = fam == alpha
    _, sa, _ = np.linalg.svd(A[:, mask], full_matrices=False)
    print(f'F{alpha}: rank={np.sum(sa > 1e-6*sa[0])}, s={np.round(sa, 6)}')


_____________________

PS C:\Dev\TECT2\Contents\PDE> python .\rank2_check.py
shape: (3, 64, 64, 64)
max|psi|: 0.5542384261235356
Global SVD s = [3.14930e-01 2.98304e-01 7.00000e-06]
Global rank  = 3
F0: rank=3, s=[2.32692e-01 1.59302e-01 3.00000e-06]
F1: rank=3, s=[1.90466e-01 1.13786e-01 2.00000e-06]
F2: rank=3, s=[2.31566e-01 7.61290e-02 4.00000e-06]

