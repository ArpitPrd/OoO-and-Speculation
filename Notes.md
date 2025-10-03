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

## Note on Res

- L2 Hit rate is much lesser than L1 because of the fact that only more difficult to search addresses access reach L2. 

## AMAT = Average Memory Access Time

- AMAT(level x) = Hit Time(Level x) + Miss Rate(Level x) * Miss Penalty(Level x)

## Metrics to collect

- instructions:
    - simInsts
- ipc:
    - board.processor.cores.core.ipc
- cache stats:
    - l1d
        - board.cache_hierarchy.l1_dcaches.demandHits::processor.cores.core.data
        - board.cache_hierarchy.l1_dcaches.demandMisses::processor.cores.core.data
    - l1i
        - board.cache_hierarchy.l1_icaches.demandHits::processor.cores.core.inst
        - board.cache_hierarchy.l1_icaches.demandMisses::processor.cores.core.inst
        - board.cache_hierarchy.l1_icaches.demandAccesses::processor.cores.core.inst
    - l2
        - board.cache_hierarchy.l2_cache.overallHits::cache_hierarchy.l1_dcaches.prefetcher
        - bboard.cache_hierarchy.l2_cache.overallHits::processor.cores.core.inst
        - board.cache_hierarchy.l2_cache.overallHits::processor.cores.core.data
        - board.cache_hierarchy.l2_cache.overallHits::total
        - board.cache_hierarchy.l2_cache.overallMisses::cache_hierarchy.l1_dcaches.prefetcher
        - board.cache_hierarchy.l2_cache.overallMisses::processor.cores.core.inst
        - board.cache_hierarchy.l2_cache.overallMisses::processor.cores.core.data
        - board.cache_hierarchy.l2_cache.overallMisses::total

        - board.cache_hierarchy.l2_cache.overallAccesses::cache_hierarchy.l1_dcaches.prefetcher
        - board.cache_hierarchy.l2_cache.overallAccesses::processor.cores.core.inst
        - board.cache_hierarchy.l2_cache.overallAccesses::processor.cores.core.data
        - board.cache_hierarchy.l2_cache.overallAccesses::total
    - Memory Latency:
        - AMAT_L2 = 20 + board.cache_hierarchy.l2_cache.overallMissRate::total * board.memory.mem_ctrl.dram.avgMemAccLat / board.clk_domain.clock

        - AMAT_L1i = 2 + board.cache_hierarchy.l1_icaches.demandMissRate::total * AMAT_L2

        - AMAT_L1d = 2 + board.cache_hierarchy.l1_dcaches.demandMissRate::total * AMAT_L2

    - Branch MisPrediction Rate:
        - board.processor.cores.core.commit.branchMispredicts
        - board.processor.cores.core.branchPred.committed_0::total

    - Memory Dependence
        - Failure:
            - board.processor.cores.core.iew.memOrderViolationEvents
        - Success:
            - = board.processor.cores.core.commitStats0.numLoadInsts - board.processor.cores.core.iew.memOrderViolationEvents
        - for rate divide success and failure by total = board.processor.cores.core.commitStats0.numLoadInsts

    - Pipeline Flushes:
        - board.processor.cores.core.commit.branchMispredicts + board.processor.cores.core.iew.memOrderViolationEvents
        - in board.processor.cores.core.commit.commitSquashedInsts (the instructions that were dropped due to one intruction being flushed due to incorrect speculation)
    
    - Effective Stall Cycles:
        - board.processor.cores.core.commit.numCommittedDist::0 (for small L2) - board.processor.cores.core.commit.numCommittedDist::0 (for large L2)
        - I will provide this number
    
    - Energy Proxies:
        - Formula: Total Energy Proxy = (L1_Accesses × W_L1) + (L2_Accesses × W_L2) + (DRAM_Accesses × W_DRAM)
        - L1_Accesses = board.cache_hierarchy.l1_icaches.overallAccesses::total + board.cache_hierarchy.l1_dcaches.overallAccesses::total
        - L2_Accesses = board.cache_hierarchy.l2_cache.overallAccesses::total
        - DRAM_Accesses = board.memory.mem_ctrl.readReqs + board.memory.mem_ctrl.writeReqs
        - W_L1 = 1
        - W_L2 = 10
        - W_DRAM = 100