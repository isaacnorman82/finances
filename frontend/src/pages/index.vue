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
      <v-col
        ><v-toolbar color="white" density="compact">
          <v-spacer />
          <timescale-toggle
            v-model="graphTimescale"
            density="default"
            variant="text"
          />
          <account-type-toggle v-model="accountTypes" class="ml-4" />
        </v-toolbar>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card flat title="Balance" color="primary" variant="tonal">
          <v-card-item>
            <TotalBalanceLineChart
              :accountSummaries="filteredAccountSummaries"
              :timescale="graphTimescale"
            />
          </v-card-item>
        </v-card>
      </v-col>
      <v-col>
        <v-card flat title="Wealth" color="secondary" variant="tonal">
          <v-card-item>
            <WealthPieChart
              :group-by-account-type="true"
              :accountSummaries="filteredAccountSummaries"
            />
          </v-card-item>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card
          flat
          title="History"
          color="blue-grey-lighten-2"
          variant="tonal"
        >
          <v-card-item>
            <StackedBarChart
              :data="chartData"
              :timescale="graphTimescale"
              @chartClick="navigateToAccountDetails"
          /></v-card-item>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import StackedBarChart from "@/components/StackedBarChart.vue";
  import TotalBalanceLineChart from "@/components/TotalBalanceLineChart.vue";
  import { useAccountSummariesStore } from "@/stores/accountSummaries";
  import { AccountSummary, Timescale } from "@/types.d";
  import {
    filterAccountSummaries,
    findAccountSummaryFromLabel,
    getSeededColor,
  } from "@/utils";
  import { ChartData } from "chart.js";
  import { computed } from "vue";

  const accountTypes = ref<string[]>([
    "Current/Credit",
    "Savings",
    "Asset",
    "Loan",
    "Pension",
    "isClosed",
  ]);

  const accountSummariesStore = useAccountSummariesStore();
  const accountSummaries = computed<AccountSummary[]>(
    () => accountSummariesStore.accountSummaries
  );

  const filteredAccountSummaries = computed<AccountSummary[]>(() => {
    return filterAccountSummaries(accountSummaries.value, accountTypes.value);
  });

  const graphTimescale = ref<Timescale>(Timescale.All);

  const router = useRouter();

  const breadcrumbs = computed(() => {
    return [
      {
        title: "Summary",
        disabled: false,
      },
    ];
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

  const chartData = computed<ChartData<"bar">>(() => {
    let summaries = filteredAccountSummaries.value;

    if (summaries.length === 0) {
      return {
        labels: [],
        datasets: [],
      };
    }

    // Extract all unique labels from all accounts
    const uniqueDates = new Set<string>();
    summaries.forEach((summary) => {
      summary.monthlyBalances.monthlyBalances.forEach((mb) => {
        uniqueDates.add(mb.yearMonth);
      });
    });

    const labels = Array.from(uniqueDates).sort();

    // Filter data based on the selected timescale
    if (graphTimescale.value !== Timescale.All) {
      const monthsToShow = graphTimescale.value;
      const startIndex = Math.max(labels.length - monthsToShow, 0);
      labels.splice(0, startIndex);
    }

    // Create datasets for each account, aligning data with the unique dates
    const datasets = summaries.map((summary) => {
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
