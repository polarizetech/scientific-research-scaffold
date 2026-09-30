## Cardiology (computational and electrophysiological)

ECG and heart-rate signals, cardiac cell and tissue models, and interactions between the heart and the brain.

- **Established versus not.** ECG waveform physiology and standard intervals are established. Most
  heart–brain (interoception) claims are active research, and "heartbeat-evoked" effects are sensitive to
  analysis choices.
- **Standards.** The AHA/ACCF/HRS recommendations for standardising and interpreting the ECG (Kligfield et
  al., 2007), and for heart-rate variability the Task Force of the ESC and NASPE (1996). Name the HRV
  measure, the window length and the artefact correction. [BK]
- **Data and models.** PhysioNet for open recordings (Goldberger et al., 2000), CellML for cell models, and
  openCARP for tissue simulation. [BK]
- **Cautions.** R-peak detection errors propagate into every HRV measure, so check them by eye on a sample.
  Respiration and posture confound HRV. Nothing built here is a diagnostic device; never word an output as
  a diagnosis.
