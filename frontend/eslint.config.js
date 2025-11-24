import js from '@eslint/js';
import globals from 'globals';
import reactRecommended from 'eslint-plugin-react/configs/recommended.js';
import reactHooks from 'eslint-plugin-react-hooks';

export default [
  {
    ignores: [
      'build/**',
      'dist/**',
      'node_modules/**',
      'coverage/**',
      '*.config.js',
      'craco.config.js'
    ]
  },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx,mjs,cjs}'],
    plugins: {
      react: reactRecommended.plugins.react,
      'react-hooks': reactHooks
    },
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: {
          jsx: true
        }
      },
      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.node,
        process: 'readonly'
      }
    },
    settings: {
      react: {
        version: 'detect'
      }
    },
    rules: {
      // React rules
      'react/react-in-jsx-scope': 'off', // Not needed in React 17+
      'react/prop-types': 'warn',
      'react/jsx-uses-react': 'off',
      'react/jsx-uses-vars': 'error',

      // React Hooks rules
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // General rules
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'prefer-const': 'warn',
      'no-var': 'error',

      // Code quality
      'eqeqeq': ['error', 'always'],
      'curly': ['error', 'all'],
      'brace-style': ['error', '1tbs'],

      // Best practices
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error'
    }
  }
];
