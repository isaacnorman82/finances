<template>
  <!-- todo move loader below breadcrumbs, ideally loader and breadcrumbs could be in app and the pages could give a loading value-->
  <v-container
    v-if="!accountSummary || !selectedMonthlyBalance"
    class="d-flex align-center justify-center"
    style="height: 400px"
  >
    <v-progress-circular indeterminate></v-progress-circular>
  </v-container>
  <v-container v-if="accountSummary && selectedMonthlyBalance">
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
      <v-col cols="4">
        <v-card
          class="fill-height d-flex flex-column"
          color="primary"
          variant="tonal"
        >
          <v-card-text>
            <div>
              <div class="text-overline mb-1">Details</div>
              <div class="text-h6">
                {{ accountSummary.account.institution }}
                {{ accountSummary.account.name }}
              </div>
              <div class="d-flex mb-4">
                <div class="subheading-text">
                  {{ accountSummary.account.acNumber }}
                </div>
                <v-spacer />
                <div class="subheading-text">
                  {{ startMonth ? startMonth.format("MMMM yyyy") : "" }}
                </div>
              </div>

              <div class="text-caption">
                {{ accountSummary.account.description }}
              </div>
            </div>
          </v-card-text>
          <v-spacer />
          <v-card-actions>
            <v-btn prepend-icon="mdi-cog" text="Settings" />
            <v-spacer />
            <v-btn
              :disabled="!accountSummary.account.externalLink"
              append-icon="mdi-open-in-new"
              text="Login"
              :href="accountSummary.account.externalLink || ''"
              target="_blank"
            />
          </v-card-actions>
        </v-card>
      </v-col>
      <v-col cols="4">
        <v-card
          class="fill-height d-flex flex-column"
          color="secondary"
          variant="tonal"
        >
          <v-card-text>
            <div>
              <div class="text-overline mb-1">Balance</div>
              <div
                class="text-h6"
                v-html="formatBalance(accountSummary.balance)"
              />
              <div class="mb-4 subheading-text">
                As of
                {{
                  formatLastTransactionDate(accountSummary.lastTransactionDate)
                }}
              </div>
              <div
                v-for="item in balanceDeltas"
                :key="item.title"
                class="headed-data-row"
              >
                <div class="data-row-header">{{ item.title }}</div>
                <div>
                  {{ calculateBalanceChange(item.timescale, accountSummary) }}
                </div>
              </div>
            </div>
          </v-card-text>
          <v-spacer />
          <v-card-actions>
            <v-btn
              prepend-icon="mdi-file-upload-outline"
              text="Upload Transactions"
            />
          </v-card-actions>
        </v-card>
      </v-col>
      <v-col cols="4">
        <v-card
          class="fill-height d-flex flex-column"
          color="blue-grey-lighten-2"
          variant="tonal"
        >
          <v-card-item class="flex-grow-1">
            <account-line-chart
              :account-summary="accountSummary"
              class="flex-grow-1"
              :selected-date="selectedDate"
              :timescale="graphTimescale"
              @date-selected="selectedDate = $event"
            />
          </v-card-item>
          <v-card-actions>
            <v-spacer />
            <v-btn-toggle
              v-model="graphTimescale"
              color="primary"
              density="compact"
              mandatory
              variant="plain"
            >
              <v-btn text="6M" :value="Timescale.SixMonths" />
              <v-btn text="1Y" :value="Timescale.OneYear" />
              <v-btn text="2Y" :value="Timescale.TwoYears" />
              <v-btn text="5Y" :value="Timescale.FiveYears" />
              <v-btn text="ALL" :value="Timescale.All" />
            </v-btn-toggle>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card flat title="Transactions">
          <v-toolbar color="white" density="compact">
            <v-card-title class="title-width">
              {{ selectedDate.format("MMMM yyyy") }}
            </v-card-title>
            <v-text-field
              v-model="search"
              density="compact"
              hide-details
              label="Search"
              prepend-inner-icon="mdi-magnify"
              single-line
              variant="outlined"
            />
            <v-btn
              :disabled="selectedDate.atStart"
              icon="mdi-page-first"
              @click="selectedDate.toStart()"
            />
            <v-btn
              :disabled="selectedDate.atStart"
              icon="mdi-chevron-left"
              @click="selectedDate.subtract(1)"
            />
            <v-btn
              :disabled="selectedDate.atEnd"
              icon="mdi-chevron-right"
              @click="selectedDate.add(1)"
            />
            <v-btn
              :disabled="selectedDate.atEnd"
              icon="mdi-page-last"
              @click="selectedDate.toEnd()"
            />
          </v-toolbar>
          <v-data-table
            density="compact"
            :headers="tableHeaders"
            hide-default-footer
            :items="transactions"
            :items-per-page="transactions.length"
            :search="search"
          >
            <template v-slot:item="{ item }">
              <tr>
                <td>{{ formatDate(item.dateTime) }}</td>
                <td>{{ item.transactionType }}</td>
                <td>{{ item.description }}</td>
                <td v-html="formatBalance(item.amount)" />
                <td>{{ item.notes }}</td>
              </tr>
            </template>
            <template v-slot:body.append>
              <tr>
                <td colspan="3" style="text-align: right; font-weight: bold">
                  <div>Starting Balance:</div>
                  <div>Monthly Balance:</div>
                  <div>Final Balance:</div>
                </td>
                <td>
                  <div
                    v-html="formatBalance(selectedMonthlyBalance.startBalance)"
                  />
                  <div
                    v-html="
                      formatBalance(selectedMonthlyBalance.monthlyBalance)
                    "
                  />
                  <div
                    v-html="formatBalance(selectedMonthlyBalance.endBalance)"
                  />
                </td>
                <td />
              </tr>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { useAccountSummariesStore } from "@/stores/accountSummaries";
  import { useTransactionsStore } from "@/stores/transactions";
  import type { AccountSummary, Transaction } from "@/types.d";
  import { MonthYear, Timescale } from "@/types.d";
  import {
    calculateBalanceChange,
    formatBalance,
    formatDate,
    formatLastTransactionDate,
    getBalanceForDate,
  } from "@/utils";
  import { useRoute } from "vue-router";

  const graphTimescale = ref<Timescale>(Timescale.OneYear);
  const search = ref("");

  const route = useRoute("/accountDetails/[id]");
  const accountId: number = parseInt(route.params.id);

  const accountSummariesStore = useAccountSummariesStore();
  const accountSummary = computed<AccountSummary | undefined>(() => {
    return accountSummariesStore.accountSummaries.find(
      (summary) => summary.account.id === accountId
    );
  });

  const transactionsStore = useTransactionsStore();
  const transactions = ref<Transaction[]>([]);

  const selectedDate = ref<MonthYear>(new MonthYear());

  watch(
    accountSummary,
    () => {
      if (route.query.date) {
        selectedDate.value.goToDate(`${route.query.date}`);
      }
      if (accountSummary.value) {
        //todo should maybe have an error if not
        selectedDate.value.setBounds(
          accountSummary.value.monthlyBalances.startYearMonth,
          accountSummary.value.monthlyBalances.endYearMonth
        );
      }
    },
    { immediate: true }
  );

  const selectedYearMonth = computed(() => ({
    year: selectedDate.value.year,
    month: selectedDate.value.month,
  }));

  watch(
    selectedYearMonth,
    async () => {
      // Ensure bounds still set
      if (accountSummary.value) {
        selectedDate.value.setBounds(
          accountSummary.value.monthlyBalances.startYearMonth,
          accountSummary.value.monthlyBalances.endYearMonth
        );
      }
      transactions.value = await transactionsStore.fetchTransactions(
        accountId,
        selectedDate.value
      );
    },
    { immediate: true }
  );

  // watch(
  //   selectedDate,
  //   async () => {
  //     // ensure bounds still set
  //     if (accountSummary.value) {
  //       //todo should maybe have an error if not
  //       selectedDate.value.setBounds(
  //         accountSummary.value.monthlyBalances.startYearMonth,
  //         accountSummary.value.monthlyBalances.endYearMonth
  //       );
  //     }
  //     transactions.value = await transactionsStore.fetchTransactions(
  //       accountId,
  //       selectedDate.value
  //     );
  //   },
  //   { immediate: true, deep: true }
  // );

  const startMonth = computed(() => {
    if (!accountSummary.value) return null;
    const startYearMonth = accountSummary.value.monthlyBalances.startYearMonth;
    // return new Date(`${startYearMonth}-01T00:00:00Z`);
    return new MonthYear(startYearMonth);
  });

  const balanceDeltas = ref([
    { title: "1 Month:", timescale: Timescale.OneMonth },
    { title: "3 Months:", timescale: Timescale.ThreeMonths },
    { title: "1 Year:", timescale: Timescale.OneYear },
  ]);

  const breadcrumbs = computed(() => {
    return [
      {
        title: "Accounts",
        disabled: false,
        to: "/",
      },
      {
        title:
          accountSummary.value?.account.institution +
          " - " +
          accountSummary.value?.account.name,
        disabled: false,
      },
    ];
  });

  const tableHeaders = computed(() => {
    return [
      {
        title: "Date",
        key: "dateTime",
      },
      {
        title: "Type",
        key: "transactionType",
      },
      {
        title: "Description",
        key: "description",
      },
      {
        title: "Amount",
        key: "amount",
      },
      {
        title: "Notes",
        key: "notes",
      },
    ];
  });

  const selectedMonthlyBalance = computed(() => {
    if (accountSummary.value) {
      // console.log(
      //   "trying to get balance for date",
      //   selectedDate.value.toString()
      // );
      return getBalanceForDate(accountSummary.value, selectedDate.value);
    }
    return null;
  });
</script>

<style scoped>
  .title-width {
    width: 185px; /* Adjust the width as needed */
  }

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
