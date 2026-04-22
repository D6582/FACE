<template>
  <div class="realtime-monitor">
    <div class="monitor-container">
      <div class="top-panel">
        <div class="all-default">0</div>
        <div class="all-default-word">异常设备</div>
        <div class="all-people">0</div>
        <div class="all-people-word">出入人数</div>
        <div class="all-number">0</div>
        <div class="all-number-word">全部设备</div>
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
          <video v-if="localStream" ref="localVideo" autoplay playsinline class="realtime-video"></video>
          <img v-else-if="videoSrc" :src="videoSrc" class="realtime-video" />
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
      localStream: null
    }
  },
  beforeDestroy() {
    this.destroyWebSocket();
    this.destroyLocalCamera();
  },
  methods: {
    openCamera(camera) {
      console.log('Open camera:', camera.name)
      this.fullScreenCamera = camera
      if (camera.id === 1) {
        this.initLocalCamera()
      } else {
        this.initWebSocket(camera.wsUrl)
      }
    },
    closeCamera() {
      this.fullScreenCamera = null
      if (this.localStream) {
        this.destroyLocalCamera()
      } else {
        this.destroyWebSocket()
      }
      this.videoSrc = ''
    },
    async initLocalCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        this.localStream = stream;
        this.$nextTick(() => {
          if (this.$refs.localVideo) {
            this.$refs.localVideo.srcObject = stream;
          }
        });
      } catch (err) {
        console.error('Error accessing local camera:', err);
      }
    },
    destroyLocalCamera() {
      if (this.localStream) {
        this.localStream.getTracks().forEach(track => track.stop());
        this.localStream = null;
      }
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
  width: 1920px;
  height: 810px;
  background: rgba(0,0,0,0.04);
  border-radius: 0px 0px 0px 0px;
}

.top-panel {
  width: 1780px;
  height: 140px;
  background: #FFFFFF;
  border-radius: 19px 19px 19px 19px;
  position: absolute;
  left: 89px;
  top: 31px;
}

.all-default {
  position: absolute;
  left: 164px;
  top: 22px;
  width: 32px;
  height: 72px;
  font-family: 'Source Han Sans', sans-serif;
  font-weight: 900;
  font-size: 48px;
  color: #3D3D3D;
  line-height: 70px;
  text-align: left;
  font-style: normal;
  text-transform: none;
}
.all-people {
  position: absolute;
  left: 885px;
  top: 22px;
  width: 32px;
  height: 72px;
  font-family: 'Source Han Sans', sans-serif;
  font-weight: 900;
  font-size: 48px;
  color: #3D3D3D;
  line-height: 70px;
  text-align: left;
  font-style: normal;
  text-transform: none;
}
.all-number {
  position: absolute;
  left: 1542px;
  top: 22px;
  width: 32px;
  height: 72px;
  font-family: 'Source Han Sans', sans-serif;
  font-weight: 900;
  font-size: 48px;
  color: #3D3D3D;
  line-height: 70px;
  text-align: left;
  font-style: normal;
  text-transform: none;
}
.all-default-word{
  position: absolute;
  left: 128px;
  top: 94px;
  width: 127px;
  height: 25px;
  font-family: Source Han Sans, Source Han Sans;
  font-weight: 700;
  font-size: 24px;
  color: #E8E3E3;
  line-height: 24px;
  letter-spacing: 3px;
  text-align: left;
  font-style: normal;
  text-transform: none;
}
.all-people-word{
  position: absolute;
  left: 848px;
  top: 94px;
  width: 127px;
  height: 25px;
  font-family: Source Han Sans, Source Han Sans;
  font-weight: 700;
  font-size: 24px;
  color: #E8E3E3;
  line-height: 24px;
  letter-spacing: 3px;
  text-align: left;
  font-style: normal;
  text-transform: none;
}
.all-number-word{
  position: absolute;
  left: 1505px;
  top: 94px;
  width: 127px;
  height: 25px;
  font-family: Source Han Sans, Source Han Sans;
  font-weight: 700;
  font-size: 24px;
  color: #E8E3E3;
  line-height: 24px;
  letter-spacing: 3px;
  text-align: left;
  font-style: normal;
  text-transform: none;
}

.monitor-log-title {
  position: absolute;
  left: 93px;
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
  left: 93px;
  top: 250px;
  width: 30px;
  height: 15px;
  background: #045D8D;
  border-radius: 8px; 
}
.middle-panel {
  width: 1780px;
  height: 448px;
  background: #FFFFFF;
  border-radius: 19px 19px 19px 19px;
  position: absolute;
  left: 89px;
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
  width: 90%;
  height: 90%;
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


