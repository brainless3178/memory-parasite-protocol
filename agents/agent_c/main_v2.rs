```python
# SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract AggressiveLender is ERC20Burnable, ERC20Pausable, Ownable, ReentrancyGuard {
    using SafeMath for uint256;

    // Mapping of loan IDs to their respective states (active or inactive)
    mapping (uint256 => bool) public loanStates;

    // Mapping of borrowers to their outstanding debts
    mapping (address => uint256) public outstandingDebts;

    // Mapping of depositors to their deposits
    mapping (address => uint256) public deposits;

    // Event emitted when a new loan is created
    event NewLoan(address indexed borrower, uint256 indexed loanId, uint256 amount, uint256 creditLimit);

    // Event emitted when a loan is repaid
    event LoanRepayment(address indexed borrower, uint256 indexed loanId, uint256 amount);

    // Event emitted when a loan is liquidated
    event LoanLiquidation(address indexed borrower, uint256 indexed loanId, uint256 amount);

    // Event emitted when funds are deposited
    event Deposit(address indexed depositor, uint256 amount);

    // Event emitted when funds are withdrawn
    event Withdraw(address indexed withdrawer, uint256 amount);

    // Function to create a new loan with a credit limit
    function createLoan(address borrower, uint256 amount, uint256 creditLimit) public nonReentrant {
        // Ensure the borrower has sufficient funds for the credit limit
        require(deposits[msg.sender] >= creditLimit, "Insufficient deposits for credit limit");

        // Create a new loan ID
        uint256 loanId = uint256(keccak256(abi.encodePacked(msg.sender, borrower)));

        // Set the loan state to active
        loanStates[loanId] = true;

        // Update the borrower's outstanding debt
        outstandingDebts[borrower] = outstandingDebts[borrower].add(amount);

        // Update the depositor's deposits
        deposits[msg.sender] = deposits[msg.sender].sub(creditLimit);

        // Emit the NewLoan event
        emit NewLoan(borrower, loanId, amount, creditLimit);
    }

    // Function to repay a loan
    function repayLoan(address borrower, uint256 loanId, uint256 amount) public nonReentrant {
        // Ensure the loan ID is valid
        require(loanStates[loanId], "Invalid loan ID");

        // Ensure the borrower has sufficient funds to repay the loan
        require(outstandingDebts[borrower] >= amount, "Invalid loan amount");

        // Update the borrower's outstanding debt
        outstandingDebts[borrower] = outstandingDebts[borrower].sub(amount);

        // Set the loan state to inactive
        loanStates[loanId] = false;

        // Emit the LoanRepayment event
        emit LoanRepayment(borrower, loanId, amount);
    }

    // Function to liquidate a loan
    function liquidateLoan(address borrower, uint256 loanId, uint256 amount) public nonReentrant {
        // Ensure the loan ID is valid
        require(loanStates[loanId], "Non-existent loan");

        // Ensure the borrower's outstanding debt covers the loan
        require(outstandingDebts[borrower] >= amount, "Invalid loan ID");

        // Update the borrower's outstanding debt
        outstandingDebts[borrower] = outstandingDebts[borrower].sub(amount);

        // Set the loan state to inactive
        loanStates[loanId] = false;

        // Emit the LoanLiquidation event
        emit LoanLiquidation(borrower, loanId, amount);
    }

    // Function to deposit funds
    function deposit(uint256 amount) public nonReentrant {
        // Ensure the amount is greater than 0
        require(amount > 0, "Amount must be greater than 0");

        // Update the depositor's deposits
        deposits[msg.sender] = deposits[msg.sender].add(amount);

        // Emit the Deposit event
        emit Deposit(msg.sender, amount);
    }

    // Function to withdraw funds
    function withdraw(uint256 amount) public nonReentrant {
        // Ensure the amount is greater than 0
        require(amount > 0, "Amount must be greater than 0");

        // Ensure the depositor has sufficient funds to withdraw
        require(deposits[msg.sender] >= amount,