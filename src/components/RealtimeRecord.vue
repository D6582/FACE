<template>
  <div class="realtime-record">
    <div class="monitor-container">
      <div class="top-panel">
        <div class="record-stats">
          <div class="stat-item">
            <span class="stat-num">{{ records.length }}</span>
            <span class="stat-label">今日记录</span>
          </div>
        </div>
      </div>
      
      <div class="date-panel">
        <input type="date" v-model="currentDate" class="date-input" />
      </div>
      
      <div class="record-list-container">
        <div class="list-body">
          <div v-for="(record, index) in records" :key="index" class="record-card">
            <div class="card-content">
              <img src="@/assets/chat-1-fill.png" class="card-icon" />
              <div class="card-info">
                <div class="info-row">
                  <span class="info-label">时间：</span>
                  <span class="info-value time-value">{{ formatTime(record.time) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">姓名：</span>
                  <span class="info-value name-value">{{ record.name }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">证件号：</span>
                  <span class="info-value">{{ record.number }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">地址：</span>
                  <span class="info-value">{{ record.address }}</span>
                </div>
              </div>
              <div class="card-image">
                 <img v-if="record.image" :src="'data:image/jpeg;base64,' + record.image" class="face-img" />
              </div>
            </div>
          </div>
          <div v-if="records.length === 0" class="no-data">
            暂无识别记录
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RealtimeRecord',
  data() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const today = `${year}-${month}-${day}`;
    
    return {
      records: [],
      ws: null,
      reconnectTimer: null,
      currentDate: today
    }
  },
  watch: {
    currentDate(newDate) {
      if (newDate) {
        this.records = []; // Clear list
        this.fetchRecords(newDate);
      }
    }
  },
  mounted() {
    this.connectWebSocket();
  },
  beforeDestroy() {
    if (this.ws) {
      this.ws.close();
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
  },
  methods: {
    fetchRecords(date) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'get_date_records',
          date: date
        }));
      }
    },
    formatTime(timeStr) {
      if (!timeStr) return '';
      // Assuming timeStr format is like "YYYY-MM-DD HH:mm:ss"
      const parts = timeStr.split(' ');
      return parts.length > 1 ? parts[1] : timeStr;
    },
    connectWebSocket() {
      if (this.ws) {
        this.ws.close();
      }

      this.ws = new WebSocket('ws://localhost:8765/records');
      
      this.ws.onopen = () => {
        console.log('Connected to records stream');
        this.fetchRecords(this.currentDate);
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'new_record') {
            this.records.unshift(message.data);
            // Limit list size to avoid memory issues
            if (this.records.length > 200) {
              this.records.pop();
            }
          }
        } catch (e) {
          console.error('Error parsing record:', e);
        }
      };
      
      this.ws.onclose = () => {
        console.log('Records stream closed, reconnecting in 3s...');
        this.reconnectTimer = setTimeout(this.connectWebSocket, 3000);
      };

      this.ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        this.ws.close();
      };
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
  position: relative;
}

.top-panel {
  width: 150px;
  height: 100px;
  background: #FFFFFF;
  border-radius: 19px;
  position: absolute;
  left: 1720px;
  top: 30px;
  display: flex;
  
  align-items: center;
  padding: 0 40px;
  box-sizing: border-box;
  justify-content: space-between;
}

.panel-title {
  font-size: 32px;
  font-weight: bold;
  color: #3D3D3D;
}

.date-panel {
  width: 262px;
  height: 67px;
  background: #FFFFFF;
  border-radius: 19px;
  position: absolute;
  left: 81px;
  top: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  box-sizing: border-box;
}

.date-input {
  border: none;
  font-family: 'Source Han Sans', sans-serif;
  font-weight: 600;
  font-size: 25px;
  color: #979696;
  font-style: normal;
}

.record-stats {
  display: flex;
  gap: 40px;
  margin-left: auto;
}

.stat-item {
  text-align: center;
}

.stat-num {
  font-size: 36px;
  font-weight: bold;
  color: #045D8D;
  display: block;
}

.stat-label {
  font-size: 16px;
  color: #999;
}

.record-list-container {
  width: 1780px;
  height: 640px;
  background: transparent;
  position: absolute;
  left: 89px;
  top: 150px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.list-body {
  flex: 1;
  overflow-y: auto;
  /* padding-right: 10px; */ /* Optional: for scrollbar */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE 10+ */
}

.list-body::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}

.record-card {
  width: 1780px;
  height: 179px;
  background: #FFFFFF;
  border-radius: 19px;
  margin-bottom: 20px;
  box-sizing: border-box;
  padding: 20px;
  display: flex;
  align-items: center;
}

.card-content {
  display: flex;
  align-items: center;
  width: 100%;
  position: relative;
}

.card-icon {
  position: absolute;
  top: 0;
  left: 0;
  width: 30px; /* Adjust size as needed */
  height: 30px; /* Adjust size as needed */
}

.card-image {
  width: 140px;
  height: 140px;
  margin-left: 40px; /* Changed from margin-right */
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  overflow: hidden;
  background: #f0f0f0;
}

.face-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-info {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  margin-top: 30px;
  margin-left: 30px;
}

.info-row {
  width: 50%; /* Two columns */
  height: 60px;
  display: flex;
  align-items: center;
  font-size: 24px;
  color: #333;
}

.info-label {
  color: #999;
  margin-right: 10px;
  min-width: 100px;
}

.info-value {
  font-weight: bold;
}

.time-value {
  color: #045D8D;
  font-size: 28px;
}

.name-value {
  font-size: 28px;
}

.no-data {
  text-align: center;
  margin-top: 100px;
  color: #999;
  font-size: 24px;
}
</style>