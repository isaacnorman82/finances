<template>
  <v-btn-toggle v-model="localValue" :density="density" class="ml-4">
    <v-btn icon :value="true" class="compact-btn">
      <v-icon>mdi-chart-timeline-variant-shimmer</v-icon>
      <v-tooltip activator="parent" location="top">
        Interpolate missing data
      </v-tooltip>
    </v-btn>
  </v-btn-toggle>
</template>

<script setup lang="ts">
  import { defineEmits, defineProps, ref, watch } from "vue";

  // Define the props for the component
  const props = defineProps({
    modelValue: {
      type: Boolean,
      required: true,
    },
    density: {
      type: String as () => "default" | "comfortable" | "compact",
      default: "default",
    },
  });

  // Define the emits for the component
  const emit = defineEmits(["update:modelValue"]);

  // Create a local value for the toggle
  const localValue = ref(props.modelValue);

  // Watch for changes in localValue and emit them
  watch(localValue, (newValue) => {
    emit("update:modelValue", newValue);
  });

  // Watch for external changes to modelValue and update localValue
  watch(
    () => props.modelValue,
    (newValue) => {
      localValue.value = newValue;
    }
  );
</script>

<style scoped>
  .compact-btn {
    padding-left: 4px !important;
    padding-right: 4px !important;
    min-width: 48px !important;
  }
</style>
