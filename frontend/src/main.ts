/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from "@/plugins";

// Components
import App from "./App.vue";

// Composables
import { useAccountSummariesStore } from "@/stores/accountSummaries";
import { createApp } from "vue";
import { useDataSeriesStore } from "./stores/dataSeries";

const app = createApp(App);

registerPlugins(app);

app.mount("#app");

const accountSummariesStore = useAccountSummariesStore();
accountSummariesStore.loadAccountSummaries();

const dataSeriesStore = useDataSeriesStore();
dataSeriesStore.loadDataSeries();
