<template>
  <v-container style="height: 100vh; width: 100%">
    <v-row>
      <v-col>
        <v-breadcrumbs bg-color="primary" :items="breadcrumbs">
          <template v-slot:item="{ item }">
            <v-breadcrumbs-item :disabled="item.disabled" :to="item.to">
              {{ item.title }}
            </v-breadcrumbs-item>
          </template>
        </v-breadcrumbs>
        <v-card flat title="Account Details">
          <v-card-text>
            <!-- Display account details here -->
            Account ID: {{ accountId }} {{ accountSummary?.account }}
          </v-card-text>
        </v-card>
        <v-card flat title="Transactions">
          <v-toolbar color="white" density="compact">
            <v-btn icon="mdi-arrow-left" @click="changeMonth(-1)" />
            <v-card-title class="text-center title-width">
              {{ displayDate }}
            </v-card-title>
            <v-btn icon="mdi-arrow-right" @click="changeMonth(1)" />
            <v-text-field
              v-model="search"
              density="compact"
              hide-details
              label="Search"
              prepend-inner-icon="mdi-magnify"
              single-line
              variant="outlined"
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
  import type { AccountSummary, Transaction } from "@/types.d.ts";
  import { formatBalance, formatDate } from "@/utils";
  import { addMonths, startOfMonth } from "date-fns";
  import { useRoute } from "vue-router";
  import { useDate } from "vuetify";

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

  const changeMonth = (increment: number) => {
    selectedDate.value = addMonths(selectedDate.value, increment);
  };

  const transactionsStore = useTransactions();
  const transactions = ref<Transaction[]>([]);

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
    width: 200px; /* Adjust the width as needed */
  }
</style>
