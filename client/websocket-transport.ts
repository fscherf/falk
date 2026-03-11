import { MutationRequestResponse } from "./types";

export class WebsocketTransport {
  private websocket: WebSocket;
  private messageIdCounter: number;

  private pendingRequests: Map<
    number,
    {
      resolve: (value: unknown) => void;
      reject: (reason?: unknown) => void;
    }
  >;

  public available: boolean;

  public init = async () => {
    this.available = await this.connect();
  };

  private handleMessage = (event: MessageEvent) => {
    const [messageId, messageData] = JSON.parse(event.data);
    const responseData = messageData.json;
    const promiseCallbacks = this.pendingRequests.get(messageId);

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
      if (this.websocket.readyState !== this.websocket.OPEN) {
        await this.connect();
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
