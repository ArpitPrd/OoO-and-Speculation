
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import (
    PrivateL1CacheHierarchy,
)
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA

from gem5.simulate.simulator import Simulator
from gem5.resources.resource import BinaryResource
from m5.objects import (
    BiModeBP,
    LocalBP,
    TournamentBP, 
    FIFORP, 
    # BaseCache, 
    SimpleCache,
    StridePrefetcher, 
    TaggedPrefetcher,
    DCPTPrefetcher,
    LRURP,
    RandomRP,
    LFURP,
    BIPRP,
)
# import m5.objects as m5

import argparse
import sys

import gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy as gcc

# print(f"@@@\n{dir(gcc)}")
# sys.exit(1)

def add_arguments(parser):
    parser.add_argument(
        "--cpu-type",
        type=str,
        choices=["O3", "TimingSimple", "Atomic"],
        default="O3",
        help="Type of CPU to use in the simulation.",
    )
    parser.add_argument(
        "--ROB-entries",
        type=int,
        default=192,
        help="Number of Reorder Buffer (ROB) entries for O3 CPU.",
    )
    parser.add_argument(
        "--issue-width",
        type=int,
        default=4,
        help="Issue width for O3 CPU.",
    )
    parser.add_argument(
        "--commit-width",
        type=int,
        default=4,
        help="Commit width for O3 CPU.",
    )
    parser.add_argument(
        "--l1d-size",
        type=str,
        default="16KiB",
        help="Size of L1 data cache.",
    )
    parser.add_argument(
        "--l1i-size",
        type=str,
        default="16KiB",
        help="Size of L1 instruction cache.",
    )
    parser.add_argument(
        "--l1d-assoc",
        type=int,
        default=2,
        help="Associativity of L1 data cache.",
    )
    parser.add_argument(
        "--l1i-assoc",
        type=int,
        default=2,
        help="Associativity of L1 instruction cache.",
    )
    parser.add_argument(
        "--l2-size",
        type=str,
        default="256KiB",
        help="Size of L2 cache.",
    )
    parser.add_argument(
        "--l2-assoc",
        type=int,
        default=8,
        help="Associativity of L2 cache.",
    )
    parser.add_argument(
        "--l1i-replace-policy",
        type=str,
        choices=["LRU", "Random", "LFU", "SRRIP", "BRRIP", "BIP"],
        default="LRU",
        help="Cache replacement policy.",
    )
    parser.add_argument(
        "--l1d-replace-policy",
        type=str,
        choices=["LRU", "Random", "LFU", "SRRIP", "BRRIP", "BIP"],
        default="LRU",
        help="Cache replacement policy.",
    )
    parser.add_argument(
        "--l2-replace-policy",
        type=str,
        choices=["LRU", "Random", "LFU", "SRRIP", "BRRIP", "BIP"],
        default="LRU",
        help="Cache replacement policy.",
    )
    parser.add_argument(
        "--branch-predictor-enable",
        action="store_true",
        help="Enable branch predictor for O3 CPU.",
    )
    parser.add_argument(
        "--branch-predictor-type",
        type=str,
        choices=["BiModeBP", "TournamentBP", "LocalBP", "GShareBP"],
        default="BiModeBP",
        help="Type of branch predictor to use.",
    )
    parser.add_argument(
        "--mem-dep-pred-enable",
        action="store_true",
        help="Enable memory dependency predictor for O3 CPU.",
    )
    parser.add_argument(
        "--l1d-prefetcher-type",
        type=str,
        choices=["StridePrefetcher"],
        default="StridePrefetcher",
        help="Type of prefetcher to use.",
    )
    parser.add_argument(
        "--l2-prefetcher-type",
        type=str,
        choices=["DCPTPrefetcher", "TaggedPrefetcher"],
        default="DCPTPrefetcher",
        help="Type of prefetcher to use.",
    )
    parser.add_argument(
        "--memory-size",
        type=str,
        default="8GiB",
        help="Size of the memory.",
    )
    parser.add_argument(
        "--clock-frequency",
        type=str,
        default="3GHz",
        help="Clock frequency of the system.",
    )
    parser.add_argument(
        "--binary",
        type=str,
        required=True,
        help="Path to the binary to be executed in the simulation.",
    )
    parser.add_argument(
        "--num-cores",
        type=int,
        default=1,
        help="Number of CPU cores.",
    )
    parser.add_argument(
        "--isa",
        type=str,
        choices=["X86", "RISCV", "ARM"],
        default="X86",
        help="Instruction set architecture (ISA) of the CPU.",
    )
    parser.add_argument(
        "--max-tick",
        type=int,
        default=1000000000,
        help="Maximum number of ticks to simulate.",
    )


parser = argparse.ArgumentParser(description="Gem5 Simulation Script")
add_arguments(parser)
args = parser.parse_args()

def replace_policy_mapping(policy_str):
    mapping = {
        "LRU": LRURP(),
        "Random": RandomRP(),
        "LFU": LFURP(),
        "BIP": BIPRP()
    }
    return mapping.get(policy_str, FIFORP())  # Default to FIFO if invalid option


def prefetcher_mapping(prefetcher_str):
    mapping = {
        "StridePrefetcher": StridePrefetcher(),
        "TaggedPrefetcher": TaggedPrefetcher(),
        "DCPTPrefetcher": DCPTPrefetcher(),
    }
    return mapping.get(prefetcher_str, None)  # Default to None if invalid option

def cpu_mapping(cpu_str):
    mapping = {
        "O3": CPUTypes.O3,
        "TimingSimple": CPUTypes.TIMING,
        "Atomic": CPUTypes.ATOMIC,
    }
    return mapping.get(cpu_str, CPUTypes.O3)  # Default to O3 if invalid option

def isa_mapping(isa_str):
    mapping = {
        "X86": ISA.X86,
        "RISCV": ISA.RISCV,
        "ARM": ISA.ARM,
    }
    return mapping.get(isa_str, ISA.X86)  # Default to X86 if invalid option

def branch_predictor_mapping(bp_str):
    mapping = {
        "BiModeBP": BiModeBP(),
        "TournamentBP": TournamentBP(),
        "LocalBP": LocalBP(),
        # "GShareBP": GShareBP(),
    }
    return mapping.get(bp_str, BiModeBP())  # Default to BiModeBP if invalid option


## Define the class for the private L2 cache
class PrivateL2Cache(SimpleCache):
    
    type = "PrivateL2Cache"
    # assoc = args.l2_assoc
    size = args.l2_size
    # latency = 20
    # response_latency = 20
    # mshrs = 16
    # tgts_per_mshr = 12
    replacement_policy = replace_policy_mapping(args.l2_replace_policy)


## combines both L1 and L2 cache 
class CustomL1L2Hierarchy(PrivateL1CacheHierarchy):
    def __init__(self, l1i_size="16KiB", l1d_size="16KiB", l2_size="256KiB"):
        self._l2_size = l2_size
        super().__init__(l1i_size=l1i_size, l1d_size=l1d_size)
        

    def instantiate(self):
        super().instantiate()

        # Example: Set replacement policies
        
        # self.l2_size = "256KiB"
        
        self.l1i.replacement_policy = replace_policy_mapping(args.l1i_replace_policy)
        self.l1d.replacement_policy = replace_policy_mapping(args.l1d_replace_policy)

        # Add prefetcher to L1D
        if args.data_prefetcher_enable:
            self.l1d.prefetcher = prefetcher_mapping(args.l1d_prefetcher_type) 
        # Add prefetcher to L1I
        if args.instruction_prefetcher_enable:
            self.l1i.prefetcher = prefetcher_mapping(args.l1d_prefetcher_type) 

        
        # Create L2 as SimpleCache
        self.l2 = SimpleCache(
            size=self._l2_size,
            assoc=args.l2_assoc,
            latency=20,
            response_latency=20,
            replacement_policy=replace_policy_mapping(args.l2_replace_policy),
        )

        self.l2.prefetcher = prefetcher_mapping(args.l2_prefetcher_type)

        # Connect L1 caches to L2
        self.l1i.mem_side = self.l2.cpu_side
        self.l1d.mem_side = self.l2.cpu_side

        # L2 -> memory will be connected by board
        self.l2.mem_side = None


# cache_hierarchy = PrivateL1CacheHierarchy(l1d_size="16KiB", l1i_size="16KiB", replacement_policy="LRU")
cache_hierarchy = CustomL1L2Hierarchy(l1d_size=args.l1d_size, l1i_size=args.l1i_size)

# memory definition
memory = SingleChannelDDR3_1600(size=args.memory_size)

# processor def
processor = SimpleProcessor(cpu_type=cpu_mapping(args.cpu_type), isa=isa_mapping(args.isa), num_cores=args.num_cores)

# building the board with all the basic elements on SimpleBoard
board = SimpleBoard(
    clk_freq=args.clock_frequency,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)


"""
for each of the cpu in the set of the cores:
    - set the branch predictor
    - issueWidth
    - commit width
    - ROB Entries
    - mem dependence
"""
for core in board.get_processor().get_cores():
    cpu = core.core
    if args.branch_predictor_enable:
        cpu.branchPred = branch_predictor_mapping(args.branch_predictor_type)
    cpu.issueWidth = args.issue_width
    cpu.commitWidth = args.commit_width
    cpu.numROBEntries = args.ROB_entries
    # cpu.enableLSQSpeculation = True
    # cpu.useStoreSets = False
    if args.mem_dep_pred_enable:
        cpu.SSITSize = 512
        cpu.LFSTSize = 128
        cpu.store_set_clear_period = 100000
    else:
        cpu.SSITSize = 1
        cpu.LFSTSize = 1
        cpu.store_set_clear_period = 1e7
    
# Setting the workload
board.set_se_binary_workload(
    BinaryResource(args.binary),
)

# Running the simulator
sim = Simulator(board=board)
sim.run()


# final exit
print(
    "Exiting @ tick {} because {}.".format(
        sim.get_current_tick(), sim.get_last_exit_event_cause()
    )
)