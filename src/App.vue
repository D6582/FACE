<template>
  <div id="app">
    <div class="nav-bar">
      <div
        class="nav-title nav-title1"
        :class="{ active: currentTab === 'FaceEnroll' }"
        @click="currentTab = 'FaceEnroll'"
      >
        人脸录入
      </div>
      <div
        class="nav-title nav-title2"
        :class="{ active: currentTab === 'RealtimeMonitor' }"
        @click="currentTab = 'RealtimeMonitor'"
      >
        实时监控
      </div>
      <div
        class="nav-title nav-title3"
        :class="{ active: currentTab === 'IdentitySearch' }"
        @click="currentTab = 'IdentitySearch'"
      >
        身份查找
      </div>
      <div
        class="nav-title nav-title4"
        :class="{ active: currentTab === 'RealtimeRecord' }"
        @click="currentTab = 'RealtimeRecord'"
      >
        实时记录
      </div>
      <img class="logo-face" src="./assets/face scanning.gif" alt="face" />
    </div>

    <div class="content">
      <FaceEnroll v-if="currentTab === 'FaceEnroll'" />
      <RealtimeMonitor v-else-if="currentTab === 'RealtimeMonitor'" />
      <IdentitySearch v-else-if="currentTab === 'IdentitySearch'" />
      <RealtimeRecord v-else-if="currentTab === 'RealtimeRecord'" />
    </div>

    <div class="footer-system">
      <div class="system-title">智能监控系统</div>
    </div>
  </div>
</template>

<script>
import FaceEnroll from './components/FaceEnroll.vue'
import RealtimeMonitor from './components/RealtimeMonitor.vue'
import IdentitySearch from './components/IdentitySearch.vue'
import RealtimeRecord from './components/RealtimeRecord.vue'

export default {
  name: 'App',
  components: {
    FaceEnroll,
    RealtimeMonitor,
    IdentitySearch,
    RealtimeRecord
  },
  data () {
    return {
      currentTab: 'FaceEnroll'
    }
  }
}
</script>

<style>
#app {
  width: 1920px;
  height: 1080px;
  margin: 0 auto;
  position: relative;
}
html, body {
  margin: 0;
  padding: 0;
  width: 1920px;
  height: 1080px;
  overflow: hidden;
}
.nav-bar {
  width: 1920px;
  height: 187px;
  border-radius: 0;
  position: absolute;
  top: 0;
  left: 0;
}

.nav-title {
  width: 200px;
  height: 60px;
  font-family: 'YouSheBiaoTiHei', sans-serif;
  font-weight: 400;
  font-size: 48px;
  color: #3D3D3D;
  line-height: 67px;
  text-align: left;
  font-style: normal;
  text-transform: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  
}

.nav-title.active {
  width: 250px;
  height: 84px;
  background: #65A0F4;
  border-radius: 45px;
  color: #F9F3F3;
  transform: translateX(-60px);
  justify-content: center;
}

.nav-title1 {
  position: absolute;
  left: 159px;
  top: 39px;
}
.nav-title2 {
  position: absolute;
  left: 510px;
  top: 39px;
}
.nav-title3 {
  position: absolute;
  left: 1268px;
  top: 39px;
}
.nav-title4 {
  position: absolute;
  left: 1595px;
  top: 39px;
}

.content {
  position: absolute;
  top: 187px;
  left: 0;
  width: 1920px;
  height: calc(1080px - 187px);
}

.logo-face {
  position: absolute;
  left: 870px;
  top: 10px;
  width: 145px;
  height: 150px;
}

.footer-system {
  width: 1920px;
  height: 115px;
  background: #045D8D;
  border-radius: 0px 0px 0px 0px;
  position: fixed;
  bottom: 0;
  left: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.system-title {
  width: 415px;
  height: 85px;
  font-family: 'YouSheBiaoTiHei', sans-serif;
  font-weight: 400;
  font-size: 72px;
  color: #F9F3F3;
  line-height: 101px;
  text-align: left;
  font-style: normal;
  text-transform: none;
}
</style>
