import asyncio
import websockets
import cv2
import base64
import logging
import threading
import json
import time
import sys
import os
import pymysql
import datetime
from datetime import timedelta

# 添加项目根目录到 sys.path 以便导入 libs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/face_system/face_system')
from libs import FaceModel
from libs.utils.utils import show_bboxes, compare_embedding
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456', # 请根据实际情况修改密码
    'database': 'face', # 假设数据库名为 face_system，请根据实际情况修改
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 数据库连接测试
try:
    connection = pymysql.connect(**DB_CONFIG)
    logging.info("Database connection successful")
    connection.close()
except Exception as e:
    logging.error(f"Database connection failed: {e}")

# Global Face Models
# Detect model for fast streaming
detect_model = FaceModel(None, detect_only=True)
# Recognition model for search and enrollment
recognition_model = FaceModel(None, detect_only=False)

# Record Management
class RecordManager:
    def __init__(self):
        self.clients = set()
        self.last_recorded = {} # {name: datetime}
        self.cooldown = timedelta(seconds=10) # 10 seconds cooldown
        self.lock = asyncio.Lock()

    async def register(self, websocket):
        self.clients.add(websocket)
        logging.info("Client registered for records. Waiting for request...")

    async def handle_client_message(self, websocket, message):
        try:
            data = json.loads(message)
            if data.get('type') == 'get_date_records':
                query_date = data.get('date')
                logging.info(f"Fetching records for date: {query_date}")
                await self.send_history_records(websocket, query_date)
        except Exception as e:
            logging.error(f"Error handling client message: {e}")

    async def send_history_records(self, websocket, query_date):
        try:
            connection = pymysql.connect(**DB_CONFIG)
            try:
                with connection.cursor() as cursor:
                    # Filter by specific date
                    # query_date format expected: 'YYYY-MM-DD'
                    sql = "SELECT `name`, `number`, `image`, `time`, `address` FROM `record` WHERE DATE(`time`) = %s ORDER BY `time` DESC"
                    cursor.execute(sql, (query_date,))
                    results = cursor.fetchall()
                    
                    logging.info(f"Found {len(results)} records for {query_date}")
                    
                    # Send records in reverse order (oldest first) so frontend can prepend them correctly 
                    # or just send them as is and let frontend handle sorting. 
                    # But frontend uses unshift, so we should send oldest to newest if we want them to appear in order?
                    # Actually frontend unshifts (adds to top), so if we send newest first, it will be added to top, 
                    # then second newest added to top... result is reversed.
                    # Correct logic for unshift: Send Oldest -> Newest.
                    # Or Send Newest -> Oldest but frontend should use push?
                    # Let's keep frontend unshift (newest on top).
                    # If we send Rec1 (Newest), it goes to top. Rec2 (Older), it goes to top (above Rec1). WRONG.
                    # We should send from Oldest to Newest if frontend uses unshift? No.
                    # If frontend uses unshift (add to start), we want the final list to be [Newest, Older, Oldest].
                    # If we send Oldest, list: [Oldest].
                    # Then send Older, list: [Older, Oldest].
                    # Then send Newest, list: [Newest, Older, Oldest]. Correct.
                    
                    # So we need to iterate results from end to start (since SQL DESC gives Newest first).
                    for row in reversed(results):
                        try:
                            image_data = row['image']
                            # Ensure image is bytes
                            if isinstance(image_data, str):
                                # If stored as base64 string in db (some legacy?), decode it? 
                                # Assuming blob (bytes) as per user description
                                pass
                            
                            img_base64 = base64.b64encode(image_data).decode('utf-8') if image_data else None
                            
                            record_data = {
                                'name': row['name'],
                                'number': row['number'],
                                'image': img_base64,
                                'time': row['time'].strftime('%Y-%m-%d %H:%M:%S') if row['time'] else '',
                                'address': row['address']
                            }
                            
                            message = json.dumps({"type": "new_record", "data": record_data})
                            await websocket.send(message)
                        except Exception as e:
                            logging.error(f"Error sending history record: {e}")
                            
            except Exception as e:
                logging.error(f"Database error loading history: {e}")
            finally:
                connection.close()
        except Exception as e:
            logging.error(f"Connection error loading history: {e}")

    async def unregister(self, websocket):
        self.clients.discard(websocket)

    async def broadcast(self, record):
        if not self.clients:
            return
        message = json.dumps({"type": "new_record", "data": record})
        to_remove = set()
        for ws in self.clients:
            try:
                await ws.send(message)
            except:
                to_remove.add(ws)
        for ws in to_remove:
            self.clients.discard(ws)

    def should_record(self, name):
        now = datetime.datetime.now()
        if name not in self.last_recorded:
            self.last_recorded[name] = now
            return True
        if now - self.last_recorded[name] > self.cooldown:
            self.last_recorded[name] = now
            return True
        return False

    def save_record(self, name, number, image_binary, address):
        # Run in thread to avoid blocking
        threading.Thread(target=self._save_thread, args=(name, number, image_binary, address)).start()

    def _save_thread(self, name, number, image_binary, address):
        try:
            connection = pymysql.connect(**DB_CONFIG)
            try:
                with connection.cursor() as cursor:
                    now = datetime.datetime.now()
                    sql = "INSERT INTO `record` (`name`, `number`, `image`, `time`, `address`) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (name, number, image_binary, now, address))
                connection.commit()
                logging.info(f"Recorded face for {name}")
                
                # Prepare data for broadcast (convert bytes to base64, datetime to str)
                record_data = {
                    'name': name,
                    'number': number,
                    'image': base64.b64encode(image_binary).decode('utf-8'),
                    'time': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'address': address
                }
                
                # Broadcast needs to be scheduled in the event loop
                asyncio.run_coroutine_threadsafe(self.broadcast(record_data), loop)
                
            except Exception as e:
                logging.error(f"Database error saving record: {e}")
            finally:
                connection.close()
        except Exception as e:
            logging.error(f"Connection error saving record: {e}")

record_manager = RecordManager()
loop = None # Will be set in main

# Face Bank Cache
face_bank_embeddings = []
face_bank_metadata = []

def load_face_bank():
    global face_bank_embeddings, face_bank_metadata
    
    # Use local variables to build the list
    new_face_bank_embeddings = []
    new_face_bank_metadata = []
    
    logging.info("Loading face bank from database...")
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            sql = "SELECT `name`, `number`, `address`, `image` FROM `face`"
            cursor.execute(sql)
            results = cursor.fetchall()
            
            for row in results:
                try:
                    # Convert binary data to image
                    image_data = row['image']
                    nparr = np.frombuffer(image_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if img is None:
                        continue
                        
                    # Get embedding
                    # We assume the stored image contains a face. 
                    # Use resize + flatten to match compare.py logic
                    try:
                        img_resized = cv2.resize(img, (112, 112))
                        embedding = img_resized.flatten().reshape(1, -1)
                        new_face_bank_embeddings.append(embedding)
                        
                        # Store metadata (convert image to base64 for display if needed, or just store reference)
                        # We store the base64 string for frontend display
                        img_base64 = base64.b64encode(image_data).decode('utf-8')
                        new_face_bank_metadata.append({
                            'name': row['name'],
                            'number': row['number'],
                            'address': row['address'],
                            'image_base64': img_base64
                        })
                    except Exception as e:
                         logging.error(f"Error extracting features for {row.get('name', 'unknown')}: {e}")
                except Exception as e:
                    logging.error(f"Error processing face {row.get('name', 'unknown')}: {e}")
                    
        logging.info(f"Loaded {len(new_face_bank_embeddings)} faces into face bank.")
        
        # Atomically update global variables
        face_bank_embeddings = new_face_bank_embeddings
        face_bank_metadata = new_face_bank_metadata
        
    except Exception as e:
        logging.error(f"Error loading face bank: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

# Load face bank on startup
load_face_bank()

def save_face_to_db(data):
    try:
        connection = pymysql.connect(**DB_CONFIG)
        try:
            with connection.cursor() as cursor:
                # 解析 Base64 图片数据
                # 前端发送的格式通常是 "data:image/jpeg;base64,......"
                image_data = data['image']
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                
                binary_data = base64.b64decode(image_data)
                
                sql = "INSERT INTO `face` (`name`, `number`, `address`, `image`) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (data['name'], data['number'], data['address'], binary_data))
            
            connection.commit()
            logging.info(f"Successfully saved face data for {data['name']}")
            
            # Reload face bank to include new face
            # Optimization: could just append, but reloading ensures consistency
            # Running in a separate thread to avoid blocking
            threading.Thread(target=load_face_bank).start()
            
            return True, "保存成功"
        except Exception as e:
            logging.error(f"Database error: {e}")
            return False, f"数据库错误: {str(e)}"
        finally:
            connection.close()
    except Exception as e:
        logging.error(f"Connection error: {e}")
        return False, f"连接数据库失败: {str(e)}"


# Global state to manage camera resources
class CameraManager:
    def __init__(self):
        self.cameras = {}  # {camera_id: cv2.VideoCapture}
        self.clients = {}  # {camera_id: set(websocket)}
        self.locks = {}    # {camera_id: asyncio.Lock}
        self.running_tasks = {} # {camera_id: asyncio.Task}

    async def get_camera(self, camera_id):
        if camera_id not in self.cameras:
            logging.info(f"Opening camera {camera_id}...")
            # Use CAP_DSHOW on Windows to avoid MSMF errors
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            if not cap.isOpened():
                logging.error(f"Failed to open camera {camera_id}")
                return None
            self.cameras[camera_id] = cap
            self.clients[camera_id] = {}
            self.locks[camera_id] = asyncio.Lock()
        return self.cameras[camera_id]

    async def release_camera(self, camera_id):
        if camera_id in self.cameras:
            if not self.clients[camera_id]: # Only release if no clients connected
                logging.info(f"Releasing camera {camera_id}...")
                self.cameras[camera_id].release()
                del self.cameras[camera_id]
                del self.clients[camera_id]
                del self.locks[camera_id]
                if camera_id in self.running_tasks:
                    self.running_tasks[camera_id].cancel()
                    del self.running_tasks[camera_id]

    async def add_client(self, camera_id, websocket, client_type='normal'):
        if camera_id not in self.clients:
            self.clients[camera_id] = {}
        self.clients[camera_id][websocket] = client_type
        
        # Start streaming task if not already running
        if camera_id not in self.running_tasks:
            self.running_tasks[camera_id] = asyncio.create_task(self.stream_camera(camera_id))

    async def remove_client(self, camera_id, websocket):
        if camera_id in self.clients:
            if websocket in self.clients[camera_id]:
                del self.clients[camera_id][websocket]
            if not self.clients[camera_id]:
                await self.release_camera(camera_id)

    async def stream_camera(self, camera_id):
        logging.info(f"Starting stream for camera {camera_id}")
        cap = await self.get_camera(camera_id)
        if not cap:
            return

        try:
            pTime = 0
            while camera_id in self.cameras and self.cameras[camera_id].isOpened():
                ret, frame = self.cameras[camera_id].read()
                if not ret:
                    logging.warning(f"Camera {camera_id}: Failed to grab frame.")
                    await asyncio.sleep(0.1) # Avoid flooding the log
                    continue
                
                # 人脸检测
                try:
                    landmarks, bboxs, faces, embeddings = detect_model(frame)
                except Exception as e:
                    logging.error(f"Error in face detection: {e}")
                    landmarks, bboxs, faces, embeddings = [], [], [], []
                
                names = [''] * len(bboxs)
                
                # Face Recognition and Recording
                if len(bboxs) > 0 and face_bank_embeddings:
                    for i in range(len(bboxs)):
                        try:
                            # Use the face image from detection for recognition
                            # Assuming 'faces' contains aligned face images
                            if i < len(faces):
                                face_img = faces[i]
                                # Preprocess for comparison (match load_face_bank logic)
                                face_resized = cv2.resize(face_img, (112, 112))
                                face_emb = face_resized.flatten()
                                
                                # Compare with face bank
                                match_idx = compare_embedding(face_emb, face_bank_embeddings, threshold=0.95)
                                
                                if match_idx is not None:
                                    match_info = face_bank_metadata[match_idx]
                                    name = match_info['name']
                                    names[i] = name # Update name for display
                                    
                                    # Check if we should record this detection
                                    if record_manager.should_record(name):
                                        # Save record
                                        # Encode face image to binary
                                        _, img_buffer = cv2.imencode('.jpg', face_img)
                                        img_binary = img_buffer.tobytes()
                                        
                                        record_manager.save_record(
                                            name, 
                                            match_info['number'], 
                                            img_binary, 
                                            match_info['address']
                                        )
                        except Exception as e:
                            logging.error(f"Error in recognition loop: {e}")

                # 绘制检测框
                try:
                    result_frame_normal = show_bboxes(frame.copy(), bboxs, landmarks, names)
                    empty_names = [''] * len(bboxs)
                    result_frame_enroll = show_bboxes(frame.copy(), bboxs, landmarks, empty_names)
                except Exception as e:
                    logging.error(f"Error drawing bounding boxes: {e}")
                    result_frame_normal = frame.copy()
                    result_frame_enroll = frame.copy()

                # 获取检测到的人脸图片（第一张）
                face_image_base64 = None
                if len(bboxs) > 0:
                    try:
                        b = bboxs[0]
                        x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
                        # 确保坐标在图像范围内
                        h, w, _ = frame.shape
                        x1 = max(0, x1)
                        y1 = max(0, y1)
                        x2 = min(w, x2)
                        y2 = min(h, y2)
                        
                        if x2 > x1 and y2 > y1:
                            face_img = frame[y1:y2, x1:x2]
                            _, face_buffer = cv2.imencode('.jpg', face_img)
                            face_image_base64 = base64.b64encode(face_buffer).decode('utf-8')
                    except Exception as e:
                        logging.error(f"Error cropping face: {e}")
                
                # Encode frame
                _, buffer_normal = cv2.imencode('.jpg', result_frame_normal)
                jpg_normal_as_text = base64.b64encode(buffer_normal).decode('utf-8')

                _, buffer_enroll = cv2.imencode('.jpg', result_frame_enroll)
                jpg_enroll_as_text = base64.b64encode(buffer_enroll).decode('utf-8')
                
                # 构建消息对象
                base_message = {
                    "face_count": len(bboxs),
                    "face_image": face_image_base64
                }
                
                json_message_normal = json.dumps({**base_message, "image": jpg_normal_as_text})
                json_message_enroll = json.dumps({**base_message, "image": jpg_enroll_as_text})

                # Broadcast to all connected clients
                if camera_id in self.clients:
                    websockets_to_remove = set()
                    current_clients = list(self.clients[camera_id].items())
                    
                    if not current_clients:
                        break

                    for ws, client_type in current_clients:
                        try:
                            if client_type == 'enroll':
                                await ws.send(json_message_enroll)
                            else:
                                await ws.send(json_message_normal)
                        except websockets.exceptions.ConnectionClosed:
                            websockets_to_remove.add(ws)
                        except Exception as e:
                            logging.error(f"Error sending to client: {e}")
                            websockets_to_remove.add(ws)
                    
                    # Clean up disconnected clients
                    for ws in websockets_to_remove:
                        await self.remove_client(camera_id, ws)

                await asyncio.sleep(0.01) # Reduce sleep time to allow higher FPS if possible

        except asyncio.CancelledError:
            # logging.info(f"Stream task for camera {camera_id} cancelled") # 避免频繁打印
            pass
        finally:
            # logging.info(f"Stream loop for camera {camera_id} ended") # 避免频繁打印
            pass

manager = CameraManager()

async def handler(websocket, path):
    # Check if this is a save request
    if path == '/save':
        logging.info("Client connected for saving data")
        try:
            message = await websocket.recv()
            data = json.loads(message)
            logging.info(f"Received save request for {data.get('name')}")
            
            success, msg = save_face_to_db(data)
            
            response = {"success": success, "message": msg}
            await websocket.send(json.dumps(response))
        except Exception as e:
            logging.error(f"Error handling save request: {e}")
            await websocket.send(json.dumps({"success": False, "message": str(e)}))
        finally:
            return

    # Check if this is a search request
    if path == '/search':
        logging.info("Client connected for search")
        try:
            message = await websocket.recv()
            data = json.loads(message)
            logging.info(f"Received search request")
            
            image_data = data.get('image')
            if not image_data:
                await websocket.send(json.dumps({"success": False, "message": "No image provided"}))
                return

            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            binary_data = base64.b64decode(image_data)
            nparr = np.frombuffer(binary_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                await websocket.send(json.dumps({"success": False, "message": "Invalid image"}))
                return

            # Get embedding
            # Use resize + flatten to match compare.py logic
            try:
                img_resized = cv2.resize(img, (112, 112))
                query_embedding = img_resized.flatten()
            except Exception as e:
                logging.error(f"Error processing search image: {e}")
                await websocket.send(json.dumps({"success": False, "message": "Error processing image"}))
                return

            # Compare with face bank
            if not face_bank_embeddings:
                await websocket.send(json.dumps({"success": False, "message": "Database is empty"}))
                return

            # compare_embedding returns index or None
            match_idx = compare_embedding(query_embedding, face_bank_embeddings, threshold=0.95)

            if match_idx is not None:
                match_info = face_bank_metadata[match_idx]
                response = {
                    "success": True,
                    "data": match_info
                }
                logging.info(f"Match found: {match_info['name']}")
            else:
                response = {
                    "success": False,
                    "message": "No match found"
                }
                logging.info("No match found")
            
            await websocket.send(json.dumps(response))
        except Exception as e:
            logging.error(f"Error handling search request: {e}")
            await websocket.send(json.dumps({"success": False, "message": str(e)}))
        finally:
            return

    # Check if this is an extract face request
    if path == '/extract_face':
        logging.info("Client connected for extracting face")
        try:
            message = await websocket.recv()
            data = json.loads(message)
            logging.info("Received extract face request")
            
            image_data = data.get('image')
            if not image_data:
                await websocket.send(json.dumps({"success": False, "message": "No image provided"}))
                return

            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            binary_data = base64.b64decode(image_data)
            nparr = np.frombuffer(binary_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                await websocket.send(json.dumps({"success": False, "message": "Invalid image"}))
                return

            # Detect face
            landmarks, bboxs, faces, embeddings = detect_model(img)
            
            if len(bboxs) > 0:
                try:
                    b = bboxs[0]
                    x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
                    h, w, _ = img.shape
                    x1 = max(0, x1)
                    y1 = max(0, y1)
                    x2 = min(w, x2)
                    y2 = min(h, y2)
                    
                    if x2 > x1 and y2 > y1:
                        face_img = img[y1:y2, x1:x2]
                        _, face_buffer = cv2.imencode('.jpg', face_img)
                        face_image_base64 = base64.b64encode(face_buffer).decode('utf-8')
                        await websocket.send(json.dumps({"success": True, "face_image": face_image_base64}))
                    else:
                        await websocket.send(json.dumps({"success": False, "message": "人脸坐标无效"}))
                except Exception as e:
                    logging.error(f"Error cropping face: {e}")
                    await websocket.send(json.dumps({"success": False, "message": "人脸截取失败"}))
            else:
                await websocket.send(json.dumps({"success": False, "message": "未检测到人脸，请上传包含清晰人脸的照片"}))
                
        except Exception as e:
            logging.error(f"Error handling extract face request: {e}")
            await websocket.send(json.dumps({"success": False, "message": str(e)}))
        finally:
            return

    # Check if this is a records subscription
    if path == '/records':
        logging.info("Client connected to records stream")
        await record_manager.register(websocket)
        try:
            async for message in websocket:
                await record_manager.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await record_manager.unregister(websocket)
            return

    # Parse camera ID from path (e.g., "/0", "/1")
    client_type = 'normal'
    try:
        # Remove leading slash
        path_clean = path.strip('/')
        if '?' in path_clean:
            path_parts = path_clean.split('?')
            path_clean = path_parts[0]
            query = path_parts[1]
            if 'type=enroll' in query:
                client_type = 'enroll'
                
        if not path_clean:
            camera_id = 0
        else:
            camera_id = int(path_clean)
    except ValueError:
        logging.error(f"Invalid camera ID in path: {path}")
        await websocket.close(1008, "Invalid camera ID")
        return

    logging.info(f"Client connected to camera {camera_id}, type: {client_type}")
    
    # Check if camera is available
    cap = await manager.get_camera(camera_id)
    if not cap:
        logging.error(f"Camera {camera_id} not available")
        await websocket.close(1011, "Camera not available")
        return

    await manager.add_client(camera_id, websocket, client_type)

    try:
        await websocket.wait_closed()
    except Exception:
        pass
    finally:
        await manager.remove_client(camera_id, websocket)
        # logging.info(f"Client disconnected from camera {camera_id}") # 避免频繁打印

async def main():
    global loop
    loop = asyncio.get_running_loop()
    async with websockets.serve(handler, "localhost", 8765):
        logging.info("Server started on ws://localhost:8765")
        # Keep the server running
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
