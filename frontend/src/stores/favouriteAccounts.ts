// stores/favoriteAccounts.ts

import { AccountSummary } from "@/types";
import { defineStore } from "pinia";
import { ref } from "vue";
import { useAccountSummariesStore } from "./accountSummaries";

// This store handles favorite accounts
export const useFavoriteAccountsStore = defineStore("favoriteAccounts", () => {
  const favoriteAccounts = ref<number[]>([]);

  // Load favorite accounts from local storage (or API)
  function loadFavoriteAccounts() {
    const storedAccounts = JSON.parse(
      localStorage.getItem("favoriteAccounts") || "[]"
    );
    favoriteAccounts.value = storedAccounts;
  }

  // Check if an account is a favorite
  function isFavAccount(accountId: number): boolean {
    return favoriteAccounts.value.includes(accountId);
  }

  // Set or unset an account as a favorite
  function setFavAccount(accountId: number, newValue: boolean) {
    if (newValue) {
      if (!favoriteAccounts.value.includes(accountId)) {
        favoriteAccounts.value.push(accountId);
      }
    } else {
      favoriteAccounts.value = favoriteAccounts.value.filter(
        (id) => id !== accountId
      );
    }

    // Update local storage after modification
    localStorage.setItem(
      "favoriteAccounts",
      JSON.stringify(favoriteAccounts.value)
    );
  }

  // Get the list of favorite account IDs
  function getFavAccounts(): number[] {
    return favoriteAccounts.value;
  }

  // Get the list of favorite account objects (with full details)
  function getFavAccountObjects(): AccountSummary[] {
    const accountSummariesStore = useAccountSummariesStore();

    // Filter to get only the favorite accounts
    const favoriteAccountsSummaries =
      accountSummariesStore.accountSummaries.filter((summary) =>
        favoriteAccounts.value.includes(summary.account.id)
      );

    // Sort by account type, then institution, then name
    return favoriteAccountsSummaries.sort((a, b) => {
      // Compare by account type
      if (a.account.accountType < b.account.accountType) return -1;
      if (a.account.accountType > b.account.accountType) return 1;

      // If account types are the same, compare by institution
      if (a.account.institution < b.account.institution) return -1;
      if (a.account.institution > b.account.institution) return 1;

      // If institutions are the same, compare by name
      if (a.account.name < b.account.name) return -1;
      if (a.account.name > b.account.name) return 1;

      // If all are the same, return 0 (no change in order)
      return 0;
    });
  }

  return {
    favoriteAccounts,
    loadFavoriteAccounts,
    isFavAccount,
    setFavAccount,
    getFavAccounts,
    getFavAccountObjects,
  };
});
