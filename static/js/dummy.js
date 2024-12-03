//let activeTab = "users";
//        let chatData = {
//            users: [],
//            groups: []
//        };
//        let groupMembers = {}
////        let groupMembers = {
////            Group1: ["User1", "User2"],
////            Group2: ["User2", "User3"],
////            Group3: ["User1", "User3"]
////        };
//
//        function switchTab(tab) {
//            activeTab = tab;
//            // Remove active class from all tabs
//            document.querySelectorAll(".tab").forEach(tabEl => tabEl.classList.remove("active"));
//            // Add active class to the selected tab based on its text content
//            document.querySelectorAll(".tab").forEach(tabEl => {
//                if (tabEl.textContent.trim().toLowerCase() === tab) {
//                    tabEl.classList.add("active");
//                }
//            });
//            populateList();
//        }
//
//        function populateList() {
//            const listContainer = document.getElementById("list-container");
//            listContainer.innerHTML = "";
//            chatData[activeTab].forEach(item => {
//                const listItem = document.createElement("div");
//                listItem.className = "list-item";
//                listItem.textContent = item;
//                listItem.onclick = () => openChat(item);
//                listContainer.appendChild(listItem);
//            });
//        }
//
//        function openChat(name) {
//            document.getElementById("chat-header").textContent = `Chat with ${name}`;
//            document.getElementById("chat-messages").innerHTML = `<div>Chat started with ${name}</div>`;
//            if (activeTab === "groups") {
//                populateGroupMembers(name);
//            } else {
//                document.getElementById("sidebar").style.display = "none";
//            }
//        }
//
//        function populateGroupMembers(group) {
//            document.getElementById("sidebar").style.display = "block";
//            const groupUsersContainer = document.getElementById("group-users");
//            groupUsersContainer.innerHTML = "";
//            (groupMembers[group] || []).forEach(member => {
//                const userItem = document.createElement("div");
//                userItem.className = "user-item";
//                userItem.textContent = member;
//                groupUsersContainer.appendChild(userItem);
//            });
//        }
//
//        function sendMessage() {
//            const message = document.getElementById("chat-input").value;
//            if (!message) return;
//            const chatMessages = document.getElementById("chat-messages");
//            const newMessage = document.createElement("div");
//            newMessage.textContent = `You: ${message}`;
//            chatMessages.appendChild(newMessage);
//            document.getElementById("chat-input").value = "";
//        }
//
//        // Initialize the app
//        populateList();


let socket = io();
let activeTab = "users";
let currentUserData = {};
let currentRoom = null;

let chatData = {
    users: [],
    groups: []
};

function showMainContainer() {
    document.getElementById("login-container").style.display = "none";
    document.getElementById("main-container").style.display = "flex";
}

function showLoginContainer() {
    document.getElementById("login-container").style.display = "flex";
    document.getElementById("main-container").style.display = "none";
}

async function validateToken() {
    const token = JSON.parse(localStorage.getItem("user_data"));
    if (!token) {
        showLoginContainer();
        return;
    }
    // TODO: Add API to check local storage user data validate or access token
    currentUserData = token
    showMainContainer();
    socket.emit("user_joined", {});
}

async function login() {
    const email = document.getElementById("login_email").value;
    const password = document.getElementById("login_password").value;

    if (!email || !password) return;

    const formData = {
        "email": email,
        "password": password,
    }

    try {
        const response = await fetch("/api/v1/auth/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            localStorage.setItem("user_data", JSON.stringify(result));
            currentUserData = result
            showMainContainer();
            socket.emit("user_joined", { email: result.email });
        } else {
            alert(result.detail || "Login failed");
        }
    } catch (error) {
        console.error("Login error:", error);
        alert("Login failed. Please try again.");
    }
}

function populateList() {
    const listContainer = document.getElementById("list-container");
    listContainer.innerHTML = "";
    chatData[activeTab].forEach(item => {
        const listItem = document.createElement("div");
        listItem.className = "list-item";

        if (activeTab == "users") {
            if (currentUserData.full_name == item.full_name){
                full_name = item.full_name + "(You)"
            }else{
                full_name = item.full_name
            }
            listItem.textContent = full_name;
        }else{
            listItem.textContent = item.group_name;
        }
        listItem.onclick = () => openChat(item);
        listContainer.appendChild(listItem);
    });
}

function switchTab(tab) {
    activeTab = tab
    document.querySelectorAll(".tab").forEach(tabEl => tabEl.classList.remove("active"));
    document.querySelectorAll(".tab").forEach(tabEl => {
        if (tabEl.textContent.trim().toLowerCase() === tab) {
            tabEl.classList.add("active");
        }
    });
    populateList();
}

function openChat(data) {
    document.getElementById("chat-header").textContent = `Chat with ${data.full_name}`;
    document.getElementById("chat-messages").innerHTML = `<div>Chat started with ${data.full_name}</div>`;
    socket.emit("direct_messages_history", {"sender_uuid": currentUserData._id, "receiver_uuid": data._id})
    currentRoom = data._id;
}

function sendMessage() {
    const message = document.getElementById("chat-input").value;
    if (!message) return;
    const chatMessages = document.getElementById("chat-messages");
    const newMessage = document.createElement("div");
    newMessage.textContent = `You: ${message}`;
    chatMessages.appendChild(newMessage);
    document.getElementById("chat-input").value = "";

    if (activeTab == "users"){
        socket.emit("direct_message_to_user", {"sender_uuid": currentUserData._id, "receiver_uuid": currentRoom, "message": message});
    }
    else{
        socket.emit("group_chat_message", {"sender_uuid": currentUserData._id, "group_id": currentRoom, "message": message});
    }

}

socket.on("return_joined_data_list", (data) => {
    chatData = {
        "users": data.users,
        "groups": data.groups,
    }
    populateList()
});


socket.on("direct_messages", (data) => {
    let messages = data.messages;
    const listContainer = document.getElementById("chat-messages")
    messages.forEach(item => {
        const listItem = document.createElement("div");
        listItem.className = "list-item";
        if (item.sender == currentUserData._id){
            text = "You: " + item.message;
        }
        else{
            text = item.sender + ": " + item.message;
        }
        listItem.textContent = text;
        listContainer.appendChild(listItem);
    });
});


validateToken();