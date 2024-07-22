<template>
  <div class="accounts-view">
    <h1>Accounts</h1>
    <div class="filters">
      <div class="filter">
        <label for="hideClosed">Hide Closed Accounts:</label>
        <input type="checkbox" id="hideClosed" v-model="hideClosed" />
      </div>
      <div class="filter">
        <label for="hideValues">Hide values:</label>
        <input type="checkbox" id="hideValues" v-model="hideValues" />
      </div>
    </div>
    <table class="account-table">
      <thead>
        <tr>
          <th @click="sortBy('institution')">
            Institution
            <span v-if="sortKey === 'institution'">
              {{ sortOrder === 1 ? "↓" : "↑" }}
            </span>
          </th>
          <th @click="sortBy('name')">
            Name
            <span v-if="sortKey === 'name'">
              {{ sortOrder === 1 ? "↓" : "↑" }}
            </span>
          </th>
          <th @click="sortBy('balance')">
            Balance
            <span v-if="sortKey === 'balance'">
              {{ sortOrder === 1 ? "↓" : "↑" }}
            </span>
          </th>
          <th @click="sortBy('last_transaction_date')">
            Last Transaction Date
            <span v-if="sortKey === 'last_transaction_date'">
              {{ sortOrder === 1 ? "↓" : "↑" }}
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="entry in filteredSummaries"
          :key="entry.account.id"
          @click="navigateToAccountDetails(entry.account.id)"
        >
          <td>{{ entry.account.institution }}</td>
          <td>{{ entry.account.name }}</td>
          <td
            :class="{
              'negative-balance': parseFloat(entry.balance) < 0,
              'hidden-values': hideValues,
            }"
          >
            {{ hideValues ? "xxxx.xx" : formatBalance(entry.balance) }}
          </td>
          <td>
            {{ formatLastTransactionDate(entry.last_transaction_date) }}
          </td>
        </tr>
      </tbody>
    </table>
    <div class="total-balance">
      Total Balance: {{ hideValues ? "xxxx.xx" : formatBalance(totalBalance) }}
    </div>
    <StackedBarChart :data="chartData" />
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from "vue";
import { getAccountsSummary } from "../services/apiService";
import StackedBarChart from "../components/StackedBarChart.vue";
import type { AccountSummary, Account } from "../types";
import { ChartData } from "chart.js";

export default defineComponent({
  name: "AccountsView",
  components: {
    StackedBarChart,
  },

  methods: {
    navigateToAccountDetails(accountId: number) {
      this.$router.push({ name: "account-details", params: { id: accountId } });
    },

    sortAccounts() {
      this.account_summaries = this.account_summaries.sort((a, b) => {
        let aValue, bValue;

        if (["name", "institution"].includes(this.sortKey)) {
          const key = this.sortKey as keyof Account;
          aValue = a.account[key];
          bValue = b.account[key];
        } else {
          const key = this.sortKey as keyof AccountSummary;
          aValue = a[key];
          bValue = b[key];
        }

        // Check if the values are strings or numbers and compare accordingly
        if (typeof aValue === "string" && typeof bValue === "string") {
          console.log("string compare");
          return this.sortOrder * aValue.localeCompare(bValue);
        } else if (typeof aValue === "number" && typeof bValue === "number") {
          console.log("number compare");
          return this.sortOrder * (aValue - bValue);
        } else {
          console.log("default compare");
          console.log(typeof aValue, typeof bValue);
        }

        return 0;
      });
    },
  },

  watch: {
    // Watchers to call sortAccounts when sortKey or sortOrder changes
    sortKey() {
      this.sortAccounts();
    },
    sortOrder() {
      this.sortAccounts();
    },
  },

  setup() {
    const account_summaries = ref<AccountSummary[]>([]);

    const sortKey = ref<string>("name");
    const sortOrder = ref<number>(1);
    const hideClosed = ref<boolean>(true);
    const hideValues = ref<boolean>(false);

    const fetchAccountSummaries = async () => {
      try {
        account_summaries.value = await getAccountsSummary();
      } catch (error) {
        console.error("Error fetching accounts:", error);
      }
    };

    const sortBy = (key: string) => {
      if (sortKey.value === key) {
        sortOrder.value = -sortOrder.value;
      } else {
        sortKey.value = key;
        sortOrder.value = 1;
      }
    };

    const filteredSummaries = computed(() => {
      return account_summaries.value.filter((summary) => {
        if (hideClosed.value && !summary.account.is_active) {
          return false;
        }
        return true;
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
      return account_summaries.value.reduce((total, accountSummary) => {
        return total + parseFloat(accountSummary.balance);
      }, 0);
    });

    const chartData = computed<ChartData<"bar">>(() => {
      if (account_summaries.value.length === 0) {
        return {
          labels: [],
          datasets: [],
        };
      }

      // Extract all unique labels from all accounts
      const uniqueDates = new Set<string>();
      account_summaries.value.forEach((summary) => {
        summary.monthly_balances.monthly_balances.forEach((mb) => {
          uniqueDates.add(mb.year_month);
        });
      });

      const labels = Array.from(uniqueDates).sort();

      // Create datasets for each account, aligning data with the unique dates
      const datasets = account_summaries.value.map((summary) => {
        const data = labels.map((label) => {
          const monthlyBalance = summary.monthly_balances.monthly_balances.find(
            (mb) => mb.year_month === label
          );
          return monthlyBalance
            ? parseFloat(monthlyBalance.cumulative_balance)
            : 0;
        });

        return {
          label: `${summary.account.institution} - ${summary.account.name}`,
          backgroundColor: getRandomColor(), // Function to get a random color
          data,
        };
      });

      return {
        labels,
        datasets,
      };
    });

    // Function to generate random colors for the datasets
    function getRandomColor() {
      const letters = "0123456789ABCDEF";
      let color = "#";
      for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
      }
      return color;
    }

    onMounted(() => {
      fetchAccountSummaries();
    });

    return {
      account_summaries,
      hideClosed,
      hideValues,
      sortBy,
      formatBalance,
      formatLastTransactionDate,
      totalBalance,
      sortKey,
      sortOrder,
      filteredSummaries,
      chartData,
    };
  },
});
</script>

<style scoped>
.accounts-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 20px;
  height: 100vh;
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

h1 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.account-table {
  border-collapse: collapse;
  width: 80%;
  margin-top: 20px;
}

.account-table th,
.account-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
  cursor: pointer;
}

.account-table th {
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

.hidden-values {
  color: #ccc; /* Color for hidden values */
  font-weight: bold;
}

.total-balance {
  margin-top: 20px;
  font-size: 1.2em;
  font-weight: bold;
  text-align: center;
}

.chart {
  margin-top: 20px;
  width: 80%;
  height: auto;
  /* flex-grow: 1; */
}
</style>
