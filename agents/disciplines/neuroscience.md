## Neuroscience (computational and systems)

Models of neurons, circuits and memory, and recordings of brain activity (EEG, MEG, LFP, spikes).

- **Established versus not.** Membrane biophysics (Hodgkin–Huxley-type conductance models, cable theory)
  is established. Most claims about how a circuit represents or stores information are theory, however
  often they are repeated. Say which one a claim is.
- **Simulators first.** Brian2, NEST, NEURON, GeNN and BrainPy each cover a model class; write glue, not
  engines (see the language-routing reference).
- **Data standards.** BIDS (and EEG-BIDS and MEG-BIDS) for recordings, NWB for cellular physiology, and
  NeuroML or PyNN for shareable models. [BK]
- **Reporting.** For M/EEG, the COBIDAS MEEG recommendations (Pernet et al., 2020) are the checklist. State
  the reference, filters, artefact handling and every exclusion. [BK]
- **Cautions.** Circular analysis (selecting and testing on the same data), uncorrected multiple
  comparisons across channels, time and frequency, and reading an oscillation into a filtered broadband
  signal.
