/* --- Chatbot Logic --- */
const chatbotToggler = document.querySelector(".chatbot-toggler");
const closeBtn = document.querySelector(".close-btn");
const chatbox = document.querySelector(".chatbox");
const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");

let userMessage = null; // Variable to store user's message
const inputInitHeight = chatInput.scrollHeight;

// Load chat history and state from local storage on boot
const loadChatHistory = () => {
    const savedChat = localStorage.getItem("chat-history");
    const isChatOpen = localStorage.getItem("is-chat-open") === "true";

    if (savedChat) {
        chatbox.innerHTML = savedChat;
    }

    if (isChatOpen) {
        document.body.classList.add("show-chatbot");
    }
}

const saveChatHistory = () => {
    localStorage.setItem("chat-history", chatbox.innerHTML);
}

const createChatLi = (message, className) => {
    // Create a chat <li> element with passed message and className
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", className);
    let chatContent = className === "outgoing" ? `<p></p>` : `<span class="material-symbols-rounded">smart_toy</span><p></p>`;
    chatLi.innerHTML = chatContent;
    chatLi.querySelector("p").textContent = message;
    return chatLi; // return chat <li> element
}

const generateResponse = (chatElement) => {
    const API_URL = "/api/chat";
    const messageElement = chatElement.querySelector("p");

    const requestOptions = {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            message: userMessage
        })
    }

    // Send POST request to API, get response and set the reponse as paragraph text
    fetch(API_URL, requestOptions).then(res => res.json()).then(data => {
        if (data.success) {
            messageElement.textContent = data.response.trim();
        } else {
            messageElement.textContent = data.response || "Oops! Something went wrong. Please try again.";
            messageElement.classList.add("error");
        }
    }).catch(() => {
        messageElement.textContent = "Oops! Something went wrong. Please try again.";
        messageElement.classList.add("error");
    }).finally(() => {
        chatbox.scrollTo(0, chatbox.scrollHeight);
        saveChatHistory(); // Save after response
    });
}

const handleChat = () => {
    userMessage = chatInput.value.trim(); // Get user entered message and remove extra whitespace
    if (!userMessage) return;

    // Clear the input textarea and set its height to default
    chatInput.value = "";
    chatInput.style.height = `${inputInitHeight}px`;

    // Append the user's message to the chatbox
    chatbox.appendChild(createChatLi(userMessage, "outgoing"));
    chatbox.scrollTo(0, chatbox.scrollHeight);
    saveChatHistory(); // Save after user message

    // Display "Thinking..." message while waiting for the response
    setTimeout(() => {
        const incomingChatLi = createChatLi("Thinking...", "incoming");
        chatbox.appendChild(incomingChatLi);
        chatbox.scrollTo(0, chatbox.scrollHeight);
        generateResponse(incomingChatLi);
    }, 600);
}

chatInput.addEventListener("input", () => {
    // Adjust the height of the input textarea based on its content
    chatInput.style.height = `${inputInitHeight}px`;
    chatInput.style.height = `${chatInput.scrollHeight}px`;
});

chatInput.addEventListener("keydown", (e) => {
    // If Enter key is pressed without Shift key and the window is 
    // width greater than 800px, handle the chat
    if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
        e.preventDefault();
        handleChat();
    }
});

sendChatBtn.addEventListener("click", handleChat);
closeBtn.addEventListener("click", () => {
    document.body.classList.remove("show-chatbot");
    localStorage.setItem("is-chat-open", "false");
});
chatbotToggler.addEventListener("click", () => {
    document.body.classList.toggle("show-chatbot");
    const isOpen = document.body.classList.contains("show-chatbot");
    localStorage.setItem("is-chat-open", isOpen);
});

// Initial load
loadChatHistory();
