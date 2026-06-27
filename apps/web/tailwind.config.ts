import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        wk: {
          green: "#16a34a",
          red: "#dc2626",
          gray: "#6b7280",
          dark: "#1f2937",
        },
      },
    },
  },
  plugins: [],
};

export default config;
