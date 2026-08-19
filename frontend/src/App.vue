<template>
  <div class="app-shell" :class="{ 'sidebar-collapsed': collapsed }">
    <aside class="sidebar">
      <button class="collapse-button" @click="collapsed = !collapsed">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M15 6l-6 6 6 6" />
        </svg>
        <span v-if="!collapsed">收起侧栏</span>
      </button>

      <nav class="sidebar-nav">
        <a
          class="sidebar-link"
          :class="{ active: activeTab === 'table' }"
          href="#section-table"
          @click.prevent="activeTab = 'table'"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <rect x="4" y="5" width="16" height="16" rx="4" />
            <path d="M8 3v4M16 3v4M4 10h16" />
          </svg>
          <span v-if="!collapsed">日期总表</span>
        </a>
        <a
          class="sidebar-link"
          :class="{ active: activeTab === 'cards' }"
          href="#section-cards"
          @click.prevent="activeTab = 'cards'"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="8" r="3.2" />
            <path d="M5 19c.7-3.4 3.2-5 7-5s6.3 1.6 7 5" />
          </svg>
          <span v-if="!collapsed">博主卡片</span>
        </a>
      </nav>

      <div class="sidebar-spacer"></div>

      <div class="sidebar-status-card">
        <div class="status-row">
          <span class="status-dot" :class="{ online: store.status.logged_in }"></span>
          <span v-if="!collapsed">{{ store.status.logged_in ? '抖音已登录' : '抖音未登录' }}</span>
        </div>
        <div v-if="!collapsed && store.lastSuccessText" class="status-meta">
          上次成功：{{ formatTime(store.lastSuccessText) }}
        </div>
      </div>
    </aside>

    <main class="main-content">
      <div class="toolbar">
        <div class="toolbar-actions">
          <el-button class="swift-button" text @click="onLogin">扫码登录</el-button>
          <el-button
            class="swift-button primary"
            :loading="store.refreshing"
            @click="onRefresh"
          >
            手动刷新
          </el-button>
        </div>
      </div>

      <el-alert
        v-if="store.hasError"
        class="swift-alert"
        type="error"
        :closable="false"
        show-icon
        :title="'最近一次采集失败：' + (store.status.last_error || '未知错误')"
      />
      <el-alert
        v-if="!store.status.logged_in"
        class="swift-alert"
        type="warning"
        :closable="false"
        show-icon
        title="请先点击“扫码登录”，在打开的浏览器中登录抖音"
      />

      <section id="section-content" class="section-card">
        <div class="section-heading">
          <div>
            <h2>{{ activeTab === 'table' ? '日期总表' : '博主卡片' }}</h2>
            <p>
              {{
                activeTab === 'table'
                  ? '按日期查看已识别的博主行程'
                  : '按博主浏览简介与行程概况'
              }}
            </p>
          </div>
        </div>
        <DateTableView
          v-if="activeTab === 'table'"
          :items="store.itineraries"
          :loading="store.loading"
          @delete="onDelete"
        />
        <BloggerCardsView
          v-else
          :users="store.following"
          :loading="store.loading"
        />
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useStore } from './store'
import DateTableView from './components/DateTableView.vue'
import BloggerCardsView from './components/BloggerCardsView.vue'

const store = useStore()
const collapsed = ref(false)
const activeTab = ref('table')

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

async function onLogin() {
  await store.scanLogin()
}

async function onRefresh() {
  await store.manualRefresh()
}

async function onDelete(id) {
  await store.deleteItinerary(id)
}

onMounted(async () => {
  await Promise.all([store.fetchStatus(), store.fetchData()])
})
</script>

<style>
:root {
  --mac-bg: #f5f5f7;
  --mac-panel: rgba(255, 255, 255, 0.82);
  --mac-panel-solid: #ffffff;
  --mac-border: rgba(0, 0, 0, 0.08);
  --mac-text: #1d1d1f;
  --mac-secondary: #6e6e73;
  --mac-blue: #0a84ff;
  --mac-blue-soft: rgba(10, 132, 255, 0.14);
  --mac-shadow: 0 18px 44px rgba(0, 0, 0, 0.08), 0 3px 10px rgba(0, 0, 0, 0.05);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background:
    radial-gradient(circle at 20% 0%, rgba(255, 255, 255, 0.88), transparent 32%),
    linear-gradient(145deg, #eef1f6 0%, #f7f7fa 45%, #eef2f7 100%);
  min-height: 100vh;
  color: var(--mac-text);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text',
    'Helvetica Neue', 'PingFang SC', sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

.app-shell {
  min-height: 100vh;
  display: flex;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: 238px;
  flex: 0 0 238px;
  padding: 20px 14px;
  background: rgba(242, 243, 247, 0.72);
  border-right: 1px solid rgba(0, 0, 0, 0.07);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease, flex-basis 0.2s ease;
}

.sidebar-collapsed .sidebar {
  width: 76px;
  flex-basis: 76px;
}

.collapse-button,
.sidebar-link {
  border: 0;
  background: transparent;
  color: var(--mac-text);
  cursor: pointer;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 11px;
  width: 100%;
  border-radius: 12px;
  font: inherit;
  font-size: 14px;
  font-weight: 550;
  text-align: left;
}

.collapse-button {
  height: 42px;
  padding: 0 12px;
  margin-bottom: 18px;
}

.collapse-button:hover,
.sidebar-link:hover {
  background: rgba(0, 0, 0, 0.055);
}

.sidebar-link.active {
  color: var(--mac-blue);
  background: var(--mac-blue-soft);
  font-weight: 650;
}

.collapse-button svg,
.sidebar-link svg {
  width: 19px;
  height: 19px;
  flex: 0 0 19px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.sidebar-link {
  height: 42px;
  padding: 0 12px;
}

.sidebar-spacer {
  flex: 1;
}

.sidebar-status-card {
  padding: 13px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 550;
  white-space: nowrap;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #b0b0b5;
  flex: 0 0 8px;
}

.status-dot.online {
  background: #34c759;
  box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.13);
}

.status-meta {
  margin-top: 5px;
  color: var(--mac-secondary);
  font-size: 11px;
  line-height: 1.4;
}

.main-content {
  flex: 1;
  min-width: 0;
  padding: 28px 32px 48px;
  overflow: auto;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 18px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.section-card {
  border-radius: 20px;
  background: var(--mac-panel);
  border: 1px solid var(--mac-border);
  box-shadow: var(--mac-shadow);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  padding: 22px;
  margin-bottom: 22px;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 18px;
}

.section-heading h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.section-heading p {
  margin: 6px 0 0;
  color: var(--mac-secondary);
  font-size: 13px;
}

.swift-button.el-button {
  height: 34px;
  border-radius: 11px;
  border: 0;
  background: rgba(255, 255, 255, 0.76);
  color: #1d1d1f;
  font-weight: 550;
  padding: 0 15px;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.08);
}

.swift-button.el-button.primary {
  background: linear-gradient(180deg, #2e9aff, #007aff);
  color: #fff;
  box-shadow: 0 7px 16px rgba(0, 122, 255, 0.22);
}

.swift-button.el-button:hover {
  filter: brightness(0.97);
}

.swift-alert {
  margin-bottom: 14px;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.72);
}

@media (max-width: 760px) {
  .sidebar {
    display: none;
  }
  .main-content {
    padding: 20px 14px 40px;
  }
}
</style>
