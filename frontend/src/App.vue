<template>
  <v-app app>
    <!-- <v-app-bar
      app
      :elevation="5"
      rounded
      scroll-behavior="hide collapse"
      scroll-threshold="1"
    >
      <template v-slot:prepend>
        <v-app-bar-nav-icon />
      </template>

      <v-app-bar-title>Application Bar</v-app-bar-title>

    </v-app-bar> -->
    <v-main>
      <router-view />
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
