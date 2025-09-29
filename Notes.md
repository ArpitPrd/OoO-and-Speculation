## Objective

- OoO interacts branch, memory speculation, two level cache hierarchy

- Report: IPC, AMAT, cache behavior, effective stall cycles

## Configuration

- DerivO3CPU
- Private L1 i, d
- shared L2
- configurable branch preds
- optional memory dependence predictor (speculative)

## Microbenchmarks

- Compute Bound Kernel: ALU-intesive loop to stress OoO exec
- Pointer Chasing Kernel: LL traversal to test memory dependece speculation
- Streaming Kernel: Sequential array to test prefetching and L1/L2 behavior


Implement them in c++ and cross compile accordingly

## Tunable Params

- CPU parameters: ROB Size, issue/ commit width
- L1/L2: size, associativity, replacement policy 
- Branch Speculation: enabled/diable, predictor type
- Memory dependence speculation: en/dis
- Optional Prefetcher: on/off

## Metrics to Collect

- Perf: IPC
- cache stats: L1d, L1i and L2 hit rates MPKI
- Memory Latency: AMAT at each cache level
- speculative stats: BPmispred rate, MDS success fail rate, pipeline flushes
- Effective stall cycles: cycles lost waiting on memory after overlapping with OoO instruciton
- Energy Proxies: weighted access counts (L1, L2, DRAM)

## Workflow

- Compile workflow for chosen ISA
- gem5 with SE mode in desired CPU and cache parameters
- run baseline on OoO CPU, no mem dep spec
- Implement MDP
- Sweep design parameters as listed above
- Produce tables, plots and comparivtiev metrics


## Submission Guidlines

- Design Docs: CPU cache configs, expected behavior
- gem5 config scripts: 
- source code: microbench source code and optional mem dependence predictor
- raw stats
- plots and tables,
- analysis report: trends, insights and final design reco
- (optional) MDP with recovery and demo fo performance impact

## Reference Links

- https://github.com/jlpteaching/gem5-assignment0-wq25
- https://github.com/jlpteaching/gem5-assignment3-wq25/blob/main/components/processors.py
- https://github.com/dhschall/LLBP
- https://github.com/useredsa/spec_tage_scl/tree/master/include/tagescl/ifaces/gem5
- https://github.com/Aasys/gshare
- https://github.com/QawsQAER/gem5branchPredictor
- https://github.com/rameshgkwd05/Agree-Branch-Predictor

may check the assignemnt ones, those are good.

## GEM5 org

- common/simulation has checkpointing features