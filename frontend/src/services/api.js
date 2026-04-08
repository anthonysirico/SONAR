const BASE_URL = 'http://localhost:8000/api'

export const fetchFullGraph = async () => {
  const res = await fetch(`${BASE_URL}/graph/`)
  return res.json()
}

export const fetchTopNodes = async (limit = 20) => {
  const res = await fetch(`${BASE_URL}/graph/top?limit=${limit}`)
  return res.json()
}

export const fetchNodeDetail = async (nodeId) => {
  const res = await fetch(`${BASE_URL}/graph/${nodeId}`)
  return res.json()
}

export const computeProminence = async () => {
  const res = await fetch(`${BASE_URL}/graph/prominence/compute`, {
    method: 'POST'
  })
  return res.json()
}