"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Form from "next/form";
import DeleteModal from "./DeleteModal";
import { postAIMessageAction, getAIMessageAction } from "@/actions/chatActions";
import styles from "./ChatModal.module.css";

const generateTempMessage = (content) => {
  return {
    id: window.crypto?.randomUUID
      ? window.crypto.randomUUID()
      : `temp-${Date.now()}`,
    role: "user",
    content: content,
    timestamp: new Date().toISOString(),
  };
};

export default function ChatOverlay({ sessionData, onClose }) {
  const backIcon = "/assets/back-button.svg";
  const deleteIcon = "/assets/trash-icon.svg";
  const sendIcon = "/assets/send-button.svg";
  const gifUrl = "/assets/loading-chat.gif";
  const bot = "/assets/chat-bot-loading.svg";

  const [messages, setMessages] = useState(() => {
    if (
      sessionData.user_message_count === 0 ||
      !sessionData.messages ||
      sessionData.messages.length === 0
    ) {
      return [
        {
          id: "w1",
          role: "ai",
          content: "Hello, User!!",
          timestamp: new Date().toISOString(),
        },
        {
          id: "w2",
          role: "ai",
          content: "Tell me how can I help you message",
          timestamp: new Date().toISOString(),
        },
      ];
    }
    return sessionData.messages;
  });

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [messageCount, setMessageCount] = useState(
    sessionData.user_message_count || 0,
  );
  const [isTyping, setIsTyping] = useState(false);
  const [pendingText, setPendingText] = useState("");
  const [errorText, setErrorText] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [streamingMessageId, setStreamingMessageId] = useState(null);
  const [displayedContent, setDisplayedContent] = useState({});

  const scrollRef = useRef(null);
  const isMounted = useRef(true);

  const suggestions = [
    "Can you give me a summary of the property features including the area and price?",
    "What are the specific beds and baths details for this report?",
    "Does the price per sqft represent a good value for this area?",
  ];

  const typeMessage = (messageId, fullText) => {
    const words = fullText.split(" ");
    let currentText = "";
    setStreamingMessageId(messageId);

    words.forEach((word, index) => {
      setTimeout(() => {
        if (!isMounted.current) return;
        currentText += (index === 0 ? "" : " ") + word;
        setDisplayedContent((prev) => ({ ...prev, [messageId]: currentText }));

        if (index === words.length - 1) {
          setStreamingMessageId(null);
          setIsTyping(false);
          setPendingText("");
        }
      }, index * 50);
    });
  };

  const openDeleteModal = () => {
    setIsDeleteModalOpen(true);
    document.body.style.overflow = "hidden";
  };

  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false);
    document.body.style.overflow = "auto";
  };

  const pollForResponse = async (messageId) => {
    const executePoll = async () => {
      if (!isMounted.current) return;

      const response = await getAIMessageAction(messageId);

      if (response.pending) {
        setPendingText(response.pending);
        setTimeout(executePoll, 5000);
        setErrorText("");
        return;
      }

      if (response.success && response.data) {
        setTimeout(() => {
          if (!isMounted.current) return;
          setMessages((prev) => [...prev, response.data]);
          typeMessage(response.data.id, response.data.content);
          setPendingText("");
          setIsTyping(false);
        }, 1000);
      } else {
        setIsTyping(false);
        setPendingText("");
        setErrorText(response.error || "Failed to retrieve message.");
      }
    };
    executePoll();
  };

  const clientAction = async (formData) => {
    const content = formData.get("content");

    if (!content?.trim() || isTyping) return;

    const userMsg = generateTempMessage(content);

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsTyping(true);
    setPendingText("Thinking...");

    const data = new FormData();
    data.append("content", content);

    const result = await postAIMessageAction(sessionData.id, null, formData);

    if (result.data?.ai_message_id) {
      setMessageCount((prev) => prev + 1);
      pollForResponse(result.data.ai_message_id);
    } else {
      setErrorText(result.error);
      setIsTyping(false);
      setPendingText("");
    }
  };

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, isTyping, pendingText]);

  return (
    <div className={styles.overlay}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <button onClick={onClose} className={styles.backBtn}>
            <Image src={backIcon} alt="Back" width={30} height={30} />
          </button>
          <div className={styles.titleContainer}>
            <span className={styles.title}>
              Report ID #{sessionData.report}
            </span>
            <span className={styles.subtitle}>Smart Assistant</span>
          </div>
        </div>
        <button onClick={openDeleteModal} className={styles.deleteBtn}>
          <Image src={deleteIcon} alt="Delete" width={30} height={30} />
        </button>
      </div>

      <div className={styles.messageList} ref={scrollRef}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`${styles.messageWrapper} ${msg.role === "user" ? styles.user : styles.ai}`}
          >
            <div className={styles.bubble}>
              {msg.role === "ai" && streamingMessageId === msg.id
                ? displayedContent[msg.id]
                : msg.content}
              <div className={styles.timestamp}>
                {new Date(msg.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
          </div>
        ))}

        {messageCount === 0 && !isTyping && (
          <div className={styles.suggestionsContainer}>
            {suggestions.map((text, index) => (
              <button
                key={index}
                className={styles.suggestionChip}
                onClick={() => {
                  const data = new FormData();
                  data.append("content", text);
                  clientAction(data);
                }}
              >
                {text}
              </button>
            ))}
          </div>
        )}

        {messageCount > 10 && (
          <div className={styles.limitReached}>
            "We couldn't process your request right now. Our models are
            experiencing an unusually high volume of traffic and need a quick
            breather."
          </div>
        )}

        {errorText && (
          <div className={styles.messageWrapper}>
            <div className={styles.limitReached}>{errorText}</div>
          </div>
        )}

        {isTyping && (
          <div className={`${styles.messageWrapper} ${styles.ai}`}>
            <div className={styles.logoContainer}>
              <Image
                src={gifUrl}
                alt="Loading Animation"
                width={200}
                height={200}
                className={styles.gif}
                unoptimized
              />
              <Image
                src={bot}
                alt="Bot"
                width={200}
                height={200}
                className={styles.botLogo}
              />
            </div>
            <div className={`${styles.bubble} ${styles.typing}`}>
              Thinking
              <span className={styles.dots}>.</span>
            </div>
          </div>
        )}
      </div>

      <Form action={clientAction} className={styles.inputArea}>
        <div className={styles.inputWrapper}>
          <input
            name="content"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={isTyping ? pendingText : "Input query here"}
            className={styles.input}
            disabled={isTyping || messageCount >= 10}
          />
          <button
            type="submit"
            className={styles.sendBtn}
            disabled={isTyping || !inputValue.trim() || messageCount >= 10}
          >
            <Image src={sendIcon} alt="Send" width={30} height={30} />
          </button>
        </div>
      </Form>

      {isDeleteModalOpen && (
        <DeleteModal
          title="Are you sure you want to delete this chat? The chat history will be removed."
          userData={sessionData}
          userRole="Agent"
          actionName="deleteChat"
          onCancel={closeDeleteModal}
          onClose={onClose}
        />
      )}
    </div>
  );
}
