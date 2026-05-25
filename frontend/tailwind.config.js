/**
 * 文件说明：
 * 这是 Tailwind 与 DaisyUI 的统一配置入口。
 * 颜色、主题与组件风格的进一步细化可以在这里扩展，但不建议
 * 替换整体技术方案。
 */
export default {
  content: ["./index.html", "./src/**/*.{vue,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        campus: {
          50: "#f5fbff",
          100: "#e5f4ff",
          500: "#1570ef",
          700: "#0e4fae",
          900: "#0b2344",
        },
        cobalt: "#2553d4",
        tomato: "#e4572e",
        butter: "#f0c94a",
        cream: "#f5efe2",
        ink: "#1f2230",
        sage: "#5c715e",
        cat: {
          delivery: "#2553d4",
          food: "#e4572e",
          carry: "#d6a74f",
          other: "#5c715e",
        },
      },
      fontFamily: {
        display: ["Fredoka", "Noto Sans SC", "sans-serif"],
        body: ["Noto Sans SC", "sans-serif"],
      },
      boxShadow: {
        chunky: "6px 6px 0 rgba(31,34,48,0.12)",
        "chunky-sm": "4px 4px 0 rgba(31,34,48,0.10)",
        "chunky-lg": "8px 8px 0 rgba(31,34,48,0.14)",
        soft: "0 16px 42px rgba(26,36,49,0.12)",
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        campusmast: {
          primary: "#1570ef",
          secondary: "#0b2344",
          accent: "#16a34a",
          neutral: "#1f2937",
          "base-100": "#ffffff",
          info: "#0ea5e9",
          success: "#16a34a",
          warning: "#f59e0b",
          error: "#dc2626",
        },
      },
    ],
  },
};
