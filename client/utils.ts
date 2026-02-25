export function parseTimedelta(timedelta: string | number) {
  if (typeof timedelta === "number") {
    return timedelta * 1000;
  }

  timedelta = timedelta as string;

  const match = /^(\d+(?:\.\d+)?)(ms|s|m|h)?$/.exec(timedelta.trim());

  if (!match) {
    throw new Error("Invalid timedelta format: " + timedelta);
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
}
