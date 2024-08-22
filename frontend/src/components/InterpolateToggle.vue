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

  const localValue = computed({
    get() {
      return props.modelValue;
    },
    set(value) {
      const booleanValue = value === true;
      if (booleanValue !== props.modelValue) {
        emit("update:modelValue", booleanValue);
      }
    },
  });
</script>

<style scoped>
  .compact-btn {
    padding-left: 4px !important;
    padding-right: 4px !important;
    min-width: 48px !important;
  }
</style>
