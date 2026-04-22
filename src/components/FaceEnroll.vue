<template>
  <div class="face-enroll">
    <div class="enroll-container">
      <img v-if="cameraImage" :src="cameraImage" class="camera-stream" />
    </div>
    <div class="main-container">
      <img src="../assets/checkbox.png" class="check-img" />
      <img src="../assets/close-circle.png" class="close-img" />
      <img src="../assets/people.png" class="people-img" />
      <img src="../assets/people2.png" class="people2-img" />
      <img src="../assets/map.png" class="people3-img" />
      <img src="../assets/glass.png" class="people4-img" />
      <img src="../assets/word@1x.png" class="word-img" />
      <div class="enroll-btn" @click="handleEnrollClick">{{ isCapturing ? '完成采集' : '采集人脸' }}</div>
      <div class="upload-btn" @click="triggerUpload">上传照片</div>
      <input type="file" ref="fileInput" @change="handleFileUpload" style="display: none" accept="image/*">
      <div class="correct-demo-text">正确示范</div>
      <div class="uncorrect-demo-text">错误示范</div>
      <div class="mask-demo-text">佩戴口罩</div>    
      <div class="map-demo-text">佩戴帽子</div>
      <div class="glass-demo-text">佩戴眼镜</div>
    </div>
    <div class="log-container">
      <div class="photo-preview">
        <img v-if="capturedFace" :src="capturedFace" class="face-preview-img" />
      </div>
      
      <div class="log-item log-name">姓名</div>
      <input type="text" class="log-input input-name" placeholder="请输入姓名" v-model="name" />
      
      <div class="log-item log-id">证件号</div>
      <input type="text" class="log-input input-id" placeholder="请输入证件号" v-model="id" />
      
      <div class="log-item log-address">地址</div>
      <input type="text" class="log-input input-address" placeholder="请输入地址" v-model="address" />
      
      <div class="save-btn" @click="saveUserInfo">保存</div>
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
  name: 'FaceEnroll',
  data() {
    return {
      cameraImage: null,
      fps: null,
      websocket: null,
      reconnectInterval: null,
      isCapturing: false,
      currentFace: null, // 实时流中当前的人脸
      capturedFace: null, // 截图保存的人脸
      name: '',
      id: '',
      address: '',
      showDialog: false,
      dialogMessage: '',
      dialogType: 'success'
    }
  },
  mounted() {
    // 移除自动连接
    // this.initWebSocket();
  },
  beforeDestroy() {
    this.closeWebSocket();
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
    triggerUpload() {
      this.$refs.fileInput.click();
    },
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;
      
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64Image = e.target.result;
        this.extractFace(base64Image);
      };
      reader.readAsDataURL(file);
      
      // clear input
      event.target.value = '';
    },
    extractFace(base64Image) {
      const ws = new WebSocket('ws://localhost:8765/extract_face');
      
      ws.onopen = () => {
        ws.send(JSON.stringify({ image: base64Image }));
      };
      
      ws.onmessage = (event) => {
        try {
          const response = JSON.parse(event.data);
          if (response.success) {
            this.capturedFace = 'data:image/jpeg;base64,' + response.face_image;
            this.showMessage("照片人脸截取成功！", "success");
            // 如果正在使用摄像头，则关闭摄像头
            if (this.isCapturing) {
              this.isCapturing = false;
              this.closeWebSocket();
            }
          } else {
            this.showMessage(response.message || "截取失败", "error");
          }
        } catch (e) {
          console.error("Error parsing extract response:", e);
          this.showMessage("截取失败: 服务器响应错误", "error");
        }
        ws.close();
      };
      
      ws.onerror = (error) => {
        console.error('Extract WebSocket error:', error);
        this.showMessage("连接服务器失败，无法截取照片", "error");
      };
    },
    handleEnrollClick() {
      if (this.isCapturing) {
        // 如果正在采集，点击则表示完成采集（截图）
        this.stopCaptureAndSave();
      } else {
        // 如果未采集，点击则开始采集
        this.startCapture();
      }
    },
    startCapture() {
      if (this.isCapturing) return;
      this.isCapturing = true;
      this.currentFace = null;
      this.capturedFace = null; // 清除之前的截图
      this.initWebSocket();
    },
    stopCaptureAndSave() {
      // 保存当前检测到的人脸
      if (this.currentFace) {
        this.capturedFace = this.currentFace;
        this.isCapturing = false;
        this.closeWebSocket();
        this.showMessage("人脸采集成功！", "success");
      } else {
        this.showMessage("未检测到人脸，请确保人脸在框内", "warning");
      }
    },
    initWebSocket() {
      if (this.websocket) {
          this.closeWebSocket();
      }
      
      this.websocket = new WebSocket('ws://localhost:8765/0?type=enroll');

      this.websocket.onopen = () => {
        console.log('WebSocket connected');
      };

      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.image) {
            this.cameraImage = 'data:image/jpeg;base64,' + data.image;
          }
          if (data.fps !== undefined) {
            this.fps = data.fps;
          }
          if (data.face_image) {
            this.currentFace = 'data:image/jpeg;base64,' + data.face_image;
          } else {
            this.currentFace = null;
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      this.websocket.onclose = () => {
        console.log('WebSocket disconnected.');
        if (this.isCapturing) {
             console.log('Reconnecting...');
             if (this.reconnectInterval) clearTimeout(this.reconnectInterval);
             this.reconnectInterval = setTimeout(() => {
                this.initWebSocket();
             }, 3000);
        }
      };

      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    },
    closeWebSocket() {
      this.isCapturing = false;
      if (this.websocket) {
        this.websocket.close();
        this.websocket = null;
      }
      if (this.reconnectInterval) {
        clearTimeout(this.reconnectInterval);
        this.reconnectInterval = null;
      }
      this.cameraImage = null;
      this.fps = null;
      // 注意：不要在这里清除 capturedFace，否则截图会消失
    },
    saveUserInfo() {
      if (!this.capturedFace) {
        this.showMessage("请先采集人脸", "warning");
        return;
      }
      if (!this.name || !this.id) {
        this.showMessage("请填写姓名和证件号", "warning");
        return;
      }
      
      const userInfo = {
        name: this.name,
        number: this.id, // 对应数据库字段 number
        address: this.address,
        image: this.capturedFace
      };
      
      console.log("Saving user info:", userInfo);
      
      // 创建一个新的 WebSocket 连接用于发送数据
      const ws = new WebSocket('ws://localhost:8765/save');
      
      ws.onopen = () => {
        console.log('Connected to server for saving...');
        ws.send(JSON.stringify(userInfo));
      };
      
      ws.onmessage = (event) => {
        try {
            const response = JSON.parse(event.data);
            if (response.success) {
                this.showMessage("保存成功!", "success");
                // 重置表单
                this.name = '';
                this.id = '';
                this.address = '';
                this.capturedFace = null;
                this.currentFace = null;
            } else {
                this.showMessage("保存失败: " + response.message, "error");
            }
        } catch (e) {
            console.error("Error parsing save response:", e);
            this.showMessage("保存失败: 服务器响应错误", "error");
        }
        ws.close();
      };
      
      ws.onerror = (error) => {
        console.error('Save WebSocket error:', error);
        this.showMessage("连接服务器失败，无法保存", "error");
      };
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
  left: 56px;
  top: 330px;
  border-radius: 50%;
  overflow: hidden; /* 确保图片不溢出圆框 */
}

.camera-stream {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 保持比例填充 */
}

.fps-display {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  padding: 5px 10px;
  border-radius: 5px;
  font-size: 14px;
  font-family: 'Source Han Sans', sans-serif;
  z-index: 10;
}

.main-container {
  width: 740px;
  height: 650px;
  border-radius: 20px 20px 20px 20px;
  border: 1px solid rgba(0,0,0,0.13);
  position: fixed;
  left: 542px;
  top: 253px;
}

.people-img {
  position: absolute;
  left: 71px;
  top: 88px;
}
.people2-img {
  position: absolute;
  left: 133px;
  top: 375px;
}
.people3-img {
  position: absolute;
  left: 331px;
  top: 386px;
}
.people4-img {
  position: absolute;
  left: 539px;
  top: 386px;
}
.word-img {
  position: absolute;
  left: 280px;
  top: 92px;
}
.check-img {
  position: absolute;
  left: 58px;
  top: 28px;
}
.close-img {
  position: absolute;
  left: 58px;
  top: 325px;
}
.enroll-btn {
  width: 300px;
  height: 75px;
  background: #65A0F4;
  border-radius: 11px 11px 11px 11px;
  position: absolute;
  left: 58px;
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

.upload-btn {
  width: 300px;
  height: 75px;
  background: #8d8e8f;
  border-radius: 11px 11px 11px 11px;
  position: absolute;
  left: 382px;
  top: 539px;
  
  font-family: 'Source Han Sans', 'Source Han Sans', sans-serif;
  font-weight: 500;
  font-size: 44px;
  color: #FCF6F6;
  line-height: 75px;
  letter-spacing: 3px;
  text-align: center;
  font-style: normal;
  text-transform: none;
  cursor: pointer;
}

.correct-demo-text {
  position: absolute;
  left: 113px;
  top: 29px;
  width: 101px;
  height: 34px;
  opacity: 1;
  font-family: 'Source Han Sans', sans-serif;
  font-size: 24px;
  font-weight: 500;
  line-height: normal;
  letter-spacing: 0em;
  font-variation-settings: "opsz" auto;
  font-feature-settings: "kern" on;
  color: #3D3D3D;
}
.uncorrect-demo-text {
  position: absolute;
  left: 113px;
  top: 325px;
  width: 101px;
  height: 34px;
  opacity: 1;
  font-family: 'Source Han Sans', sans-serif;
  font-size: 24px;
  font-weight: 500;
  line-height: normal;
  letter-spacing: 0em;
  font-variation-settings: "opsz" auto;
  font-feature-settings: "kern" on;
  color: #3D3D3D;
}
.mask-demo-text {
  position: absolute;
  left: 132px;
  top: 495px;
  width: 101px;
  height: 34px;
  opacity: 1;
  font-family: 'Source Han Sans', sans-serif;
  font-size: 24px;
  font-weight: 500;
  line-height: normal;
  letter-spacing: 0em;
  font-variation-settings: "opsz" auto;
  font-feature-settings: "kern" on;
  color: #3D3D3D;
}
.map-demo-text {
  position: absolute;
  left: 330px;
  top: 495px;
  width: 101px;
  height: 34px;
  opacity: 1;
  font-family: 'Source Han Sans', sans-serif;
  font-size: 24px;
  font-weight: 500;
  line-height: normal;
  letter-spacing: 0em;
  font-variation-settings: "opsz" auto;
  font-feature-settings: "kern" on;
  color: #3D3D3D;
}
.glass-demo-text {
  position: absolute;
  left: 537px;
  top: 495px;
  width: 101px;
  height: 34px;
  opacity: 1;
  font-family: 'Source Han Sans', sans-serif;
  font-size: 24px;
  font-weight: 500;
  line-height: normal;
  letter-spacing: 0em;
  font-variation-settings: "opsz" auto;
  font-feature-settings: "kern" on;
  color: #3D3D3D;
}

.log-container {
  position: fixed;
  left: 1335px;
  top: 253px;
  width: 491px;
  height: 658px;
  border-radius: 37px;
  opacity: 1;
  background: rgba(0, 0, 0, 0.0392);
}

.photo-preview {
  position: absolute;
  left: 155px;
  top: 62px;
  width: 180px;
  height: 230px;
  opacity: 1;
  background: #FFFFFF;
  
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  border-radius: 20px;
}

.face-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 10px;
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
}

.log-id {
  top: 442px;
}

.log-address {
  top: 499px;
}

.log-input {
  position: absolute;
  left: 230px; /* 调整输入框左边距，使其在标签右侧 */
  width: 200px;
  height: 30px;
  font-family: 'Source Han Serif CN', sans-serif;
  font-size: 20px;
  border: none;
  background: transparent;
  border-bottom: 1px solid #3D3D3D;
  outline: none;
  color: #3D3D3D;
}

.input-name {
  top: 384px;
}

.input-id {
  top: 442px;
}

.input-address {
  top: 499px;
}

.save-btn {
  position: absolute;
  left: 193px;
  top: 569px;
  width: 107px;
  height: 54px;
  border-radius: 37px;
  opacity: 1;
  background: #78B1EE;
  
  font-family: 'Source Han Serif CN', sans-serif;
  font-size: 24px;
  font-weight: bold;
  color: #FFFFFF;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
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


