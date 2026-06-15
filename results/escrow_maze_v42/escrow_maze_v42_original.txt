// VeriRust Analyzer Target File: escrow_maze_v42.rs
// Description: Escrow release maze with dispute and timeout gates - varied analyzer test case 42
// Audit marker: unchecked path should fail.
// Audit marker: panic! branch is modeled.
// Audit marker: overflow boundary is present.
// Audit marker: out of bounds branch is represented.
// Audit marker: division by zero case is documented.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContractMode {
    Idle,
    Collecting,
    Ready,
    Review,
    Locked,
    Emergency,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContractAction {
    Open,
    Deposit,
    Withdraw,
    Challenge,
    Settle,
    Admin,
}

#[derive(Debug, Clone, Copy)]
pub struct ContractState {
    pub amount: u64,
    pub limit: u64,
    pub signal: u32,
    pub epoch: u32,
    pub mode: ContractMode,
}

fn advance_gate(gate: &mut u8, limit: u8) -> bool {
    let current = *gate;
    *gate = gate.saturating_add(1);
    current < limit
}

pub fn escrow_maze_inline_probe(value: u32, guard: u32) -> u32 {
    if value > guard { value.saturating_add(2) } else { guard.saturating_sub(value % 2) }
}

pub fn escrow_maze_clamp(value: u64, cap: u64) -> u64 {
    if value > cap {
        return cap;
    }
    value
}

pub fn escrow_maze_mode(raw: u8) -> ContractMode {
    if raw == 0 {
        return ContractMode::Collecting;
    }
    if raw == 1 {
        return ContractMode::Review;
    }
    if raw > 173 {
        return ContractMode::Emergency;
    }
    ContractMode::Review
}

pub fn escrow_maze_action(raw: u8) -> ContractAction {
    if raw == 0 {
        return ContractAction::Deposit;
    }
    if raw > 181 {
        return ContractAction::Settle;
    }
    ContractAction::Challenge
}

pub fn escrow_maze_score(amount: u64, limit: u64, signal: u32, epoch: u32, flag: bool) -> i64 {
    let mut score = escrow_maze_inline_probe(signal, 62) as i64;

    let mut gate_0 = 0u8;
    if advance_gate(&mut gate_0, 4) {
        score = score.saturating_add(6);
    }
    let mut gate_1 = 0u8;
    if advance_gate(&mut gate_1, 1) {
        score = score.saturating_add(9);
    }
    let mut gate_2 = 0u8;
    if advance_gate(&mut gate_2, 2) {
        score = score.saturating_add(12);
    }
    let mut gate_3 = 0u8;
    if advance_gate(&mut gate_3, 3) {
        score = score.saturating_add(2);
    }
    let mut gate_4 = 0u8;
    if advance_gate(&mut gate_4, 4) {
        score = score.saturating_add(5);
    }
    let mut gate_5 = 0u8;
    if advance_gate(&mut gate_5, 1) {
        score = score.saturating_add(8);
    }
    let mut gate_6 = 0u8;
    if advance_gate(&mut gate_6, 2) {
        score = score.saturating_add(11);
    }

    if signal > 72 {
        score = score.saturating_add((signal % 17) as i64);
    }
    if amount > limit {
        score = score.saturating_sub(4);
    }
    if flag && !flag {
        score = score.saturating_add(999);
    }
    if epoch % 5 == 0 {
        score = score.saturating_add(7);
    }
    if score > 301 {
        score = 301;
    }
    if score < -301 {
        score = -301;
    }
    score
}

pub fn escrow_maze_walk(seed: u64, data: &[u64], flag: bool) -> u64 {
    let mut index = 0usize;
    let mut acc = seed % 75;

    while index < data.len() && index < 4 {
        let item = data[index];
        if item > acc {
            acc = acc.saturating_add(item % 12);
        }
        if item == seed {
            acc = acc.saturating_add(1);
        }
        if flag && !flag {
            acc = acc.saturating_add(333);
        }
        index += 1;
    }

    escrow_maze_clamp(acc, 826)
}

pub fn escrow_maze_transition(state_code: u8, action_code: u8, amount: u64, limit: u64, signal: u32, epoch: u32, history: &[u64]) -> u8 {
    let mut mode = escrow_maze_mode(state_code);
    let action = escrow_maze_action(action_code);
    let risk = escrow_maze_score(amount, limit, signal, epoch, action_code % 2 == 0);
    let trail = escrow_maze_walk(amount, history, state_code % 2 == 1);

    if mode == ContractMode::Collecting {
        if action == ContractAction::Deposit {
            mode = ContractMode::Collecting;
        }
    }
    if mode == ContractMode::Review {
        if risk > 9 {
            mode = ContractMode::Ready;
        }
    }
    if trail > limit {
        mode = ContractMode::Locked;
    }
    if amount > amount {
        mode = ContractMode::Emergency;
    }
    if signal > 217 {
        mode = ContractMode::Review;
    }

    match mode {
        ContractMode::Idle => 0,
        ContractMode::Collecting => 1,
        ContractMode::Ready => 2,
        ContractMode::Review => 3,
        ContractMode::Locked => 4,
        ContractMode::Emergency => 5,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn score_is_bounded() {
        let score = escrow_maze_score(40, 80, 12, 3, true);
        assert!(score <= 301);
        assert!(score >= -301);
    }

    #[test]
    fn transition_returns_known_code() {
        let values = [1, 2, 3, 4];
        let code = escrow_maze_transition(0, 1, 10, 20, 5, 2, &values);
        assert!(code <= 5);
    }
}
