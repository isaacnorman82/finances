<!-- UploadTransactionsDialog.vue -->
<template>
  <v-dialog v-model="isOpen" activator="parent" max-width="600px">
    <template v-slot:default="{ isActive }">
      <v-card
        prepend-icon="mdi-file-upload-outline"
        title="Add Transactions"
        subtitle="Upload a file with transactions for this account"
      >
        <v-card-text>
          Existing transactions for the same time window will be deleted first.
        </v-card-text>
        <v-card-text>
          <v-form>
            <v-select
              label="Ingest File Type"
              prepend-icon="mdi-file-question-outline"
              :items="metadataStore.ingestValues"
              v-model="formData.ingestType"
              variant="outlined"
            ></v-select>
            <v-file-input
              clearable
              label="Ingest File"
              v-model="formData.file"
              accept=".csv,.ofx"
              show-size
              variant="outlined"
            ></v-file-input>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            text="Submit"
            variant="text"
            color="primary"
            @click="handleSubmit()"
            :disabled="!formData.file"
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
  import { ingestTransactions } from "@/services/apiService";
  import { useMetadataStore } from "@/stores/metadata";
  import { AccountSummary } from "@/types.d";
  import { formatIngestResult } from "@/utils";
  import { ref } from "vue";

  const metadataStore = useMetadataStore();

  const props = defineProps<{
    accountSummary: AccountSummary;
  }>();

  const formData = ref({
    ingestType: "csv",
    file: null as File | null,
  });

  const handleSubmit = async () => {
    // console.log("Form Submitted:", formData.value);

    if (formData.value.file) {
      const data = new FormData();
      data.append("upload_file", formData.value.file);

      try {
        const result = await ingestTransactions(
          props.accountSummary.account.id,
          data,
          formData.value.ingestType
        );
        // console.log("Ingest successful:", result);
        showResults(formatIngestResult(result));
        resetForm();
      } catch (error) {
        console.error("Failed:  ", error);
        showResults("Failed: " + error, "red");
        resultSnackbar.value = true;
      }
    } else {
      console.error("No file selected.");
    }
  };

  function showResults(msg: string, color: string = "secondary") {
    resultText.value = msg;
    resultColor.value = color;
    resultSnackbar.value = true;
  }

  const resetForm = () => {
    formData.value.ingestType = props.accountSummary.account.defaultIngestType;
    formData.value.file = null;
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
