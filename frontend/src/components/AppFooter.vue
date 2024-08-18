<template>
  <v-footer app height="40">
    <v-spacer />
    <a
      v-for="item in items"
      :key="item.title"
      class="d-inline-block mx-2 social-link"
      :href="item.href"
      rel="noopener noreferrer"
      target="_blank"
      :title="item.title"
    >
      <v-icon :icon="item.icon" size="16" />
    </a>
    <span class="version-info">Version: {{ version }}</span>
  </v-footer>
</template>

<script setup lang="ts">
  import { getAPIVersion } from "@/services/apiService";
  import { onMounted, ref } from "vue";

  // Footer items
  const items = [
    {
      title: "GitHub",
      icon: "mdi-github",
      href: "https://github.com/isaacnorman82/finances",
    },
  ];

  const version = ref<string | null>(null);

  onMounted(async () => {
    try {
      const versionInfo = await getAPIVersion();
      version.value = versionInfo.apiVersion;
    } catch (error) {
      console.error("Error fetching API version:", error);
      version.value = "Error";
    }
  });
</script>

<style scoped lang="sass">
  .social-link :deep(.v-icon)
    color: rgba(var(--v-theme-on-background), var(--v-disabled-opacity))
    text-decoration: none
    transition: .2s ease-in-out

    &:hover
      color: rgba(25, 118, 210, 1)

  .version-info
    font-size: 12px
    color: rgba(var(--v-theme-on-background), 0.6)
    text-align: right
    line-height: 1.5
    padding: 4px 0 2px 0
</style>
