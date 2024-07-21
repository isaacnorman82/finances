<template>
  <div class="container">
    <h1>Accounts</h1>
    <div class="filters">
      <div class="filter">
        <label for="activeFilter">Hide Closed Accounts:</label>
        <input type="checkbox" id="activeFilter" v-model="isActiveFilter" />
      </div>
      <div class="filter">
        <label for="hideValues">Hide values:</label>
        <input type="checkbox" id="hideValues" v-model="hideValues" />
      </div>
    </div>
    <table class="account-table">
      <thead>
        <tr>
          <th @click="toggleSort('institution')">Institution</th>
          <th @click="toggleSort('name')">Name</th>
          <th @click="toggleSort('balance')">Balance</th>
          <th @click="toggleSort('lastTransactionDate')">
            Last Transaction Date
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="account in sortedAccounts"
          :key="account.id"
          @click="navigateToAccountDetails(account.id)"
        >
          <td>{{ account.institution }}</td>
          <td>{{ account.name }}</td>
          <td
            :class="{
              'negative-balance': parseFloat(account.balance) < 0,
              blurred: hideValues,
            }"
          >
            {{ hideValues ? "xxxx.xx" : formatBalance(account.balance) }}
          </td>
          <td>{{ formatLastTransactionDate(account.lastTransactionDate) }}</td>
        </tr>
      </tbody>
    </table>
    <div class="total-balance">
      Total Balance: {{ hideValues ? "xxxx.xx" : formatBalance(totalBalance) }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from "vue";
import { getAccounts, getAccountBalance } from "../services/apiService";
import type { Account, BalanceResult, ExtendedAccount } from "../types";

export default defineComponent({
  name: "AccountsView",

  methods: {
    navigateToAccountDetails(accountId: number) {
      this.$router.push({ name: "account-details", params: { id: accountId } });
    },
  },

  setup() {
    const accounts = ref<ExtendedAccount[]>([]);
    const sortKey = ref<keyof Account>("name");
    const sortOrder = ref<string>("asc");
    const isActiveFilter = ref<boolean>(true);
    const hideValues = ref<boolean>(false);

    const fetchAccounts = async () => {
      try {
        const fetchedAccounts = await getAccounts();
        const accountsWithDetails: ExtendedAccount[] = await Promise.all(
          fetchedAccounts.map(async (account: Account) => {
            const balanceResult: BalanceResult = await getAccountBalance(
              account.id
            );
            return {
              ...account,
              balance: balanceResult.balance,
              lastTransactionDate: balanceResult.last_transaction_date,
            };
          })
        );
        accounts.value = accountsWithDetails;
      } catch (error) {
        console.error("Error fetching accounts:", error);
      }
    };

    onMounted(() => {
      fetchAccounts();
    });

    const filteredAccounts = computed(() => {
      return accounts.value.filter((account) =>
        isActiveFilter.value ? account.is_active : true
      );
    });

    const sortedAccounts = computed(() => {
      return [...filteredAccounts.value].sort((a, b) => {
        const aValue = a[sortKey.value] ?? "";
        const bValue = b[sortKey.value] ?? "";
        if (aValue < bValue) return sortOrder.value === "asc" ? -1 : 1;
        if (aValue > bValue) return sortOrder.value === "asc" ? 1 : -1;
        return 0;
      });
    });

    const formatBalance = (balance: string) => {
      const parsedBalance = Math.abs(parseFloat(balance)); // Remove the minus sign
      return `£${parsedBalance.toFixed(2)}`;
    };

    const formatLastTransactionDate = (dateTime: string | null) => {
      if (!dateTime) return "N/A";

      // Parse the date
      const date = new Date(dateTime);
      const now = new Date();
      const diffTime = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

      // Format date as dd/mm/yy
      const day = String(date.getDate()).padStart(2, "0");
      const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are zero-based
      const year = date.getFullYear().toString().slice(-2); // Get last 2 digits of the year

      return `${day}/${month}/${year} (${diffDays} days ago)`;
    };

    const totalBalance = computed(() => {
      return filteredAccounts.value.reduce((total, account) => {
        return total + parseFloat(account.balance);
      }, 0);
    });

    const toggleSort = (key: keyof Account) => {
      if (sortKey.value === key) {
        sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
      } else {
        sortKey.value = key;
        sortOrder.value = "asc";
      }
    };

    return {
      accounts,
      sortKey,
      sortOrder,
      isActiveFilter,
      hideValues,
      sortedAccounts,
      formatBalance,
      formatLastTransactionDate,
      totalBalance,
      toggleSort,
    };
  },
});
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 20px;
}

.filters {
  display: flex;
  gap: 20px; /* Space between checkboxes */
  margin-bottom: 20px;
}

.filter {
  display: flex;
  align-items: center;
}

.account-table {
  border-collapse: collapse;
  width: 80%; /* Adjust width as needed */
  margin-top: 20px;
}

.account-table th,
.account-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center; /* Center text in cells */
}

.account-table th {
  cursor: pointer;
  background-color: #f2f2f2;
}

.account-table tr:nth-child(even) {
  background-color: #f9f9f9;
}

.account-table tr:hover {
  background-color: #ddd;
}

.negative-balance {
  color: red; /* Color for negative balances */
}

.blurred {
  color: #ccc; /* Color for hidden values */
  font-weight: bold;
}

.total-balance {
  margin-top: 20px;
  font-size: 1.2em;
  font-weight: bold;
  text-align: center;
}
</style>
