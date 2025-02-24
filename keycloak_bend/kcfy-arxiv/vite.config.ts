import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { keycloakify } from "keycloakify/vite-plugin";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        react(),
        keycloakify({
            themeName: "kc-arXiv-react",
            accountThemeImplementation: "none",
            environmentVariables: [
                { name: "ARXIV_USER_LOGIN_URL", default: "https://arxiv.org/user/login" },
                { name: "ARXIV_USER_REGISTRATION_URL", default: "https://arxiv.org/user/register" },
                { name: "ARXIV_PRIVACY_POLICY", default: "https://arxiv.org/help/policies/privacy_policy" },
                { name: "ARXIV_MEMBER_INSTITUTIONS", default: "https://info.arxiv.org/about/ourmembers.html" }
            ]
        })
    ]
});
