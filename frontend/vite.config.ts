import { defineConfig } from "vite";
import dyadComponentTagger from "@dyad-sh/react-vite-component-tagger";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { splitVendorChunkPlugin } from "vite";

export default defineConfig(({ command, mode }) => ({
  server: {
    host: "::",
    port: 3000,
  },
  plugins: [
    dyadComponentTagger(),
    react(),
    splitVendorChunkPlugin()
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    // Production optimizations
    target: 'esnext',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: mode === 'production',
        drop_debugger: mode === 'production',
      },
    },
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-tabs'],
          utils: ['clsx', 'tailwind-merge'],
        },
      },
    },
    // Enable source maps in development only
    sourcemap: mode === 'development',
    // Optimize chunk size
    chunkSizeWarningLimit: 1000,
  },
  // Performance optimizations
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react/jsx-runtime',
    ],
  },
  // Enable CSS code splitting
  css: {
    devSourcemap: mode === 'development',
  },
  // Preview server configuration for production testing
  preview: {
    port: 4173,
    host: true,
  },
}));
