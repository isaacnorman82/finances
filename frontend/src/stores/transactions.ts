import { getTransactionsForAccount } from "@/services/apiService";
import type { MonthYear, Transaction } from "@/types.d.ts";
import { defineStore } from "pinia";

// todo make this part of MonthYear type
function getMonthStartEnd(
  month: number,
  year: number
): {
  startDate: string;
  endDate: string;
} {
  // Create start date as the first day of the month in UTC
  const start = new Date(Date.UTC(year, month - 1, 1));
  const startDate = start.toISOString(); // .slice(0, 10); // YYYY-MM-DD

  // Create end date as the last day of the month in UTC
  const end = new Date(Date.UTC(year, month, 0, 23, 59, 59, 999));
  const endDate = end.toISOString(); // Full ISO string including time

  return { startDate, endDate };
}

export const useTransactions = defineStore("transactions", {
  state: () => ({
    transactionsCache: {} as Record<string, Transaction[]>,
  }),

  actions: {
    async fetchTransactions(
      accountId: number,
      selectedDate: MonthYear
    ): Promise<Transaction[]> {
      const { startDate, endDate } = getMonthStartEnd(
        selectedDate.month,
        selectedDate.year
      );
      const cacheKey = `${accountId}-${selectedDate}`;

      if (!this.transactionsCache[cacheKey]) {
        console.log(
          "Cache Miss - Loading transactions for account ID",
          accountId,
          "for",
          selectedDate.toString()
        );
        const transactions = await getTransactionsForAccount(
          accountId,
          startDate,
          endDate
        );
        this.transactionsCache[cacheKey] = transactions;
      }

      return this.transactionsCache[cacheKey];
    },
  },
});
