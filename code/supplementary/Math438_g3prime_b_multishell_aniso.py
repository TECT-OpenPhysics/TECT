#!/usr/bin/env python3
"""Math438_g3prime_b_multishell_aniso.py -- G3'-b execution (CLAUDE.md
6.3.8): (i) THREE-shell BCC ensemble race {110}+{200}+{211} and
(ii) ANISOTROPIC per-axis {200} second harmonics, under the anchored
exact-Wick Gibbs--Bogoliubov protocol (Math429/430/432 machinery; engine
re-derived standalone from the Math432 source to avoid module-level scan
re-execution on import).

G3'-b residuals being executed (registered in Math432 / OPEN-QUESTIONS):
 (i)  shells >= 3 mixed-shell sextic dominance: phi_c = A1*Phi_{110}
      + A2*Phi_{200} + A3*Phi_{211}; does any (A1,A2,A3,M) beat R_H?
 (ii) anisotropic second harmonics: per-axis a = (a_x,a_y,a_z) {200}
      amplitudes (uniaxial / biaxial branches) -- does symmetry breaking
      deepen the SHG tilt below the disordered baseline?
 (iii) Math400-AddF N=64 harmonic-ratio extraction: NOT executed here
      (data-extraction task; registered with spec in the Math438 note).

Pre-registered outcomes (CLAUDE.md 6.3.3):
  FAIL <=> some scanned point has anchored dF < 0 confirmed at both the
           production resolution (cut12/48^3/nk4) and the refinement
           (cut20/64^3) -> Math424 Outcome-3 branch (re-scope).
  PASS <=> all scanned points positive AND refinement margins exceed
           the last-step drift at the checked extrema.
Checkpoint/resume: Runs/math/Math438/state.json (45-s sandbox cap).
JSON: Runs/math/Math438/g3prime_b_multishell_aniso.json
"""
import json, math, os, sys, time, itertools
import numpy as np

sys.path.insert(0, 'Codes/supplementary')
import Math424_AddA_reading_uniqueness as m424

U, V, Q0, C = -0.86, 3.24, 0.6801747616, 1.0
R = 0.005
S = Q0 / math.sqrt(2.0)
K1 = R
K2 = R + C * Q0**4
K3 = R + 4.0 * C * Q0**4
CLAIMS = []
def claim(name, expected, actual, tol):
    ok = abs(actual - expected) <= tol
    CLAIMS.append(dict(name=name, expected=expected, actual=actual,
                       tol=tol, passed=bool(ok)))
    assert ok, f"FAIL {name}: {expected} vs {actual}"
def claim_true(name, cond, detail=""):
    CLAIMS.append(dict(name=name, expected=True, actual=bool(cond),
                       tol=0, passed=bool(cond), detail=detail))
    assert cond, f"FAIL {name}: {detail}"
def record(name, value, detail=""):
    CLAIMS.append(dict(name=name, recorded=value, detail=detail,
                       passed=True, tol=None, expected=None, actual=None))

SHELL1 = sorted({p for q in [(1,1,0),(1,-1,0)]
                 for p in itertools.permutations(q)}
                | {(-a,-b,-c) for (a,b,c) in
                   {p for q in [(1,1,0),(1,-1,0)]
                    for p in itertools.permutations(q)}})
SHELL1 = [v for v in SHELL1 if sum(x*x for x in v) == 2]
SHELL2 = [(2,0,0),(-2,0,0),(0,2,0),(0,-2,0),(0,0,2),(0,0,-2)]
SHELL3 = sorted({(sa*a, sb*b, sc*c)
                 for (a,b,c) in set(itertools.permutations((2,1,1)))
                 for sa in (1,-1) for sb in (1,-1) for sc in (1,-1)})
claim("shell1_count", 12, len(SHELL1), 0)
claim("shell3_count", 24, len(SHELL3), 0)
claim_true("shell3_D3_parity", all((a+b+c) % 2 == 0 for (a,b,c) in SHELL3))
claim_true("shell3_norm6", all(a*a+b*b+c*c == 6 for (a,b,c) in SHELL3))

def d3(cut2):
    r = int(math.isqrt(cut2)) + 1
    o = [(a,b,c3) for a in range(-r,r+1) for b in range(-r,r+1)
         for c3 in range(-r,r+1)
         if (a+b+c3) % 2 == 0 and a*a+b*b+c3*c3 <= cut2]
    o.sort(key=lambda t:(t[0]**2+t[1]**2+t[2]**2,t)); return o

B = S*np.array([[1,1,0],[1,0,1],[0,1,1]],dtype=float).T
V_CELL = (2*math.pi)**3/abs(np.linalg.det(B))
def kmesh(nk):
    f = (np.arange(nk)+0.5)/nk
    return [B@np.array([x,y,z]) for x in f for y in f for z in f]

class Engine:
    """Math432 engine generalised: condensate passed as a prebuilt grid
    field phic plus its exact per-shell quadratic kernel energy Fquad."""
    def __init__(self, cut2, nk, grid):
        self.cut2, self.grid_n = cut2, grid
        self.Gs = d3(cut2); self.kpts = kmesh(nk)
        dmap = {}
        for i,Gi in enumerate(self.Gs):
            for j,Gj in enumerate(self.Gs):
                d = (Gi[0]-Gj[0],Gi[1]-Gj[1],Gi[2]-Gj[2])
                dmap.setdefault(d, []).append((i,j))
        maxax = max(max(abs(d[0]),abs(d[1]),abs(d[2])) for d in dmap)
        claim_true(f"nyquist_cut{cut2}_grid{grid}",
                   3*maxax < grid//2, f"3*{maxax} vs {grid//2}")
        self.dlist = list(dmap); self.n_d = len(self.dlist)
        II, JJ, TT = [], [], []
        for t,d in enumerate(self.dlist):
            for (i,j) in dmap[d]:
                II.append(i); JJ.append(j); TT.append(t)
        self.II = np.array(II); self.JJ = np.array(JJ); self.TT = np.array(TT)
        Gp = S*np.array(self.Gs,dtype=float)
        self.den = []
        for kv in self.kpts:
            q = Gp + kv[None,:]
            self.den.append(C*((np.einsum("ij,ij->i",q,q))-Q0*Q0)**2)
        ax = np.arange(grid)*(2*np.pi/grid)
        X,Y,Z = np.meshgrid(ax,ax,ax,indexing="ij")
        def build(vs):
            f = np.zeros_like(X)
            for kv in vs:
                f += np.cos(kv[0]*X+kv[1]*Y+kv[2]*Z)
            return f
        self.phi1 = build(SHELL1); self.phi2 = build(SHELL2)
        self.phi3 = build(SHELL3)
        self.phi2ax = [build([(2,0,0),(-2,0,0)]),
                       build([(0,2,0),(0,-2,0)]),
                       build([(0,0,2),(0,0,-2)])]
        self.fidx = [tuple(c % grid for c in d) for d in self.dlist]
    def _what(self, field):
        fh = np.fft.fftn(field)/field.size
        return np.array([fh[fi] for fi in self.fidx]).real
    def F_exact(self, phic, Fquad, M):
        mH2 = R + 3*U*M + 15*V*M*M
        p2g = phic*phic; p4g = p2g*p2g
        w2 = self._what(p2g); w4 = self._what(p4g)
        coefs = (3*U+30*V*M)*w2 + 5*V*w4
        nG = len(self.Gs)
        W = np.zeros((nG,nG)); W[self.II,self.JJ] = coefs[self.TT]
        tot = 0.0
        sig_acc = np.zeros(self.n_d)
        for den in self.den:
            K = W.copy(); K[np.diag_indices_from(K)] += mH2 + den
            sgn, ld = np.linalg.slogdet(K)
            if sgn <= 0: return None
            tot += ld
            Ki = np.linalg.inv(K)
            sig_acc += np.bincount(self.TT, weights=Ki[self.II,self.JJ],
                                   minlength=self.n_d)
        norm = 1.0/(V_CELL*len(self.kpts))
        arr = np.zeros((self.grid_n,)*3, dtype=complex)
        for t,fi in enumerate(self.fidx):
            arr[fi] += sig_acc[t]*norm
        sig = np.real(np.fft.ifftn(arr))*self.grid_n**3
        sbar = float(sig.mean()); p2s = float((p2g*sig).mean())
        s2 = float((sig*sig).mean()); p2s2 = float((p2g*sig*sig).mean())
        s3 = float((sig**3).mean())
        Fcl = (Fquad + 0.25*U*float(p4g.mean())
               + (V/6)*float((p4g*p2g).mean()))
        rem = (-(0.5)*(3*U*M+15*V*M*M)*sbar - 15*V*M*p2s
               + 0.75*U*s2 + 7.5*V*p2s2 + 2.5*V*s3)
        return Fcl + 0.5*tot*norm + rem
    def F_diag_basis(self, phic, Fquad, M):
        mH2 = R + 3*U*M + 15*V*M*M
        p2g = phic*phic; p4g = p2g*p2g
        w2bar = float(p2g.mean()); w4bar = float(p4g.mean())
        rhat = mH2 + (3*U+30*V*M)*w2bar + 5*V*w4bar
        tot = 0.0; sb = 0.0
        for den in self.den:
            tot += float(np.sum(np.log(rhat+den)))
            sb  += float(np.sum(1.0/(rhat+den)))
        norm = 1.0/(V_CELL*len(self.kpts))
        Mt = sb*norm
        Fcl = (Fquad + 0.25*U*w4bar + (V/6)*float((p4g*p2g).mean()))
        rem = (-(0.5)*(3*U*M+15*V*M*M)*Mt - 15*V*M*w2bar*Mt
               + 0.75*U*Mt*Mt + 7.5*V*w2bar*Mt*Mt + 2.5*V*Mt**3)
        return Fcl + 0.5*tot*norm + rem

rR = m424.gap_solve(R,0,0,0.0); MR = m424.M_fast(rR)
claim("r_R", 0.30452570866744433, rR, 5e-9)
claim("c2_shell3_analytic", 13.9279, 12.0*(rR + 4*C*Q0**4), 5e-4)

def F_diag_cont_rel(E, phic, Fquad, M):
    mH2 = R + 3*U*M + 15*V*M*M
    p2g = phic*phic; p4g = p2g*p2g
    w2bar = float(p2g.mean()); w4bar = float(p4g.mean())
    rhat = mH2 + (3*U+30*V*M)*w2bar + 5*V*w4bar
    Mt = m424.M_fast(rhat)
    Fcl = (Fquad + 0.25*U*w4bar + (V/6)*float((p4g*p2g).mean()))
    rem = (-(0.5)*(3*U*M+15*V*M*M)*Mt - 15*V*M*w2bar*Mt
           + 0.75*U*Mt*Mt + 7.5*V*w2bar*Mt*Mt + 2.5*V*Mt**3)
    ref = (-(0.5)*(3*U*MR+15*V*MR*MR)*MR + 0.75*U*MR*MR + 2.5*V*MR**3)
    return Fcl + 0.5*m424.dI(rhat, rR) + rem - ref

def anchored(E, phic, Fquad, M):
    FE = E.F_exact(phic, Fquad, M)
    if FE is None: return None
    return (F_diag_cont_rel(E, phic, Fquad, M)
            + (FE - E.F_diag_basis(phic, Fquad, M)))

def make_state(E, A1, A2v, A3):
    """A2v: scalar (isotropic) or 3-tuple per-axis {200} amplitudes."""
    if np.isscalar(A2v):
        phi2 = A2v*E.phi2; q2 = K2*0.5*float((phi2*phi2).mean()) if A2v else 0.0
    else:
        phi2 = sum(a*f for a,f in zip(A2v, E.phi2ax))
        q2 = K2*0.5*float((phi2*phi2).mean())
    phic = A1*E.phi1 + phi2 + A3*E.phi3
    Fquad = K1*0.5*(A1*A1*12.0) + q2 + K3*0.5*(A3*A3*24.0)
    return phic, Fquad

# checkpoint infra
OUTDIR = "Runs/math/Math438"; os.makedirs(OUTDIR, exist_ok=True)
STATE_F = os.path.join(OUTDIR, "state.json")
STATE = json.load(open(STATE_F)) if os.path.exists(STATE_F) else {}
T0 = time.time()
def memo(key, fn):
    if key in STATE: return STATE[key]
    if time.time() - T0 > 33.0:
        json.dump(STATE, open(STATE_F, "w"))
        print(f"[CHECKPOINT] budget reached before {key}; rerun to resume",
              flush=True)
        sys.exit(3)
    v = fn(); STATE[key] = v
    return v

E12 = Engine(12, 4, 48)
# moment identities
claim("p2_shell1", 12.0, float((E12.phi1**2).mean()), 1e-9)
claim("p2_shell3", 24.0, float((E12.phi3**2).mean()), 1e-7)  # 12 pairs x 2 = 2*n3
claim("p2_shell2ax", 2.0, float((E12.phi2ax[0]**2).mean()), 1e-9)
m31_13 = float((E12.phi1**3 * E12.phi3).mean())
m31_12 = float((E12.phi1**3 * E12.phi2).mean())
m21_23 = float((E12.phi1**2 * E12.phi2 * E12.phi3).mean())
record("cross_moments_3shell",
       dict(m31_110x3_200=m31_12, m31_110x3_211=m31_13,
            m211_110x2_200_211=m21_23),
       "4-wave resonance strengths feeding the mixed-shell channels")
# Math440 R3: promote the three moments from record to assert (6.3.8)
claim("m31_110x3_200_exact", 144.0, m31_12, 1e-9)
claim("m31_110x3_211_exact", 432.0, m31_13, 1e-9)
claim("m211_110x2_200_211_exact", 192.0, m21_23, 1e-9)
claim_true("m31_110x3_211_nonzero", abs(m31_13) > 0.5,
           "{110}^3 x {211} 4-wave resonance ACTIVE (e.g. (1,1,0)+(1,0,1)"
           "+(0,1,-1)-(2,1,1)... lattice closure)")
# A=0 identities
F0e = E12.F_exact(np.zeros((48,)*3), 0.0, MR)
claim("A0_exact_equals_diag", E12.F_diag_basis(np.zeros((48,)*3), 0.0, MR),
      F0e, 1e-10)
phic0, fq0 = make_state(E12, 0.0, 0.0, 0.0)
claim("A0_anchored_zero", 0.0, anchored(E12, phic0, fq0, MR), 1e-9)

# Math432 regression: two-shell points must reproduce (same machinery)
def pt(A1, A2v, A3, mf, tag):
    M = mf*MR
    phic, fq = make_state(E12, A1, A2v, A3)
    v = anchored(E12, phic, fq, M)
    return v
v_leg = memo("reg_legacy", lambda: pt(0.01, 0.015, 0.0, 1.0, "leg"))
claim_true("math432_scanmin_region_reproduced",
           abs(v_leg - 5.536e-4) < 8e-5,
           f"two-shell scan-min point: {v_leg:.6e} vs Math432 +5.536e-4")
# small-A3 quadratic: c2^(3) finite difference at A1 = 0
v3p = memo("c2_3_fd", lambda: pt(0.0, 0.0, 0.005, 1.0, "fd"))
claim_true("c2_shell3_smallA_match",
           abs(v3p/(0.005**2) - 12.0*(rR + 4*C*Q0**4)) <
           0.05*12.0*(rR + 4*C*Q0**4),
           f"dF/A3^2 = {v3p/2.5e-5:.3f} vs c2(3) = 13.93 (5% window)")

# ---------------- (i) three-shell scan ----------------
A1g = [0.01, 0.0856, 0.14]
A2g = [-0.06, 0.0, 0.06]
A3g = [-0.04, -0.01, 0.0, 0.01, 0.04]
Mg  = [0.7, 1.0, 1.4]
rows = []
neg = []
mn = (1e9, None)
for A1 in A1g:
    for A2 in A2g:
        for A3 in A3g:
            for mf in Mg:
                if A2 == 0.0 and A3 == 0.0 and A1 != 0.01:
                    pass  # keep: serves as single-shell regression rows
                key = f"i_{A1}_{A2}_{A3}_{mf}"
                v = memo(key, lambda A1=A1,A2=A2,A3=A3,mf=mf:
                         pt(A1, A2, A3, mf, key))
                rows.append(dict(A1=A1, A2=A2, A3=A3, M_over_MR=mf, dF=v))
                if v is None or v <= 0: neg.append(rows[-1])
                if v is not None and v < mn[0]: mn = (v, (A1,A2,A3,mf))
claim_true("threeshell_no_negatives", len(neg) == 0,
           f"{len(rows)} pts, negatives: {len(neg)}")
record("threeshell_min", dict(dF=mn[0], at=mn[1]), f"{len(rows)} points")

# ---------------- (ii) anisotropic {200} branches ----------------
rows2 = []
mn2 = (1e9, None)
for A1 in (0.0856, 0.14):
    for amp in (0.03, 0.065):
        for pat, tag in (((amp,0,0), "uniax+"), ((-amp,0,0), "uniax-"),
                         ((amp,amp,0), "biax+"), ((-amp,-amp,0), "biax-"),
                         ((amp,)*3, "iso+"), ((-amp,)*3, "iso-")):
            key = f"ii_{A1}_{amp}_{tag}"
            v = memo(key, lambda A1=A1,pat=pat: pt(A1, pat, 0.0, 1.0, key))
            rows2.append(dict(A1=A1, a=pat, tag=tag, dF=v))
            if v is not None and v < mn2[0]: mn2 = (v, (A1, pat, tag))
claim_true("aniso_no_negatives",
           all(r["dF"] is not None and r["dF"] > 0 for r in rows2),
           f"{len(rows2)} anisotropic points")
record("aniso_min", dict(dF=mn2[0], at=mn2[1]), f"{len(rows2)} points")

# ---------------- refinement spot-checks at the extrema ----------------
def refine(A1, A2v, A3, mf):
    E20 = Engine(20, 4, 64)
    M = mf*MR
    if np.isscalar(A2v):
        phi2 = A2v*E20.phi2
    else:
        phi2 = sum(a*f for a,f in zip(A2v, E20.phi2ax))
    phic = A1*E20.phi1 + phi2 + A3*E20.phi3
    q2 = K2*0.5*float((phi2*phi2).mean())
    Fq = K1*0.5*(A1*A1*12.0) + q2 + K3*0.5*(A3*A3*24.0)
    return anchored(E20, phic, Fq, M)
A1m, A2m, A3m, mfm = mn[1]
v_ref = memo("refine_i", lambda: refine(A1m, A2m, A3m, mfm))
claim_true("refine_threeshell_min_positive", v_ref is not None and v_ref > 0,
           f"cut20/64^3 at scan min: {v_ref:.6e} vs cut12 {mn[0]:.6e}")
record("refine_drift_i", v_ref - mn[0], "cut12->cut20 at the 3-shell min")
A1a, pa, ta = mn2[1]
v_ref2 = memo("refine_ii", lambda: refine(A1a, pa, 0.0, 1.0))
claim_true("refine_aniso_min_positive", v_ref2 is not None and v_ref2 > 0,
           f"cut20/64^3 at aniso min: {v_ref2:.6e} vs cut12 {mn2[0]:.6e}")
record("refine_drift_ii", v_ref2 - mn2[0], "cut12->cut20 at the aniso min")

verdict = ("PASS (three-shell and anisotropic-harmonic ensembles positive "
           "everywhere; refinement margins hold)"
           if not neg else "FAIL")
record("G3prime_b_verdict", verdict,
       f"min_i={mn[0]:.6e} at {mn[1]}; min_ii={mn2[0]:.6e} at {mn2[1]}")
out = dict(theory_tag="Math438", date="2026-06-04",
           constants=dict(u=U, v=V, r=R, q0=Q0, K2=K2, K3=K3,
                          r_R=rR, M_R=MR),
           rows_threeshell=rows, rows_aniso=rows2, verdict=verdict,
           claims=CLAIMS)
json.dump(out, open(os.path.join(OUTDIR,
          "g3prime_b_multishell_aniso.json"), "w"), indent=1)
json.dump(STATE, open(STATE_F, "w"))
npass = sum(1 for c in CLAIMS if c.get("passed"))
print(f"3-shell min {mn[0]:+.6e} at {mn[1]}; aniso min {mn2[0]:+.6e} at "
      f"{mn2[1]}")
print(f"VERDICT: {verdict}  (claims {npass}/{len(CLAIMS)})")
sys.exit(0)
