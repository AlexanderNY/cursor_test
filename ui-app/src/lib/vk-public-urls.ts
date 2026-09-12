/** Origin сайта из поля «публичный URL gateway» (часто https://host/api). */
export function buildVkSiteOrigin(publicGatewayUrl: string): string {
  let base = publicGatewayUrl.trim().replace(/\/+$/, '')
  if (!base) return ''
  if (base.endsWith('/vk/oauth/callback')) {
    return base.slice(0, -'/vk/oauth/callback'.length).replace(/\/+$/, '')
  }
  if (base.endsWith('/vk/callback')) {
    return base.slice(0, -'/vk/callback'.length).replace(/\/+$/, '')
  }
  if (base.endsWith('/api')) {
    return base.slice(0, -'/api'.length).replace(/\/+$/, '')
  }
  return base
}

export function buildVkOAuthRedirectUri(publicGatewayUrl: string): string {
  const raw = publicGatewayUrl.trim().replace(/\/+$/, '')
  if (!raw) return ''
  if (raw.endsWith('/vk/oauth/callback')) return raw
  const origin = buildVkSiteOrigin(raw)
  return origin ? `${origin}/vk/oauth/callback` : ''
}

export function buildVkCallbackApiUrl(publicGatewayUrl: string): string {
  const raw = publicGatewayUrl.trim().replace(/\/+$/, '')
  if (!raw) return ''
  if (raw.endsWith('/vk/callback')) return raw
  const origin = buildVkSiteOrigin(raw)
  return origin ? `${origin}/vk/callback` : ''
}
