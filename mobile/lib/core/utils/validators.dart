/// Shared validation utilities for form fields.
///
/// Use these validators across all screens to ensure consistent
/// validation rules and error messages.
class Validators {
  Validators._();

  /// Email validation regex pattern.
  static final _emailRegex = RegExp(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
  );

  /// Validates an email address.
  ///
  /// Returns null if valid, error message otherwise.
  static String? email(String? value) {
    if (value == null || value.isEmpty) {
      return 'Email is required';
    }
    if (!_emailRegex.hasMatch(value)) {
      return 'Please enter a valid email';
    }
    return null;
  }

  /// Validates a password for login (only checks if not empty).
  ///
  /// Returns null if valid, error message otherwise.
  static String? loginPassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    return null;
  }

  /// Validates a password for registration/reset (full validation).
  ///
  /// Requirements:
  /// - At least 8 characters
  /// - At least one letter
  /// - At least one digit
  ///
  /// Returns null if valid, error message otherwise.
  static String? password(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (!value.contains(RegExp(r'[a-zA-Z]'))) {
      return 'Password must contain at least one letter';
    }
    if (!value.contains(RegExp(r'[0-9]'))) {
      return 'Password must contain at least one digit';
    }
    return null;
  }

  /// Validates password confirmation.
  ///
  /// Returns null if passwords match, error message otherwise.
  static String? confirmPassword(String? value, String? password) {
    if (value == null || value.isEmpty) {
      return 'Please confirm your password';
    }
    if (value != password) {
      return 'Passwords do not match';
    }
    return null;
  }

  /// Validates a required field.
  ///
  /// Returns null if valid, error message otherwise.
  static String? required(String? value, [String fieldName = 'This field']) {
    if (value == null || value.isEmpty) {
      return '$fieldName is required';
    }
    return null;
  }

  /// Validates a project name.
  ///
  /// Returns null if valid, error message otherwise.
  static String? projectName(String? value) {
    if (value == null || value.isEmpty) {
      return 'Project name is required';
    }
    if (value.length < 2) {
      return 'Project name is too short';
    }
    if (value.length > 100) {
      return 'Project name is too long';
    }
    return null;
  }

  /// Validates a 6-digit verification code.
  ///
  /// Returns null if valid, error message otherwise.
  static String? verificationCode(String? value) {
    if (value == null || value.isEmpty) {
      return 'Code is required';
    }
    if (value.length != 6) {
      return 'Code must be 6 digits';
    }
    if (!RegExp(r'^[0-9]+$').hasMatch(value)) {
      return 'Code must contain only digits';
    }
    return null;
  }
}
