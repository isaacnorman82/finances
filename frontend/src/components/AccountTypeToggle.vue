<template>
  <v-btn-toggle v-model="localAccountTypes" :density="density" multiple>
    <v-btn icon value="Current/Credit">
      <v-icon>mdi-credit-card-outline</v-icon>
      <v-tooltip activator="parent" location="top">Current/Credit</v-tooltip>
    </v-btn>
    <v-btn icon value="Savings">
      <v-icon>mdi-piggy-bank-outline</v-icon>
      <v-tooltip activator="parent" location="top">Savings</v-tooltip>
    </v-btn>
    <v-btn icon value="Asset">
      <v-icon>mdi-home-outline</v-icon>
      <v-tooltip activator="parent" location="top">Assets</v-tooltip>
    </v-btn>
    <v-btn icon value="Pension">
      <v-icon>mdi-cash-clock</v-icon>
      <v-tooltip activator="parent" location="top">Pensions</v-tooltip>
    </v-btn>
    <v-btn icon value="Loan">
      <v-icon>mdi-hand-extended-outline</v-icon>
      <v-tooltip activator="parent" location="top">Loans</v-tooltip>
    </v-btn>
    <v-btn icon value="isClosed">
      <v-icon>mdi-cash-off</v-icon>
      <v-tooltip activator="parent" location="top">Closed</v-tooltip>
    </v-btn>
  </v-btn-toggle>
</template>

<script setup lang="ts">
  import { useAccountFilterStore } from "@/stores/accountFilter";
  import { onMounted, ref, watch } from "vue";

  const defaultAccountTypes = [
    "Current/Credit",
    "Savings",
    "Asset",
    "Loan",
    "Pension",
    "isClosed",
  ];

  const props = defineProps({
    modelValue: {
      type: Array as () => string[],
      default: () => [],
    },
    density: {
      type: String as () => "default" | "comfortable" | "compact",
      default: "default",
    },
    filterKey: {
      type: String,
      default: "common",
    },
  });

  const emit = defineEmits(["update:modelValue"]);

  const store = useAccountFilterStore();
  const key = props.filterKey;

  // Load saved from store (cookies) or default
  const saved = store.get(key);
  const localAccountTypes = ref<string[]>(
    saved === undefined ? defaultAccountTypes : saved
  );

  // Emit initial value to parent so v-model is in sync
  onMounted(() => {
    emit("update:modelValue", localAccountTypes.value);
  });

  // Watch changes: persist to store and emit to parent
  watch(
    localAccountTypes,
    (newVal) => {
      store.set(key, newVal);
      emit("update:modelValue", newVal);
    },
    { deep: true }
  );
</script>
