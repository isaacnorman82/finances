<template>
  <v-container v-if="accountSummary" style="width: 100%">
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
              <div class="mb-4 subheading-text">1234-5678-9012-3456</div>
              <div class="text-caption">Account notes go here.</div>
            </div>
          </v-card-text>
          <v-spacer />
          <v-card-actions>
            <v-btn prepend-icon="mdi-cog" text="Settings" />
            <v-spacer />
            <v-btn append-icon="mdi-open-in-new" text="Login" />
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
                  formatLastTransactionDate(
                    accountSummary.last_transaction_date
                  )
                }}
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
          color="primary"
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
              variant="plain"
            >
              <v-btn text="6M" :value="Timescale.SixMonths" />
              <v-btn text="1Y" :value="Timescale.OneYear" />
              <v-btn text="5Y" :value="Timescale.FiveYears" />
              <v-btn text="ALL" :value="Timescale.All" />
            </v-btn-toggle>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <!-- <v-card-text>
            Account ID: {{ accountId }} {{ accountSummary.account }}
            </v-card-text> -->

        <v-card flat title="Transactions">
          <v-toolbar color="white" density="compact">
            <v-card-title class="title-width">
              {{ displayDate }}
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
              :disabled="atStart"
              icon="mdi-page-first"
              @click="changeMonth(MonthChangeAction.First)"
            />
            <v-btn
              :disabled="atStart"
              icon="mdi-chevron-left"
              @click="changeMonth(MonthChangeAction.Prev)"
            />
            <v-btn
              :disabled="atEnd"
              icon="mdi-chevron-right"
              @click="changeMonth(MonthChangeAction.Next)"
            />
            <v-btn
              :disabled="atEnd"
              icon="mdi-page-last"
              @click="changeMonth(MonthChangeAction.Last)"
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
                <td>{{ formatDate(item.date_time) }}</td>
                <td>{{ item.transaction_type }}</td>
                <td>{{ item.description }}</td>
                <td v-html="formatBalance(item.amount)" />
                <td>{{ item.notes }}</td>
              </tr>
            </template>
            <template v-slot:body.append>
              <tr>
                <td colspan="3" style="text-align: right; font-weight: bold">
                  Monthly Balance:
                </td>
                <td v-html="formatBalance(totalBalance)" />
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
  import { useAccountSummaries } from "@/stores/accountSummaries";
  import { useTransactions } from "@/stores/transactions";
  import type { AccountSummary, Transaction } from "@/types.d";
  import { MonthChangeAction, Timescale } from "@/types.d";
  import {
    formatBalance,
    formatDate,
    formatLastTransactionDate,
  } from "@/utils";
  import { addMonths, startOfMonth } from "date-fns";
  import { useRoute } from "vue-router";
  import { useDate } from "vuetify";

  const graphTimescale = ref<Timescale>(Timescale.All);
  const search = ref("");

  const route = useRoute("/accountDetails/[id]");
  const accountId: number = parseInt(route.params.id);

  const accountSummariesStore = useAccountSummaries();
  const accountSummary = computed<AccountSummary | undefined>(() => {
    return accountSummariesStore.accountSummaries.find(
      (summary) => summary.account.id === accountId
    );
  });

  const date = useDate();

  const displayDate = computed<string>(() => {
    return date.format(selectedDate.value, "monthAndYear");
  });
  const selectedDate = ref(startOfMonth(new Date()));

  const changeMonth = (action: MonthChangeAction) => {
    if (!accountSummary.value) return;

    const { start_year_month, end_year_month } =
      accountSummary.value.monthly_balances;

    switch (action) {
      case MonthChangeAction.First:
        selectedDate.value = startOfMonth(
          new Date(`${start_year_month}-01T00:00:00`)
        );
        break;
      case MonthChangeAction.Last:
        selectedDate.value = startOfMonth(
          new Date(`${end_year_month}-01T00:00:00`)
        );
        break;
      case MonthChangeAction.Next:
        selectedDate.value = addMonths(selectedDate.value, 1);
        break;
      case MonthChangeAction.Prev:
        selectedDate.value = addMonths(selectedDate.value, -1);
        break;
    }
  };

  const transactionsStore = useTransactions();
  const transactions = ref<Transaction[]>([]);

  const atStart = computed(() => {
    if (!accountSummary.value) return true;
    const startYearMonth =
      accountSummary.value.monthly_balances.start_year_month;
    const startDate = new Date(`${startYearMonth}-01T00:00:00`);
    return selectedDate.value <= startOfMonth(startDate);
  });

  const atEnd = computed(() => {
    if (!accountSummary.value) return true;
    const endYearMonth = accountSummary.value.monthly_balances.end_year_month;
    const endDate = new Date(`${endYearMonth}-01T00:00:00`);
    return selectedDate.value >= startOfMonth(endDate);
  });

  watch(
    [selectedDate],
    async () => {
      console.log(
        "Fetching transactions for account",
        accountId,
        selectedDate.value
      );
      transactions.value = await transactionsStore.fetchTransactions(
        accountId,
        date.getMonth(selectedDate.value) + 1,
        date.getYear(selectedDate.value)
      );
      // console.log(transactions.value);
    },
    { immediate: true }
  );

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
        key: "date_time",
      },
      {
        title: "Type",
        key: "transaction_type",
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

  const totalBalance = computed(() => {
    return transactions.value.reduce((total, transaction) => {
      return total + parseFloat(transaction.amount);
    }, 0);
  });
</script>

<style scoped>
  .title-width {
    width: 185px; /* Adjust the width as needed */
  }
</style>
