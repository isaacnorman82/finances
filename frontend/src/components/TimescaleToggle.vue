<template>
  <v-btn-toggle
    v-model="localTimescale"
    color="primary"
    :density="density"
    mandatory
    :variant="variant"
  >
    <v-btn text="6M" :value="Timescale.SixMonths" class="compact-btn" />
    <v-btn text="1Y" :value="Timescale.OneYear" class="compact-btn" />
    <v-btn text="2Y" :value="Timescale.TwoYears" class="compact-btn" />
    <v-btn text="5Y" :value="Timescale.FiveYears" class="compact-btn" />
    <v-btn text="ALL" :value="Timescale.All" class="compact-btn" />
  </v-btn-toggle>
</template>

<script setup lang="ts">
  import { Timescale } from "@/types.d";
  import { ref, watch } from "vue";

  const props = defineProps<{
    modelValue: Timescale;
    density: "default" | "comfortable" | "compact";
    variant:
      | "flat"
      | "plain"
      | "text"
      | "elevated"
      | "tonal"
      | "outlined"
      | undefined;
  }>();

  const emit = defineEmits(["update:modelValue"]);

  const localTimescale = ref<Timescale>(props.modelValue);

  watch(localTimescale, (newValue) => {
    emit("update:modelValue", newValue);
  });
</script>

<style scoped>
  .compact-btn {
    padding-left: 4px !important;
    padding-right: 4px !important;
    min-width: 48px !important;
  }
</style>
