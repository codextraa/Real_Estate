import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import prettier from "eslint-config-prettier/flat";
import reactCompiler from "eslint-plugin-react-compiler";

const eslintConfig = defineConfig([
  ...nextVitals,
  prettier,
  {
    plugins: {
      "react-compiler": reactCompiler,
    },
    rules: {
      "no-unused-vars": "warn",
      "react/jsx-uses-vars": "error",
      "react-compiler/react-compiler": "error",
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/immutability": "warn",
      "react/no-unescaped-entities": "off",
      "react-hooks/exhaustive-deps": "warn",
    },
  },
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
