import { getIngestValues } from "@/services/apiService";
import { defineStore } from "pinia";
export const useMetadataStore = defineStore("metadata", {
  state: () => ({
    ingestValues: [] as string[],
  }),

  actions: {
    async loadMetadata() {
      try {
        console.log("Loading metadata");
        this.ingestValues = await getIngestValues();
      } catch (error) {
        console.error("Failed to load metadata:", error);
      }
    },
  },
});
