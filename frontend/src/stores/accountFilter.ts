import { defineStore } from "pinia";

export const useAccountFilterStore = defineStore("accountFilter", () => {
  // get saved account types for a given page key
  function get(key: string): string[] | undefined {
    const cookieKey = `accountTypes_${key}`;
    const cookie = document.cookie
      .split("; ")
      .find((row) => row.startsWith(cookieKey + "="));

    if (cookie) {
      try {
        return JSON.parse(decodeURIComponent(cookie.split("=")[1])) as string[];
      } catch {
        return undefined;
      }
    }

    return undefined;
  }

  // save account types for a given page key
  function set(key: string, value: string[]) {
    const cookieKey = `accountTypes_${key}`;
    document.cookie = `${cookieKey}=${encodeURIComponent(
      JSON.stringify(value)
    )}; path=/; max-age=${60 * 60 * 24 * 365}`; // 1 year
  }

  return { get, set };
});
