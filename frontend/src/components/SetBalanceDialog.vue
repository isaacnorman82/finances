<!-- UploadTransactionsDialog.vue -->
<template>
  <v-dialog v-model="isOpen" activator="parent" max-width="600px">
    <template v-slot:default="{ isActive }">
      <v-card
        prepend-icon="mdi-clock-edit-outline"
        title="Set Balance"
        subtitle="Manually set the balance for a given month"
      >
        <v-card-text>
          <p>
            Insert an artificial transaction to achieve the specified end
            balance. Useful if you don't have a suitable transaction file to
            upload.
          </p>
          <br />
          <p>
            Choose between just setting a balance or setting both value and
            contributions for accounts that grow.
          </p>
        </v-card-text>
        <v-card-text>
          <v-form ref="formRef" v-model="isFormValid">
            <v-row dence>
              <v-radio-group inline v-model="selectedType">
                <v-radio label="Balance Adjustment" value="balance"></v-radio>
                <v-radio
                  label="Value and Contributions"
                  value="valueAndContrib"
                ></v-radio>
              </v-radio-group>
            </v-row>
            <v-row dense>
              <v-col cols="auto">
                <v-select
                  label="Month"
                  prepend-icon="mdi-calendar-month-outline"
                  v-model="formData.month"
                  :items="months"
                  variant="outlined"
                ></v-select>
              </v-col>
              <v-col cols="auto">
                <v-text-field
                  class="ml-4"
                  v-model="formData.year"
                  label="Year"
                  type="number"
                  :rules="yearRules"
                  variant="outlined"
                  min="1970"
                  :max="currentMonthYear.year"
                  required
                />
              </v-col>
            </v-row>
            <v-row v-if="selectedType === 'balance'" dense class="mt-4">
              <v-col cols="auto">
                <v-text-field
                  max-width="220px"
                  v-model="formData.balance"
                  label="Enter Balance"
                  prepend-icon="mdi-currency-gbp"
                  type="number"
                  step="0.01"
                  min="0"
                  :rules="currencyRules"
                  variant="outlined"
                  required
                  persistent-hint
                  :hint="`Existing Value £${
                    selectedMonthYearBalance?.endBalance || 0
                  }`"
                />
              </v-col>
            </v-row>
            <v-row v-else>
              <v-col cols="auto">
                <v-text-field
                  max-width="220px"
                  v-model="formData.balance"
                  label="Enter Value"
                  prepend-icon="mdi-currency-gbp"
                  type="number"
                  step="0.01"
                  min="0"
                  :rules="currencyRules"
                  variant="outlined"
                  required
                  persistent-hint
                  :hint="`Existing Value £${
                    selectedMonthYearBalance?.endBalance || 0
                  }`"
                />
              </v-col>
              <v-col cols="auto">
                <v-text-field
                  max-width="220px"
                  v-model="formData.contrib"
                  label="Enter Contributions"
                  prepend-icon="mdi-currency-gbp"
                  type="number"
                  step="0.01"
                  min="0"
                  :rules="currencyRules"
                  variant="outlined"
                  required
                  persistent-hint
                  :hint="`Existing Value £${
                    selectedMonthYearBalance?.depositsToDate || 0
                  }`"
                />
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            text="Submit"
            variant="text"
            color="primary"
            @click="handleSubmit()"
          />
          <v-btn text="Close" variant="text" @click="isActive.value = false" />
        </v-card-actions>
      </v-card>
    </template>
  </v-dialog>
  <v-snackbar v-model="resultSnackbar" :timeout="5000" :color="resultColor">
    {{ resultText }}

    <template v-slot:actions>
      <v-btn text="Close" variant="text" @click="resultSnackbar = false" />
    </template>
  </v-snackbar>
</template>

<script setup lang="ts">
  import { setBalance } from "@/services/apiService";
  import { AccountSummary, MonthYear } from "@/types.d";
  import { formatTransaction, getLatestBalanceForDate } from "@/utils";
  import { ref } from "vue";

  // set balance should always be given a non-interpolated accountSummary
  const props = defineProps<{
    accountSummary: AccountSummary;
  }>();

  const isFormValid = ref(true);
  const formRef = ref();
  const selectedType = ref("balance");

  // Array of month names
  const months: string[] = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  // Initialize MonthYear object with the current date
  const currentMonthYear = new MonthYear();

  // Initialize form data
  const formData = ref({
    month: months[currentMonthYear.month - 1], // Month is 1-based, array is 0-based
    year: currentMonthYear.year,
    balance: "", // Balance Mode - currency field
    value: "", // Value and Contrib mode - total value
    contrib: "", // Value and Cotrib mode - total contrib
  });

  // Computed property for combined year-month format
  const selectedMonthYear = computed(() => {
    const monthNumber = (months.indexOf(formData.value.month) + 1)
      .toString()
      .padStart(2, "0");
    return `${formData.value.year}-${monthNumber}`;
  });

  const selectedMonthYearBalance = computed(() => {
    return getLatestBalanceForDate(
      props.accountSummary,
      new MonthYear(selectedMonthYear.value)
    );
  });

  // Validation rules for the year input
  const yearRules = [
    (v: number) => !!v || "Year is required",
    (v: number) => (v >= 1970 && v <= currentMonthYear.year) || "Invalid",
  ];

  const currencyRules = [
    (v: number) => !!v || "Amount is required",
    (v: string) => /^(-)?\d+(\.\d{1,2})?$/.test(v) || "Max 2 decimal places",
  ];

  const handleSubmit = async () => {
    if (formRef.value) {
      const valid = await formRef.value.validate();
      if (valid.valid) {
        console.log(valid.valid);
        try {
          // Convert month name back to a number (e.g., "January" -> "01")
          // const monthNumber = (months.indexOf(formData.value.month) + 1)
          //   .toString()
          //   .padStart(2, "0");
          // const yearMonth = `${formData.value.year}-${monthNumber}`;

          var depositsToDate = undefined;
          if (selectedType.value == "valueAndContrib") {
            depositsToDate = parseFloat(formData.value.contrib);
          }

          // Call the setBalance function
          const transactions = await setBalance(
            props.accountSummary.account.id,
            parseFloat(formData.value.balance),
            depositsToDate,
            selectedMonthYear.value
          );

          if (transactions.length === 0) {
            showResults("Balance Unchanged:  No transactions added.");
          } else {
            let successMsg = `Success:  Added ${formatTransaction(
              transactions[0]
            )}`;

            if (transactions.length > 1) {
              successMsg += `, ${formatTransaction(transactions[1])}`;
            }
            showResults(successMsg);
          }
          resetForm();
        } catch (error) {
          console.error("Error setting balance:", error);
          showResults("Failed:  " + error, "red");
        }
      }
    }
  };

  function showResults(msg: string, color: string = "secondary") {
    resultText.value = msg;
    resultColor.value = color;
    resultSnackbar.value = true;
  }

  const resetForm = () => {
    formData.value.month = months[currentMonthYear.month - 1];
    formData.value.year = currentMonthYear.year;
    formData.value.balance = "";
    formData.value.contrib = "";

    if (formRef.value) {
      formRef.value.resetValidation();
    }
  };

  const isOpen = ref(false);
  const resultSnackbar = ref(false);
  const resultText = ref("");
  const resultColor = ref("secondary");

  watch(
    () => isOpen.value,
    (newValue, oldValue) => {
      if (newValue && !oldValue) {
        resetForm();
      }
    }
  );
</script>
