<template>
  <div>
    <el-form :inline="true" class="filters">
      <el-form-item label="关键词">
        <el-input v-model="keyword" clearable placeholder="博主/地点/活动" style="width: 220px" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="statusFilter" clearable placeholder="全部" style="width: 140px">
          <el-option label="有日期" value="upcoming" />
          <el-option label="待定" value="pending" />
        </el-select>
      </el-form-item>
      <el-form-item label="开始">
        <el-date-picker v-model="dateFrom" type="date" value-format="YYYY-MM-DD" clearable />
      </el-form-item>
      <el-form-item label="结束">
        <el-date-picker v-model="dateTo" type="date" value-format="YYYY-MM-DD" clearable />
      </el-form-item>
    </el-form>

    <el-table :data="filteredItems" v-loading="loading" stripe>
      <el-table-column prop="trip_date" label="行程日期" width="130">
        <template #default="{ row }">
          <el-tag v-if="row.trip_date" type="warning">{{ row.trip_date }}</el-tag>
          <el-tag v-else type="info">待定</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="博主" width="170">
        <template #default="{ row }">
          <a class="user-link" :href="profileUrl(row)" target="_blank" rel="noopener noreferrer">
            {{ row.user_nickname }}
          </a>
        </template>
      </el-table-column>
      <el-table-column prop="user_douyin_id" label="抖音号" width="150">
        <template #default="{ row }">{{ row.user_douyin_id || '-' }}</template>
      </el-table-column>
      <el-table-column prop="location_activity" label="地点 / 活动" min-width="220" />
      <el-table-column label="来源简介" min-width="260">
        <template #default="{ row }">
          <div class="source-text">{{ row.raw_source_text }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'upcoming' ? 'success' : 'info'">
            {{ row.status === 'upcoming' ? '有日期' : '待定' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" @click="$emit('delete', row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})
defineEmits(['delete'])

const keyword = ref('')
const statusFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')

const filteredItems = computed(() => {
  let result = props.items
  if (statusFilter.value) {
    result = result.filter((item) => item.status === statusFilter.value)
  }
  if (keyword.value) {
    const k = keyword.value.toLowerCase()
    result = result.filter((item) =>
      [item.location_activity, item.user_nickname, item.user_douyin_id]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(k))
    )
  }
  if (dateFrom.value) {
    result = result.filter((item) => item.trip_date >= dateFrom.value)
  }
  if (dateTo.value) {
    result = result.filter((item) => item.trip_date <= dateTo.value)
  }
  return result
})

function profileUrl(row) {
  return row.user_sec_uid
    ? `https://www.douyin.com/user/${row.user_sec_uid}`
    : '#'
}
</script>

<style scoped>
.filters {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(0, 0, 0, 0.055);
}
.source-text {
  white-space: pre-wrap;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}
.user-link {
  color: #007aff;
  text-decoration: none;
  font-weight: 550;
}
.user-link:hover {
  text-decoration: underline;
}
:deep(.el-table) {
  --el-table-border-color: rgba(0, 0, 0, 0.055);
  --el-table-header-bg-color: rgba(247, 247, 250, 0.78);
  --el-table-row-hover-bg-color: rgba(0, 122, 255, 0.055);
  background: transparent;
  border-radius: 14px;
  overflow: hidden;
}
:deep(.el-table th.el-table__cell) {
  color: #5f5f66;
  font-weight: 650;
  letter-spacing: 0.01em;
}
:deep(.el-table .cell) {
  line-height: 1.45;
}
:deep(.el-tag) {
  border-radius: 8px;
  border: 0;
  font-weight: 600;
}
:deep(.el-input__wrapper),
:deep(.el-select__wrapper),
:deep(.el-date-editor.el-input__wrapper) {
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.08);
}
:deep(.el-button) {
  border-radius: 10px;
}
</style>
