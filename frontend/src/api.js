import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 15000
})

export const api = {
  getStatus: () => http.get('/douyin/status').then((res) => res.data),
  login: () => http.post('/douyin/login').then((res) => res.data),
  refresh: () => http.post('/refresh').then((res) => res.data),
  getItineraries: (params = {}) =>
    http.get('/itineraries', { params }).then((res) => res.data),
  getFollowing: () => http.get('/following').then((res) => res.data),
  deleteItinerary: (id) => http.delete(`/itineraries/${id}`).then((res) => res.data)
}
