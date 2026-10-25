export type Field = 'title' | 'assetCode' | 'description' | 'reportedBy'
export type Errors = Partial<Record<Field, string>>

const ASSET_PATTERN = /^[A-Z0-9-]+$/

export function validate(values: { title: string; assetCode: string; description: string; reportedBy: string }): Errors {
  const errors: Errors = {}
  const title = values.title.trim()
  const asset = values.assetCode.trim()
  const reporter = values.reportedBy.trim()
  if (title.length < 3 || title.length > 120) errors.title = 'Title must be 3 to 120 characters.'
  if (asset.length < 2 || asset.length > 40) errors.assetCode = 'Asset code must be 2 to 40 characters.'
  else if (!ASSET_PATTERN.test(asset)) errors.assetCode = 'Use only uppercase letters, digits and "-".'
  if (values.description.length > 1000) errors.description = 'Description must be at most 1000 characters.'
  if (reporter.length < 2 || reporter.length > 100) errors.reportedBy = 'Reporter must be 2 to 100 characters.'
  return errors
}
