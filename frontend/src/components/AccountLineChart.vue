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

      const graphDate = props.selectedDate.copy();
      graphDate.toEnd();

      const months = graphDate.getMonthsForTimescale(props.timescale);

      // Filter out entries with interpolated == "inter"
      // const filteredBalances =
      //   props.accountSummary.monthlyBalances.monthlyBalances.filter(
      //     (mb: MonthlyBalance) => mb.interpolated !== "inter"
      //   );
      const filteredBalances =
        props.accountSummary.monthlyBalances.monthlyBalances;

      // Extract balances
      const balancesMap = new Map(
        filteredBalances.map((mb: MonthlyBalance) => [
          mb.yearMonth,
          parseBalance(mb.endBalance),
        ])
      );

      // Extract deposits to date
      const depositsMap = new Map(
        filteredBalances.map((mb: MonthlyBalance) => [
          mb.yearMonth,
          parseBalance(mb.depositsToDate),
        ])
      );

      // Create the data arrays with null for missing months
      const balanceData = months.map((month) => balancesMap.get(month) ?? null);
      const depositsData = months.map(
        (month) => depositsMap.get(month) ?? null
      );

      return {
        labels: months,
        datasets: [
          {
            label: "Value",
            data: balanceData,
            fill: false,
            spanGaps: true,
            borderColor: "#48A8A6",
            pointRadius: balanceData.length > 60 ? 0 : 3, // Hide points if more than 60 data points
            pointHitRadius: 5,
          },
          ...(JSON.stringify(balanceData) !== JSON.stringify(depositsData)
            ? [
                {
                  label: "Deposits",
                  data: depositsData,
                  fill: false,
                  spanGaps: true,
                  borderColor: "#1866C0",
                  pointRadius: balanceData.length > 60 ? 0 : 3, // Hide points if more than 60 data points
                  pointHitRadius: 5,
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
