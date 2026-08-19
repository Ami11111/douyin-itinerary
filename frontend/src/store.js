import { defineStore } from 'pinia'
import { api } from './api'

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export const useStore = defineStore('main', {
  state: () => ({
    status: {
      logged_in: false,
      last_success_at: null,
      last_run_status: null,
      last_error: null,
      running: false
    },
    itineraries: [],
    following: [],
    loading: false,
    refreshing: false
  }),
  getters: {
    hasError: (state) => state.status.last_run_status === 'failed',
    lastSuccessText: (state) => state.status.last_success_at
  },
  actions: {
    async fetchStatus() {
      this.status = await api.getStatus()
      return this.status
    },
    async fetchData() {
      this.loading = true
      try {
        const [itineraries, following] = await Promise.all([
          api.getItineraries(),
          api.getFollowing()
        ])
        this.itineraries = itineraries
        this.following = following
      } finally {
        this.loading = false
      }
    },
    async scanLogin() {
      await api.login()
      await this.fetchStatus()
    },
    async manualRefresh() {
      this.refreshing = true
      try {
        await api.refresh()
        await this.fetchStatus()
        let attempts = 0
        while (this.status.running && attempts < 120) {
          await sleep(1000)
          await this.fetchStatus()
          attempts += 1
        }
        await this.fetchData()
      } finally {
        this.refreshing = false
      }
    },
    async deleteItinerary(id) {
      await api.deleteItinerary(id)
      await this.fetchData()
    }
  }
})
