import { getDataSeries } from "@/services/apiService";
import type { DataSeries } from "@/types.d.ts";
import { defineStore } from "pinia";

export const useDataSeriesStore = defineStore("dataSeries", {
  state: () => ({
    dataSeriesCache: {} as Record<string, DataSeries[]>,
  }),

  actions: {
    async loadDataSeries(): Promise<void> {
      const fetchedData: DataSeries[] = await getDataSeries();

      // Populate the cache with fetched data
      this.dataSeriesCache = {};
      for (const data of fetchedData) {
        if (!this.dataSeriesCache[data.key]) {
          this.dataSeriesCache[data.key] = [];
        }
        this.dataSeriesCache[data.key].push(data);
      }
    },

    getDataSeries(keys: string | string[]): DataSeries[] {
      // Normalize keys to always be an array
      if (!Array.isArray(keys)) {
        keys = [keys];
      }

      // Concatenate the results for all keys
      return keys.reduce<DataSeries[]>((acc, key) => {
        if (this.dataSeriesCache[key]) {
          acc.push(...this.dataSeriesCache[key]);
        } else {
          console.log(`Key "${key}" not found in the data series cache.`);
        }
        return acc;
      }, []);
    },
  },
});
