// apiService.ts

import axios from "axios";
import type {
  Account,
  AccountCreate,
  AccountSummary,
  BalanceResult,
  IngestResult,
  MonthlyBalanceResult,
  Transaction,
} from "../types.d.ts";

// Define the base URL for the API
const BASE_URL = "http://localhost:8000/api";

// Create an axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Define API functions with type annotations

/**
 * Get all accounts with optional filters.
 * @param institution - Optional filter by institution
 * @param name - Optional filter by account name
 * @param skip - Number of records to skip
 * @param limit - Number of records to return
 * @returns A promise that resolves to an array of accounts
 */
export const getAccounts = async (
  institution?: string,
  name?: string,
  skip = 0,
  limit = 100
): Promise<Account[]> => {
  const response = await apiClient.get("/accounts/", {
    params: {
      institution,
      name,
      skip,
      limit,
    },
  });
  return response.data;
};

/**
 * Create one or more accounts.
 * @param accounts - Array of accounts to create
 * @returns A promise that resolves to the created account(s)
 */
export const createAccounts = async (
  accounts: AccountCreate | AccountCreate[]
): Promise<Account | Account[]> => {
  const response = await apiClient.post("/accounts/", accounts);
  return response.data;
};

/**
 * Get an account by its ID.
 * @param accountId - The ID of the account
 * @returns A promise that resolves to the account
 */
export const getAccountById = async (accountId: number): Promise<Account> => {
  const response = await apiClient.get(`/accounts/${accountId}/`);
  return response.data;
};

/**
 * Get all transactions for a specific account.
 * @param accountId - The ID of the account
 * @param skip - Number of records to skip
 * @param limit - Number of records to return
 * @returns A promise that resolves to an array of transactions
 */
export const getTransactionsForAccount = async (
  accountId: number,
  skip = 0,
  limit = 100
): Promise<Transaction[]> => {
  const response = await apiClient.get(`/accounts/${accountId}/transactions/`, {
    params: {
      skip,
      limit,
    },
  });
  return response.data;
};

/**
 * Ingest transactions for a specific account.
 * @param accountId - The ID of the account
 * @param formData - The form data containing the file to upload
 * @returns A promise that resolves to the ingest result
 */
export const ingestTransactions = async (
  accountId: number,
  formData: FormData
): Promise<IngestResult> => {
  const response = await apiClient.post(
    `/accounts/${accountId}/transactions/`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
};

/**
 * Get the balance for a specific account with optional date filters.
 * @param accountId - The ID of the account
 * @param startDate - Optional start date for the balance calculation
 * @param endDate - Optional end date for the balance calculation
 * @returns A promise that resolves to the balance result
 */
export const getAccountBalance = async (
  accountId: number,
  startDate?: string,
  endDate?: string
): Promise<BalanceResult> => {
  const response = await apiClient.get(`/accounts/${accountId}/balance/`, {
    params: {
      start_date: startDate,
      end_date: endDate,
    },
  });
  return response.data;
};

/**
 * Get the monthly balances for a specific account.
 * @param accountId - The ID of the account
 * @returns A promise that resolves to the monthly balance result
 */
export const getMonthlyBalances = async (
  accountId: number
): Promise<MonthlyBalanceResult> => {
  const response = await apiClient.get(
    `/accounts/${accountId}/monthly_balances/`
  );
  return response.data;
};

export const getAccountsSummary = async (): Promise<AccountSummary[]> => {
  const response = await apiClient.get("/accounts/summary/");
  return response.data;
};
