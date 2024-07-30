import { format as formatDate } from "date-fns";

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

export class MonthYear {
  public year: number;
  public month: number;
  private min?: MonthYear;
  private max?: MonthYear;

  constructor();
  constructor(dateString?: string);
  constructor(dateString?: string) {
    if (dateString) {
      const [year, month] = dateString.split("-").map(Number);
      this.year = year;
      this.month = month;
    } else {
      const currentDate = new Date();
      this.year = currentDate.getUTCFullYear();
      this.month = currentDate.getUTCMonth() + 1;
    }
  }

  toDate(): Date {
    return new Date(Date.UTC(this.year, this.month - 1));
  }

  format(pattern: string): string {
    return formatDate(this.toDate(), pattern);
  }

  compare(other: MonthYear): number {
    if (this.year === other.year) {
      return this.month - other.month;
    }
    return this.year - other.year;
  }

  add(months: number): void {
    const totalMonths = this.year * 12 + (this.month - 1) + months;
    this.year = Math.floor(totalMonths / 12);
    this.month = (totalMonths % 12) + 1;
    this.applyBounds();
  }

  subtract(months: number): void {
    this.add(-months);
  }

  setBounds(min: string, max: string): void {
    this.min = new MonthYear(min);
    this.max = new MonthYear(max);
  }

  toStart(): void {
    if (!this.min) {
      throw new Error(
        "Cannot call toStart() without setting a minimum bound.",
        this
      );
    }
    this.year = this.min.year;
    this.month = this.min.month;
  }

  toEnd(): void {
    if (!this.max) {
      throw new Error(
        "Cannot call toEnd() without setting a maximum bound.",
        this
      );
    }
    this.year = this.max.year;
    this.month = this.max.month;
  }

  get atStart(): boolean {
    return this.min ? this.compare(this.min) === 0 : false;
  }

  get atEnd(): boolean {
    return this.max ? this.compare(this.max) === 0 : false;
  }

  public applyBounds(): void {
    if (this.min && this.compare(this.min) < 0) {
      this.year = this.min.year;
      this.month = this.min.month;
    }
    if (this.max && this.compare(this.max) > 0) {
      this.year = this.max.year;
      this.month = this.max.month;
    }
  }

  public toString(): string {
    return `${this.year.toString().padStart(4, "0")}-${this.month
      .toString()
      .padStart(2, "0")}`;
  }

  public copy(): MonthYear {
    const copy = new MonthYear(this.toString());
    if (this.min) copy.min = new MonthYear(this.min.toString());
    if (this.max) copy.max = new MonthYear(this.max.toString());
    return copy;
  }

  public getMonthsForTimescale(timescale: Timescale): string[] {
    const result: string[] = [];
    const copy = this.copy();

    if (timescale === Timescale.All) {
      copy.toStart();
    } else {
      copy.subtract(timescale - 1);
    }
    let count = 0;

    while (copy.compare(this) < 0) {
      // copy can't go beyond bounds so can't do <=
      result.push(copy.toString());
      copy.add(1);
    }
    result.push(copy.toString());

    return result;
  }
}
