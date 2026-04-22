<template>
  <div class="realtime-monitor">
    <div class="monitor-container">
      <div class="top-panel">
        <div class="stat-item">
          <div class="stat-num">0</div>
          <div class="stat-label">异常设备</div>
        </div>
        <div class="stat-item">
          <div class="stat-num">{{ entryCount }}</div>
          <div class="stat-label">出入人数</div>
        </div>
        <div class="stat-item">
          <div class="stat-num">{{ cameras.length }}</div>
          <div class="stat-label">全部设备</div>
        </div>
      </div>
      <div class="monitor-log-title">全部设备</div>
      <div class="monitor-log"></div>
      <div class="middle-panel">
        <div class="video-list">
          <div 
            v-for="(camera, index) in cameras" 
            :key="index" 
            class="video"
            @click="openCamera(camera)"
          >
            <img src="../assets/play.png" class="play-icon" />
          </div>
        </div>
      </div>
    </div>

    <!-- 全屏显示摄像头画面 -->
    <div v-if="fullScreenCamera" class="fullscreen-modal" @click="closeCamera">
      <div class="fullscreen-content" @click.stop>
        <div class="fullscreen-header">
          <span>{{ fullScreenCamera.name }}</span>
          <button class="close-btn" @click="closeCamera">×</button>
        </div>
        <div class="fullscreen-video-placeholder">
          <!-- 真实的视频流显示区域 -->
          <img v-if="videoSrc" :src="videoSrc" class="realtime-video" />
          <div v-else class="placeholder-content">
            <img src="../assets/play.png" class="play-icon-large" />
            <p>等待视频流...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RealtimeMonitor',
  data() {
    return {
      cameras: [
        { id: 1, name: '摄像头 1', wsUrl: 'ws://localhost:8765/0' },
        { id: 2, name: '摄像头 2', wsUrl: 'ws://localhost:8765/1' },
        { id: 3, name: '摄像头 3', wsUrl: 'ws://localhost:8765/2' }
      ],
      fullScreenCamera: null,
      ws: null,
      videoSrc: '',
      entryCount: 0,
      recordsWs: null,
      reconnectTimer: null
    }
  },
  mounted() {
    this.connectRecordsWebSocket();
  },
  beforeDestroy() {
    this.destroyWebSocket();
    if (this.recordsWs) {
      this.recordsWs.close();
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
  },
  methods: {
    connectRecordsWebSocket() {
      if (this.recordsWs) {
        this.recordsWs.close();
      }

      this.recordsWs = new WebSocket('ws://localhost:8765/records');
      
      this.recordsWs.onopen = () => {
        console.log('Connected to records stream for monitor stats');
        
        // 获取当天记录总数
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const today = `${year}-${month}-${day}`;
        
        this.recordsWs.send(JSON.stringify({
          type: 'get_date_records',
          date: today
        }));
      };
      
      this.recordsWs.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          // 初始化加载当天的记录时更新数量
          if (message.type === 'new_record') {
            this.entryCount += 1;
          }
        } catch (e) {
          console.error('Error parsing record message:', e);
        }
      };
      
      this.recordsWs.onclose = () => {
        console.log('Records stream closed, reconnecting in 3s...');
        this.reconnectTimer = setTimeout(this.connectRecordsWebSocket, 3000);
      };

      this.recordsWs.onerror = (err) => {
        console.error('Records WebSocket error:', err);
        this.recordsWs.close();
      };
    },
    openCamera(camera) {
      console.log('Open camera:', camera.name)
      this.fullScreenCamera = camera
      this.initWebSocket(camera.wsUrl)
    },
    closeCamera() {
      this.fullScreenCamera = null
      this.destroyWebSocket()
      this.videoSrc = ''
    },
    initWebSocket(url) {
      this.destroyWebSocket(); // Ensure previous connection is closed
      console.log('Connecting to WebSocket:', url);
      try {
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
          console.log('WebSocket Connected');
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.image) {
              this.videoSrc = 'data:image/jpeg;base64,' + data.image;
            }
          } catch (e) {
            console.error('WebSocket Error parsing JSON:', e);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket Error:', error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket Closed');
        };
      } catch (e) {
        console.error('WebSocket Connection Failed:', e);
      }
    },
    destroyWebSocket() {
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
    }
  }
}
</script>

<style scoped>
.monitor-container {
  width: 100%;
  height: 810px;
  background: rgba(0,0,0,0.04);
  border-radius: 0px 0px 0px 0px;
  position: relative;
  overflow-x: hidden;
}

.top-panel {
  left: 50px;
  right: 50px;
  height: 140px;
  background: #FFFFFF;
  border-radius: 19px;
  position: absolute;
  top: 31px;
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.stat-num {
  font-family: 'Source Han Sans', sans-serif;
  font-weight: 900;
  font-size: 48px;
  color: #3D3D3D;
  line-height: 1;
}

.stat-label {
  font-family: 'Source Han Sans', sans-serif;
  font-weight: 700;
  font-size: 24px;
  color: #E8E3E3;
  letter-spacing: 3px;
}

.monitor-log-title {
  position: absolute;
  left: 50px;
  top: 192px;
  width: 156px;
  height: 73px;
  font-family: 'Source Han Sans', sans-serif;
  font-weight: 700;
  font-size: 36px;
  color: #3D3D3D;
  line-height: 52px;
  text-align: left;
  font-style: normal;
  text-transform: none;
}
.monitor-log {
  position: absolute;
  left: 50px;
  top: 250px;
  width: 30px;
  height: 15px;
  background: #045D8D;
  border-radius: 8px; 
}
.middle-panel {
  left: 50px;
  right: 50px;
  height: 448px;
  background: #FFFFFF;
  border-radius: 19px;
  position: absolute;
  top: 286px;
  display: flex;
  align-items: center;
  padding-left: 40px; /* 左边距作为第一个元素的起始偏移 */
  overflow-x: auto; /* 如果摄像头太多，支持横向滚动 */
}
.video-list {
  display: flex;
  gap: 40px; /* 框之间间隔10px */
}
.video {
  width: 539px;
  height: 284px;
  background: #867F7F;
  border-radius: 26px 26px 26px 26px;
  flex-shrink: 0; /* 防止宽度被压缩 */
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
}
.play-icon {
  opacity: 0.8;
}

/* 全屏模态框样式 */
.fullscreen-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.fullscreen-content {
  width: 1280px;
  height: 720px;
  background-color: #000;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.fullscreen-header {
  height: 60px;
  background-color: rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  color: #fff;
  font-size: 24px;
  font-family: 'Source Han Sans', sans-serif;
}

.close-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 36px;
  cursor: pointer;
}

.fullscreen-video-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #fff;
  font-size: 20px;
}

.realtime-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.play-icon-large {
  width: 200px;
  height: 200px;
  opacity: 0.8;
  margin-bottom: 20px;
}
</style>


