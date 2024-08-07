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

  interface Props {
    groupByAccountType: boolean;
  }

  const props = defineProps<Props>();

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

    let labels: string[] = [];
    let data: number[] = [];
    let backgroundColors: string[] = [];

    if (props.groupByAccountType) {
      const groupedByAccountType: { [key: string]: number } = {};

      accountBalances.forEach((summary) => {
        const accountType = summary.account.accountType;
        if (!groupedByAccountType[accountType]) {
          groupedByAccountType[accountType] = 0;
        }
        groupedByAccountType[accountType] += summary.balance;
      });

      labels = Object.keys(groupedByAccountType);
      data = Object.values(groupedByAccountType);
      backgroundColors = labels.map((accountType) =>
        getSeededColor(accountType)
      );
    } else {
      // Labels are account names
      labels = accountBalances.map((summary) => summary.account.name);

      // Data for the pie chart
      data = accountBalances.map((val) => val.balance);

      // Colors for each slice
      backgroundColors = accountBalances.map((account) =>
        getSeededColor(account.account.id)
      );
    }

    const datasets = [
      {
        label: "Balance",
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
    plugins: {
      legend: {
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
