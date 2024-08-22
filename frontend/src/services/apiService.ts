// apiService.ts

import axios from "axios";
import camelcaseKeys from "camelcase-keys";
import type {
  Account,
  AccountCreate,
  AccountSummary,
  APIVersionType,
  BalanceResult,
  DataSeries,
  DataSeriesCreate,
  InflationRates,
  IngestResult,
  MonthlyBalanceResult,
  Transaction,
} from "../types.d.ts";

// Helper function to convert response data to camelCase
const convertToCamelCase = (data: any) => {
  return camelcaseKeys(data, { deep: true });
};

// Define the base URL for the API
const BASE_URL = "http://localhost:8000/api";

// Create an axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add a response interceptor to convert all responses to camelCase
apiClient.interceptors.response.use(
  (response) => {
    response.data = convertToCamelCase(response.data);
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

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
 * @param startDate - Optional start date for transactions
 * @param endDate - Optional end date for transactions
 * @param skip - Number of records to skip
 * @param limit - Number of records to return
 * @returns A promise that resolves to an array of transactions
 */
export const getTransactionsForAccount = async (
  accountId: number,
  startDate?: string,
  endDate?: string,
  skip?: number,
  limit?: number
): Promise<Transaction[]> => {
  const params: any = {
    ...(startDate && { start_date: startDate }),
    ...(endDate && { end_date: endDate }),
    ...(skip !== undefined && { skip }),
    ...(limit !== undefined && { limit }),
  };
  const response = await apiClient.get(`/accounts/${accountId}/transactions/`, {
    params,
  });
  return response.data;
};

/**
 * Ingest transactions for a specific account.
 * @param accountId - The ID of the account
 * @param formData - The form data containing the file to upload
 * @param ingestType - The type of ingestion (optional, passed as a query string if provided)
 * @returns A promise that resolves to the ingest result
 */
export const ingestTransactions = async (
  accountId: number,
  formData: FormData,
  ingestType?: string
): Promise<IngestResult> => {
  // Construct the URL
  let url = `/accounts/${accountId}/transactions/`;
  if (ingestType) {
    url += `?ingest_type=${encodeURIComponent(ingestType)}`;
  }

  // Make the API request
  const response = await apiClient.post(url, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

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
    `/accounts/${accountId}/monthlyBalances/`
  );
  return response.data;
};

/**
 * Get the summary of all accounts.
 * @param interpolate - Optional flag to interpolate missing balances
 * @returns A promise that resolves to an array of account summaries
 */
export const getAccountsSummary = async (
  interpolate: boolean
): Promise<AccountSummary[]> => {
  const response = await apiClient.get(`/accounts/summary/`, {
    params: { interpolate },
  });
  return response.data;
};

/**
 * Get all data series.
 * @param keys A single key or a list of keys (comma-separated string or array of strings)
 * @returns A promise that resolves to an array of data series
 */
export const getDataSeries = async (
  keys?: string | string[]
): Promise<DataSeries[]> => {
  // If keys is an array, join it into a comma-separated string
  const formattedKeys = Array.isArray(keys) ? keys.join(",") : keys;

  const response = await apiClient.get("/dataseries/", {
    params: {
      keys: formattedKeys,
    },
  });

  return response.data;
};

/**
 * Create a data series entry.
 * @param dataSeries - Data series entry to create
 * @returns A promise that resolves to the created data series entry
 */
export const createDataSeries = async (
  dataSeries: DataSeriesCreate
): Promise<DataSeries> => {
  const response = await apiClient.post("/dataseries/", dataSeries);
  return response.data;
};

export const getAPIVersion = async (): Promise<APIVersionType> => {
  const response = await apiClient.get<APIVersionType>("/metadata/version");
  return response.data;
};

export const getIngestValues = async (): Promise<string[]> => {
  const response = await apiClient.get<string[]>("/metadata/ingest-types");
  return response.data;
};

export async function setBalance(
  accountId: number,
  balance: number,
  yearMonth?: string
): Promise<Transaction[]> {
  const response = await apiClient.post<Transaction[]>(
    `/accounts/${accountId}/set-balance/`,
    null,
    {
      params: {
        balance: balance.toString(),
        year_month: yearMonth,
      },
    }
  );

  return response.data;
}

export async function getInflationRates(): Promise<InflationRates> {
  const response = await apiClient.get<InflationRates>("/metadata/cpi/");
  return response.data;
}
