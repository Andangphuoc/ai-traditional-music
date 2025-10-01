
```
GET http://localhost:8000/
```
**Response:**
```json
{
  "message": "AI Chatbot for Music Instruments Sales API"
}
```

---

## 2. API Tư vấn Nhạc cụ (Consultation)

### 2.1. Chat Tư vấn Thông thường
```
POST http://localhost:8000/consultation/
```

**Request Body (Lần đầu - không có history):**
```json
{
  "query": "Tôi muốn học sáo trúc, mới bắt đầu, ngân sách khoảng 500k",
  "history": []
}
```

**Request Body (Có history - chat tiếp):**
```json
{
  "query": "Còn phụ kiện gì cần mua thêm không?",
  "history": [
    {
      "user": "Tôi muốn học sáo trúc, mới bắt đầu, ngân sách khoảng 500k",
      "ai": "Bạn mới học sáo trúc? Nên chọn sáo tone D, tre già giá 350k, dễ thổi, âm ấm, kèm giáo trình cơ bản + túi đựng."
    }
  ]
}
```

**Response:**
```json
{
  "suggestion": "Cần thêm: dây treo sáo (30k), sáp bảo dưỡng tre (50k), và giáo trình video online miễn phí. Tổng khoảng 430k.",
  "updated_history": [
    {
      "user": "Tôi muốn học sáo trúc, mới bắt đầu, ngân sách khoảng 500k",
      "ai": "Bạn mới học sáo trúc? Nên chọn sáo tone D, tre già giá 350k, dễ thổi, âm ấm, kèm giáo trình cơ bản + túi đựng."
    },
    {
      "user": "Còn phụ kiện gì cần mua thêm không?",
      "ai": "Cần thêm: dây treo sáo (30k), sáp bảo dưỡng tre (50k), và giáo trình video online miễn phí. Tổng khoảng 430k."
    }
  ]
}
```

### 2.2. Tư vấn Nhanh (Quick Consult)
```
POST http://localhost:8000/consultation/quick
```

**Request Body:**
```json
{
  "level": "mới học",
  "budget": "dưới 500k",
  "purpose": "học",
  "instrument_type": "hơi",
  "age": 25,
  "additional_info": "Muốn tự học tại nhà"
}
```

**Request Body (Ví dụ 2):**
```json
{
  "level": "trung cấp",
  "budget": "500k-1tr",
  "purpose": "biểu diễn",
  "instrument_type": "dây",
  "age": 30,
  "additional_info": "Đã biết chơi guitar, muốn học nhạc cụ dân tộc"
}
```

**Response:**
```json
{
  "suggestion": "Với người mới học và mục đích tự học tại nhà, nên chọn sáo trúc tone D (30cm), tre già giá 350k, dễ thổi, âm ấm, kèm giáo trình PDF + túi vải + dây treo.",
  "user_profile": {
    "level": "mới học",
    "budget": "dưới 500k",
    "purpose": "học",
    "instrument_type": "hơi",
    "age": 25
  }
}
```

---

## 3. API Demo Âm thanh (Demo Audio)

### 3.1. Lấy File Mẫu Có Sẵn
```
POST http://localhost:8000/demo/
```

**Request Body:**
```json
{
  "product": "sáo",
  "use_ai": false,
  "style": "dân gian Việt Nam",
  "duration": 5
}
```

**Danh sách nhạc cụ có file mẫu:**
- "sáo"
- "đàn tranh"
- "đàn bầu"
- "đàn nguyệt"
- "đàn nhi"
- "đàn đá"
- "đàn day"
- "đàn sen"
- "đàn tỳ bà"
- "danh tranh"
- "kèn bé"
- "t'rưng"

**Response:** File audio WAV/MP3 (download)

### 3.2. Tạo Âm thanh bằng AI
```
POST http://localhost:8000/demo/
```

**Request Body:**
```json
{
  "product": "đàn bầu",
  "use_ai": true,
  "style": "trữ tình",
  "duration": 10
}
```

**Request Body (Ví dụ 2 - Nhạc cụ không có mẫu):**
```json
{
  "product": "ken_bau",
  "use_ai": true,
  "style": "dân gian miền núi",
  "duration": 8
}
```

**Response:** File audio WAV được tạo bởi AI (download)

---

## 4. API Hướng dẫn Sử dụng (Guide)

### 4.1. Hỏi Hướng dẫn Cơ bản
```
POST http://localhost:8000/guide/
```

**Request Body:**
```json
{
  "query": "Cách thổi sáo trúc cho người mới bắt đầu",
  "history": []
}
```

**Response:**
```json
{
  "guide": "Trả lời ngắn gọn 3-4 bước cơ bản:\n1. Đặt miệng tạo hình chữ O, thổi nhẹ vào lỗ thổi\n2. Điều chỉnh góc nghiêng sáo đến khi có âm thanh\n3. Luyện thổi dài đều, không ngắt quãng\n\nVideo gợi ý: Hướng dẫn thổi sáo trúc cơ bản - [link]",
  "updated_history": [
    {
      "user": "Cách thổi sáo trúc cho người mới bắt đầu",
      "ai": "Trả lời ngắn gọn 3-4 bước cơ bản:\n1. Đặt miệng tạo hình chữ O, thổi nhẹ vào lỗ thổi\n2. Điều chỉnh góc nghiêng sáo đến khi có âm thanh\n3. Luyện thổi dài đều, không ngắt quãng\n\nVideo gợi ý: Hướng dẫn thổi sáo trúc cơ bản - [link]"
    }
  ]
}
```

### 4.2. Hỏi Chi tiết (Follow-up)
```
POST http://localhost:8000/guide/
```

**Request Body:**
```json
{
  "query": "Chi tiết hơn về cách đặt miệng thế nào?",
  "history": [
    {
      "user": "Cách thổi sáo trúc cho người mới bắt đầu",
      "ai": "Trả lời ngắn gọn 3-4 bước cơ bản:\n1. Đặt miệng tạo hình chữ O, thổi nhẹ vào lỗ thổi\n2. Điều chỉnh góc nghiêng sáo đến khi có âm thanh\n3. Luyện thổi dài đều, không ngắt quãng"
    }
  ]
}
```

**Response:**
```json
{
  "guide": "Kỹ thuật đặt miệng cụ thể:\n1. Môi trên và dưới hơi chu lại, tạo khe hở nhỏ ở giữa\n2. Đặt rìa lỗ thổi sáo sát môi dưới\n3. Thổi luồng khí mỏng, hướng xuống khoảng 45 độ\n4. Điều chỉnh độ rộng môi đến khi âm trong, rõ ràng\n\nTips quan trọng: Thở bằng bụng, không căng cứng vùng hàm",
  "updated_history": [...]
}
```

---

## 5. API Câu chuyện Nhạc cụ (Story)

```
POST http://localhost:8000/story/
```

**Request Body (Ví dụ 1):**
```json
{
  "query": "Kể về nguồn gốc đàn bầu",
  "history": []
}
```

**Request Body (Ví dụ 2):**
```json
{
  "query": "Lịch sử của sáo trúc Việt Nam",
  "history": []
}
```

**Request Body (Ví dụ 3):**
```json
{
  "query": "Đàn tranh có ý nghĩa gì trong văn hóa Việt?",
  "history": []
}
```

**Response:**
```json
{
  "story": "Đàn bầu là nhạc cụ độc tấu một dây của Việt Nam. Xuất hiện từ thế kỷ 10, gắn liền với ca trù. Âm thanh uốn lượn như giọng hát, thể hiện tâm hồn người Việt.",
  "updated_history": [
    {
      "user": "Kể về nguồn gốc đàn bầu",
      "ai": "Đàn bầu là nhạc cụ độc tấu một dây của Việt Nam. Xuất hiện từ thế kỷ 10, gắn liền với ca trù. Âm thanh uốn lượn như giọng hát, thể hiện tâm hồn người Việt."
    }
  ]
}
```

---

## 6. API Hỗ trợ Khách hàng (Support)

```
POST http://localhost:8000/support/
```

**Request Body (Ví dụ 1 - Bảo quản):**
```json
{
  "query": "Cách bảo quản sáo trúc khi trời ẩm?",
  "history": []
}
```

**Request Body (Ví dụ 2 - Vận chuyển):**
```json
{
  "query": "Giao hàng mất bao lâu?",
  "history": []
}
```

**Request Body (Ví dụ 3 - Bảo hành):**
```json
{
  "query": "Đàn tranh có bảo hành không?",
  "history": []
}
```

**Request Body (Ví dụ 4 - Sửa chữa):**
```json
{
  "query": "Sáo của tôi bị nứt, sửa được không?",
  "history": []
}
```

**Response:**
```json
{
  "response": "Bảo quản sáo khi trời ẩm: cất nơi khô ráo, dùng túi hút ẩm silica gel. Tránh để gần cửa sổ hoặc nơi có nước.",
  "updated_history": [
    {
      "user": "Cách bảo quản sáo trúc khi trời ẩm?",
      "ai": "Bảo quản sáo khi trời ẩm: cất nơi khô ráo, dùng túi hút ẩm silica gel. Tránh để gần cửa sổ hoặc nơi có nước."
    }
  ]
}
```

---
