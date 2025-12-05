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

    if (document.readyState === "complete") {
      this.dispatchRenderEvents(document.body, {
        initial: true,
      });
    } else {
      window.addEventListener("load", () => {
        this.dispatchRenderEvents(document.body, {
          initial: true,
        });
      });
    }
  };

  // helper
  public parseDelay = (delay: string | number) => {
    if (typeof delay === "number") {
      return delay * 1000;
    }

    delay = delay as string;

    const match = /^(\d+(?:\.\d+)?)(ms|s|m|h)?$/.exec(delay.trim());

    if (!match) {
      throw new Error("Invalid time format: " + delay);
    }

    const value = parseFloat(match[1]);
    const unit = match[2] || "s";

    if (unit === "ms") {
      return value;
    } else if (unit === "s") {
      return value * 1000;
    } else if (unit === "m") {
      return value * 60 * 1000;
    } else if (unit === "h") {
      return value * 60 * 60 * 1000;
    } else {
      throw new Error("Unknown unit: " + unit);
    }
  };

  // request handling: AJAX
  public sendHttpRequest = async (data): Promise<any> => {
    return new Promise(async (resolve, reject) => {
      const response = await fetch(window.location + "", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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

  // request handling: websockets
  private handleWebsocketMessage = (event: MessageEvent) => {
    const [messageId, messageData] = JSON.parse(event.data);
    const responseData = messageData.json;
    const promiseCallbacks = this.pendingWebsocketRequests.get(messageId);

    // handle reloads
    if (responseData.flags.reload) {
      window.location.reload();
    }

    // HTML responses
    promiseCallbacks["resolve"](responseData);

    this.pendingWebsocketRequests.delete(messageData);
  };

  public connectWebsocket = (): Promise<boolean> => {
    return new Promise((resolve) => {
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

  public sendWebsocketRequest = async (data): Promise<any> => {
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
  public sendRequest = async (data): Promise<any> => {
    if (this.websocketsAvailable) {
      return await this.sendWebsocketRequest(data);
    } else {
      return await this.sendHttpRequest(data);
    }
  };

  // events
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

  public dispatchEvent = (shortName: string, element: Element) => {
    const attributeName: string = `on${shortName}`;
    const eventName: string = `falk:${shortName}`;
    const attribute = element.getAttribute(attributeName);
    const fn: Function = new Function("event", attribute);

    const event = new CustomEvent(eventName, {
      bubbles: true,
      cancelable: true,
    });

    // inline event handler
    try {
      fn.call(element, event);
    } catch (error) {
      console.error(error);
    }

    // event listener
    element.dispatchEvent(event);
  };

  public dispatchRenderEvents = (
    rootNode: Element = document.body,
    options: { initial: boolean } = { initial: false },
  ) => {
    this.iterNodes(
      "[data-falk-id]",
      (node) => {
        if (options.initial || node != rootNode) {
          this.dispatchEvent("initialrender", node);
        }

        this.dispatchEvent("render", node);
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
  public patchNode = (node, newNode, flags) => {
    const nodeShouldBeSkipped = (node) => {
      if (flags.forceRendering) {
        return false;
      }

      if (flags.skipRendering) {
        return true;
      }

      return node.hasAttribute("data-skip-rerendering");
    };

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

        if (nodeShouldBeSkipped(node)) {
          return node;
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

        if (nodeShouldBeSkipped(node)) {
          return false;
        }

        return true;
      },

      onBeforeElUpdated: (fromEl, toEl) => {
        if (nodeShouldBeSkipped(fromEl)) {
          return false;
        }

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
  public runCallback = async (options: {
    optionsString?: string;
    event?: Event;
    node?: HTMLElement;
    nodeId?: string;
    selector?: string;
    callbackName?: string;
    callbackArgs?: any;
    stopEvent?: boolean;
    delay?: string | number;
  }) => {
    let nodes: Array<HTMLElement>;

    // parse options string
    if (options.optionsString) {
      const optionsOverrides = JSON.parse(
        decodeURIComponent(options.optionsString),
      );

      options = Object.assign(optionsOverrides);
    }

    // find nodes
    if (options.node) {
      nodes = [options.node];
    } else if (options.nodeId) {
      const node: HTMLElement = document.querySelector(
        `[data-falk-id=${options.nodeId}]`,
      );

      if (!node) {
        throw `no node with id ${options.nodeId}`;
      }

      nodes = [node];
    } else if (options.selector) {
      nodes = Array.from(document.querySelectorAll(options.selector));
    }

    // iter nodes
    for (const node of nodes) {
      const token = node.getAttribute("data-falk-token");
      const nodeId = node.getAttribute("data-falk-id");

      const data = {
        requestType: "falk/mutation",
        nodeId: nodeId,
        token: token,
        callbackName: options.callbackName || "",
        callbackArgs: options.callbackArgs || {},
        event: {},
      };

      if (options.event) {
        data.event = this.dumpEvent(options.event);
      }

      // The event is `undefined` when handling non-standard event handler
      // like `onRender`.
      if (options.event && options.stopEvent) {
        options.event.stopPropagation();
        options.event.preventDefault();
      }

      setTimeout(
        async () => {
          // run beforerequest hook
          this.dispatchEvent("beforerequest", node);

          // send mutation request
          const responseData = await this.sendRequest(data);
          const domParser = new DOMParser();

          const newDocument = domParser.parseFromString(
            responseData.body as string,
            "text/html",
          );

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
            this.patchNode(document.body, newDocument.body, responseData.flags);

            // patch only one node in the body
          } else {
            this.patchNode(
              node,
              newDocument.body.firstChild,
              responseData.flags,
            );
          }

          // run hooks
          this.dispatchRenderEvents(node);

          // run callbacks
          for (const callback of responseData.callbacks) {
            this.runCallback({
              selector: callback[0],
              callbackName: callback[1],
              callbackArgs: callback[2],
            });
          }
        },
        this.parseDelay(options.delay || 0),
      );
    }
  };

  public filterEvents = (selector: string, callback: (event) => any) => {
    return (event) => {
      if (!event.target.matches(selector)) {
        return;
      }

      return callback(event);
    };
  };

  private on = (...args) => {
    const eventShortName: string = args[0];
    const eventName: string = `falk:${eventShortName}`;
    let selector: string;
    let callback: (event) => any;

    // falk.on("render", ".component#1", event => { console.log(event));
    if (args.length == 2) {
      callback = args[1];

      document.addEventListener(eventName, callback);

      // falk.on("render", event => { console.log(event));
    } else if (args.length == 3) {
      selector = args[1];
      callback = args[2];

      document.addEventListener(
        eventName,
        this.filterEvents(selector, callback),
      );
    }
  };
}

window["falk"] = new Falk();

window["falk"].init();
