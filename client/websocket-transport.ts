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

    // handle reloads
    if (responseData.flags.reload) {
      window.location.reload();
    }

    // HTML responses
    promiseCallbacks["resolve"](responseData);

    this.pendingRequests.delete(messageData);
  };

  private connect = (): Promise<boolean> => {
    return new Promise((resolve) => {
      this.websocket = new WebSocket(window.location + "");

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
  }): Promise<any> => {
    return new Promise(async (resolve, reject) => {
      // connect websocket if necessary
      if (this.websocket.readyState !== this.websocket.OPEN) {
        await this.connect();
      }

      // send request
      const data = {
        // TODO: `requestType` is obsolete because we use a header for this now
        requestType: "falk/mutation",
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
