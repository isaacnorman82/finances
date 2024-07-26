<template>
  <v-container style="height: 100vh; width: 100%">
    <v-row>
      <v-col>
        <v-breadcrumbs bg-color="primary" :items="[]">
          <template v-slot:prepend>Accounts</template>
        </v-breadcrumbs>
        <v-data-table
          :headers="tableHeaders"
          hide-default-footer
          :items="tableData"
        >
          <template v-slot:item="{ item }">
            <tr style="cursor: pointer" @click="navigateToAccount(item)">
              <td>{{ item.institution }}</td>
              <td>{{ item.name }}</td>
              <td v-html="formatBalance(item.balance)" />

              <td>{{ item.last_transaction_date }}</td>
            </tr>
          </template>
          <template v-slot:body.append>
            <tr>
              <td colspan="2" style="text-align: right; font-weight: bold">
                Total Amount:
              </td>
              <td>
                {{ formatBalance(totalBalance) }}
              </td>
            </tr>
          </template>
        </v-data-table>
        <StackedBarChart :data="chartData" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import StackedBarChart from "@/components/StackedBarChart.vue";
  import { useAccountSummaries } from "@/stores/accountSummaries";
  import type { AccountSummary } from "@/types.d.ts";
  import { formatBalance, formatDate } from "@/utils";
  import { ChartData } from "chart.js";
  import { computed, ref } from "vue";

  const accountSummariesStore = useAccountSummaries();
  const accountSummaries = computed<AccountSummary[]>(
    () => accountSummariesStore.accountSummaries
  );

  const hideClosed = ref<boolean>(true);
  const router = useRouter();

  const filteredSummaries = computed(() => {
    return accountSummaries.value.filter((summary) => {
      if (hideClosed.value && !summary.account.is_active) {
        return false;
      }
      return true;
    });
  });

  const tableData = computed(() => {
    return filteredSummaries.value.map((summary) => ({
      id: summary.account.id,
      institution: summary.account.institution,
      name: summary.account.name,
      balance: summary.balance,
      last_transaction_date: formatLastTransactionDate(
        summary.last_transaction_date
      ),
    }));
  });

  const formatLastTransactionDate = (dateTime: string | null) => {
    if (!dateTime) return "N/A";

    // Parse the date
    const date = new Date(dateTime);
    const now = new Date();
    const diffTime = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    return `${formatDate(dateTime)} (${diffDays} days ago)`;
  };

  function navigateToAccount(item: any) {
    router.push({ path: `/accountDetails/${item.id}` });
  }

  const totalBalance = computed(() => {
    return accountSummaries.value.reduce((total, accountSummary) => {
      return total + parseFloat(accountSummary.balance);
    }, 0);
  });

  function formatHeaderText(key: string): string {
    return key
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  }

  const tableHeaders = computed(() => {
    if (tableData.value.length === 0) return [];

    // Generate headers based on the keys of the first item in tableData
    const keys = Object.keys(tableData.value[0])
      .filter((key) => key !== "id")
      .map((key) => ({
        title: formatHeaderText(key),
        key,
      }));
    return keys;
  });

  const chartData = computed<ChartData<"bar">>(() => {
    if (accountSummaries.value.length === 0) {
      return {
        labels: [],
        datasets: [],
      };
    }

    // Extract all unique labels from all accounts
    const uniqueDates = new Set<string>();
    accountSummaries.value.forEach((summary) => {
      summary.monthly_balances.monthly_balances.forEach((mb) => {
        uniqueDates.add(mb.year_month);
      });
    });

    const labels = Array.from(uniqueDates).sort();

    // Create datasets for each account, aligning data with the unique dates
    const datasets = accountSummaries.value.map((summary) => {
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
</script>

<style scoped></style>
