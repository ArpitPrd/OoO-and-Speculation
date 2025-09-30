
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import (
    PrivateL1CacheHierarchy,
)
from gem5.components.memory import SingleChannelDDR3_1600
from gem5.components.cachehierarchies.abstract_cache_hierarchy import (
    AbstractCacheHierarchy,
)
# import gem5
# print(f"@@@\n{dir(gem5.components.processors)}")
# from gem5.components.processors.o3_cpu import O3CPU
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA

from gem5.simulate.simulator import Simulator
from gem5.resources.resource import BinaryResource
from m5.objects import (
    SystemXBar,
    L2XBar,
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
    Cache,
    RiscvInterrupts
)


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
        choices=["StridePrefetcher", "None"],
        default="None",
        help="Type of prefetcher to use.",
    )
    parser.add_argument(
        "--l2-prefetcher-type",
        type=str,
        choices=["DCPTPrefetcher", "TaggedPrefetcher", "None"],
        default="None",
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
    if prefetcher_str == "None":
        return None
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




## combines both L1 and L2 cache 
# class CustomL1L2Hierarchy(PrivateL1CacheHierarchy):
#     def __init__(self, l1i_size="16KiB", l1d_size="16KiB", l2_size="256KiB", l2_assoc=8):
#         super().__init__(l1i_size=l1i_size, l1d_size=l1d_size)
#         # Store L2 parameters for later use.
#         # DO NOT create L1/L2 caches here. The parent class handles L1s,
#         # and we will create the L2 in incorporate_cache.
#         self._l2_size = l2_size
#         self._l2_assoc = l2_assoc

#     def incorporate_cache(self, board):
#         # Let the parent class create the L1 caches and connect them to the CPU.
#         super().incorporate_cache(board)

#         # Create the L2 cache. SimpleCache is suitable for this level of scripting
#         # as it provides cpu_side and mem_side ports.
#         self.l2 = SimpleCache(
#             size=self._l2_size,
#             # assoc=self._l2_assoc,
#             replacement_policy=replace_policy_mapping(args.l2_replace_policy),
#         )

#         # Register the L2 cache as a child of this hierarchy. This is crucial for
#         # gem5's object model and for stats collection.
#         self.add_child("l2", self.l2)

#         # Attach a prefetcher to the L2 cache if specified.
#         if args.l2_prefetcher_type:
#             self.l2.prefetcher = prefetcher_mapping(args.l2_prefetcher_type)

#         # The parent class creates lists of L1 caches: self.l1_icaches and self.l1_dcaches.
#         # We need to iterate through these and connect their memory side to the L2's CPU side.
#         for l1_icache in self.l1_icaches:
#             l1_icache.mem_side = self.l2.cpu_side

#         for l1_dcache in self.l1_dcaches:
#             l1_dcache.mem_side = self.l2.cpu_side

#         # Connect the L2 cache to the main memory bus on the board.
#         self.l2.mem_side = board.get_mem_port()


class L1L2Hierarchy(AbstractCacheHierarchy):
    def __init__(
        self,
        l1i_size: str,
        l1d_size: str,
        l2_size: str,
    ):

        super().__init__()

        self.l2_bus = L2XBar()
        self.membus = SystemXBar()
        self.l1_icaches = [
            Cache(
                size=l1i_size,
                assoc=args.l1i_assoc,
                tag_latency = 2,
                data_latency = 2,
                response_latency = 2,
                mshrs = 4,
                tgts_per_mshr = 20,
                replacement_policy=replace_policy_mapping(args.l1i_replace_policy)
            ) for i in range(args.num_cores)
        ]
        l1d_params = {
            "size": l1d_size, "assoc": args.l1d_assoc,
            "tag_latency": 2, "data_latency": 2, "response_latency": 2,
            "mshrs": 4, "tgts_per_mshr": 20,
            "replacement_policy": replace_policy_mapping(args.l1d_replace_policy)
        }
        l1d_prefetcher = prefetcher_mapping(args.l1d_prefetcher_type)
        if l1d_prefetcher:
            l1d_params["prefetcher"] = l1d_prefetcher
        
        self.l1_dcaches = [ Cache(**l1d_params) for i in range(args.num_cores) ]

        self.l2_cache = Cache(
            size=l2_size,
            assoc=args.l2_assoc,
            tag_latency = 20,
            data_latency = 20,
            response_latency = 20,
            mshrs = 20,
            tgts_per_mshr = 20,
            replacement_policy=replace_policy_mapping(args.l2_replace_policy),
        )

        if args.l2_prefetcher_type:
            self.l2_cache.prefetcher = prefetcher_mapping(args.l2_prefetcher_type)

    def incorporate_cache(self, board):
        self.membus.mem_side_ports = board.get_mem_ports()[0][1]
        self.l2_cache.mem_side = self.membus.cpu_side_ports
        self.l2_bus.mem_side_ports = self.l2_cache.cpu_side
        for i in range(args.num_cores):
            self.l1_icaches[i].mem_side = self.l2_bus.cpu_side_ports
            self.l1_dcaches[i].mem_side = self.l2_bus.cpu_side_ports
        
        for i, core in enumerate(board.get_processor().get_cores()):
            # print(f"@@@\n{dir(core)}")
            core.connect_icache(self.l1_icaches[i].cpu_side)
            core.connect_dcache(self.l1_dcaches[i].cpu_side)



# cache_hierarchy = PrivateL1CacheHierarchy(l1d_size="16KiB", l1i_size="16KiB", replacement_policy="LRU")
# cache_hierarchy = CustomL1L2Hierarchy(l1d_size=args.l1d_size, l1i_size=args.l1i_size)
# cache_hierarchy = None
cache_hierarchy = L1L2Hierarchy(
    l1i_size=args.l1i_size,
    l1d_size=args.l1d_size,
    l2_size=args.l2_size,
)


# memory definition
memory = SingleChannelDDR3_1600(size=args.memory_size)

# # processor def
processor = SimpleProcessor(cpu_type=cpu_mapping(args.cpu_type), isa=isa_mapping(args.isa), num_cores=args.num_cores)

# processor = O3CPU(isa=isa_mapping(args.isa), num_cores=args.num_cores)
# print(f"@@@\n{dir(processor)}")
# processor.create_interrupt_controllers()

# processor.l1_icaches = [
#     SimpleCache(
#         size=args.l1i_size,
#         # assoc=args.l1i_assoc,
#         replacement_policy=replace_policy_mapping(args.l1i_replace_policy)
#     )
#     for _ in range(args.num_cores)
# ]

# processor.l1_dcaches = [
#     SimpleCache(
#         size=args.l1d_size,
#         # assoc=args.l1d_assoc,
#         replacement_policy=replace_policy_mapping(args.l1d_replace_policy)
#     )
#     for _ in range(args.num_cores)
# ]

# l2_cache = SimpleCache(
#     size=args.l2_size,
#     # assoc=args.l2_assoc,
#     replacement_policy=replace_policy_mapping(args.l2_replace_policy)
# )

# if args.l2_prefetcher_type:
#     l2_cache.prefetcher = prefetcher_mapping(args.l2_prefetcher_type)

# for i in range(args.num_cores):
#     processor.l1_icaches[i].mem_side = l2_cache.cpu_side
#     processor.l1_dcaches[i].mem_side = l2_cache.cpu_side



# # building the board with all the basic elements on SimpleBoard
board = SimpleBoard(
    clk_freq=args.clock_frequency,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# board.connect_io_bus(processor.get_io_bus())
# l2_cache.mem_side = board.get_memory_port()

# for i in range(args.num_cores):
#     processor.cores[i].add_icache(processor.l1_icaches[i])
#     processor.cores[i].add_dcache(processor.l1_dcaches[i])




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
    
    if args.isa == "X86":
        # X86 has a creation method on the ISA object and needs connections.
        cpu.interrupts = cpu.isa[0].create_interrupt_controller()
        cpu.interrupts[0].pio = board.get_mem_ports()[0][1]
        cpu.interrupts[0].int_requestor = board.get_mem_ports()[0][1]
    elif args.isa == "RISCV":
        # RISC-V's interrupt controller is instantiated directly.
        cpu.interrupts = RiscvInterrupts()


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