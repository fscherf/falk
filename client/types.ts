export type MutationRequestResponse = {
  valid: boolean;

  httpResponse?: any;

  flags?: Record<string, boolean>;
  body?: string;
  tokens?: Record<string, string>;
  callbacks?: Array<Array<any>>;
};
