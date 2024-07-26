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
import { useAccountSummaries } from "@/stores/accountSummaries";
import { createApp } from "vue";

const app = createApp(App);

registerPlugins(app);

app.mount("#app");

const accountSummariesStore = useAccountSummaries();
accountSummariesStore.loadAccountSummaries();
