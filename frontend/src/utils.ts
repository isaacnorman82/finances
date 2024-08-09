import type { AccountSummary, MonthlyBalance } from "@/types.d";
import { MonthYear, Timescale } from "@/types.d";
import { ChartData } from "chart.js";
import { startOfMonth, subMonths } from "date-fns";
import { useDataSeriesStore } from "./stores/dataSeries";

export function formatBalance(balance: string | number): string {
  if (balance === undefined) return "Error";

  const numericBalance =
    typeof balance === "string" ? parseFloat(balance) : balance;

  if (isNaN(numericBalance)) return "Error";

  const formattedBalance = numericBalance.toLocaleString("en-GB", {
    style: "currency",
    currency: "GBP",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  if (numericBalance < 0) {
    return `<span style="color: red">${formattedBalance}</span>`;
  }
  return formattedBalance;
}

export function formatDate(dateTime: string): string {
  if (!dateTime) return "N/A";

  // Parse the date
  const date = new Date(dateTime);

  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are zero-based
  const year = date.getFullYear().toString();

  return `${day}/${month}/${year}`;
}

export const formatLastTransactionDate = (dateTime: string | null) => {
  if (!dateTime) return "N/A";

  // Parse the date
  const date = new Date(dateTime);
  const now = new Date();
  const diffTime = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  return `${formatDate(dateTime)} (${diffDays} days ago)`;
};

export function calculateBalanceChange(
  timescale: Timescale,
  accountSummary: AccountSummary
): string {
  const monthlyBalances = accountSummary.monthlyBalances.monthlyBalances;

  const currentDate = new Date();
  let startDate: Date;

  if (timescale === Timescale.All) {
    startDate = new Date(accountSummary.monthlyBalances.startYearMonth + "-01");
  } else {
    startDate = subMonths(currentDate, timescale);
    startDate = startOfMonth(startDate); // Set start date to the beginning of the previous month
    // Ensure startDate does not go before the first available balance
    if (
      startDate <
      new Date(accountSummary.monthlyBalances.startYearMonth + "-01")
    ) {
      startDate = new Date(
        accountSummary.monthlyBalances.startYearMonth + "-01"
      );
    }
  }

  const endDate = new Date(accountSummary.monthlyBalances.endYearMonth + "-01");

  // console.log(
  //   "Calculating balance change for timescale, start, end",
  //   timescale,
  //   startDate,
  //   endDate
  // );

  // Find the closest balance entries for startDate and endDate
  const startBalanceEntry = monthlyBalances.find(
    (balance) => new Date(balance.yearMonth + "-01") >= startDate
  );
  const endBalanceEntry = monthlyBalances
    .filter((balance) => new Date(balance.yearMonth + "-01") <= endDate)
    .pop(); // Get the last entry before or equal to endDate

  // console.log("Found balance entries", startBalanceEntry, endBalanceEntry);

  // Use the start balance entry or zero if not found and timescale is not All
  const startBalance =
    startBalanceEntry && timescale !== Timescale.All
      ? parseFloat(startBalanceEntry.endBalance)
      : 0;
  const endBalance = endBalanceEntry
    ? parseFloat(endBalanceEntry.endBalance)
    : parseFloat(accountSummary.balance);

  const balanceChange = endBalance - startBalance;
  const percentageChange = startBalance
    ? (balanceChange / startBalance) * 100
    : 0;

  const sign = balanceChange > 0 ? "+" : "-";

  let formattedChange = `${sign}£${Math.abs(balanceChange).toFixed(2)}`;

  if (startBalance !== 0) {
    formattedChange += ` (${Math.abs(percentageChange).toFixed(2)}%)`;
  }

  return formattedChange;
}

export function sumMonthlyBalances(
  accountSummaries: AccountSummary[],
  timescale: Timescale
): string {
  const now = new Date();
  const endYearMonth = `${now.getFullYear()}-${String(
    now.getMonth() + 1
  ).padStart(2, "0")}`;

  // Calculate startYearMonth based on the timescale
  let startYearMonth: string;
  if (timescale === Timescale.All) {
    startYearMonth = "0000-00"; // effectively no limit
  } else {
    const startDate = new Date(now);
    startDate.setMonth(now.getMonth() - timescale);
    startYearMonth = `${startDate.getFullYear()}-${String(
      startDate.getMonth() + 1
    ).padStart(2, "0")}`;
  }

  let totalBalance = 0;

  accountSummaries.forEach((summary) => {
    summary.monthlyBalances.monthlyBalances.forEach((balance) => {
      if (
        balance.yearMonth >= startYearMonth &&
        balance.yearMonth <= endYearMonth
      ) {
        totalBalance += parseFloat(balance.monthlyBalance);
      }
    });
  });
  return totalBalance.toFixed(2);
}

export function sumAccountBalances(accountSummaries: AccountSummary[]): string {
  let totalBalance = 0;

  accountSummaries.forEach((summary) => {
    totalBalance += parseFloat(summary.balance);
  });

  return totalBalance.toFixed(2);
}

export function getBalanceForDate(
  accountSummary: AccountSummary,
  date: MonthYear
): MonthlyBalance | null {
  const yearMonth = `${date.year}-${date.month.toString().padStart(2, "0")}`;
  return (
    accountSummary.monthlyBalances.monthlyBalances.find(
      (balance: MonthlyBalance) => balance.yearMonth === yearMonth
    ) || null
  );
}

export function findAccountSummaryFromLabel(
  accountString: string,
  summaries: AccountSummary[]
): AccountSummary | null {
  const [institution, name] = accountString.split(" - ");
  return (
    summaries.find(
      (summary) =>
        summary.account.institution === institution &&
        summary.account.name === name
    ) ?? null
  );
}

export function formatTaxYear(date: string): string {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = d.getMonth() + 1;
  return month < 4
    ? `${year - 1}/${year.toString().slice(-2)}`
    : `${year}/${(year + 1).toString().slice(-2)}`;
}

export function formatMonthYear(date: string): string {
  const d = new Date(date);
  const month = (d.getMonth() + 1).toString().padStart(2, "0");
  const year = d.getFullYear();

  return `${month}/${year}`;
}

export function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

export function hashStringToNumber(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return hash;
}

// Existing getSeededColor function updated to handle string seeds
export function getSeededColor(seed: number | string): string {
  if (typeof seed === "string") {
    seed = hashStringToNumber(seed);
  }
  const letters = "0123456789ABCDEF";
  let color = "#";
  for (let i = 0; i < 6; i++) {
    const randomIndex = Math.floor(seededRandom(seed + i) * 16);
    color += letters[randomIndex];
  }
  return color;
}

export function dataSeriesToChartData(
  keysOrColorMap: string[] | Record<string, string>,
  formatDate: (dateTime: string) => string = formatTaxYear
): ChartData {
  const dataSeriesStore = useDataSeriesStore();
  const keys = Array.isArray(keysOrColorMap)
    ? keysOrColorMap
    : Object.keys(keysOrColorMap);
  const dataSeriesArray = dataSeriesStore.getDataSeries(keys);

  if (dataSeriesArray.length === 0) {
    return {
      labels: [],
      datasets: [],
    };
  }

  // Extract all unique dates from dataSeriesArray
  const uniqueDates = new Set<string>();
  dataSeriesArray.forEach((dataSeries) => {
    uniqueDates.add(dataSeries.dateTime);
  });

  // Convert uniqueDates to an array and sort them
  const sortedDates = Array.from(uniqueDates).sort(
    (a, b) => new Date(a).getTime() - new Date(b).getTime()
  );

  // Format the sorted dates
  const labels = sortedDates.map((date) => formatDate(date));

  // Create datasets for each key, aligning data with the unique dates
  const datasetsMap = new Map<
    string,
    { label: string; data: (number | null)[]; backgroundColor: string }
  >();

  dataSeriesArray.forEach((dataSeries) => {
    if (!datasetsMap.has(dataSeries.key)) {
      datasetsMap.set(dataSeries.key, {
        label: dataSeries.key,
        data: Array(labels.length).fill(null),
        backgroundColor: Array.isArray(keysOrColorMap)
          ? getSeededColor(dataSeries.key)
          : keysOrColorMap[dataSeries.key],
      });
    }
    const dataset = datasetsMap.get(dataSeries.key)!;
    const dateIndex = sortedDates.indexOf(dataSeries.dateTime);
    if (dateIndex !== -1) {
      dataset.data[dateIndex] = parseFloat(dataSeries.value);
    }
  });

  const datasets = Array.from(datasetsMap.values());

  return {
    labels,
    datasets,
  };
}

export function formatHeaderText(text: string): string {
  return text
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2") // Add space before uppercase letters
    .replace(/^./, (str) => str.toUpperCase()); // Capitalize the first letter
}

export function filterAccountSummaries(
  accountSummaries: AccountSummary[],
  accountTypes: string[]
): AccountSummary[] {
  const includesClosed = accountTypes.includes("isClosed");

  // First filter based on isActive status
  const activeFilteredAccounts = accountSummaries.filter((summary) => {
    return includesClosed || summary.account.isActive;
  });

  // Then filter based on account types
  return activeFilteredAccounts.filter((summary) => {
    return accountTypes.includes(summary.account.accountType);
  });
}
