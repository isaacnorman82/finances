<template>
  <v-container fluid>
    <v-row>
      <v-col>
        <v-breadcrumbs :items="breadcrumbs" class="text-h5">
          <template v-slot:item="{ item }">
            <v-breadcrumbs-item :disabled="item.disabled" :to="item.to">
              {{ item.title }}
            </v-breadcrumbs-item>
          </template>
        </v-breadcrumbs>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
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

              <td>{{ item.lastTransactionDate }}</td>
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
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <StackedBarChart
          :data="chartData"
          @chartClick="navigateToAccountDetails"
        />
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card flat title="Balance" color="primary" variant="tonal">
          <v-card-item>
            <TotalBalanceLineChart />
          </v-card-item>
        </v-card>
      </v-col>
      <v-col>
        <v-card flat title="Wealth" color="secondary" variant="tonal">
          <v-card-item>
            <WealthPieChart :group-by-account-type="true" />
          </v-card-item>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import StackedBarChart from "@/components/StackedBarChart.vue";
  import TotalBalanceLineChart from "@/components/TotalBalanceLineChart.vue";
  import { useAccountSummariesStore } from "@/stores/accountSummaries";
  import type { AccountSummary } from "@/types.d.ts";
  import {
    findAccountSummaryFromLabel,
    formatBalance,
    formatHeaderText,
    formatLastTransactionDate,
    getSeededColor,
  } from "@/utils";
  import { ChartData } from "chart.js";
  import { computed, ref } from "vue";

  const accountSummariesStore = useAccountSummariesStore();
  const accountSummaries = computed<AccountSummary[]>(
    () => accountSummariesStore.accountSummaries
  );

  const hideClosed = ref<boolean>(true);
  const router = useRouter();

  const breadcrumbs = computed(() => {
    return [
      {
        title: "Summary",
        disabled: false,
      },
    ];
  });

  const filteredSummaries = computed(() => {
    return accountSummaries.value.filter((summary) => {
      if (hideClosed.value && !summary.account.isActive) {
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
      lastTransactionDate: formatLastTransactionDate(
        summary.lastTransactionDate
      ),
    }));
  });

  const navigateToAccountDetails = ({
    account,
    date,
  }: {
    account: string;
    date: string;
  }) => {
    const accountSummary = findAccountSummaryFromLabel(
      account,
      accountSummaries.value
    );
    if (accountSummary) {
      const accountId = accountSummary.account.id;
      router.push({ path: `/accountDetails/${accountId}`, query: { date } });
    }
  };

  function navigateToAccount(item: any) {
    router.push({ path: `/accountDetails/${item.id}` });
  }

  const totalBalance = computed(() => {
    return accountSummaries.value.reduce((total, accountSummary) => {
      return total + parseFloat(accountSummary.balance);
    }, 0);
  });

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
      summary.monthlyBalances.monthlyBalances.forEach((mb) => {
        uniqueDates.add(mb.yearMonth);
      });
    });

    const labels = Array.from(uniqueDates).sort();

    // Create datasets for each account, aligning data with the unique dates
    const datasets = accountSummaries.value.map((summary) => {
      const data = labels.map((label) => {
        const monthlyBalance = summary.monthlyBalances.monthlyBalances.find(
          (mb) => mb.yearMonth === label
        );
        return monthlyBalance ? parseFloat(monthlyBalance.endBalance) : 0;
      });

      return {
        label: `${summary.account.institution} - ${summary.account.name}`,
        backgroundColor: getSeededColor(summary.account.id), // Function to get a random color
        data,
      };
    });

    return {
      labels,
      datasets,
    };
  });
</script>

<style scoped></style>
