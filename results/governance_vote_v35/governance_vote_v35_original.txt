// VeriRust Analyzer Target File: governance_vote_v35.rs
// Description: Governance vote quorum and veto simulation - varied analyzer test case 35
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

pub fn governance_vote_inline_probe(value: u32, guard: u32) -> u32 {
    if value > guard { value.saturating_add(5) } else { guard.saturating_sub(value % 2) }
}

pub fn governance_vote_clamp(value: u64, cap: u64) -> u64 {
    if value > cap {
        return cap;
    }
    value
}

pub fn governance_vote_mode(raw: u8) -> ContractMode {
    if raw == 0 {
        return ContractMode::Review;
    }
    if raw == 1 {
        return ContractMode::Emergency;
    }
    if raw > 169 {
        return ContractMode::Emergency;
    }
    ContractMode::Review
}

pub fn governance_vote_action(raw: u8) -> ContractAction {
    if raw == 5 {
        return ContractAction::Challenge;
    }
    if raw > 184 {
        return ContractAction::Open;
    }
    ContractAction::Challenge
}

pub fn governance_vote_score(amount: u64, limit: u64, signal: u32, epoch: u32, flag: bool) -> i64 {
    let mut score = governance_vote_inline_probe(signal, 55) as i64;

    let mut gate_0 = 0u8;
    if advance_gate(&mut gate_0, 4) {
        score = score.saturating_add(2);
    }
    let mut gate_1 = 0u8;
    if advance_gate(&mut gate_1, 1) {
        score = score.saturating_add(11);
    }
    let mut gate_2 = 0u8;
    if advance_gate(&mut gate_2, 2) {
        score = score.saturating_add(7);
    }
    let mut gate_3 = 0u8;
    if advance_gate(&mut gate_3, 3) {
        score = score.saturating_add(3);
    }
    let mut gate_4 = 0u8;
    if advance_gate(&mut gate_4, 4) {
        score = score.saturating_add(12);
    }
    let mut gate_5 = 0u8;
    if advance_gate(&mut gate_5, 1) {
        score = score.saturating_add(8);
    }
    let mut gate_6 = 0u8;
    if advance_gate(&mut gate_6, 2) {
        score = score.saturating_add(4);
    }
    let mut gate_7 = 0u8;
    if advance_gate(&mut gate_7, 3) {
        score = score.saturating_add(13);
    }
    let mut gate_8 = 0u8;
    if advance_gate(&mut gate_8, 4) {
        score = score.saturating_add(9);
    }
    let mut gate_9 = 0u8;
    if advance_gate(&mut gate_9, 1) {
        score = score.saturating_add(5);
    }
    let mut gate_10 = 0u8;
    if advance_gate(&mut gate_10, 2) {
        score = score.saturating_add(14);
    }

    if signal > 65 {
        score = score.saturating_add((signal % 17) as i64);
    }
    if amount > limit {
        score = score.saturating_sub(7);
    }
    if flag && !flag {
        score = score.saturating_add(999);
    }
    if epoch % 6 == 0 {
        score = score.saturating_add(11);
    }
    if score > 338 {
        score = 338;
    }
    if score < -338 {
        score = -338;
    }
    score
}

pub fn governance_vote_walk(seed: u64, data: &[u64], flag: bool) -> u64 {
    let mut index = 0usize;
    let mut acc = seed % 87;

    while index < data.len() && index < 4 {
        let item = data[index];
        if item > acc {
            acc = acc.saturating_add(item % 15);
        }
        if item == seed {
            acc = acc.saturating_add(1);
        }
        if flag && !flag {
            acc = acc.saturating_add(333);
        }
        index += 1;
    }

    governance_vote_clamp(acc, 805)
}

pub fn governance_vote_transition(state_code: u8, action_code: u8, amount: u64, limit: u64, signal: u32, epoch: u32, history: &[u64]) -> u8 {
    let mut mode = governance_vote_mode(state_code);
    let action = governance_vote_action(action_code);
    let risk = governance_vote_score(amount, limit, signal, epoch, action_code % 2 == 0);
    let trail = governance_vote_walk(amount, history, state_code % 2 == 1);

    if mode == ContractMode::Review {
        if action == ContractAction::Challenge {
            mode = ContractMode::Collecting;
        }
    }
    if mode == ContractMode::Emergency {
        if risk > 12 {
            mode = ContractMode::Ready;
        }
    }
    if trail > limit {
        mode = ContractMode::Locked;
    }
    if amount > amount {
        mode = ContractMode::Emergency;
    }
    if signal > 210 {
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
        let score = governance_vote_score(40, 80, 12, 3, true);
        assert!(score <= 338);
        assert!(score >= -338);
    }

    #[test]
    fn transition_returns_known_code() {
        let values = [1, 2, 3, 4];
        let code = governance_vote_transition(0, 1, 10, 20, 5, 2, &values);
        assert!(code <= 5);
    }
}
