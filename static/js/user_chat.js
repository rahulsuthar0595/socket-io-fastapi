let currentRoom = null;
let socket = null;
let logged_in_uuid_code = null;
let username = null;

let currentUser = { id: null, name: null};

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

            currentUser = { id: data._id, name: data.full_name};

            document.getElementById("login-box").style.display = "none";
            document.getElementById("chat-container").style.display = "flex";

            socket = io("/user-chat");
            socket.emit("user_joined", { email: email });

            socket.on("return_user_list", (users) => {
                const userList = document.getElementById("user-list");
                userList.innerHTML = "";
                users.forEach((user) => {
                    const userDiv = document.createElement("li");
                    userDiv.className = "user";
                    currentRoom = user._id
                    let full_name = user.full_name
                    if (full_name == username){
                        full_name = full_name + "(You)"
                    }
                    userDiv.textContent = full_name;
                    userDiv.dataset.uuid = user.uuid_code;
                    userList.appendChild(userDiv);
                });
            });
            socket.on("return_group_list", (groups) => {
                const groupList = document.getElementById("group-list");
                const groupSidebar = document.getElementById("group-sidebar");
                groupSidebar.style = "";
                groupList.innerHTML = "";
                groups.forEach((group) => {
                    const groupItem = document.createElement("li");
                    groupItem.textContent = group.group_name;
                    groupItem.dataset.id = group._id;
                    groupItem.addEventListener("click", () => {
                        currentRoom = group._id + "_GROUP";
                        socket.emit("user_group_joined", { user_uuid: currentUser.id, group_id: group._id });
                        document.getElementById("chat-box").innerHTML = ""; // Clear previous messages
                        socket.emit("group_chat_history", { group_id: group._id });
                    });
                    groupList.appendChild(groupItem);
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

    socket.on("group_message", (data) => {
        addMessage(data.message, data.user_id);
    });

    // Create Group
    document.getElementById("create-group-btn").addEventListener("click", () => {
        const groupName = document.getElementById("new-group-name").value.trim();
        if (groupName) {
            socket.emit("chat_group_create", { user_uuid: currentUser.id, group_name: groupName });
            document.getElementById("new-group-name").value = ""; // Clear input
        }
    });


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
        if (!message || !currentRoom) {
            return null;
        }

        if (currentRoom.split("_").length == 2){
            socket.emit("group_chat_message", { sender_uuid: currentUser.id, group_id: currentRoom.split("_")[0], message: message });
        }
        else{
            socket.emit("direct_message_to_user", { sender_uuid: currentUser.id, receiver_uuid: currentRoom.split("_")[0], message: message });
        }
        messageInput.value = "";
    }

    socket.on("group_chat_list", (data) => {
        data.messages.forEach((msg) => addMessage(msg.message, msg.user_id));
    });

    socket.on("new_message", (data) => {
        addMessage(data.username, data.message, data.created_date);
    });


    function addMessage(text, sender) {
        const messagesDiv = document.getElementById("chat-box");
        const messageDiv = document.createElement("div");
        messageDiv.className = "message";
        messageDiv.innerHTML = `<span>${sender}:</span> ${text}`;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
});
