import {
  patchNode,
  patchNodeAttributes,
  iterFalkComponents,
  nodeHasFalkNodeId,
  getFalkNodeId,
  nodeIsUiNode,
} from "./rendering";
import { WebsocketTransport } from "./websocket-transport";
import { parseTimedelta } from "./utils";
import { HTTPTransport } from "./http-transport";
import { dumpEvent } from "./events";

class Falk {
  public httpTransport: HTTPTransport;
  public websocketTransport: WebsocketTransport;

  public settings: Object;
  public tokens: Object;
  public initialCallbacks: Array<any>;

  private requestId: number;

  public init = async () => {
    this.requestId = 1;

    // setup transports
    this.httpTransport = new HTTPTransport();
    this.websocketTransport = new WebsocketTransport();

    const _init = async () => {
      const htmlElement = document.querySelector("html");

      // run beforeinit event handler
      this.dispatchEvent("beforeinit", htmlElement);

      // try to connect websocket
      if (this.settings["websockets"]) {
        await this.websocketTransport.init();
      }

      // dispatch initialRender events
      iterFalkComponents({
        rootNode: document.body,
        preserveNodes: false,
        callback: (node: HTMLElement) => {
          if (!nodeIsUiNode(node)) {
            return;
          }

          this.dispatchEvent("initialrender", node);
          this.dispatchEvent("render", node);
        },
      });

      // run initial callbacks
      this.runCallbacks(this.initialCallbacks);
    };

    if (document.readyState === "complete") {
      await _init();
    } else {
      window.addEventListener("load", async () => {
        await _init();
      });
    }
  };

  // helper
  private getRequestId = () => {
    const requestId: number = this.requestId;

    this.requestId += 1;

    return requestId;
  };

  // events
  public dispatchEvent = (
    shortName: string,
    element: HTMLElement,
    extraDetail?: Object,
  ) => {
    const attributeName: string = `on${shortName}`;
    const eventName: string = `falk:${shortName}`;
    const attribute = element.getAttribute(attributeName);
    const fn: Function = new Function("event", attribute);
    const nodeId: string = getFalkNodeId(element);

    const event = new CustomEvent(eventName, {
      bubbles: true,
      cancelable: true,
      detail: {
        nodeId: nodeId,
        rootNode: element,
        ...extraDetail,
      },
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

    // falk.on("render", event => { console.log(event));
    if (args.length == 2) {
      callback = args[1];

      document.addEventListener(eventName, callback);

      // falk.on("render", ".component#1", event => { console.log(event));
    } else if (args.length == 3) {
      selector = args[1];
      callback = args[2];

      document.addEventListener(
        eventName,
        this.filterEvents(selector, callback),
      );
    }
  };

  // callbacks
  public runCallback = async (options: {
    optionsString?: string;
    event?: Event;
    node?: HTMLElement;
    selector?: string;
    callbackName?: string;
    callbackArgs?: any;
    stopEvent?: boolean;
    delay?: string | number;
  }) => {
    // TODO: add test that checks whether the awaiting actually works

    const callbacksDone = new Array();
    let nodes: Array<HTMLElement>;

    // parse options string
    if (options.optionsString) {
      const optionsOverrides = JSON.parse(
        decodeURIComponent(options.optionsString),
      );

      options = Object.assign(options, optionsOverrides);
    }

    // find event type
    let eventType: string = "";

    if (event) {
      eventType = event.type;
    }

    // find nodes
    if (options.node) {
      nodes = [options.node];
    } else if (options.selector) {
      nodes = Array.from(document.querySelectorAll(options.selector));
    }

    // iter nodes
    for (const node of nodes) {
      const requestId = this.getRequestId();
      const eventData = dumpEvent(options.event);
      const nodeId = getFalkNodeId(node);
      const token = this.tokens[nodeId];
      const callbackName = options.callbackName || "";
      const callbackArgs = options.callbackArgs || {};

      // The event is `undefined` when handling non-standard event handler
      // like `onRender`.
      if (options.event && options.stopEvent) {
        options.event.stopPropagation();
        options.event.preventDefault();
      }

      const promise = new Promise((resolve) => {
        setTimeout(
          async () => {
            // run beforerequest hook
            this.dispatchEvent("beforerequest", node, {
              requestId: requestId,
            });

            // send mutation request
            let responseData;

            // HTTP multipart POST (file uploads)
            if (eventData.files.length > 0) {
              responseData =
                await this.httpTransport.sendMultipartMutationRequest({
                  nodeId: nodeId,
                  token: token,
                  callbackName: callbackName,
                  callbackArgs: callbackArgs,
                  eventData: eventData,
                });

              // websocket
            } else if (
              this.settings["websockets"] &&
              this.websocketTransport.available
            ) {
              responseData = await this.websocketTransport.sendMutationRequest({
                nodeId: nodeId,
                token: token,
                callbackName: callbackName,
                callbackArgs: callbackArgs,
                eventData: eventData,
              });

              // HTTP POST
            } else {
              responseData = await this.httpTransport.sendMutationRequest({
                nodeId: nodeId,
                token: token,
                callbackName: callbackName,
                callbackArgs: callbackArgs,
                eventData: eventData,
              });
            }

            // run response hook
            this.dispatchEvent("response", node, {
              requestId: requestId,
            });

            // rendering
            const render: boolean =
              !responseData.flags.skipRendering ||
              responseData.flags.forceRendering;

            // parse response HTML
            if (render) {
              const domParser = new DOMParser();

              const newDocument = domParser.parseFromString(
                responseData.body as string,
                "text/html",
              );

              // load linked styles
              const linkNodes = newDocument.head.querySelectorAll(
                "link[rel=stylesheet]",
              );

              linkNodes.forEach((node: HTMLLinkElement) => {
                // check if style is already loaded
                let selector: string;
                const styleHref: string = node.getAttribute("href");

                if (styleHref) {
                  selector = `link[href="${styleHref}"]`;
                } else {
                  const styleId: string = getFalkNodeId(node);

                  selector = `link[fx-id="${styleId}"]`;
                }

                if (document.querySelector(selector)) {
                  return;
                }

                // load style
                document.head.appendChild(node);
              });

              // load styles
              const styleNodes = newDocument.head.querySelectorAll("style");

              styleNodes.forEach((node: HTMLStyleElement) => {
                // check if style is already loaded
                const styleId: string = getFalkNodeId(node);
                const selector = `style[fx-id="${styleId}"]`;

                if (document.querySelector(selector)) {
                  return;
                }

                // load style
                document.head.appendChild(node);
              });

              // load scripts
              const scriptNodes = newDocument.body.querySelectorAll("script");
              const scriptsLoaded = new Array();

              scriptNodes.forEach((node: HTMLScriptElement) => {
                // check if script is already loaded
                let selector: string;
                const scriptSrc: string = node.getAttribute("src");

                if (scriptSrc) {
                  selector = `script[src="${scriptSrc}"]`;
                } else {
                  const scriptId: string = getFalkNodeId(node);

                  selector = `script[fx-id="${scriptId}"]`;
                }

                if (document.querySelector(selector)) {
                  return;
                }

                // load script
                // We need to create a new node so our original document will
                // run it.
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

                  scriptsLoaded.push(promise);
                }

                document.body.appendChild(newNode);
              });

              await Promise.all(scriptsLoaded);

              // render HTML
              // patch entire document
              if (node.tagName == "HTML") {
                // patch the attributes of the HTML node
                // (node id, token, event handlers, ...)
                patchNodeAttributes({
                  node: node,
                  newNode: newDocument.children[0] as HTMLElement,
                  onRender: (node: HTMLElement) => {
                    this.dispatchEvent("render", node);
                  },
                });

                // patch title
                document.title = newDocument.title;

                // patch body
                patchNode({
                  node: document.body,
                  newNode: newDocument.body,
                  preserveNodes: !responseData.flags.forceRendering,

                  onInitialRender: (node: HTMLElement) => {
                    this.dispatchEvent("initialrender", node);
                  },

                  onRender: (node: HTMLElement) => {
                    this.dispatchEvent("render", node);
                  },

                  onBeforeUnmount: (node: HTMLElement) => {
                    this.dispatchEvent("beforeunmount", node);

                    // remove obsolete token
                    if (nodeHasFalkNodeId(node)) {
                      const nodeId = getFalkNodeId(node);

                      delete this.tokens[nodeId];
                    }
                  },
                });

                // patch only one node in the body
              } else {
                patchNode({
                  node: node,
                  newNode: newDocument.body.firstChild as HTMLElement,
                  preserveNodes: !responseData.flags.forceRendering,

                  onInitialRender: (node: HTMLElement) => {
                    this.dispatchEvent("initialrender", node);
                  },

                  onRender: (node: HTMLElement) => {
                    this.dispatchEvent("render", node);
                  },

                  onBeforeUnmount: (node: HTMLElement) => {
                    this.dispatchEvent("beforeunmount", node);
                  },
                });
              }
            }

            // update tokens
            // NOTE: this needs to happen after we patched the DOM because
            // morphdom removes all tokens for us that are not needed anymore,
            // and before we run the hooks because the hooks need the tokens to
            // be updated.
            for (const [key, value] of Object.entries(responseData.tokens)) {
              this.tokens[key] = value;
            }

            // run callbacks
            this.runCallbacks(responseData.callbacks);

            // end callback
            resolve(null);
          },
          parseTimedelta(options.delay || 0),
        );
      });

      callbacksDone.push(promise);
    }

    // wait for all callbacks to be done
    return Promise.all(callbacksDone);
  };

  private runCallbacks = (callbacks: Array<any>) => {
    for (const callback of callbacks) {
      this.runCallback({
        selector: callback[0],
        callbackName: callback[1],
        callbackArgs: callback[2],
        delay: callback[3],
      });
    }
  };
}

window["falk"] = new Falk();
