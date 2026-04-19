const { createApp } = Vue
const socket = io();

createApp({
    data: () => ({
      connections: [],
      //{ip:"", port:"", hash:"", salt:""}
      
      _queries: [],
      //{query: "", error:"XXXX/false", result:{cols:[], rows:[]}}

      filterQuery: '',
    }),

    computed: {

      queries() {
        let result = [];

        for (let i = this._queries.length - 1; i >= 0; i--) {
          
          if (this.filterQuery && !this._queries[i].query.toLowerCase().includes(this.filterQuery.toLowerCase())) {
            continue;
          }
          result.push(this._queries[i]);
        }
        return result;
      }


    },

    created() {
      socket.on("connect", () => { console.log('connected'); });
      socket.on("disconnect", () => { console.log('disconnected'); });

      socket.on("msg", (msg) => {

        if (msg.info) {
          this.connections.push(msg.info);
        }

        if (msg.query) {
          let q = {'query': msg.query, 'result': ''}
          this._queries.push(q)
        }

        if (msg.result) {
          this._queries[this._queries.length-1]['result'] = msg.result;
          this._queries[this._queries.length-1]['error'] = msg.error;
        }
      });
    },

    methods: {

      onrequest() {
        socket.emit('request', {});
      }

    }

}).mount("#app");
