import { getInflationRates, getIngestValues } from "@/services/apiService";
import { InflationRates } from "@/types";
import { defineStore } from "pinia";

export const useMetadataStore = defineStore("metadata", {
  state: () => ({
    ingestValues: [] as string[],
    inflationRates: {} as InflationRates,
  }),

  actions: {
    async loadMetadata() {
      try {
        console.log("Loading metadata");

        // Fetch ingest values and inflation rates concurrently
        const [ingestValues, inflationRates] = await Promise.all([
          getIngestValues(),
          getInflationRates(),
        ]);

        // Assign the fetched data to the state
        this.ingestValues = ingestValues;
        this.inflationRates = inflationRates;

        console.log("Loaded metadata successfully");
      } catch (error) {
        console.error("Failed to load metadata:", error);
      }
    },
  },
});
