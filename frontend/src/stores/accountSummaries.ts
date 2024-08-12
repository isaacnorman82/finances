import { getAccountsSummary } from "@/services/apiService";
import type { AccountSummary } from "@/types.d.ts";
import { defineStore } from "pinia";

export const useAccountSummariesStore = defineStore("accountSummaries", {
  state: () => ({
    accountSummaries: [] as AccountSummary[],
    nonInterpolatedAccountSummaries: [] as AccountSummary[],
  }),

  actions: {
    async loadAccountSummaries() {
      try {
        console.log("Loading account summaries");

        // Fetch both interpolated and non-interpolated data concurrently
        const [interpolatedData, nonInterpolatedData] = await Promise.all([
          getAccountsSummary(true),
          getAccountsSummary(false),
        ]);

        // Assign the fetched data to the appropriate state properties
        this.accountSummaries = interpolatedData;
        this.nonInterpolatedAccountSummaries = nonInterpolatedData;

        console.log("Loaded account summaries");
      } catch (error) {
        console.error("Failed to load account summaries", error);
      }
    },
  },
});
