<template>
  <Line
    v-if="chartData.labels.length"
    :data="chartData"
    :options="chartOptions"
  />
</template>

<script setup lang="ts">
  import type { AccountSummary, MonthlyBalance } from "@/types.d";
  import { MonthYear, Timescale } from "@/types.d";
  import {
    ActiveElement,
    CategoryScale,
    Chart,
    ChartDataset,
    ChartEvent,
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
    accountSummary: AccountSummary;
    selectedDate: MonthYear;
    timescale: Timescale;
  }

  const props = defineProps<Props>();
  const emit = defineEmits(["dateSelected"]);

  const parseBalance = (balance: string): number | null => {
    const parsed = parseFloat(balance);
    return isNaN(parsed) ? null : parsed;
  };

  const chartData = computed(
    (): { labels: string[]; datasets: ChartDataset<"line">[] } => {
      if (!props.accountSummary) {
        throw new Error("Account summary is required");
      }

      const months = props.selectedDate.getMonthsForTimescale(props.timescale);

      // Extract cumulative balances
      const balancesMap = new Map(
        props.accountSummary.monthlyBalances.monthlyBalances.map(
          (mb: MonthlyBalance) => [mb.yearMonth, parseBalance(mb.endBalance)]
        )
      );

      // Extract value adjusted balances
      const adjBalancesMap = new Map(
        props.accountSummary.monthlyBalances.monthlyBalances.map(
          (mb: MonthlyBalance) => [
            mb.yearMonth,
            parseBalance(mb.startValAdjBalance),
          ]
        )
      );

      // Create the data arrays with null for missing months
      const balanceData = months.map((month) => balancesMap.get(month) ?? null);
      const adjBalanceData = months.map((month) => {
        const balance = balancesMap.get(month) ?? null;
        const adjBalance = adjBalancesMap.get(month) ?? 0;
        return balance !== null ? balance - adjBalance : null;
      });

      return {
        labels: months,
        datasets: [
          {
            label: "Value",
            data: balanceData,
            fill: false,
            spanGaps: false,
            borderColor: "rgba(72, 168, 166, 1)",
          },
          ...(JSON.stringify(balanceData) !== JSON.stringify(adjBalanceData)
            ? [
                {
                  label: "Payments",
                  data: adjBalanceData,
                  fill: false,
                  spanGaps: false,
                  borderColor: "rgba(24, 102, 192, 1)",
                },
              ]
            : []),
        ],
      };
    }
  );

  const chartOptions = ref<ChartOptions<"line">>({
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
    elements: {
      line: {
        tension: 0.3,
        borderWidth: 3,
      },
      point: {
        radius: 2,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
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
    animation: {
      duration: 0, // Disable animations
    },
    onClick: (event: ChartEvent, elements: ActiveElement[], chart: Chart) => {
      handleChartClick(event, elements, chart);
    },
  });

  const handleChartClick = (
    event: ChartEvent,
    elements: ActiveElement[],
    chart: Chart
  ) => {
    if (elements.length && chart.data.labels) {
      const elementIndex = elements[0].index;
      const date = chart.data.labels[elementIndex];
      if (date) {
        emit("dateSelected", new MonthYear(`${date}`));
      }
    }
  };
</script>

<style scoped>
  /* Add any component-specific styles here */
</style>
