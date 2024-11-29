const socket = io("/");
const adminSocket = io("/admin");

function addMessage(text) {
    const messagesDiv = document.getElementById("log");
    const messageDiv = document.createElement("div");
    messageDiv.className = "message";
    messageDiv.textContent = text;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Default Namespace Events
socket.on("connect", function() {
    socket.emit("welcome_user", { data: "I'm connected!" });
});

socket.on("disconnect", function() {
    addMessage("You are disconnected.");
});

socket.on("return_response", function(data) {
    addMessage(`[Default Namespace] ${data.data}`);
});

// Admin Namespace Events
adminSocket.on("connect", function() {
    addMessage("Connected to Admin namespace.");
});

adminSocket.on("disconnect", function() {
    addMessage("Disconnected from Admin namespace.");
});

adminSocket.on("return_response", function(data) {
    addMessage(`[Admin Namespace] ${data.data}`);
});

// Default Namespace Form Handlers
document.getElementById("emit").addEventListener("submit", function(event) {
    event.preventDefault();
    socket.emit("custom_event", { data: document.getElementById("emit_data").value });
});

document.getElementById("broadcast").addEventListener("submit", function(event) {
    event.preventDefault();
    socket.emit("broadcast", { data: document.getElementById("broadcast_data").value });
});

document.getElementById("join").addEventListener("submit", function(event) {
    event.preventDefault();
    socket.emit("join", { room: document.getElementById("join_room").value });
});

document.getElementById("leave").addEventListener("submit", function(event) {
    event.preventDefault();
    socket.emit("leave", { room: document.getElementById("leave_room").value });
});

document.getElementById("send_room").addEventListener("submit", function(event) {
    event.preventDefault();
    socket.emit("room_chat", {
        room: document.getElementById("room_name").value,
        data: document.getElementById("room_data").value
    });
});

document.getElementById("close").addEventListener("submit", function(event) {
    event.preventDefault();
    socket.emit("close_room", { room: document.getElementById("close_room").value });
});

document.getElementById("list_rooms").addEventListener("submit", function(event) {
    event.preventDefault();
    socket.emit("list_rooms", { room: "" });
});

// Admin Namespace Form Handlers
document.getElementById("admin_broadcast").addEventListener("submit", function(event) {
    event.preventDefault();
    adminSocket.emit("broadcast", { data: document.getElementById("admin_broadcast_data").value });
});