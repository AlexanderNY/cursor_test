export const MAX_IMAGE_BYTES = 8 * 1024 * 1024
export const MAX_IMPORT_BYTES = 1 * 1024 * 1024
export const MAX_CSV_ROWS = 500

export function fileTooLargeMessage(maxBytes: number): string {
  const mb = maxBytes / (1024 * 1024)
  return `Файл больше ${mb} МБ`
}

export function isFileWithinLimit(file: File, maxBytes: number): boolean {
  return file.size <= maxBytes
}
