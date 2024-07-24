/**
 * .eslint.js
 *
 * ESLint configuration file.
 */

// const { queryObjects } = require("v8");

module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: [
    "vuetify",
    "@vue/eslint-config-typescript",
    "./.eslintrc-auto-import.json",
  ],
  rules: {
    "vue/multi-word-component-names": "off",
    "vue/v-slot-style": "off",
    "space-before-function-paren": [
      "error",
      {
        anonymous: "always",
        named: "never",
        asyncArrow: "always",
      },
    ],
    quotes: ["error", "double"],
    semi: ["error", "always"],
    "arrow-parens": ["error", "always"],
  },
};
