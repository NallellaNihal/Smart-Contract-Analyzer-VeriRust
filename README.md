# VeriRust Smart Contract Analyzer

VeriRust is a Rust smart contract verification and coverage-analysis toolkit. It instruments Rust source files with reachability assertions, runs Kani formal verification, generates LLVM branch coverage reports, and stores auditable outputs under `results/`.

## What This Repository Contains

| Path | Purpose |
|---|---|
| `rust_injector.py` | Injects `REACHABLE_TRUE` / `REACHABLE_FALSE` assertions into `if` and `while` branches, then appends Kani harnesses where possible. |
| `verify_rust.sh` | Main orchestration script for single files, folders, and Cargo workspaces. |
| `Rust Dataset/` | Rust smart-contract-style benchmark files used as verification targets. |
| `results/` | Existing verification outputs: modified source snapshots, Kani logs, summaries, assertion checks, and LLVM coverage metadata. |
| `diagrams/` | Architecture and verification-flow diagrams. |
| `src/lib.rs` | Minimal Cargo library entry point so coverage tooling has a stable crate root. |
| `Cargo.toml` | Root Cargo manifest for the analyzer project. |
| `rust-toolchain.toml` | Pins Rust to `nightly-2026-03-10` with required components. |

## Verification Pipeline

The normal flow is:

1. Select a `.rs` file or directory.
2. Back up the original source.
3. Run `rust_injector.py` to add reachability assertions.
4. Save the modified file under `results/<name>/`.
5. Run Kani and write `kani_output.txt`.
6. Extract failed `REACHABLE_TRUE` / `REACHABLE_FALSE` checks into `assertion_checks.txt`.
7. Restore the original source file.
8. Run `cargo +nightly-2026-03-10 llvm-cov --branch --html`.
9. Write a per-contract `SUMMARY.txt`.

Original input files are restored after verification. The modified versions are kept only in `results/` for audit and review.

## Assertion Logic

For a condition like:

```rust
if balance >= amount {
    transfer();
}
```

the injector inserts:

```rust
assert!(!(balance >= amount), "REACHABLE_TRUE");
assert!((balance >= amount), "REACHABLE_FALSE");
```

With this reachability technique, Kani assertion failures are useful signals:

| Failed assertion | Meaning |
|---|---|
| `REACHABLE_TRUE` | The condition can be true, so the true branch is reachable. |
| `REACHABLE_FALSE` | The condition can be false, so the false branch is reachable. |

## Usage

Verify a single file:

```bash
./verify_rust.sh "Rust Dataset/vault_guard_v10.rs"
```

Verify a folder:

```bash
./verify_rust.sh "Rust Dataset"
```

Verify the current project:

```bash
./verify_rust.sh .
```

Manually inject assertions into a file:

```bash
python3 rust_injector.py path/to/file.rs
```

## Tooling Requirements

Install these tools before running full verification:

| Tool | Why it is needed |
|---|---|
| Rust nightly `nightly-2026-03-10` | Reproducible build and coverage behavior. |
| Kani | Formal verification and symbolic execution. |
| `cargo-llvm-cov` | Branch and condition coverage reports. |
| Python 3 | Assertion injection and harness generation. |

The pinned Rust toolchain is declared in `rust-toolchain.toml`.

## Output Layout

Each verification target writes files like:

```text
results/<contract_name>/
├── <contract_name>_original.txt
├── <contract_name>_mod.txt
├── injection.log
├── kani_output.txt
├── assertion_checks.txt
├── SUMMARY.txt
└── coverage_report/
    ├── llvm_cov_output.log
    └── LLVM_COVERAGE_SUMMARY.txt
```

If HTML coverage is generated successfully, `coverage_report/index.html` is also created.

## Notes On This Checkout

The attached knowledge-base document describes a larger historical `rust_try` project that included additional helper scripts and example contracts. This repository currently contains the active analyzer core, benchmark dataset, diagrams, and generated results. The README here documents the project as it exists in this checkout.
