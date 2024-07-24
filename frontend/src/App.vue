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

<script lang="ts" setup>
  //
</script>
