export default {
    plugins: {
        '@tailwindcss/postcss': {},
        autoprefixer: {}, // Autoprefixer might not be needed with v4 but keeping it safe or removing it? 
        // v4 handles prefixing usually. Let's keep it if installed.
    },
}
