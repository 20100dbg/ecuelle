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
      databaseInfos: ''
    }),

    computed: {

      queries() {
        let result = [];

        for (let i = this._queries.length - 1; i >= 0; i--) {
          if (this.filterQuery && !this._queries[i].query.toLowerCase().includes(this.filterQuery.toLowerCase())) {
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

      socket.on("msg", (msg) => {
        console.log(msg);

        if (msg.status) {
          if (msg.status.client) this.clientState = msg.status.client;
          if (msg.status.server) this.serverState = msg.status.server;
        }

        if (msg.connection) {
          //update current object with new value(s)
          this.connection = Object.assign(this.connection, msg.connection);

          //keep first value, only add new properties
          this.connection = Object.assign(msg.connection, this.connection);

          console.log(this.connection);
        }

        if (msg.query) {
          let q = {'query': msg.query, 'result': ''}
          this._queries.push(q)
        }

        if (msg.app_error) {
          this._queries[this._queries.length-1]['app_error'] = msg.app_error;
        }

        if (msg.result) {
          this._queries[this._queries.length-1]['result'] = msg.result;
          this._queries[this._queries.length-1]['error'] = msg.error;
        }

        this.queriesCount = this._queries.length;
      });
    },

    methods: {

      toggleOrder() {
        this.reversedOrder = !this.reversedOrder;
      },

      clearQueries() {
        this._queries = [];
      },

      onrequest() {
        socket.emit('request', {});
      }

    }

}).mount("#app");
