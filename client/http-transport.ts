import { MutationRequestResponse } from "./types";

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
  }): Promise<MutationRequestResponse> => {
    return new Promise(async (resolve, reject) => {
      const data = {
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

      const mutationRequestResponse: MutationRequestResponse = {
        valid: true,
        httpResponse: response,
      };

      try {
        const responseData = await response.json();

        mutationRequestResponse.flags = responseData.flags;
        mutationRequestResponse.body = responseData.body;
        mutationRequestResponse.tokens = responseData.tokens;
        mutationRequestResponse.callbacks = responseData.callbacks;
      } catch {
        mutationRequestResponse.valid = false;
      }

      resolve(mutationRequestResponse);
    });
  };

  public sendMultipartMutationRequest = async (args: {
    nodeId: string;
    token: string;
    callbackName: string;
    callbackArgs: object;
    eventData: any;
  }): Promise<MutationRequestResponse> => {
    return new Promise(async (resolve, reject) => {
      const body: FormData = new FormData();

      // data
      const data = {
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

      const mutationRequestResponse: MutationRequestResponse = {
        valid: true,
        httpResponse: response,
      };

      try {
        const responseData = await response.json();

        mutationRequestResponse.flags = responseData.flags;
        mutationRequestResponse.body = responseData.body;
        mutationRequestResponse.tokens = responseData.tokens;
        mutationRequestResponse.callbacks = responseData.callbacks;
      } catch {
        mutationRequestResponse.valid = false;
      }

      resolve(mutationRequestResponse);
    });
  };
}
