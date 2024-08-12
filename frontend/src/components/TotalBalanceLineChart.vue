<template>
  <Line
    class="chart-container"
    v-if="chartData.labels?.length"
    :data="chartData"
    :options="chartOptions"
  />
</template>

<script setup lang="ts">
  import { AccountSummary, Timescale } from "@/types.d";
  import {
    CategoryScale,
    Chart,
    ChartData,
    ChartOptions,
    Filler,
    LinearScale,
    LineController,
    LineElement,
    PointElement,
    Title,
  } from "chart.js";
  import { computed, ref } from "vue";
  import { Line } from "vue-chartjs";

  // Register necessary chart components
  Chart.register(
    LineController,
    LineElement,
    PointElement,
    LinearScale,
    Title,
    CategoryScale,
    Filler
  );

  interface Props {
    accountSummaries: AccountSummary[];
    timescale: Timescale;
  }

  const props = defineProps<Props>();

  //   const accountSummariesStore = useAccountSummariesStore();
  //   const accountSummaries = computed<AccountSummary[]>(
  //     () => accountSummariesStore.accountSummaries
  //   );

  const chartData = computed<ChartData<"line">>(() => {
    const summaries = props.accountSummaries;
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

    // Calculate the total balance for each month
    const totalBalances = labels.map((label) => {
      return summaries.reduce((sum, summary) => {
        const monthlyBalance = summary.monthlyBalances.monthlyBalances.find(
          (mb) => mb.yearMonth === label
        );
        return (
          sum + (monthlyBalance ? parseFloat(monthlyBalance.endBalance) : 0)
        );
      }, 0);
    });

    // Filter data based on the selected timescale
    if (props.timescale !== Timescale.All) {
      const startIndex = Math.max(labels.length - props.timescale, 0);
      labels.splice(0, startIndex);
      totalBalances.splice(0, startIndex);
    }

    // Create a single dataset for the line graph
    const datasets = [
      {
        label: "Total Balance",
        backgroundColor: "rgba(75, 192, 192, 0.2)", // Line color with transparency
        borderColor: "rgba(72, 168, 166, 1)", // Line color
        data: totalBalances,
        fill: false, // Don't fill the area under the line
      },
    ];

    return {
      labels,
      datasets,
    };
  });

  const chartOptions = ref<ChartOptions<"line">>({
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        display: false,
      },
      y: {
        display: true,
      },
    },
    elements: {
      line: {
        tension: 0.3,
        borderWidth: 3,
      },
      point: {
        radius: 0,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: "index", // Ensure the tooltip shows all values at the hovered index
        intersect: false, // Ensure the tooltip shows even if not directly intersecting a point
        callbacks: {
          label: (context) => {
            let label = context.dataset.label || "";
            if (label) {
              label += ": ";
            }
            if (context.parsed.y !== null) {
              const value = context.parsed.y as number;
              label += `${value < 0 ? "-" : ""}£${Math.abs(
                value
              ).toLocaleString()}`;
            }
            return label;
          },
        },
      },
    },
    // animation: {
    //   duration: 0, // Disable animations
    // },
  });
</script>

<style scoped>
  .chart-container {
    position: relative;
    width: 100%;
    height: 270px;
  }

  .chart-container canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100% !important;
    height: 100% !important;
  }
</style>
