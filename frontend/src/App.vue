<template>
  <v-app app>
    <v-navigation-drawer permanent expand-on-hover rail>
      <v-list>
        <v-list-item subtitle="By Isaac Norman" title="Finances">
          <template #prepend>
            <img
              src="/favicon.svg"
              style="height: 24px; width: 24px; margin-right: 32px"
            />
          </template>
        </v-list-item>
      </v-list>

      <v-divider></v-divider>

      <v-list density="compact" nav>
        <v-list-item prepend-icon="mdi-finance" title="Summary" to="/" />
        <v-list-item
          prepend-icon="mdi-cash-multiple"
          title="Accounts"
          to="/accounts"
        />
        <v-list-item
          prepend-icon="mdi-hand-coin"
          title="Taxable Income"
          to="/taxableIncome"
        />
      </v-list>

      <v-divider></v-divider>
      <v-list density="compact" nav>
        <v-list-item
          v-for="account in favoriteAccountsStore.getFavAccountObjects()"
          :key="account.account.id"
          :title="`${account.account.institution} - ${account.account.name}`"
          :to="`/accountDetails/${account.account.id}`"
          :prepend-icon="getAccountTypeIcon(account.account.accountType)"
        />
      </v-list>
    </v-navigation-drawer>
    <v-main>
      <div class="app-container">
        <router-view />
      </div>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
  // import { useAccountSummaries } from "@/stores/accountSummaries";
  import { onMounted } from "vue";
  import { useFavoriteAccountsStore } from "./stores/favouriteAccounts";
  import { getAccountTypeIcon } from "./utils";

  const favoriteAccountsStore = useFavoriteAccountsStore();

  onMounted(() => {
    document.title = "Finances";
    setFavicon("/favicon.svg");
  });

  const setFavicon = (url: string) => {
    const link: HTMLLinkElement = document.createElement("link");
    link.type = "image/svg+xml";
    link.rel = "icon";
    link.href = url;
    removeExistingFavicons();
    document.head.appendChild(link);
  };

  const removeExistingFavicons = () => {
    const existingFavicons = document.querySelectorAll("link[rel='icon']");
    existingFavicons.forEach((favicon) =>
      favicon.parentNode?.removeChild(favicon)
    );
  };
</script>

<style>
  .app-container {
    max-width: 1200px;
    margin: 0 auto;
  }
</style>
