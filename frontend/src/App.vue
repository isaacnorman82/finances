<template>
  <v-app app>
    <!-- <v-app-bar app flat rounded>
      <template v-slot:prepend>
        <v-app-bar-nav-icon />
      </template>

      <v-app-bar-title>Application Bar</v-app-bar-title>
    </v-app-bar> -->
    <v-navigation-drawer permanent expand-on-hover rail>
      <v-list>
        <v-list-item subtitle="By Isaac Norman" title="Finances"
          ><template #prepend>
            <img
              src="/favicon.svg"
              style="height: 24px; width: 24px; margin-right: 32px"
            /> </template
        ></v-list-item>
      </v-list>

      <v-divider></v-divider>

      <v-list density="compact" nav>
        <v-list-item
          prepend-icon="mdi-finance"
          title="Summary"
          to="/"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-cash-multiple"
          title="Accounts"
          to="accounts"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-hand-coin"
          title="Taxable Income"
          to="taxableIncome"
        ></v-list-item>
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

  // const accountSummariesStore = useAccountSummaries();

  // onBeforeMount(async () => {
  //   // console.log("onBeforeMount");
  //   console.log("Loading account summaries");
  //   await accountSummariesStore.loadAccountSummaries();
  // });

  onMounted(() => {
    // Set the page title
    document.title = "My Vuetify App";

    // Set the favicon
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
