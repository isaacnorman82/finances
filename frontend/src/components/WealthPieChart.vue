<template>
  <Pie
    v-if="chartData.labels?.length"
    :data="chartData"
    :options="chartOptions"
  />
</template>

<script setup lang="ts">
  import { useAccountSummariesStore } from "@/stores/accountSummaries";
  import { AccountSummary } from "@/types.d";
  import { getSeededColor } from "@/utils";
  import {
    ArcElement,
    Chart,
    ChartData,
    ChartOptions,
    Legend,
    Title,
    Tooltip,
  } from "chart.js";
  import { computed, ref } from "vue";
  import { Pie } from "vue-chartjs";

  // Register necessary chart components
  Chart.register(ArcElement, Tooltip, Legend, Title);

  //   interface Props {}

  //   const props = defineProps<Props>();

  const accountSummariesStore = useAccountSummariesStore();
  const accountSummaries = computed<AccountSummary[]>(
    () => accountSummariesStore.accountSummaries
  );

  const chartData = computed<ChartData<"pie">>(() => {
    if (accountSummaries.value.length === 0) {
      return {
        labels: [],
        datasets: [],
      };
    }

    // Extract the latest balance for each account with a non-zero balance
    const accountBalances = accountSummaries.value
      .map((summary) => {
        return {
          account: summary.account,
          balance: parseFloat(summary.balance),
        };
      })
      .filter((summary) => summary.account.isActive == true);

    // Labels are account names
    const labels: string[] = accountBalances.map(
      (summary) => summary.account.name
    );

    // Data for the bar chart
    const data: number[] = accountBalances.map((val) => val.balance);

    // Colors for each bar
    const backgroundColors = accountBalances.map((account) =>
      getSeededColor(account.account.id)
    );

    const datasets = [
      {
        label: "Account Balances",
        backgroundColor: backgroundColors,
        data,
      },
    ];

    return {
      labels,
      datasets,
    };
  });

  const chartOptions = ref<ChartOptions<"pie">>({
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        display: false,
      },
      y: {
        display: false,
      },
    },
    plugins: {
      legend: {
        display: true,
        position: "right",
      },
      tooltip: {
        mode: "index",
        intersect: true,
        callbacks: {
          label: (context) => {
            let label = context.dataset.label || "";
            if (label) {
              label += ": ";
            }
            if (context.parsed !== null) {
              label += `${context.parsed < 0 ? "-" : ""}£${Math.abs(
                context.parsed
              ).toLocaleString()}`;
            }
            return label;
          },
        },
      },
    },
  });
</script>

<style scoped>
  /* Add any component-specific styles here */
</style>
