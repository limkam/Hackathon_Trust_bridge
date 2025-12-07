use anchor_lang::prelude::*;

declare_id!("FEQJZDk4afcXbSrRj7iW3PieNtrmeT2Hjtt5BCmoNfRr");

// Startup Registry Program ID (for on-chain verification)
use anchor_lang::solana_program::pubkey;
const STARTUP_REGISTRY_PROGRAM_ID: Pubkey = pubkey!("DqwhC5DDZZmL4E1f4YYQJ9R121NurZV8ttk2dfGoYnTj");

#[program]
pub mod investment_ledger {
    use super::*;

    /// Records a new investment transaction
    /// Verifies startup exists on-chain before recording investment
    pub fn record_investment(
        ctx: Context<RecordInvestment>,
        investment_id: String,
        startup_id: String,
        amount_usdc: u64,
    ) -> Result<()> {
        // On-chain verification: Verify startup exists
        // Anchor's account constraint above already verifies:
        // 1. Startup account exists (via PDA seeds)
        // 2. Account is owned by Startup Registry Program (via seeds::program)

        // Verify account is owned by Startup Registry
        require!(
            ctx.accounts.startup.owner == &STARTUP_REGISTRY_PROGRAM_ID,
            ErrorCode::InvalidStartup
        );

        // Verify account has data (more than just discriminator)
        require!(
            ctx.accounts.startup.data_len() > 8,
            ErrorCode::InvalidStartup
        );

        msg!("Startup verified on-chain: {}", startup_id);

        let investment = &mut ctx.accounts.investment;
        let clock = Clock::get()?;

        investment.investment_id = investment_id;
        investment.investor_address = ctx.accounts.investor.key();
        investment.startup_id = startup_id;
        investment.amount_usdc = amount_usdc;
        investment.timestamp = clock.unix_timestamp;
        investment.status = "confirmed".to_string();

        msg!(
            "Investment recorded: {} USDC to {}",
            amount_usdc,
            investment.startup_id
        );
        Ok(())
    }

    /// Gets investment history for an investor
    pub fn get_investment_history(ctx: Context<GetInvestmentHistory>) -> Result<()> {
        let investment = &ctx.accounts.investment;
        msg!("Investment ID: {}", investment.investment_id);
        msg!("Startup: {}", investment.startup_id);
        msg!("Amount: {} USDC", investment.amount_usdc);
        msg!("Status: {}", investment.status);
        Ok(())
    }

    /// Gets all investments for a startup
    pub fn get_startup_investments(ctx: Context<GetStartupInvestments>) -> Result<()> {
        let investment = &ctx.accounts.investment;
        msg!("Startup ID: {}", investment.startup_id);
        msg!("Investment ID: {}", investment.investment_id);
        msg!("Amount: {} USDC", investment.amount_usdc);
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(investment_id: String, startup_id: String)]
pub struct RecordInvestment<'info> {
    #[account(
        init,
        payer = investor,
        space = 8 + 4 + 100 + 32 + 4 + 100 + 8 + 8 + 4 + 20,
        seeds = [b"investment", investment_id.as_bytes()],
        bump
    )]
    pub investment: Account<'info, Investment>,
    #[account(mut)]
    pub investor: Signer<'info>,
    /// Startup account from Startup Registry - verified on-chain
    /// PDA: [b"startup", startup_id.as_bytes()]
    /// Must be owned by Startup Registry Program
    /// CHECK: We verify ownership in the instruction logic
    #[account(
        seeds = [b"startup", startup_id.as_bytes()],
        bump,
        seeds::program = STARTUP_REGISTRY_PROGRAM_ID
    )]
    pub startup: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}

// Startup account structure (matches Startup Registry)
#[account]
pub struct StartupAccount {
    pub startup_id: String,
    pub name: String,
    pub sector: String,
    pub founder_address: Pubkey,
    pub employee_addresses: Vec<String>,
    pub registration_timestamp: i64,
}

#[derive(Accounts)]
pub struct GetInvestmentHistory<'info> {
    pub investment: Account<'info, Investment>,
}

#[derive(Accounts)]
pub struct GetStartupInvestments<'info> {
    pub investment: Account<'info, Investment>,
}

#[account]
pub struct Investment {
    pub investment_id: String,
    pub investor_address: Pubkey,
    pub startup_id: String,
    pub amount_usdc: u64,
    pub timestamp: i64,
    pub status: String,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid investment")]
    InvalidInvestment,
    #[msg("Invalid amount")]
    InvalidAmount,
    #[msg("Invalid startup - startup not found or invalid")]
    InvalidStartup,
}
