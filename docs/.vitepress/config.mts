import { defineConfig } from "vitepress";
import generatedSidebar from "./sidebar.generated.mts";

export default defineConfig({
  base: "/",
  srcDir: "src",
  title: "Omico's dotfiles",
  description: "Docs for Omico's dotfiles.",
  themeConfig: {
    socialLinks: [
      { icon: "github", link: "https://github.com/Omico/dotfiles" },
    ],
    nav: [
      { text: "Home", link: "/" },
      { text: "Agent skills", link: "/agent-skills/" },
      { text: "Cursor commands", link: "/cursor-commands/" },
      { text: "Cursor rules", link: "/cursor-rules/" },
    ],
    sidebar: generatedSidebar,
  },
});
