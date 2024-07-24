<!-- src/pages/AccountDetails.vue -->
<template>
  <v-container>
    <v-row>
      <v-col>
        <v-card>
          <v-card-title>Account Details</v-card-title>
          <v-card-text>
            <!-- Display account details here -->
            Account ID: {{ accountId }}
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
  import { useRoute } from "vue-router";

  export default defineComponent({
    name: "AccountsView",
    components: {
      // StackedBarChart,
    },

    setup() {
      const route = useRoute();
      const accountId = route.params.id;

      return {
        accountId,
      };
    },
  });
</script>

<style scoped>
  /* Add your styles here */
</style>
