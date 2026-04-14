/**
 * 文件说明：
 * 这是 Tailwind 与 DaisyUI 的统一配置入口。
 * 颜色、主题与组件风格的进一步细化可以由 A 同学在这里继续扩展，但不建议
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

