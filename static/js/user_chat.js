let currentRoom = null;
let socket = null;
let logged_in_uuid_code = null;
let username = null;

document.getElementById("login-button").addEventListener("click", async () => {
    const usernameInput = document.getElementById("username").value.trim();
    const passwordInput = document.getElementById("password").value.trim();
    if (!usernameInput || !passwordInput) {
        document.getElementById("error-message").innerText = "Please enter both username and password"
        return;
    }
    try {
        const response = await fetch("/api/v1/auth/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ email: usernameInput, password: passwordInput })
        });
        if (response.ok) {
            const data = await response.json();
            username = data.full_name;
            email = data.email;
            logged_in_uuid_code = data.uuid_code;

            document.getElementById("login-box").style.display = "none";
            document.getElementById("chat-container").style.display = "flex";

            socket = io("/user-chat");
            socket.emit("user_joined", { email: email });

            socket.on("return_fetched_users", (users) => {
                const userList = document.getElementById("user-list");
                userList.innerHTML = "";
                users.forEach((user) => {
                    const userDiv = document.createElement("li");
                    userDiv.className = "user";
                    let full_name = user.full_name
                    if (full_name == username){
                        full_name = full_name + "(You)"
                    }
                    userDiv.textContent = full_name;
                    userDiv.dataset.uuid = user.uuid_code;
                    userList.appendChild(userDiv);
                });
            });
        }
        else {
            document.getElementById("error-message").innerText = "Invalid username or password"
        }
    }
    catch (error) {
        alert("An error occurred. Please try again.");
    }

    document.getElementById("user-list").addEventListener("click", (event) => {
        if (event.target.classList.contains("user")) {
            const targetUUID = event.target.dataset.uuid;
            socket.emit("create_room", { target_uuid: targetUUID, logged_in_uuid_code: logged_in_uuid_code });
        }
    });

    socket.on("room_created_success", (data) => {
        currentRoom = data.room;
        document.getElementById("chat-box").innerHTML = "";
        socket.emit("fetch_history", { room: currentRoom });
    });

    socket.on("chat_history", (data) => {
        const chatBox = document.getElementById("chat-box");
        chatBox.innerHTML = "";
        data.history.forEach((msg) => {
            addMessage(msg.username, msg.message, msg.created_date);
        });
    });

    document.getElementById("send-button").addEventListener("click", sendMessage);

    function sendMessage() {
        const messageInput = document.getElementById("message-input");
        const message = messageInput.value.trim();
        if (!message || !currentRoom) return;

        socket.emit("send_message", { room: currentRoom, message, username });
        messageInput.value = "";
    }


    socket.on("new_message", (data) => {
        addMessage(data.username, data.message, data.created_date);
    });


    function addMessage(user, message, timestamp) {
        const chatBox = document.getElementById("chat-box");
        const messageDiv = document.createElement("div");
        messageDiv.className = "message";
        messageDiv.textContent = `${user}: ${message} (${new Date(timestamp).toLocaleTimeString()})`;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});
