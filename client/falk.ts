import morphdom from "morphdom";

class Falk {
  private websocketsAvailable: boolean;
  private websocket: WebSocket;
  private websocketMessageIdCounter: number;

  private pendingWebsocketRequests: Map<
    number,
    {
      resolve: (value: unknown) => void;
      reject: (reason?: unknown) => void;
    }
  >;

  public init = async () => {
    this.websocketsAvailable = await this.connectWebsocket();

    this.runHook("render");
  };

  // request handling: AJAX
  public sendHttpRequest = async (data): Promise<string> => {
    return new Promise(async (resolve, reject) => {
      const response = await fetch(window.location + "", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        reject(`HTTP error! Status: ${response.status}`);
      }

      const responseText = await response.text();

      resolve(responseText);
    });
  };

  // request handling: websockets
  private handleWebsocketMessage = (event: MessageEvent) => {
    const [messageId, messageData] = JSON.parse(event.data);
    const promiseCallbacks = this.pendingWebsocketRequests.get(messageId);

    promiseCallbacks["resolve"](messageData["body"]);

    this.pendingWebsocketRequests.delete(messageId);
  };

  public connectWebsocket = async (): Promise<boolean> => {
    return new Promise(async (resolve, reject) => {
      this.websocket = new WebSocket(window.location + "");

      this.websocket.addEventListener("message", this.handleWebsocketMessage);

      this.websocket.addEventListener("open", () => {
        this.websocketMessageIdCounter = 1;
        this.pendingWebsocketRequests = new Map();

        resolve(true);
      });

      this.websocket.addEventListener("error", (event) => {
        resolve(false);
      });
    });
  };

  public sendWebsocketRequest = async (data): Promise<string> => {
    return new Promise(async (resolve, reject) => {
      // connect websocket if necessary
      if (this.websocket.readyState !== this.websocket.OPEN) {
        await this.connectWebsocket();
      }

      // send request
      const messageId: number = this.websocketMessageIdCounter;
      const message: string = JSON.stringify([messageId, data]);

      this.websocketMessageIdCounter += 1;

      this.websocket.send(message);

      this.pendingWebsocketRequests.set(messageId, {
        resolve: resolve,
        reject: reject,
      });
    });
  };

  // request handling
  public sendRequest = async (data): Promise<string> => {
    if (this.websocketsAvailable) {
      return await this.sendWebsocketRequest(data);
    } else {
      return await this.sendHttpRequest(data);
    }
  };

  // hooks
  public iterNodes = (
    selector: string,
    callback: (node: Element) => any,
    rootNode: Element = document.body,
  ) => {
    if (rootNode.nodeType !== Node.ELEMENT_NODE) {
      return;
    }

    Array.from(rootNode.children).forEach((child) => {
      this.iterNodes(selector, callback, child);
    });

    if (rootNode.matches(selector)) {
      callback(rootNode);
    }
  };

  public runHook = (name: string, rootNode: Element = document.body) => {
    const attributeName: string = `on${name}`;

    this.iterNodes(
      `[${attributeName}]`,
      (element) => {
        const attribute = element.getAttribute(attributeName);
        let fn: Function = new Function(attribute);

        try {
          fn.call(element);
        } catch (error) {
          console.error(error);
        }
      },
      rootNode,
    );
  };

  // events
  public dumpEvent = (event: Event) => {
    const eventData = {
      type: "",
      data: undefined,
      formData: {},
    };

    // The event is `undefined` when handling non-standard event handler
    // like `onRender`.
    if (!event) {
      return eventData;
    }

    eventData.type = event.type;

    // input, change, submit
    if (
      event.type == "input" ||
      event.type == "change" ||
      event.type == "submit"
    ) {
      // forms
      if (event.currentTarget instanceof HTMLFormElement) {
        const formData: FormData = new FormData(event.currentTarget);

        for (const [key, value] of formData.entries()) {
          eventData.formData[key] = value;
        }

        // inputs
      } else {
        const inputElement: HTMLInputElement =
          event.currentTarget as HTMLInputElement;

        eventData.data = inputElement.value;

        if (inputElement.hasAttribute("name")) {
          const inputName: string = inputElement.getAttribute("name");

          if (inputName) {
            eventData.formData[inputName] = inputElement.value;
          }
        }
      }
    }

    return eventData;
  };

  // node patching
  public patchNode = (node, newNode) => {
    return morphdom(node, newNode, {
      onBeforeNodeAdded: (node) => {
        // ignore styles and scripts
        if (node.nodeType !== Node.ELEMENT_NODE) {
          return node;
        }

        const tagName: string = (node as HTMLElement).tagName;

        if (["SCRIPT", "LINK", "STYLE"].includes(tagName)) {
          return false;
        }

        return node;
      },

      onBeforeNodeDiscarded: (node) => {
        // ignore styles and scripts
        if (node.nodeType !== Node.ELEMENT_NODE) {
          return true;
        }

        const tagName: string = (node as HTMLElement).tagName;

        if (["SCRIPT", "LINK", "STYLE"].includes(tagName)) {
          return false;
        }

        return true;
      },

      onBeforeElUpdated: (fromEl, toEl) => {
        // ignore styles and scripts
        if (["SCRIPT", "LINK", "STYLE"].includes(fromEl.tagName)) {
          return false;
        }

        // preserve values of input elemente
        if (
          (fromEl instanceof HTMLInputElement &&
            toEl instanceof HTMLInputElement) ||
          (fromEl instanceof HTMLTextAreaElement &&
            toEl instanceof HTMLTextAreaElement) ||
          (fromEl instanceof HTMLSelectElement &&
            toEl instanceof HTMLSelectElement)
        ) {
          toEl.value = fromEl.value;
        }

        return true;
      },
    });
  };

  public patchNodeAttributes = (node, newNode) => {
    return morphdom(node, newNode, {
      onBeforeElChildrenUpdated: (fromEl, toEl) => {
        // ignore all children
        return false;
      },
    });
  };

  // callbacks
  public runCallback = async (
    event: Event,
    nodeId: string,
    callbackName: string,
    callbackArgs: string,
    stopEvent: boolean,
    delay: number,
  ) => {
    const node = document.querySelector(`[data-falk-id=${nodeId}]`);
    const token = node.getAttribute("data-falk-token");

    const data = {
      requestType: "falk/mutation",
      nodeId: nodeId,
      token: token,
      callbackName: callbackName,
      callbackArgs: JSON.parse(decodeURIComponent(callbackArgs)),
      event: this.dumpEvent(event),
    };

    // The event is `undefined` when handling non-standard event handler
    // like `onRender`.
    if (event && stopEvent) {
      event.stopPropagation();
      event.preventDefault();
    }

    setTimeout(async () => {
      const responseText: string = await this.sendRequest(data);
      const domParser = new DOMParser();

      const newDocument = domParser.parseFromString(responseText, "text/html");

      // load linked styles
      const linkNodes = newDocument.head.querySelectorAll(
        "link[rel=stylesheet]",
      );

      linkNodes.forEach((node) => {
        // check if style is already loaded
        let selector: string;
        const styleHref: string = node.getAttribute("href");

        if (styleHref) {
          selector = `link[href="${styleHref}"]`;
        } else {
          const styleId: string = node.getAttribute("data-falk-id");

          selector = `link[data-falk-id="${styleId}"]`;
        }

        if (document.querySelector(selector)) {
          return;
        }

        // load style
        document.head.appendChild(node);
      });

      // load styles
      const styleNodes = newDocument.head.querySelectorAll("style");

      styleNodes.forEach((node) => {
        // check if style is already loaded
        const styleId: string = node.getAttribute("data-falk-id");
        const selector = `style[data-falk-id="${styleId}"]`;

        if (document.querySelector(selector)) {
          return;
        }

        // load style
        document.head.appendChild(node);
      });

      // load scripts
      const scriptNodes = newDocument.body.querySelectorAll("script");
      const promises = new Array();

      scriptNodes.forEach((node) => {
        // check if script is already loaded
        let selector: string;
        const scriptSrc: string = node.getAttribute("src");

        if (scriptSrc) {
          selector = `script[src="${scriptSrc}"]`;
        } else {
          const scriptId: string = node.getAttribute("data-falk-id");

          selector = `script[data-falk-id="${scriptId}"]`;
        }

        if (document.querySelector(selector)) {
          return;
        }

        // load script
        // We need to create a new node so our original document will run it.
        const newNode = document.createElement("script");

        for (const attribute of node.attributes) {
          newNode.setAttribute(attribute.name, attribute.value);
        }

        if (!node.src) {
          newNode.textContent = node.textContent;
        } else {
          const promise = new Promise((resolve) => {
            newNode.addEventListener("load", () => {
              resolve(null);
            });
          });

          promises.push(promise);
        }

        document.body.appendChild(newNode);
      });

      await Promise.all(promises);

      // render HTML
      // patch entire document
      if (node.tagName == "HTML") {
        // patch the attributes of the HTML node
        // (node id, token, event handlers, ...)
        this.patchNodeAttributes(node, newDocument.children[0]);

        // patch title
        document.title = newDocument.title;

        // patch body
        this.patchNode(document.body, newDocument.body);

        // patch only one node in the body
      } else {
        this.patchNode(node, newDocument.body.firstChild);
      }

      // run hooks
      this.runHook("render", node);
    }, delay);
  };
}

window["falk"] = new Falk();

window["falk"].init();
