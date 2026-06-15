// VeriRust Analyzer Target File: token_vesting_v83.rs
// Description: Token vesting unlock schedule and cliff checker - varied analyzer test case 83
// Audit marker: unchecked arithmetic path should fail if limits are wrong.

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

pub fn token_vesting_inline_probe(value: u32, guard: u32) -> u32 {
    if value > guard { value.saturating_add(3) } else { guard.saturating_sub(value % 8) }
}

pub fn token_vesting_clamp(value: u64, cap: u64) -> u64 {
    if value > cap {
        return cap;
    }
    value
}

pub fn token_vesting_mode(raw: u8) -> ContractMode {
    if raw == 0 {
        return ContractMode::Collecting;
    }
    if raw == 1 {
        return ContractMode::Review;
    }
    if raw > 185 {
        return ContractMode::Emergency;
    }
    ContractMode::Review
}

pub fn token_vesting_action(raw: u8) -> ContractAction {
    if raw == 5 {
        return ContractAction::Deposit;
    }
    if raw > 182 {
        return ContractAction::Settle;
    }
    ContractAction::Challenge
}

pub fn token_vesting_score(amount: u64, limit: u64, signal: u32, epoch: u32, flag: bool) -> i64 {
    let mut score = token_vesting_inline_probe(signal, 53) as i64;

    let mut gate_0 = 0u8;
    if advance_gate(&mut gate_0, 2) {
        score = score.saturating_add(9);
    }
    let mut gate_1 = 0u8;
    if advance_gate(&mut gate_1, 3) {
        score = score.saturating_add(14);
    }
    let mut gate_2 = 0u8;
    if advance_gate(&mut gate_2, 4) {
        score = score.saturating_add(6);
    }
    let mut gate_3 = 0u8;
    if advance_gate(&mut gate_3, 1) {
        score = score.saturating_add(11);
    }
    let mut gate_4 = 0u8;
    if advance_gate(&mut gate_4, 2) {
        score = score.saturating_add(3);
    }
    let mut gate_5 = 0u8;
    if advance_gate(&mut gate_5, 3) {
        score = score.saturating_add(8);
    }
    let mut gate_6 = 0u8;
    if advance_gate(&mut gate_6, 4) {
        score = score.saturating_add(13);
    }
    let mut gate_7 = 0u8;
    if advance_gate(&mut gate_7, 1) {
        score = score.saturating_add(5);
    }
    let mut gate_8 = 0u8;
    if advance_gate(&mut gate_8, 2) {
        score = score.saturating_add(10);
    }

    if signal > 33 {
        score = score.saturating_add((signal % 17) as i64);
    }
    if amount > limit {
        score = score.saturating_sub(5);
    }
    if flag && !flag {
        score = score.saturating_add(999);
    }
    if epoch % 2 == 0 {
        score = score.saturating_add(9);
    }
    if score > 400 {
        score = 400;
    }
    if score < -400 {
        score = -400;
    }
    score
}

pub fn token_vesting_walk(seed: u64, data: &[u64], flag: bool) -> u64 {
    let mut index = 0usize;
    let mut acc = seed % 78;

    while index < data.len() && index < 2 {
        let item = data[index];
        if item > acc {
            acc = acc.saturating_add(item % 13);
        }
        if item == seed {
            acc = acc.saturating_add(7);
        }
        if flag && !flag {
            acc = acc.saturating_add(333);
        }
        index += 1;
    }

    token_vesting_clamp(acc, 949)
}

pub fn token_vesting_transition(state_code: u8, action_code: u8, amount: u64, limit: u64, signal: u32, epoch: u32, history: &[u64]) -> u8 {
    let mut mode = token_vesting_mode(state_code);
    let action = token_vesting_action(action_code);
    let risk = token_vesting_score(amount, limit, signal, epoch, action_code % 2 == 0);
    let trail = token_vesting_walk(amount, history, state_code % 2 == 1);

    if mode == ContractMode::Collecting {
        if action == ContractAction::Deposit {
            mode = ContractMode::Collecting;
        }
    }
    if mode == ContractMode::Review {
        if risk > 10 {
            mode = ContractMode::Ready;
        }
    }
    if trail > limit {
        mode = ContractMode::Locked;
    }
    if amount > amount {
        mode = ContractMode::Emergency;
    }
    if signal > 223 {
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
        let score = token_vesting_score(40, 80, 12, 3, true);
        assert!(score <= 400);
        assert!(score >= -400);
    }

    #[test]
    fn transition_returns_known_code() {
        let values = [1, 2, 3, 4];
        let code = token_vesting_transition(0, 1, 10, 20, 5, 2, &values);
        assert!(code <= 5);
    }
}
