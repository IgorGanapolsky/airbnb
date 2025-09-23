import { ThemeColors } from "@/types";

export const lightTheme: ThemeColors = {
  primary: "#667eea",
  primaryDark: "#5a67d8",
  accent: "#764ba2",
  background: "#f7fafc",
  surface: "#ffffff",
  text: "#1a202c",
  textSecondary: "#718096",
  error: "#f56565",
  success: "#48bb78",
  warning: "#ed8936",
  info: "#4299e1",
  divider: "#e2e8f0",
  gradient: {
    start: "#667eea",
    end: "#764ba2",
  },
};

export const darkTheme: ThemeColors = {
  primary: "#667eea",
  primaryDark: "#5a67d8",
  accent: "#764ba2",
  background: "#1a202c",
  surface: "#2d3748",
  text: "#f7fafc",
  textSecondary: "#a0aec0",
  error: "#fc8181",
  success: "#68d391",
  warning: "#f6ad55",
  info: "#63b3ed",
  divider: "#4a5568",
  gradient: {
    start: "#0f172a",
    end: "#1e293b",
  },
};

export const passwordStrengthColors = {
  0: "#f56565", // Very Weak - Red
  1: "#ed8936", // Weak - Orange
  2: "#ecc94b", // Fair - Yellow
  3: "#48bb78", // Good - Green
  4: "#38b2ac", // Strong - Teal
  5: "#4299e1", // Very Strong - Blue
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
};

export const fontSize = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

export const shadows = {
  sm: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  md: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
  },
  lg: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 8,
  },
  xl: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
    elevation: 16,
  },
};
