<template>
  <Bar v-if="data" :data="data" :options="chartOptions" />
  <div v-else>Loading...</div>
</template>

<script lang="ts">
  import {
    BarElement,
    CategoryScale,
    ChartData,
    Chart as ChartJS,
    ChartOptions,
    Legend,
    LinearScale,
    Title,
    Tooltip,
  } from "chart.js";
  import { defineComponent, PropType } from "vue";
  import { Bar } from "vue-chartjs";

  // Register required components
  ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
  );

  export default defineComponent({
    name: "StackedBarChart",
    components: {
      Bar,
    },
    props: {
      data: {
        type: Object as PropType<ChartData<"bar">>,
        required: true,
      },
    },
    setup() {
      const chartOptions: ChartOptions<"bar"> = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: "bottom",
          },
          title: {
            display: true,
            text: "Stacked Bar Chart",
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
          },
          y: {
            stacked: true,
            ticks: {
              callback: (value) => {
                const val = value as number;
                return `${val < 0 ? "-" : ""}£${Math.abs(
                  val
                ).toLocaleString()}`;
              },
              color(context) {
                const value = context.tick.value;
                return value < 0 ? "red" : "black";
              },
            },
          },
        },
      };

      return {
        chartOptions,
      };
    },
  });
</script>

<style scoped>
  .chart-container {
    /* width: 100%;
    height: auto; Ensure the container height adjusts automatically */
    position: relative;
    /* height: 40vh; */
    /* width: 80vw; */
    flex-grow: 1 1 auto;
  }
</style>
