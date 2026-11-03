const { createApp } = Vue
const socket = io();

createApp({
    data: () => ({
      connection: {},
      _queries: [],
      filterQuery: '',
      reversedOrder: false,
      clientState: '',
      serverState: '',
      queriesCount: 0,
      dbUsername: '',
      dbName: '',
      dbms: '',
      dbVersion: '',
    }),

    computed: {

      queries() {
        let result = [];

        for (let i = this._queries.length - 1; i >= 0; i--) {
          if (this.filterQuery && !this._queries[i].cmd.toLowerCase().includes(this.filterQuery.toLowerCase())) {
            continue;
          }
          this._queries[i].id = i;
          result.push(this._queries[i]);
        }

        if (this.reversedOrder) {
          return result.reverse();
        }

        return result;
      }
    },

    created() {
      socket.on("connect", () => { });
      socket.on("disconnect", () => { });

      socket.on("status", (msg) => {
        if (msg.client) this.clientState = msg.client;
        if (msg.server) this.serverState = msg.server;
      });

      socket.on("connection", (msg) => {
        if (msg.connection.username) this.dbUsername = msg.connection.username;
        if (msg.connection.schema) this.dbName = msg.connection.schema;
        if (msg.connection.db_version) this.dbVersion = msg.connection.db_version;
        if (msg.dbms) this.dbms = msg.dbms;
      });

      socket.on("query", (msg) => {
        prettyQuery = window.highlight(msg.query, { html: true });
        let q = {'cmd': msg.query, 'cmdHighlight': prettyQuery, 'result': '', 'date': new Date(msg.timestamp * 1000).toLocaleString()};
        this._queries.push(q);
        this.queriesCount = this._queries.length;
      });

      socket.on("parameters", (msg) => {
      });

      socket.on("results", (msg) => {
        this._queries[this._queries.length-1]['result'] = msg.result;
      });

      socket.on("error", (msg) => {
        this._queries[this._queries.length-1]['error'] = msg.error;
      });

      socket.on("parse_error", (msg) => {
        this._queries[this._queries.length-1]['parse_error'] = msg.parse_error;
      });
    },

    methods: {

      toggleOrder() {
        this.reversedOrder = !this.reversedOrder;
      },

      clearQueries() {
        this._queries = [];
        this.queriesCount = 0;
      },

      onrequest() {
        socket.emit('request', {});
      }

    }

}).mount("#app");
