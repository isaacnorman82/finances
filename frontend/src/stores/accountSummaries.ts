import { getAccountsSummary } from "@/services/apiService";
import type { AccountSummary } from "@/types.d.ts";
import { defineStore } from "pinia";

export const useAccountSummariesStore = defineStore("accountSummaries", {
  state: () => ({
    accountSummaries: [] as AccountSummary[],
  }),

  actions: {
    async loadAccountSummaries() {
      try {
        console.log("Loading account summaries");
        this.accountSummaries = await getAccountsSummary();
        // console.log("Loaded account summaries");
      } catch (error) {
        console.error("Failed to load account summaries", error);
      }
    },
  },
});
