import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(214 32% 91%)",
        surface: "hsl(0 0% 100%)",
        muted: "hsl(210 40% 96%)",
        ink: "hsl(222 47% 11%)",
        subtle: "hsl(215 16% 47%)",
        brand: {
          50: "hsl(172 52% 96%)",
          100: "hsl(172 48% 88%)",
          600: "hsl(175 84% 32%)",
          700: "hsl(176 86% 26%)",
        },
        accent: {
          500: "hsl(43 96% 56%)",
          700: "hsl(34 92% 40%)",
        },
      },
      boxShadow: {
        panel: "0 1px 2px rgb(15 23 42 / 0.06)",
      },
    },
  },
  plugins: [],
} satisfies Config;
