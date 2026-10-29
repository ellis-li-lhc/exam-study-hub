import { latestReferenceScore } from './institutionQuality.js'

export function verifiedReferenceScore(institution, majorName) {
  if (institution?.source?.confidence !== 'verified') return null
  const score = latestReferenceScore(institution, majorName)?.score
  return Number.isFinite(Number(score)) && score != null ? Number(score) : null
}
