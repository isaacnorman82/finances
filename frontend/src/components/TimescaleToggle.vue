<template>
  <v-btn-toggle
    v-model="localTimescale"
    color="primary"
    :density="density"
    mandatory
    :variant="variant"
  >
    <v-btn text="6M" :value="Timescale.SixMonths" />
    <v-btn text="1Y" :value="Timescale.OneYear" />
    <v-btn text="2Y" :value="Timescale.TwoYears" />
    <v-btn text="5Y" :value="Timescale.FiveYears" />
    <v-btn text="ALL" :value="Timescale.All" />
  </v-btn-toggle>
</template>

<script setup lang="ts">
  import { Timescale } from "@/types.d";
  import { defineEmits, defineProps, ref, watch } from "vue";

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
