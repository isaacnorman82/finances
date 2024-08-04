<template>
  <v-container>
    <v-row>
      <v-col>
        <v-breadcrumbs :items="breadcrumbs">
          <template v-slot:item="{ item }">
            <v-breadcrumbs-item :disabled="item.disabled" :to="item.to">
              {{ item.title }}
            </v-breadcrumbs-item>
          </template>
        </v-breadcrumbs>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card flat title="Taxable Income">
          <StackedBarChart :data="taxableIncomeSeries as ChartData<'bar'>" />
        </v-card>
      </v-col>
      <v-col>
        <v-card flat title="Salary">
          <StackedBarChart :data="salarySeries as ChartData<'bar'>" />
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { dataSeriesToChartData, formatMonthYear } from "@/utils";
  import { ChartData } from "chart.js";

  const breadcrumbs = computed(() => {
    return [{ title: "Salary and Tax", disabled: false }];
  });

  const taxableIncomeSeries = computed<ChartData>(() => {
    return dataSeriesToChartData({
      "Net Pay": "#64B5F6",
      "Tax Paid": "#E57373",
    });
  });

  const salarySeries = computed<ChartData>(() => {
    return dataSeriesToChartData(
      {
        Salary: "#64B5F6",
        "Car Allowance": "#90CAF9",
        "Bonus Target": "#BBDEFB",
      },
      formatMonthYear
    );
  });
</script>

<style scoped></style>
