const BASE_URL = 'http://localhost:8000'; // FastAPI dev port

export interface ApiError {
  code: string;
  message: string;
}

export class ApiRequestError extends Error {
  status: number;
  code: string;

  constructor(status: number, errorObj: ApiError) {
    super(errorObj.message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.code = errorObj.code;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorPayload: any = {};
    try {
      errorPayload = await response.json();
    } catch {
      // JSON parsing failed
    }

    let code = 'HTTP_ERROR';
    let message = response.statusText || `Request failed with status ${response.status}`;

    if (errorPayload && errorPayload.detail) {
      if (typeof errorPayload.detail === 'object') {
        code = errorPayload.detail.code || 'HTTP_ERROR';
        message = errorPayload.detail.message || JSON.stringify(errorPayload.detail);
      } else if (typeof errorPayload.detail === 'string') {
        code = 'VALIDATION_ERROR';
        message = errorPayload.detail;
      }
    } else if (errorPayload && errorPayload.error) {
      code = errorPayload.error.code || 'HTTP_ERROR';
      message = errorPayload.error.message || message;
    }

    throw new ApiRequestError(response.status, { code, message });
  }

  // Handle empty responses
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const apiClient = {
  get: async <T>(url: string): Promise<T> => {
    const response = await fetch(`${BASE_URL}${url}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Mandated for cookie-based session auth
    });
    return handleResponse<T>(response);
  },

  post: async <T>(url: string, body?: any): Promise<T> => {
    const response = await fetch(`${BASE_URL}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
      credentials: 'include',
    });
    return handleResponse<T>(response);
  },

  delete: async <T>(url: string): Promise<T> => {
    const response = await fetch(`${BASE_URL}${url}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    return handleResponse<T>(response);
  },

  download: async (url: string, filename: string): Promise<void> => {
    const response = await fetch(`${BASE_URL}${url}`, {
      method: 'GET',
      credentials: 'include',
    });
    
    if (!response.ok) {
      let errorPayload: any = {};
      try {
        errorPayload = await response.json();
      } catch {}
      
      let code = 'HTTP_ERROR';
      let message = response.statusText || `Request failed with status ${response.status}`;
      
      if (errorPayload && errorPayload.detail) {
        if (typeof errorPayload.detail === 'object') {
          code = errorPayload.detail.code || 'HTTP_ERROR';
          message = errorPayload.detail.message || JSON.stringify(errorPayload.detail);
        } else if (typeof errorPayload.detail === 'string') {
          code = 'VALIDATION_ERROR';
          message = errorPayload.detail;
        }
      } else if (errorPayload && errorPayload.error) {
        code = errorPayload.error.code || 'HTTP_ERROR';
        message = errorPayload.error.message || message;
      }
      throw new ApiRequestError(response.status, { code, message });
    }
    
    const blob = await response.blob();
    const objectUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(objectUrl);
  },
};
