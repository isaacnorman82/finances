// types.ts

export type AcBehaviour = "standard" | "crowd_property";

export type AcType =
  | "current_account"
  | "asset"
  | "cash_isa"
  | "credit_card"
  | "if_isa"
  | "junior_isa"
  | "loan"
  | "mortgage"
  | "pension"
  | "savings_account"
  | "share_isa"
  | "stockbroker";

export type IngestType =
  | "crowd_property_csv"
  | "csv"
  | "money_farm_csv"
  | "ofx_transactions";

export interface Account {
  id: number;
  institution: string;
  name: string;
  account_type: AcType;
  account_behaviour?: AcBehaviour;
  default_ingest_type?: IngestType;
  is_active?: boolean;
  description?: string | null;
}

export interface AccountCreate {
  institution: string;
  name: string;
  account_type: AcType;
  account_behaviour?: AcBehaviour;
  default_ingest_type?: IngestType;
  is_active?: boolean;
  description?: string | null;
}

export interface Transaction {
  id: number;
  account_id: number;
  date_time: string; // ISO 8601 date-time string
  amount: string;
  transaction_type?: string | null;
  description?: string | null;
  reference?: string | null;
  notes?: string | null;
}

export interface BalanceResult {
  account_id: number;
  balance: string;
  last_transaction_date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface IngestResult {
  account_id: number;
  transactions_deleted?: number;
  transactions_inserted?: number;
  start_date?: string | null;
  end_date?: string | null;
}

export interface HTTPValidationError {
  detail: ValidationError[];
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ExtendedAccount extends Account {
  balance: string;
  lastTransactionDate?: string | null; // Include other properties added in fetchAccounts.
}
