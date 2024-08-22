<template>
  <v-card
    class="fill-height d-flex flex-column"
    color="secondary"
    variant="tonal"
  >
    <v-card-text>
      <div>
        <div class="text-overline mb-1">Balance</div>
        <div class="text-h6" v-html="formatBalance(accountSummary.balance)" />
        <div class="mb-4 subheading-text">
          As of
          {{ formatLastTransactionDate(accountSummary.lastTransactionDate) }}
        </div>
        <div
          v-for="item in balanceDeltas"
          :key="item.title"
          class="headed-data-row"
        >
          <div class="data-row-header">{{ item.title }}</div>
          <div>
            {{ calculateBalanceChange(item.timescale, props.accountSummary) }}
          </div>
        </div>
      </div>
    </v-card-text>
    <v-spacer />
    <v-card-actions>
      <v-btn prepend-icon="mdi-file-upload-outline">
        Upload Transactions
        <upload-transactions-dialog :account-summary="accountSummary" />
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
  import { defineProps } from "vue";

  import { AccountSummary, Timescale } from "@/types.d";

  import {
    calculateBalanceChange,
    formatBalance,
    formatLastTransactionDate,
  } from "@/utils";

  const props = defineProps<{
    accountSummary: AccountSummary;
  }>();

  const balanceDeltas = ref([
    { title: "1 Month:", timescale: Timescale.OneMonth },
    { title: "3 Months:", timescale: Timescale.ThreeMonths },
    { title: "1 Year:", timescale: Timescale.OneYear },
  ]);
</script>

<style scoped>
  .headed-data-row {
    display: table-row;
  }
  .headed-data-row div {
    display: table-cell;
  }
  .data-row-header {
    padding-right: 8px;
  }
</style>
