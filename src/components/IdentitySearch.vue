<template>
  <div class="identity-search">
    <div class="enroll-container">
      <img v-if="videoSrc" :src="videoSrc" class="camera-stream" />
    </div>
    <div class="enroll-btn" @click="startRecognition">点击获取人像</div>
    <div class="log-container">
      <div class="photo-preview">
        <img v-if="capturedImage" :src="capturedImage" class="face-preview" />
      </div>
      <div class="photo-database">
        <img v-if="databaseImage" :src="databaseImage" class="face-preview" />
      </div>
      <div class="log-item log-name">姓名 {{ currentName }}</div>
      <div class="log-item log-id">证件号 {{ currentId }}</div>
      <div class="log-item log-address">地址 {{ currentAddress }}</div>
      <div class="enroll-database" @click="searchInDatabase">数据库查找</div>
    </div>

    <!-- 自定义弹出框 -->
    <div class="custom-dialog-overlay" v-if="showDialog">
      <div class="custom-dialog">
        <div class="dialog-icon" :class="dialogType">
          <span v-if="dialogType === 'success'">✓</span>
          <span v-else-if="dialogType === 'warning'">!</span>
          <span v-else>✕</span>
        </div>
        <div class="dialog-content">{{ dialogMessage }}</div>
        <div class="dialog-btn" @click="closeDialog">确定</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IdentitySearch',
  data() {
    return {
      ws: null,
      videoSrc: '',
      currentName: '',
      currentId: '',
      currentAddress: '',
      isRecognizing: false,
      capturedImage: '',
      searchImage: '',
      lastFaceImage: '',
      databaseImage: '',
      showDialog: false,
      dialogMessage: '',
      dialogType: 'success'
    }
  },
  beforeDestroy() {
    this.closeWebSocket()
  },
  methods: {
    showMessage(msg, type = 'success') {
      this.dialogMessage = msg;
      this.dialogType = type;
      this.showDialog = true;
    },
    closeDialog() {
      this.showDialog = false;
    },
    searchInDatabase() {
        const imageToSend = this.searchImage || this.capturedImage;
        if (!imageToSend) {
            this.showMessage("请先获取人像", "warning");
            return;
        }
        
        this.showMessage("正在查询数据库...", "success"); // Add a loading indicator

        // Connect to search endpoint
        const ws = new WebSocket('ws://localhost:8765/search');
        
        ws.onopen = () => {
            console.log('Connected to server for search...');
            ws.send(JSON.stringify({ image: imageToSend }));
        };
        
        ws.onmessage = (event) => {
            try {
                const response = JSON.parse(event.data);
                if (response.success) {
                    const result = response.data;
                    this.currentName = result.name;
                    this.currentId = result.number;
                    this.currentAddress = result.address;
                    if (result.image_base64) {
                        this.databaseImage = 'data:image/jpeg;base64,' + result.image_base64;
                    }
                    this.showMessage("查找成功", "success");
                } else {
                    this.showMessage("暂无该人脸信息", "warning");
                    // Clear previous results on failure?
                    this.currentName = '';
                    this.currentId = '';
                    this.currentAddress = '';
                    this.databaseImage = '';
                }
            } catch (e) {
                console.error("Error parsing search response:", e);
                this.showMessage("查找失败: 服务器响应错误", "error");
            }
            ws.close();
        };
        
        ws.onerror = (error) => {
            console.error('Search WebSocket error:', error);
            this.showMessage("连接服务器失败", "error");
        };
    },
    startRecognition() {
      if (this.isRecognizing) {
        // Stop recognition and capture image
        // We save the full video frame for the search API because the backend 
        // recognition model requires a large enough image to avoid "kernel size" errors.
        if (this.videoSrc) {
            this.searchImage = this.videoSrc; // Image sent to API
            // For UI preview, prefer the cropped face if available, else use full frame
            this.capturedImage = this.lastFaceImage ? this.lastFaceImage : this.videoSrc;
        } else if (this.lastFaceImage) {
            this.searchImage = this.lastFaceImage;
            this.capturedImage = this.lastFaceImage;
        }
        this.closeWebSocket();
        return;
      }
      
      this.initWebSocket()
    },
    initWebSocket() {
      this.closeWebSocket() // Close existing if any
      
      this.capturedImage = ''; // Clear previous capture
      this.searchImage = ''; // Clear previous search image
      this.lastFaceImage = ''; // Clear previous face
      
      // Assuming camera 0
      this.ws = new WebSocket('ws://localhost:8765/0?type=enroll')
      this.isRecognizing = true
      
      this.ws.onopen = () => {
        console.log('WebSocket Connected')
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.image) {
            this.videoSrc = 'data:image/jpeg;base64,' + data.image
          }
          if (data.face_image) {
            this.lastFaceImage = 'data:image/jpeg;base64,' + data.face_image
          }
          // Handle potential recognition data
          if (data.name) this.currentName = data.name
          if (data.number) this.currentId = data.number
          if (data.address) this.currentAddress = data.address
        } catch (e) {
          console.error('Error parsing WebSocket message:', e)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket Error:', error)
        this.isRecognizing = false
      }

      this.ws.onclose = () => {
        console.log('WebSocket Closed')
        this.isRecognizing = false
      }
    },
    closeWebSocket() {
      if (this.ws) {
        this.ws.close()
        this.ws = null
      }
      this.isRecognizing = false
    }
  }
}
</script>

<style scoped>
.enroll-container {
  width: 420px;
  height: 420px;
  background: #D8D8D8;
  position: fixed;
  left: 256px;
  top: 220px;
  border-radius: 50%;
  overflow: hidden; /* Ensure image stays within circle */
}
.camera-stream {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.enroll-btn {
  width: 624px;
  height: 75px;
  background: #65A0F4;
  border-radius: 11px 11px 11px 11px;
  position: absolute;
  left: 165px;
  top: 539px;
  font-family: 'Source Han Sans', 'Source Han Sans', sans-serif;
  font-weight: 500;
  font-size: 44px;
  color: #FCF6F6;
  line-height: 75px; /* 让文字垂直居中 */
  letter-spacing: 3px;
  text-align: center; /* 让文字水平居中 */
  font-style: normal;
  text-transform: none;
  cursor: pointer;
}
.enroll-database {
  width: 254px;
  height: 75px;
  background: #8d8e8f;
  border-radius: 11px 11px 11px 11px;
  position: absolute;
  left: 180px;
  top: 559px;
  font-family: 'Source Han Sans', 'Source Han Sans', sans-serif;
  font-weight: 500;
  font-size: 35px;
  color: #FCF6F6;
  line-height: 75px; /* 让文字垂直居中 */
  letter-spacing: 3px;
  text-align: center; /* 让文字水平居中 */
  font-style: normal;
  text-transform: none;
  cursor: pointer;
}
.log-container {
  position: fixed;
  left: 1100px;
  top: 230px;
  width: 601px;
  height: 658px;
  border-radius: 37px;
  opacity: 1;
  background: rgba(0, 0, 0, 0.0392);
}
.photo-preview {
  position: absolute;
  left: 59px;
  top: 62px;
  width: 234px;
  height: 279px;
  opacity: 1;
  background: #FFFFFF;

  overflow: hidden;
}
.photo-database {
  position: absolute;
  left: 319px;
  top: 62px;
  width: 234px;
  height: 279px;
  opacity: 1;
  background: #FFFFFF;
  overflow: hidden;
}


.face-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.log-item {
  position: absolute;
  left: 129px;
  font-family: 'Source Han Serif CN', sans-serif;
  font-size: 24px;
  font-weight: bold;
  line-height: 100.83%;
  letter-spacing: 0.1em;
  font-variation-settings: "opsz" auto;
  font-feature-settings: "kern" on;
  color: #3D3D3D;
  opacity: 1;
}

.log-name {
  top: 384px;
  width: 114px;
  height: 40px;
  white-space: nowrap;
}

.log-id {
  top: 442px;
  width: 234px;
  height: 39px;
  white-space: nowrap;
}

.log-address {
  top: 499px;
  width: 234px;
  height: 40px;
  white-space: nowrap;
}

/* 弹出框样式 */
.custom-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.custom-dialog {
  width: 400px;
  background: #FFFFFF;
  border-radius: 20px;
  padding: 40px 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  animation: dialogFadeIn 0.3s ease;
}

@keyframes dialogFadeIn {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

.dialog-icon {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 40px;
  color: white;
  margin-bottom: 25px;
  font-weight: bold;
}

.dialog-icon.success {
  background: #67C23A;
}

.dialog-icon.warning {
  background: #E6A23C;
}

.dialog-icon.error {
  background: #F56C6C;
}

.dialog-content {
  font-family: 'Source Han Sans', sans-serif;
  font-size: 22px;
  color: #3D3D3D;
  text-align: center;
  margin-bottom: 35px;
  line-height: 1.5;
}

.dialog-btn {
  width: 200px;
  height: 50px;
  background: #65A0F4;
  border-radius: 25px;
  color: #FFFFFF;
  font-size: 22px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  font-family: 'Source Han Sans', sans-serif;
  transition: background 0.2s;
}

.dialog-btn:hover {
  background: #508AE0;
}

</style>
