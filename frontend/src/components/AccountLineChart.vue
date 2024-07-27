<template>
  <Line
    v-if="chartData.datasets[0].data.length"
    :data="chartData"
    :options="chartOptions"
  />
</template>

<script setup lang="ts">
  import type { AccountSummary, MonthlyBalance } from "@/types.d";
  import { Timescale } from "@/types.d";
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
    selectedDate: Date;
    timescale: Timescale;
  }

  const props = defineProps<Props>();
  const emit = defineEmits(["dateSelected"]);

  const chartData = computed(
    (): { labels: string[]; datasets: ChartDataset<"line">[] } => {
      if (!props.accountSummary) {
        throw new Error("Account summary is required");
      }

      const selectedDate = new Date(props.selectedDate);
      selectedDate.setDate(1); // Ensure it's the first day of the month

      // Extract cumulative balances
      const balancesMap = new Map(
        props.accountSummary.monthlyBalances.monthlyBalances.map(
          (mb: MonthlyBalance) => [
            mb.yearMonth,
            parseFloat(mb.cumulativeBalance),
          ]
        )
      );

      // Determine the range of months to display based on timescale
      const monthsToShow = (numMonths: number) => {
        const months = [];
        for (let i = numMonths - 1; i >= 0; i--) {
          const date = new Date(selectedDate);
          date.setMonth(date.getMonth() - i);
          months.push(date.toISOString().slice(0, 7));
        }
        return months;
      };

      let months: string[];
      switch (props.timescale) {
        case Timescale.All:
          months = Array.from(balancesMap.keys());
          break;
        case Timescale.FiveYears:
          months = monthsToShow(5 * 12);
          break;
        case Timescale.OneYear:
          months = monthsToShow(12);
          break;
        case Timescale.SixMonths:
          months = monthsToShow(6);
          break;
        case Timescale.ThreeMonths:
          months = monthsToShow(3);
          break;
        // not supportin 1 month yet as we'd need to switch to transaction data instead of monthly balance data
        default:
          months = monthsToShow(12); // Default to 12 months if not specified
      }

      // Create the data array with null for missing months
      const data = months.map((month) => balancesMap.get(month) ?? null);

      return {
        labels: months,
        datasets: [
          {
            label: "Balance",
            data,
            fill: false,
            spanGaps: false,
            borderColor: (context) => {
              const index = context.dataIndex;
              const value = context.dataset.data[index];
              if (typeof value === "number") {
                return value >= 0
                  ? "rgba(66, 185, 131, 1)"
                  : "rgba(220, 20, 60, 1)";
              }
              return "#000"; // Default color if value is not a number
            },
            borderWidth: 3,
            segment: {
              borderColor: (ctx) => {
                const y0 = ctx.p0.parsed.y;
                const y1 = ctx.p1.parsed.y;
                if (typeof y0 === "number" && typeof y1 === "number") {
                  if (y0 >= 0 && y1 >= 0) {
                    return "rgba(66, 185, 131, 1)";
                  } else if (y0 < 0 && y1 < 0) {
                    return "rgba(220, 20, 60, 1)";
                  } else {
                    return y0 >= 0
                      ? "rgba(66, 185, 131, 1)"
                      : "rgba(220, 20, 60, 1)";
                  }
                }
                return "#000"; // Default color if values are not numbers
              },
            },
          },
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
        emit("dateSelected", new Date(`${date}-01T00:00:00`));
      }
    }
  };
</script>

<style scoped>
  /* Add any component-specific styles here */
</style>
