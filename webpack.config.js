const TerserPlugin = require("terser-webpack-plugin");
const path = require("path");

module.exports = {
  mode: "production",
  entry: {
    falk: "./client/falk.ts",
  },
  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "falk/static/falk"),
  },
  resolve: {
    extensions: [".ts"],
    alias: {
      "@": path.resolve(__dirname, "client"),
    },
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
    ],
  },
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_debugger: false,
            drop_console: false,
          },
        },
      }),
    ],
  },
};
