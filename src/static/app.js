const { createApp } = Vue
const socket = io();

createApp({
    data: () => ({
      connections: [],
      //{ip:"", port:"", hash:"", salt:""}
      
      queries: [],
      //{query: "", error:"XXXX/false", result:{cols:[], rows:[]}}
    }),

    created() {
      socket.on("connect", () => { console.log('connected'); });
      socket.on("disconnect", () => { console.log('disconnected'); });

      socket.on("msg", (msg) => {

        if (msg.info) {
          this.connections.push(msg.info);
        }

        if (msg.query) {
          let q = {'query': msg.query, 'result': ''}
          this.queries.push(q)
        }

        if (msg.result) {
          this.queries[this.queries.length-1]['result'] = msg.result;
          this.queries[this.queries.length-1]['error'] = msg.error;
        }
      });
    },

    methods: {

      onrequest() {
        socket.emit('request', {});
      }

    }

}).mount("#app");
