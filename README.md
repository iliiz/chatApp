# STATION ✦ | Full-Stack Real-Time Chat Application

STATION is a modern, high-performance, and secure full-stack real-time chat web application designed with a robust asynchronous backend and a dynamic frontend architecture. It features secure user authentication, interactive chat rooms, and a comprehensive admin analytics dashboard.

## 🚀 Live Demo & Links
Experience the live application and explore the architecture:
- **Live Demo:** [Deploy on Render](https://chatapp-0n10.onrender.com)
- **Source Code:** [GitHub Repository](https://github.com/iliiz/chatApp)

---

## 🛠️ Tech Stack & Architecture

### Backend (Asynchronous & Scalable)
- **Python & FastAPI:** High-performance, asynchronous framework handling core routing and business logic.
- **WebSockets:** Powering bi-directional, ultra-low latency real-time communication for instant messaging.
- **SQLAlchemy (Async ORM):** Efficient database management, schema definitions, and relationship mapping.
- **SQLite:** Lightweight relational database utilized for local and production deployment data storage.
- **Brevo API (HTTP Client):** Integrated third-party service ensuring secure and reliable 2FA/OTP email delivery.

### Frontend (Responsive & Interactive)
- **React.js:** Building a fast, component-based, single-page application (SPA) experience.
- **JavaScript (ES6+), HTML5, CSS3:** Delivering sleek styling, modern animations, and dynamic UI updates.

---

## ✨ Core Features

* **Secure Authentication & 2FA:** User registration and login protected with industry-standard password hashing, reinforced with secure 2-Factor Authentication via email verification (OTP).
* **Real-Time Global Chat:** Fully optimized clean chat interface leveraging WebSockets for instant message broadcasting.
* **Comprehensive Admin Dashboard:** An analytical command center providing administrators full visibility over system metrics, user data, and infrastructure statistics represented through interactive charts and graphs.
* **User Profile Management:** Dedicated interfaces for user profiles, including an intuitive "Edit Profile" engine allowing secure account credential and info updates.
* **Contact & Support Engine:** Integrated contact interface enabling seamless communication between users and platform administrators.

---

## 📈 Database Schema & Security Standards
- **Password Security:** Multi-layered credential security using modern hashing algorithms (e.g., bcrypt/passlib) before database persistence.
- **Session Protection:** Route guards enforced at both backend (FastAPI dependencies) and frontend layers to prevent unauthorized endpoint access.

---

## ⚙️ Installation & Local Setup

To run this project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/iliiz/chatApp.git](https://github.com/iliiz/chatApp.git)
   cd chatApp
