import { translate } from '../shared/i18n'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function clean(value: string): string {
  return value.trim()
}

export function validateEmail(value: string): string | null {
  const input = clean(value)
  if (!input) return translate('errors.validation.emailRequired')
  if (!EMAIL_RE.test(input)) return translate('errors.validation.emailInvalid')
  return null
}

export function validatePassword(value: string): string | null {
  if (!value) return translate('errors.validation.passwordRequired')
  if (value.length < 8) return translate('errors.validation.passwordShort')
  if (value.length > 128) return translate('errors.validation.passwordLong')
  return null
}

export function validateFullName(value: string): string | null {
  const input = clean(value)
  if (!input) return null
  if (input.length < 2) return translate('errors.validation.fullNameShort')
  if (input.length > 120) return translate('errors.validation.fullNameLong')
  return null
}

export function validateQuery(value: string): string | null {
  const input = clean(value)
  if (!input) return translate('errors.validation.queryRequired')
  if (input.length < 2) return translate('errors.validation.queryShort')
  if (input.length > 120) return translate('errors.validation.queryLong')
  return null
}

export function validatePages(value: number): string | null {
  if (!Number.isInteger(value)) return translate('errors.validation.pagesInteger')
  if (value < 1 || value > 20) return translate('errors.validation.pagesRange')
  return null
}

export function validateLimit(value: number): string | null {
  if (!Number.isInteger(value)) return translate('errors.validation.limitInteger')
  if (value < 1 || value > 500) return translate('errors.validation.limitRange')
  return null
}

export function validateOptionalText(value: string, maxLength: number, label: string): string | null {
  const input = clean(value)
  if (!input) return null
  if (input.length > maxLength) {
    return translate('errors.validation.optionalMax', { label, max: maxLength })
  }
  return null
}
