import client from './client'

export async function fetchDeposits(params = {}) {
    const { data } = await client.get('/api/deposits', { params })
    return data
}

export async function searchDeposits(payload) {
    const { data } = await client.post('/api/deposits/search', payload)
    return data
}

export async function calculateDeposit(payload) {
    const { data } = await client.post('/api/deposits/calculate', payload)
    return data
}

export async function fetchDepositsStats() {
    const { data } = await client.get('/api/deposits/stats')
    return data
}

export async function fetchDepositVariantById(variantId) {
    const { data } = await client.get(`/api/deposits/${variantId}`)
    return data
}
export async function fetchCalculatorOptions(variantId) {
    const { data } = await client.get(`/api/deposits/${variantId}/calculator-options`)
    return data
}

export async function getDepositBanks() {
  const response = await client.get('/api/deposits/banks')
  return response.data
}