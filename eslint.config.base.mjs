// Base ESLint configuration shared across frontend and mobile packages
// This file defines common rules for TypeScript/React projects

/** @type {import('eslint').Linter.Config[]} */
export const baseRules = {
  // TypeScript rules
  '@typescript-eslint/no-explicit-any': 'error',
  '@typescript-eslint/no-unused-vars': [
    'error',
    {
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_',
    },
  ],
  '@typescript-eslint/no-non-null-assertion': 'warn',
  '@typescript-eslint/prefer-nullish-coalescing': 'error',
  '@typescript-eslint/strict-boolean-expressions': 'off',

  // React rules
  'react/prop-types': 'off',
  'react/react-in-jsx-scope': 'off',
  'react-hooks/rules-of-hooks': 'error',
  'react-hooks/exhaustive-deps': 'warn',

  // General rules
  'no-console': ['warn', { allow: ['warn', 'error'] }],
  'prefer-const': 'error',
  'no-var': 'error',
  eqeqeq: ['error', 'always', { null: 'ignore' }],
}

export const ignorePatterns = [
  'node_modules/',
  'dist/',
  'build/',
  '.expo/',
  'coverage/',
  '*.gen.ts',
  'api.gen.ts',
]
