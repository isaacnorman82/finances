<template>
  <v-btn-toggle v-model="localAccountTypes" :density="density" multiple>
    <v-btn icon="mdi-credit-card-outline" value="Current/Credit" />
    <v-btn icon="mdi-piggy-bank-outline" value="Savings" />
    <v-btn icon="mdi-home-outline" value="Asset" />
    <v-btn icon="mdi-cash-clock" value="Pension" />
    <v-btn icon="mdi-hand-extended-outline" value="Loan" />
    <v-btn icon="mdi-cash-off" value="inactive" />
  </v-btn-toggle>
</template>

<script setup lang="ts">
  import { defineEmits, defineProps, ref, watch } from "vue";

  const props = defineProps({
    modelValue: {
      type: Array as () => string[],
      default: () => [],
    },
    density: {
      type: String as () => "default" | "comfortable" | "compact",
      default: "default",
    },
  });

  const emit = defineEmits(["update:modelValue"]);

  const localAccountTypes = ref(props.modelValue);

  watch(localAccountTypes, (newVal) => {
    emit("update:modelValue", newVal);
  });
</script>
