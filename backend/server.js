require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const mqtt = require('mqtt');
const cors = require('cors');
const nodemailer = require('nodemailer');

const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

// --- DATABASE CONNECT ---
mongoose.connect(process.env.MONGO_URI)
    .then(() => console.log("MongoDB Connected"))
    .catch(err => console.error("MongoDB Error:", err));

// --- SCHEMAS & MODELS ---
const Log = mongoose.model('Log', new mongoose.Schema({
    user: String, status: String, method: String, timestamp: { type: Date, default: Date.now }
}));

const User = mongoose.model('User', new mongoose.Schema({
    name: String, image: String, enrolledAt: { type: Date, default: Date.now }
}));

// --- NODEMAILER CONFIGURATION ---
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: process.env.EMAIL_USER, // Set this in your .env file
        pass: process.env.EMAIL_PASS  // Your 16-character Google App Password
    }
});

// Helper function to send email security alerts
const sendSecurityEmail = async (logData) => {
    const mailOptions = {
        from: `"AI Gate Security System" <${process.env.EMAIL_USER}>`,
        to: 'chahine.justin@gmail.com',
        subject: 'SECURITY ALERT: Unauthorized Access Blocked',
        text: `Security Notification:\nAn unauthorized access attempt was detected.\nMethod: ${logData.method}\nTime: ${new Date().toLocaleString()}`,
        html: `
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ff4d4d; border-radius: 8px; max-width: 500px;">
                <h2 style="color: #d9534f; margin-top: 0;">Breach Attempt Blocked</h2>
                <p><strong>System Status:</strong> ACCESS DENIED</p>
                <p><strong>Authentication Method:</strong> ${logData.method || 'Unknown'}</p>
                <p><strong>Target User Identity:</strong> ${logData.user || 'Unknown'}</p>
                <p><strong>Timestamp:</strong> ${new Date().toLocaleString()}</p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #777;">This is an automated response from your Oracle Cloud AI Gate framework.</p>
            </div>
        `
    };

    try {
        await transporter.sendMail(mailOptions);
        console.log("Security alert email sent to chahine.justin@gmail.com");
    } catch (err) {
        console.error("Failed to send security email:", err.message);
    }
};

// --- MQTT MODULE ---
const mqttClient = mqtt.connect('mqtt://127.0.0.1:1883');

mqttClient.on('connect', () => {
    mqttClient.subscribe(['security/logs']);
    console.log("MQTT Linked");
});

mqttClient.on('message', async (topic, message) => {
    if (topic === 'security/logs') {
        try {
            const data = JSON.parse(message.toString());
            
            // Save log to MongoDB database
            await new Log(data).save();

            // Trigger Nodemailer alert automatically if the status is DENIED
            if (data.status === "DENIED") {
                sendSecurityEmail(data);
            }
        } catch (e) { 
            console.log("Log Error"); 
        }
    }
});

// --- HTTP API ROUTES ---

// GET Logs with Pagination
app.get('/api/logs', async (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const limit = 10;
    const skip = (page - 1) * limit;
    try {
        const logs = await Log.find().sort({ timestamp: -1 }).skip(skip).limit(limit);
        const total = await Log.countDocuments();
        res.json({ logs, totalPages: Math.ceil(total / limit), currentPage: page });
    } catch (err) { res.status(500).send(err); }
});

// GET All Registered Users
app.get('/api/users', async (req, res) => {
    const users = await User.find().sort({ enrolledAt: -1 });
    res.json(users);
});

// POST Enroll New User
app.post('/api/users', async (req, res) => {
    const { name, image } = req.body;
    try {
        const newUser = new User({ name, image });
        await newUser.save();
        const cleanBase64 = image.split(',')[1];
        mqttClient.publish('security/add_user', JSON.stringify({ name: name.toLowerCase(), image: cleanBase64 }));
        res.json({ status: "Enrolled", name });
    } catch (err) { res.status(500).json({ error: "Save failed" }); }
});

// DELETE User
app.delete('/api/users/:id', async (req, res) => {
    try {
        const user = await User.findById(req.params.id);
        if (!user) return res.status(404).send("User not found");
        mqttClient.publish('security/delete_user', JSON.stringify({ name: user.name.toLowerCase() }));
        await User.findByIdAndDelete(req.params.id);
        res.json({ status: "Deleted" });
    } catch (err) { res.status(500).send(err); }
});

// POST Remote Override Gate Command
app.post('/api/control', (req, res) => {
    mqttClient.publish('security/control', req.body.command);
    res.json({ status: "Sent" });
});

// --- ENGINE EXECUTION ---
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log("Server spinning on port " + PORT));