<template>
  <v-container fluid>
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
      <v-col>
        <v-data-table
          :headers="tableHeaders"
          hide-default-footer
          :items="tableData"
          :items-per-page="tableData.length"
        >
          <template v-slot:item="{ item }">
            <tr style="cursor: pointer" @click="navigateToAccount(item)">
              <td>{{ item.institution }}</td>
              <td>{{ item.name }}</td>
              <td v-html="formatBalance(item.balance)" />

              <td>{{ item.lastTransactionDate }}</td>
            </tr>
          </template>
          <template v-slot:body.append>
            <tr>
              <td colspan="2" style="text-align: right; font-weight: bold">
                Total Amount:
              </td>
              <td>
                {{ formatBalance(totalBalance) }}
              </td>
            </tr>
          </template>
        </v-data-table>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { useAccountSummariesStore } from "@/stores/accountSummaries";
  import type { AccountSummary } from "@/types.d.ts";
  import {
    formatBalance,
    formatHeaderText,
    formatLastTransactionDate,
  } from "@/utils";

  const router = useRouter();
  const accountSummariesStore = useAccountSummariesStore();

  const accountSummaries = computed<AccountSummary[]>(
    () => accountSummariesStore.accountSummaries
  );

  const tableData = computed(() => {
    return accountSummaries.value.map((summary) => ({
      id: summary.account.id,
      institution: summary.account.institution,
      name: summary.account.name,
      balance: summary.balance,
      lastTransactionDate: formatLastTransactionDate(
        summary.lastTransactionDate
      ),
    }));
  });

  const tableHeaders = computed(() => {
    if (tableData.value.length === 0) return [];

    // Generate headers based on the keys of the first item in tableData
    const keys = Object.keys(tableData.value[0])
      .filter((key) => key !== "id")
      .map((key) => ({
        title: formatHeaderText(key),
        key,
      }));
    return keys;
  });

  const breadcrumbs = computed(() => {
    return [
      {
        title: "Accounts",
        disabled: false,
      },
    ];
  });

  function navigateToAccount(item: any) {
    router.push({ path: `/accountDetails/${item.id}` });
  }

  //todo this function is in both this file and index.vue and should prob use the items in the table in case of filtering
  const totalBalance = computed(() => {
    return accountSummaries.value.reduce((total, accountSummary) => {
      return total + parseFloat(accountSummary.balance);
    }, 0);
  });
</script>
