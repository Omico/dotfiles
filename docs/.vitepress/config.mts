import { defineConfig } from "vitepress";
import generatedSidebar from "./sidebar.generated.mts";
import generatedNav from "./nav.generated.mts";

export default defineConfig({
  base: "/",
  srcDir: "src",
  title: "Omico's dotfiles",
  description: "Docs for Omico's dotfiles.",
  themeConfig: {
    socialLinks: [
      { icon: "github", link: "https://github.com/Omico/dotfiles" },
    ],
    nav: generatedNav,
    sidebar: generatedSidebar,
  },
});
