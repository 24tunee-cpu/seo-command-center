import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Custom SEO Dashboard colors
        cyber: {
          50: "#e0f2fe",
          100: "#bae6fd",
          200: "#7dd3fc",
          300: "#38bdf8",
          400: "#0ea5e9",
          500: "#0284c7",
          600: "#0369a1",
          700: "#075985",
          800: "#0c4a6e",
          900: "#082f49",
          950: "#020617",
        },
        health: {
          excellent: "#10b981", // Green
          good: "#3b82f6",      // Blue
          warning: "#f59e0b",   // Amber
          poor: "#ef4444",      // Red
        },
        severity: {
          critical: "#dc2626",
          high: "#ea580c",
          medium: "#ca8a04",
          low: "#16a34a",
          info: "#2563eb",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        "card-swipe-left": "swipeLeft 0.5s ease-out forwards",
        "card-swipe-right": "swipeRight 0.5s ease-out forwards",
        "card-enter": "cardEnter 0.3s ease-out",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "gauge-fill": "gaugeFill 1.5s ease-out forwards",
      },
      keyframes: {
        swipeLeft: {
          "0%": { transform: "translateX(0) rotate(0)", opacity: "1" },
          "100%": { transform: "translateX(-150%) rotate(-20deg)", opacity: "0" },
        },
        swipeRight: {
          "0%": { transform: "translateX(0) rotate(0)", opacity: "1" },
          "100%": { transform: "translateX(150%) rotate(20deg)", opacity: "0" },
        },
        cardEnter: {
          "0%": { transform: "scale(0.9)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(56, 189, 248, 0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(56, 189, 248, 0.6)" },
        },
        gaugeFill: {
          "0%": { strokeDashoffset: "339.292" },
          "100%": { strokeDashoffset: "var(--gauge-offset, 0)" },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
