<template>
  <div v-if="data" class="chart-container">
    <Bar :data="data" :options="chartOptions" />
  </div>
  <div v-else>Loading...</div>
</template>

<script setup lang="ts">
  import {
    ActiveElement,
    BarElement,
    CategoryScale,
    ChartData,
    ChartEvent,
    Chart as ChartJS,
    ChartOptions,
    Legend,
    LinearScale,
    Title,
    Tooltip,
  } from "chart.js";
  import { defineProps } from "vue";
  import { Bar } from "vue-chartjs";

  ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
  );

  defineProps<{
    data: ChartData<"bar">;
  }>();

  const emit = defineEmits<{
    (e: "chartClick", payload: { account: string; date: string }): void;
  }>();

  const handleChartClick = (
    event: ChartEvent,
    elements: ActiveElement[],
    chart: ChartJS<"bar">
  ) => {
    if (elements.length && chart.data.labels) {
      const elementIndex = elements[0].index;
      const datasetIndex = elements[0].datasetIndex;
      const dataset = chart.data.datasets[datasetIndex];
      const account = dataset.label;
      const date = chart.data.labels[elementIndex];

      // Ensure the date is a string
      const dateString = typeof date === "string" ? date : String(date);

      console.log("chartClick", { account, date: dateString });
      if (account && dateString) {
        emit("chartClick", { account, date: dateString });
      }
    }
  };

  const chartOptions: ChartOptions<"bar"> = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: "bottom",
        display: false,
      },
      title: {
        text: "",
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
    scales: {
      x: {
        stacked: true,
        grid: {
          display: false, // Disable vertical grid lines
        },
      },
      y: {
        stacked: true,
        ticks: {
          callback: (value) => {
            const val = value as number;
            return `£${Math.abs(val).toLocaleString()}`;
          },
          color(context) {
            const value = context.tick.value;
            return value < 0 ? "red" : "black";
          },
        },
      },
    },
    onClick: (
      event: ChartEvent,
      elements: ActiveElement[],
      chart: ChartJS<"bar">
    ) => {
      handleChartClick(event, elements, chart);
    },
  };
</script>

<style scoped>
  .chart-container {
    position: relative;
    width: 100%;
    /* height: 400px; Set a fixed height or use other methods to control the height */
  }
</style>
