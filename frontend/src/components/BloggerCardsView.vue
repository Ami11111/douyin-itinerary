<template>
  <div v-loading="loading">
    <el-empty v-if="!users.length" description="暂无关注用户数据" />
    <div v-else class="card-grid">
      <el-card v-for="user in users" :key="user.id" class="user-card" shadow="hover">
        <div class="user-head">
          <a :href="profileUrl(user)" target="_blank" rel="noopener noreferrer">
            <el-avatar :size="52" :src="user.avatar_url">
              {{ user.nickname.slice(0, 1) }}
            </el-avatar>
          </a>
          <div>
            <a class="user-link" :href="profileUrl(user)" target="_blank" rel="noopener noreferrer">
              <div class="nickname">{{ user.nickname }}</div>
            </a>
            <div class="douyin-id">{{ user.douyin_id || user.douyin_user_id }}</div>
          </div>
          <el-tag class="count" type="info">{{ user.itinerary_count }} 条</el-tag>
        </div>
        <div class="bio">{{ user.bio || '暂无简介' }}</div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
defineProps({
  users: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

function profileUrl(user) {
  return user.douyin_user_id
    ? `https://www.douyin.com/user/${user.douyin_user_id}`
    : '#'
}
</script>

<style scoped>
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.user-head {
  display: flex;
  align-items: center;
  gap: 13px;
}
.nickname {
  font-weight: 680;
  font-size: 15px;
}
.user-link {
  color: #1d1d1f;
  text-decoration: none;
}
.user-link:hover {
  color: #007aff;
}
.douyin-id {
  color: #909399;
  font-size: 12px;
  margin-top: 2px;
}
.count {
  margin-left: auto;
}
.bio {
  margin-top: 14px;
  white-space: pre-wrap;
  color: #3a3a3c;
  font-size: 13px;
  line-height: 1.65;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
:deep(.el-card) {
  border-radius: 18px;
  border: 1px solid rgba(0, 0, 0, 0.065);
  background: rgba(255, 255, 255, 0.74);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.045);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
:deep(.el-card:hover) {
  transform: translateY(-2px);
  box-shadow: 0 16px 34px rgba(0, 0, 0, 0.07);
}
:deep(.el-tag) {
  border: 0;
  border-radius: 8px;
  font-weight: 600;
}
:deep(.el-avatar) {
  box-shadow: 0 5px 14px rgba(0, 0, 0, 0.12);
}
:deep(.el-empty) {
  padding: 48px 0;
}
</style>
