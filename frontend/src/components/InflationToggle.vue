<template>
  <v-btn-toggle v-model="isOn" :density="density" class="ml-4">
    <v-btn icon :value="true" class="compact-btn">
      <v-icon>mdi-finance</v-icon>
      <v-tooltip activator="parent" location="top">
        Toggle Inflation Adjustment
      </v-tooltip>
    </v-btn>
  </v-btn-toggle>

  <v-select
    :disabled="!isOn"
    v-model="selectedYear"
    :items="yearOptions"
    hide-details
    class="compact-select"
    :density="density"
    prepend-inner-icon="mdi-calendar"
    solo-inverted
    flat
    ><v-tooltip activator="parent" location="top"
      >Inflation Reference Year</v-tooltip
    >
  </v-select>
</template>

<script setup lang="ts">
  import { useMetadataStore } from "@/stores/metadata";
  import { computed, ref, watch } from "vue";

  const props = defineProps({
    modelValue: {
      type: Object as () => { isOn: boolean; year: number },
      required: true,
    },
    density: {
      type: String as () => "default" | "comfortable" | "compact",
      default: "default",
    },
  });

  const emit = defineEmits(["update:modelValue"]);

  const metadataStore = useMetadataStore();
  const inflationRates = computed(() => metadataStore.inflationRates);

  const isOn = ref(props.modelValue.isOn);

  const selectedYear = ref(props.modelValue.year);

  // Computed property to generate year options based on loaded inflation data
  const yearOptions = computed(() => {
    return Object.keys(inflationRates.value) // Use .value to access the reactive data
      .map((year) => parseInt(year))
      .sort((a, b) => b - a);
  });

  // Watch for changes in the inflation data to update the selected year and options
  watch(
    inflationRates,
    (newRates) => {
      if (Object.keys(newRates).length > 0) {
        selectedYear.value = Math.max(
          ...Object.keys(newRates).map((year) => parseInt(year))
        );
      }
    },
    { immediate: true }
  ); // Ensure the watch runs immediately with the current value

  // Ensure selectedYear is set correctly on component mount
  onMounted(() => {
    if (Object.keys(inflationRates.value).length > 0) {
      selectedYear.value = Math.max(
        ...Object.keys(inflationRates.value).map((year) => parseInt(year))
      );
    }
  });

  watch([isOn, selectedYear], () => {
    emit("update:modelValue", { isOn: isOn.value, year: selectedYear.value });
  });
</script>

<style scoped>
  .ml-4 {
    margin-left: 16px;
  }
  .compact-btn {
    padding: 8px;
  }

  .compact-select {
    max-width: 140px;
    padding-left: 4px;
    padding-right: 4px;
    background-color: var(--v-theme-surface);
  }
</style>
