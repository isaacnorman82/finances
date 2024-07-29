export type AcBehaviour = "standard" | "crowdProperty";

export type AcType =
  | "currentAccount"
  | "asset"
  | "cashIsa"
  | "creditCard"
  | "ifIsa"
  | "juniorIsa"
  | "loan"
  | "mortgage"
  | "pension"
  | "savingsAccount"
  | "shareIsa"
  | "stockbroker";

export type IngestType =
  | "crowdPropertyCsv"
  | "csv"
  | "moneyFarmCsv"
  | "ofxTransactions";

export interface AccountCreate {
  institution: string;
  name: string;
  accountType: AcType;
  accountBehaviour?: AcBehaviour;
  defaultIngestType?: IngestType;
  isActive?: boolean;
  description?: string | null;
}

export interface Account extends AccountCreate {
  id: number;
}

export interface Transaction {
  id: number;
  accountId: number;
  dateTime: string; // ISO 8601 date-time string
  amount: string;
  transactionType?: string | null;
  description?: string | null;
  reference?: string | null;
  notes?: string | null;
}

export interface BalanceResult {
  accountId: number;
  balance: string;
  lastTransactionDate?: string | null;
  startDate?: string | null;
  endDate?: string | null;
}

export interface IngestResult {
  accountId: number;
  transactionsDeleted?: number;
  transactionsInserted?: number;
  startDate?: string | null;
  endDate?: string | null;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface HTTPValidationError {
  detail: ValidationError[];
}

export interface MonthlyBalance {
  yearMonth: string;
  startBalance: string;
  monthlyBalance: string;
  endBalance: string;
}

export interface MonthlyBalanceResult {
  accountId: number;
  monthlyBalances: MonthlyBalance[];
  startYearMonth: string;
  endYearMonth: string;
}

export interface AccountSummary {
  account: Account;
  balance: string;
  monthlyBalances: MonthlyBalanceResult;
  lastTransactionDate: string | null;
}

export enum Timescale {
  All = 0,
  FiveYears = 60,
  TwoYears = 24,
  OneYear = 12,
  SixMonths = 6,
  ThreeMonths = 3,
  OneMonth = 1,
}

export enum MonthChangeAction {
  First = "first",
  Last = "last",
  Next = "next",
  Prev = "prev",
}
