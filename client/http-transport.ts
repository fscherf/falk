export class HTTPTransport {
  private headers = {
    "Content-Type": "application/json",
    "X-Falk-Request-Type": "mutation",
  };

  public setHeader = (name: string, value: string): void => {
    this.headers[name] = value;
  };

  public sendMutationRequest = async (args: {
    nodeId: string;
    token: string;
    callbackName: string;
    callbackArgs: object;
    eventData: any;
  }): Promise<any> => {
    return new Promise(async (resolve, reject) => {
      const data = {
        // TODO: `requestType` is obsolete because we use a header for this now
        requestType: "falk/mutation",
        nodeId: args.nodeId,
        token: args.token,
        callbackName: args.callbackName,
        callbackArgs: args.callbackArgs,
        event: args.eventData.eventData,
      };

      const response = await fetch(window.location + "", {
        method: "POST",
        headers: this.headers,
        body: JSON.stringify(data),
        redirect: "manual",
      });

      if (!response.ok) {
        reject(`HTTP error! Status: ${response.status}`);
      }

      const responseData = await response.json();

      // handle reloads
      if (responseData.flags.reload) {
        window.location.reload();
      }

      resolve(responseData);
    });
  };

  public sendMultipartMutationRequest = async (args: {
    nodeId: string;
    token: string;
    callbackName: string;
    callbackArgs: object;
    eventData: any;
  }): Promise<any> => {
    return new Promise(async (resolve, reject) => {
      const body: FormData = new FormData();

      // data
      const data = {
        // TODO: `requestType` is obsolete because we use a header for this now
        requestType: "falk/mutation",
        nodeId: args.nodeId,
        token: args.token,
        callbackName: args.callbackName,
        callbackArgs: args.callbackArgs,
        event: args.eventData.eventData,
      };

      body.append("falk/mutation", JSON.stringify(data));

      // files
      for (const { key, file } of args.eventData.files) {
        body.append(key, file);
      }

      const response = await fetch(window.location + "", {
        method: "POST",
        headers: {
          "X-Falk-Request-Type": "mutation",
          "X-Falk-Upload-Token": args.eventData.uploadToken,
        },
        body: body,
        redirect: "manual",
      });

      if (!response.ok) {
        reject(`HTTP error! Status: ${response.status}`);
      }

      const responseData = await response.json();

      // handle reloads
      if (responseData.flags.reload) {
        window.location.reload();
      }

      resolve(responseData);
    });
  };
}
