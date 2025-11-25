export function toPlayerSlug(name) {
  if (!name) return '';
  const cleaned = name
    .trim()
    .replace(/’/g, "'")                // normalize curly apostrophes
    .replace(/\s+/g, '_')              // spaces -> underscore
    .replace(/[^A-Za-z0-9_'._-]/g, '') // keep letters, digits, apostrophe, underscore, period, hyphen
    .replace(/__+/g, '_');             // collapse multiple underscores
  return encodeURIComponent(cleaned).replace(/'/g, '%27'); // ensure apostrophes encoded
}

export function displayFromSlug(slug) {
  if (!slug) return '';
  const decoded = decodeURIComponent(slug);
  return decoded.replace(/_/g, ' ');
}