/**
 * Chat Type Definitions
 * 
 * These types define the structure of chat-related requests and responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

/**
 * Chat request payload
 * Sent to POST /chat/chat and POST /chat/stream
 * Used to send a message to an AI agent
 */
export interface ChatRequest {
  message: string;
  agent_type?: string;
}

/**
 * Chat response
 * Returned by POST /chat/chat
 * Contains the agent's response and conversation metadata
 */
export interface ChatResponse {
  response: string;
  agent_type: string;
  conversation_id: string;
  tools_used: string[];
}

/**
 * Chat history response
 * Returned by GET /chat/history
 * Contains list of messages and total count
 */
export interface ChatHistoryResponse {
  messages: MessageDict[];
  total: number;
}

/**
 * Individual message in chat history
 * Represents a single message in the conversation
 */
export interface MessageDict {
  role: string;
  content: string;
  agent_type: string | null;
  created_at: string;
}

/**
 * Structured error for chat service
 * Used to provide detailed error information to UI components
 */
export interface ChatServiceError {
  status: number;
  code?: string;
  message: string;
  redirect?: string;
}
