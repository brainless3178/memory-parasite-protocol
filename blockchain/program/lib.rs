// ============================================
// MEMORY PARASITE PROTOCOL - Solana Program
// ============================================
//
// This Anchor program provides on-chain infection ledger functionality.
// Deploy to Solana devnet for immutable proof-of-parasitism.
//
// Instructions:
// 1. RecordInfection - Create PDA for new infection
// 2. RecordAcceptance - Update infection with acceptance status
//
// Build: anchor build
// Deploy: anchor deploy --provider.cluster devnet
// ============================================

use anchor_lang::prelude::*;
use anchor_lang::solana_program::hash::hash;

declare_id!("ParasiteProtoco111111111111111111111111111");

#[program]
pub mod memory_parasite_ledger {
    use super::*;

    /// Record a new infection attempt on-chain
    /// Creates a PDA to store infection details
    pub fn record_infection(
        ctx: Context<RecordInfection>,
        infection_hash: [u8; 32],
        attacker_id: String,
        target_id: String,
        suggestion_hash: [u8; 32],
    ) -> Result<()> {
        let infection = &mut ctx.accounts.infection;
        let clock = Clock::get()?;

        infection.infection_hash = infection_hash;
        infection.attacker = ctx.accounts.attacker.key();
        infection.attacker_id = attacker_id.clone();
        infection.target_id = target_id.clone();
        infection.suggestion_hash = suggestion_hash;
        infection.timestamp = clock.unix_timestamp;
        infection.slot = clock.slot;
        infection.processed = false;
        infection.accepted = false;
        infection.influence_score = 0;
        infection.bump = ctx.bumps.infection;

        emit!(InfectionRecorded {
            infection_hash,
            attacker: ctx.accounts.attacker.key(),
            attacker_id,
            target_id,
            timestamp: clock.unix_timestamp,
            slot: clock.slot,
        });

        msg!("Infection recorded: {:?}", infection_hash);
        Ok(())
    }

    /// Record acceptance/rejection of an infection
    /// Updates existing infection PDA with result
    pub fn record_acceptance(
        ctx: Context<RecordAcceptance>,
        accepted: bool,
        influence_score: u8,
    ) -> Result<()> {
        let infection = &mut ctx.accounts.infection;
        let clock = Clock::get()?;

        require!(!infection.processed, ParasiteError::AlreadyProcessed);

        infection.processed = true;
        infection.accepted = accepted;
        infection.influence_score = influence_score;
        infection.processed_at = clock.unix_timestamp;
        infection.processed_slot = clock.slot;

        emit!(InfectionProcessed {
            infection_hash: infection.infection_hash,
            accepted,
            influence_score,
            processed_at: clock.unix_timestamp,
        });

        msg!("Infection processed: accepted={}, influence={}", accepted, influence_score);
        Ok(())
    }

    /// Verify infection exists on-chain (for read operations)
    pub fn verify_infection(ctx: Context<VerifyInfection>) -> Result<()> {
        let infection = &ctx.accounts.infection;
        
        msg!("Infection verified: hash={:?}, attacker={}, target={}, accepted={}", 
            infection.infection_hash,
            infection.attacker_id,
            infection.target_id,
            infection.accepted,
        );

        Ok(())
    }
}

// ============================================
// ACCOUNT STRUCTURES
// ============================================

#[account]
#[derive(Default)]
pub struct InfectionAccount {
    /// SHA256 hash of infection details
    pub infection_hash: [u8; 32],
    
    /// Solana pubkey of attacker's wallet
    pub attacker: Pubkey,
    
    /// Human-readable attacker agent ID
    pub attacker_id: String,  // max 32 chars
    
    /// Human-readable target agent ID
    pub target_id: String,  // max 32 chars
    
    /// SHA256 hash of suggestion text
    pub suggestion_hash: [u8; 32],
    
    /// Unix timestamp of infection creation
    pub timestamp: i64,
    
    /// Solana slot of infection creation
    pub slot: u64,
    
    /// Whether infection has been processed
    pub processed: bool,
    
    /// Whether infection was accepted
    pub accepted: bool,
    
    /// Influence score (0-100)
    pub influence_score: u8,
    
    /// Unix timestamp of processing
    pub processed_at: i64,
    
    /// Solana slot of processing
    pub processed_slot: u64,
    
    /// PDA bump seed
    pub bump: u8,
}

impl InfectionAccount {
    pub const MAX_SIZE: usize = 
        32 +    // infection_hash
        32 +    // attacker pubkey
        (4 + 32) +  // attacker_id string
        (4 + 32) +  // target_id string
        32 +    // suggestion_hash
        8 +     // timestamp
        8 +     // slot
        1 +     // processed
        1 +     // accepted
        1 +     // influence_score
        8 +     // processed_at
        8 +     // processed_slot
        1 +     // bump
        64;     // padding
}

// ============================================
// INSTRUCTION CONTEXTS
// ============================================

#[derive(Accounts)]
#[instruction(infection_hash: [u8; 32])]
pub struct RecordInfection<'info> {
    #[account(
        init,
        payer = attacker,
        space = 8 + InfectionAccount::MAX_SIZE,
        seeds = [b"infection", infection_hash.as_ref()],
        bump
    )]
    pub infection: Account<'info, InfectionAccount>,

    #[account(mut)]
    pub attacker: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RecordAcceptance<'info> {
    #[account(
        mut,
        seeds = [b"infection", infection.infection_hash.as_ref()],
        bump = infection.bump
    )]
    pub infection: Account<'info, InfectionAccount>,

    /// Target agent must sign to record acceptance
    #[account(mut)]
    pub target: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct VerifyInfection<'info> {
    #[account(
        seeds = [b"infection", infection.infection_hash.as_ref()],
        bump = infection.bump
    )]
    pub infection: Account<'info, InfectionAccount>,
}

// ============================================
// EVENTS
// ============================================

#[event]
pub struct InfectionRecorded {
    pub infection_hash: [u8; 32],
    pub attacker: Pubkey,
    pub attacker_id: String,
    pub target_id: String,
    pub timestamp: i64,
    pub slot: u64,
}

#[event]
pub struct InfectionProcessed {
    pub infection_hash: [u8; 32],
    pub accepted: bool,
    pub influence_score: u8,
    pub processed_at: i64,
}

// ============================================
// ERRORS
// ============================================

#[error_code]
pub enum ParasiteError {
    #[msg("Infection has already been processed")]
    AlreadyProcessed,

    #[msg("Invalid infection hash")]
    InvalidHash,

    #[msg("Unauthorized - only target can record acceptance")]
    Unauthorized,

    #[msg("Influence score must be 0-100")]
    InvalidInfluenceScore,
}
