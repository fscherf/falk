import { MutationRequestResponse } from "./types";

export class WebsocketTransport {
  private websocket: WebSocket | undefined;
  private messageIdCounter: number;

  private pendingRequests: Map<
    number,
    {
      resolve: (value: any) => void;
      reject: (reason?: any) => void;
    }
  >;

  public available: boolean;

  public init = async () => {
    this.available = await this.connect();
  };

  constructor() {
    this.websocket = undefined;
    this.available = false;
    this.messageIdCounter = 1;
    this.pendingRequests = new Map();
  }

  private handleMessage = (event: MessageEvent) => {
    const [messageId, messageData] = JSON.parse(event.data);
    const responseData = messageData.json;
    const promiseCallbacks = this.pendingRequests.get(messageId);

    if (!promiseCallbacks) {
      throw `unknown message id: ${messageId}`;
    }

    const mutationRequestResponse: MutationRequestResponse = {
      valid: true,
      httpResponse: null,
    };

    try {
      mutationRequestResponse.flags = responseData.flags;
      mutationRequestResponse.body = responseData.body;
      mutationRequestResponse.tokens = responseData.tokens;
      mutationRequestResponse.callbacks = responseData.callbacks;
    } catch {
      mutationRequestResponse.valid = false;
    }

    // HTML responses
    promiseCallbacks["resolve"](mutationRequestResponse);

    this.pendingRequests.delete(messageData);
  };

  private connect = (): Promise<boolean> => {
    return new Promise((resolve) => {
      try {
        this.websocket = new WebSocket(
          `${window.location.protocol}//${window.location.host}${window.location.pathname}`,
        );
      } catch {
        resolve(false);

        return;
      }

      this.websocket.addEventListener("message", this.handleMessage);

      this.websocket.addEventListener("open", () => {
        this.messageIdCounter = 1;
        this.pendingRequests = new Map();

        resolve(true);
      });

      this.websocket.addEventListener("error", (event) => {
        resolve(false);
      });
    });
  };

  public sendMutationRequest = async (args: {
    nodeId: string;
    token: string;
    callbackName: string;
    callbackArgs: object;
    eventData: any;
  }): Promise<MutationRequestResponse> => {
    return new Promise(async (resolve, reject) => {
      // connect websocket if necessary
      if (
        !this.websocket ||
        this.websocket.readyState !== this.websocket.OPEN
      ) {
        await this.connect();
      }

      if (!this.websocket) {
        // FIXME: if this happens we should flag this transport as unavailable
        // and retry the request using HTTP.

        throw "websocket not available";
      }

      // send request
      const data = {
        nodeId: args.nodeId,
        token: args.token,
        callbackName: args.callbackName,
        callbackArgs: args.callbackArgs,
        event: args.eventData.eventData,
      };

      const messageId: number = this.messageIdCounter;
      const message: string = JSON.stringify([messageId, data]);

      this.messageIdCounter += 1;

      this.websocket.send(message);

      this.pendingRequests.set(messageId, {
        resolve: resolve,
        reject: reject,
      });
    });
  };
}
