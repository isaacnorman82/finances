<template>
  <div class="chart-container">
    <Bar v-if="data" :data="data" :options="chartOptions" />
    <div v-else>Loading...</div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref } from "vue";
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  ChartOptions,
} from "chart.js";

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
              return `${val < 0 ? "-" : ""}£${Math.abs(val).toLocaleString()}`;
            },
            color: function (context) {
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
  width: 80%;
  height: auto; /* Ensure the container height adjusts automatically */
  flex-grow: 1;
}
</style>
