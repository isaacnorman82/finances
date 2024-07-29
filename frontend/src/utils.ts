import { AccountSummary, MonthlyBalance, Timescale } from "@/types.d";
import { startOfMonth, subMonths } from "date-fns";

export function formatBalance(balance: string | number): string {
  // console.log("Formatting balance", balance);
  if (balance === undefined) return "Error";
  const numericBalance =
    typeof balance === "string" ? parseFloat(balance) : balance;
  const formattedBalance = `£${Math.abs(numericBalance).toFixed(2)}`;

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

export function getBalanceForDate(
  accountSummary: AccountSummary,
  date: Date
): MonthlyBalance | null {
  // console.log("Getting balance for date", date);
  const yearMonth = date.toISOString().slice(0, 7);
  // console.log("Getting balance for date", yearMonth);
  return (
    accountSummary?.monthlyBalances.monthlyBalances.find(
      (mb) => mb.yearMonth === yearMonth
    ) ?? null
  );
}
