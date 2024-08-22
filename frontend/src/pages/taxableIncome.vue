<template>
  <v-container>
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
          <inflation-toggle v-model="inflationToggleState" />
        </v-toolbar>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card flat title="Taxable Income" color="primary" variant="tonal">
          <v-card-item>
            <StackedBarChart :data="taxableIncomeSeries as ChartData<'bar'>" />
          </v-card-item>
        </v-card>
      </v-col>
      <v-col>
        <v-card flat title="Salary" color="secondary" variant="tonal">
          <v-card-item>
            <StackedBarChart :data="salarySeries as ChartData<'bar'>" />
          </v-card-item>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col class="mt-4">
        <v-timeline direction="horizontal" density="compact">
          <v-timeline-item
            v-for="(company, index) in companies"
            :key="company.name"
            :dot-color="getDotColor(index)"
            side="top"
          >
            <div>{{ company.date }} - {{ company.name }}</div>
          </v-timeline-item>
        </v-timeline>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { useDataSeriesStore } from "@/stores/dataSeries";
  import { DataSeries } from "@/types";
  import {
    adjustChartDataForInflation,
    dataSeriesToChartData,
    formatMonthYear,
  } from "@/utils";
  import { ChartData } from "chart.js";

  const inflationToggleState = ref({ isOn: false, year: 2023 });

  const breadcrumbs = computed(() => {
    return [{ title: "Taxable Income", disabled: false }];
  });

  const taxableIncomeSeries = computed<ChartData>(() => {
    let chartData = dataSeriesToChartData({
      "Net Pay": "#64B5F6",
      "Tax Paid": "#E57373",
    });

    return inflationToggleState.value.isOn
      ? adjustChartDataForInflation(
          chartData,
          inflationToggleState.value.year,
          "YYYY"
        )
      : chartData;
  });

  const salarySeries = computed<ChartData>(() => {
    let chartData = dataSeriesToChartData(
      {
        Salary: "#64B5F6",
        "Car Allowance": "#90CAF9",
        "Bonus Target": "#BBDEFB",
      },
      formatMonthYear
    );

    return inflationToggleState.value.isOn
      ? adjustChartDataForInflation(
          chartData,
          inflationToggleState.value.year,
          "MM/YYYY"
        )
      : chartData;
  });

  const companies = computed(() => {
    const dataSeriesStore = useDataSeriesStore();
    const companiesDS = dataSeriesStore.getDataSeries("Company");
    return companiesDS.map((dataseries: DataSeries) => {
      return {
        name: dataseries.value,
        date: new Date(dataseries.dateTime).getFullYear(),
      };
    });
  });

  const getDotColor = (index: number) => {
    return index % 2 === 0 ? "primary" : "secondary";
  };
</script>

<style scoped></style>
