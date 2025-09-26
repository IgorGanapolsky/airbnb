import { PasswordOptions, PasswordStrength } from "@/types";

const UPPERCASE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const LOWERCASE_CHARS = "abcdefghijklmnopqrstuvwxyz";
const NUMBER_CHARS = "0123456789";
const SYMBOL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?";
const AMBIGUOUS_CHARS = "il1Lo0O";

export const generatePassword = (options: PasswordOptions): string => {
  let availableChars = "";
  let password = "";
  const requiredChars: string[] = [];

  // Build character set based on options
  if (options.includeLowercase) {
    availableChars += LOWERCASE_CHARS;
    requiredChars.push(
      LOWERCASE_CHARS[Math.floor(Math.random() * LOWERCASE_CHARS.length)],
    );
  }

  if (options.includeUppercase) {
    availableChars += UPPERCASE_CHARS;
    requiredChars.push(
      UPPERCASE_CHARS[Math.floor(Math.random() * UPPERCASE_CHARS.length)],
    );
  }

  if (options.includeNumbers) {
    availableChars += NUMBER_CHARS;
    requiredChars.push(
      NUMBER_CHARS[Math.floor(Math.random() * NUMBER_CHARS.length)],
    );
  }

  if (options.includeSymbols) {
    availableChars += SYMBOL_CHARS;
    requiredChars.push(
      SYMBOL_CHARS[Math.floor(Math.random() * SYMBOL_CHARS.length)],
    );
  }

  // Add custom characters
  if (options.customCharacters) {
    availableChars += options.customCharacters;
  }

  // Remove excluded characters
  if (options.excludeCharacters) {
    for (const char of options.excludeCharacters) {
      availableChars = availableChars.replace(
        new RegExp(escapeRegExp(char), "g"),
        "",
      );
    }
  }

  // Remove ambiguous characters if specified
  if (options.excludeAmbiguous) {
    for (const char of AMBIGUOUS_CHARS) {
      availableChars = availableChars.replace(new RegExp(char, "g"), "");
    }
  }

  // If no characters available, use defaults
  if (availableChars.length === 0) {
    availableChars = LOWERCASE_CHARS + UPPERCASE_CHARS + NUMBER_CHARS;
  }

  // Generate the password
  for (let i = 0; i < options.length; i++) {
    password +=
      availableChars[Math.floor(Math.random() * availableChars.length)];
  }

  // Ensure at least one character from each selected type (for passwords >= 4 chars)
  if (options.length >= requiredChars.length && requiredChars.length > 0) {
    const passwordArray = password.split("");
    for (let i = 0; i < requiredChars.length; i++) {
      passwordArray[i] = requiredChars[i];
    }
    // Shuffle the password
    password = shuffleString(passwordArray.join(""));
  }

  return password;
};

export const calculatePasswordStrength = (
  password: string,
): PasswordStrength => {
  if (!password) return PasswordStrength.VeryWeak;

  let strength = 0;
  const length = password.length;

  // Length criteria
  if (length >= 8) strength++;
  if (length >= 12) strength++;
  if (length >= 16) strength++;

  // Character diversity
  if (/[a-z]/.test(password)) strength++;
  if (/[A-Z]/.test(password)) strength++;
  if (/[0-9]/.test(password)) strength++;
  if (/[^a-zA-Z0-9]/.test(password)) strength++;

  // Pattern detection (reduce strength for common patterns)
  if (/(.)\1{2,}/.test(password)) strength--; // Repeated characters
  if (/^[a-zA-Z]+$/.test(password)) strength--; // Only letters
  if (/^[0-9]+$/.test(password)) strength--; // Only numbers
  if (/^(123|abc|qwerty|password)/i.test(password)) strength -= 2; // Common patterns

  // Calculate entropy-based score
  const charsetSize = getCharsetSize(password);
  const entropy = length * Math.log2(charsetSize);

  if (entropy >= 60) strength++;
  if (entropy >= 80) strength++;

  // Normalize to our scale (0-5)
  const normalizedStrength = Math.max(0, Math.min(5, Math.floor(strength / 2)));

  return normalizedStrength as PasswordStrength;
};

export const getPasswordStrengthLabel = (
  strength: PasswordStrength,
): string => {
  const labels = {
    [PasswordStrength.VeryWeak]: "Very Weak",
    [PasswordStrength.Weak]: "Weak",
    [PasswordStrength.Fair]: "Fair",
    [PasswordStrength.Good]: "Good",
    [PasswordStrength.Strong]: "Strong",
    [PasswordStrength.VeryStrong]: "Very Strong",
  };
  return labels[strength];
};

export const estimateCrackTime = (password: string): string => {
  const charsetSize = getCharsetSize(password);
  const possibilities = Math.pow(charsetSize, password.length);
  const guessesPerSecond = 1e9; // 1 billion guesses per second

  const seconds = possibilities / (2 * guessesPerSecond);

  if (seconds < 1) return "Instantly";
  if (seconds < 60) return `${Math.floor(seconds)} seconds`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours`;
  if (seconds < 31536000) return `${Math.floor(seconds / 86400)} days`;
  if (seconds < 3153600000) return `${Math.floor(seconds / 31536000)} years`;

  return "Centuries";
};

// Helper functions
function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");
}

function shuffleString(str: string): string {
  const arr = str.split("");
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr.join("");
}

function getCharsetSize(password: string): number {
  let size = 0;
  if (/[a-z]/.test(password)) size += 26;
  if (/[A-Z]/.test(password)) size += 26;
  if (/[0-9]/.test(password)) size += 10;
  if (/[^a-zA-Z0-9]/.test(password)) size += 32;
  return size || 26; // Default to lowercase if no patterns match
}

export const generateMultiplePasswords = (
  options: PasswordOptions,
  count: number,
): string[] => {
  const passwords: string[] = [];
  for (let i = 0; i < count; i++) {
    passwords.push(generatePassword(options));
  }
  return passwords;
};

export const validatePasswordOptions = (options: PasswordOptions): boolean => {
  // At least one character type must be selected
  const hasCharType =
    options.includeUppercase === true ||
    options.includeLowercase === true ||
    options.includeNumbers === true ||
    options.includeSymbols === true ||
    (typeof options.customCharacters === "string" &&
      options.customCharacters.length > 0);

  // Length must be reasonable
  const validLength = options.length >= 4 && options.length <= 128;

  return hasCharType && validLength;
};
