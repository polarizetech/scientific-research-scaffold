<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Language Routing for Computational Neuroscience — Working Doc

**Status:** v0.1 (working draft) · **Last updated:** 2026-09-30
**Inputs:** Gemini answer (domain→language) · ChatGPT critique (constraint→language) · literature pass via Scientific Research RAG

*The computational-engineer agent routes by § 2. An applied note about one organisation's project is left out of this copy.*

**Legend**
- Confidence: **H** high · **M** medium · **L** low
- Source basis: **[Lit-read]** read in-session from the full text · **[Lit-idx]** retrieved passage from the RAG index · **[Web]** web search this session · **[BK]** background knowledge, not verified in-session

---

## 1. Bottom line

The literature supports ChatGPT's framing over Gemini's. In practice, the field runs a **Python front end over generated or compiled native code**, not a choice between Python *or* C++. The literature also brings in cost dimensions that neither answer covered: fixed vs variable run cost, host↔GPU transfer, developer time, and long-term maintainability. **Go has essentially no footprint in the neuro literature.**

---

## 2. Routing rule (revised)

```text
0. Is there an existing simulator/toolkit for this model class?
   → Use it (Brian2 / NEST / NEURON / GeNN / BrainPy / MNE). Write glue, not engines.

1. Is hardware access or hard-real-time behavior the constraint?
   → C / C++ at the edge; expose data to Python (e.g., via LSL-style streaming).

2. Is this exploration, analysis, or model iteration?
   → Python. Optimize for developer time first.

3. Too slow? → PROFILE. Then classify the cost:
   a. Fixed cost (build/compile/load) dominates?  → prefer CPU/runtime-mode tools; avoid rebuild loops.
   b. Variable cost (per-timestep) dominates?     → codegen/standalone C++ or GPU backend.
   c. Host↔device transfer dominates?             → keep stimuli/recording on-device; batch transfers.
   d. Sparse / event-driven ops dominate?         → framework with dedicated sparse/event operators.

4. Does the framework's model language fail to express what you need?
   → Drop to a target-language extension (e.g., Brian user C++ functions), keep the Python script as source of truth.

5. Only if the *whole runtime* (not one kernel) is the problem
   → Write/extend a native engine in C++ (and budget for maintaining it).

6. Is it primarily services, APIs, or concurrent network I/O?
   → Go or Python, chosen by team/ecosystem fit rather than performance.
```

---

## 3. Claim-by-claim pressure test

| # | Claim (origin) | Literature verdict | Conf. | Basis |
|---|---|---|---|---|
| 1 | Python is the master interface (Gemini) | **Supported.** PyGeNN's authors describe comp-neuro and ML converging on a Python ecosystem. They note NEST, NEURON and CARLsim added Python interfaces, and Brian2 and Arbor were Python-first from the start. | H | [Lit-read] Knight 2021 |
| 2 | "~80% of work is Python" (Gemini) | **Unsupported.** No source found gives a proportion. | H (that it's unsourced) | Search found nothing |
| 3 | Python is slow (Gemini) | **Qualified.** Brian2 states its flexibility cost performance, especially for small models that don't benefit from vectorisation. Brian Hears shows interpretation overhead dominates at low channel counts, and that pushing filtering into C removes most of it. | H | [Lit-read] Stimberg 2019; [Lit-idx] Fontaine 2011 |
| 4 | C++ gives absolute speed (Gemini) | **Rejected as stated.** Brian2 reports performance similar to low-level-language simulators via code generation. Brian2GeNN accelerates some cases by tens to hundreds of times. Speed comes from the execution layer, not from writing C++ by hand. | H | [Lit-read] Stimberg 2019 |
| 5 | C++ dominates performance-critical simulator cores (ChatGPT, softened) | **Supported.** PyGeNN notes that many SNN simulators are written in C++ for performance reasons. NEST uses OpenMP/MPI. | H | [Lit-read] Knight 2021; Schmitt 2023 |
| 6 | Separate large networks from detailed multicompartment biophysics (ChatGPT) | **Supported.** Tools split by niche: NEST for large point-neuron networks, NEURON/Arbor for multicompartment, GeNN and others for GPU point neurons. | H | [Lit-read] Knight 2021 |
| 7 | Python frontend ≠ Python execution (ChatGPT) | **Strongly supported.** Brian2 has two modes. Runtime mode keeps Python in control and calls compiled code. Standalone mode generates the whole control loop in C++ and trades flexibility for speed. | H | [Lit-read] Stimberg 2019 |
| 8 | JAX-style compilation breaks "Python = slow" (ChatGPT) | **Supported, with caveat.** BrainPy JIT-compiles Python models via JAX/XLA to CPU/GPU/TPU. However, it needed **dedicated sparse/event-driven operators** because conventional dense operators handle brain dynamics poorly, and it reports multi-order-of-magnitude gains from them. These are the authors' own claims. | M-H | [Lit-read] Wang 2023 |
| 9 | Descend only where the framework can't express the algorithm (ChatGPT) | **Supported.** Brian2 lets model code call user-written target-language functions and link external libraries. Its example is a real-time microphone input to an auditory network. | H | [Lit-read] Stimberg 2019 |
| 10 | C for firmware/ABI/hardware SDKs (ChatGPT) | **Plausible, not tested here.** Nothing retrieved directly addresses C vs C++ on neuro hardware. | M | [BK] |
| 11 | Acquisition edge in C/C++ → analysis in Python (ChatGPT) | **Supported in pattern.** LSL is the de facto neuro streaming layer, with clients in C/C++, Python, MATLAB, Rust, Julia and others, across more than 150 device classes. Its core library being C++ is [BK]. | M-H | [Lit-read] Kothe 2024 abstract |
| 12 | Go for big neuro datasets / streaming (Gemini) | **No literature support.** A RAG search for Go in neuroscience pipelines returned nothing relevant. The field's streaming infrastructure (LSL) and data SDKs are not Go-based. Absence of papers ≠ absence of use in industry infra. | M | RAG search (null) |
| 13 | Go's GC isn't the main barrier (ChatGPT) | **Untested in literature.** Reasonable. | M | [BK] |
| 14 | Python 3.14 free-threaded build is officially supported (ChatGPT) | **Correct.** PEP 779 removed the "experimental" tag. The build is still opt-in, not the default. | H | [Web] prior turn |

---

## 4. Dimensions both answers missed

| Dimension | Evidence | Routing implication | Conf. |
|---|---|---|---|
| **Fixed vs variable cost** | GeNN has high fixed costs: model definition, building on CPU, and loading onto the GPU. Non-global parameter changes need recompilation. Its variable (per-sim-time) costs are low, which suits long biological timescales and real-time use. | Many short runs with changing structure → CPU/runtime tools. Few long runs → GPU codegen. | H [Lit-read] Schmitt 2023 |
| **Host↔GPU transfer** | PyGeNN names two bottlenecks: copying spikes off the GPU every timestep in large models, and copying stimuli onto the GPU in long protocols. It reports only minimal overhead over pure C++ once these are handled. | The Python-vs-C++ question matters less than where data lives. | H [Lit-read] Knight 2021 |
| **Developer time** | Brian 1 deliberately chose flexibility over speed. Its authors argue model development often takes weeks while runs take minutes to hours. | Weight time-to-first-result, not just runtime. | H [Lit-read] Stimberg 2019 |
| **Maintainability / portability** | NEURON's modernization paper describes a codebase maintained over four decades as a major engineering burden. Supporting more hardware targets multiplies redundant, error-prone code. The field responded with code generation (NMODL) rather than hand-written ports. | Hand-written C++ has a long-tail cost; prefer codegen/DSL paths. | H [Lit-read] Awile 2022 |
| **Correctness / verification** | Much scientific software is written by scientists with little software-engineering training. The paper cites retractions traced to inherited analysis code. Brian2 argues explicit, readable equations make models easier to verify. | Readability and tests are a routing criterion, not a nicety. | H [Lit-read] Gewaltig 2014; Stimberg 2019 |
| **Parameter search as the real cost** | Schmitt et al. argue that parameter search usually creates the highest demand for compute time. GeNN batching gave a 1.6× speed-up at batch size 40 in their setup. | Benchmark sweeps, not single runs. | M-H [Lit-read] Schmitt 2023 |

---

## 5. Tool → language-layer map

| Tool | User-facing layer | Execution layer | Niche | Basis |
|---|---|---|---|---|
| Brian2 | Python (equations as strings) | Generated C++ (runtime/standalone); GPU via Brian2GeNN/Brian2CUDA | Flexible SNNs, custom models, closed-loop | [Lit-read] |
| NEST | Python / SLI; NESTML for custom models | C++ with OpenMP/MPI | Large point-neuron networks | [Lit-read] |
| NEURON | Python / HOC; NMODL mechanisms | C/C++ via CoreNEURON + NMODL codegen, CPU/GPU | Detailed multicompartment | [Lit-read] |
| GeNN / PyGeNN | Python or C++ | Generated CUDA/C++ | GPU point-neuron SNNs | [Lit-read] |
| BrainPy | Python | JAX/XLA + custom sparse/event operators | Multi-scale, trainable brain dynamics | [Lit-read] |
| Auryn (example) | C++ | C++/MPI; analysis done in Python | Custom plasticity at scale | [Lit-idx] Tomé 2022 |
| MNE-Python | Python | NumPy/SciPy | M/EEG analysis | [Lit-idx] Gramfort 2013 |
| LSL | Many bindings | C++ core [BK] | Synchronized multimodal acquisition | [Lit-read] abstract |

---

## 7. Gaps & unverified

- **Go:** no neuro literature found. The verdict rests on absence of evidence. · **L-M**
- **Rust / Julia:** suggested by ChatGPT; not searched. LSL lists both as client languages, which is the only evidence here.
- **C vs C++ on neuromorphic/embedded hardware:** not retrieved.
- **Head-to-head JAX vs C++ simulator benchmarks:** not retrieved. BrainPy's performance claims are self-reported.
- **Tooling limits this session:** RAG embeddings were unavailable (lexical-only retrieval). OpenAlex was unreachable. Newly fetched papers were stored but not passage-indexed, so their claims were read directly from full text and could not be run through `check_citations`.

---

## 8. Devil's advocate

- **For Gemini's coarse map:** for a newcomer, "Python for work, C++ is what the simulator is written in" is accurate enough, and every tool in §5 fits it. The nuance in §2 pays off mainly for people building tools, not using them.
- **Against "stay in Python":** the codegen/JIT stack is itself a large, opaque dependency. BrainPy's own authors cite transparency and extensibility limits of codegen approaches. Debugging generated code or XLA can cost more than a small hand-written C++ kernel.
- **Against the literature sample:** the papers are almost all written by simulator developers promoting their own designs. Independent benchmarks would carry more weight.

---

## 9. Sources (read depth)

| Source | Depth |
|---|---|
| Stimberg, Brette & Goodman 2019, *Brian 2*, eLife, doi:10.7554/elife.47314 | Full text ~80% (intro, case studies, codegen, discussion) |
| Knight, Komissarov & Nowotny 2021, *PyGeNN*, Front Neuroinform, doi:10.3389/fninf.2021.659005 | Intro/background only (~15%) |
| Wang et al. 2023, *BrainPy*, eLife, doi:10.7554/elife.86365 | Intro + infrastructure (~25%) |
| Awile et al. 2022, *Modernizing NEURON*, Front Neuroinform, doi:10.3389/fninf.2022.884046 | Intro (~10%) |
| Schmitt, Rostami & Nawrot 2023, *GeNN and NEST*, Front Neuroinform, doi:10.3389/fninf.2023.941696 | Intro + discussion + methods sections (~30%) |
| Gewaltig & Cannon 2014, *Current practice in software development…*, PLoS Comput Biol, doi:10.1371/journal.pcbi.1003376 | Intro (~9%) |
| Kothe et al. 2024, *Lab Streaming Layer*, bioRxiv, doi:10.1101/2024.02.13.580071 | Abstract + intro (~7%) |
| Fontaine et al. 2011, *Brian Hears*, Front Neuroinform, doi:10.3389/fninf.2011.00009 | Retrieved passages only |
| Tomé et al. 2022, Nat Commun, doi:10.1038/s41467-022-28339-z | One methods passage only |
| Gramfort et al. 2013, *MNE-Python*, Front Neurosci, doi:10.3389/fnins.2013.00267 | One passage only |
| PEP 779 (Python free-threading) | Web snippets only |

---

## 10. Next steps

- [ ] Get PyGeNN results section: quantify overhead vs pure C++.
- [ ] Search independent SNN simulator benchmarks (e.g., Tikidji-Hamburyan 2017).
- [ ] Search Rust/Julia neuro tooling.
- [ ] Re-run once the fetched papers are passage-indexed, then run `check_citations` on §3–4 claims.
