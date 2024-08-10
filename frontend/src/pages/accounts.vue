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
        <v-toolbar color="white" density="compact">
          <v-text-field
            v-model="search"
            density="compact"
            hide-details
            label="Search"
            prepend-inner-icon="mdi-magnify"
            single-line
            variant="outlined"
          />
          <interpolate-toggle v-model="interpolate" class="ml-4" />
          <account-type-toggle v-model="accountTypes" class="ml-4" />
        </v-toolbar>
        <div class="ma-10" align="center" v-if="!tableData.length">
          No accounts to show.
        </div>
        <v-data-table
          v-else
          :headers="tableHeaders"
          hide-default-footer
          :items="tableData"
          :items-per-page="tableData.length"
          :search="search"
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
    filterAccountSummaries,
    formatBalance,
    formatHeaderText,
    formatLastTransactionDate,
  } from "@/utils";

  const search = ref("");
  const accountTypes = ref<string[]>(["Current/Credit", "Savings"]);

  const router = useRouter();
  const interpolate = ref<boolean>(true);

  const accountSummariesStore = useAccountSummariesStore();
  const accountSummaries = computed<AccountSummary[]>(() => {
    if (interpolate.value) {
      return accountSummariesStore.accountSummaries;
    } else {
      return accountSummariesStore.nonInterpolatedAccountSummaries;
    }
  });
  const filteredAccountSummaries = computed<AccountSummary[]>(() => {
    return filterAccountSummaries(accountSummaries.value, accountTypes.value);
  });

  const tableData = computed(() => {
    return filteredAccountSummaries.value.map((summary) => ({
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
  // also it should be in the table and based on items so it inherits the filtering
  const totalBalance = computed(() => {
    return filteredAccountSummaries.value.reduce((total, accountSummary) => {
      return total + parseFloat(accountSummary.balance);
    }, 0);
  });
</script>
