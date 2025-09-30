#!/bin/bash

# ==============================================================================
# Gem5 Experiment Sweeper for OoO & Speculation Lab
# ==============================================================================
#
# This script automates the process of compiling workloads and running a series
# of gem5 simulations to sweep through different architectural parameters.
#
# Instructions:
# 1. Place this script in the same directory as your gem5 configuration script
#    ('test.py') and your C workload files.
# 2. Make sure the paths to your gem5 executable and C source files are correct.
# 3. Make the script executable: chmod +x run_experiments.sh
# 4. Run the script: ./run_experiments.sh
#
# Note on Prefetcher Sweep:
# To properly test the prefetcher "with and without", your 'test.py' script
# should be modified to handle a 'None' option for the --l1d-prefetcher-type
# argument. This script assumes such a modification has been made.
#
# ==============================================================================

# Exit immediately if any command fails
set -e

# --- Configuration ---
# Path to your gem5 executable for RISC-V
GEM5_PATH="../gem5/build/RISCV/gem5.opt"
# Path to your Python simulation script
SCRIPT_PATH="test.py"
# The ISA to simulate
ISA="RISCV"
# The C compiler for your target ISA. If running on an x86 host, you'll need a
# RISC-V cross-compiler (e.g., riscv64-unknown-linux-gnu-gcc). If running on
# a RISC-V host, 'gcc' is sufficient.
CC="riscv64-linux-gnu-gcc"

# Define the C workload source files and their output binary names
declare -A C_WORKLOADS
C_WORKLOADS=(
    ["compute_bound_wl.c"]="compute_bound_workload"
    ["pointer_chasing_wl.c"]="pointer_chaser_workload"
    ["streaming_kernel_wl.c"]="streaming_workload"
)

# --- Step 1: Compile Workloads ---
echo "================================================="
echo " Compiling C Workloads for RISC-V..."
echo "================================================="

for src in "${!C_WORKLOADS[@]}"; do
    binary=${C_WORKLOADS[$src]}
    echo "Compiling $src -> $binary..."
    if ! $CC -static -o "$binary" "$src"; then
        echo "ERROR: Compilation of $src failed. Aborting."
        exit 1
    fi
done
echo "All workloads compiled successfully."
echo


# --- Step 2: Define Parameter Sweeps ---
# This is where you define the values for each parameter you want to test.

# An array of the workload binaries to run
WORKLOADS=("compute_bound_workload" "pointer_chaser_workload" "streaming_workload")

# Out-of-Order CPU Core parameters
ROB_SIZES=(64 128 192 256)
WIDTHS=(2 4 8) # Issue and Commit Width

# Cache parameters
L1_SIZES=("16kB" "32kB" "64kB")
L1_ASSOCS=(2 4 8)
L2_SIZES=("128kB" "256kB" "512kB" "1MB")
L2_ASSOCS=(8 16)
REPLACEMENT_POLICIES=("LRU" "Random" "LFU") # Add others like 'BIP' if desired

# Speculation parameters
BRANCH_PREDICTORS=("BiModeBP" "LocalBP" "TournamentBP")
L2_PREFETCHERS=("TaggedPrefetcher" "DCPTPrefetcher")

# --- Step 3: Run Simulation Sweeps ---
# The script will now iterate through each parameter set for each workload.

# Define a baseline configuration function to avoid repetition
run_simulation() {
    local outdir=$1
    local binary=$2
    shift 2 # Remove the first two arguments
    local params="$@"

    echo "-------------------------------------------------"
    echo " WORKLOAD: $binary"
    echo " SAVING TO: $outdir"
    echo " PARAMS: $params"
    echo "-------------------------------------------------"

    mkdir -p "$outdir"

    # The main gem5 command
    $GEM5_PATH --outdir="$outdir" \
        "$SCRIPT_PATH" \
        --isa="$ISA" \
        --binary="$binary" \
        --cpu-type=O3 \
        $params # Pass the specific parameters for this run

    echo "Simulation finished for $outdir."
    echo
}

# The baseline parameters that will be used unless overridden by a sweep
BASELINE_ARGS="--ROB-entries=192 --issue-width=4 --commit-width=4 \
--l1i-size=32kB --l1i-assoc=8 --l1d-size=32kB --l1d-assoc=8 \
--l2-size=256kB --l2-assoc=16 --l1i-replace-policy=LRU \
--l1d-replace-policy=LRU --l2-replace-policy=LRU \
--branch-predictor-enable --branch-predictor-type=TournamentBP \
--mem-dep-pred-enable --l1d-prefetcher-type=StridePrefetcher \
--l2-prefetcher-type=TaggedPrefetcher"


# Outer loop: Iterate over each workload
for workload in "${WORKLOADS[@]}"; do

    # --- Sweep 1: Re-Order Buffer (ROB) Size ---
    for rob in "${ROB_SIZES[@]}"; do
        params="--ROB-entries=$rob $(echo $BASELINE_ARGS | sed 's/--ROB-entries=[0-9]* //')"
        run_simulation "results/${workload}/rob_${rob}" "$workload" $params
    done

    # --- Sweep 2: Issue/Commit Width ---
    for width in "${WIDTHS[@]}"; do
        params="--issue-width=$width --commit-width=$width $(echo $BASELINE_ARGS | sed 's/--issue-width=[0-9]* //' | sed 's/--commit-width=[0-9]* //')"
        run_simulation "results/${workload}/width_${width}" "$workload" $params
    done

    # --- Sweep 3: L1 Cache Parameters (Size and Associativity) ---
    for l1_size in "${L1_SIZES[@]}"; do
        for l1_assoc in "${L1_ASSOCS[@]}"; do
            params="--l1i-size=$l1_size --l1d-size=$l1_size --l1i-assoc=$l1_assoc --l1d-assoc=$l1_assoc \
            $(echo $BASELINE_ARGS | sed 's/--l1i-size=[^ ]* //' | sed 's/--l1d-size=[^ ]* //' | sed 's/--l1i-assoc=[^ ]* //' | sed 's/--l1d-assoc=[^ ]* //')"
            run_simulation "results/${workload}/l1_${l1_size}_${l1_assoc}way" "$workload" $params
        done
    done

    # --- Sweep 4: L2 Cache Parameters (Size and Associativity) ---
    for l2_size in "${L2_SIZES[@]}"; do
        for l2_assoc in "${L2_ASSOCS[@]}"; do
            params="--l2-size=$l2_size --l2-assoc=$l2_assoc $(echo $BASELINE_ARGS | sed 's/--l2-size=[^ ]* //' | sed 's/--l2-assoc=[^ ]* //')"
            run_simulation "results/${workload}/l2_${l2_size}_${l2_assoc}way" "$workload" $params
        done
    done

    # --- Sweep 5: Replacement Policy ---
    for policy in "${REPLACEMENT_POLICIES[@]}"; do
        params="--l1i-replace-policy=$policy --l1d-replace-policy=$policy --l2-replace-policy=$policy \
        $(echo $BASELINE_ARGS | sed 's/--l1i-replace-policy=[^ ]* //' | sed 's/--l1d-replace-policy=[^ ]* //' | sed 's/--l2-replace-policy=[^ ]* //')"
        run_simulation "results/${workload}/policy_${policy}" "$workload" $params
    done

    # --- Sweep 6: Branch Speculation ---
    # a) Without branch speculation
    params="$(echo $BASELINE_ARGS | sed 's/--branch-predictor-enable //')"
    run_simulation "results/${workload}/branch_spec_off" "$workload" $params

    # b) With different branch predictors
    for bp in "${BRANCH_PREDICTORS[@]}"; do
        params="--branch-predictor-type=$bp $(echo $BASELINE_ARGS | sed 's/--branch-predictor-type=[^ ]* //')"
        run_simulation "results/${workload}/branch_spec_${bp}" "$workload" $params
    done

    # --- Sweep 7: Memory Dependence Speculation ---
    # a) Without memory speculation
    params="$(echo $BASELINE_ARGS | sed 's/--mem-dep-pred-enable //')"
    run_simulation "results/${workload}/mem_spec_off" "$workload" $params

    # b) With memory speculation (this is the baseline)
    run_simulation "results/${workload}/mem_spec_on" "$workload" $BASELINE_ARGS

    # --- Sweep 8: L1D Prefetcher ---
    # a) Without L1D prefetcher (Requires 'None' to be a valid choice in test.py)
    params="--l1d-prefetcher-type=None $(echo $BASELINE_ARGS | sed 's/--l1d-prefetcher-type=[^ ]* //')"
    run_simulation "results/${workload}/prefetcher_off" "$workload" $params

    # b) With L1D prefetcher (this is the baseline)
    run_simulation "results/${workload}/prefetcher_on" "$workload" $BASELINE_ARGS

    # --- Sweep 9: L2 Prefetcher ---
    # a) Without L2 prefetcher
    params="--l2-prefetcher-type=None $(echo $BASELINE_ARGS | sed 's/--l2-prefetcher-type=[^ ]* //')"
    run_simulation "results/${workload}/l2_prefetcher_off" "$workload" $params

    # b) With different L2 prefetchers
    for l2_pf in "${L2_PREFETCHERS[@]}"; do
        params="--l2-prefetcher-type=$l2_pf $(echo $BASELINE_ARGS | sed 's/--l2-prefetcher-type=[^ ]* //')"
        run_simulation "results/${workload}/l2_prefetcher_${l2_pf}" "$workload" $params
    done
done

echo "================================================="
echo " All experiments complete!"
echo " Results are located in the 'results/' directory."
echo "================================================="
