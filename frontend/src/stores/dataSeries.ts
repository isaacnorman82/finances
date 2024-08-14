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

    getDataSeries(key: string | string[]): DataSeries[] {
      if (Array.isArray(key)) {
        // If key is an array, concatenate the results for all keys
        return key.reduce<DataSeries[]>((acc, k) => {
          if (this.dataSeriesCache[k]) {
            acc.push(...this.dataSeriesCache[k]);
          } else {
            console.log(`Key "${k}" not found in the data series cache.`);
          }
          return acc;
        }, []);
      } else {
        // If key is a string, return data from cache if the key exists, else log an error and return an empty list
        if (this.dataSeriesCache[key]) {
          return this.dataSeriesCache[key];
        } else {
          console.error(`Key "${key}" not found in the data series cache.`);
          return [];
        }
      }
    },
  },
});
